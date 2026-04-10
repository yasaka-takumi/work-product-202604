import httpx
import json

async def ask_ollama(prompt: str, system_prompt: str):
    url = "http://localhost:12000/api/generate" # OllamaのURL
    payload = {
        "model": "qwen2.5:3b",
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
async def ask_ollama_streaming(message: str, system_prompt: str):
    """Ollamaからストリーミング形式で回答を受け取るジェネレーター"""
    url = "http://localhost:12000/api/chat"  # OllamaのURL
    
    payload = {
        "model": "dsasai/llama3-elyza-jp-8b:latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "stream": True,  # ストリーミングを有効化
        "options": {
            "temperature": 0.0, # 決定論的な回答を優先
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