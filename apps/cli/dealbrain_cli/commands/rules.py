"""CLI commands for valuation rules management"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from dealbrain_api.db import session_scope
from dealbrain_api.models.core import (
    ValuationRuleset,
    ValuationRuleGroup,
    ValuationRuleV2,
)
from dealbrain_api.services.rules import RulesService
from dealbrain_api.services.rule_evaluation import RuleEvaluationService
from dealbrain_api.services.rule_preview import RulePreviewService
from dealbrain_api.services.ruleset_packaging import RulesetPackagingService
from dealbrain_core.rules.packaging import (
    RulesetPackage,
    create_package_metadata,
)

console = Console()
rules_app = typer.Typer(help="Manage valuation rules")


@rules_app.command("list")
def list_rules(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    ruleset: Optional[str] = typer.Option(None, "--ruleset", "-r", help="Filter by ruleset name"),
    active_only: bool = typer.Option(False, "--active", help="Show only active rules"),
) -> None:
    """List all valuation rules"""

    async def runner() -> None:
        async with session_scope() as session:
            service = RulesService()

            # Get rulesets
            rulesets = await service.list_rulesets(
                session=session, active_only=active_only, skip=0, limit=100
            )

            # Filter by name if provided
            if ruleset:
                rulesets = [rs for rs in rulesets if ruleset.lower() in rs.name.lower()]

            for rs in rulesets:
                console.print(f"\n[bold cyan]Ruleset:[/bold cyan] {rs.name} (v{rs.version})")
                console.print(f"  [dim]ID: {rs.id} | Active: {rs.is_active}[/dim]")

                # Get groups for this ruleset
                groups = await service.list_rule_groups(
                    session=session, ruleset_id=rs.id, category=category
                )

                for group in groups:
                    console.print(
                        f"\n  [bold yellow]└─ {group.category}:[/bold yellow] {group.name}"
                    )
                    console.print(f"     [dim]ID: {group.id} | Weight: {group.weight}[/dim]")

                    # Get rules for this group
                    rules = await service.list_rules(
                        session=session,
                        group_id=group.id,
                        active_only=active_only,
                        skip=0,
                        limit=100,
                    )

                    if rules:
                        table = Table(show_header=True, header_style="bold")
                        table.add_column("ID", style="dim")
                        table.add_column("Name")
                        table.add_column("Priority")
                        table.add_column("Active")
                        table.add_column("Conditions")
                        table.add_column("Actions")

                        for rule in rules:
                            table.add_row(
                                str(rule.id),
                                rule.name,
                                str(rule.priority),
                                "✓" if rule.is_active else "✗",
                                str(len(rule.conditions)),
                                str(len(rule.actions)),
                            )

                        console.print("     ")
                        console.print(table)

    asyncio.run(runner())


@rules_app.command("show")
def show_rule(rule_id: int) -> None:
    """Show detailed information about a rule"""

    async def runner() -> None:
        async with session_scope() as session:
            service = RulesService()
            rule = await service.get_rule(session, rule_id)

            if not rule:
                console.print(f"[red]Rule {rule_id} not found[/red]")
                raise typer.Exit(code=1)

            console.print(f"\n[bold cyan]Rule #{rule.id}:[/bold cyan] {rule.name}")
            console.print(
                f"[dim]Group ID: {rule.group_id} | Priority: {rule.priority} | Active: {rule.is_active}[/dim]"
            )

            if rule.description:
                console.print(f"\n[bold]Description:[/bold] {rule.description}")

            # Conditions
            if rule.conditions:
                console.print("\n[bold yellow]Conditions:[/bold yellow]")
                for i, cond in enumerate(rule.conditions, 1):
                    console.print(f"  {i}. {cond.field_name} {cond.operator} {cond.value_json}")
                    if cond.logical_operator:
                        console.print(f"     [dim]({cond.logical_operator})[/dim]")

            # Actions
            if rule.actions:
                console.print("\n[bold green]Actions:[/bold green]")
                for i, action in enumerate(rule.actions, 1):
                    console.print(f"  {i}. Type: {action.action_type}")
                    if action.value_usd:
                        console.print(f"     Value: ${action.value_usd}")
                    if action.formula:
                        console.print(f"     Formula: {action.formula}")
                    if action.modifiers_json:
                        console.print(
                            f"     Modifiers: {json.dumps(action.modifiers_json, indent=2)}"
                        )

            # Metadata
            if rule.metadata_json:
                console.print(
                    f"\n[bold]Metadata:[/bold]\n{json.dumps(rule.metadata_json, indent=2)}"
                )

    asyncio.run(runner())


@rules_app.command("create")
def create_rule(
    file: Path = typer.Option(..., "--from-file", "-f", help="Path to YAML rule definition"),
) -> None:
    """Create a new rule from a YAML file"""

    async def runner() -> None:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(code=1)

        # Load YAML
        with open(file) as f:
            data = yaml.safe_load(f)

        async with session_scope() as session:
            service = RulesService()

            # Create rule
            rule = await service.create_rule(
                session=session,
                group_id=data["group_id"],
                name=data["name"],
                description=data.get("description"),
                priority=data.get("priority", 100),
                evaluation_order=data.get("evaluation_order", 100),
                conditions=data.get("conditions", []),
                actions=data.get("actions", []),
                metadata=data.get("metadata", {}),
            )

            console.print(f"[green]✓[/green] Created rule #{rule.id}: {rule.name}")

    asyncio.run(runner())


@rules_app.command("update")
def update_rule(
    rule_id: int,
    file: Path = typer.Option(..., "--file", "-f", help="Path to YAML with updates"),
) -> None:
    """Update a rule from a YAML file"""

    async def runner() -> None:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(code=1)

        # Load YAML
        with open(file) as f:
            updates = yaml.safe_load(f)

        async with session_scope() as session:
            service = RulesService()

            rule = await service.update_rule(session, rule_id, updates)
            if not rule:
                console.print(f"[red]Rule {rule_id} not found[/red]")
                raise typer.Exit(code=1)

            console.print(f"[green]✓[/green] Updated rule #{rule.id}: {rule.name}")

    asyncio.run(runner())


@rules_app.command("import")
def import_rules(
    file: Path,
    format: str = typer.Option("json", "--format", "-f", help="Format: json, yaml, csv"),
    mapping: Optional[Path] = typer.Option(
        None, "--mapping", "-m", help="Field mapping file (for CSV)"
    ),
) -> None:
    """Import rules from a file"""

    async def runner() -> None:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(code=1)

        console.print(f"Importing rules from {file} (format: {format})...")

        # Load file based on format
        with open(file) as f:
            if format == "json":
                data = json.load(f)
            elif format == "yaml":
                data = yaml.safe_load(f)
            elif format == "csv":
                console.print("[yellow]CSV import not yet implemented[/yellow]")
                raise typer.Exit(code=1)
            else:
                console.print(f"[red]Unsupported format: {format}[/red]")
                raise typer.Exit(code=1)

        # TODO: Implement actual import logic
        console.print(f"[yellow]Import functionality to be implemented[/yellow]")

    asyncio.run(runner())


@rules_app.command("export")
def export_rules(
    format: str = typer.Option("json", "--format", "-f", help="Format: json, yaml, csv"),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path"),
    ruleset_id: Optional[int] = typer.Option(None, "--ruleset", "-r", help="Ruleset ID to export"),
) -> None:
    """Export rules to a file"""

    async def runner() -> None:
        async with session_scope() as session:
            service = RulesService()

            if ruleset_id:
                ruleset = await service.get_ruleset(session, ruleset_id)
                if not ruleset:
                    console.print(f"[red]Ruleset {ruleset_id} not found[/red]")
                    raise typer.Exit(code=1)

                # Export ruleset structure
                export_data = {
                    "ruleset": {
                        "id": ruleset.id,
                        "name": ruleset.name,
                        "version": ruleset.version,
                        "description": ruleset.description,
                    },
                    "rule_groups": [],
                    "rules": [],
                }

                for group in ruleset.rule_groups:
                    export_data["rule_groups"].append(
                        {
                            "id": group.id,
                            "name": group.name,
                            "category": group.category,
                            "weight": float(group.weight) if group.weight else 1.0,
                        }
                    )

                    for rule in group.rules:
                        export_data["rules"].append(
                            {
                                "id": rule.id,
                                "group_id": rule.group_id,
                                "name": rule.name,
                                "description": rule.description,
                                "priority": rule.priority,
                                "conditions": [
                                    {
                                        "field_name": c.field_name,
                                        "operator": c.operator,
                                        "value": c.value_json,
                                    }
                                    for c in rule.conditions
                                ],
                                "actions": [
                                    {
                                        "action_type": a.action_type,
                                        "value_usd": float(a.value_usd) if a.value_usd else None,
                                        "formula": a.formula,
                                    }
                                    for a in rule.actions
                                ],
                            }
                        )
            else:
                # Export all rules
                rulesets = await service.list_rulesets(
                    session, active_only=False, skip=0, limit=1000
                )
                export_data = {"rulesets": [rs.name for rs in rulesets]}

            # Write to file
            with open(output, "w") as f:
                if format == "json":
                    json.dump(export_data, f, indent=2)
                elif format == "yaml":
                    yaml.dump(export_data, f, default_flow_style=False)
                else:
                    console.print(f"[red]Unsupported format: {format}[/red]")
                    raise typer.Exit(code=1)

            console.print(f"[green]✓[/green] Exported to {output}")

    asyncio.run(runner())


@rules_app.command("preview")
def preview_rule(
    rule_id: int, sample_size: int = typer.Option(10, help="Number of sample listings")
) -> None:
    """Preview the impact of a rule"""

    async def runner() -> None:
        async with session_scope() as session:
            service = RulesService()
            rule = await service.get_rule(session, rule_id)

            if not rule:
                console.print(f"[red]Rule {rule_id} not found[/red]")
                raise typer.Exit(code=1)

            preview_service = RulePreviewService()

            conditions = [
                {
                    "field_name": c.field_name,
                    "field_type": c.field_type,
                    "operator": c.operator,
                    "value": c.value_json,
                }
                for c in rule.conditions
            ]

            actions = [
                {
                    "action_type": a.action_type,
                    "value_usd": float(a.value_usd) if a.value_usd else None,
                    "formula": a.formula,
                }
                for a in rule.actions
            ]

            result = await preview_service.preview_rule(
                session=session, conditions=conditions, actions=actions, sample_size=sample_size
            )

            console.print(f"\n[bold]Preview for Rule:[/bold] {rule.name}")
            console.print(f"\n[bold cyan]Statistics:[/bold cyan]")
            for key, value in result["statistics"].items():
                console.print(f"  {key}: {value}")

            if result["sample_matched_listings"]:
                console.print("\n[bold green]Sample Matched Listings:[/bold green]")
                table = Table(show_header=True)
                table.add_column("ID")
                table.add_column("Title")
                table.add_column("Original Price")
                table.add_column("Adjustment")
                table.add_column("Adjusted Price")

                for listing in result["sample_matched_listings"][:5]:
                    table.add_row(
                        str(listing["id"]),
                        listing["title"][:40],
                        f"${listing['original_price']:.2f}",
                        f"${listing.get('adjustment', 0):.2f}",
                        f"${listing.get('adjusted_price', 0):.2f}",
                    )

                console.print(table)

    asyncio.run(runner())


@rules_app.command("apply")
def apply_ruleset(
    ruleset_name: str,
    category: Optional[str] = typer.Option(None, help="Filter listings by category"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Preview without applying"),
) -> None:
    """Apply a ruleset to listings"""

    async def runner() -> None:
        async with session_scope() as session:
            # Find ruleset by name
            result = await session.execute(
                select(ValuationRuleset).where(ValuationRuleset.name == ruleset_name)
            )
            ruleset = result.scalar_one_or_none()

            if not ruleset:
                console.print(f"[red]Ruleset '{ruleset_name}' not found[/red]")
                raise typer.Exit(code=1)

            if dry_run:
                console.print(
                    f"[yellow]DRY RUN:[/yellow] Would apply ruleset '{ruleset.name}' (ID: {ruleset.id})"
                )
                console.print("Run with --no-dry-run to apply changes")
            else:
                console.print(f"Applying ruleset '{ruleset.name}' to listings...")

                service = RuleEvaluationService()
                result = await service.apply_ruleset_to_all_listings(session, ruleset.id)

                console.print(
                    f"[green]✓[/green] Applied to {result.get('listings_processed', 0)} listings"
                )

    asyncio.run(runner())


@rules_app.command("package")
def package_ruleset(
    ruleset_name: str,
    output: Path = typer.Option(..., "--output", "-o", help="Output .dbrs file path"),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Package version"),
    author: str = typer.Option("Unknown", "--author", "-a", help="Package author"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Package description"
    ),
) -> None:
    """Package a ruleset for distribution"""

    async def runner() -> None:
        async with session_scope() as session:
            # Find ruleset by name
            result = await session.execute(
                select(ValuationRuleset).where(ValuationRuleset.name == ruleset_name)
            )
            ruleset = result.scalar_one_or_none()

            if not ruleset:
                console.print(f"[red]Ruleset '{ruleset_name}' not found[/red]")
                raise typer.Exit(code=1)

            console.print(f"Packaging ruleset '{ruleset.name}'...")

            service = RulesetPackagingService()
            metadata = create_package_metadata(
                name=ruleset.name,
                version=version,
                author=author,
                description=description or ruleset.description or "",
                min_app_version="1.0.0",
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Creating package...", total=None)

                package = await service.export_ruleset_to_package(
                    session=session,
                    ruleset_id=ruleset.id,
                    metadata=metadata,
                    include_examples=False,
                )

                progress.update(task, description="Writing package file...")
                package.to_file(output)

            console.print(f"[green]✓[/green] Package created: {output}")
            console.print(f"  Rulesets: {len(package.rulesets)}")
            console.print(f"  Rule Groups: {len(package.rule_groups)}")
            console.print(f"  Rules: {len(package.rules)}")
            console.print(f"  Size: {output.stat().st_size / 1024:.1f} KB")

    asyncio.run(runner())


@rules_app.command("install")
def install_package(
    file: Path,
    merge_strategy: str = typer.Option(
        "replace", "--strategy", help="Merge strategy: replace, skip, merge"
    ),
) -> None:
    """Install a ruleset package from a .dbrs file"""

    async def runner() -> None:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(code=1)

        console.print(f"Installing package from {file}...")

        # Load package
        package = RulesetPackage.from_file(file)

        console.print(
            f"\n[bold cyan]Package:[/bold cyan] {package.metadata.name} v{package.metadata.version}"
        )
        console.print(f"[dim]Author: {package.metadata.author}[/dim]")
        console.print(f"[dim]Description: {package.metadata.description}[/dim]")

        async with session_scope() as session:
            service = RulesetPackagingService()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Installing package...", total=None)

                result = await service.install_package(
                    session=session, package=package, actor="cli", merge_strategy=merge_strategy
                )

                progress.update(task, description="Installation complete")

            console.print(f"\n[green]✓[/green] Installation successful!")
            console.print(f"  Rulesets created: {result['rulesets_created']}")
            console.print(f"  Rulesets updated: {result['rulesets_updated']}")
            console.print(f"  Rule groups created: {result['rule_groups_created']}")
            console.print(f"  Rules created: {result['rules_created']}")

            if result.get("warnings"):
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result["warnings"]:
                    console.print(f"  • {warning}")

    asyncio.run(runner())


if __name__ == "__main__":
    rules_app()
