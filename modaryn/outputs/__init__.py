from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from modaryn.domain.model import DbtProject, DbtModel, ScoreStatistics


def _extract_complexity_fields(model: DbtModel) -> Tuple[str, str, str, str, str]:
    """Returns (join_count, cte_count, conditional_count, where_count, sql_char_count) as strings."""
    if model.complexity:
        return (
            str(model.complexity.join_count),
            str(model.complexity.cte_count),
            str(model.complexity.conditional_count),
            str(model.complexity.where_count),
            str(model.complexity.sql_char_count),
        )
    return "N/A", "N/A", "N/A", "N/A", "N/A"


class OutputGenerator(ABC):
    @abstractmethod
    def generate_report(self, project: DbtProject, problematic_models: Optional[List[DbtModel]] = None, threshold: Optional[float] = None, apply_zscore: bool = False, statistics: Optional[ScoreStatistics] = None) -> Optional[str]:
        """
        Generates a combined scan and score report for the given DbtProject.
        Returns a string for file-based formats, or None if printing directly to console.
        """
        pass
