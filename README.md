# modaryn
![modaryn](./docs/assets/header.png)
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
The `modaryn` CLI provides the following commands:

#### `score` command
Analyzes and scores dbt models based on complexity and importance, displaying combined scan and score information.
```bash
modaryn score --project-path . --dialect bigquery --config custom_weights.yml --format html --output modaryn_report.html
```

![modaryn](./docs/assets/result.png)

#### `ci-check` command
Checks dbt model complexity against a defined Z-score threshold for CI pipelines. Exits with code 1 if any model's score exceeds the threshold, 0 otherwise. This command is designed for automated quality gates in your CI/CD workflows.

```bash
modaryn ci-check --project-path . --threshold 1.5 --format terminal
```
- `--project-path`: Path to the dbt project directory.
- `--threshold`: The maximum allowed Z-score for models. CI will fail if any model exceeds this.
- `--format`: Output format (`terminal`, `markdown`, `html`). Defaults to `terminal`.

---

### 概要 (Overview)
`modaryn` は、dbt (data build tool) プロジェクトを分析するために設計されたPythonベースのコマンドラインインターフェース (CLI) ツールです。その主な目的は、dbtモデルの複雑さと構造的重要性に基づいてスコアを付け、データチームが高リスクで影響の大きいデータモデルを特定するのに役立つことです。現在、`JOIN`数、CTE数、条件文(`CASE`、`IF`)、`WHERE`句の数、SQLの文字数などの詳細な複雑性メトリクスを抽出し、Zスコアを使用してモデルをランク付けします。

### インストール (Installation)
このプロジェクトは、依存関係の管理に `uv` を使用しています。依存関係をインストールするには、以下を実行します。
```bash
uv pip install -e .
```

### 使い方 (Usage)
`modaryn` CLIは以下のコマンドを提供します。

#### `score` コマンド
複雑さと重要性に基づいてdbtモデルを分析およびスコアリングし、スキャンとスコアの情報を組み合わせたレポートを表示します。
```bash
modaryn score --project-path . --dialect bigquery --config custom_weights.yml --format html --output modaryn_report.html
```

#### `ci-check` コマンド
CIパイプライン向けに、dbtモデルの複雑性を定義されたZスコア閾値と照合してチェックします。いずれかのモデルのスコアが閾値を超過した場合、終了コード1で終了し、そうでない場合は0で終了します。このコマンドは、CI/CDワークフローにおける自動化された品質ゲートのために設計されています。

```bash
modaryn ci-check --project-path . --threshold 1.5 --format terminal
```
- `--project-path`: dbtプロジェクトディレクトリへのパス。
- `--threshold`: モデルに許容される最大Zスコア閾値。いずれかのモデルがこの値を超過するとCIは失敗します。
- `--format`: 出力フォーマット (`terminal`、`markdown`、`html`)。デフォルトは`terminal`です。