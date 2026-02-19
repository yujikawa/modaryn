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

#### dbtテストカバレッジ評価
`modaryn`は、dbtテストカバレッジをスコアリングメカニズムに組み込み、「品質スコア」を各モデルに提供するようになりました。このスコアは、モデルの列がdbtテストによってどれだけカバーされているかを反映し、テストが不十分なモデルを特定するのに役立ちます。

**品質スコアの計算方法:**
`quality_score`は、主に以下の2つの要素から導き出されます。
1.  **総テスト数 (`test_count`):** モデルに直接関連付けられているdbtテストの数。
2.  **列テストカバレッジ (`column_coverage`):** モデルの列のうち、少なくとも1つのdbtテストでカバーされている列の割合。

`quality_score`の計算式は次の通りです。
`quality_score = (model.test_count * weight_test_count) + (model.column_test_coverage * weight_column_coverage)`

この`quality_score`は、全体のrawスコア計算において減算要素として考慮されます。
`raw_score = complexity_score + importance_score - quality_score`
これは、テストカバレッジが高く、関連するテストが多いモデルほど、全体のリスクスコアが低くなり、品質と保守性が高いことを示します。

`score`コマンドの出力（ターミナル、Markdown、HTML形式）には、「Quality Score」、「Tests」、「Coverage (%)」という新しい列が追加され、各モデルのテスト状況に関する詳細な洞察を提供します。

##### カスタム重み設定 (`custom_weights.yml`)
`--config` フラグを使用してYAMLファイルを指定することで、複雑性、重要性、および**品質**スコアの計算に使用される重みをカスタマイズできます。これにより、プロジェクトのニーズに合わせてスコアリングメカニズムを微調整できます。

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

quality:
  test_count: 0.5
  column_coverage: 1.0
```
- `sql_complexity`: さまざまなSQL複雑性メトリクスの重みを含みます。これらの値を調整すると、各要因が全体の複雑性スコアにどれだけ寄与するかが変わります。
- `importance`: 重要性メトリクスの重みを含みます。現在、`downstream_model_count` は、他のモデルがどれだけそれに依存しているかに基づいてモデルに重み付けするために使用されます。
- `quality`: テストカバレッジメトリクスの重みを含みます。`test_count` は、関連するテストの数に基づいてモデルに重み付けし、`column_coverage` は、テストされている列の割合に基づいてモデルに重み付けします。

複雑性、重要性、または品質の特定の側面を強調または軽視するために、これらの値を調整してください。

##### スコア統計 (Score Statistics)
スコアコマンドは、計算されたスコアの統計量（平均、中央値、標準偏差）を選択された出力形式で出力するようになりました。これにより、モデル全体のスコアの分布をよりよく理解できます。

![modaryn](./docs/assets/result.png)

### レポートの列説明と算出ロジック
`modaryn` は、**複雑度 (Complexity)**、**重要度 (Importance)**、**品質 (Quality)** の3つの柱に基づいて包括的なリスクスコアを算出します。

#### 1. SQL複雑度メトリクス (Complexity)
これらのメトリクスは、`sqlglot` を使用して各モデルのコンパイル済みSQLを解析することで抽出されます。

| メトリクス | 算出方法 | 例 |
| :--- | :--- | :--- |
| **JOINs** | SQL内のすべての `JOIN` 句の数。 | `JOIN`, `LEFT JOIN`, `CROSS JOIN` がそれぞれ 1 とカウントされます。 |
| **CTEs** | 定義されたすべての共通テーブル式 (CTE) の数。 | `WITH cte_a AS (...), cte_b AS (...)` は 2 とカウントされます。 |
| **Conditionals** | `CASE WHEN` 文と `IF` 関数の数。 | `CASE` 内に複数の `WHEN` があっても、CASE文単位でカウントされます。 |
| **WHEREs** | `WHERE` 句の数（サブクエリ内を含む）。 | メインの `WHERE` とサブクエリ内の `WHERE` で計 2 とカウントされます。 |
| **SQL Chars** | SQLの総文字数（空白を除く）。 | `SELECT 1` は 8 文字としてカウントされます。 |

#### 2. 構造的重要度メトリクス (Importance)
プロジェクト内の他のモデルが、そのモデルにどれだけ依存しているかを示します。

| メトリクス | 算出方法 | 例 |
| :--- | :--- | :--- |
| **Downstream** | そのモデルを直接参照しているユニークなdbtモデルの数。 | モデルBとモデルCがモデルAを参照している場合、モデルAの数値は **2** です。 |
| **Col. Down** | そのモデルのカラムを参照している下流カラムの**延べ数**。 | モデルBの `col1` と `col2` が両方ともモデルAの `id` を参照している場合、**2** 加算されます。 |

**`Col. Down` の具体例:**
モデルAに `user_id` カラムがあり、以下の依存関係がある場合：
- モデルBが `user_id` を使って `b_user_id` を計算している (+1)
- モデルCが `user_id` を使って `c_user_id` と `creator_id` の2つを計算している (+2)
- **モデルAの `Col. Down` 合計** = 1 + 2 = **3**

#### 3. 品質メトリクス (Quality)
これらは「負のリスク」として働き、全体のスコアを低減させます。

| メトリクス | 算出方法 | 例 |
| :--- | :--- | :--- |
| **Tests** | モデルに設定されたすべての dbt テスト（`unique`, `not_null`, カスタムテスト等）の数。 | 4つのカラムテストがあるモデルは **4** とカウントされます。 |
| **Coverage (%)** | モデル内のカラムのうち、少なくとも1つのテストが設定されている割合。 | 10カラム中8カラムにテストがあれば **80%** です。 |

### スコア計算式
最終的なスコアは、これらのメトリクスに重み付けをして算出されます。

1.  **複雑度スコア (Complexity Score)** = `(JOINs * w1) + (CTEs * w2) + (Cond. * w3) + (WHEREs * w4) + (Chars * w5)`
2.  **重要度スコア (Importance Score)** = `(Downstream Models * w6) + (Col. Down * w7)`
3.  **品質スコア (Quality Score)** = `(Tests * w8) + (Coverage % * w9)`

**Raw Score (生スコア)** = `複雑度スコア + 重要度スコア - 品質スコア` (最小値 0)

#### Zスコア正規化
`--apply-zscore` を使用すると、生スコアがプロジェクト全体の分布に基づいて標準化されます。
`Z-Score = (Raw Score - 平均) / 標準偏差`
これにより、そのモデルがプロジェクトの平均からどれだけ乖離しているか（リスクが突出しているか）を相対的に把握できます。

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