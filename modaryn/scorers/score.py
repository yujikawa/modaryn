import yaml
from pathlib import Path
from typing import Dict

from modaryn.domain.model import DbtProject, DbtModel

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
            # A simple merge, user weights override defaults
            if "sql_complexity" in user_weights:
                weights["sql_complexity"].update(user_weights["sql_complexity"])
            if "importance" in user_weights:
                weights["importance"].update(user_weights["importance"])
        return weights

    def score_project(self, project: DbtProject):
        for model in project.models.values():
            self.score_model(model)

    def score_model(self, model: DbtModel):
        sql_complexity_weights = self.weights.get("sql_complexity", {})
        importance_weights = self.weights.get("importance", {})

        complexity_score = 0
        if model.complexity:
            complexity_score += (
                model.complexity.join_count
                * sql_complexity_weights.get("join_count", 0)
            )
            complexity_score += (
                model.complexity.cte_count * sql_complexity_weights.get("cte_count", 0)
            )

        importance_score = (
            model.downstream_model_count
            * importance_weights.get("downstream_model_count", 0)
        )

        model.score = complexity_score + importance_score
