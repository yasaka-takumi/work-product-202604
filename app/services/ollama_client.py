import httpx
import json

async def ask_ollama(prompt: str, system_prompt: str):
    url = "http://localhost:12000/api/generate" # OllamaのURL
    payload = {
        "model": "qwen2.5:3b", # ここでモデルを指定
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

"""
        async with client.stream("POST", url, json=payload, timeout=None) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    yield data.get("response", "") # 1文字ずつ（あるいは数文字ずつ）外へ出す
                    if data.get("done"):
                        break
"""

"""
stream : False の時のコード        
        response = await client.post(url, json=payload, timeout=60.0)
        return response.json().get("response")
"""
    
# pythonの辞書におけるget methodは辞書に指定のkeyがあればvalueをとってくるが、なければNoneを返す
# .get("key", "予備のvalue")であれば、keyがなければ、予備のvalueを渡す

#