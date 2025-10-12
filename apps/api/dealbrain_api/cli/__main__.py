"""Module entry-point for python -m dealbrain_api.cli."""

from . import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
