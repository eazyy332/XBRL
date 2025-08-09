import sys
import json
import pathlib
from typing import Optional

import typer
from rich.console import Console

from xbrlval.core.validation import ValidationEngine
from xbrlval.reporting.report import ValidationReport
from xbrlval.api.server import run_api

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def validate(
    input: str = typer.Argument(..., help="Path or URL to XBRL instance or iXBRL document"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON report to stdout"),
    sarif_out: Optional[pathlib.Path] = typer.Option(None, "--sarif", help="Write SARIF report to file"),
    calc: bool = typer.Option(True, help="Run calculation linkbase checks if available"),
    all_rules: bool = typer.Option(True, help="Run all implemented validation rules"),
    cache_dir: pathlib.Path = typer.Option(pathlib.Path(".xbrl_cache"), help="Cache directory for fetched resources"),
):
    engine = ValidationEngine(cache_dir=cache_dir)
    report: ValidationReport = engine.validate(input, run_calculation=calc, run_all=all_rules)

    if json_out:
        console.print_json(data=report.to_dict())
    else:
        for issue in report.issues:
            level = issue.severity.upper()
            console.print(f"[{level}] {issue.code}: {issue.message}")

    if sarif_out:
        sarif_data = report.to_sarif()
        sarif_out.write_text(json.dumps(sarif_data))

    if report.has_errors:
        raise typer.Exit(code=2)


@app.command()
def api(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8080, "--port"),
    cache_dir: pathlib.Path = typer.Option(pathlib.Path(".xbrl_cache")),
):
    run_api(host=host, port=port, cache_dir=cache_dir)


if __name__ == "__main__":
    app()