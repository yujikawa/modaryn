from modaryn.domain.model import DbtModel, SqlComplexityResult
from pathlib import Path
import pytest

def test_dbtmodel_has_raw_score_and_z_score_fields():
    # Arrange
    unique_id = "model.test.my_model"
    model_name = "my_model"
    file_path = Path("/path/to/my_model.sql")
    raw_sql = "SELECT 1 AS id"
    
    # Act
    model = DbtModel(
        unique_id=unique_id,
        model_name=model_name,
        file_path=file_path,
        raw_sql=raw_sql,
        raw_score=10.5, # This should fail if raw_score doesn't exist
        score=2.3 # This is the existing 'score' field, to be used for z-score
    )

    # Assert
    assert model.unique_id == unique_id
    assert model.raw_score == 10.5
    assert model.score == 2.3 # This is now explicitly the z-score

def test_dbtmodel_default_raw_score_is_zero():
    unique_id = "model.test.my_model"
    model_name = "my_model"
    file_path = Path("/path/to/my_model.sql")
    raw_sql = "SELECT 1 AS id"
    model = DbtModel(
        unique_id=unique_id,
        model_name=model_name,
        file_path=file_path,
        raw_sql=raw_sql,
    )
    assert model.raw_score == 0.0

