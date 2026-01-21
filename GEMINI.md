# Project Overview: modaryn

`modaryn` is a Python-based Command Line Interface (CLI) tool designed to analyze dbt (data build tool) projects. Its primary purpose is to score the complexity and structural importance of dbt models, helping data teams identify high-risk and high-impact data models within their projects.

The tool leverages `sqlglot` for SQL parsing, `typer` for building the CLI, and `rich` for enhanced terminal output. It also uses `pyyaml` for configuration, `jinja2` for templating, and `plotly`, `numpy`, `pandas` for potential future data visualization and manipulation.

## Core Components:

*   **Loaders:** Reads the dbt `manifest.json` file to construct an in-memory representation of the dbt project, including models, their SQL content, and dependencies.
*   **Analyzers:**
    *   `SqlComplexityAnalyzer`: Parses the raw SQL of dbt models to extract complexity metrics such as the number of `JOIN`s and Common Table Expressions (CTEs).
*   **Scorers:** Calculates a combined score for each dbt model based on its SQL complexity and structural importance (e.g., number of downstream models). This scoring uses configurable weights defined in a YAML file.
*   **Outputs:** Provides various output formats for the analysis results, including terminal tables, Markdown, and HTML reports.

## Building and Running

### Installation

The project uses `uv` for dependency management. To install dependencies:

```bash
uv pip install -e .
```

### Commands

The `modaryn` CLI provides the following commands:

*   **`modaryn scan`**: Scans a dbt project and displays basic model information.
    *   `--manifest-path`, `-m`: Path to the dbt `manifest.json` file (default: `target/manifest.json`).
    *   `--format`, `-f`: Output format (`terminal`, `markdown`).
    *   `--output`, `-o`: Path to write the output file (for `markdown` format).
    Example:
    ```bash
    modaryn scan -m target/manifest.json -f markdown -o modaryn_scan_report.md
    ```

*   **`modaryn score`**: Scores dbt models based on complexity and importance.
    *   `--manifest-path`, `-m`: Path to the dbt `manifest.json` file (default: `target/manifest.json`).
    *   `--config`, `-c`: Path to a custom weights configuration YAML file (e.g., `custom_weights.yml`).
    *   `--format`, `-f`: Output format (`terminal`, `markdown`, `html`).
    *   `--output`, `-o`: Path to write the output file.
    Example:
    ```bash
    modaryn score -m target/manifest.json -c custom_weights.yml -f html -o modaryn_report.html
    ```

## Configuration

Default scoring weights are defined in `modaryn/config/default.yml`. Users can provide a custom YAML file (e.g., `custom_weights.yml`) to override these defaults. The custom file only needs to specify the weights it intends to change.

Example `custom_weights.yml`:
```yaml
sql_complexity:
  join_count: 3.0
  cte_count: 2.0
importance:
  downstream_model_count: 1.5
```

## Development Conventions

*   **Language:** Python 3.9+
*   **CLI Framework:** `typer`
*   **SQL Parsing:** `sqlglot`
*   **Data Structures:** Uses `dataclasses` for representing dbt models and projects.
*   **Dependency Management:** `uv`
*   **Project Structure:** Modular, with separate directories for analyzers, loaders, outputs, and scorers.