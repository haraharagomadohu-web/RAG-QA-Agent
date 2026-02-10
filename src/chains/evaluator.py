"""回答品質評価チェーン

生成された回答が質問に十分に答えているかをLLMで自己評価する。
LangGraphエージェントの「不十分なら再検索」ループの判断基準として使用。

参考: 書籍Chapter10 InformationEvaluator（行186-219）のパターン
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from src.config.settings import Settings


class EvaluationResult(BaseModel):
    """回答品質評価の構造化出力

    書籍Chapter10の EvaluationResult を参考に、
    RAG向けに回答品質のスコアと理由を追加。
    """

    is_sufficient: bool = Field(
        ...,
        description="回答が質問に十分に答えているかどうか",
    )
    score: float = Field(
        ...,
        description="回答品質のスコア（0.0〜1.0）。0.7以上で十分と判断",
        ge=0.0,
        le=1.0,
    )
    reason: str = Field(
        ...,
        description="十分/不十分と判断した理由",
    )
    missing_info: str = Field(
        default="",
        description="不十分な場合、追加で必要な情報の説明",
    )


def create_evaluator(settings: Settings):
    """回答品質評価チェーンを作成して返す

    チェーンの流れ:
    {"question": str, "answer": str} → プロンプト → LLM（構造化出力） → EvaluationResult

    Returns:
        Runnable: invoke({"question": "...", "answer": "..."}) で EvaluationResult を返すチェーン
    """
    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.0,
    )

    # with_structured_output: EvaluationResultの型に従って出力をパース
    structured_llm = llm.with_structured_output(EvaluationResult)

    # 評価プロンプト: 回答の品質を判定する指示
    # 書籍Chapter10のInformationEvaluatorのプロンプト構造を参考に、
    # RAG向けの評価基準（正確性・網羅性・出典有無）を追加
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "あなたは回答品質を評価する専門家です。\n"
                "以下の基準で評価してください:\n"
                "1. 正確性: 回答が質問に正確に答えているか\n"
                "2. 網羅性: 質問の全ての側面に回答しているか\n"
                "3. 出典: 回答が根拠を示しているか\n"
                "4. 明確さ: 回答が分かりやすいか\n\n"
                "スコアが0.7以上なら is_sufficient=true としてください。",
            ),
            (
                "human",
                "以下の質問と回答を評価してください。\n\n"
                "質問: {question}\n\n"
                "回答: {answer}",
            ),
        ]
    )

    chain = prompt | structured_llm

    return chain
