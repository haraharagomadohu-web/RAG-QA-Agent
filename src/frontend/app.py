"""Streamlit チャットUI

RAGエージェントのフロントエンド。
FastAPIバックエンド（localhost:8000）にHTTPリクエストを送り、
チャット形式で質問応答を行う。

起動方法:
    streamlit run src/frontend/app.py
"""

import requests
import streamlit as st

# === バックエンドAPIのURL ===
# FastAPIサーバーのベースURL。バックエンドとフロントエンドは別プロセスで動作する
API_BASE_URL = "http://localhost:8000/api"


# === ページ設定 ===
# set_page_config はStreamlitスクリプトの最初に呼ぶ必要がある
# （他のStreamlitコマンドより前に実行しないとエラーになる）
st.set_page_config(
    page_title="技術文書QA RAGエージェント",
    page_icon="📚",
    layout="centered",
)

st.title("📚 技術文書QA RAGエージェント")
st.caption("LangChain + LangGraph + Ollama によるRAG質問応答システム")


# === サイドバー: システム状態の表示 ===
with st.sidebar:
    st.header("システム状態")

    # ヘルスチェックAPIを呼んでバックエンドの状態を表示する
    # バックエンドが起動していない場合はエラーメッセージを表示
    if st.button("状態を確認"):
        try:
            resp = requests.get(f"{API_BASE_URL}/health", timeout=5)
            data = resp.json()
            # 全体のステータスに応じて色を変える
            if data["status"] == "healthy":
                st.success(f"ステータス: {data['status']}")
            else:
                st.error(f"ステータス: {data['status']}")
            st.write(f"Ollama: {data['ollama_status']}")
            st.write(f"ベクトルDB: {data['vectorstore_status']}")
        except requests.ConnectionError:
            st.error("バックエンドに接続できません。FastAPIサーバーを起動してください。")
        except Exception as e:
            st.error(f"エラー: {e}")

    st.divider()
    st.markdown(
        "**使い方**: 下の入力欄に技術的な質問を入力してください。"
        "投入済みの技術文書から回答を生成します。"
    )


# === セッション状態の初期化 ===
# Streamlitはユーザー操作のたびにスクリプト全体を再実行する。
# st.session_state を使うことで、再実行をまたいでデータを保持できる。
# ここではチャットのメッセージ履歴を保存する。
if "messages" not in st.session_state:
    st.session_state.messages = []


# === チャット履歴の表示 ===
# session_stateに保存された過去のメッセージを順番に描画する。
# roleが "user" ならユーザーアイコン、"assistant" ならAIアイコンで表示される。
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # アシスタントの回答には出典・評価情報が付属している場合がある
        if message["role"] == "assistant" and "metadata" in message:
            _render_metadata(message["metadata"])


def _render_metadata(metadata: dict) -> None:
    """回答のメタデータ（出典・評価情報）を折りたたみで表示する

    Args:
        metadata: sources, is_sufficient, iterations を含む辞書
    """
    # 出典情報の表示
    sources = metadata.get("sources", [])
    if sources:
        with st.expander(f"📄 出典 ({len(sources)}件)"):
            for src in sources:
                st.markdown(f"**{src['source']}**")
                st.caption(src["content"])

    # 評価情報の表示（エージェントが回答を十分と判断したか）
    cols = st.columns(2)
    with cols[0]:
        if metadata.get("is_sufficient"):
            st.success("✅ 十分な回答")
        else:
            st.warning("⚠️ 情報が不十分な可能性")
    with cols[1]:
        st.metric("検索回数", f"{metadata.get('iterations', 0)}回")


# === ユーザー入力の受付 ===
# st.chat_input はページ下部に固定される入力欄を表示する。
# ユーザーがEnterを押すと、入力内容が返される（Noneでない場合に処理を実行）。
if prompt := st.chat_input("技術的な質問を入力してください"):

    # --- ユーザーメッセージの表示と保存 ---
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- バックエンドAPIの呼び出し ---
    with st.chat_message("assistant"):
        # st.spinner で処理中であることをユーザーに伝える
        # Ollamaでの推論は時間がかかるため、ローディング表示が重要
        with st.spinner("回答を生成中..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/query",
                    json={"question": prompt},
                    # Ollamaの推論時間を考慮して長めのタイムアウトを設定
                    # 自己評価ループで最大3回反復するため、余裕を持たせる
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()

                # 回答本文を表示
                answer = data.get("answer", "回答を取得できませんでした。")
                st.markdown(answer)

                # メタデータ（出典・評価情報）を表示
                metadata = {
                    "sources": data.get("sources", []),
                    "is_sufficient": data.get("is_sufficient", False),
                    "iterations": data.get("iterations", 0),
                }
                _render_metadata(metadata)

                # セッション状態に保存（次回の再描画時に履歴として表示される）
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "metadata": metadata,
                })

            except requests.ConnectionError:
                error_msg = "バックエンドに接続できません。FastAPIサーバーを起動してください。"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })
            except requests.Timeout:
                error_msg = "回答の生成がタイムアウトしました。もう一度お試しください。"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })
            except Exception as e:
                error_msg = f"エラーが発生しました: {e}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })
