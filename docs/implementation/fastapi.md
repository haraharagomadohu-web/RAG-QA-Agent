# FastAPI REST API

## 概要

RAGエージェントをREST APIとして公開する。
3つのエンドポイント（質問応答・ドキュメントアップロード・ヘルスチェック）を提供。

## 実装手順

### 1. スキーマ定義（schemas.py）

- 目的: APIのリクエスト/レスポンスの型を定義
- やること: Pydantic BaseModelで各エンドポイントの入出力を定義
- なぜPydantic: FastAPIがPydanticモデルを自動でSwagger UIのドキュメントに反映する

### 2. APIルート（routes.py）

- 目的: 各エンドポイントの処理ロジックを定義
- やること:
  - `POST /api/query`: 質問→エージェント実行→回答
  - `POST /api/upload`: ファイルアップロード→チャンク分割→ベクトルDB追加
  - `GET /api/health`: Ollamaとベクトルストアの状態確認
- なぜAPIRouter: ルートをモジュール分離することで、main.pyをシンプルに保つ

### 3. FastAPIアプリ（main.py）

- 目的: FastAPIアプリケーションの初期化とルーターの登録
- やること: FastAPIインスタンス作成、CORSミドルウェア設定、ルーター登録
- なぜCORS: フロントエンド（将来的にNext.js等）から呼び出す場合に必要

## 判断理由

- **FastAPI**: 型安全、自動ドキュメント生成（Swagger UI）、非同期対応。インターン先の業務でも使用される可能性が高い
- **UploadFile**: FastAPIのファイルアップロード機能。multipart/form-dataに対応
- **Depends(get_settings)**: 設定のDI（依存性注入）。テスト時にモック設定に差し替えやすい
