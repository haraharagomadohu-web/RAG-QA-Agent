"""回答生成チェーン

検索で得たドキュメントを基に、出典情報付きの回答を生成する。
LCELの `prompt | llm | StrOutputParser()` パターンを使用。

参考: 書籍Chapter6 cell-8 のRAGチェーンパターン
"""

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.config.settings import Settings


def format_documents(documents: list[Document]) -> str:
    """Documentリストをプロンプトに埋め込むための文字列に変換する

    各ドキュメントに番号を振り、出典情報（ファイル名・ページ番号）を付与する。
    LLMがどのドキュメントを参照して回答したかを追跡できるようにする。
    """
    formatted_parts = []
    for i, doc in enumerate(documents, 1):
        # メタデータから出典情報を取得
        source = doc.metadata.get("source", "不明")
        page = doc.metadata.get("page", "")
        # 出典表示: ファイル名とページ番号（あれば）
        source_info = f"出典: {source}"
        if page:
            source_info += f" (p.{page})"

        formatted_parts.append(
            f"[文書{i}] {source_info}\n{doc.page_content}"
        )

    return "\n\n---\n\n".join(formatted_parts)


def create_answer_generator(settings: Settings):
    """回答生成チェーンを作成して返す

    チェーンの流れ:
    {"question": str, "context": str} → プロンプト → LLM → StrOutputParser → str

    Returns:
        Runnable: invoke({"question": "...", "context": "..."}) で回答文字列を返すチェーン
    """
    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.temperature,
    )

    # RAGプロンプト: コンテキスト（検索結果）を基に回答を生成する指示
    # 重要なポイント:
    # - 「コンテキストの情報のみ」を使うよう指示→ハルシネーション防止
    # - 「出典を明記」→RAGの信頼性を示す
    # - 「分からない場合は正直に」→不正確な回答より「分からない」の方が価値がある
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "あなたは技術文書の質問応答アシスタントです。\n"
                "以下のルールに従って回答してください:\n"
                "1. 提供されたコンテキスト（検索結果）の情報のみを使って回答すること\n"
                "2. 回答の根拠となった文書番号を [文書N] の形式で明記すること\n"
                "3. コンテキストに回答に必要な情報がない場合は、正直に「提供された文書からは回答できません」と述べること\n"
                "4. 回答は日本語で、簡潔かつ正確に行うこと",
            ),
            (
                "human",
                "コンテキスト:\n{context}\n\n"
                "質問: {question}\n\n"
                "上記のコンテキストを基に回答してください。",
            ),
        ]
    )

    # LCEL: prompt | llm | StrOutputParser()
    # StrOutputParserはLLMの出力から文字列部分だけを取り出す最もシンプルなパーサー
    chain = prompt | llm | StrOutputParser()

    return chain
