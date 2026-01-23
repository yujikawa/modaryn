from dataclasses import dataclass
import sys
import sqlglot
import re


@dataclass
class SqlComplexityResult:
    join_count: int
    cte_count: int
    conditional_count: int
    where_count: int
    sql_char_count: int


class SqlComplexityAnalyzer:
    def __init__(self, dialect: str = "bigquery"):
        self.dialect = dialect

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
            expression = sqlglot.parse_one(processed_sql, read=self.dialect)
        except sqlglot.errors.ParseError as e:
            # If sqlglot can't parse, return zero for all metrics
            # We don't print warnings here to avoid polluting test output
            return SqlComplexityResult(join_count=0, cte_count=0, conditional_count=0, where_count=0, sql_char_count=0)

        join_count = len(list(expression.find_all(sqlglot.exp.Join)))
        cte_count = len(list(expression.find_all(sqlglot.exp.CTE)))
        conditional_count = len(list(expression.find_all(sqlglot.exp.Case))) + len(list(expression.find_all(sqlglot.exp.If)))
        where_count = len(list(expression.find_all(sqlglot.exp.Where)))
        sql_char_count = len(processed_sql)


        return SqlComplexityResult(
            join_count=join_count,
            cte_count=cte_count,
            conditional_count=conditional_count,
            where_count=where_count,
            sql_char_count=sql_char_count
        )
