# Technology Stack

## Architecture

`modaryn` is a monolithic command-line application built on Python. It follows a standard layered architecture, separating concerns into data loading, analysis, scoring, and output generation.

## Core Technologies

- **Language**: Python 3.9+
- **Framework**: Typer (for the CLI)
- **Runtime**: Python

## Key Libraries

- **SQL Parsing**: `sqlglot` is used for parsing and analyzing SQL queries.
- **CLI UI**: `rich` provides rich text and beautiful formatting in the terminal.
- **Configuration**: `pyyaml` handles the loading of YAML configuration files.
- **Templating**: `jinja2` is used for generating reports from templates.
- **Data Manipulation**: `pandas` and `numpy` are used for data manipulation and calculations.
- **Plotting**: `plotly` is used for generating visualizations in HTML reports.

## Development Standards

### Type Safety
The project uses Python's type hints for better code clarity and maintainability, though it is not strictly enforced at runtime.

### Code Quality
The project does not currently have a standardized linter or formatter configured (e.g., Black, Ruff).

### Testing
- **Framework**: `pytest`
- **Location**: Tests are located in the `tests/` directory.

## Development Environment

### Required Tools
- `uv`: For dependency management.

### Common Commands
```bash
# Install dependencies
uv pip install -e .

# Run tests
pytest
```

## Key Technical Decisions

- **CLI Framework**: The choice of `Typer` simplifies the creation of a clean and user-friendly command-line interface.
- **SQL Parsing**: Using `sqlglot` provides a robust and efficient way to parse and analyze dbt models without executing them.
- **Dependency Management**: `uv` is used for fast and efficient dependency management.

---
_Document standards and patterns, not every dependency_
