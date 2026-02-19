import yaml
from pathlib import Path
from typing import Dict, List
import numpy as np

from modaryn.domain.model import DbtProject, DbtModel, ScoreStatistics

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "default.yml"


class Scorer:
    def __init__(self, config_path: Path | None = None):
        self.weights = self._load_weights(config_path)

    def _load_weights(self, config_path: Path | None) -> Dict:
        with open(DEFAULT_CONFIG_PATH, "r") as f:
            weights = yaml.safe_load(f)

        if config_path:
            with open(config_path, "r") as f:
                user_weights = yaml.safe_load(f)
            if "sql_complexity" in user_weights:
                weights["sql_complexity"].update(user_weights["sql_complexity"])
            if "importance" in user_weights:
                weights["importance"].update(user_weights["importance"])
            if "quality" in user_weights:
                weights["quality"].update(user_weights["quality"])
        return weights

    def score_project(self, project: DbtProject, apply_zscore: bool = False):
        """Scores all models in a project. Optionally applies Z-scores and calculates score statistics."""
        if not project.models:
            return

        raw_scores_map: Dict[str, float] = {}
        for model in project.models.values():
            model_raw_score = self._calculate_raw_score(model)
            model.raw_score = model_raw_score
            raw_scores_map[model.unique_id] = model_raw_score

        # Calculate statistics for raw scores
        if raw_scores_map:
            raw_score_values: List[float] = list(raw_scores_map.values())
            project.statistics = ScoreStatistics(
                mean=np.mean(raw_score_values),
                median=np.median(raw_score_values),
                std_dev=np.std(raw_score_values)
            )

        if apply_zscore:
            score_values: List[float] = list(raw_scores_map.values()) # Use raw scores for Z-score calculation
            mean_score = np.mean(score_values)
            std_dev = np.std(score_values)

            for model in project.models.values():
                raw_score = raw_scores_map[model.unique_id]
                if std_dev > 0:
                    model.score = (raw_score - mean_score) / std_dev
                else:
                    model.score = 0.0  # All models have the same raw score

    def _calculate_raw_score(self, model: DbtModel) -> float:
        """Calculates a raw, un-normalized score for a single model."""
        sql_complexity_weights = self.weights.get("sql_complexity", {})
        importance_weights = self.weights.get("importance", {})
        quality_weights = self.weights.get("quality", {})

        complexity_score = 0
        if model.complexity:
            complexity_score += model.complexity.join_count * sql_complexity_weights.get("join_count", 0)
            complexity_score += model.complexity.cte_count * sql_complexity_weights.get("cte_count", 0)
            complexity_score += model.complexity.conditional_count * sql_complexity_weights.get("conditional_count", 0)
            complexity_score += model.complexity.where_count * sql_complexity_weights.get("where_count", 0)
            complexity_score += model.complexity.sql_char_count * sql_complexity_weights.get("sql_char_count", 0)

        importance_score = (
            model.downstream_model_count
            * importance_weights.get("downstream_model_count", 0)
        )
        importance_score += (
            model.downstream_column_count
            * importance_weights.get("downstream_column_count", 0)
        )
        
        quality_score = 0
        quality_score += model.test_count * quality_weights.get("test_count", 0)
        quality_score += model.column_test_coverage * quality_weights.get("column_coverage", 0)
        model.quality_score = quality_score
        
        raw_score = complexity_score + importance_score - quality_score

        return max(0, raw_score)
