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
        # Store table names in lowercase for case-insensitive lookup
        table_to_id = {model.model_name.lower(): model.unique_id for model in project.models.values()}

        for model in project.models.values():
            if not model.raw_sql:
                continue

            for column_name in model.columns:
                try:
                    # Try variations (Original, Uppercase, Quoted) to find the column in different dialects.
                    # This handles cases like Snowflake (uppercase by default) or BigQuery (backticks).
                    node = None
                    search_variations = [column_name, column_name.upper(), f'"{column_name}"', f'`{column_name}`']
                    
                    for variation in search_variations:
                        try:
                            node = lineage(variation, sql=model.raw_sql, schema=schema, dialect=self.dialect)
                            if node:
                                break
                        except Exception:
                            continue
                    
                    if node:
                        self._extract_source_columns(model, column_name, node, table_to_id, project)
                except Exception:
                    continue

    def _build_schema(self, project: DbtProject) -> Dict:
        """
        Builds a sqlglot compatible schema from the dbt project.
        """
        schema = {}
        for model in project.models.values():
            # Use lowercase for table and column names in schema to allow flexible matching
            model_name_lower = model.model_name.lower()
            schema[model_name_lower] = {col.name.lower(): "UNKNOWN" for col in model.columns.values()}
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

            # Identify if this node represents a source table and column.
            # We prioritize Table expressions but fallback to parsing the node name (e.g., 'table.column').
            table_name = None
            source_col_raw = None

            if isinstance(current_node.expression, exp.Table):
                table_id_raw = current_node.expression.this
                if hasattr(table_id_raw, 'name'):
                    table_name = table_id_raw.name.lower().strip('"`')
                else:
                    table_name = str(table_id_raw).lower().strip('"`')
                source_col_raw = current_node.name.split('.')[-1].lower().strip('"`')
            
            elif '.' in current_node.name:
                parts = current_node.name.split('.')
                table_name = parts[-2].lower().strip('"`')
                source_col_raw = parts[-1].lower().strip('"`')
            
            # If we found a candidate table name, check if it's in our dbt project
            if table_name and table_name in table_to_id:
                source_model_id = table_to_id[table_name]
                source_model = project.models.get(source_model_id)
                
                if source_model:
                    # Map normalized source_col_raw back to the actual column name in the source model
                    actual_source_col = None
                    for col_name in source_model.columns:
                        if col_name.lower() == source_col_raw:
                            actual_source_col = col_name
                            break
                    
                    if actual_source_col:
                        # Add reference if not already present
                        if not any(ref.model_unique_id == source_model_id and ref.column_name == actual_source_col 
                                   for ref in target_model.columns[target_column_name].upstream_columns):
                            
                            target_model.columns[target_column_name].upstream_columns.append(
                                ColumnReference(model_unique_id=source_model_id, column_name=actual_source_col)
                            )
                            source_model.columns[actual_source_col].downstream_columns.append(
                                ColumnReference(model_unique_id=target_model.unique_id, column_name=target_column_name)
                            )
            
            for downstream in current_node.downstream:
                walk(downstream)

        walk(node)
