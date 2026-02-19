import pytest
from pathlib import Path
from modaryn.domain.model import DbtProject, DbtModel, DbtColumn
from modaryn.analyzers.lineage import LineageAnalyzer

def test_lineage_analyzer_basic():
    # Setup mock project
    model_a = DbtModel(
        unique_id="model.a",
        model_name="table_a",
        file_path=Path("models/a.sql"),
        raw_sql="SELECT 1 as id, 'Alice' as name",
        columns={
            "id": DbtColumn(name="id", description="ID"),
            "name": DbtColumn(name="name", description="Name")
        }
    )

    model_b = DbtModel(
        unique_id="model.b",
        model_name="table_b",
        file_path=Path("models/b.sql"),
        raw_sql="SELECT id, name FROM table_a",
        columns={
            "id": DbtColumn(name="id", description="ID from A"),
            "name": DbtColumn(name="name", description="Name from A")
        },
        dependencies=["model.a"]
    )

    project = DbtProject(models={"model.a": model_a, "model.b": model_b})
    # project._build_dag() is called in __post_init__

    analyzer = LineageAnalyzer(dialect="bigquery")
    analyzer.analyze(project)

    # Verify model.b's columns point to model.a
    assert len(model_b.columns["id"].upstream_columns) == 1
    assert model_b.columns["id"].upstream_columns[0].model_unique_id == "model.a"
    assert model_b.columns["id"].upstream_columns[0].column_name == "id"

    assert len(model_b.columns["name"].upstream_columns) == 1
    assert model_b.columns["name"].upstream_columns[0].model_unique_id == "model.a"
    assert model_b.columns["name"].upstream_columns[0].column_name == "name"

    # Verify model.a's columns have downstream references
    assert len(model_a.columns["id"].downstream_columns) == 1
    assert model_a.columns["id"].downstream_columns[0].model_unique_id == "model.b"
    assert model_a.columns["id"].downstream_columns[0].column_name == "id"

    # Verify model stats
    assert model_a.downstream_column_count == 2 # id and name
    assert model_b.downstream_column_count == 0

def test_lineage_analyzer_joins():
    # Setup mock project
    model_a = DbtModel(
        unique_id="model.a",
        model_name="table_a",
        file_path=Path("models/a.sql"),
        raw_sql="SELECT 1 as user_id, 'Alice' as user_name",
        columns={
            "user_id": DbtColumn(name="user_id", description=""),
            "user_name": DbtColumn(name="user_name", description="")
        }
    )

    model_b = DbtModel(
        unique_id="model.b",
        model_name="table_b",
        file_path=Path("models/b.sql"),
        raw_sql="SELECT 1 as order_id, 1 as user_id, 100 as amount",
        columns={
            "order_id": DbtColumn(name="order_id", description=""),
            "user_id": DbtColumn(name="user_id", description=""),
            "amount": DbtColumn(name="amount", description="")
        }
    )

    model_c = DbtModel(
        unique_id="model.c",
        model_name="table_c",
        file_path=Path("models/c.sql"),
        raw_sql="""
            SELECT 
                b.order_id, 
                a.user_name, 
                b.amount 
            FROM table_b b 
            JOIN table_a a ON a.user_id = b.user_id
        """,
        columns={
            "order_id": DbtColumn(name="order_id", description=""),
            "user_name": DbtColumn(name="user_name", description=""),
            "amount": DbtColumn(name="amount", description="")
        },
        dependencies=["model.a", "model.b"]
    )

    project = DbtProject(models={"model.a": model_a, "model.b": model_b, "model.c": model_c})
    analyzer = LineageAnalyzer(dialect="bigquery")
    analyzer.analyze(project)

    # Verify model.c's columns
    assert len(model_c.columns["order_id"].upstream_columns) == 1
    assert model_c.columns["order_id"].upstream_columns[0].model_unique_id == "model.b"

    assert len(model_c.columns["user_name"].upstream_columns) == 1
    assert model_c.columns["user_name"].upstream_columns[0].model_unique_id == "model.a"

    assert len(model_c.columns["amount"].upstream_columns) == 1
    assert model_c.columns["amount"].upstream_columns[0].model_unique_id == "model.b"

    # Verify downstream counts
    assert model_a.downstream_column_count == 1 # user_name
    assert model_b.downstream_column_count == 2 # order_id and amount

def test_lineage_analyzer_ctes():
    # Setup mock project
    model_a = DbtModel(
        unique_id="model.a",
        model_name="table_a",
        file_path=Path("models/a.sql"),
        raw_sql="SELECT 1 as id, 'Alice' as name",
        columns={
            "id": DbtColumn(name="id", description=""),
            "name": DbtColumn(name="name", description="")
        }
    )

    model_b = DbtModel(
        unique_id="model.b",
        model_name="table_b",
        file_path=Path("models/b.sql"),
        raw_sql="""
            WITH source AS (
                SELECT * FROM table_a
            )
            SELECT id, name FROM source
        """,
        columns={
            "id": DbtColumn(name="id", description=""),
            "name": DbtColumn(name="name", description="")
        },
        dependencies=["model.a"]
    )

    project = DbtProject(models={"model.a": model_a, "model.b": model_b})
    analyzer = LineageAnalyzer(dialect="bigquery")
    analyzer.analyze(project)

    # Verify model.b's columns
    assert len(model_b.columns["id"].upstream_columns) == 1
    assert model_b.columns["id"].upstream_columns[0].model_unique_id == "model.a"
    assert model_b.columns["id"].upstream_columns[0].column_name == "id"

def test_lineage_analyzer_dialect_bigquery():
    model_a = DbtModel(
        unique_id="model.a",
        model_name="table_a",
        file_path=Path("models/a.sql"),
        raw_sql="SELECT 1 as id",
        columns={"id": DbtColumn(name="id", description="")}
    )
    model_b = DbtModel(
        unique_id="model.b",
        model_name="table_b",
        file_path=Path("models/b.sql"),
        raw_sql="SELECT `id` FROM `table_a`", # BigQuery backticks
        columns={"id": DbtColumn(name="id", description="")},
        dependencies=["model.a"]
    )
    project = DbtProject(models={"model.a": model_a, "model.b": model_b})
    analyzer = LineageAnalyzer(dialect="bigquery")
    analyzer.analyze(project)
    assert len(model_b.columns["id"].upstream_columns) == 1

def test_lineage_analyzer_dialect_snowflake():
    model_a = DbtModel(
        unique_id="model.a",
        model_name="table_a",
        file_path=Path("models/a.sql"),
        raw_sql="SELECT 1 as id",
        columns={"id": DbtColumn(name="id", description="")}
    )
    model_b = DbtModel(
        unique_id="model.b",
        model_name="table_b",
        file_path=Path("models/b.sql"),
        raw_sql='SELECT id FROM table_a', # Snowflake standard (unquoted)
        columns={"id": DbtColumn(name="id", description="")},
        dependencies=["model.a"]
    )
    project = DbtProject(models={"model.a": model_a, "model.b": model_b})
    analyzer = LineageAnalyzer(dialect="snowflake")
    analyzer.analyze(project)
    assert len(model_b.columns["id"].upstream_columns) == 1

def test_lineage_analyzer_dialect_postgres():
    model_a = DbtModel(
        unique_id="model.a",
        model_name="table_a",
        file_path=Path("models/a.sql"),
        raw_sql="SELECT 1 as id",
        columns={"id": DbtColumn(name="id", description="")}
    )
    model_b = DbtModel(
        unique_id="model.b",
        model_name="table_b",
        file_path=Path("models/b.sql"),
        raw_sql="SELECT id::TEXT FROM table_a", # Postgres cast syntax
        columns={"id": DbtColumn(name="id", description="")},
        dependencies=["model.a"]
    )
    project = DbtProject(models={"model.a": model_a, "model.b": model_b})
    analyzer = LineageAnalyzer(dialect="postgres")
    analyzer.analyze(project)
    assert len(model_b.columns["id"].upstream_columns) == 1
