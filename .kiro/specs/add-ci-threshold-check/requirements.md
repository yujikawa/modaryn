# Requirements Document

## Introduction
このドキュメントは、modarynコマンドでdbtモデルの複雑性をCIで自動的にチェックし、定義された閾値を超過した場合にCIプロセスをエラーにする機能の要件を定義します。これにより、モデルの複雑化を早期に検出し、品質を維持することを目的とします。

## Requirements

### 1. CI用閾値チェックコマンドの提供
**Objective:** As a CI/CDエンジニア、私はモデルの複雑度を自動でチェックしたい、CIパイプラインの安定性を保ちたい。

#### Acceptance Criteria
1. When `modaryn` が特定のCI用コマンドで実行されたとき、The `modaryn` shall モデルの複雑度を評価する。
2. The `modaryn` shall 通常のスコアコマンドとは異なる方法で動作するCI専用のコマンドを提供する。

### 2. 閾値設定と超過時のCIエラー
**Objective:** As a CI/CDエンジニア、私は特定の閾値を設定し、その閾値を超過したモデルがある場合にCIを失敗させたい、これによりモデルの品質低下を未然に防ぎたい。

#### Acceptance Criteria
1. When 設定された閾値を超えるモデルが検出されたとき、The `modaryn` shall CIプロセスをエラー状態にする。
2. The `modaryn` shall ユーザーが閾値を設定できるメカニズムを提供する。
3. Where 閾値設定がZスコア形式の場合、The `modaryn` shall Zスコア閾値の指定をサポートする。

### 3. CI出力におけるスコアと問題モデルの表示
**Objective:** As a開発者、私はCIの実行結果からモデルのスコアと問題点を迅速に把握したい、問題のあるモデルの特定と修正を効率化したい。

#### Acceptance Criteria
1. When CIが正常に完了したとき、The `modaryn` shall 評価されたすべてのモデルのスコア結果を表示する。
2. When CIがエラー状態になったとき、The `modaryn` shall 閾値を超過したモデルの詳細情報をCI画面に出力する。