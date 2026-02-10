"""エージェントノード関数

LangGraphの各ノードで実行される処理を関数として定義する。
各関数は RAGAgentState を受け取り、更新するフィールドのdictを返す。

関数の戻り値はStateの「更新分」のみを含むdict。
LangGraphが自動的にStateとマージする。

参考: 書籍Chapter10 _generate_personas, _conduct_interviews等（行307-337）
"""

from typing import Any

from src.agent.state import RAGAgentState
from src.chains.answer_generator import create_answer_generator, format_documents
from src.chains.evaluator import create_evaluator
from src.chains.query_analyzer import create_query_analyzer
from src.config.settings import Settings
from src.rag.vectorstore import VectorStoreManager


def create_nodes(settings: Settings):
    """全ノード関数を作成して辞書で返す

    settingsを受け取り、各チェーン・マネージャーを初期化してノード関数に注入する。
    LangGraphに登録するノード関数は (state) -> dict の形式が必要。

    Returns:
        dict: {"ノード名": ノード関数} の辞書
    """
    # 各コンポーネントの初期化
    query_analyzer = create_query_analyzer(settings)
    answer_generator = create_answer_generator(settings)
    evaluator = create_evaluator(settings)
    vectorstore_manager = VectorStoreManager(settings)

    # --- ノード1: クエリ分析 ---
    def analyze_query(state: RAGAgentState) -> dict[str, Any]:
        """ユーザーの質問を分析し、検索クエリを生成する

        query_analyzerチェーンを呼び出し、3つの検索クエリを生成。
        再検索時（iteration > 0）は前回の評価理由も考慮する。
        """
        question = state["query"]

        # 再検索時は前回の評価理由を加味して、より適切なクエリを生成
        if state.get("iteration", 0) > 0 and state.get("evaluation_reason"):
            question = (
                f"{state['query']}\n\n"
                f"前回の検索では以下が不足していました: {state['evaluation_reason']}\n"
                f"この不足を補う検索クエリを生成してください。"
            )

        # チェーン実行: SearchQueriesオブジェクトが返る
        result = query_analyzer.invoke({"question": question})

        return {
            "search_queries": result.queries,
        }

    # --- ノード2: ドキュメント検索 ---
    def retrieve_documents(state: RAGAgentState) -> dict[str, Any]:
        """生成された検索クエリでベクトル検索を実行する

        複数のクエリそれぞれで検索し、結果を統合する（Multi-Query RAG）。
        Annotated[list, operator.add] により、前回の検索結果に追加される。
        """
        search_queries = state["search_queries"]
        all_documents = []

        # 各検索クエリで検索を実行し、結果を統合
        for query in search_queries:
            docs = vectorstore_manager.similarity_search(query, k=3)
            all_documents.extend(docs)

        # 重複ドキュメントを除去（page_contentが同一のものを除外）
        # 注意: 複数クエリで同じドキュメントがヒットすることがある
        seen_contents = set()
        unique_documents = []
        for doc in all_documents:
            if doc.page_content not in seen_contents:
                seen_contents.add(doc.page_content)
                unique_documents.append(doc)

        return {
            "retrieved_documents": unique_documents,
        }

    # --- ノード3: 回答生成 ---
    def generate_answer(state: RAGAgentState) -> dict[str, Any]:
        """検索結果を基に回答を生成する

        検索で得たドキュメントをコンテキストとしてフォーマットし、
        answer_generatorチェーンで回答を生成する。
        """
        documents = state["retrieved_documents"]
        # ドキュメントをプロンプト用の文字列にフォーマット
        context = format_documents(documents)

        # チェーン実行: 回答文字列が返る
        answer = answer_generator.invoke({
            "question": state["query"],
            "context": context,
        })

        return {
            "answer": answer,
        }

    # --- ノード4: 回答評価 ---
    def evaluate_answer(state: RAGAgentState) -> dict[str, Any]:
        """生成された回答の品質を評価する

        evaluatorチェーンで回答の十分性を判定。
        不十分と判断された場合、グラフの条件分岐でanalyze_queryに戻る。

        参考: 書籍Chapter10 _evaluate_information（行322-330）
        """
        # チェーン実行: EvaluationResultオブジェクトが返る
        result = evaluator.invoke({
            "question": state["query"],
            "answer": state["answer"],
        })

        return {
            "is_sufficient": result.is_sufficient,
            "evaluation_reason": result.reason,
            # iterationを+1して反復回数をカウント
            "iteration": state.get("iteration", 0) + 1,
        }

    # ノード関数を辞書で返す
    return {
        "analyze_query": analyze_query,
        "retrieve_documents": retrieve_documents,
        "generate_answer": generate_answer,
        "evaluate_answer": evaluate_answer,
    }
