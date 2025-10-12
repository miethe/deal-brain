"""Baseline valuation CLI commands."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer

from ..db import session_scope
from ..services.baseline_loader import BaselineLoaderService

app = typer.Typer(help="Baseline valuation operations.")


@app.command("load")
def load_baseline(
    source: Path = typer.Argument(..., exists=True, readable=True, help="Path to baseline JSON artifact"),
    actor: str = typer.Option("system", "--actor", "-a", help="Actor recorded in metadata/audit logs"),
    ensure_basic_ruleset_id: int = typer.Option(
        0,
        "--ensure-basic-for",
        help="Ruleset ID that should contain a managed Basic · Adjustments group (0=none)",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Emit the result as JSON for scripting",
    ),
) -> None:
    """Populate the System Baseline ruleset from a JSON artifact."""

    async def _run() -> dict[str, object]:
        async with session_scope() as session:
            service = BaselineLoaderService()
            result = await service.load_from_path(
                session,
                source,
                actor=actor,
                ensure_basic_for_ruleset=ensure_basic_ruleset_id if ensure_basic_ruleset_id > 0 else None,
            )
            return result.to_dict()

    summary = asyncio.run(_run())

    if output_json:
        typer.echo(json.dumps(summary, indent=2))
    else:
        typer.echo(
            f"[{summary['status']}]: ruleset={summary.get('ruleset_name')} "
            f"(id={summary.get('ruleset_id')}) version={summary.get('version')} "
            f"groups={summary.get('created_groups')} rules={summary.get('created_rules')}"
        )
        if summary.get("skipped_reason"):
            typer.echo(f"Reason: {summary['skipped_reason']}")
