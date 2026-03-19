# modaryn
![modaryn](https://raw.githubusercontent.com/yujikawa/modaryn/main/docs/assets/header.png)

[![PyPI version](https://img.shields.io/pypi/v/modaryn.svg)](https://pypi.org/project/modaryn/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![dbt](https://img.shields.io/badge/dbt-compatible-orange.svg)](https://www.getdbt.com/)
[![sqlglot](https://img.shields.io/badge/powered%20by-sqlglot-blueviolet.svg)](https://github.com/tobymao/sqlglot)

modaryn analyzes dbt projects to score model complexity and structural importance,
helping teams identify high-risk and high-impact data models.

### Overview
`modaryn` is a Python-based CLI tool that analyzes dbt projects and scores each model based on three pillars:

- **Complexity** — SQL metrics (JOINs, CTEs, conditionals, WHERE clauses, character count)
- **Importance** — Structural metrics (downstream model/column counts)
- **Quality** — Test coverage metrics (test count, column coverage %)

**Final score:** `raw_score = complexity_score + importance_score - quality_score` (higher = riskier)

The SQL dialect is auto-detected from `manifest.json`. Column-level lineage is traced via `sqlglot` to compute downstream column impact.

### Installation
```bash
pip install modaryn
```

### Usage

#### `score` command
Analyzes and scores all dbt models, displaying a combined scan and score report.

```bash
modaryn score --project-path . --apply-zscore --format html --output report.html
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--project-path` | `-p` | Path to the dbt project directory | `.` |
| `--dialect` | `-d` | SQL dialect (`bigquery`, `snowflake`, `duckdb`, etc.). Auto-detected from `manifest.json` if omitted. | auto |
| `--config` | `-c` | Path to a custom weights YAML file | `None` |
| `--apply-zscore` | `-z` | Apply Z-score normalization to scores | `False` |
| `--format` | `-f` | Output format: `terminal`, `markdown`, `html` | `terminal` |
| `--output` | `-o` | Path to write the output file | `None` |
| `--select` | `-s` | Filter models by selector (repeatable, OR logic) | `None` |
| `--verbose` | `-v` | Show detailed warnings (missing SQL, skipped columns) | `False` |

**`--select` selector syntax:**
```bash
# Model name glob
modaryn score --project-path . --select "fct_*"

# Path prefix
modaryn score --project-path . --select path:marts/finance

# dbt tag
modaryn score --project-path . --select tag:daily

# Multiple selectors (OR logic)
modaryn score --project-path . --select path:marts/customer --select path:marts/finance
```

---

#### `ci-check` command
Checks model scores against a threshold for use in CI/CD pipelines. Exits with code `1` if any model exceeds the threshold, `0` otherwise.

```bash
modaryn ci-check --project-path . --threshold 20.0 --apply-zscore
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--project-path` | `-p` | Path to the dbt project directory | `.` |
| `--threshold` | `-t` | Maximum allowed score (**required**) | — |
| `--dialect` | `-d` | SQL dialect. Auto-detected if omitted. | auto |
| `--config` | `-c` | Path to a custom weights YAML file | `None` |
| `--apply-zscore` | `-z` | Check against Z-scores instead of raw scores | `False` |
| `--format` | `-f` | Output format: `terminal`, `markdown`, `html` | `terminal` |
| `--output` | `-o` | Path to write the output file | `None` |
| `--select` | `-s` | Filter models by selector (repeatable, OR logic) | `None` |
| `--verbose` | `-v` | Show detailed warnings | `False` |

---

#### `impact` command
Traces all downstream columns affected by a change to a specific column (BFS column-level impact analysis).

```bash
modaryn impact --project-path . --model fct_orders --column order_id
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--project-path` | `-p` | Path to the dbt project directory | `.` |
| `--model` | `-m` | Model name to trace impact from (**required**) | — |
| `--column` | `-c` | Column name to trace impact from (**required**) | — |
| `--dialect` | `-d` | SQL dialect. Auto-detected if omitted. | auto |
| `--select` | `-s` | Filter models by selector (restricts lineage scope) | `None` |
| `--verbose` | `-v` | Show detailed warnings | `False` |

---

### Missing compiled SQL (N/A columns)

Complexity metrics require compiled SQL from `target/compiled/`. If `dbt compile` has not been run or a model failed to compile, those columns will show `N/A` in the report. A warning summary is printed at the end of the output. Use `--verbose` to see the full list of affected models.

```
⚠ 3 model(s) show N/A for complexity columns because compiled SQL was not found.
Run `dbt compile` to enable full analysis: model_a, model_b, model_c
```

---

### Report Columns and Calculation Logic

#### 1. SQL Complexity Metrics

| Metric | Calculation | Example |
|--------|-------------|---------|
| **JOINs** | Count of all `JOIN` clauses | `JOIN`, `LEFT JOIN`, `CROSS JOIN` each count as 1 |
| **CTEs** | Count of all CTEs defined | `WITH a AS (...), b AS (...)` = 2 |
| **Conditionals** | Count of `IF` expressions (each `WHEN` branch in a `CASE`) | A `CASE WHEN ... WHEN ... END` with 2 branches = 2 |
| **WHEREs** | Count of `WHERE` clauses including subqueries | Main `WHERE` + subquery `WHERE` = 2 |
| **SQL Chars** | Total character count of the compiled SQL | — |

#### 2. Structural Importance Metrics

| Metric | Calculation | Example |
|--------|-------------|---------|
| **Downstream** | Number of dbt models that directly reference this model | Models B and C use A → A has **2** |
| **Col. Down** | Total count of downstream column references | B's `col1` and `col2` both reference A's `id` → **2** |

#### 3. Quality Metrics

| Metric | Calculation | Example |
|--------|-------------|---------|
| **Tests** | Total dbt tests attached to the model | 4 column tests → **4** |
| **Coverage (%)** | % of columns with at least one test | 8 of 10 columns tested → **80%** |

---

### Scoring Formula

1. **Complexity Score** = `(JOINs × w1) + (CTEs × w2) + (Conditionals × w3) + (WHEREs × w4) + (Chars × w5)`
2. **Importance Score** = `(Downstream Models × w6) + (Col. Down × w7)`
3. **Quality Score** = `(Tests × w8) + (Coverage % × w9)`

**Raw Score** = `Complexity Score + Importance Score − Quality Score` (minimum 0)

#### Z-Score Normalization
When `--apply-zscore` is used:
`Z-Score = (Raw Score − Mean) / Standard Deviation`

---

### Custom Weights Configuration

Override default weights by passing a YAML file via `--config`:

```yaml
sql_complexity:
  join_count: 2.0
  cte_count: 1.5
  conditional_count: 1.0
  where_count: 0.5
  sql_char_count: 0.01

importance:
  downstream_model_count: 1.0

quality:
  test_count: 0.5
  column_coverage: 1.0
```

Unknown sections or keys are reported as warnings at runtime.

---

![modaryn](https://raw.githubusercontent.com/yujikawa/modaryn/main/docs/assets/result.png)

![modaryn](https://raw.githubusercontent.com/yujikawa/modaryn/main/docs/assets/result2.png)
