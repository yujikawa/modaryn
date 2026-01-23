import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from typing import Optional
from enum import Enum

from modaryn.loaders.manifest import ManifestLoader
from modaryn.outputs.markdown import markdown_output
from modaryn.outputs.html import html_output
from modaryn.scorers.score import Scorer


class OutputFormat(str, Enum):
    terminal = "terminal"
    markdown = "markdown"
    html = "html"


app = typer.Typer(help="A CLI to analyze dbt projects and score model complexity.")
console = Console()

@app.callback()
def main():
    """
    modaryn analyzes dbt projects to score model complexity and structural importance.
    """
    pass

@app.command()
def scan(
    manifest_path: Path = typer.Option(
        "target/manifest.json",
        "--manifest-path",
        "-m",
        help="Path to the dbt manifest.json file",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    dialect: str = typer.Option(
        "bigquery",
        "--dialect",
        "-d",
        help="The SQL dialect to use for parsing.",
        case_sensitive=False,
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.terminal,
        "--format",
        "-f",
        help="Output format.",
        case_sensitive=False,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to write the output file.",
        writable=True,
    ),
):
    """
    Scans a dbt project and displays basic model information.
    """
    console.print(f"🔍 Scanning manifest file: [bold cyan]{manifest_path}[/bold cyan]")

    try:
        loader = ManifestLoader(manifest_path, dialect=dialect)
        project = loader.load()
    except Exception as e:
        console.print(f"[bold red]Error loading manifest file: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"✅ Found [bold]{len(project.models)}[/bold] models.")

    if format == OutputFormat.markdown:
        report = markdown_output(project, scored=False)
        if output:
            with open(output, "w") as f:
                f.write(report)
            console.print(f"✅ Report saved to [bold cyan]{output}[/bold cyan]")
        else:
            print(report)
    elif format == OutputFormat.html:
        console.print("[bold yellow]Warning: HTML output is only supported for the 'score' command.[/bold yellow]")
    else:  # terminal format
        if output:
            console.print("[bold yellow]Warning: --output is only supported for file-based formats. Printing to terminal.[/bold yellow]")
        
        table = Table("Model Name", "JOINs", "CTEs", "Conditionals", "WHEREs", "SQL Chars", "Downstream Children")
        sorted_models = sorted(
            project.models.values(),
            key=lambda m: m.downstream_model_count,
            reverse=True,
        )

        for model in sorted_models:
            if model.complexity:
                join_count = str(model.complexity.join_count)
                cte_count = str(model.complexity.cte_count)
                conditional_count = str(model.complexity.conditional_count)
                where_count = str(model.complexity.where_count)
                sql_char_count = str(model.complexity.sql_char_count)
            else:
                join_count = "N/A"
                cte_count = "N/A"
                conditional_count = "N/A"
                where_count = "N/A"
                sql_char_count = "N/A"

            table.add_row(
                model.model_name,
                join_count,
                cte_count,
                conditional_count,
                where_count,
                sql_char_count,
                str(model.downstream_model_count),
            )

        console.print(table)

@app.command()
def score(
    manifest_path: Path = typer.Option(
        "target/manifest.json",
        "--manifest-path",
        "-m",
        help="Path to the dbt manifest.json file",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    dialect: str = typer.Option(
        "bigquery",
        "--dialect",
        "-d",
        help="The SQL dialect to use for parsing.",
        case_sensitive=False,
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to a custom weights configuration YAML file.",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.terminal,
        "--format",
        "-f",
        help="Output format.",
        case_sensitive=False,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to write the output file.",
        writable=True,
    ),
):
    """
    Scores dbt models based on complexity and importance.
    """
    console.print(f"🔍 Loading manifest file: [bold cyan]{manifest_path}[/bold cyan]")
    try:
        loader = ManifestLoader(manifest_path, dialect=dialect)
        project = loader.load()
    except Exception as e:
        console.print(f"[bold red]Error loading manifest file: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"⚖️  Scoring project...")
    scorer = Scorer(config)
    scorer.score_project(project)

    if format == OutputFormat.html:
        report = html_output(project)
        if not output:
            output = Path("modaryn_report.html")
        with open(output, "w") as f:
            f.write(report)
        console.print(f"✅ HTML report saved to [bold cyan]{output}[/bold cyan]")

    elif format == OutputFormat.markdown:
        report = markdown_output(project, scored=True)
        if output:
            with open(output, "w") as f:
                f.write(report)
            console.print(f"✅ Report saved to [bold cyan]{output}[/bold cyan]")
        else:
            print(report)

    else: # Terminal output
        table = Table("Rank", "Model Name", "Score")
        sorted_models = sorted(
            project.models.values(),
            key=lambda m: m.score,
            reverse=True,
        )

        for i, model in enumerate(sorted_models):
            table.add_row(
                str(i + 1),
                model.model_name,
                f"{model.score:.2f}",
            )
        
        console.print(table)

if __name__ == "__main__":
    app()