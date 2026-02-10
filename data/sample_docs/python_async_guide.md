# Python非同期処理ガイド

## 非同期処理とは

非同期処理は、I/O待ち（ネットワーク通信、ファイル読み書き等）の間に他のタスクを実行する手法です。Pythonでは`asyncio`モジュールとasync/await構文で実現します。

## 基本構文

### async/await

```python
import asyncio

async def fetch_data(url: str) -> str:
    """非同期でデータを取得する"""
    # awaitで非同期処理の完了を待つ
    # この間、他のタスクが実行可能
    await asyncio.sleep(1)  # I/O処理のシミュレーション
    return f"Data from {url}"

async def main():
    result = await fetch_data("https://example.com")
    print(result)

# イベントループの起動
asyncio.run(main())
```

### 並列実行

`asyncio.gather`を使うと、複数の非同期タスクを並列に実行できます。

```python
async def main():
    # 3つのリクエストを並列に実行
    results = await asyncio.gather(
        fetch_data("https://api1.com"),
        fetch_data("https://api2.com"),
        fetch_data("https://api3.com"),
    )
    # 全てのリクエストが完了するまで約1秒（直列なら3秒）
    print(results)
```

## httpxによる非同期HTTPリクエスト

```python
import httpx

async def fetch_api(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

## 非同期ジェネレータ

```python
async def count_up(n: int):
    for i in range(n):
        await asyncio.sleep(0.5)
        yield i

async def main():
    async for number in count_up(5):
        print(number)
```

## FastAPIでの非同期処理

FastAPIは非同期エンドポイントをネイティブにサポートしています。

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/data")
async def get_data():
    # 非同期でデータベースにアクセス
    data = await database.fetch_all()
    return data
```

注意: `def`で定義したエンドポイントは、FastAPIが自動的にスレッドプールで実行します。CPU集約的な処理には`def`を使い、I/O集約的な処理には`async def`を使うのが適切です。

## asyncioの注意点

### ブロッキング処理の回避

非同期コード内でブロッキングI/O（`time.sleep`、同期的なDB接続等）を使うと、イベントループ全体がブロックされます。

```python
# 悪い例
async def bad_example():
    import time
    time.sleep(5)  # イベントループをブロック!

# 良い例
async def good_example():
    await asyncio.sleep(5)  # イベントループをブロックしない
```

### タスクのキャンセル

```python
async def long_task():
    try:
        await asyncio.sleep(100)
    except asyncio.CancelledError:
        print("タスクがキャンセルされました")
        raise  # CancelledErrorは再raiseすること

task = asyncio.create_task(long_task())
await asyncio.sleep(1)
task.cancel()
```

## 同期処理との連携

非同期コードから同期関数を呼ぶ場合は、`run_in_executor`を使います。

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def sync_heavy_computation(n):
    """CPU集約的な同期関数"""
    return sum(range(n))

async def main():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        ThreadPoolExecutor(),
        sync_heavy_computation,
        10_000_000
    )
    print(result)
```
