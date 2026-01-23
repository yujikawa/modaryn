from typer.testing import CliRunner
from modaryn.cli import app
import pytest
from pathlib import Path
import json

from modaryn.loaders.manifest import ManifestLoader
from modaryn.scorers.score import Scorer


runner = CliRunner()

@pytest.fixture(scope="module")
def manifest_file(tmp_path_factory) -> Path:
    manifest_content = {
      "nodes": {
        "model.modaryn_test.model_a": {
          "unique_id": "model.modaryn_test.model_a",
          "resource_type": "model",
          "name": "model_a",
          "path": "models/model_a.sql",
          "raw_code": "select 1 as id",
          "depends_on": {
            "nodes": []
          }
        },
        "model.modaryn_test.model_b": {
          "unique_id": "model.modaryn_test.model_b",
          "resource_type": "model",
          "name": "model_b",
          "path": "models/model_b.sql",
          "raw_code": "select * from {{ ref('model_a') }}",
          "depends_on": {
            "nodes": [
              "model.modaryn_test.model_a"
            ]
          }
        },
        "model.modaryn_test.model_c": {
          "unique_id": "model.modaryn_test.model_c",
          "resource_type": "model",
          "name": "model_c",
          "path": "models/model_c.sql",
          "raw_code": "select * from {{ ref('model_a') }} where id = 1",
          "depends_on": {
            "nodes": [
              "model.modaryn_test.model_a"
            ]
          }
        },
        "model.modaryn_test.model_d": {
          "unique_id": "model.modaryn_test.model_d",
          "resource_type": "model",
          "name": "model_d",
          "path": "models/model_d.sql",
          "raw_code": "WITH model_b_cte AS (SELECT * FROM {{ ref('model_b') }}) SELECT b.id, c.id FROM model_b_cte AS b JOIN {{ ref('model_c') }} AS c ON b.id = c.id",
          "depends_on": {
            "nodes": [
              "model.modaryn_test.model_b",
              "model.modaryn_test.model_c"
            ]
          }
        },
        "model.modaryn_test.complex_model": {
          "unique_id": "model.modaryn_test.complex_model",
          "resource_type": "model",
          "name": "complex_model",
          "path": "models/complex_model.sql",
          "raw_code": "SELECT CASE WHEN a > b THEN 1 ELSE 0 END as new_col, IF(c, 1, 0) FROM my_table WHERE x = 1 AND y = 2",
          "depends_on": {
            "nodes": []
          }
        }
      }
    }
    manifest_dir = tmp_path_factory.mktemp("target")
    manifest_path = manifest_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_content, f)
    return manifest_path

def test_sql_complexity_analysis(manifest_file):
    loader = ManifestLoader(manifest_file)
    project = loader.load()

    # Model A
    model_a = project.get_model("model.modaryn_test.model_a")
    assert model_a.complexity.join_count == 0
    assert model_a.complexity.cte_count == 0
    assert model_a.complexity.conditional_count == 0
    assert model_a.complexity.where_count == 0
    assert model_a.complexity.sql_char_count == 14
    assert model_a.downstream_model_count == 2 # model_b, model_c

    # Model B
    model_b = project.get_model("model.modaryn_test.model_b")
    assert model_b.complexity.join_count == 0
    assert model_b.complexity.cte_count == 0
    assert model_b.complexity.conditional_count == 0
    assert model_b.complexity.where_count == 0
    assert model_b.complexity.sql_char_count == 21
    assert model_b.downstream_model_count == 1 # model_d

    # Model C
    model_c = project.get_model("model.modaryn_test.model_c")
    assert model_c.complexity.join_count == 0
    assert model_c.complexity.cte_count == 0
    assert model_c.complexity.conditional_count == 0
    assert model_c.complexity.where_count == 1
    assert model_c.complexity.sql_char_count == 34 # Corrected from 33
    assert model_c.downstream_model_count == 1 # model_d
    
    # Model D
    model_d = project.get_model("model.modaryn_test.model_d")
    assert model_d.complexity.join_count == 1
    assert model_d.complexity.cte_count == 1
    assert model_d.complexity.conditional_count == 0
    assert model_d.complexity.where_count == 0
    assert model_d.complexity.sql_char_count == 116 # Corrected from 101
    assert model_d.downstream_model_count == 0

    # Complex Model
    complex_model = project.get_model("model.modaryn_test.complex_model")
    assert complex_model.complexity.join_count == 0
    assert complex_model.complexity.cte_count == 0
    assert complex_model.complexity.conditional_count == 3
    assert complex_model.complexity.where_count == 1
    assert complex_model.complexity.sql_char_count == 100 # Corrected from 68
    assert complex_model.downstream_model_count == 0


def test_scoring_and_ranking(manifest_file):
    loader = ManifestLoader(manifest_file)
    project = loader.load()

    scorer = Scorer()
    scorer.score_project(project)

    # Weights (from `modaryn/config/default.yml`):
    # join_count: 2.0, cte_count: 1.5, conditional_count: 1.0, where_count: 0.5, sql_char_count: 0.01, downstream_model_count: 1.0

    # Raw Scores:
    # model_a: (0 * 2.0) + (0 * 1.5) + (0 * 1.0) + (0 * 0.5) + (14 * 0.01) + (2 * 1.0) = 0.14 + 2.0 = 2.14
    # model_b: (0 * 2.0) + (0 * 1.5) + (0 * 1.0) + (0 * 0.5) + (21 * 0.01) + (1 * 1.0) = 0.21 + 1.0 = 1.21
    # model_c: (0 * 2.0) + (0 * 1.0) + (0 * 1.0) + (1 * 0.5) + (34 * 0.01) + (1 * 1.0) = 0.5 + 0.34 + 1.0 = 1.84
    # model_d: (1 * 2.0) + (1 * 1.5) + (0 * 1.0) + (0 * 0.5) + (116 * 0.01) + (0 * 1.0) = 2.0 + 1.5 + 1.16 = 4.66
    # complex_model: (0 * 2.0) + (0 * 1.5) + (3 * 1.0) + (1 * 0.5) + (100 * 0.01) + (0 * 1.0) = 3.0 + 0.5 + 1.00 = 4.50

    # scores: [2.14, 1.21, 1.84, 4.66, 4.50]
    # mean: 2.87
    # std_dev: 1.4289

    # Z-Scores:
    # model_a: (2.14 - 2.87) / 1.4289 = -0.511
    # model_b: (1.21 - 2.87) / 1.4289 = -1.161
    # model_c: (1.84 - 2.87) / 1.4289 = -0.721
    # model_d: (4.66 - 2.87) / 1.4289 = 1.253
    # complex_model: (4.50 - 2.87) / 1.4289 = 1.140

    # Ranks:
    # model_d (1.253)
    # complex_model (1.140)
    # model_a (-0.511)
    # model_c (-0.721)
    # model_b (-1.161)

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
    assert project.get_model("model.modaryn_test.model_d").score == pytest.approx(1.253, abs=0.01)
    assert project.get_model("model.modaryn_test.complex_model").score == pytest.approx(1.140, abs=0.01)
    assert project.get_model("model.modaryn_test.model_a").score == pytest.approx(-0.511, abs=0.01)
    assert project.get_model("model.modaryn_test.model_c").score == pytest.approx(-0.721, abs=0.01)
    assert project.get_model("model.modaryn_test.model_b").score == pytest.approx(-1.161, abs=0.01)