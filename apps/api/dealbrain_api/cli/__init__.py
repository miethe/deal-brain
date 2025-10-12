"""Deal Brain CLI entrypoint."""

from typer import Typer

from . import baselines


app = Typer(help="Deal Brain command line utilities.")
app.add_typer(baselines.app, name="baselines")


__all__ = ["app"]
