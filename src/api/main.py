"""FastAPIアプリケーションのエントリーポイント

FastAPIインスタンスの作成、ミドルウェア設定、ルーター登録を行う。

起動方法:
    uvicorn src.api.main:app --reload

Swagger UIは http://localhost:8000/docs でアクセス可能
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config.settings import get_settings

# Settings初期化（環境変数をos.environに反映）
# アプリ起動時に1回だけ実行される
get_settings()

# FastAPIアプリの作成
app = FastAPI(
    title="技術文書QA RAGエージェント",
    description=(
        "技術文書を対象としたAI質問応答システム。\n"
        "LangChain + LangGraph + Ollama を使用し、"
        "ベクトル検索→回答生成→自己評価のマルチステップエージェントで回答を生成します。"
    ),
    version="0.1.0",
)

# CORSミドルウェアの設定
# フロントエンド（別オリジン）からのAPIアクセスを許可する
# 注意: 本番環境では allow_origins を具体的なドメインに制限すること
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発用: 全オリジン許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーターの登録
# prefix="/api" で全ルートに /api プレフィックスを追加
app.include_router(router, prefix="/api", tags=["RAG Agent"])
