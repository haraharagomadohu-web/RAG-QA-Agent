"""APIルート定義

各エンドポイントの処理ロジックを定義する。
FastAPIのAPIRouterを使い、ルートをモジュール分離している。
"""

import tempfile
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from src.agent.graph import create_rag_agent
from src.api.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SourceDocument,
    UploadResponse,
)
from src.config.settings import Settings, get_settings
from src.rag.chunker import split_documents
from src.rag.document_loader import load_markdown, load_pdf
from src.rag.vectorstore import VectorStoreManager

# APIRouterでルートをグループ化
# prefix="/api" は main.py で設定するためここでは不要
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    settings: Settings = Depends(get_settings),
):
    """質問応答エンドポイント

    ユーザーの質問を受け取り、RAGエージェントを実行して回答を返す。

    処理の流れ:
    1. エージェントグラフを作成
    2. 初期状態を設定してグラフを実行
    3. 結果から回答・出典・評価情報を抽出してレスポンスを構築
    """
    # エージェントグラフを作成（settingsを注入）
    agent = create_rag_agent(settings)

    # 初期状態を設定してエージェントを実行
    # 全フィールドを初期値で埋める必要がある（TypedDictの制約）
    result = agent.invoke({
        "query": request.question,
        "search_queries": [],
        "retrieved_documents": [],
        "answer": "",
        "is_sufficient": False,
        "evaluation_reason": "",
        "iteration": 0,
    })

    # 検索結果から出典情報を抽出
    sources = []
    # 重複を避けるため、出典のソースパスを追跡
    seen_sources = set()
    for doc in result.get("retrieved_documents", []):
        source_key = doc.metadata.get("source", "不明")
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append(
                SourceDocument(
                    # 内容は先頭200文字に制限（レスポンスサイズを抑える）
                    content=doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content,
                    source=doc.metadata.get("source", "不明"),
                    page=str(doc.metadata.get("page", "")),
                )
            )

    return QueryResponse(
        answer=result.get("answer", "回答を生成できませんでした"),
        sources=sources,
        is_sufficient=result.get("is_sufficient", False),
        iterations=result.get("iteration", 0),
    )


@router.post("/upload", response_model=UploadResponse)
def upload_document(
    file: UploadFile,
    settings: Settings = Depends(get_settings),
):
    """ドキュメントアップロードエンドポイント

    ファイルをアップロードし、チャンク分割してベクトルDBに追加する。

    処理の流れ:
    1. アップロードされたファイルを一時ファイルに保存
    2. ファイル形式に応じてローダーで読み込み
    3. チャンクに分割
    4. ベクトルストアに追加
    """
    # 対応するファイル形式を確認
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".pdf", ".md", ".txt"):
        raise HTTPException(
            status_code=400,
            detail=f"未対応のファイル形式: {suffix}。PDF, Markdown, テキストに対応しています。",
        )

    # 一時ファイルに保存してから処理
    # 注意: UploadFileはメモリ上のストリームなので、ローダーがファイルパスを必要とする場合は
    # 一時ファイルに書き出す必要がある
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # ファイル形式に応じたローダーで読み込み
    if suffix == ".pdf":
        documents = load_pdf(tmp_path)
    else:
        documents = load_markdown(tmp_path)

    # チャンク分割
    chunks = split_documents(
        documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    # ベクトルストアに追加
    vectorstore_manager = VectorStoreManager(settings)
    vectorstore_manager.add_documents(chunks)

    # 一時ファイルを削除
    Path(tmp_path).unlink(missing_ok=True)

    return UploadResponse(
        message=f"{file.filename} を正常に処理しました",
        document_count=len(chunks),
    )


@router.get("/health", response_model=HealthResponse)
def health_check(
    settings: Settings = Depends(get_settings),
):
    """ヘルスチェックエンドポイント

    Ollamaサーバーとベクトルストアの状態を確認する。
    デプロイ後のモニタリングや、フロントエンドからの接続確認に使用。
    """
    # Ollamaサーバーの接続確認
    ollama_status = "ok"
    try:
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
        if response.status_code != 200:
            ollama_status = "error: 接続できません"
    except Exception:
        ollama_status = "error: Ollamaサーバーに接続できません"

    # ベクトルストアの状態確認
    vectorstore_status = "ok"
    try:
        manager = VectorStoreManager(settings)
        db = manager.load_existing()
        # コレクション内のドキュメント数を確認
        count = db._collection.count()
        vectorstore_status = f"ok ({count} documents)"
    except Exception:
        vectorstore_status = "error: ベクトルストアにアクセスできません"

    # 全体のステータス
    overall = "healthy" if "error" not in ollama_status and "error" not in vectorstore_status else "unhealthy"

    return HealthResponse(
        status=overall,
        ollama_status=ollama_status,
        vectorstore_status=vectorstore_status,
    )
