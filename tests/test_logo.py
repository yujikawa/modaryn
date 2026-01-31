import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Mock rich.console.Console for testing output
@pytest.fixture
def mock_console():
    with patch("modaryn.outputs.logo.Console") as mock_console_cls:
        mock_instance = MagicMock()
        mock_console_cls.return_value = mock_instance
        yield mock_instance

# Mock the assets path to control logo.txt content
@pytest.fixture
def mock_logo_file(tmp_path):
    # Create a dummy assets directory within the temporary test path
    assets_dir = tmp_path / "modaryn" / "assets"
    assets_dir.mkdir(parents=True)
    
    # Create a dummy logo.txt file
    logo_file = assets_dir / "logo.txt"
    logo_file.write_text("TEST LOGO")
    
    # We need to patch Path(__file__) for the module under test
    # to point to a temporary location during the test.
    # This mock should simulate the structure:
    # tmp_path/modaryn/outputs/logo.py
    # so that the Path(__file__).parent.parent.parent logic resolves to tmp_path
    
    mock_logo_py_path = tmp_path / "modaryn" / "outputs" / "logo.py"
    mock_logo_py_path.parent.mkdir(parents=True, exist_ok=True)
    mock_logo_py_path.write_text("") # Content doesn't matter, just its existence for Path(__file__)
    
    with patch("modaryn.outputs.logo.__file__", str(mock_logo_py_path)):
        yield logo_file # Yield the actual logo file path created in tmp_path

def test_display_logo_prints_logo_from_file(mock_console, mock_logo_file):
    from modaryn.outputs.logo import display_logo 

    display_logo()
    mock_console.print.assert_called_once_with(mock_logo_file.read_text())