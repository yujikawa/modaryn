from rich.console import Console
from rich.table import Table
from typing import Optional, List

from ..domain.model import DbtProject, DbtModel, ScoreStatistics
from . import OutputGenerator


class TerminalOutput(OutputGenerator):
    def __init__(self):
        self.console = Console()

    def generate_report(self, project: DbtProject, problematic_models: Optional[List[DbtModel]] = None, threshold: Optional[float] = None, apply_zscore: bool = False, statistics: Optional[ScoreStatistics] = None) -> Optional[str]:
        table = Table(title="dbt Models Score and Scan Results", expand=True)
        table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
        table.add_column("Model Name", justify="left", style="white", ratio=1, no_wrap=False)

        if apply_zscore:
            table.add_column("Score(Z)", justify="right", style="green", no_wrap=True)
            sort_key = lambda m: m.score if m.score is not None else -1
            score_attr = "score"
        else:
            table.add_column("Score(Raw)", justify="right", style="green", no_wrap=True)
            sort_key = lambda m: m.raw_score if m.raw_score is not None else -1
            score_attr = "raw_score"
        
        table.add_column("Qual.", justify="right", style="magenta", no_wrap=True)
        table.add_column("JOINs", justify="right", style="blue", no_wrap=True)
        table.add_column("CTEs", justify="right", style="blue", no_wrap=True)
        table.add_column("Cond.", justify="right", style="blue", no_wrap=True)
        table.add_column("WHERs", justify="right", style="blue", no_wrap=True)
        table.add_column("Chars", justify="right", style="blue", no_wrap=True)
        table.add_column("Down.", justify="right", style="yellow", no_wrap=True)
        table.add_column("C-Down", justify="right", style="yellow", no_wrap=True)
        table.add_column("Tests", justify="right", style="yellow", no_wrap=True)
        table.add_column("Cov.%", justify="right", style="yellow", no_wrap=True)

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
                f"{model.quality_score:.2f}",
                join_count,
                cte_count,
                conditional_count,
                where_count,
                sql_char_count,
                str(model.downstream_model_count),
                str(model.downstream_column_count),
                str(model.test_count),
                f"{model.column_test_coverage:.1f}%",
            )
        
        self.console.print(table)

        if statistics:
            self.console.print("\n--- Score Statistics ---")
            self.console.print(f"Mean: {statistics.mean:.3f}")
            self.console.print(f"Median: {statistics.median:.3f}")
            self.console.print(f"Standard Deviation: {statistics.std_dev:.3f}")

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
