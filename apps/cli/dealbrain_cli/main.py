"""CLI entrypoint using Typer."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from sqlalchemy import select

from dealbrain_api.api.rankings import VALID_METRICS
from dealbrain_api.db import session_scope
from dealbrain_api.models import Listing
from dealbrain_api.seeds import seed_from_workbook
from dealbrain_api.services.listings import (
    apply_listing_metrics,
    create_listing,
    sync_listing_components,
)
from dealbrain_core.schemas import ListingCreate

app = typer.Typer(help="Deal Brain CLI utilities")


@app.command()
def version() -> None:
    """Print the installed Deal Brain version."""
    from dealbrain_core import __version__

    typer.echo(f"Deal Brain version: {__version__}")


@app.command("import")
def import_workbook(path: Path) -> None:
    """Import an Excel workbook into the database."""

    async def runner() -> None:
        await seed_from_workbook(path)

    asyncio.run(runner())
    typer.echo(f"Imported workbook from {path}")


@app.command()
def add(
    title: str = typer.Option(..., help="Listing title"),
    price: float = typer.Option(..., help="Listing price in USD"),
    condition: str = typer.Option("used", help="Condition: new/refurb/used"),
    cpu_id: Optional[int] = typer.Option(None, help="CPU ID"),
    ram_gb: int = typer.Option(0, help="Installed RAM in GB"),
    storage_gb: int = typer.Option(0, help="Primary storage in GB"),
    storage_type: Optional[str] = typer.Option(None, help="Primary storage type"),
) -> None:
    """Add a new listing and compute valuation metrics."""

    async def runner() -> None:
        payload = ListingCreate(
            title=title,
            price_usd=price,
            condition=condition,
            cpu_id=cpu_id,
            ram_gb=ram_gb,
            primary_storage_gb=storage_gb,
            primary_storage_type=storage_type,
        )
        async with session_scope() as session:
            listing = await create_listing(session, payload.model_dump(exclude={"components"}, exclude_none=True))
            await sync_listing_components(session, listing, None)
            await apply_listing_metrics(session, listing)
            await session.refresh(listing)
            typer.echo(f"Created listing #{listing.id} — adjusted price ${listing.adjusted_price_usd}")

    asyncio.run(runner())


@app.command()
def top(metric: str = typer.Option("score_composite"), limit: int = typer.Option(5)) -> None:
    """Show top listings by metric."""

    async def runner() -> None:
        async with session_scope() as session:
            ordering = VALID_METRICS.get(metric, lambda column: column.desc())
            column = getattr(Listing, metric)
            result = await session.execute(
                select(Listing)
                    .where(column.is_not(None))
                    .order_by(ordering(column))
                    .limit(limit)
            )
            for listing in result.scalars().all():
                value = getattr(listing, metric)
                typer.echo(
                    f"#{listing.id}: {listing.title} — {metric}={value} adjusted=${listing.adjusted_price_usd}"
                )

    asyncio.run(runner())


@app.command()
def explain(listing_id: int) -> None:
    """Print the valuation breakdown for a listing."""

    async def runner() -> None:
        async with session_scope() as session:
            listing = await session.get(Listing, listing_id)
            if not listing:
                typer.echo(f"Listing {listing_id} not found", err=True)
                raise typer.Exit(code=1)
            await apply_listing_metrics(session, listing)
            breakdown = listing.valuation_breakdown or {}
            typer.echo(json.dumps(breakdown, indent=2))

    asyncio.run(runner())


@app.command()
def export(
    metric: str = typer.Option("score_composite"),
    limit: int = typer.Option(20),
    output: Optional[Path] = typer.Option(None),
) -> None:
    """Export top listings to JSON."""

    async def runner() -> list[dict[str, object]]:
        async with session_scope() as session:
            ordering = VALID_METRICS.get(metric, lambda column: column.desc())
            column = getattr(Listing, metric)
            result = await session.execute(
                select(Listing)
                    .where(column.is_not(None))
                    .order_by(ordering(column))
                    .limit(limit)
            )
            return [listing_to_dict(listing) for listing in result.scalars().all()]

    data = asyncio.run(runner())
    payload = json.dumps(data, indent=2)
    if output:
        output.write_text(payload)
        typer.echo(f"Exported {len(data)} listings to {output}")
    else:
        typer.echo(payload)


def listing_to_dict(listing: Listing) -> dict[str, object]:
    return {
        "id": listing.id,
        "title": listing.title,
        "price_usd": float(listing.price_usd or 0),
        "adjusted_price_usd": listing.adjusted_price_usd,
        "score_composite": listing.score_composite,
        "score_cpu_multi": listing.score_cpu_multi,
        "score_cpu_single": listing.score_cpu_single,
        "dollar_per_cpu_mark": listing.dollar_per_cpu_mark,
        "perf_per_watt": listing.perf_per_watt,
    }


if __name__ == "__main__":  # pragma: no cover
    app()

