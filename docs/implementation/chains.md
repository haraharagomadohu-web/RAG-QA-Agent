# LCELチェーン（クエリ分析・回答生成・評価）

## 概要

LangChain Expression Language（LCEL）を使った3つのチェーンを実装する。
LCELは `prompt | llm | parser` のパイプ演算子でチェーンを構成するパターン。
書籍Chapter5-6で詳しく解説されている。

## 実装手順

### 1. クエリ分析チェーン（query_analyzer.py）

- 目的: ユーザーの質問を分析し、ベクトル検索に適した複数の検索クエリを生成する
- やること:
  - Pydanticモデルで出力スキーマを定義（SearchQueries）
  - `with_structured_output`でLLMの出力を構造化
  - `prompt | structured_llm` のチェーンを構成
- なぜ複数クエリ: 1つのクエリだけでは見落とす文書がある。異なる言い回しで検索することで網羅性が上がる（Multi-Query RAGパターン）
- 参考: 書籍Chapter6 cell-14のQueryGenerationOutputパターン

### 2. 回答生成チェーン（answer_generator.py）

- 目的: 検索で得たドキュメントを基に、出典付きの回答を生成する
- やること:
  - 検索結果をコンテキストとしてプロンプトに埋め込む
  - LCELで `prompt | llm | StrOutputParser()` を構成
  - 出典情報をメタデータから抽出して回答に含める
- なぜ出典付き: RAGの価値は「情報源を示せること」にある。ハルシネーション対策にもなる
- 参考: 書籍Chapter6 cell-8のRAGチェーンパターン

### 3. 回答品質評価チェーン（evaluator.py）

- 目的: 生成された回答が質問に十分に答えているかをLLMで自己評価する
- やること:
  - 評価結果のPydanticモデル（EvaluationResult）を定義
  - `with_structured_output`で構造化出力
  - 回答の十分性・不足している情報を判定
- なぜ自己評価: エージェントの「不十分なら再検索」ループの判断基準として使用
- 参考: 書籍Chapter10 InformationEvaluator（行186-219）のパターン

## 判断理由

- **LCEL vs 関数チェーン**: LCELはストリーミング・バッチ処理・非同期に自動対応。書籍でも推奨
- **with_structured_output vs JsonOutputParser**: with_structured_outputの方がシンプルで、Ollamaでも対応済み
- **StrOutputParser**: 回答本文は自由形式テキストなので、構造化不要。最もシンプルなパーサー
