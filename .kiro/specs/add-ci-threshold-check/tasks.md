# Implementation Plan

- [ ] 1. CI閾値チェックコマンドの基本構造と引数定義 (P)
  - [ ] 1.1 `modaryn/cli.py`に`app.command()`デコレータを用いて`ci-check`コマンドを新規作成する。
    - コマンドの説明とヘルプメッセージを追加する。
    - _Requirements: 1.2_
  - [ ] 1.2 `ci-check`コマンドに`DBT_PROJECT_PATH`引数を追加し、dbtプロジェクトのパスを受け取れるようにする。
    - _Requirements: 1.1_
  - [ ] 1.3 `ci-check`コマンドに`--threshold`オプション（float型）を追加し、閾値を受け取れるようにする。
    - オプションの説明とヘルプメッセージを追加する。
    - _Requirements: 2.2, 2.3_
  - [ ] 1.4 `ci-check`コマンドに`--format`オプションと`--output`オプション（既存の`score`コマンドと同様）を追加し、レポート出力形式とファイルパスを指定できるようにする。
    - _Requirements: 3.1, 3.2_

- [ ] 2. モデルスコアリングと閾値チェックロジックの実装 (P)
  - [ ] 2.1 `ci-check`コマンド内で`Scorer`クラス（`modaryn.scorers.score.Scorer`）を初期化し、`score_project`メソッドを呼び出してモデルのZ-scoreを計算する。
    - _Requirements: 1.1_
  - [ ] 2.2 計算された各モデルのZ-scoreと`--threshold`オプションで指定された閾値を比較し、閾値を超過したモデルのリストを作成する。
    - _Requirements: 2.1_

- [ ] 3. CI出力の生成と結果表示の強化 (P)
  - [ ] 3.1 閾値を超過したモデルの有無に応じて、適切な`OutputGenerator`インスタンスを生成する。
    - _Requirements: 3.1, 3.2_
  - [ ] 3.2 選択された`OutputGenerator`の`generate_report`メソッドを呼び出し、レポートコンテンツを生成する。`TerminalOutput`に対しては、閾値超過モデルのリストを渡せるようにインターフェースを拡張する。
    - _Requirements: 3.1, 3.2_
  - [ ] 3.3 `modaryn/outputs/terminal.py`内の`TerminalOutput.generate_report`メソッドを修正し、`problematic_models`リストを受け取った場合に、閾値を超過したモデルを視覚的にハイライト表示するようにする。
    - _Requirements: 3.2_
  - [ ] 3.4 閾値チェックのサマリー（合格/不合格、閾値超過モデルの数など）をレポートに含める。
    - _Requirements: 3.1, 3.2_

- [ ] 4. CI終了コードの制御とテストの追加 (P)
  - [ ] 4.1 閾値超過モデルが存在する場合、`typer.Exit(code=1)`でCLIを終了させる。
    - _Requirements: 2.1_
  - [ ] 4.2 閾値超過モデルが存在しない場合、`typer.Exit(code=0)`でCLIを終了させる。
    - _Requirements: 2.1_
  - [ ] 4.3 新しい`ci-check`コマンドの単体テストを追加する。
    - 引数解析、閾値比較ロジック、および`TerminalOutput`へのデータ連携を検証する。
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2_
  - [ ] 4.4 `modaryn ci-check`コマンドの統合テストを追加する。
    - 実際のdbtプロジェクトに対してコマンドを実行し、閾値超過の有無によるExit Codeの検証、およびターミナル出力の内容を検証する。
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2_
