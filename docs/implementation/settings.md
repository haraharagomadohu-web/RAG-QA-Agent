# 設定モジュール（src/config/settings.py）

## 概要

アプリケーション全体の設定を一元管理するモジュール。
環境変数と`.env`ファイルから設定値を読み込み、型安全に管理する。
Ollama（LLM・Embedding）、LangSmith（トレース）、Chroma（ベクトルDB）の設定を含む。

## 実装手順

### 1. pydantic-settingsのBaseSettingsを継承したSettingsクラスを定義

- 目的: 環境変数を型安全に管理し、デフォルト値を提供するため
- やること: `BaseSettings`を継承し、各設定項目をクラス変数として定義
- なぜpydantic-settings: `.env`ファイルの自動読み込み、型バリデーション、デフォルト値が一箇所で管理できる。参考書籍（Chapter12 settings.py）でも同じパターンを使用

### 2. SettingsConfigDictでenv_fileを設定

- 目的: `.env`ファイルのパスとエンコーディングを指定するため
- やること: `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")`
- なぜ: 日本語パスを含む環境で文字化けを防ぐためにutf-8を明示指定

### 3. 大文字の設定値（環境変数にそのまま反映するもの）を定義

- 目的: LangSmithなど、環境変数名がそのまま設定名になるサービス向け
- やること: `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`等を大文字で定義
- なぜ大文字: LangChainは`LANGCHAIN_TRACING_V2`等の環境変数名を直接参照するため、設定名と環境変数名を一致させる

### 4. 小文字の設定値（アプリケーション固有）を定義

- 目的: Ollamaモデル名やChromaパスなど、アプリ固有の設定を管理
- やること: `ollama_model`, `chroma_persist_directory`等を定義
- なぜ小文字: 環境変数として直接使われないアプリ設定であることを区別

### 5. `_set_env_variables`メソッドでLangSmith用環境変数を設定

- 目的: LangChainが環境変数を直接参照するため、Settingsの値をos.environに反映
- やること: 大文字の設定項目をループしてos.environに設定
- なぜ必要: pydantic-settingsは`.env`を読むが、os.environには自動反映しない。LangChainライブラリは`os.environ`を直接参照するため、手動で反映が必要

### 6. シングルトン関数`get_settings`を作成

- 目的: アプリ全体で同じSettingsインスタンスを共有するため
- やること: `functools.lru_cache`でキャッシュしたファクトリ関数を作成
- なぜlru_cache: Settingsの初期化（.envファイル読み込み）は1回だけ行えば十分。毎回読み込むのは無駄

## 判断理由

- **pydantic-settings**: FastAPIとの相性が良く、型安全。参考書籍でも同じパターンを採用
- **_set_env_variables**: 書籍Chapter12のパターンをそのまま踏襲。LangChainの環境変数依存を解決する定番手法
- **lru_cache**: FastAPIのDependency Injectionと組み合わせて使えるシンプルなシングルトンパターン
