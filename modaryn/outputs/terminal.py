from rich.console import Console
from rich.table import Table
from typing import Optional, List

from ..domain.model import DbtProject, DbtModel
from . import OutputGenerator


class TerminalOutput(OutputGenerator):
    def __init__(self):
        self.console = Console()

    def generate_report(self, project: DbtProject, problematic_models: Optional[List[DbtModel]] = None, threshold: Optional[float] = None, apply_zscore: bool = False) -> Optional[str]:
        table = Table(title="dbt Models Score and Scan Results")
        table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
        table.add_column("Model Name", justify="left", style="white")

        if apply_zscore:
            table.add_column("Score (Z-Score)", justify="right", style="green")
            sort_key = lambda m: m.score if m.score is not None else -1
            score_attr = "score"
        else:
            table.add_column("Score (Raw)", justify="right", style="green")
            sort_key = lambda m: m.raw_score if m.raw_score is not None else -1
            score_attr = "raw_score"

        table.add_column("JOINs", justify="right", style="blue")
        table.add_column("CTEs", justify="right", style="blue")
        table.add_column("Conditionals", justify="right", style="blue")
        table.add_column("WHEREs", justify="right", style="blue")
        table.add_column("SQL Chars", justify="right", style="blue")
        table.add_column("Downstream", justify="right", style="yellow")

        sorted_models = sorted(
            project.models.values(),
            key=sort_key,
            reverse=True,
        )

        problematic_model_names = {model.model_name for model in problematic_models} if problematic_models else set()

        for i, model in enumerate(sorted_models):
            model_name_style = "[red]" if model.model_name in problematic_model_names else ""
            
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

            score_to_display = getattr(model, score_attr)

            table.add_row(
                str(i + 1),
                f"{model_name_style}{model.model_name}[/]" if model_name_style else model.model_name,
                f"{score_to_display:.2f}" if score_to_display is not None else "N/A",
                join_count,
                cte_count,
                conditional_count,
                where_count,
                sql_char_count,
                str(model.downstream_model_count),
            )
        
        self.console.print(table)

        if threshold is not None:
        # Add summary
            self.console.print("\n--- CI Check Summary ---")
            if problematic_models:
                self.console.print(f"[bold red]Status: FAILED[/bold red] - {len(problematic_models)} models exceeded threshold.")
            else:
                self.console.print("[bold green]Status: PASSED[/bold green] - All models are within the defined threshold.")
            self.console.print(f"Total models checked: {len(project.models)}")

            self.console.print(f"Threshold: {threshold:.3f}")
        return None
