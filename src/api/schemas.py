"""APIスキーマ定義

FastAPIのリクエスト/レスポンスの型をPydanticモデルで定義する。
FastAPIはこれらのモデルを基にSwagger UIのドキュメントを自動生成する。
"""

from pydantic import BaseModel, Field


# === クエリ（質問応答）エンドポイント ===

class QueryRequest(BaseModel):
    """質問リクエスト"""

    question: str = Field(
        ...,
        description="質問文",
        min_length=1,
        # 空文字を防ぐため min_length=1 を設定
        examples=["FastAPIの非同期処理について教えてください"],
    )
    top_k: int = Field(
        default=5,
        description="検索で返すドキュメント数",
        ge=1,
        le=20,
    )


class SourceDocument(BaseModel):
    """回答の出典ドキュメント情報"""

    content: str = Field(..., description="ドキュメントの内容（抜粋）")
    source: str = Field(..., description="ファイルパスまたはドキュメント名")
    page: str = Field(default="", description="ページ番号（あれば）")


class QueryResponse(BaseModel):
    """質問応答レスポンス"""

    answer: str = Field(..., description="生成された回答")
    sources: list[SourceDocument] = Field(
        default_factory=list,
        description="参照した出典ドキュメント",
    )
    is_sufficient: bool = Field(
        ..., description="エージェントが回答を十分と判断したか"
    )
    iterations: int = Field(
        ..., description="検索→回答→評価の反復回数"
    )


# === アップロードエンドポイント ===

class UploadResponse(BaseModel):
    """ドキュメントアップロードレスポンス"""

    message: str = Field(..., description="処理結果メッセージ")
    document_count: int = Field(..., description="追加されたドキュメントチャンク数")


# === ヘルスチェックエンドポイント ===

class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""

    status: str = Field(..., description="全体のステータス")
    ollama_status: str = Field(..., description="Ollamaの接続状態")
    vectorstore_status: str = Field(..., description="ベクトルストアの状態")
