# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Modaryn** is a Python CLI tool that analyzes dbt projects and scores each model based on three pillars:
- **Complexity** — SQL metrics (JOINs, CTEs, conditionals, WHERE clauses, char count)
- **Importance** — Structural metrics (downstream model/column counts)
- **Quality** — Test coverage metrics (test count, column coverage %)

Final score: `raw_score = complexity_score + importance_score - quality_score` (higher = riskier)

## Commands

```bash
# Install dependencies
uv pip install -e ".[test]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_scorer.py

# Run a single test
pytest tests/test_scorer.py::test_function_name

# CLI usage
modaryn score --project-path . --dialect bigquery --apply-zscore --format html --output report.html
modaryn ci-check --project-path . --threshold 20.0 --apply-zscore
```

## Architecture

**Processing pipeline:**

1. `loaders/manifest.py` — `ManifestLoader` reads `dbt_project.yml` + `target/manifest.json`, loads compiled SQL from `target/compiled/`, and builds the dependency graph with test associations.

2. `analyzers/sql_complexity.py` — `SqlComplexityAnalyzer` uses `sqlglot` to parse SQL and extract metrics into `SqlComplexityResult`.

3. `analyzers/lineage.py` — `LineageAnalyzer` performs column-level lineage tracing via `sqlglot.lineage`, mapping upstream columns to downstream columns across models.

4. `scorers/score.py` — `Scorer` loads weights from `config/default.yml` (overridable via `--config`), computes scores, and optionally applies Z-score normalization.

5. `outputs/` — Output generators inherit from `OutputGenerator` (ABC in `outputs/__init__.py`). Implementations: `TerminalOutput` (Rich tables), `MarkdownOutput`, `HtmlOutput` (Jinja2 + Vis.js).

**Domain models** (`domain/model.py`): `DbtProject` → `DbtModel` → `DbtColumn` → `ColumnReference`. `ScoreStatistics` holds mean/median/std_dev for the score distribution.

**Configuration** (`config/default.yml`): Default weights for all scoring factors. Users can override with a custom YAML via `--config`.
