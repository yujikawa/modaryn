from typing import Dict, List, Set
import sqlglot
from sqlglot import exp
from sqlglot.lineage import lineage
from modaryn.domain.model import DbtProject, ColumnReference, DbtModel


class LineageAnalyzer:
    def __init__(self, dialect: str = "bigquery"):
        self.dialect = dialect

    def analyze(self, project: DbtProject):
        """
        Analyzes column-level lineage for all models in the project.
        """
        schema = self._build_schema(project)
        table_to_id = {model.model_name: model.unique_id for model in project.models.values()}

        for model in project.models.values():
            if not model.raw_sql:
                continue

            for column_name in model.columns:
                try:
                    node = lineage(column_name, sql=model.raw_sql, schema=schema, dialect=self.dialect)
                    self._extract_source_columns(model, column_name, node, table_to_id, project)
                except Exception:
                    continue

    def _build_schema(self, project: DbtProject) -> Dict:
        schema = {}
        for model in project.models.values():
            schema[model.model_name] = {col.name: "UNKNOWN" for col in model.columns.values()}
        return schema

    def _extract_source_columns(self, target_model: DbtModel, target_column_name: str, node, table_to_id: Dict[str, str], project: DbtProject):
        """
        Recursively finds the source columns from the lineage node and populates the project model.
        """
        processed = set()
        
        def walk(current_node):
            if id(current_node) in processed:
                return
            processed.add(id(current_node))

            # If node.expression is a Table, it's likely a leaf pointing to a source column
            if isinstance(current_node.expression, exp.Table):
                # Table name is in expression.this.name
                table_name = current_node.expression.this.name
                # Column name is the last part of node.name (e.g., alias.col or table.col)
                source_col = current_node.name.split('.')[-1]
                
                if table_name in table_to_id:
                    source_model_id = table_to_id[table_name]
                    
                    # Add upstream reference to the target column
                    target_model.columns[target_column_name].upstream_columns.append(
                        ColumnReference(model_unique_id=source_model_id, column_name=source_col)
                    )
                    
                    # Add downstream reference to the source column
                    if source_model_id in project.models:
                        source_model = project.models[source_model_id]
                        if source_col in source_model.columns:
                            source_model.columns[source_col].downstream_columns.append(
                                ColumnReference(model_unique_id=target_model.unique_id, column_name=target_column_name)
                            )
            
            for downstream in current_node.downstream:
                walk(downstream)

        walk(node)
