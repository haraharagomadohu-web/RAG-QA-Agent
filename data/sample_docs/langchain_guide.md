# LangChain 基本ガイド

## LangChainとは

LangChainは、大規模言語モデル（LLM）を使ったアプリケーション開発のためのフレームワークです。プロンプト管理、チェーン構成、外部データ連携など、LLMアプリ開発に必要な機能を提供します。

## 主要コンポーネント

### Chat Models

LLMとの対話を抽象化するインターフェースです。

```python
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

# OpenAI
llm = ChatOpenAI(model="gpt-4o-mini")

# Ollama（ローカル）
llm = ChatOllama(model="qwen2.5:3b")

response = llm.invoke("Pythonの特徴を3つ挙げてください")
```

### Prompt Templates

プロンプトをテンプレートとして管理し、変数を埋め込むことができます。

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "あなたは{role}です。"),
    ("human", "{question}"),
])

# 変数を埋め込んでメッセージを生成
messages = prompt.invoke({"role": "Python専門家", "question": "デコレータとは？"})
```

### LCEL（LangChain Expression Language）

パイプ演算子（|）でコンポーネントをチェーンとして構成するパターンです。

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | llm | StrOutputParser()
result = chain.invoke({"role": "Python専門家", "question": "デコレータとは？"})
```

LCELの利点:
- ストリーミング出力に自動対応
- バッチ処理に自動対応
- 非同期実行に自動対応

### 構造化出力（Structured Output）

LLMの出力をPydanticモデルに変換できます。

```python
from pydantic import BaseModel, Field

class Answer(BaseModel):
    answer: str = Field(description="回答")
    confidence: float = Field(description="確信度")

structured_llm = llm.with_structured_output(Answer)
result = structured_llm.invoke("Pythonの型ヒントについて教えてください")
# result は Answer のインスタンス
```

## RAG（Retrieval-Augmented Generation）

RAGは外部データソースから関連情報を検索し、LLMの回答に組み込むパターンです。

### ドキュメント読み込み

```python
from langchain_community.document_loaders import PyMuPDFLoader

loader = PyMuPDFLoader("document.pdf")
documents = loader.load()
```

### テキスト分割

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = splitter.split_documents(documents)
```

### ベクトルストア

```python
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="bge-m3")
db = Chroma.from_documents(chunks, embeddings)

# 検索
results = db.similarity_search("Pythonのデコレータ", k=3)
```

### RAGチェーン

```python
from langchain_core.runnables import RunnablePassthrough

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
answer = rag_chain.invoke("デコレータの使い方は？")
```

## LangSmithによるトレース

LangSmithを使うと、チェーンの各ステップの実行を可視化できます。

環境変数を設定するだけで自動的にトレースが有効になります:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your-api-key
export LANGCHAIN_PROJECT=my-project
```
