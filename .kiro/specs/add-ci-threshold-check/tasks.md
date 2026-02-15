# Implementation Plan

- [x] 1. CI閾値チェックコマンドの基本構造と引数定義 (P)
  - _Requirements: 1.1, 1.2, 2.2, 2.3, 3.1, 3.2_
- [x] 1.1 (P) `modaryn/cli.py`に`app.command()`デコレータを用いて`ci-check`コマンドを新規作成する。
  - コマンドの説明とヘルプメッセージを追加する。
  - `DBT_PROJECT_PATH`引数を追加し、dbtプロジェクトのパスを受け取れるようにする。
  - `--threshold`オプション（float型）を追加し、閾値を受け取れるようにする。
  - `--format`オプションと`--output`オプション（既存の`score`コマンドと同様）を追加し、レポート出力形式とファイルパスを指定できるようにする。
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2_

- [x] 2. モデルスコアリングと閾値チェックロジックの実装 (P)
  - _Requirements: 1.1, 2.1_
- [x] 2.1 (P) `ci-check`コマンド内で`Scorer`クラスを初期化し、`score_project`メソッドを呼び出してモデルのZ-scoreを計算する。
  - _Requirements: 1.1_
- [x] 2.2 (P) 計算された各モデルのZ-scoreと`--threshold`オプションで指定された閾値を比較し、閾値を超過したモデルのリストを作成する。
  - _Requirements: 2.1_

- [x] 3. CI出力の生成と結果表示の強化 (P)
  - _Requirements: 3.1, 3.2_
- [x] 3.1 (P) 閾値を超過したモデルの有無に応じて、適切な`OutputGenerator`インスタンスを生成する。
  - _Requirements: 3.1, 3.2_
- [x] 3.2 (P) 選択された`OutputGenerator`の`generate_report`メソッドを呼び出し、レポートコンテンツを生成する。`TerminalOutput`に対しては、閾値超過モデルのリストを渡せるようにインターフェースを拡張する。
  - _Requirements: 3.1, 3.2_
- [x] 3.3 (P) `modaryn/outputs/terminal.py`内の`TerminalOutput.generate_report`メソッドを修正し、`problematic_models`リストを受け取った場合に、閾値を超過したモデルを視覚的にハイライト表示するようにする。
  - _Requirements: 3.2_
- [x] 3.4 (P) 閾値チェックのサマリー（合格/不合格、閾値超過モデルの数など）をレポートに含める。
  - _Requirements: 3.1, 3.2_

- [x] 4. CI終了コードの制御とテストの追加 (P)
  - _Requirements: 2.1_
- [x] 4.1 (P) 閾値超過モデルが存在する場合、`typer.Exit(code=1)`でCLIを終了させる。
  - _Requirements: 2.1_
- [x] 4.2 (P) 閾値超過モデルが存在しない場合、`typer.Exit(code=0)`でCLIを終了させる。
  - _Requirements: 2.1_
- [x] 4.3 (P) 新しい`ci-check`コマンドの単体テストを追加する。
  - 引数解析、閾値比較ロジック、および`TerminalOutput`へのデータ連携を検証する。
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2_
- [x] 4.4 (P) `modaryn ci-check`コマンドの統合テストを追加する。
  - 実際のdbtプロジェクトに対してコマンドを実行し、閾値超過の有無によるExit Codeの検証、およびターミナル出力の内容を検証する。
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2_