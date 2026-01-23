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
from modaryn.outputs import OutputGenerator # Import the base class for type hinting


class OutputFormat(str, Enum):
    terminal = "terminal"
    markdown = "markdown"
    html = "html"


app = typer.Typer(help="A CLI to analyze dbt projects and score model complexity.")
console = Console() # Keep for general messages

@app.callback()
def main():
    """
    modaryn analyzes dbt projects to score model complexity and structural importance.
    """
    pass

@app.command()
def scan(
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
    console.print(f"🔍 Scanning dbt project: [bold cyan]{project_path}[/bold cyan]")

    try:
        loader = ManifestLoader(project_path, dialect=dialect)
        project = loader.load()
    except Exception as e:
        console.print(f"[bold red]Error loading manifest file: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"✅ Found [bold]{len(project.models)}[/bold] models.")

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

    report_content = output_generator.generate_scan_report(project)

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
from modaryn.outputs import OutputGenerator # Import the base class for type hinting


class OutputFormat(str, Enum):
    terminal = "terminal"
    markdown = "markdown"
    html = "html"


app = typer.Typer(help="A CLI to analyze dbt projects and score model complexity.")
console = Console() # Keep for general messages

@app.callback()
def main():
    """
    modaryn analyzes dbt projects to score model complexity and structural importance.
    """
    pass

@app.command()
def scan(
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
    console.print(f"🔍 Scanning dbt project: [bold cyan]{project_path}[/bold cyan]")

    try:
        loader = ManifestLoader(project_path, dialect=dialect)
        project = loader.load()
    except Exception as e:
        console.print(f"[bold red]Error loading manifest file: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"✅ Found [bold]{len(project.models)}[/bold] models.")

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

    report_content = output_generator.generate_scan_report(project)

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
    console.print(f"🔍 Loading dbt project: [bold cyan]{project_path}[/bold cyan]")
    try:
        loader = ManifestLoader(project_path, dialect=dialect)
        project = loader.load()
    except Exception as e:
        console.print(f"[bold red]Error loading manifest file: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"⚖️  Scoring project...")
    scorer = Scorer(config)
    scorer.score_project(project)

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
    
    report_content = output_generator.generate_score_report(project)

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

if __name__ == "__main__":
    app()
    scorer = Scorer(config)
    scorer.score_project(project)

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
    
    report_content = output_generator.generate_score_report(project)

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

if __name__ == "__main__":
    app()