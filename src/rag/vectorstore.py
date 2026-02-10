"""ベクトルストアモジュール

Ollamaの bge-m3 Embeddingモデルを使い、ドキュメントチャンクをベクトル化して
Chromaに保存・検索する。永続化モードで、Embeddingの再計算を避ける。

参考: 書籍Chapter6 notebook (cell-7, 8) のChromaパターン
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_ollama import OllamaEmbeddings

from src.config.settings import Settings


class VectorStoreManager:
    """Chromaベクトルストアの作成・読み込み・検索を管理するクラス

    Chromaを永続化モードで使用するため、一度作成したEmbeddingは
    ディスクに保存され、再起動後も再利用できる。
    """

    def __init__(self, settings: Settings):
        # OllamaEmbeddings: ローカルのOllamaサーバーからEmbeddingを生成
        # bge-m3は多言語対応で日本語の意味的類似度を高精度に計算できる
        self.embeddings = OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )
        # 永続化ディレクトリ: このパスにChromaのデータが保存される
        self.persist_directory = settings.chroma_persist_directory

    def create_from_documents(self, documents: list[Document]) -> Chroma:
        """ドキュメントリストから新しいベクトルストアを作成する

        内部でEmbedding生成が行われるため、ドキュメント数に比例して時間がかかる。
        注意: 既存のデータがある場合は上書きされる
        """
        return Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def load_existing(self) -> Chroma:
        """永続化済みのベクトルストアを読み込む

        scripts/ingest.pyで事前にデータを投入しておく必要がある。
        データが無い場合でもエラーにはならず、空のストアが返る。
        """
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

    def add_documents(self, documents: list[Document]) -> Chroma:
        """既存のベクトルストアにドキュメントを追加する

        新しいドキュメントをアップロードした際に使用。
        既存のデータは保持したまま、新しいドキュメントのEmbeddingを追加する。
        """
        db = self.load_existing()
        db.add_documents(documents)
        return db

    def similarity_search(
        self, query: str, k: int = 5
    ) -> list[Document]:
        """クエリに類似するドキュメントを検索する

        Args:
            query: 検索クエリ（自然言語テキスト）
            k: 返す結果の数。多いほど網羅的だがノイズも増える。
               5はRAGで一般的なデフォルト値。

        Returns:
            類似度の高い順にソートされたDocumentリスト
        """
        db = self.load_existing()
        return db.similarity_search(query, k=k)

    def as_retriever(self, k: int = 5) -> VectorStoreRetriever:
        """LangChainのRetrieverインターフェースとして返す

        Retrieverはチェーン（LCEL）の中で使うための標準インターフェース。
        `retriever.invoke(query)` で検索結果のDocumentリストを返す。
        LangGraphのノードやLCELチェーンに組み込む際に使用する。
        """
        db = self.load_existing()
        return db.as_retriever(search_kwargs={"k": k})
