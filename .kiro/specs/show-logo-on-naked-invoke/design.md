# 技術設計書

## 概要
この機能は、`modaryn` CLIを引数なしで実行した際に、ASCIIアートのロゴとCLIのバージョン情報を表示します。これにより、ユーザーはツールが正しくインストールされていることと、そのバージョンを視覚的に確認できます。この変更は主にCLIのエントリポイントとロゴ表示ロジックに影響を与えます。

### ゴール
- 引数なしの`modaryn`実行時にロゴとバージョン情報を表示する。
- ロゴ表示ロジックとバージョン取得ロジックを既存のコマンド機能から分離する。
- ロゴのコンテンツとバージョン情報を管理しやすくする。

### 非ゴール
- ロゴのデザイン自体の作成。
- ロゴ表示およびバージョン表示以外のCLIの動作変更。

## アーキテクチャ

### 既存アーキテクチャの分析
`modaryn`は`typer`ライブラリ上に構築されたCLIアプリケーションです。`modaryn/cli.py`がエントリポイントとして機能し、`@app.callback()`デコレータを持つ`main`関数がすべてのコマンド実行前に呼び出されます。この既存の構造が、新しいロゴおよびバージョン表示ロジックの注入ポイントとして最適です。

### アーキテクチャパターンと境界マップ
この変更は非常に限定的であり、既存のアーキテクチャに準拠します。新しい表示ロジックを`modaryn/outputs`レイヤーに追加し、プレゼンテーションに関する関心事を分離するという既存のパターンに従います。バージョン情報もこの表示ロジック内で処理されます。

```mermaid
graph TD
    subgraph CLI Entrypoint
        A[cli.py: main(ctx)]
        B_ver[cli.py: get_version()]
    end
    subgraph Output Layer
        C[outputs/logo.py: display_logo_and_version(version_str)]
        D[assets/logo.txt]
    end

    A -- "if ctx.invoked_subcommand is None" --> B_ver
    B_ver --> C
    C -- "reads" --> D
```

**アーキテクチャ統合**:
- **選択したパターン**: 既存のレイヤードアーキテクチャを拡張します。
- **ドメイン/フィーチャー境界**: `cli.py`が呼び出しのコンテキストを判断し、バージョン情報を取得して`outputs/logo.py`の表示関数に渡し、表示を担当させることで、関心事を分離します。
- **ステアリング準拠**: `modaryn/outputs`に出力関連のロジックを配置する`structure.md`の原則に準拠しています。

### 技術スタック

| レイヤー | 選択 / バージョン | 機能における役割 | ノート |
|---|---|---|---|
| Frontend / CLI | Typer | コマンドライン引数の解釈とコールバックのトリガー、バージョン情報の管理 | `typer.Context`を使用して呼び出し状態を判断、`app.info.version`を通じてバージョン取得 |
| Frontend / CLI | Rich | ターミナルへのスタイリングされたロゴとバージョン情報の出力 | 既存の依存関係を活用 |

## 要求事項トレーサビリティ

| 要求事項 | 概要 | コンポーネント |
|---|---|---|
| 1.1 | 引数なしでロゴ表示 | `cli.py`, `outputs/logo.py` |
| 1.2 | 引数ありでロゴ非表示 | `cli.py` |
| 2.1 | ヘルプ表示を優先 | `cli.py` (Typerのデフォルト動作) |
| 3.1 | ロゴを外部ファイルで定義 | `assets/logo.txt`, `outputs/logo.py` |
| 3.2 | richを使用してスタイリング | `outputs/logo.py` |
| 4.1 | ロゴの直後にCLIバージョン表示 | `cli.py`, `outputs/logo.py` |

## コンポーネントとインターフェース

### `cli` レイヤー

#### `modaryn/cli.py`
- **責務**: CLIのエントリポイントとして、引数を解釈し、ロゴとバージョンを表示するか、または指定されたサブコマンドを実行するかを決定する。
- **変更点**:
  - `app = typer.Typer(...)` の初期化時に `version="0.1.0"` (または `importlib.metadata` を使用して`pyproject.toml`から動的に取得) を渡す。
  - `main`関数が`ctx: typer.Context`を受け取るように変更。
  - `ctx.invoked_subcommand` が `None` の場合にのみ、`display_logo_and_version(app.info.version)` を呼び出すロジックを追加する。

### `outputs` レイヤー

#### `modaryn/outputs/logo.py`
- **責務**: ロゴとCLIバージョンの表示ロジックをカプセル化する。
- **インターフェース**:
  ```python
  def display_logo_and_version(version_string: str):
      """
      アセットファイルからASCIIロゴを読み込み、バージョン文字列とともにコンソールに表示する。
      """
      # 実装の詳細
  ```

### `assets` レイヤー

#### `modaryn/assets/logo.txt`
- **責務**: 表示されるASCIIアートのロゴ文字列を保持する。
- **フォーマット**: プレーンテキスト。

## テスト戦略
- **ユニットテスト**:
  - `outputs/logo.py`の`display_logo_and_version`関数が、`logo.txt`の内容と渡されたバージョン文字列を正しく読み込み、`rich.print`を呼び出すことを検証する（`print`はモックする）。
- **統合テスト**:
  - `typer.testing.CliRunner` を使用して、`modaryn`を引数なしで実行した場合にロゴとバージョンが表示されることを検証する（標準出力をキャプチャして検証）。
  - `score` などのサブコマンド付きで実行した際にロゴとバージョンが表示*されない*ことを検証する。
