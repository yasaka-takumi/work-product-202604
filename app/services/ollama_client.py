import os
import json

import httpx

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:12000")

async def ask_ollama(prompt: str, system_prompt: str):
    url = f"{OLLAMA_URL}/api/generate" # OllamaのURL
    payload = {
        "model": "qwen2.5:3b", # dsasai/llama3-elyza-jp-8b:latest
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options":{
            "temparature":0.0,
            "top_p": 0.9,
            "num_predict":300
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=None)
        return response.json().get("response")
    
# pythonの辞書におけるget methodは辞書に指定のkeyがあればvalueをとってくるが、なければNoneを返す
# .get("key", "予備のvalue")であれば、keyがなければ、予備のvalueを渡す




# streaming実装
async def ask_ollama_streaming(message: str, system_prompt: str, history: list=None):
    """Ollamaからストリーミング形式で回答を受け取るジェネレーター"""
    url = f"{OLLAMA_URL}/api/chat"  # OllamaのURL
    
    
    # 履歴がない場合は、空リスト
    if history is None :
        history = []
    
    # メッセージの組み立て
    # 常に [Systemプロンプト] -> [過去のやり取り] -> [今回の質問] の順にする
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)  # 過去の user/assistant のやり取りを追加
    messages.append({"role": "user", "content": message}) # 今回の入力を最後に追加
    
    
    
    payload = {
        "model": "qwen2.5:3b", # dsasai/llama3-elyza-jp-8b:latest
        "messages": messages,
        "stream": True,  # ストリーミングを有効化
        "options": {
            "temperature": 0.3, # 決定論的な回答を優先
            "num_predict":300
        }
    }

    # タイムアウトを無効にしてストリーミング接続を開始
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=payload) as response:
            # 不完全なJSONを保持するためのバッファ
            buffer = ""
            async for chunk in response.aiter_text(): # text単位で受け取る
                if not chunk:
                    continue
                
                buffer += chunk
                # 改行が含まれているか確認
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        chunk_data = json.loads(line)
                        content = chunk_data.get("message", {}).get("content", "")
                        if content:
                            # デバッグ用：ここで確実に生成されているか確認
                            # print(f"yield: {content}", end="", flush=True) 
                            yield content
                        
                        if chunk_data.get("done"):
                            return
                    except json.JSONDecodeError:
                        # 不完全な行は次のchunkを待つ
                        continue

"""
terminal上でstreamの確認code
docsからstream機能は確認できないため
curl -s -N -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test",
       "session_id": "test",
       "message": "こんにちは！簡単な自己紹介をして",
       "external_data": {}
     }'
"""

"""
httpx.AsyncClientとは何か
一言でいうと、「Webブラウザを立ち上げっぱなしにする」ようなイメージのオブジェクト

通常、requets.get()などを個別に使うと、リクエストのたびに「接続を開いて、閉じる」という作業が発生する。
これに対し、AsyncClient以下のようなメリットがある。

- コネクションプール（再利用）: 一度確立した接続（TCPコネクション）を使い回すため、リクエストが高速化します。

- 非同期対応: await を使って、リクエストの待ち時間に他の処理（別のユーザーの対応など）を並行して行うことができます。

- Cookieや共通設定の維持: ログイン情報やタイムアウト設定などを全リクエストで共通化できます。

ストリーミングの機能の実装において、「接続を維持し続ける必要がある」ため不可欠である。

"""
