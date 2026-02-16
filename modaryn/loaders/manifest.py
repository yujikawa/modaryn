import json
from pathlib import Path
from typing import Dict
import yaml

from modaryn.analyzers.sql_complexity import SqlComplexityAnalyzer
from modaryn.domain.model import DbtModel, DbtProject, DbtColumn


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
        nodes = manifest_data.get("nodes", {})
        
        # Pass 1: Load models and their columns
        models: Dict[str, DbtModel] = {}
        for unique_id, node_data in nodes.items():
            if node_data.get("resource_type") == "model":
                model_relative_path = Path(node_data.get("path", ""))
                compiled_sql_path = compiled_code_dir / model_relative_path

                compiled_sql = ""
                if compiled_sql_path.exists():
                    with open(compiled_sql_path, "r") as sql_f:
                        compiled_sql = sql_f.read()
                else:
                    print(f"Warning: Compiled SQL not found for model {node_data.get('name')} at {compiled_sql_path}. Using empty string for analysis.")

                # Create DbtColumn objects
                model_columns = {
                    col_name: DbtColumn(name=col_name, description=col_data.get("description", ""))
                    for col_name, col_data in node_data.get("columns", {}).items()
                }

                model = DbtModel(
                    unique_id=unique_id,
                    model_name=node_data.get("name", ""),
                    file_path=Path(node_data.get("path", "")),
                    raw_sql=compiled_sql,
                    columns=model_columns,
                    dependencies=self._get_node_dependencies(node_data),
                    complexity=self.sql_analyzer.analyze(compiled_sql),
                )
                models[unique_id] = model

        # Pass 2: Associate tests with models and columns
        for unique_id, node_data in nodes.items():
            if node_data.get("resource_type") == "test":
                test_dependencies = node_data.get("depends_on", {}).get("nodes", [])
                
                for dep_id in test_dependencies:
                    if dep_id in models:
                        target_model = models[dep_id]
                        target_model.test_count += 1
                        
                        column_name = node_data.get("column_name")
                        if column_name and column_name in target_model.columns:
                            target_model.columns[column_name].test_count += 1
                        break # Assume test depends on only one model

        return DbtProject(models=models)

    def _get_node_dependencies(self, node_data: Dict) -> list[str]:
        return [
            dep
            for dep in node_data.get("depends_on", {}).get("nodes", [])
            if dep.startswith("model.")
        ]
