from dataclasses import dataclass
import sys
import sqlglot
import re


@dataclass
class SqlComplexityResult:
    join_count: int
    cte_count: int


class SqlComplexityAnalyzer:
    def _preprocess_sql(self, sql: str) -> str:
        """
        Replaces dbt ref() functions with just the model name.
        """
        return re.sub(r"\{\{\s*ref\('([^']*)'\)\s*\}\}", r"\1", sql)

    def analyze(self, sql: str) -> SqlComplexityResult:
        """
        Analyzes the complexity of a SQL query.

        Args:
            sql: The SQL query string to analyze.

        Returns:
            A dictionary containing complexity metrics.
        """
        processed_sql = self._preprocess_sql(sql)
        try:
            expression = sqlglot.parse_one(processed_sql)
        except sqlglot.errors.ParseError as e:
            # If sqlglot can't parse, print a warning and return zero for all metrics
            print(f"Warning: Failed to parse SQL for complexity analysis. Error: {e}", file=sys.stderr)
            return SqlComplexityResult(join_count=0, cte_count=0)

        join_count = len(list(expression.find_all(sqlglot.exp.Join)))
        cte_count = len(list(expression.find_all(sqlglot.exp.CTE)))

        return SqlComplexityResult(
            join_count=join_count,
            cte_count=cte_count,
        )
