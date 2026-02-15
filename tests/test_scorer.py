from modaryn.scorers.score import Scorer
from modaryn.domain.model import DbtProject, DbtModel, SqlComplexityResult
from pathlib import Path
import pytest
import numpy as np

# Helper function to create a dummy DbtProject for testing
def create_dummy_project(model_data):
    project = DbtProject()
    for unique_id, data in model_data.items():
        model = DbtModel(
            unique_id=unique_id,
            model_name=data['model_name'],
            file_path=Path(f"/path/to/{data['model_name']}.sql"),
            raw_sql="SELECT 1",
            complexity=SqlComplexityResult(
                join_count=data.get('join_count', 0),
                cte_count=data.get('cte_count', 0),
                conditional_count=data.get('conditional_count', 0),
                where_count=data.get('where_count', 0),
                sql_char_count=data.get('sql_char_count', 0)
            )
        )
        project.models[unique_id] = model
    return project


def test_score_project_accepts_apply_zscore_argument():
    # Arrange
    scorer = Scorer()
    project = create_dummy_project({
        "model.test.model_a": {"model_name": "model_a", "join_count": 1},
    })

    # Act & Assert
    # This call should fail if apply_zscore is not in the signature
    scorer.score_project(project, apply_zscore=True)
    # If it doesn't fail, we'll assert that it runs without error,
    # further checks will be in later tests for actual z-score logic.
    assert True

def test_score_project_calculates_raw_scores_correctly():
    scorer = Scorer()
    project = create_dummy_project({
        "model.test.model_a": {"model_name": "model_a", "join_count": 1, "cte_count": 0, "conditional_count": 0, "where_count": 0, "sql_char_count": 0},
        "model.test.model_b": {"model_name": "model_b", "join_count": 0, "cte_count": 1, "conditional_count": 0, "where_count": 0, "sql_char_count": 0},
    })
    
    # Assuming default weights for simplicity (join_count: 1, cte_count: 1)
    # raw_score_a = 1 * 1 = 1
    # raw_score_b = 1 * 1 = 1
    
    # Force weights to known values for predictable raw score calculation
    scorer.weights = {
        "sql_complexity": {
            "join_count": 1.0,
            "cte_count": 1.0,
            "conditional_count": 1.0,
            "where_count": 1.0,
            "sql_char_count": 0.01,
        },
        "importance": {
            "downstream_model_count": 1.0
        }
    }

    scorer.score_project(project, apply_zscore=False) # Important: do not apply z-score yet

    assert project.models["model.test.model_a"].raw_score == 1.0
    assert project.models["model.test.model_b"].raw_score == 1.0
    assert project.models["model.test.model_a"].score == 0.0 # score (z-score) should remain default
    assert project.models["model.test.model_b"].score == 0.0 # score (z-score) should remain default

def test_score_project_applies_z_scores_when_enabled():
    scorer = Scorer()
    project = create_dummy_project({
        "model.test.model_x": {"model_name": "model_x", "join_count": 1, "cte_count": 0, "conditional_count": 0, "where_count": 0, "sql_char_count": 0}, # raw score = 1
        "model.test.model_y": {"model_name": "model_y", "join_count": 2, "cte_count": 0, "conditional_count": 0, "where_count": 0, "sql_char_count": 0}, # raw score = 2
        "model.test.model_z": {"model_name": "model_z", "join_count": 3, "cte_count": 0, "conditional_count": 0, "where_count": 0, "sql_char_count": 0}, # raw score = 3
    })

    # Force weights to known values
    scorer.weights = {
        "sql_complexity": {
            "join_count": 1.0,
            "cte_count": 1.0,
            "conditional_count": 1.0,
            "where_count": 1.0,
            "sql_char_count": 0.01,
        },
        "importance": {
            "downstream_model_count": 1.0
        }
    }

    scorer.score_project(project, apply_zscore=True)

    raw_scores = [1.0, 2.0, 3.0]
    mean_raw_score = np.mean(raw_scores) # 2.0
    std_dev_raw_score = np.std(raw_scores) # sqrt(((1-2)^2 + (2-2)^2 + (3-2)^2) / 3) = sqrt(2/3) approx 0.816

    # Z-scores
    # model_x: (1 - 2) / 0.816 = -1.224
    # model_y: (2 - 2) / 0.816 = 0.0
    # model_z: (3 - 2) / 0.816 = 1.224

    assert project.models["model.test.model_x"].raw_score == 1.0
    assert pytest.approx(project.models["model.test.model_x"].score, abs=1e-3) == -1.224
    
    assert project.models["model.test.model_y"].raw_score == 2.0
    assert pytest.approx(project.models["model.test.model_y"].score, abs=1e-3) == 0.0

    assert project.models["model.test.model_z"].raw_score == 3.0
    assert pytest.approx(project.models["model.test.model_z"].score, abs=1e-3) == 1.224

def test_score_project_handles_zero_std_dev():
    scorer = Scorer()
    project = create_dummy_project({
        "model.test.model_a": {"model_name": "model_a", "join_count": 1},
        "model.test.model_b": {"model_name": "model_b", "join_count": 1},
    })
    
    scorer.weights = {
        "sql_complexity": { "join_count": 1.0 }, "importance": { "downstream_model_count": 1.0 }
    }

    scorer.score_project(project, apply_zscore=True)

    # If all raw scores are the same, std dev is 0, z-score should be 0
    assert project.models["model.test.model_a"].raw_score == 1.0
    assert project.models["model.test.model_a"].score == 0.0
    assert project.models["model.test.model_b"].raw_score == 1.0
    assert project.models["model.test.model_b"].score == 0.0


def test_score_project_calculates_statistics():
    scorer = Scorer()
    project = create_dummy_project({
        "model.test.model_1": {"model_name": "model_1", "join_count": 1}, # raw score = 1
        "model.test.model_2": {"model_name": "model_2", "join_count": 2}, # raw score = 2
        "model.test.model_3": {"model_name": "model_3", "join_count": 3}, # raw score = 3
        "model.test.model_4": {"model_name": "model_4", "join_count": 4}, # raw score = 4
        "model.test.model_5": {"model_name": "model_5", "join_count": 5}, # raw score = 5
    })
    
    scorer.weights = {
        "sql_complexity": { "join_count": 1.0 }, "importance": { "downstream_model_count": 1.0 }
    }

    scorer.score_project(project, apply_zscore=False) # Calculate raw scores and statistics

    assert project.statistics is not None
    # Raw scores: [1.0, 2.0, 3.0, 4.0, 5.0]
    # Mean: (1+2+3+4+5)/5 = 3.0
    # Median: 3.0
    # Std Dev: np.std([1,2,3,4,5]) = 1.4142135623730951

    assert pytest.approx(project.statistics.mean, abs=1e-3) == 3.0
    assert pytest.approx(project.statistics.median, abs=1e-3) == 3.0
    assert pytest.approx(project.statistics.std_dev, abs=1e-3) == 1.414

    # Test with empty project
    empty_project = DbtProject()
    scorer.score_project(empty_project)
    assert empty_project.statistics is None

    # Test with single model
    single_model_project = create_dummy_project({
        "model.test.single": {"model_name": "single", "join_count": 10},
    })
    scorer.weights = {
        "sql_complexity": { "join_count": 1.0 }, "importance": { "downstream_model_count": 1.0 }
    }
    scorer.score_project(single_model_project)
    assert single_model_project.statistics is not None
    assert pytest.approx(single_model_project.statistics.mean, abs=1e-3) == 10.0
    assert pytest.approx(single_model_project.statistics.median, abs=1e-3) == 10.0
    assert pytest.approx(single_model_project.statistics.std_dev, abs=1e-3) == 0.0

