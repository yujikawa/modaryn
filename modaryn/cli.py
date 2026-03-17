import warnings
import typer
from pathlib import Path
from rich.console import Console # Keep Console for general messages
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
from typing import Optional
from enum import Enum

from modaryn.loaders.manifest import ManifestLoader
from modaryn.analyzers.lineage import LineageAnalyzer
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
    dialect: Optional[str] = typer.Option(
        None,
        "--dialect",
        "-d",
        help="The SQL dialect to use for parsing (e.g. bigquery, snowflake, duckdb). Auto-detected from manifest.json if not specified.",
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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed warnings (e.g. columns skipped during lineage analysis).",
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

    resolved_dialect = loader.dialect
    if not dialect:
        console.print(f"🔎 Auto-detected SQL dialect: [bold cyan]{resolved_dialect}[/bold cyan] (use --dialect to override)")

    lineage_analyzer = LineageAnalyzer(dialect=resolved_dialect)
    total_models = len(project.models)
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), MofNCompleteColumn(), console=console, transient=True) as progress:
            task = progress.add_task(f"📊 Analyzing column-level lineage ({total_models} models)...", total=total_models)
            lineage_analyzer.analyze(project, on_progress=lambda cur, _total: progress.update(task, completed=cur))
    lineage_warnings = [w for w in caught_warnings if issubclass(w.category, UserWarning)]
    if lineage_warnings and verbose:
        for w in lineage_warnings:
            console.print(f"  [yellow]⚠ {w.message}[/yellow]")
    if lineage_warnings:
        console.print(f"📊 Column-level lineage analysis complete. [yellow]({len(lineage_warnings)} column(s) skipped — use --verbose for details)[/yellow]")
    else:
        console.print(f"📊 Column-level lineage analysis complete.")

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
    
    report_content = output_generator.generate_report(project, apply_zscore=apply_zscore, statistics=project.statistics)

    if report_content:
        if output:
            with open(output, "w") as f:
                f.write(report_content)
            console.print(f"✅ Report saved to [bold cyan]{output}[/bold cyan]")
        else:
            print(report_content)
    else:
        if output:
            console.print("[bold yellow]Warning: --output is ignored when using terminal format. Use -f markdown or -f html to save to a file.[/bold yellow]")


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
    dialect: Optional[str] = typer.Option(
        None,
        "--dialect",
        "-d",
        help="The SQL dialect to use for parsing (e.g. bigquery, snowflake, duckdb). Auto-detected from manifest.json if not specified.",
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
        help="Use Z-scores instead of raw scores for threshold checking and output.",
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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed warnings (e.g. columns skipped during lineage analysis).",
    ),
):
    """
    Checks dbt model complexity against a defined score threshold for CI pipelines.
    By default, uses raw scores. Use --apply-zscore to check against Z-scores.
    Exits with code 1 if any model's score exceeds the threshold, 0 otherwise.
    """
    console.print(f"🔍 Loading dbt project: [bold cyan]{project_path}[/bold cyan]")
    try:
        loader = ManifestLoader(project_path, dialect=dialect)
        project = loader.load()
    except Exception as e:
        console.print(f"[bold red]Error loading manifest file: {e}[/bold red]")
        raise typer.Exit(code=1)

    resolved_dialect = loader.dialect
    if not dialect:
        console.print(f"🔎 Auto-detected SQL dialect: [bold cyan]{resolved_dialect}[/bold cyan] (use --dialect to override)")

    lineage_analyzer = LineageAnalyzer(dialect=resolved_dialect)
    total_models = len(project.models)
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), MofNCompleteColumn(), console=console, transient=True) as progress:
            task = progress.add_task(f"📊 Analyzing column-level lineage ({total_models} models)...", total=total_models)
            lineage_analyzer.analyze(project, on_progress=lambda cur, _total: progress.update(task, completed=cur))
    lineage_warnings = [w for w in caught_warnings if issubclass(w.category, UserWarning)]
    if lineage_warnings and verbose:
        for w in lineage_warnings:
            console.print(f"  [yellow]⚠ {w.message}[/yellow]")
    if lineage_warnings:
        console.print(f"📊 Column-level lineage analysis complete. [yellow]({len(lineage_warnings)} column(s) skipped — use --verbose for details)[/yellow]")
    else:
        console.print(f"📊 Column-level lineage analysis complete.")

    console.print(f"⚖️  Scoring project and checking thresholds...")
    scorer = Scorer(config)
    scorer.score_project(project, apply_zscore=apply_zscore)

    problematic_models = []
    if apply_zscore:
        # Check against z-score if --apply-zscore is specified
        problematic_models = [model for model in project.models.values() if model.score > threshold]
    else:
        # Default to raw score
        problematic_models = [model for model in project.models.values() if model.raw_score > threshold]

    exit_code: int
    if problematic_models:
        console.print(f"[bold red]❌ Threshold exceeded by {len(problematic_models)} models:[/bold red]")
        for model in problematic_models:
            score_value = model.score if apply_zscore else model.raw_score
            console.print(f"  - [red]{model.model_name}[/red] (Score: {score_value:.3f} > Threshold: {threshold:.3f})")
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
    
    report_content = output_generator.generate_report(project, problematic_models, threshold, apply_zscore=apply_zscore, statistics=project.statistics)

    if report_content:
        if output:
            with open(output, "w") as f:
                f.write(report_content)
            console.print(f"✅ Report saved to [bold cyan]{output}[/bold cyan]")
        else:
            print(report_content)
    else:
        if output:
            console.print("[bold yellow]Warning: --output is ignored when using terminal format. Use -f markdown or -f html to save to a file.[/bold yellow]")

    raise typer.Exit(code=exit_code)


@app.command()
def impact(
    project_path: Path = typer.Option(
        ".",
        "--project-path",
        "-p",
        help="Path to the dbt project directory.",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    model: str = typer.Option(
        ...,
        "--model",
        "-m",
        help="Model name to trace impact from.",
    ),
    column: str = typer.Option(
        ...,
        "--column",
        "-c",
        help="Column name to trace impact from.",
    ),
    dialect: Optional[str] = typer.Option(
        None,
        "--dialect",
        "-d",
        help="The SQL dialect to use for parsing (e.g. bigquery, snowflake, duckdb). Auto-detected from manifest.json if not specified.",
        case_sensitive=False,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed warnings (e.g. columns skipped during lineage analysis).",
    ),
):
    """
    Shows all downstream columns affected by a change to a specific column (column-level impact analysis).
    """
    from collections import deque

    console.print(f"🔍 Loading dbt project: [bold cyan]{project_path}[/bold cyan]")
    try:
        loader = ManifestLoader(project_path, dialect=dialect)
        project = loader.load()
    except Exception as e:
        console.print(f"[bold red]Error loading manifest file: {e}[/bold red]")
        raise typer.Exit(code=1)

    resolved_dialect = loader.dialect
    if not dialect:
        console.print(f"🔎 Auto-detected SQL dialect: [bold cyan]{resolved_dialect}[/bold cyan] (use --dialect to override)")

    lineage_analyzer = LineageAnalyzer(dialect=resolved_dialect)
    total_models = len(project.models)
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), MofNCompleteColumn(), console=console, transient=True) as progress:
            task = progress.add_task(f"📊 Analyzing column-level lineage ({total_models} models)...", total=total_models)
            lineage_analyzer.analyze(project, on_progress=lambda cur, _total: progress.update(task, completed=cur))
    lineage_warnings = [w for w in caught_warnings if issubclass(w.category, UserWarning)]
    if lineage_warnings and verbose:
        for w in lineage_warnings:
            console.print(f"  [yellow]⚠ {w.message}[/yellow]")
    if lineage_warnings:
        console.print(f"📊 Column-level lineage analysis complete. [yellow]({len(lineage_warnings)} column(s) skipped — use --verbose for details)[/yellow]")
    else:
        console.print(f"📊 Column-level lineage analysis complete.")

    # Find the target model
    target_model_obj = next(
        (m for m in project.models.values() if m.model_name == model), None
    )
    if not target_model_obj:
        console.print(f"[bold red]Model '{model}' not found in project.[/bold red]")
        raise typer.Exit(code=1)

    if column not in target_model_obj.columns:
        available = ", ".join(target_model_obj.columns.keys()) or "(none defined)"
        console.print(f"[bold red]Column '{column}' not found in model '{model}'.[/bold red]")
        console.print(f"Available columns: {available}")
        raise typer.Exit(code=1)

    # BFS traversal through downstream column references
    console.print(f"\n[bold]Impact Analysis: [cyan]{model}[/cyan].[green]{column}[/green][/bold]\n")

    visited = set()
    queue = deque([(target_model_obj.unique_id, column, 0)])
    results_by_hop: dict = {}

    while queue:
        current_model_id, current_col, hop = queue.popleft()
        key = (current_model_id, current_col)
        if key in visited:
            continue
        visited.add(key)

        if hop > 0:
            results_by_hop.setdefault(hop, []).append((current_model_id, current_col))

        current_model_obj = project.models.get(current_model_id)
        if current_model_obj and current_col in current_model_obj.columns:
            for ref in current_model_obj.columns[current_col].downstream_columns:
                if (ref.model_unique_id, ref.column_name) not in visited:
                    queue.append((ref.model_unique_id, ref.column_name, hop + 1))

    if not results_by_hop:
        console.print("[yellow]No downstream column references found.[/yellow]")
        console.print("[dim]This may be because lineage could not be resolved for this column.[/dim]")
        raise typer.Exit(code=0)

    total_cols = sum(len(v) for v in results_by_hop.values())
    total_models_affected = len({mid for refs in results_by_hop.values() for mid, _ in refs})

    for hop in sorted(results_by_hop.keys()):
        label = "Direct downstream" if hop == 1 else f"Indirect downstream ({hop} hops)"
        console.print(f"[bold]{label}:[/bold]")
        for model_id, col_name in results_by_hop[hop]:
            model_name_str = project.models[model_id].model_name
            console.print(f"  [cyan]→[/cyan] [white]{model_name_str}[/white].[green]{col_name}[/green]")
        console.print()

    console.print(f"[bold]Total impact:[/bold] {total_cols} column(s) across {total_models_affected} model(s)")


if __name__ == "__main__":
    app()