"""Console script for pyxpcsviewer."""
import pyxpcsviewer

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def main():
    """Console script for pyxpcsviewer."""
    console.print("Replace this message by putting your code into "
               "pyxpcsviewer.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    


if __name__ == "__main__":
    app()
