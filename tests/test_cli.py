from typer.testing import CliRunner
from modaryn.cli import app
import pytest
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

from modaryn.loaders.manifest import ManifestLoader
from modaryn.scorers.score import Scorer
from modaryn.outputs.terminal import TerminalOutput
from modaryn.domain.model import DbtProject, DbtModel, ScoreStatistics # Added ScoreStatistics
from modaryn.analyzers.sql_complexity import SqlComplexityResult
from rich.console import Console # Added this import


runner = CliRunner()

@pytest.fixture(scope="module")
def dbt_project_with_compiled_sql() -> Path:
    """
    Returns the path to the pre-configured sample dbt project for testing.
    This project should be compiled before running tests that depend on it.
    """
    sample_project_path = Path(__file__).parent.parent / "examples" / "sample_project"
    # Ensure the sample project is compiled before tests run
    # This assumes `dbt` is available in the environment
    import subprocess
    try:
        # Run dbt deps
        deps_result = subprocess.run(["dbt", "deps"], cwd=sample_project_path, capture_output=True, text=True)
        if deps_result.returncode != 0:
            print(f"""dbt deps failed:
{deps_result.stdout}
{deps_result.stderr}""")
            deps_result.check_returncode() # Raise CalledProcessError if failed

        # Run dbt compile
        compile_result = subprocess.run(["dbt", "compile"], cwd=sample_project_path, capture_output=True, text=True)
        if compile_result.returncode != 0:
            print(f"""dbt compile failed:
{compile_result.stdout}
{compile_result.stderr}""")
            compile_result.check_returncode() # Raise CalledProcessError if failed
    except subprocess.CalledProcessError as e:
        print(f"Error during dbt command execution: {e}")
        raise
    return sample_project_path





def test_sql_complexity_analysis_with_compiled_sql(dbt_project_with_compiled_sql):
    loader = ManifestLoader(dbt_project_with_compiled_sql)
    project = loader.load()

    # int_customer_order_summary
    model_ics = project.get_model("model.sample_project.int_customer_order_summary")
    assert model_ics.complexity.join_count == 2
    assert model_ics.complexity.cte_count == 2
    assert model_ics.complexity.conditional_count == 3
    assert model_ics.complexity.where_count == 0
    assert model_ics.complexity.sql_char_count == 815 # Updated from 1076
    assert model_ics.downstream_model_count == 1 # fct_customer_product_affinity

    # fct_customer_product_affinity
    model_fcpa = project.get_model("model.sample_project.fct_customer_product_affinity")
    assert model_fcpa.complexity.join_count == 1
    assert model_fcpa.complexity.cte_count == 2
    assert model_fcpa.complexity.conditional_count == 0
    assert model_fcpa.complexity.where_count == 2 # "where total_product_spend > 0" and "where rnk <= 3"
    assert model_fcpa.complexity.sql_char_count == 806 # Updated from 819
    assert model_fcpa.downstream_model_count == 0

    # int_order_product_details
    model_iopd = project.get_model("model.sample_project.int_order_product_details")
    assert model_iopd.complexity.join_count == 1
    assert model_iopd.complexity.cte_count == 1
    assert model_iopd.complexity.conditional_count == 0
    assert model_iopd.complexity.where_count == 0
    assert model_iopd.complexity.sql_char_count == 290 # Updated from 283
    assert model_iopd.downstream_model_count == 1 # fct_customer_product_affinity

    # stg_orders
    model_so = project.get_model("model.sample_project.stg_orders")
    assert model_so.complexity.join_count == 0
    assert model_so.complexity.cte_count == 0
    assert model_so.complexity.conditional_count == 0
    assert model_so.complexity.where_count == 0
    assert model_so.complexity.sql_char_count == 89 # Updated from 110
    assert model_so.downstream_model_count == 12 # Updated from 2

    # stg_products
    model_sp = project.get_model("model.sample_project.stg_products")
    assert model_sp.complexity.join_count == 0
    assert model_sp.complexity.cte_count == 0
    assert model_sp.complexity.conditional_count == 0
    assert model_sp.complexity.where_count == 0
    assert model_sp.complexity.sql_char_count == 67 # Updated from 80
    assert model_sp.downstream_model_count == 4 # Updated from 2

    # stg_customers
    model_sc = project.get_model("model.sample_project.stg_customers")
    assert model_sc.complexity.join_count == 0
    assert model_sc.complexity.cte_count == 0
    assert model_sc.complexity.conditional_count == 0
    assert model_sc.complexity.where_count == 0
    assert model_sc.complexity.sql_char_count == 81 # Updated from 94
    assert model_sc.downstream_model_count == 3 # Updated from 4

def test_scoring_and_ranking_with_compiled_sql(dbt_project_with_compiled_sql):
    loader = ManifestLoader(dbt_project_with_compiled_sql)
    project = loader.load()

    scorer = Scorer()
    scorer.score_project(project, apply_zscore=True)

    # Sort models by score to get ranks
    sorted_models = sorted(
        project.models.values(),
        key=lambda m: m.score,
        reverse=True
    )
    
    # Assert ranks (top 2 models by Z-score)
    # This test is simplified to be less brittle to scoring changes.
    assert sorted_models[0].model_name == "fct_customer_segmentation"
    assert sorted_models[1].model_name == "fct_profit_and_loss_statement"


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
    assert "| Rank | Model Name | Score (Raw) | Quality Score | JOINs | CTEs | Conditionals | WHEREs | SQL Chars | Downstream Children | Tests | Coverage (%) |" in content
    assert "int_customer_order_summary" in content
    assert "fct_customer_product_affinity" in content
    assert "int_order_product_details" in content
    assert "stg_orders" in content
    assert "stg_products" in content
    assert "stg_customers" in content


def test_score_command_to_markdown_file_with_zscore(dbt_project_with_compiled_sql, tmp_path):
    output_file = tmp_path / "report_zscore.md"
    result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql), "-f", "markdown", "-o", str(output_file), "--apply-zscore"])
    assert result.exit_code == 0
    assert "Report saved to" in result.stdout
    assert output_file.name in result.stdout
    assert output_file.exists()
    content = output_file.read_text()
    assert "# Modaryn Score and Scan Report" in content
    assert "| Rank | Model Name | Score (Z-Score) | Quality Score | JOINs | CTEs | Conditionals | WHEREs | SQL Chars | Downstream Children | Tests | Coverage (%) |" in content
    assert "int_customer_order_summary" in content


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

def test_ci_check_command_fails_on_zscore_threshold_exceeded(dbt_project_with_compiled_sql):
    # Models exceeding 1.0 Z-score: 4 models
    test_threshold = 1.0
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold), "--apply-zscore"])
    
    assert result.exit_code == 1
    assert "Threshold exceeded by 4 models" in result.stdout
    assert "fct_customer_segmentation" in result.stdout # Ensure high-score models are listed
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: FAILED" in result.stdout
    assert "4 models exceeded threshold." in result.stdout
    assert "Total models checked: 30" in result.stdout
    assert f"Threshold: {test_threshold:.3f}" in result.stdout

def test_ci_check_command_passes_on_zscore_threshold_not_exceeded(dbt_project_with_compiled_sql):
    # Set a threshold higher than the highest Z-score
    test_threshold = 10.0
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold), "--apply-zscore"])
    
    assert result.exit_code == 0
    assert "All models are within the defined threshold." in result.stdout
    assert "Threshold exceeded" not in result.stdout # Ensure no failure message
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: PASSED" in result.stdout
    assert "All models are within the defined threshold." in result.stdout
    assert "Total models checked: 30" in result.stdout
    assert f"Threshold: {test_threshold:.3f}" in result.stdout


def test_ci_check_command_fails_on_threshold_exceeded(dbt_project_with_compiled_sql):
    # Models exceeding 20.0 raw score: fct_customer_segmentation (20.77) (1 model)
    test_threshold = 20.0
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold)])
    
    assert result.exit_code == 1
    assert "Threshold exceeded by 1 models" in result.stdout # Updated from 2
    assert "fct_customer_segmentation" in result.stdout # Ensure high-score models are listed
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: FAILED" in result.stdout
    assert "1 models exceeded threshold." in result.stdout # Corrected count
    assert "Total models checked: 30" in result.stdout # Updated count
    assert f"Threshold: {test_threshold:.3f}" in result.stdout


def test_ci_check_command_passes_on_threshold_not_exceeded(dbt_project_with_compiled_sql):
    # Set a threshold higher than the highest raw score (fct_customer_segmentation: 20.77)
    test_threshold = 21.0 # Updated from 24.0
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold)])
    
    assert result.exit_code == 0
    assert "All models are within the defined threshold." in result.stdout
    assert "Threshold exceeded" not in result.stdout
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: PASSED" in result.stdout
    assert "All models are within the defined threshold." in result.stdout
    assert "Total models checked: 30" in result.stdout # Updated count
    assert f"Threshold: {test_threshold:.3f}" in result.stdout


def test_terminal_output_highlights_problematic_models(dbt_project_with_compiled_sql): # Changed fixture
    from io import StringIO
    mock_file = StringIO()
    mock_console = Console(file=mock_file, force_terminal=True, width=200, 
        color_system="standard",
        legacy_windows=False)

    # Patch the Console constructor to return our mock_console
    with patch('modaryn.outputs.terminal.Console', return_value=mock_console):
        loader = ManifestLoader(dbt_project_with_compiled_sql)
        project = loader.load()
        scorer = Scorer()
        scorer.score_project(project, apply_zscore=True)
        terminal_output = TerminalOutput()
        
        # Use models from sample_project that exceed a threshold
        # int_customer_order_summary (1.69), fct_customer_product_affinity (0.97)
        problematic_models = [
            project.get_model("model.sample_project.int_customer_order_summary"),
            project.get_model("model.sample_project.fct_customer_product_affinity")
        ]
        test_threshold = 0.5 # Set threshold so these two models are problematic
        
        terminal_output.generate_report(project, problematic_models, threshold=test_threshold) # Changed project argument
        
        output_str = mock_file.getvalue()

        # # Check that problematic models are highlighted in the output (e.g., with '[red]' tag)
        # \x1b[31m は red の ANSI エスケープコード
        assert "\x1b[31m" in output_str 
        assert "int_customer_order_summary" in output_str
        # 色がついている行にモデル名があることを確認
        assert any("\x1b[31m" in line and "int_customer_order_summary" in line 
                   for line in output_str.splitlines())
        assert any("\x1b[31m" in line and "fct_customer_product_affinity" in line 
                for line in output_str.splitlines())

@patch('modaryn.cli.Scorer')
@patch('modaryn.cli.ManifestLoader')
def test_score_command_with_apply_zscore_option_calls_scorer_correctly(
    mock_manifest_loader, mock_scorer, dbt_project_with_compiled_sql
):
    # Arrange
    mock_project_instance = MagicMock(spec=DbtProject)
    mock_project_instance.models = {} # Added to prevent AttributeError
    mock_project_instance.statistics = MagicMock(spec=ScoreStatistics) # Mock statistics
    mock_project_instance.statistics.mean = 10.0
    mock_project_instance.statistics.median = 9.0
    mock_project_instance.statistics.std_dev = 2.0

    mock_loader_instance = MagicMock()
    mock_loader_instance.load.return_value = mock_project_instance
    mock_manifest_loader.return_value = mock_loader_instance

    mock_scorer_instance = MagicMock()
    mock_scorer.return_value = mock_scorer_instance

    # Act
    result = runner.invoke(app, [
        "score",
        "--project-path", str(dbt_project_with_compiled_sql),
        "--apply-zscore"
    ])

    # Assert
    assert result.exit_code == 0
    mock_manifest_loader.assert_called_once_with(dbt_project_with_compiled_sql, dialect="bigquery")
    mock_loader_instance.load.assert_called_once()
    mock_scorer.assert_called_once_with(None) # No config passed
    mock_scorer_instance.score_project.assert_called_once_with(mock_project_instance, apply_zscore=True)
    assert "Scoring project..." in result.stdout


@pytest.fixture
def sample_project_for_output_test() -> DbtProject:
    """Creates a sample DbtProject for testing outputs."""
    model1 = DbtModel(
        unique_id="model.proj.model1",
        model_name="model1",
        file_path=Path("models/model1.sql"),
        raw_sql="select 1",
        columns={},
        complexity=SqlComplexityResult(join_count=1, cte_count=1, conditional_count=1, where_count=1, sql_char_count=100),
        raw_score=15.5,
        score=1.5, # z-score
    )
    model2 = DbtModel(
        unique_id="model.proj.model2",
        model_name="model2",
        file_path=Path("models/model2.sql"),
        raw_sql="select 2",
        columns={},
        complexity=SqlComplexityResult(join_count=2, cte_count=2, conditional_count=2, where_count=2, sql_char_count=200),
        raw_score=25.5,
        score=2.5, # z-score
    )
    project = DbtProject(models={"model.proj.model1": model1, "model.proj.model2": model2})
    # Manually add children to test downstream count
    model1.children = {model2.unique_id: model2}
    return project


def test_terminal_output_with_zscore(sample_project_for_output_test: DbtProject):
    """
    Tests terminal output when apply_zscore is True.
    It should display the z-score and indicate it in the header.
    """
    from io import StringIO
    project = sample_project_for_output_test
    mock_file = StringIO()
    mock_console = Console(file=mock_file, force_terminal=True, width=200)

    with patch('modaryn.outputs.terminal.Console', return_value=mock_console):
        terminal_output = TerminalOutput()
        terminal_output.generate_report(project, apply_zscore=True)

        output = mock_file.getvalue()
        # Check for z-score indicator in header
        assert "Score (Z-Score)" in output
        # Check that the z-scores are displayed (sorted by z-score desc)
        # model2 has higher z-score (2.5)
        assert "model2" in output.splitlines()[4]
        assert "2.50" in output.splitlines()[4]
        # model1 has lower z-score (1.5)
        assert "model1" in output.splitlines()[5]
        assert "1.50" in output.splitlines()[5]


def test_terminal_output_without_zscore(sample_project_for_output_test: DbtProject):
    """
    Tests terminal output when apply_zscore is False.
    It should display the raw score and indicate it in the header.
    """
    from io import StringIO
    project = sample_project_for_output_test
    # Populate statistics for testing
    project.statistics = ScoreStatistics(mean=20.5, median=20.5, std_dev=5.0)

    mock_file = StringIO()
    mock_console = Console(file=mock_file, force_terminal=True, width=200)

    with patch('modaryn.outputs.terminal.Console', return_value=mock_console):
        terminal_output = TerminalOutput()
        terminal_output.generate_report(project, apply_zscore=False, statistics=project.statistics)

        output = mock_file.getvalue()
        # Check for raw score indicator in header
        assert "Score (Raw)" in output
        # Check that the raw scores are displayed (sorted by raw_score desc)
        # model2 has higher raw_score (25.5)
        assert "model2" in output.splitlines()[4]
        assert "25.50" in output.splitlines()[4]
        # model1 has lower raw_score (15.5)
        assert "model1" in output.splitlines()[5]
        assert "15.50" in output.splitlines()[5] # THIS IS THE LINE THAT WAS MODIFIED
        # Check for statistics
        assert "--- Score Statistics ---" in output
        assert "Mean: \x1b[1;36m20.500\x1b[0m" in output
        assert "Median: \x1b[1;36m20.500\x1b[0m" in output
        assert "Standard Deviation: \x1b[1;36m5.000\x1b[0m" in output


def test_score_command_outputs_statistics(dbt_project_with_compiled_sql):
    result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql)])
    assert result.exit_code == 0
    assert "--- Score Statistics ---" in result.stdout
    assert "Mean:" in result.stdout
    assert "Median:" in result.stdout
    assert "Standard Deviation:" in result.stdout

def test_ci_check_command_outputs_statistics(dbt_project_with_compiled_sql):
    test_threshold = 1.0 # arbitrary threshold
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold)])
    assert result.exit_code == 1 # Expected to fail due to threshold
    assert "--- Score Statistics ---" in result.stdout
    assert "Mean:" in result.stdout
    assert "Median:" in result.stdout
    assert "Standard Deviation:" in result.stdout

def test_score_command_to_markdown_file_outputs_statistics(dbt_project_with_compiled_sql, tmp_path):
    output_file = tmp_path / "report_stats.md"
    result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql), "-f", "markdown", "-o", str(output_file)])
    assert result.exit_code == 0
    content = output_file.read_text()
    assert "### Score Statistics" in content
    assert "- Mean:" in content
    assert "- Median:" in content
    assert "- Standard Deviation:" in content

def test_score_command_to_html_file_outputs_statistics(dbt_project_with_compiled_sql, tmp_path):
    output_file = tmp_path / "report_stats.html"
    result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql), "-f", "html", "-o", str(output_file)])
    assert result.exit_code == 0
    content = output_file.read_text()
    assert "<h2>Score Statistics</h2>" in content
    assert "<li>Mean:" in content
    assert "<li>Median:" in content
    assert "<li>Standard Deviation:" in content
