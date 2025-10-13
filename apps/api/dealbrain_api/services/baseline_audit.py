"""Service for auditing baseline operations."""

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.baseline_audit import BaselineAuditLog

logger = logging.getLogger(__name__)


class BaselineAuditService:
    """Service for logging baseline operations."""

    async def log_instantiation(
        self,
        session: AsyncSession,
        actor: str | None,
        source_hash: str,
        version: str,
        ruleset_id: int | None,
        success: bool = True,
        error: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> BaselineAuditLog:
        """Log baseline instantiation operation.

        Args:
            session: Database session
            actor: Actor name or ID
            source_hash: Hash of baseline source
            version: Baseline version
            ruleset_id: Created ruleset ID
            success: Whether operation succeeded
            error: Error message if failed
            payload: Additional operation data

        Returns:
            Created audit log entry
        """
        audit_log = BaselineAuditLog(
            operation="baseline_instantiation",
            actor_name=actor,
            source_hash=source_hash,
            version=version,
            ruleset_id=ruleset_id,
            result="success" if success else "failure",
            error_message=error,
            payload=payload or {},
            timestamp=datetime.utcnow()
        )

        session.add(audit_log)
        await session.commit()

        logger.info(
            f"Baseline instantiation logged: version={version}, "
            f"hash={source_hash[:8]}..., actor={actor}, result={audit_log.result}"
        )

        return audit_log

    async def log_diff_request(
        self,
        session: AsyncSession,
        actor: str | None,
        candidate_hash: str,
        current_hash: str | None,
        payload: dict[str, Any] | None = None,
    ) -> BaselineAuditLog:
        """Log baseline diff request.

        Args:
            session: Database session
            actor: Actor name or ID
            candidate_hash: Hash of candidate baseline
            current_hash: Hash of current baseline
            payload: Diff results

        Returns:
            Created audit log entry
        """
        audit_log = BaselineAuditLog(
            operation="baseline_diff",
            actor_name=actor,
            source_hash=candidate_hash,
            payload={
                "candidate_hash": candidate_hash,
                "current_hash": current_hash,
                **(payload or {})
            },
            result="success",
            timestamp=datetime.utcnow()
        )

        session.add(audit_log)
        await session.commit()

        logger.info(
            f"Baseline diff logged: candidate={candidate_hash[:8]}..., "
            f"current={current_hash[:8] if current_hash else 'none'}..., actor={actor}"
        )

        return audit_log

    async def log_adoption(
        self,
        session: AsyncSession,
        actor: str | None,
        changes_applied: int,
        new_version: str,
        old_version: str | None,
        new_hash: str,
        old_hash: str | None,
        affected_listings: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> BaselineAuditLog:
        """Log baseline adoption operation.

        Args:
            session: Database session
            actor: Actor name or ID
            changes_applied: Number of changes applied
            new_version: New baseline version
            old_version: Previous baseline version
            new_hash: New baseline hash
            old_hash: Previous baseline hash
            affected_listings: Number of affected listings
            payload: Additional operation data

        Returns:
            Created audit log entry
        """
        audit_log = BaselineAuditLog(
            operation="baseline_adoption",
            actor_name=actor,
            source_hash=new_hash,
            version=new_version,
            affected_listings_count=affected_listings,
            payload={
                "changes_applied": changes_applied,
                "old_version": old_version,
                "new_version": new_version,
                "old_hash": old_hash,
                "new_hash": new_hash,
                **(payload or {})
            },
            result="success",
            timestamp=datetime.utcnow()
        )

        session.add(audit_log)
        await session.commit()

        logger.info(
            f"Baseline adoption logged: old={old_version}, new={new_version}, "
            f"changes={changes_applied}, actor={actor}"
        )

        return audit_log

    async def log_override_operation(
        self,
        session: AsyncSession,
        operation: str,  # "create", "update", "delete", "reset"
        actor: str | None,
        entity_key: str,
        field_name: str,
        old_value: Any = None,
        new_value: Any = None,
        success: bool = True,
        error: str | None = None,
    ) -> BaselineAuditLog:
        """Log override operation.

        Args:
            session: Database session
            operation: Type of override operation
            actor: Actor name or ID
            entity_key: Entity identifier
            field_name: Field being overridden
            old_value: Previous value
            new_value: New value
            success: Whether operation succeeded
            error: Error message if failed

        Returns:
            Created audit log entry
        """
        audit_log = BaselineAuditLog(
            operation=f"override_{operation}",
            actor_name=actor,
            entity_key=entity_key,
            field_name=field_name,
            payload={
                "old_value": old_value,
                "new_value": new_value,
                "operation": operation
            },
            result="success" if success else "failure",
            error_message=error,
            timestamp=datetime.utcnow()
        )

        session.add(audit_log)
        await session.commit()

        logger.info(
            f"Override {operation} logged: entity={entity_key}, "
            f"field={field_name}, actor={actor}, result={audit_log.result}"
        )

        return audit_log

    async def log_bulk_operation(
        self,
        session: AsyncSession,
        operation: str,
        actor: str | None,
        affected_count: int,
        total_adjustment_change: float | None = None,
        success: bool = True,
        error: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> BaselineAuditLog:
        """Log bulk baseline operation.

        Args:
            session: Database session
            operation: Type of bulk operation
            actor: Actor name or ID
            affected_count: Number of entities affected
            total_adjustment_change: Total valuation change
            success: Whether operation succeeded
            error: Error message if failed
            payload: Additional operation data

        Returns:
            Created audit log entry
        """
        audit_log = BaselineAuditLog(
            operation=f"bulk_{operation}",
            actor_name=actor,
            affected_listings_count=affected_count,
            total_adjustment_change=total_adjustment_change,
            payload=payload or {},
            result="success" if success else "failure",
            error_message=error,
            timestamp=datetime.utcnow()
        )

        session.add(audit_log)
        await session.commit()

        logger.info(
            f"Bulk {operation} logged: affected={affected_count}, "
            f"actor={actor}, result={audit_log.result}"
        )

        return audit_log

    async def get_recent_operations(
        self,
        session: AsyncSession,
        limit: int = 100,
        operation_type: str | None = None,
        actor: str | None = None,
    ) -> list[BaselineAuditLog]:
        """Get recent audit log entries.

        Args:
            session: Database session
            limit: Maximum number of entries to return
            operation_type: Filter by operation type
            actor: Filter by actor

        Returns:
            List of audit log entries
        """
        from sqlalchemy import select, and_

        stmt = select(BaselineAuditLog).order_by(
            BaselineAuditLog.timestamp.desc()
        ).limit(limit)

        conditions = []
        if operation_type:
            conditions.append(BaselineAuditLog.operation == operation_type)
        if actor:
            conditions.append(BaselineAuditLog.actor_name == actor)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await session.execute(stmt)
        return list(result.scalars().all())