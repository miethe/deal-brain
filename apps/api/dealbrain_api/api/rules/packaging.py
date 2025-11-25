"""API endpoints for ruleset packaging (export/import/preview)"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import session_dependency as get_session
from ...schemas.rules import (
    PackageMetadataRequest,
    PackageExportResponse,
    PackageInstallResponse,
)
from ...services.ruleset_packaging import RulesetPackagingService
from dealbrain_core.rules.packaging import RulesetPackage, create_package_metadata


router = APIRouter()


@router.post("/rulesets/{ruleset_id}/package")
async def export_ruleset_package(
    ruleset_id: int,
    request: PackageMetadataRequest,
    session: AsyncSession = Depends(get_session),
):
    """Export a ruleset as a .dbrs package file"""
    service = RulesetPackagingService()

    # Create package metadata
    metadata = create_package_metadata(
        name=request.name,
        version=request.version,
        author=request.author or "Unknown",
        description=request.description or "",
        min_app_version=request.min_app_version,
        required_custom_fields=request.required_custom_fields,
        tags=request.tags or [],
    )

    try:
        # Export to package
        package = await service.export_ruleset_to_package(
            session=session,
            ruleset_id=ruleset_id,
            metadata=metadata,
            include_examples=request.include_examples or False,
        )

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dbrs", delete=False) as tmp:
            tmp.write(package.to_json())
            tmp_path = Path(tmp.name)

        # Return file
        return FileResponse(
            path=str(tmp_path),
            filename=f"{request.name.replace(' ', '_')}_v{request.version}.dbrs",
            media_type="application/json",
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/rulesets/install", response_model=PackageInstallResponse)
async def install_ruleset_package(
    file: UploadFile = File(...),
    actor: str = Query("system", description="User installing the package"),
    merge_strategy: str = Query("replace", description="Conflict resolution strategy"),
    session: AsyncSession = Depends(get_session),
):
    """Install a .dbrs package file"""
    service = RulesetPackagingService()

    try:
        # Read package file
        content = await file.read()
        package = RulesetPackage.from_json(content.decode("utf-8"))

        # Install package
        results = await service.install_package(
            session=session, package=package, actor=actor, merge_strategy=merge_strategy
        )

        return PackageInstallResponse(
            success=True,
            message="Package installed successfully",
            rulesets_created=results["rulesets_created"],
            rulesets_updated=results["rulesets_updated"],
            rule_groups_created=results["rule_groups_created"],
            rules_created=results["rules_created"],
            warnings=results.get("warnings", []),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Installation failed: {str(e)}")


@router.post("/rulesets/{ruleset_id}/package/preview")
async def preview_package_export(
    ruleset_id: int,
    request: PackageMetadataRequest,
    session: AsyncSession = Depends(get_session),
):
    """Preview what will be included in a package export"""
    service = RulesetPackagingService()

    metadata = create_package_metadata(
        name=request.name,
        version=request.version,
        author=request.author or "Unknown",
        description=request.description or "",
        min_app_version=request.min_app_version,
        required_custom_fields=request.required_custom_fields,
        tags=request.tags or [],
    )

    try:
        package = await service.export_ruleset_to_package(
            session=session, ruleset_id=ruleset_id, metadata=metadata, include_examples=False
        )

        dependencies = package.get_dependencies()

        return PackageExportResponse(
            package_name=package.metadata.name,
            package_version=package.metadata.version,
            rulesets_count=len(package.rulesets),
            rule_groups_count=len(package.rule_groups),
            rules_count=len(package.rules),
            custom_fields_count=len(package.custom_field_definitions),
            dependencies=dependencies,
            estimated_size_kb=len(package.to_json()) / 1024,
            readme=package.generate_readme(),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")
