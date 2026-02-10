"""アプリケーション設定モジュール

pydantic-settingsを使い、環境変数と.envファイルから設定を読み込む。
Ollama、LangSmith、Chromaなど全コンポーネントの設定を一元管理する。

参考: 書籍Chapter12 settings.py のパターンを拡張
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション全体の設定を管理するクラス

    設定値の命名規則:
    - 大文字: 環境変数としてそのまま使われるもの（LangSmith等）
    - 小文字: アプリケーション固有の設定
    """

    # SettingsConfigDictで.envファイルの読み込み設定を定義
    # env_file_encoding="utf-8" は日本語パス対応のため明示指定
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # === LangSmith設定 ===
    # LangChainはこれらの環境変数を直接参照してトレースを制御する
    # "true"にすると全てのLangChain呼び出しがLangSmithに記録される
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    # プロジェクト名: LangSmithダッシュボードでの識別用
    LANGCHAIN_PROJECT: str = "tech-doc-qa-agent"

    # === Ollama設定 ===
    # ローカルで動作するLLMを使用するため、APIキー不要・コストゼロ
    ollama_model: str = "qwen2.5:3b"
    # bge-m3は多言語対応の高品質Embeddingモデル（日本語に強い）
    ollama_embedding_model: str = "bge-m3"
    ollama_base_url: str = "http://localhost:11434"

    # === アプリケーション設定 ===
    # Chromaの永続化ディレクトリ: Embeddingの再計算を避けるため永続化
    chroma_persist_directory: str = "./data/chroma_db"
    # チャンクサイズ: 大きすぎるとコンテキストが曖昧に、小さすぎると情報が断片化
    # 1000文字は日本語技術文書で1つのトピックを含むのに適切なサイズ
    chunk_size: int = 1000
    # オーバーラップ: チャンク境界での情報欠落を防ぐ
    # chunk_sizeの20%程度が目安
    chunk_overlap: int = 200
    temperature: float = 0.0

    def __init__(self, **values):
        super().__init__(**values)
        # LangChainが環境変数を直接参照するため、Settingsの値をos.environに反映
        # 注意: pydantic-settingsは.envを読むが、os.environには自動で書き込まない
        self._set_env_variables()

    def _set_env_variables(self):
        """大文字の設定値をos.environに反映する

        LangChainライブラリ（特にLangSmith）は os.environ["LANGCHAIN_TRACING_V2"] 等を
        直接参照するため、.envから読み込んだ値を環境変数にも設定する必要がある。
        書籍Chapter12のsettings.pyと同じパターン。
        """
        for key in self.model_fields:
            # 大文字のフィールド名のみ環境変数に設定
            # （小文字のアプリ設定は環境変数に反映する必要がない）
            if key.isupper():
                os.environ[key] = getattr(self, key)


# lru_cacheでSettingsインスタンスをキャッシュ（シングルトンパターン）
# .envファイルの読み込みは1回だけ行えば十分なため
# FastAPIのDepends(get_settings)でも使用できる
@lru_cache
def get_settings() -> Settings:
    """Settingsのシングルトンインスタンスを返す"""
    return Settings()
