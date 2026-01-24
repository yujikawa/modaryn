from rich.console import Console
from rich.table import Table
from typing import Optional

from ..domain.model import DbtProject
from . import OutputGenerator


class TerminalOutput(OutputGenerator):
    def __init__(self):
        self.console = Console()

    def generate_report(self, project: DbtProject) -> Optional[str]:
        table = Table(title="dbt Models Score and Scan Results")
        table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
        table.add_column("Model Name", justify="left", style="magenta")
        table.add_column("Score", justify="right", style="green")
        table.add_column("JOINs", justify="right", style="blue")
        table.add_column("CTEs", justify="right", style="blue")
        table.add_column("Conditionals", justify="right", style="blue")
        table.add_column("WHEREs", justify="right", style="blue")
        table.add_column("SQL Chars", justify="right", style="blue")
        table.add_column("Downstream", justify="right", style="yellow")

        sorted_models = sorted(
            project.models.values(),
            key=lambda m: m.score if m.score is not None else -1, # Handle None scores
            reverse=True,
        )

        for i, model in enumerate(sorted_models):
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
                str(i + 1),
                model.model_name,
                f"{model.score:.2f}" if model.score is not None else "N/A",
                join_count,
                cte_count,
                conditional_count,
                where_count,
                sql_char_count,
                str(model.downstream_model_count),
            )
        
        self.console.print(table)
        return None
