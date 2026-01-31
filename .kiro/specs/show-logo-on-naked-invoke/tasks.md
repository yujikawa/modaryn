# 実装計画

- [ ] 1. (P) ロゴ表示機能の基盤をセットアップする
  - `modaryn/assets` ディレクトリを作成する。
  - `modaryn/assets/logo.txt` というプレースホルダーのロゴファイルを配置する。
  - `modaryn/outputs/logo.py` という空の表示ロジック用モジュールを作成する。
  - _Requirements: 3.1_

- [ ] 2. (P) ロゴ表示ロジックを実装する
  - `modaryn/outputs/logo.py` に `display_logo` 関数を実装する。
  - この関数は `modaryn/assets/logo.txt` からロゴのテキストを読み込む。
  - `rich` ライブラリを使用して、読み込んだテキストをコンソールにスタイリングして出力する。
  - _Requirements: 3.1, 3.2_

- [ ] 3. CLIにロゴ表示ロジックを統合する
  - `modaryn/cli.py` を修正する。
  - `display_logo` 関数をインポートする。
  - `main` コールバック関数が `typer.Context` を受け取るようにシグネチャを変更する。
  - `ctx.invoked_subcommand` が `None` の場合にのみ `display_logo` を呼び出す条件ロジックを追加する。
  - _Requirements: 1.1, 1.2, 2.1_

- [ ] 4. テストを実装する
  - `display_logo` 関数のためのユニットテストを作成する。ファイル読み込みと `print` の呼び出しをモックして検証する。
  - `typer.testing.CliRunner` を使用した統合テストを作成する。
    - 引数なしで `modaryn` を実行した際にロゴが出力されることを確認する。
    - `score` などのサブコマンド付きで実行した際にロゴが出力されないことを確認する。
  - _Requirements: 1.1, 1.2, 2.1, 3.1, 3.2_
