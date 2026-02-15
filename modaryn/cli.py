import typer
from pathlib import Path
from rich.console import Console # Keep Console for general messages
from typing import Optional
from enum import Enum

from modaryn.loaders.manifest import ManifestLoader
from modaryn.scorers.score import Scorer
from modaryn.outputs.terminal import TerminalOutput
from modaryn.outputs.markdown import MarkdownOutput
from modaryn.outputs.html import HtmlOutput
from modaryn.outputs.logo import display_logo_and_version
from modaryn.outputs import OutputGenerator # Import the base class for type hinting


class OutputFormat(str, Enum):
    terminal = "terminal"
    markdown = "markdown"
    html = "html"


__version__ = "0.1.0" # Define version here

app = typer.Typer(
    help="A CLI to analyze dbt projects and score model complexity."
)
app.info.version = __version__ # Set version directly on app.info
console = Console() # Keep for general messages

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    modaryn analyzes dbt projects to score model complexity and structural importance.
    """
    if ctx.invoked_subcommand is None:
        display_logo_and_version(app.info.version)


@app.command()
def score(
    project_path: Path = typer.Option(
        ".",
        "--project-path",
        "-p",
        help="Path to the dbt project directory.",
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
    apply_zscore: bool = typer.Option(
        False,
        "--apply-zscore",
        "-z",
        help="Apply Z-score transformation to model scores.",
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
    Analyzes and scores dbt models based on complexity and importance, displaying combined scan and score information.
    """
    console.print(f"🔍 Loading dbt project: [bold cyan]{project_path}[/bold cyan]")
    try:
        loader = ManifestLoader(project_path, dialect=dialect)
        project = loader.load()
    except Exception as e:
        console.print(f"[bold red]Error loading manifest file: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"⚖️  Scoring project...")
    scorer = Scorer(config)
    scorer.score_project(project, apply_zscore=apply_zscore)

    output_generator: OutputGenerator
    if format == OutputFormat.terminal:
        output_generator = TerminalOutput()
    elif format == OutputFormat.markdown:
        output_generator = MarkdownOutput()
    elif format == OutputFormat.html:
        output_generator = HtmlOutput()
    else:
        # This case should ideally not be reached due to Enum validation
        console.print(f"[bold red]Unsupported output format: {format.value}[/bold red]")
        raise typer.Exit(code=1)
    
    report_content = output_generator.generate_report(project, apply_zscore=apply_zscore)

    if report_content:
        if output:
            with open(output, "w") as f:
                f.write(report_content)
            console.print(f"✅ Report saved to [bold cyan]{output}[/bold cyan]")
        else:
            print(report_content)
    else:
        if output:
            console.print("[bold yellow]Warning: --output is only supported for file-based formats. Printing to terminal.[/bold yellow]")


@app.command()
def ci_check(
    project_path: Path = typer.Option(
        ".",
        "--project-path",
        "-p",
        help="Path to the dbt project directory.",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    threshold: float = typer.Option(
        ..., # ... means required
        "--threshold",
        "-t",
        help="The maximum allowed Z-score for models. CI will fail if any model exceeds this.",
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
    Checks dbt model complexity against a defined Z-score threshold for CI pipelines.
    Exits with code 1 if any model's score exceeds the threshold, 0 otherwise.
    """
    console.print(f"🔍 Loading dbt project: [bold cyan]{project_path}[/bold cyan]")
    try:
        loader = ManifestLoader(project_path, dialect=dialect)
        project = loader.load()
    except Exception as e:
        console.print(f"[bold red]Error loading manifest file: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"⚖️  Scoring project and checking thresholds...")
    scorer = Scorer(config)
    scorer.score_project(project, apply_zscore=True) # Always use Z-score for CI check

    problematic_models = [model for model in project.models.values() if model.score > threshold]

    exit_code: int
    if problematic_models:
        console.print(f"[bold red]❌ Threshold exceeded by {len(problematic_models)} models:[/bold red]")
        for model in problematic_models:
            console.print(f"  - [red]{model.model_name}[/red] (Score: {model.score:.3f} > Threshold: {threshold:.3f})")
        exit_code = 1
    else:
        console.print("[bold green]✅ All models are within the defined threshold.[/bold green]")
        exit_code = 0

    output_generator: OutputGenerator
    if format == OutputFormat.terminal:
        output_generator = TerminalOutput()
    elif format == OutputFormat.markdown:
        output_generator = MarkdownOutput()
    elif format == OutputFormat.html:
        output_generator = HtmlOutput()
    else:
        console.print(f"[bold red]Unsupported output format: {format.value}[/bold red]")
        raise typer.Exit(code=1)
    
    report_content = output_generator.generate_report(project, problematic_models, threshold, apply_zscore=True)

    if report_content:
        if output:
            with open(output, "w") as f:
                f.write(report_content)
            console.print(f"✅ Report saved to [bold cyan]{output}[/bold cyan]")
        else:
            print(report_content)
    else:
        if output:
            console.print("[bold yellow]Warning: --output is only supported for file-based formats. Printing to terminal.[/bold yellow]")

    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()