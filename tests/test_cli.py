from typer.testing import CliRunner
from modaryn.cli import app
import pytest
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

from modaryn.loaders.manifest import ManifestLoader
from modaryn.scorers.score import Scorer
from modaryn.outputs.terminal import TerminalOutput
from modaryn.domain.model import DbtProject, DbtModel
from modaryn.analyzers.sql_complexity import SqlComplexityResult
from rich.console import Console # Added this import


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
          "model_name": "model_a",
          "path": "model_a.sql",
          "raw_code": "select 1 as id", # raw_code is still in manifest but we'll read compiled
          "depends_on": {
            "nodes": []
          }
        },
        "model.modaryn_test_project.model_b": {
          "unique_id": "model.modaryn_test_project.model_b",
          "resource_type": "model",
          "model_name": "model_b",
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
          "model_name": "model_c",
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
          "model_name": "model_d",
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
          "model_name": "complex_model",
          "path": "complex_model.sql", # Fixed typo here
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


@pytest.fixture
def mock_dbt_project() -> DbtProject:
    project = DbtProject(
        models={
            "model.test_project.model_a": DbtModel(
                unique_id="model.test_project.model_a",
                model_name="model_a",
                file_path=Path("models/model_a.sql"),
                raw_sql="SELECT 1",
                dependencies=[],
                complexity=SqlComplexityResult(
                    join_count=0,
                    cte_count=0,
                    conditional_count=0,
                    where_count=0,
                    sql_char_count=0,
                ),
                score=0.5
            ),
            "model.test_project.model_b": DbtModel(
                unique_id="model.test_project.model_b",
                model_name="model_b",
                file_path=Path("models/model_b.sql"),
                raw_sql="SELECT 2",
                dependencies=[],
                complexity=SqlComplexityResult(
                    join_count=0,
                    cte_count=0,
                    conditional_count=0,
                    where_count=0,
                    sql_char_count=0,
                ),
                score=1.5
            ),
            "model.test_project.model_c": DbtModel(
                unique_id="model.test_project.model_c",
                model_name="model_c",
                file_path=Path("models/model_c.sql"),
                raw_sql="SELECT 3",
                dependencies=[],
                complexity=SqlComplexityResult(
                    join_count=0,
                    cte_count=0,
                    conditional_count=0,
                    where_count=0,
                    sql_char_count=0,
                ),
                score=2.5
            ),
        }
    )
    return project


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
    assert project.get_model("model.modaryn_test_project.model_d").score == pytest.approx(1.348, abs=0.01)
    assert project.get_model("model.modaryn_test_project.complex_model").score == pytest.approx(1.039, abs=0.01)
    assert project.get_model("model.modaryn_test_project.model_a").score == pytest.approx(-0.565, abs=0.01)
    assert project.get_model("model.modaryn_test_project.model_c").score == pytest.approx(-0.689, abs=0.01)
    assert project.get_model("model.modaryn_test_project.model_b").score == pytest.approx(-1.134, abs=0.01)


def test_score_command_with_project_path(dbt_project_with_compiled_sql):
    result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql)])
    assert result.exit_code == 0
    assert "Loading dbt project:" in result.stdout
    assert "Scoring project..." in result.stdout
    # We can't reliably assert rich table content in stdout due to potential truncation/formatting.
    # We'll rely on file output tests for content verification.

def test_score_command_to_markdown_file(dbt_project_with_compiled_sql, tmp_path):
    output_file = tmp_path / "report.md"
    result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql), "-f", "markdown", "-o", str(output_file)])
    assert result.exit_code == 0
    assert "Report saved to" in result.stdout
    assert output_file.name in result.stdout
    assert output_file.exists()
    content = output_file.read_text()
    assert "# Modaryn Score and Scan Report" in content
    assert "| Rank | Model Name | Score (Z-Score) | JOINs | CTEs | Conditionals | WHEREs | SQL Chars | Downstream Children |" in content
    assert "model_d" in content
    assert "complex_model" in content
    assert "model_a" in content
    assert "model_c" in content
    assert "model_b" in content


def test_naked_invoke_shows_logo():
    with patch("modaryn.cli.display_logo_and_version") as mock_display_logo_and_version:
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        mock_display_logo_and_version.assert_called_once_with(app.info.version)

def test_invoke_with_command_does_not_show_logo(dbt_project_with_compiled_sql):
    with patch("modaryn.cli.display_logo_and_version") as mock_display_logo_and_version:
        result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql)])
        assert result.exit_code == 0
        mock_display_logo_and_version.assert_not_called()

def test_ci_check_command_is_listed_in_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ci-check" in result.stdout

def test_ci_check_command_fails_on_threshold_exceeded(dbt_project_with_compiled_sql):
    # This project has model_d (score 1.351) and complex_model (score 1.148) as highest scores
    # Let's set a threshold that model_d will exceed (e.g., 1.0)
    test_threshold = 1.0
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold)])
    
    assert result.exit_code == 1
    assert "Threshold exceeded by 2 models" in result.stdout
    assert "model_d" in result.stdout
    assert "complex_model" in result.stdout
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: FAILED" in result.stdout
    assert "2 models exceeded threshold." in result.stdout
    assert "Total models checked: 5" in result.stdout
    assert f"Threshold: {test_threshold:.3f}" in result.stdout

def test_ci_check_command_passes_on_threshold_not_exceeded(dbt_project_with_compiled_sql):
    # Set a threshold higher than the highest score (model_d: 1.351)
    test_threshold = 1.4
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold)])
    
    assert result.exit_code == 0
    assert "All models are within the defined threshold." in result.stdout
    assert "Threshold exceeded" not in result.stdout # Ensure no failure message
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: PASSED" in result.stdout
    assert "All models are within the defined threshold." in result.stdout
    assert "Total models checked: 5" in result.stdout
    assert f"Threshold: {test_threshold:.3f}" in result.stdout


def test_terminal_output_highlights_problematic_models(mock_dbt_project):
    from io import StringIO
    mock_file = StringIO()
    mock_console = Console(file=mock_file)

    # Patch the Console constructor to return our mock_console
    with patch('modaryn.outputs.terminal.Console', return_value=mock_console):
        terminal_output = TerminalOutput()
        problematic_models = [mock_dbt_project.get_model("model.test_project.model_b"), mock_dbt_project.get_model("model.test_project.model_c")]
        test_threshold = 1.0
        
        terminal_output.generate_report(mock_dbt_project, problematic_models, threshold=test_threshold)
        
        output_str = mock_file.getvalue()

        # Check that problematic models are highlighted in the output (e.g., with '[red]' tag)
        assert "model_c" in output_str
        assert "model_b" in output_str
        assert "model_a" in output_str and "[red]model_a[/red]" not in output_str # Ensure it's not red
        
        # Assert summary content
        assert "--- CI Check Summary ---" in output_str
        assert "Status: FAILED" in output_str
        assert f"- {len(problematic_models)} models exceeded threshold." in output_str
        assert f"Total models checked: {len(mock_dbt_project.models)}" in output_str
        assert f"Threshold: {test_threshold:.3f}" in output_str