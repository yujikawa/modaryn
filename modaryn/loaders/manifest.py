import json
from pathlib import Path
from typing import Dict
import yaml

from modaryn.analyzers.sql_complexity import SqlComplexityAnalyzer
from modaryn.domain.model import DbtModel, DbtProject


class ManifestLoader:
    def __init__(self, project_path: Path, dialect: str = "bigquery"):
        self.project_path = project_path
        self.sql_analyzer = SqlComplexityAnalyzer(dialect=dialect)
        self.manifest_path = self.project_path / "target" / "manifest.json"
        self.dbt_project_yml_path = self.project_path / "dbt_project.yml"

    def _get_project_name_from_dbt_project_yml(self) -> str:
        if not self.dbt_project_yml_path.exists():
            raise FileNotFoundError(f"dbt_project.yml not found at {self.dbt_project_yml_path}. Ensure this is a dbt project directory.")

        with open(self.dbt_project_yml_path, "r") as f:
            dbt_project_config = yaml.safe_load(f)
        
        project_name = dbt_project_config.get("name")
        if not project_name:
            raise ValueError(f"Could not find 'name' in {self.dbt_project_yml_path}. Is it a valid dbt_project.yml?")
        
        return project_name


    def load(self) -> DbtProject:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found at {self.manifest_path}. Please ensure 'dbt compile' has been run in the dbt project at {self.project_path}.")

        project_name = self._get_project_name_from_dbt_project_yml()

        with open(self.manifest_path, "r") as f:
            manifest_data = json.load(f)

        compiled_code_dir = self.project_path / "target" / "compiled" / project_name / "models"

        models: Dict[str, DbtModel] = {}
        nodes = manifest_data.get("nodes", {})

        for unique_id, node_data in nodes.items():
            if node_data.get("resource_type") == "model":
                # Construct path to compiled SQL file
                model_relative_path = Path(node_data.get("path", ""))
                compiled_sql_path = compiled_code_dir / model_relative_path

                compiled_sql = ""
                if compiled_sql_path.exists():
                    with open(compiled_sql_path, "r") as sql_f:
                        compiled_sql = sql_f.read()
                else:
                    # Fallback to raw_code if compiled SQL not found, or raise an error
                    # For now, let's log a warning and use an empty string
                    print(f"Warning: Compiled SQL not found for model {node_data.get('name')} at {compiled_sql_path}. Using empty string for analysis.")

                model = DbtModel(
                    unique_id=unique_id,
                    model_name=node_data.get("name", ""),
                    file_path=Path(node_data.get("path", "")),
                    raw_sql=compiled_sql, # Use compiled SQL
                    dependencies=self._get_node_dependencies(node_data),
                    complexity=self.sql_analyzer.analyze(compiled_sql), # Analyze compiled SQL
                )
                models[unique_id] = model

        return DbtProject(models=models)

    def _get_node_dependencies(self, node_data: Dict) -> list[str]:
        return [
            dep
            for dep in node_data.get("depends_on", {}).get("nodes", [])
            if dep.startswith("model.")
        ]
