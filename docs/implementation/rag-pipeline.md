# RAGパイプライン（ドキュメントローダー・チャンカー・ベクトルストア）

## 概要

RAG（Retrieval-Augmented Generation）の基盤となる3つのモジュールを実装する。
ドキュメントの読み込み→テキスト分割→Embedding生成・保存・検索の一連の流れ。

```
PDF/Markdown → DocumentLoader → Chunker → VectorStore(Chroma + bge-m3) → Retriever
```

## 実装手順

### 1. ドキュメントローダー（document_loader.py）

- 目的: PDF・Markdownファイルを統一された`Document`オブジェクトに変換する
- やること:
  - `load_pdf`: PyMuPDFLoaderでPDFを読み込み（日本語対応）
  - `load_markdown`: TextLoaderでMarkdownを読み込み
  - `load_directory`: ディレクトリ内の全ファイルを一括読み込み
- なぜPyMuPDF: 日本語PDFの文字化けが少なく、ページ情報をメタデータに保持できる
- なぜLangChainのLoaderを使う: `Document`オブジェクト（page_content + metadata）に統一できる

### 2. テキスト分割（chunker.py）

- 目的: ドキュメントを検索に適したサイズのチャンクに分割する
- やること: `RecursiveCharacterTextSplitter`で分割（日本語セパレータ対応）
- なぜRecursive: 大きい区切り（`\n\n`）から順に試し、指定サイズに収まるまで細かく分割。文脈の断片化を最小限にする
- 日本語対応: セパレータに`。`（句点）、`、`（読点）を追加。英語デフォルトだと日本語文が不自然な箇所で切れる

### 3. ベクトルストア（vectorstore.py）

- 目的: ドキュメントチャンクをEmbeddingに変換し、Chromaに保存・検索する
- やること:
  - `create_from_documents`: ドキュメントリストからベクトルストアを新規作成
  - `load_existing`: 既存の永続化済みストアを読み込み
  - `add_documents`: 既存ストアにドキュメントを追加
  - `similarity_search`: 類似度検索
  - `as_retriever`: LangChainのRetrieverインターフェースとして返す
- なぜChroma: 軽量・組み込み可能・永続化対応。ポートフォリオ規模に最適
- なぜ永続化: Embeddingの生成は時間がかかるため、毎回やり直すのは非効率

## 判断理由

- **PyMuPDF vs pdfplumber**: PyMuPDFの方が高速で、LangChainとの統合が容易
- **RecursiveCharacterTextSplitter vs TokenTextSplitter**: トークン数ベースの方が正確だが、Ollamaのトークナイザー情報が不要なRecursiveの方がシンプル
- **Chroma vs FAISS**: Chromaは永続化が組み込みで、フィルタリング機能もある。FAISSはメモリ上のみ（永続化には追加コードが必要）
- **bge-m3**: 多言語対応で日本語Embeddingの品質が高い。既にOllamaにインストール済み
