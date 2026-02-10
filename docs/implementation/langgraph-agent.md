# LangGraphエージェント（State・ノード・グラフ）

## 概要

LangGraphのStateGraphを使い、RAGを「質問分析→検索→回答生成→自己評価」の
マルチステップエージェントに進化させる。自己評価で回答が不十分と判断された場合、
自動的に再検索・再回答を行う自己改善ループを持つ。

```
analyze_query → retrieve → generate_answer → evaluate
    ^                                            |
    |------ (不十分 & iteration < 3) ←-----------|
                                                 |
                                      (十分) → END
```

## 実装手順

### 1. State定義（state.py）

- 目的: エージェントの全ノード間で共有する状態を定義
- やること: `TypedDict`でStateを定義。`Annotated[list, operator.add]`パターンで検索結果を蓄積
- なぜTypedDict: LangGraphのStateGraphが要求する形式。Pydanticではなく`TypedDict`を使う（LangGraphの公式推奨）
- なぜAnnotated[list, operator.add]: 各ノードから返されたリストを自動的にマージ。再検索時に以前の結果も保持される
- 参考: 書籍Chapter10 InterviewState（行49-63）

### 2. ノード関数（nodes.py）

- 目的: エージェントの各ステップの処理を関数として定義
- やること: 4つのノード関数を作成
  1. `analyze_query`: 質問→検索クエリ生成（query_analyzerチェーン使用）
  2. `retrieve_documents`: 検索クエリ→ベクトル検索（VectorStoreManager使用）
  3. `generate_answer`: 検索結果→回答生成（answer_generatorチェーン使用）
  4. `evaluate_answer`: 回答→品質評価（evaluatorチェーン使用）
- なぜ関数に分離: グラフのノードは関数として登録する。チェーンの呼び出しとState更新を各関数内で行う
- 各ノードの戻り値はdictで、Stateの更新したいフィールドのみを含める
- 参考: 書籍Chapter10 _generate_personas等（行307-337）

### 3. グラフ構築（graph.py）

- 目的: StateGraphでノードとエッジを接続し、エージェントのワークフローを定義
- やること:
  - StateGraphの初期化
  - 4ノードの登録
  - エッジの接続（直線的な流れ）
  - 条件付きエッジ（自己評価→再検索 or 終了）
  - コンパイルして実行可能なグラフを返す
- 条件分岐のロジック:
  - `is_sufficient == True` → 終了（十分な回答が得られた）
  - `is_sufficient == False && iteration < 3` → analyze_queryに戻って再検索
  - `iteration >= 3` → 強制終了（無限ループ防止）
- 参考: 書籍Chapter10 _create_graph（行279-305）

## 判断理由

- **StateGraph vs AgentExecutor**: StateGraphの方がワークフローを明示的に制御できる。AgentExecutorはReActパターン向け
- **最大3回の反復**: 多すぎるとコスト増加、少なすぎると品質が不十分。3回はバランスの良い設定
- **TypedDict vs Pydantic for State**: LangGraphは内部的にTypedDictを推奨。Pydanticも使えるが、TypedDictの方がシンプル
- **ノード関数をクラスにまとめない**: 書籍ではクラスメソッドにしているが、関数の方がテストしやすく依存注入が明確
