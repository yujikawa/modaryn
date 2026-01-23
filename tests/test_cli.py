from typer.testing import CliRunner
from modaryn.cli import app
import pytest
from pathlib import Path
import json

from modaryn.loaders.manifest import ManifestLoader
from modaryn.scorers.score import Scorer


runner = CliRunner()

@pytest.fixture(scope="module")
def dbt_project_with_compiled_sql(tmp_path_factory) -> Path:
    project_dir = tmp_path_factory.mktemp("dbt_project")
    project_name = "modaryn_test_project"
    
    # Create target directory
    target_dir = project_dir / "target"
    target_dir.mkdir()

    # Create compiled directory
    compiled_dir = target_dir / "compiled" / project_name / "models"
    compiled_dir.mkdir(parents=True, exist_ok=True)

    # Define model SQL content
    compiled_sql_a = "select 1 as id_a"
    compiled_sql_b = "select id_a from model_a_compiled"
    compiled_sql_c = "select id_a from model_a_compiled where id_a = 1"
    compiled_sql_d = "WITH model_b_cte AS (SELECT id_a FROM model_b_compiled) SELECT b.id_a, c.id_a FROM model_b_cte AS b JOIN model_c_compiled AS c ON b.id_a = c.id_a"
    compiled_sql_complex = "SELECT CASE WHEN a > b THEN 1 ELSE 0 END as new_col, IF(c, 1, 0) FROM my_table WHERE x = 1 AND y = 2"

    # Write compiled SQL files
    (compiled_dir / "model_a.sql").write_text(compiled_sql_a)
    (compiled_dir / "model_b.sql").write_text(compiled_sql_b)
    (compiled_dir / "model_c.sql").write_text(compiled_sql_c)
    (compiled_dir / "model_d.sql").write_text(compiled_sql_d)
    (compiled_dir / "complex_model.sql").write_text(compiled_sql_complex)

    manifest_content = {
      "metadata": {
          "project_name": project_name
      },
      "nodes": {
        "model.modaryn_test_project.model_a": {
          "unique_id": "model.modaryn_test_project.model_a",
          "resource_type": "model",
          "name": "model_a",
          "path": "model_a.sql",
          "raw_code": "select 1 as id", # raw_code is still in manifest but we'll read compiled
          "depends_on": {
            "nodes": []
          }
        },
        "model.modaryn_test_project.model_b": {
          "unique_id": "model.modaryn_test_project.model_b",
          "resource_type": "model",
          "name": "model_b",
          "path": "model_b.sql",
          "raw_code": "select * from {{ ref('model_a') }}",
          "depends_on": {
            "nodes": [
              "model.modaryn_test_project.model_a"
            ]
          }
        },
        "model.modaryn_test_project.model_c": {
          "unique_id": "model.modaryn_test_project.model_c",
          "resource_type": "model",
          "name": "model_c",
          "path": "model_c.sql",
          "raw_code": "select * from {{ ref('model_a') }} where id = 1",
          "depends_on": {
            "nodes": [
              "model.modaryn_test_project.model_a"
            ]
          }
        },
        "model.modaryn_test_project.model_d": {
          "unique_id": "model.modaryn_test_project.model_d",
          "resource_type": "model",
          "name": "model_d",
          "path": "model_d.sql",
          "raw_code": "WITH model_b_cte AS (SELECT * FROM {{ ref('model_b') }}) SELECT b.id, c.id FROM model_b_cte AS b JOIN {{ ref('model_c') }} AS c ON b.id = c.id",
          "depends_on": {
            "nodes": [
              "model.modaryn_test_project.model_b",
              "model.modaryn_test_project.model_c"
            ]
          }
        },
        "model.modaryn_test_project.complex_model": {
          "unique_id": "model.modaryn_test_project.complex_model",
          "resource_type": "model",
          "name": "complex_model",
          "path": "complex_model.sql",
          "raw_code": "SELECT CASE WHEN a > b THEN 1 ELSE 0 END as new_col, IF(c, 1, 0) FROM my_table WHERE x = 1 AND y = 2",
          "depends_on": {
            "nodes": []
          }
        }
      }
    }
    
    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_content, f)
    
    # Create dbt_project.yml
    dbt_project_yml_content = f"""
name: '{project_name}'
version: '1.0.0'
config-version: 2

profile: 'default'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"
  - "logs"
"""
    (project_dir / "dbt_project.yml").write_text(dbt_project_yml_content)
    
    return project_dir

# Remove the old manifest_file fixture as it's no longer needed
# @pytest.fixture(scope="module")
# def manifest_file(tmp_path_factory) -> Path:
#     manifest_content = {
#       "nodes": {
#         "model.modaryn_test.model_a": {
#           "unique_id": "model.modaryn_test.model_a",
#           "resource_type": "model",
#           "name": "model_a",
#           "path": "model_a.sql",
#           "raw_code": "select 1 as id",
#           "depends_on": {
#             "nodes": []
#           }
#         },
#         # ... other models ...
#       }
#     }
#     manifest_dir = tmp_path_factory.mktemp("target")
#     manifest_path = manifest_dir / "manifest.json"
#     with open(manifest_path, "w") as f:
#         json.dump(manifest_content, f)
#     return manifest_path

from typer.testing import CliRunner
from modaryn.cli import app
import pytest
from pathlib import Path
import json

from modaryn.loaders.manifest import ManifestLoader
from modaryn.scorers.score import Scorer


runner = CliRunner()

@pytest.fixture(scope="module")
def dbt_project_with_compiled_sql(tmp_path_factory) -> Path:
    project_dir = tmp_path_factory.mktemp("dbt_project")
    project_name = "modaryn_test_project"
    
    # Create target directory
    target_dir = project_dir / "target"
    target_dir.mkdir()

    # Create compiled directory
    compiled_dir = target_dir / "compiled" / project_name / "models"
    compiled_dir.mkdir(parents=True, exist_ok=True)

    # Define model SQL content
    compiled_sql_a = "select 1 as id_a"
    compiled_sql_b = "select id_a from model_a_compiled"
    compiled_sql_c = "select id_a from model_a_compiled where id_a = 1"
    compiled_sql_d = "WITH model_b_cte AS (SELECT id_a FROM model_b_compiled) SELECT b.id_a, c.id_a FROM model_b_cte AS b JOIN model_c_compiled AS c ON b.id_a = c.id_a"
    compiled_sql_complex = "SELECT CASE WHEN a > b THEN 1 ELSE 0 END as new_col, IF(c, 1, 0) FROM my_table WHERE x = 1 AND y = 2"

    # Write compiled SQL files
    (compiled_dir / "model_a.sql").write_text(compiled_sql_a)
    (compiled_dir / "model_b.sql").write_text(compiled_sql_b)
    (compiled_dir / "model_c.sql").write_text(compiled_sql_c)
    (compiled_dir / "model_d.sql").write_text(compiled_sql_d)
    (compiled_dir / "complex_model.sql").write_text(compiled_sql_complex)

    manifest_content = {
      "metadata": {
          "project_name": project_name
      },
      "nodes": {
        "model.modaryn_test_project.model_a": {
          "unique_id": "model.modaryn_test_project.model_a",
          "resource_type": "model",
          "name": "model_a",
          "path": "model_a.sql",
          "raw_code": "select 1 as id", # raw_code is still in manifest but we'll read compiled
          "depends_on": {
            "nodes": []
          }
        },
        "model.modaryn_test_project.model_b": {
          "unique_id": "model.modaryn_test_project.model_b",
          "resource_type": "model",
          "name": "model_b",
          "path": "model_b.sql",
          "raw_code": "select * from {{ ref('model_a') }}",
          "depends_on": {
            "nodes": [
              "model.modaryn_test_project.model_a"
            ]
          }
        },
        "model.modaryn_test_project.model_c": {
          "unique_id": "model.modaryn_test_project.model_c",
          "resource_type": "model",
          "name": "model_c",
          "path": "model_c.sql",
          "raw_code": "select * from {{ ref('model_a') }} where id = 1",
          "depends_on": {
            "nodes": [
              "model.modaryn_test_project.model_a"
            ]
          }
        },
        "model.modaryn_test_project.model_d": {
          "unique_id": "model.modaryn_test_project.model_d",
          "resource_type": "model",
          "name": "model_d",
          "path": "model_d.sql",
          "raw_code": "WITH model_b_cte AS (SELECT * FROM {{ ref('model_b') }}) SELECT b.id, c.id FROM model_b_cte AS b JOIN {{ ref('model_c') }} AS c ON b.id = c.id",
          "depends_on": {
            "nodes": [
              "model.modaryn_test_project.model_b",
              "model.modaryn_test_project.model_c"
            ]
          }
        },
        "model.modaryn_test_project.complex_model": {
          "unique_id": "model.modaryn_test_project.complex_model",
          "resource_type": "model",
          "name": "complex_model",
          "path": "complex_model.sql",
          "raw_code": "SELECT CASE WHEN a > b THEN 1 ELSE 0 END as new_col, IF(c, 1, 0) FROM my_table WHERE x = 1 AND y = 2",
          "depends_on": {
            "nodes": []
          }
        }
      }
    }
    
    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_content, f)
    
    # Create dbt_project.yml
    dbt_project_yml_content = f"""
name: '{project_name}'
version: '1.0.0'
config-version: 2

profile: 'default'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"
  - "logs"
"""
    (project_dir / "dbt_project.yml").write_text(dbt_project_yml_content)
    
    return project_dir

# Remove the old manifest_file fixture as it's no longer needed
# @pytest.fixture(scope="module")
# def manifest_file(tmp_path_factory) -> Path:
#     manifest_content = {
#       "nodes": {
#         "model.modaryn_test.model_a": {
#           "unique_id": "model.modaryn_test.model_a",
#           "resource_type": "model",
#           "name": "model_a",
#           "path": "model_a.sql",
#           "raw_code": "select 1 as id",
#           "depends_on": {
#             "nodes": []
#           }
#         },
#         # ... other models ...
#       }
#     }
#     manifest_dir = tmp_path_factory.mktemp("target")
#     manifest_path = manifest_dir / "manifest.json"
#     with open(manifest_path, "w") as f:
#         json.dump(manifest_content, f)
#     return manifest_path

from typer.testing import CliRunner
from modaryn.cli import app
import pytest
from pathlib import Path
import json

from modaryn.loaders.manifest import ManifestLoader
from modaryn.scorers.score import Scorer


runner = CliRunner()

@pytest.fixture(scope="module")
def dbt_project_with_compiled_sql(tmp_path_factory) -> Path:
    project_dir = tmp_path_factory.mktemp("dbt_project")
    project_name = "modaryn_test_project"
    
    # Create target directory
    target_dir = project_dir / "target"
    target_dir.mkdir()

    # Create compiled directory
    compiled_dir = target_dir / "compiled" / project_name / "models"
    compiled_dir.mkdir(parents=True, exist_ok=True)

    # Define model SQL content
    compiled_sql_a = "select 1 as id_a"
    compiled_sql_b = "select id_a from model_a_compiled"
    compiled_sql_c = "select id_a from model_a_compiled where id_a = 1"
    compiled_sql_d = "WITH model_b_cte AS (SELECT id_a FROM model_b_compiled) SELECT b.id_a, c.id_a FROM model_b_cte AS b JOIN model_c_compiled AS c ON b.id_a = c.id_a"
    compiled_sql_complex = "SELECT CASE WHEN a > b THEN 1 ELSE 0 END as new_col, IF(c, 1, 0) FROM my_table WHERE x = 1 AND y = 2"

    # Write compiled SQL files
    (compiled_dir / "model_a.sql").write_text(compiled_sql_a)
    (compiled_dir / "model_b.sql").write_text(compiled_sql_b)
    (compiled_dir / "model_c.sql").write_text(compiled_sql_c)
    (compiled_dir / "model_d.sql").write_text(compiled_sql_d)
    (compiled_dir / "complex_model.sql").write_text(compiled_sql_complex)

    manifest_content = {
      "metadata": {
          "project_name": project_name
      },
      "nodes": {
        "model.modaryn_test_project.model_a": {
          "unique_id": "model.modaryn_test_project.model_a",
          "resource_type": "model",
          "name": "model_a",
          "path": "model_a.sql",
          "raw_code": "select 1 as id", # raw_code is still in manifest but we'll read compiled
          "depends_on": {
            "nodes": []
          }
        },
        "model.modaryn_test_project.model_b": {
          "unique_id": "model.modaryn_test_project.model_b",
          "resource_type": "model",
          "name": "model_b",
          "path": "model_b.sql",
          "raw_code": "select * from {{ ref('model_a') }}",
          "depends_on": {
            "nodes": [
              "model.modaryn_test_project.model_a"
            ]
          }
        },
        "model.modaryn_test_project.model_c": {
          "unique_id": "model.modaryn_test_project.model_c",
          "resource_type": "model",
          "name": "model_c",
          "path": "model_c.sql",
          "raw_code": "select * from {{ ref('model_a') }} where id = 1",
          "depends_on": {
            "nodes": [
              "model.modaryn_test_project.model_a"
            ]
          }
        },
        "model.modaryn_test_project.model_d": {
          "unique_id": "model.modaryn_test_project.model_d",
          "resource_type": "model",
          "name": "model_d",
          "path": "model_d.sql",
          "raw_code": "WITH model_b_cte AS (SELECT * FROM {{ ref('model_b') }}) SELECT b.id, c.id FROM model_b_cte AS b JOIN {{ ref('model_c') }} AS c ON b.id = c.id",
          "depends_on": {
            "nodes": [
              "model.modaryn_test_project.model_b",
              "model.modaryn_test_project.model_c"
            ]
          }
        },
        "model.modaryn_test_project.complex_model": {
          "unique_id": "model.modaryn_test_project.complex_model",
          "resource_type": "model",
          "name": "complex_model",
          "path": "complex_model.sql",
          "raw_code": "SELECT CASE WHEN a > b THEN 1 ELSE 0 END as new_col, IF(c, 1, 0) FROM my_table WHERE x = 1 AND y = 2",
          "depends_on": {
            "nodes": []
          }
        }
      }
    }
    
    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_content, f)
    
    # Create dbt_project.yml
    dbt_project_yml_content = f"""
name: '{project_name}'
version: '1.0.0'
config-version: 2

profile: 'default'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"
  - "logs"
"""
    (project_dir / "dbt_project.yml").write_text(dbt_project_yml_content)
    
    return project_dir

def test_sql_complexity_analysis_with_compiled_sql(dbt_project_with_compiled_sql):
    loader = ManifestLoader(dbt_project_with_compiled_sql)
    project = loader.load()

    # Model A
    model_a = project.get_model("model.modaryn_test_project.model_a")
    assert model_a.complexity.join_count == 0
    assert model_a.complexity.cte_count == 0
    assert model_a.complexity.conditional_count == 0
    assert model_a.complexity.where_count == 0
    assert model_a.complexity.sql_char_count == 16
    assert model_a.downstream_model_count == 2 # model_b, model_c

    # Model B
    model_b = project.get_model("model.modaryn_test_project.model_b")
    assert model_b.complexity.join_count == 0
    assert model_b.complexity.cte_count == 0
    assert model_b.complexity.conditional_count == 0
    assert model_b.complexity.where_count == 0
    assert model_b.complexity.sql_char_count == 33
    assert model_b.downstream_model_count == 1 # model_d

    # Model C
    model_c = project.get_model("model.modaryn_test_project.model_c")
    assert model_c.complexity.join_count == 0
    assert model_c.complexity.cte_count == 0
    assert model_c.complexity.conditional_count == 0
    assert model_c.complexity.where_count == 1
    assert model_c.complexity.sql_char_count == 48
    assert model_c.downstream_model_count == 1 # model_d
    
    # Model D
    model_d = project.get_model("model.modaryn_test_project.model_d")
    assert model_d.complexity.join_count == 1
    assert model_d.complexity.cte_count == 1
    assert model_d.complexity.conditional_count == 0
    assert model_d.complexity.where_count == 0
    assert model_d.complexity.sql_char_count == 145
    assert model_d.downstream_model_count == 0

    # Complex Model
    complex_model = project.get_model("model.modaryn_test_project.complex_model")
    assert complex_model.complexity.join_count == 0
    assert complex_model.complexity.cte_count == 0
    assert complex_model.complexity.conditional_count == 3
    assert complex_model.complexity.where_count == 1
    assert complex_model.complexity.sql_char_count == 100
    assert complex_model.downstream_model_count == 0


def test_scoring_and_ranking_with_compiled_sql(dbt_project_with_compiled_sql):
    loader = ManifestLoader(dbt_project_with_compiled_sql)
    project = loader.load()

    scorer = Scorer()
    scorer.score_project(project)

    # Weights (from `modaryn/config/default.yml`):
    # join_count: 2.0, cte_count: 1.5, conditional_count: 1.0, where_count: 0.5, sql_char_count: 0.01, downstream_model_count: 1.0

    # Raw Scores:
    # model_a: (0 * 2.0) + (0 * 1.5) + (0 * 1.0) + (0 * 0.5) + (16 * 0.01) + (2 * 1.0) = 0.16 + 2.0 = 2.16
    # model_b: (0 * 2.0) + (0 * 1.5) + (0 * 1.0) + (0 * 0.5) + (33 * 0.01) + (1 * 1.0) = 0.33 + 1.0 = 1.33
    # model_c: (0 * 2.0) + (0 * 1.0) + (0 * 1.0) + (1 * 0.5) + (40 * 0.01) + (1 * 1.0) = 0.5 + 0.40 + 1.0 = 1.90
    # model_d: (1 * 2.0) + (1 * 1.5) + (0 * 1.0) + (0 * 0.5) + (115 * 0.01) + (0 * 1.0) = 2.0 + 1.5 + 1.15 = 4.65
    # complex_model: (0 * 2.0) + (0 * 1.5) + (3 * 1.0) + (1 * 0.5) + (100 * 0.01) + (0 * 1.0) = 3.0 + 0.5 + 1.00 = 4.50

    # scores: [2.16, 1.33, 1.90, 4.65, 4.50]
    # mean: 2.908
    # std_dev: 1.388

    # Z-Scores:
    # model_a: (2.16 - 2.908) / 1.388 = -0.539
    # model_b: (1.33 - 2.908) / 1.388 = -1.137
    # model_c: (1.90 - 2.908) / 1.388 = -0.726
    # model_d: (4.65 - 2.908) / 1.388 = 1.255
    # complex_model: (4.50 - 2.908) / 1.388 = 1.147

    # Ranks:
    # model_d (1.255)
    # complex_model (1.147)
    # model_a (-0.539)
    # model_c (-0.726)
    # model_b (-1.137)

    # Sort models by score to get ranks
    sorted_models = sorted(
        project.models.values(),
        key=lambda m: m.score,
        reverse=True
    )
    
    # Assert ranks
    assert sorted_models[0].model_name == "model_d"
    assert sorted_models[1].model_name == "complex_model"
    assert sorted_models[2].model_name == "model_a"
    assert sorted_models[3].model_name == "model_c"
    assert sorted_models[4].model_name == "model_b"

    # Assert scores with approximation
    assert project.get_model("model.modaryn_test_project.model_d").score == pytest.approx(1.255, abs=0.01)
    assert project.get_model("model.modaryn_test_project.complex_model").score == pytest.approx(1.147, abs=0.01)
    assert project.get_model("model.modaryn_test_project.model_a").score == pytest.approx(-0.539, abs=0.01)
    assert project.get_model("model.modaryn_test_project.model_c").score == pytest.approx(-0.726, abs=0.01)
    assert project.get_model("model.modaryn_test_project.model_b").score == pytest.approx(-1.137, abs=0.01)


def test_scoring_and_ranking_with_compiled_sql(dbt_project_with_compiled_sql):
    loader = ManifestLoader(dbt_project_with_compiled_sql)
    project = loader.load()

    scorer = Scorer()
    scorer.score_project(project)

    # Weights (from `modaryn/config/default.yml`):
    # join_count: 2.0, cte_count: 1.5, conditional_count: 1.0, where_count: 0.5, sql_char_count: 0.01, downstream_model_count: 1.0

    # Raw Scores:
    # model_a: (0 * 2.0) + (0 * 1.5) + (0 * 1.0) + (0 * 0.5) + (16 * 0.01) + (2 * 1.0) = 0.16 + 2.0 = 2.16
    # model_b: (0 * 2.0) + (0 * 1.5) + (0 * 1.0) + (0 * 0.5) + (26 * 0.01) + (1 * 1.0) = 0.26 + 1.0 = 1.26
    # model_c: (0 * 2.0) + (0 * 1.0) + (0 * 1.0) + (1 * 0.5) + (39 * 0.01) + (1 * 1.0) = 0.5 + 0.39 + 1.0 = 1.89
    # model_d: (1 * 2.0) + (1 * 1.5) + (0 * 1.0) + (0 * 0.5) + (114 * 0.01) + (0 * 1.0) = 2.0 + 1.5 + 1.14 = 4.64
    # complex_model: (0 * 2.0) + (0 * 1.5) + (3 * 1.0) + (1 * 0.5) + (100 * 0.01) + (0 * 1.0) = 3.0 + 0.5 + 1.00 = 4.50

    # scores: [2.16, 1.26, 1.89, 4.64, 4.50]
    # mean: 2.89
    # std_dev: 1.403

    # Z-Scores:
    # model_a: (2.16 - 2.89) / 1.403 = -0.520
    # model_b: (1.26 - 2.89) / 1.403 = -1.162
    # model_c: (1.89 - 2.89) / 1.403 = -0.713
    # model_d: (4.64 - 2.89) / 1.403 = 1.247
    # complex_model: (4.50 - 2.89) / 1.403 = 1.148

    # Ranks:
    # model_d (1.351)
    # complex_model (1.041)
    # model_a (-0.566)
    # model_c (-0.690)
    # model_b (-1.136)

    # Sort models by score to get ranks
    sorted_models = sorted(
        project.models.values(),
        key=lambda m: m.score,
        reverse=True
    )
    
    # Assert ranks
    assert sorted_models[0].model_name == "model_d"
    assert sorted_models[1].model_name == "complex_model"
    assert sorted_models[2].model_name == "model_a"
    assert sorted_models[3].model_name == "model_c"
    assert sorted_models[4].model_name == "model_b"

    # Assert scores with approximation
    assert project.get_model("model.modaryn_test_project.model_d").score == pytest.approx(1.351, abs=0.01)
    assert project.get_model("model.modaryn_test_project.complex_model").score == pytest.approx(1.041, abs=0.01)
    assert project.get_model("model.modaryn_test_project.model_a").score == pytest.approx(-0.566, abs=0.01)
    assert project.get_model("model.modaryn_test_project.model_c").score == pytest.approx(-0.690, abs=0.01)
    assert project.get_model("model.modaryn_test_project.model_b").score == pytest.approx(-1.136, abs=0.01)


def test_scan_command_with_project_path(dbt_project_with_compiled_sql):
    result = runner.invoke(app, ["scan", "--project-path", str(dbt_project_with_compiled_sql)])
    assert result.exit_code == 0
    assert "Scanning dbt project:" in result.stdout
    assert "Found 5 models." in result.stdout

def test_score_command_with_project_path(dbt_project_with_compiled_sql):
    result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql)])
    assert result.exit_code == 0
    assert "Loading dbt project:" in result.stdout
    assert "Scoring project..." in result.stdout