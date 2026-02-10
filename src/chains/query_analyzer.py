"""クエリ分析チェーン

ユーザーの質問を分析し、ベクトル検索に適した複数の検索クエリを生成する。
1つの質問に対して3つの異なる検索クエリを生成することで、
検索の網羅性を高める（Multi-Query RAGパターン）。

参考: 書籍Chapter6 cell-14 の QueryGenerationOutput パターン
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from src.config.settings import Settings


# === 出力スキーマ定義 ===
# with_structured_output で使用するPydanticモデル
# LLMの出力をこの型に強制的にパースする
class SearchQueries(BaseModel):
    """検索クエリの構造化出力"""

    queries: list[str] = Field(
        ...,
        description="元の質問を異なる言い回しで表現した3つの検索クエリ",
        min_length=1,
        max_length=5,
    )
    intent: str = Field(
        ...,
        description="ユーザーの質問の意図を簡潔に説明",
    )


def create_query_analyzer(settings: Settings):
    """クエリ分析チェーンを作成して返す

    チェーンの流れ:
    ユーザーの質問 → プロンプト → LLM（構造化出力） → SearchQueries

    Returns:
        Runnable: invoke({"question": "..."}) で SearchQueries を返すチェーン
    """
    # ChatOllama: ローカルのOllamaサーバーに接続
    # temperature=0.0: 検索クエリ生成は創造性よりも正確性が重要なため
    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.0,
    )

    # with_structured_output: LLMの出力をPydanticモデルにパースする
    # Ollamaはformat="json"を内部で使用して構造化出力に対応
    structured_llm = llm.with_structured_output(SearchQueries)

    # プロンプト: 検索クエリ生成の指示
    # systemメッセージで役割を定義し、humanメッセージでタスクを指示
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "あなたは検索クエリの最適化を行う専門家です。"
                "ユーザーの質問に対して、異なる観点から3つの検索クエリを生成してください。",
            ),
            (
                "human",
                "以下の質問に対して、ベクトル検索で関連ドキュメントを見つけるための"
                "検索クエリを3つ生成してください。\n\n"
                "各クエリは異なる言い回しや観点を使い、検索の網羅性を高めてください。\n\n"
                "質問: {question}",
            ),
        ]
    )

    # LCEL: パイプ演算子でチェーンを構成
    # prompt | structured_llm の形で、プロンプト → LLM → パース が一連の流れになる
    chain = prompt | structured_llm

    return chain
