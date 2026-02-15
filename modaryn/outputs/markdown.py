from typing import Optional, List

from modaryn.domain.model import DbtProject, DbtModel
from . import OutputGenerator


class MarkdownOutput(OutputGenerator):
    def generate_report(self, project: DbtProject, problematic_models: Optional[List[DbtModel]] = None, threshold: Optional[float] = None, apply_zscore: bool = False) -> Optional[str]:
        score_header = "Score (Z-Score)" if apply_zscore else "Score (Raw)"
        sort_key = (lambda m: m.score) if apply_zscore else (lambda m: m.raw_score)
        score_attr = "score" if apply_zscore else "raw_score"

        lines = [
            "# Modaryn Score and Scan Report",
            "",
            f"| Rank | Model Name | {score_header} | JOINs | CTEs | Conditionals | WHEREs | SQL Chars | Downstream Children |",
            "|------|------------|-----------------|-------|------|--------------|--------|-----------|---------------------|",
        ]
        sorted_models = sorted(
            project.models.values(),
            key=lambda m: sort_key(m) if sort_key(m) is not None else -1,
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

            score_to_display = getattr(model, score_attr)
            lines.append(
                f"| {i + 1} | {model.model_name} | {score_to_display:.2f} | {join_count} | {cte_count} | {conditional_count} | {where_count} | {sql_char_count} | {model.downstream_model_count} |"
            )
        return "\n".join(lines)
