"""LangGraphエージェントのテスト

State定義とグラフ構造のテスト。
ノード関数のテストはOllama依存のため、統合テストとして別途実施。
"""

from src.agent.graph import MAX_ITERATIONS, should_retry
from src.agent.state import RAGAgentState


class TestShouldRetry:
    """条件分岐関数のテスト"""

    def test_sufficient_answer_ends(self):
        """回答が十分な場合は終了すること"""
        state: RAGAgentState = {
            "query": "テスト",
            "search_queries": [],
            "retrieved_documents": [],
            "answer": "テスト回答",
            "is_sufficient": True,
            "evaluation_reason": "十分な回答",
            "iteration": 1,
        }
        assert should_retry(state) == "end"

    def test_insufficient_answer_retries(self):
        """回答が不十分な場合は再検索すること"""
        state: RAGAgentState = {
            "query": "テスト",
            "search_queries": [],
            "retrieved_documents": [],
            "answer": "不十分な回答",
            "is_sufficient": False,
            "evaluation_reason": "情報不足",
            "iteration": 1,
        }
        assert should_retry(state) == "retry"

    def test_max_iterations_ends(self):
        """最大反復回数に達した場合は終了すること"""
        state: RAGAgentState = {
            "query": "テスト",
            "search_queries": [],
            "retrieved_documents": [],
            "answer": "不十分な回答",
            "is_sufficient": False,
            "evaluation_reason": "情報不足",
            "iteration": MAX_ITERATIONS,
        }
        assert should_retry(state) == "end"

    def test_first_iteration_retries(self):
        """初回で不十分な場合は再検索すること"""
        state: RAGAgentState = {
            "query": "テスト",
            "search_queries": [],
            "retrieved_documents": [],
            "answer": "不十分",
            "is_sufficient": False,
            "evaluation_reason": "",
            "iteration": 0,
        }
        assert should_retry(state) == "retry"
