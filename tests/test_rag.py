"""RAGパイプラインのテスト

ドキュメント読み込み → チャンク分割 の基本的な流れをテストする。
ベクトルストアのテストはOllamaが必要なため、統合テストとして分離。
"""

from pathlib import Path

from langchain_core.documents import Document

from src.rag.chunker import split_documents
from src.rag.document_loader import load_directory, load_markdown


# サンプルドキュメントのディレクトリ
SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample_docs"


class TestDocumentLoader:
    """ドキュメントローダーのテスト"""

    def test_load_markdown(self):
        """Markdownファイルが正しく読み込めること"""
        md_files = list(SAMPLE_DIR.glob("*.md"))
        assert len(md_files) > 0, "サンプルMDファイルが見つかりません"

        docs = load_markdown(str(md_files[0]))
        assert len(docs) > 0
        assert isinstance(docs[0], Document)
        # page_contentが空でないこと
        assert len(docs[0].page_content) > 0

    def test_load_directory(self):
        """ディレクトリ内の全ファイルが読み込めること"""
        docs = load_directory(str(SAMPLE_DIR))
        assert len(docs) > 0
        # 3つのサンプルファイルが読み込まれるはず
        assert len(docs) >= 3

    def test_load_directory_empty(self, tmp_path):
        """空ディレクトリの場合は空リストを返すこと"""
        docs = load_directory(str(tmp_path))
        assert docs == []


class TestChunker:
    """テキスト分割のテスト"""

    def test_split_documents(self):
        """ドキュメントがチャンクに分割されること"""
        # テスト用のドキュメント
        docs = [
            Document(
                page_content="あ" * 2000,  # 2000文字のドキュメント
                metadata={"source": "test.md"},
            )
        ]
        chunks = split_documents(docs, chunk_size=1000, chunk_overlap=200)

        # 2000文字のドキュメントは複数チャンクに分割されるはず
        assert len(chunks) > 1
        # 各チャンクがchunk_size以下であること
        for chunk in chunks:
            assert len(chunk.page_content) <= 1000

    def test_metadata_preserved(self):
        """分割後もメタデータが保持されること"""
        docs = [
            Document(
                page_content="テスト文書。" * 500,
                metadata={"source": "test.pdf", "page": 1},
            )
        ]
        chunks = split_documents(docs, chunk_size=500, chunk_overlap=100)

        for chunk in chunks:
            assert chunk.metadata["source"] == "test.pdf"

    def test_short_document_not_split(self):
        """短いドキュメントは分割されないこと"""
        docs = [
            Document(
                page_content="短い文書です。",
                metadata={"source": "short.md"},
            )
        ]
        chunks = split_documents(docs, chunk_size=1000, chunk_overlap=200)
        assert len(chunks) == 1
