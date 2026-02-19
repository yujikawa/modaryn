# modaryn
![modaryn](./docs/assets/header.png)
modaryn analyzes dbt projects to score model complexity and structural importance,
helping teams identify high-risk and high-impact data models.

### Overview
`modaryn` is a Python-based Command Line Interface (CLI) tool designed to analyze dbt (data build tool) projects. Its primary purpose is to score the complexity and structural importance of dbt models, helping data teams identify high-risk and high-impact data models within their projects. It now extracts detailed complexity metrics such as `JOIN` counts, CTE counts, conditional statements (`CASE`, `IF`), `WHERE` clause counts, and SQL character length, and ranks models using Z-scores.

### Installation
The project uses `uv` for dependency management. To install dependencies, run:
```bash
uv pip install git+https://github.com/yujikawa/modaryn.git
```

### Usage
The `modaryn` CLI provides the following commands:

#### `score` command
Analyzes and scores dbt models based on complexity and importance, displaying combined scan and score information.
```bash
modaryn score --project-path . --dialect bigquery --config custom_weights.yml --apply-zscore --format html --output modaryn_report.html
```
- `--project-path` / `-p`: Path to the dbt project directory. (Type: Path, Default: `.`)
- `--dialect` / `-d`: The SQL dialect to use for parsing (e.g., `bigquery`, `snowflake`, `redshift`). (Type: str, Default: `bigquery`)
- `--config` / `-c`: Path to a custom weights configuration YAML file. (Type: Optional[Path], Default: `None`)
- `--apply-zscore` / `-z`: Apply Z-score transformation to model scores. When this flag is present, scores will be Z-score normalized. Otherwise, raw scores are used. (Type: bool, Default: `False`)
- `--format` / `-f`: Output format. Available options: `terminal`, `markdown`, `html`. (Type: OutputFormat, Default: `terminal`)
- `--output` / `-o`: Path to write the output file. If not specified, output is printed to stdout. (Type: Optional[Path], Default: `None`)

#### dbt Test Coverage Evaluation
`modaryn` now incorporates dbt test coverage into its scoring mechanism, providing a "Quality Score" for each model. This score reflects the extent to which a model's columns are covered by dbt tests, helping to identify models with insufficient testing.

**How Quality Score is Calculated:**
The `quality_score` is derived from two primary factors:
1.  **Total Test Count (`test_count`):** The number of dbt tests directly associated with the model.
2.  **Column Test Coverage (`column_coverage`):** The percentage of a model's columns that are covered by at least one dbt test.

The formula for `quality_score` is:
`quality_score = (model.test_count * weight_test_count) + (model.column_test_coverage * weight_column_coverage)`

This `quality_score` is then factored into the overall raw score calculation as a subtractive component:
`raw_score = complexity_score + importance_score - quality_score`
This means that models with higher test coverage and more associated tests will have a lower overall risk score, indicating better quality and maintainability.

The `score` command's output (terminal, markdown, and html formats) now includes new columns: "Quality Score", "Tests", and "Coverage (%)", providing detailed insights into the test status of each model.

##### Custom Weights Configuration (`custom_weights.yml`)
You can customize the weights used for calculating complexity, importance, and **quality** scores by providing a YAML file via the `--config` flag. This allows you to fine-tune the scoring mechanism to better suit your project's needs.

The structure of the `custom_weights.yml` should mirror the default configuration found in `modaryn/config/default.yml`. Here's an example based on the default:

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
- `sql_complexity`: Contains weights for various SQL complexity metrics. Adjusting these values will change how much each factor contributes to the overall complexity score.
- `importance`: Contains weights for importance metrics. Currently, `downstream_model_count` is used to weigh models based on how many other models depend on them.
- `quality`: Contains weights for test coverage metrics. `test_count` weighs models based on the number of associated tests, and `column_coverage` weighs them based on the percentage of tested columns.

Adjust these values to emphasize or de-emphasize certain aspects of complexity, importance, or quality.

##### Score Statistics
The score commands will now output statistics (mean, median, standard deviation) of the calculated scores in the chosen output format. This provides a better understanding of the distribution of scores across your models.

![modaryn](./docs/assets/result.png)

### Report Columns and Calculation Logic
`modaryn` calculates a comprehensive risk score based on three pillars: **Complexity**, **Importance**, and **Quality**.

#### 1. SQL Complexity Metrics
These metrics are extracted by parsing the compiled SQL of each model using `sqlglot`.

| Metric | Calculation Method | Example |
| :--- | :--- | :--- |
| **JOINs** | Count of all `JOIN` clauses in the SQL. | `JOIN`, `LEFT JOIN`, `CROSS JOIN` each count as 1. |
| **CTEs** | Count of all Common Table Expressions defined. | `WITH cte_a AS (...), cte_b AS (...)` counts as 2. |
| **Conditionals** | Count of `CASE WHEN` branches and `IF` functions. | A `CASE` with 3 `WHEN` clauses counts as 1 (case-level). |
| **WHEREs** | Count of `WHERE` clauses (including subqueries). | A main `WHERE` and one in a subquery counts as 2. |
| **SQL Chars** | Total character count of the SQL (excluding spaces). | `SELECT 1` (8 chars). |

#### 2. Structural Importance Metrics
These metrics represent how much other parts of the dbt project depend on a model.

| Metric | Calculation Method | Example |
| :--- | :--- | :--- |
| **Downstream** | Number of unique dbt models that directly reference this model. | If Model B and Model C use Model A, Model A has **2** Downstream Models. |
| **Col. Down** | **Total count** of downstream column references across all models. | If Model B's `col1` and `col2` both use Model A's `id`, it adds **2** to Model A's `Col. Down` count. |

**Example of `Col. Down`:**
If Model A has a column `user_id`, and:
- Model B uses `user_id` to calculate `b_user_id`. (+1)
- Model C uses `user_id` to calculate `c_user_id` AND `creator_id`. (+2)
- **Total `Col. Down` for Model A** = 1 + 2 = **3**.

#### 3. Quality Metrics
These metrics act as "negative risk" (they reduce the overall score).

| Metric | Calculation Method | Example |
| :--- | :--- | :--- |
| **Tests** | Count of all dbt tests (`unique`, `not_null`, custom, etc.) attached to the model. | A model with 4 column tests has a count of **4**. |
| **Coverage (%)** | Percentage of columns in the model that have at least one test. | If 8 out of 10 columns have tests, coverage is **80%**. |

### Scoring Formula
The final score is a weighted combination of these metrics:

1.  **Complexity Score** = `(JOINs * w1) + (CTEs * w2) + (Conditionals * w3) + (WHEREs * w4) + (Chars * w5)`
2.  **Importance Score** = `(Downstream Models * w6) + (Col. Down * w7)`
3.  **Quality Score** = `(Tests * w8) + (Coverage % * w9)`

**Raw Score** = `Complexity Score + Importance Score - Quality Score` (Minimum 0)

#### Z-Score Normalization
When `--apply-zscore` is used, the raw scores are standardized:
`Z-Score = (Raw Score - Mean) / Standard Deviation`
This allows you to see how many standard deviations a model is away from the project average.

#### `ci-check` command
Checks dbt model complexity against a defined score threshold for CI pipelines. By default, it uses raw scores. Use `--apply-zscore` to check against Z-scores. Exits with code 1 if any model's score exceeds the threshold, 0 otherwise. This command is designed for automated quality gates in your CI/CD workflows.

```bash
modaryn ci-check --project-path . --threshold 20.0 --apply-zscore --format terminal
```
- `--project-path` / `-p`: Path to the dbt project directory. (Type: Path, Default: `.`)
- `--threshold` / `-t`: The maximum allowed score for models. CI will fail if any model exceeds this. (Type: float, Required)
- `--dialect` / `-d`: The SQL dialect to use for parsing. (Type: str, Default: `bigquery`)
- `--config` / `-c`: Path to a custom weights configuration YAML file. (Type: Optional[Path], Default: `None`)
- `--apply-zscore` / `-z`: Use Z-scores instead of raw scores for threshold checking and output. When this flag is present, Z-scores are used. Otherwise, raw scores are used (default behavior). (Type: bool, Default: `False`)
- `--format` / `-f`: Output format. Available options: `terminal`, `markdown`, `html`. (Type: OutputFormat, Default: `terminal`)
- `--output` / `-o`: Path to write the output file. If not specified, output is printed to stdout. (Type: Optional[Path], Default: `None`)

![modaryn](./docs/assets/result2.png)