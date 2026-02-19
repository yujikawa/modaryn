from typing import Optional, List

from modaryn.domain.model import DbtProject, DbtModel, ScoreStatistics
from . import OutputGenerator


class MarkdownOutput(OutputGenerator):
    def generate_report(self, project: DbtProject, problematic_models: Optional[List[DbtModel]] = None, threshold: Optional[float] = None, apply_zscore: bool = False, statistics: Optional[ScoreStatistics] = None) -> Optional[str]:
        score_header = "Score (Z-Score)" if apply_zscore else "Score (Raw)"
        sort_key = (lambda m: m.score) if apply_zscore else (lambda m: m.raw_score)
        score_attr = "score" if apply_zscore else "raw_score"

        lines = [
            "# Modaryn Score and Scan Report",
            "",
            f"| Rank | Model Name | {score_header} | Quality Score | JOINs | CTEs | Conditionals | WHEREs | SQL Chars | Downstream Children | Col. Down | Tests | Coverage (%) |",
            "|------|------------|-----------------|---------------|-------|------|--------------|--------|-----------|---------------------|-----------|-------|--------------|",
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
                f"| {i + 1} | {model.model_name} | {score_to_display:.2f} | {model.quality_score:.2f} | {join_count} | {cte_count} | {conditional_count} | {where_count} | {sql_char_count} | {model.downstream_model_count} | {model.downstream_column_count} | {model.test_count} | {model.column_test_coverage:.1f}% |"
            )
        
        if statistics:
            lines.append("\n### Score Statistics")
            lines.append(f"- Mean: {statistics.mean:.3f}")
            lines.append(f"- Median: {statistics.median:.3f}")
            lines.append(f"- Standard Deviation: {statistics.std_dev:.3f}")

        if threshold is not None:
            lines.append("\n### CI Check Summary")
            if problematic_models:
                lines.append(f"**Status: FAILED** - {len(problematic_models)} models exceeded threshold.")
            else:
                lines.append("**Status: PASSED** - All models are within the defined threshold.")
            lines.append(f"Total models checked: {len(project.models)}")
            lines.append(f"Threshold: {threshold:.3f}")
        
        return "\n".join(lines)
