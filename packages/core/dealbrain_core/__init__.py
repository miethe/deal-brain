"""Core domain package for Deal Brain."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("deal-brain")
except PackageNotFoundError:  # pragma: no cover - during local dev without install
    __version__ = "0.0.0"

__all__ = ["__version__"]
