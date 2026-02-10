"""ドキュメント投入スクリプト

data/sample_docs/ 内のファイルを読み込み、チャンク分割してベクトルDBに投入する。
初回セットアップ時や新しいドキュメントを追加する際に使用。

使用方法:
    python -m scripts.ingest

注意:
    - Ollamaサーバーが起動している必要がある
    - bge-m3モデルがpull済みである必要がある (ollama pull bge-m3)
"""

import sys
from pathlib import Path

# プロジェクトルートをsys.pathに追加
# スクリプトを直接実行する場合、srcパッケージが見つからないことがあるため
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_settings
from src.rag.chunker import split_documents
from src.rag.document_loader import load_directory
from src.rag.vectorstore import VectorStoreManager


def main():
    """メインの投入処理"""
    settings = get_settings()
    sample_dir = project_root / "data" / "sample_docs"

    print(f"=== ドキュメント投入スクリプト ===")
    print(f"対象ディレクトリ: {sample_dir}")
    print(f"ベクトルDB保存先: {settings.chroma_persist_directory}")
    print(f"Embeddingモデル: {settings.ollama_embedding_model}")
    print()

    # 1. ドキュメント読み込み
    print("[1/3] ドキュメントを読み込み中...")
    documents = load_directory(str(sample_dir))
    if not documents:
        print("エラー: ドキュメントが見つかりませんでした。")
        print(f"{sample_dir} にPDFまたはMarkdownファイルを配置してください。")
        return
    print(f"  → {len(documents)} 件のドキュメントを読み込みました")

    # 2. チャンク分割
    print("[2/3] チャンクに分割中...")
    chunks = split_documents(
        documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    print(f"  → {len(chunks)} 個のチャンクに分割しました")

    # 3. ベクトルDBに投入
    print("[3/3] ベクトルDBに投入中（Embedding生成に時間がかかります）...")
    manager = VectorStoreManager(settings)
    manager.create_from_documents(chunks)
    print(f"  → ベクトルDBへの投入が完了しました")
    print()
    print("完了! APIサーバーを起動して質問を試してみてください:")
    print("  uvicorn src.api.main:app --reload")


if __name__ == "__main__":
    main()
