"""エージェントState定義

LangGraphのStateGraphで使用するState（状態）を定義する。
各ノード間で共有されるデータ構造。

TypedDictを使う理由:
- LangGraphが公式に推奨する形式
- Annotated[list, operator.add] でリストの自動マージが可能

参考: 書籍Chapter10 InterviewState（行49-63）のパターン
"""

import operator
from typing import Annotated, TypedDict

from langchain_core.documents import Document


class RAGAgentState(TypedDict):
    """RAGエージェントの状態を定義するTypedDict

    各フィールドの役割:
    - query: ユーザーの元の質問（不変）
    - search_queries: クエリ分析で生成された検索クエリ
    - retrieved_documents: 検索で得たドキュメント（Annotated[list, operator.add]で蓄積）
    - answer: 生成された回答
    - is_sufficient: 回答が十分かどうかの評価結果
    - evaluation_reason: 評価の理由（デバッグ・LangSmithトレース用）
    - iteration: 検索→回答→評価の反復回数（無限ループ防止）
    """

    # ユーザーの質問（グラフ実行開始時に設定、以降変更されない）
    query: str

    # クエリ分析ノードが生成した検索クエリのリスト
    search_queries: list[str]

    # 検索で得たドキュメント
    # Annotated[list, operator.add] により、各反復で得たドキュメントが
    # 上書きではなく蓄積される（1回目の結果 + 2回目の結果 + ...）
    # これにより再検索時に以前の検索結果も参照できる
    retrieved_documents: Annotated[list[Document], operator.add]

    # 回答生成ノードが生成した回答文字列
    answer: str

    # 評価ノードの判定結果（True: 十分、False: 不十分）
    is_sufficient: bool

    # 評価の理由（LangSmithのトレースで確認する際に有用）
    evaluation_reason: str

    # 反復回数（0から始まり、毎回の検索→回答→評価で+1）
    # iteration >= 3 で強制終了（無限ループ防止）
    iteration: int
