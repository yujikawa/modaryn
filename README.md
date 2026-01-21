# modaryn

modaryn analyzes dbt projects to score model complexity and structural importance,
helping teams identify high-risk and high-impact data models.

### Overview
`modaryn` is a Python-based Command Line Interface (CLI) tool designed to analyze dbt (data build tool) projects. Its primary purpose is to score the complexity and structural importance of dbt models, helping data teams identify high-risk and high-impact data models within their projects.

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
modaryn scan --manifest-path target/manifest.json --format terminal
```

#### `score` command
Scores dbt models based on complexity and importance.
```bash
modaryn score --manifest-path target/manifest.json --config custom_weights.yml --format html --output modaryn_report.html
```

---

### 概要 (Overview)
`modaryn` は、dbt (data build tool) プロジェクトを分析するために設計されたPythonベースのコマンドラインインターフェース (CLI) ツールです。その主な目的は、dbtモデルの複雑さと構造的重要性に基づいてスコアを付け、データチームが高リスクで影響の大きいデータモデルを特定するのに役立つことです。

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
modaryn scan --manifest-path target/manifest.json --format terminal
```

#### `score` コマンド
複雑さと重要性に基づいてdbtモデルをスコアリングします。
```bash
modaryn score --manifest-path target/manifest.json --config custom_weights.yml --format html --output modaryn_report.html
```
