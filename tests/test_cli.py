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

    # int_orders_enriched: 2 JOINs, 5 CTEs, no conditionals, no WHERE
    model_ioe = project.get_model("model.sample_project.int_orders_enriched")
    assert model_ioe.complexity.join_count == 2
    assert model_ioe.complexity.cte_count == 5
    assert model_ioe.complexity.conditional_count == 0
    assert model_ioe.complexity.where_count == 0
    assert model_ioe.complexity.sql_char_count == 987
    assert model_ioe.downstream_model_count == 7

    # fct_customer_churn_risk: complex model with many WHEN branches
    model_fcr = project.get_model("model.sample_project.fct_customer_churn_risk")
    assert model_fcr.complexity.join_count == 2
    assert model_fcr.complexity.cte_count == 4
    assert model_fcr.complexity.conditional_count == 14
    assert model_fcr.complexity.where_count == 0
    assert model_fcr.complexity.sql_char_count == 1882
    assert model_fcr.downstream_model_count == 0

    # stg_orders: simple staging model, no JOINs/CTEs/conditions
    model_so = project.get_model("model.sample_project.stg_orders")
    assert model_so.complexity.join_count == 0
    assert model_so.complexity.cte_count == 0
    assert model_so.complexity.conditional_count == 0
    assert model_so.complexity.where_count == 0
    assert model_so.complexity.sql_char_count == 166
    assert model_so.downstream_model_count == 3

    # stg_products: simple staging model
    model_sp = project.get_model("model.sample_project.stg_products")
    assert model_sp.complexity.join_count == 0
    assert model_sp.complexity.cte_count == 0
    assert model_sp.complexity.conditional_count == 0
    assert model_sp.complexity.where_count == 0
    assert model_sp.complexity.sql_char_count == 242
    assert model_sp.downstream_model_count == 2

    # stg_customers: simple staging model
    model_sc = project.get_model("model.sample_project.stg_customers")
    assert model_sc.complexity.join_count == 0
    assert model_sc.complexity.cte_count == 0
    assert model_sc.complexity.conditional_count == 0
    assert model_sc.complexity.where_count == 0
    assert model_sc.complexity.sql_char_count == 157
    assert model_sc.downstream_model_count == 3




def test_score_command_with_project_path(dbt_project_with_compiled_sql):
    result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql)])
    assert result.exit_code == 0
    assert "Loading dbt project:" in result.stdout
    assert "Scoring project" in result.stdout
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
    assert "| Rank | Model Name | Score (Raw) | Quality Score | JOINs | CTEs | Conditionals | WHEREs | SQL Chars | Downstream Children | Col. Down | Tests | Coverage (%) |" in content
    assert "fct_customer_churn_risk" in content
    assert "int_orders_enriched" in content
    assert "stg_orders" in content
    assert "stg_products" in content
    assert "stg_customers" in content


def test_score_command_to_markdown_file_with_zscore(dbt_project_with_compiled_sql, tmp_path):
    output_file = tmp_path / "report_zscore.md"
    result = runner.invoke(app, ["score", "--project-path", str(dbt_project_with_compiled_sql), "-f", "markdown", "-o", str(output_file), "--apply-zscore"])
    assert result.exit_code == 0
    assert "Report saved to" in result.stdout
    assert output_file.name in result.stdout.replace("\x1b[1;36m", "").replace("\x1b[0m", "").replace("\n", "")
    assert output_file.exists()
    content = output_file.read_text()
    assert "# Modaryn Score and Scan Report" in content
    assert "| Rank | Model Name | Score (Z-Score) | Quality Score | JOINs | CTEs | Conditionals | WHEREs | SQL Chars | Downstream Children | Col. Down | Tests | Coverage (%) |" in content
    assert "fct_customer_churn_risk" in content


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
    # Models exceeding 1.0 Z-score: 5 models (fct_customer_churn_risk, fct_customer_ltv, int_orders_enriched, fct_attribution, int_customer_order_metrics)
    test_threshold = 1.0
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold), "--apply-zscore"])

    assert result.exit_code == 1
    assert "Threshold exceeded by 5 models" in result.stdout
    assert "fct_customer_churn_risk" in result.stdout
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: FAILED" in result.stdout
    assert "5 models exceeded threshold." in result.stdout
    assert "Total models checked: 28" in result.stdout
    assert f"Threshold: {test_threshold:.3f}" in result.stdout

def test_ci_check_command_passes_on_zscore_threshold_not_exceeded(dbt_project_with_compiled_sql):
    # Set a threshold higher than the highest Z-score (fct_customer_churn_risk: 2.65)
    test_threshold = 10.0
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold), "--apply-zscore"])

    assert result.exit_code == 0
    assert "All models are within the defined threshold." in result.stdout
    assert "Threshold exceeded" not in result.stdout
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: PASSED" in result.stdout
    assert "Total models checked: 28" in result.stdout
    assert f"Threshold: {test_threshold:.3f}" in result.stdout


def test_ci_check_command_fails_on_threshold_exceeded(dbt_project_with_compiled_sql):
    # Models exceeding 35.0 raw score: fct_customer_churn_risk (39.32) (1 model)
    test_threshold = 35.0
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold)])

    assert result.exit_code == 1
    assert "Threshold exceeded by 1 models" in result.stdout
    assert "fct_customer_churn_risk" in result.stdout
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: FAILED" in result.stdout
    assert "1 models exceeded threshold." in result.stdout
    assert "Total models checked: 28" in result.stdout
    assert f"Threshold: {test_threshold:.3f}" in result.stdout


def test_ci_check_command_passes_on_threshold_not_exceeded(dbt_project_with_compiled_sql):
    # Set a threshold higher than the highest raw score (fct_customer_churn_risk: 39.32)
    test_threshold = 45.0
    result = runner.invoke(app, ["ci-check", "--project-path", str(dbt_project_with_compiled_sql), "--threshold", str(test_threshold)])

    assert result.exit_code == 0
    assert "All models are within the defined threshold." in result.stdout
    assert "Threshold exceeded" not in result.stdout
    assert "--- CI Check Summary ---" in result.stdout
    assert "Status: PASSED" in result.stdout
    assert "Total models checked: 28" in result.stdout
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
        # fct_customer_churn_risk (2.65), fct_customer_ltv (1.95)
        problematic_models = [
            project.get_model("model.sample_project.fct_customer_churn_risk"),
            project.get_model("model.sample_project.fct_customer_ltv")
        ]
        test_threshold = 1.5

        terminal_output.generate_report(project, problematic_models, threshold=test_threshold)

        output_str = mock_file.getvalue()

        # \x1b[31m は red の ANSI エスケープコード
        assert "\x1b[31m" in output_str
        assert "fct_customer_churn_risk" in output_str
        assert any("\x1b[31m" in line and "fct_customer_churn_risk" in line
                   for line in output_str.splitlines())
        assert any("\x1b[31m" in line and "fct_customer_ltv" in line
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
    mock_loader_instance.dialect = "duckdb"
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
    mock_manifest_loader.assert_called_once_with(dbt_project_with_compiled_sql, dialect=None)
    mock_loader_instance.load.assert_called_once()
    mock_scorer.assert_called_once_with(None) # No config passed
    mock_scorer_instance.score_project.assert_called_once_with(mock_project_instance, apply_zscore=True)
    assert "Scoring project" in result.stdout


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
        assert "Score(Z)" in output
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
        assert "Score(Raw)" in output
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
