"""Import utilities for Deal Brain."""

# Exported names are kept lazy so the CLI can run without notebooks dependencies
# (notably pandas) unless the spreadsheet importer is actually needed.
__all__ = ["SpreadsheetImporter", "ImportSummary"]


def __getattr__(name: str):  # pragma: no cover - simple delegation helper
    if name in __all__:
        from .excel import ImportSummary, SpreadsheetImporter

        return {"SpreadsheetImporter": SpreadsheetImporter, "ImportSummary": ImportSummary}[name]
    raise AttributeError(f"module {__name__} has no attribute {name!r}")


def __dir__() -> list[str]:  # pragma: no cover - convenience for introspection
    return sorted(__all__)
