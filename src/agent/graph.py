"""LangGraphエージェント構築モジュール

StateGraphでノードとエッジを接続し、RAGエージェントのワークフローを定義する。
自己評価ループにより、回答品質が不十分な場合は自動的に再検索・再回答を行う。

グラフのフロー:
```
analyze_query → retrieve → generate_answer → evaluate
    ^                                            |
    |------ (不十分 & iteration < 3) ←-----------|
                                                 |
                                      (十分) → END
```

参考: 書籍Chapter10 DocumentationAgent._create_graph（行279-305）
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agent.nodes import create_nodes
from src.agent.state import RAGAgentState
from src.config.settings import Settings


# 自己評価ループの最大反復回数
# 多すぎるとOllamaの処理時間が増大、少なすぎると品質が不十分
MAX_ITERATIONS = 3


def should_retry(state: RAGAgentState) -> str:
    """条件付きエッジの判定関数

    evaluate_answerノードの後に呼ばれ、次のノードを決定する。

    判定ロジック:
    - 回答が十分（is_sufficient=True） → "end"（終了）
    - 反復回数が上限に達した → "end"（強制終了、無限ループ防止）
    - 上記以外 → "retry"（再検索）

    Returns:
        "end" or "retry" の文字列。add_conditional_edgesのマッピングで使用
    """
    if state.get("is_sufficient", False):
        return "end"
    if state.get("iteration", 0) >= MAX_ITERATIONS:
        return "end"
    return "retry"


def create_rag_agent(settings: Settings) -> CompiledStateGraph:
    """RAGエージェントのグラフを構築してコンパイルする

    Args:
        settings: アプリケーション設定

    Returns:
        CompiledStateGraph: invoke()で実行可能なコンパイル済みグラフ

    使用例:
        agent = create_rag_agent(settings)
        result = agent.invoke({
            "query": "FastAPIの非同期処理について教えて",
            "search_queries": [],
            "retrieved_documents": [],
            "answer": "",
            "is_sufficient": False,
            "evaluation_reason": "",
            "iteration": 0,
        })
        print(result["answer"])
    """
    # ノード関数を作成（settingsを注入）
    nodes = create_nodes(settings)

    # StateGraphの初期化
    # RAGAgentStateの型情報を基に、各ノード間のデータフローを管理する
    workflow = StateGraph(RAGAgentState)

    # --- ノードの登録 ---
    # add_nodeの第1引数はノード名、第2引数はノード関数
    workflow.add_node("analyze_query", nodes["analyze_query"])
    workflow.add_node("retrieve_documents", nodes["retrieve_documents"])
    workflow.add_node("generate_answer", nodes["generate_answer"])
    workflow.add_node("evaluate_answer", nodes["evaluate_answer"])

    # --- エントリーポイント設定 ---
    # グラフの開始ノードを指定
    workflow.set_entry_point("analyze_query")

    # --- エッジの接続（直線的な流れ） ---
    # add_edgeで「このノードの次はこのノード」を指定
    workflow.add_edge("analyze_query", "retrieve_documents")
    workflow.add_edge("retrieve_documents", "generate_answer")
    workflow.add_edge("generate_answer", "evaluate_answer")

    # --- 条件付きエッジ（自己評価後の分岐） ---
    # evaluate_answerの後、should_retry関数の戻り値に応じて分岐:
    # - "retry" → analyze_queryに戻る（再検索ループ）
    # - "end" → ENDで終了
    workflow.add_conditional_edges(
        "evaluate_answer",  # 分岐元のノード
        should_retry,       # 判定関数
        {
            "retry": "analyze_query",  # 再検索ループ
            "end": END,               # グラフ終了
        },
    )

    # コンパイル: グラフの整合性チェックを行い、実行可能な形式にする
    return workflow.compile()
