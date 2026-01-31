# 実装計画

- [x] 1. (P) CLIアプリケーションのバージョンを初期化する
  - `modaryn/cli.py`の`typer.Typer`インスタンスの初期化時に`version="0.1.0"`を追加する。
  - _Requirements: 4.1_

- [x] 2. (P) ロゴとバージョン表示ロジックを実装する
  - `modaryn/outputs/logo.py`内の関数名を`display_logo_and_version`に変更する。
  - `display_logo_and_version`関数に`version_string: str`パラメータを追加する。
  - `logo.txt`の内容を`rich`で出力した後、新しい行にバージョン文字列を出力する。
  - _Requirements: 3.1, 3.2, 4.1_

- [x] 3. CLIにロゴとバージョン表示ロジックを統合する
  - `modaryn/cli.py`を修正する。
  - `main`コールバック関数内で、`display_logo()`の呼び出しを`display_logo_and_version(app.info.version)`に変更する。
  - _Requirements: 1.1, 1.2, 2.1, 4.1_

- [x] 4. テストを更新する
  - `tests/test_logo.py`内のユニットテストを`display_logo_and_version`関数がバージョン文字列を正しく受け取り、ロゴとともに表示することを検証するように更新する。
  - `tests/test_cli.py`内の統合テストを、引数なしで`modaryn`を実行した際にロゴとバージョンが表示されることを検証するように更新する。
  - `score`などのサブコマンド付きで実行した際にロゴとバージョンが表示されないことを検証する統合テストを更新する。
  - _Requirements: 1.1, 1.2, 2.1, 3.1, 3.2, 4.1_