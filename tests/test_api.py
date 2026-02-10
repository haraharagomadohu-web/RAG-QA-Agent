"""FastAPI エンドポイントのテスト

APIスキーマのバリデーションとヘルスチェックをテストする。
query/uploadエンドポイントはOllamaとベクトルDB依存のため、統合テストとして別途実施。
"""

from src.api.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SourceDocument,
    UploadResponse,
)


class TestSchemas:
    """APIスキーマのバリデーションテスト"""

    def test_query_request_valid(self):
        """正常なクエリリクエストが受け付けられること"""
        req = QueryRequest(question="FastAPIとは？", top_k=3)
        assert req.question == "FastAPIとは？"
        assert req.top_k == 3

    def test_query_request_default_top_k(self):
        """top_kのデフォルト値が5であること"""
        req = QueryRequest(question="テスト")
        assert req.top_k == 5

    def test_query_response(self):
        """レスポンスモデルが正しく構築できること"""
        resp = QueryResponse(
            answer="テスト回答",
            sources=[
                SourceDocument(
                    content="テスト内容",
                    source="test.md",
                    page="1",
                )
            ],
            is_sufficient=True,
            iterations=1,
        )
        assert resp.answer == "テスト回答"
        assert len(resp.sources) == 1

    def test_upload_response(self):
        """アップロードレスポンスが正しく構築できること"""
        resp = UploadResponse(
            message="test.pdf を正常に処理しました",
            document_count=10,
        )
        assert resp.document_count == 10

    def test_health_response(self):
        """ヘルスチェックレスポンスが正しく構築できること"""
        resp = HealthResponse(
            status="healthy",
            ollama_status="ok",
            vectorstore_status="ok (5 documents)",
        )
        assert resp.status == "healthy"
