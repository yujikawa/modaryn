![modaryn](./docs/assets/header.png)
### 概要 (Overview)
`modaryn` は、dbt (data build tool) プロジェクトを分析するために設計されたPythonベースのコマンドラインインターフェース (CLI) ツールです。その主な目的は、dbtモデルの複雑さと構造的重要性に基づいてスコアを付け、データチームが高リスクで影響の大きいデータモデルを特定するのに役立つことです。現在、`JOIN`数、CTE数、条件文(`CASE`、`IF`)、`WHERE`句の数、SQLの文字数などの詳細な複雑性メトリクスを抽出し、Zスコアを使用してモデルをランク付けします。

### インストール (Installation)
このプロジェクトは、依存関係の管理に `uv` を使用しています。依存関係をインストールするには、以下を実行します。
```bash
uv pip install git+https://github.com/yujikawa/modaryn.git
```

### 使い方 (Usage)
`modaryn` CLIは以下のコマンドを提供します。

#### `score` コマンド
複雑さと重要性に基づいてdbtモデルを分析およびスコアリングし、スキャンとスコアの情報を組み合わせたレポートを表示します。
```bash
modaryn score --project-path . --dialect bigquery --config custom_weights.yml --apply-zscore --format html --output modaryn_report.html
```
- `--project-path` / `-p`: dbtプロジェクトディレクトリへのパス。(型: Path, デフォルト: `.`)
- `--dialect` / `-d`: 解析に使用するSQL方言 (`bigquery`, `snowflake`, `redshift`など)。(型: str, デフォルト: `bigquery`)
- `--config` / `-c`: カスタム重み設定YAMLファイルへのパス。(型: Optional[Path], デフォルト: `None`)
- `--apply-zscore` / `-z`: モデルスコアにZスコア変換を適用します。このフラグが存在する場合、スコアはZスコア正規化されます。それ以外の場合は、rawスコアが使用されます。(型: bool, デフォルト: `False`)
- `--format` / `-f`: 出力フォーマット。利用可能なオプション: `terminal`, `markdown`, `html`。(型: OutputFormat, デフォルト: `terminal`)
- `--output` / `-o`: 出力ファイルを書き込むパス。指定しない場合、出力は標準出力に表示されます。(型: Optional[Path], デフォルト: `None`)

##### カスタム重み設定 (`custom_weights.yml`)
`--config` フラグを使用してYAMLファイルを指定することで、複雑性および重要性スコアの計算に使用される重みをカスタマイズできます。これにより、プロジェクトのニーズに合わせてスコアリングメカニズムを微調整できます。

`custom_weights.yml` の構造は、`modaryn/config/default.yml` にあるデフォルト設定と同じである必要があります。デフォルトに基づいた例を以下に示します。

```yaml
sql_complexity:
  join_count: 2.0
  cte_count: 1.5
  conditional_count: 1.0
  where_count: 0.5
  sql_char_count: 0.01

importance:
  downstream_model_count: 1.0
```
- `sql_complexity`: さまざまなSQL複雑性メトリクスの重みを含みます。これらの値を調整すると、各要因が全体の複雑性スコアにどれだけ寄与するかが変わります。
- `importance`: 重要性メトリクスの重みを含みます。現在、`downstream_model_count` は、他のモデルがどれだけそれに依存しているかに基づいてモデルに重み付けするために使用されます。

複雑性または重要性の特定の側面を強調または軽視するために、これらの値を調整してください。

##### スコア統計 (Score Statistics)
スコアコマンドは、計算されたスコアの統計量（平均、中央値、標準偏差）を選択された出力形式で出力するようになりました。これにより、モデル全体のスコアの分布をよりよく理解できます。

![modaryn](./docs/assets/result.png)

#### `ci-check` コマンド
CIパイプライン向けに、定義されたスコア閾値に対してdbtモデルの複雑性をチェックします。デフォルトではrawスコアを使用します。Zスコアでチェックするには`--apply-zscore`を使用します。いずれかのモデルのスコアが閾値を超過した場合、終了コード1で終了し、そうでない場合は0で終了します。このコマンドは、CI/CDワークフローにおける自動化された品質ゲートのために設計されています。

```bash
modaryn ci-check --project-path . --threshold 20.0 --apply-zscore --format terminal
```
- `--project-path` / `-p`: dbtプロジェクトディレクトリへのパス。(型: Path, デフォルト: `.`)
- `--threshold` / `-t`: モデルに許容される最大スコア。いずれかのモデルがこの値を超過するとCIは失敗します。(型: float, 必須)
- `--dialect` / `-d`: 解析に使用するSQL方言。(型: str, デフォルト: `bigquery`)
- `--config` / `-c`: カスタム重み設定YAMLファイルへのパス。(型: Optional[Path], デフォルト: `None`)
- `--apply-zscore` / `-z`: 閾値チェックと出力にrawスコアの代わりにZスコアを使用します。このフラグが存在する場合、Zスコアが使用されます。それ以外の場合、rawスコアが使用されます (デフォルトの動作)。(型: bool, デフォルト: `False`)
- `--format` / `-f`: 出力フォーマット。利用可能なオプション: `terminal`, `markdown`, `html`。(型: OutputFormat, デフォルト: `terminal`)
- `--output` / `-o`: 出力ファイルを書き込むパス。指定しない場合、出力は標準出力に表示されます。(型: Optional[Path], デフォルト: `None`)

![modaryn](./docs/assets/result2.png)