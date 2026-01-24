# modaryn

modaryn analyzes dbt projects to score model complexity and structural importance,
helping teams identify high-risk and high-impact data models.

### Overview
`modaryn` is a Python-based Command Line Interface (CLI) tool designed to analyze dbt (data build tool) projects. Its primary purpose is to score the complexity and structural importance of dbt models, helping data teams identify high-risk and high-impact data models within their projects. It now extracts detailed complexity metrics such as `JOIN` counts, CTE counts, conditional statements (`CASE`, `IF`), `WHERE` clause counts, and SQL character length, and ranks models using Z-scores.

### Installation
The project uses `uv` for dependency management. To install dependencies, run:
```bash
uv pip install -e .
```

### Usage
The `modaryn` CLI provides two main commands: `scan` and `score`.

#### `scan` command
Scans a dbt project and displays basic model information.
```bash
modaryn scan --project-path . --dialect bigquery --format terminal
```

#### `score` command
Scores dbt models based on complexity and importance, and provides a Z-score based ranking.
```bash
modaryn score --project-path . --dialect bigquery --config custom_weights.yml --format html --output modaryn_report.html
```

---

### 概要 (Overview)
`modaryn` は、dbt (data build tool) プロジェクトを分析するために設計されたPythonベースのコマンドラインインターフェース (CLI) ツールです。その主な目的は、dbtモデルの複雑さと構造的重要性に基づいてスコアを付け、データチームが高リスクで影響の大きいデータモデルを特定するのに役立つことです。現在、`JOIN`数、CTE数、条件文(`CASE`、`IF`)、`WHERE`句の数、SQLの文字数などの詳細な複雑性メトリクスを抽出し、Zスコアを使用してモデルをランク付けします。

### インストール (Installation)
このプロジェクトは、依存関係の管理に `uv` を使用しています。依存関係をインストールするには、以下を実行します。
```bash
uv pip install -e .
```

### 使い方 (Usage)
`modaryn` CLIは主に `scan` と `score` の2つのコマンドを提供します。

#### `scan` コマンド
dbtプロジェクトをスキャンし、基本的なモデル情報を表示します。
```bash
modaryn scan --project-path . --dialect bigquery --format terminal
```

#### `score` コマンド
複雑さと重要性に基づいてdbtモデルをスコアリングし、Zスコアに基づいたランキングを提供します。
```bash
modaryn score --project-path . --dialect bigquery --config custom_weights.yml --format html --output modaryn_report.html
```