"""テキスト分割モジュール

ドキュメントを検索に適したサイズのチャンクに分割する。
日本語文書に対応したセパレータ設定が特徴。

参考: 書籍Chapter6のテキスト分割パターン
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 日本語文書に適したセパレータリスト
# RecursiveCharacterTextSplitterはこのリストの先頭から順に試し、
# chunk_size以下に収まる区切りを採用する
# → 大きい区切り（段落）で分割できるならそちらを優先し、文脈の断片化を防ぐ
JAPANESE_SEPARATORS = [
    "\n\n",  # 段落区切り（最も大きな区切り）
    "\n",    # 改行
    "。",    # 句点（日本語の文末）
    "、",    # 読点（日本語の文中区切り）
    " ",     # スペース
    "",      # 最後の手段: 1文字ずつ分割
]


def split_documents(
    documents: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[Document]:
    """ドキュメントリストをチャンクに分割する

    Args:
        documents: 分割対象のDocumentリスト
        chunk_size: 1チャンクの最大文字数。
            大きすぎると検索精度が下がる（無関係な情報が多く含まれる）。
            小さすぎると文脈が断片化する。
            1000文字は日本語技術文書で1つのトピックを含むのに適切なサイズ。
        chunk_overlap: チャンク間のオーバーラップ文字数。
            チャンク境界で情報が失われるのを防ぐ。
            chunk_sizeの20%程度が目安。

    Returns:
        分割後のDocumentリスト（元のmetadataは保持される）
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=JAPANESE_SEPARATORS,
    )

    # split_documentsはmetadata（出典情報等）を保持したまま分割する
    return splitter.split_documents(documents)
