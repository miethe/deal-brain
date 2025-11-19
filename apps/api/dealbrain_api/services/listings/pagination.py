"""Cursor-based pagination for listings.

This module implements high-performance keyset pagination with:
- Composite key (sort_column, id) for stable pagination
- Base64-encoded cursors to prevent manipulation
- Cached total count (5 minutes TTL)
- Support for dynamic sorting and filtering
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...cache import cache_manager
from ...models import Listing
from ...telemetry import get_logger

logger = get_logger("dealbrain.listings.pagination")


def encode_cursor(listing_id: int, sort_value: Any) -> str:
    """Encode cursor for keyset pagination.

    Args:
        listing_id: Listing ID
        sort_value: Value of the sort column (converted to string for serialization)

    Returns:
        Base64-encoded cursor string
    """
    cursor_data = {
        "id": listing_id,
        "sort_value": str(sort_value) if sort_value is not None else None,
    }
    cursor_json = json.dumps(cursor_data)
    cursor_bytes = cursor_json.encode("utf-8")
    return base64.urlsafe_b64encode(cursor_bytes).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[int, str | None]:
    """Decode cursor for keyset pagination.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Tuple of (listing_id, sort_value)

    Raises:
        ValueError: If cursor is invalid
    """
    try:
        cursor_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        cursor_json = cursor_bytes.decode("utf-8")
        cursor_data = json.loads(cursor_json)
        return cursor_data["id"], cursor_data.get("sort_value")
    except Exception as exc:
        raise ValueError(f"Invalid cursor format: {exc}") from exc


async def get_paginated_listings(
    session: AsyncSession,
    *,
    limit: int = 50,
    cursor: str | None = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    form_factor: str | None = None,
    manufacturer: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> dict[str, Any]:
    """Get paginated listings using cursor-based (keyset) pagination.

    Implements high-performance cursor-based pagination with:
    - Composite key (sort_column, id) for stable pagination
    - Base64-encoded cursors to prevent manipulation
    - Cached total count (5 minutes TTL)
    - Support for dynamic sorting and filtering

    Args:
        session: Database session
        limit: Number of items per page (1-500, default 50)
        cursor: Pagination cursor from previous response
        sort_by: Column to sort by (default "updated_at")
        sort_order: Sort direction ("asc" or "desc", default "desc")
        form_factor: Filter by form factor
        manufacturer: Filter by manufacturer
        min_price: Filter by minimum price
        max_price: Filter by maximum price

    Returns:
        Dictionary with:
        - items: List of Listing objects
        - total: Total count (cached)
        - limit: Requested limit
        - next_cursor: Cursor for next page (None if last page)
        - has_next: Boolean indicating if more pages exist

    Raises:
        ValueError: If sort_by contains invalid characters or cursor is malformed
    """
    # Validate sort_by to prevent SQL injection
    if not sort_by.replace("_", "").isalpha():
        raise ValueError(f"Invalid sort column: {sort_by}")

    # Validate limit
    if limit < 1 or limit > 500:
        raise ValueError("Limit must be between 1 and 500")

    # Get sortable column
    sort_column = getattr(Listing, sort_by, None)
    if sort_column is None:
        raise ValueError(f"Invalid sort column: {sort_by}")

    # Build base query with eager loading
    stmt = select(Listing).options(
        selectinload(Listing.cpu),
        selectinload(Listing.gpu),
        selectinload(Listing.ports_profile),
    )

    # Apply filters
    filters = []
    if form_factor:
        filters.append(Listing.form_factor == form_factor)
    if manufacturer:
        filters.append(Listing.manufacturer == manufacturer)
    if min_price is not None:
        filters.append(Listing.price_usd >= min_price)
    if max_price is not None:
        filters.append(Listing.price_usd <= max_price)

    if filters:
        stmt = stmt.where(and_(*filters))

    # Apply cursor-based filtering (keyset pagination)
    if cursor:
        cursor_id, cursor_sort_value = decode_cursor(cursor)

        # Build keyset condition based on sort order
        if sort_order.lower() == "desc":
            # For DESC: (sort_col < cursor_value) OR (sort_col = cursor_value AND id < cursor_id)
            if cursor_sort_value is not None:
                # Convert cursor_sort_value back to appropriate type
                if isinstance(sort_column.type, type(Listing.id.type)):  # Integer column
                    cursor_sort_value = int(cursor_sort_value)
                elif hasattr(sort_column.type, "python_type"):
                    # For datetime columns
                    if sort_column.type.python_type == datetime:
                        cursor_sort_value = datetime.fromisoformat(cursor_sort_value)
                    else:
                        cursor_sort_value = float(cursor_sort_value)

                stmt = stmt.where(
                    or_(
                        sort_column < cursor_sort_value,
                        and_(sort_column == cursor_sort_value, Listing.id < cursor_id),
                    )
                )
            else:
                # If sort_value is NULL, only filter by ID
                stmt = stmt.where(Listing.id < cursor_id)
        else:
            # For ASC: (sort_col > cursor_value) OR (sort_col = cursor_value AND id > cursor_id)
            if cursor_sort_value is not None:
                # Convert cursor_sort_value back to appropriate type
                if isinstance(sort_column.type, type(Listing.id.type)):  # Integer column
                    cursor_sort_value = int(cursor_sort_value)
                elif hasattr(sort_column.type, "python_type"):
                    # For datetime columns
                    if sort_column.type.python_type == datetime:
                        cursor_sort_value = datetime.fromisoformat(cursor_sort_value)
                    else:
                        cursor_sort_value = float(cursor_sort_value)

                stmt = stmt.where(
                    or_(
                        sort_column > cursor_sort_value,
                        and_(sort_column == cursor_sort_value, Listing.id > cursor_id),
                    )
                )
            else:
                # If sort_value is NULL, only filter by ID
                stmt = stmt.where(Listing.id > cursor_id)

    # Apply sorting (composite key: sort_column, id)
    if sort_order.lower() == "desc":
        stmt = stmt.order_by(desc(sort_column), desc(Listing.id))
    else:
        stmt = stmt.order_by(asc(sort_column), asc(Listing.id))

    # Fetch limit+1 to determine has_next (without separate count query per page)
    stmt = stmt.limit(limit + 1)

    result = await session.execute(stmt)
    listings = list(result.scalars().unique().all())

    # Determine if there's a next page
    has_next = len(listings) > limit
    if has_next:
        listings = listings[:limit]  # Remove the extra item

    # Generate next_cursor from last item
    next_cursor = None
    if has_next and listings:
        last_listing = listings[-1]
        last_sort_value = getattr(last_listing, sort_by)
        # Handle datetime serialization for cursor
        if isinstance(last_sort_value, datetime):
            last_sort_value = last_sort_value.isoformat()
        next_cursor = encode_cursor(last_listing.id, last_sort_value)

    # Get cached total count
    cache_key = "listings:total_count"
    cached_total = await cache_manager.get(cache_key)

    if cached_total is not None:
        total = int(cached_total)
    else:
        # Calculate total and cache it
        count_stmt = select(func.count()).select_from(Listing)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Cache for 5 minutes
        await cache_manager.set(cache_key, str(total), ttl=timedelta(minutes=5))

    return {
        "items": listings,
        "total": total,
        "limit": limit,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }
