# FastAPI 基本ガイド

## FastAPIとは

FastAPIは、Python 3.7以降で使用できる、高速なWeb APIフレームワークです。型ヒントを活用した自動バリデーション、自動ドキュメント生成（Swagger UI）、高速な非同期処理が特徴です。

## インストール

```bash
pip install fastapi uvicorn[standard]
```

## 基本的なアプリケーション

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

## 起動方法

```bash
uvicorn main:app --reload
```

`--reload`オプションを付けると、コードの変更を検知して自動的にサーバーを再起動します。開発時に便利です。

## リクエストボディ

Pydanticモデルを使ってリクエストボディを定義します。

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    description: str = None

@app.post("/items/")
def create_item(item: Item):
    return item
```

FastAPIは自動的にリクエストボディのバリデーションを行い、不正なデータの場合は422エラーを返します。

## 依存性注入（Dependency Injection）

FastAPIの依存性注入システムを使うと、共通の処理を関数として切り出し、エンドポイントに注入できます。

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

## 非同期処理

FastAPIはasync/awaitによる非同期処理をサポートしています。I/O待ちの多い処理で効果的です。

```python
@app.get("/async-items/")
async def read_async_items():
    result = await some_async_function()
    return result
```

注意: 同期関数（defで定義）もFastAPIが自動的にスレッドプールで実行するため、混在可能です。

## ミドルウェア

CORSミドルウェアを追加することで、フロントエンドからのクロスオリジンリクエストを許可できます。

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## エラーハンドリング

HTTPExceptionを使ってエラーレスポンスを返します。

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```
