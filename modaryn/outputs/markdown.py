from typing import Optional

from modaryn.domain.model import DbtProject
from . import OutputGenerator


class MarkdownOutput(OutputGenerator):
    def generate_report(self, project: DbtProject) -> Optional[str]:
        lines = [
            "# Modaryn Score and Scan Report",
            "",
            "| Rank | Model Name | Score (Z-Score) | JOINs | CTEs | Conditionals | WHEREs | SQL Chars | Downstream Children |",
            "|------|------------|-----------------|-------|------|--------------|--------|-----------|---------------------|",
        ]
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

            lines.append(
                f"| {i + 1} | {model.model_name} | {model.score:.2f} | {join_count} | {cte_count} | {conditional_count} | {where_count} | {sql_char_count} | {model.downstream_model_count} |"
            )
        return "\n".join(lines)

