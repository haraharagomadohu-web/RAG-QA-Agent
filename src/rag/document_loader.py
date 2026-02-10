"""ドキュメントローダーモジュール

PDF・Markdownファイルを読み込み、LangChainのDocumentオブジェクトに変換する。
LangChainのDocumentは page_content（テキスト）と metadata（出典情報等）を持つ。

参考: 書籍Chapter6のドキュメント読み込みパターン
"""

from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_core.documents import Document


def load_pdf(file_path: str) -> list[Document]:
    """PDFファイルを読み込んでDocumentリストを返す

    PyMuPDFLoaderを使用する理由:
    - 日本語PDFの文字化けが少ない
    - ページ番号をmetadataに自動で含む（出典表示に便利）
    - 他のローダー（pdfplumber等）より高速
    """
    loader = PyMuPDFLoader(file_path)
    return loader.load()


def load_markdown(file_path: str) -> list[Document]:
    """Markdownファイルを読み込んでDocumentリストを返す

    TextLoaderを使用し、encoding="utf-8"を明示指定する。
    注意: Windows環境ではデフォルトがcp932のため、utf-8を指定しないと文字化けする
    """
    loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()


def load_directory(dir_path: str) -> list[Document]:
    """ディレクトリ内のPDF・Markdownファイルを全て読み込む

    対応するファイル形式:
    - .pdf → load_pdf
    - .md → load_markdown
    - .txt → load_markdown（TextLoaderで対応）

    ファイルが見つからない場合は空リストを返す（エラーにしない）
    """
    directory = Path(dir_path)
    documents: list[Document] = []

    # 拡張子ごとに適切なローダーを選択
    # globで再帰的にファイルを探索（サブディレクトリも含む）
    for file_path in sorted(directory.rglob("*")):
        if file_path.suffix.lower() == ".pdf":
            documents.extend(load_pdf(str(file_path)))
        elif file_path.suffix.lower() in (".md", ".txt"):
            documents.extend(load_markdown(str(file_path)))

    return documents
