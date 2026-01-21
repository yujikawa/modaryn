import json
from pathlib import Path
from typing import Dict

from modaryn.analyzers.sql_complexity import SqlComplexityAnalyzer
from modaryn.domain.model import DbtModel, DbtProject


class ManifestLoader:
    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self.sql_analyzer = SqlComplexityAnalyzer()

    def load(self) -> DbtProject:
        with open(self.manifest_path, "r") as f:
            manifest_data = json.load(f)

        models: Dict[str, DbtModel] = {}
        nodes = manifest_data.get("nodes", {})

        for unique_id, node_data in nodes.items():
            if node_data.get("resource_type") == "model":
                raw_sql = node_data.get("raw_sql", "")
                model = DbtModel(
                    unique_id=unique_id,
                    model_name=node_data.get("name", ""),
                    file_path=Path(node_data.get("path", "")),
                    raw_sql=raw_sql,
                    dependencies=self._get_node_dependencies(node_data),
                    complexity=self.sql_analyzer.analyze(raw_sql),
                )
                models[unique_id] = model

        return DbtProject(models=models)

    def _get_node_dependencies(self, node_data: Dict) -> list[str]:
        return [
            dep
            for dep in node_data.get("depends_on", {}).get("nodes", [])
            if dep.startswith("model.")
        ]
