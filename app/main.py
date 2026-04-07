from fastapi import FastAPI,status
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ChatRequest, ChatResponse,Product
from app.services.ollama_client import ask_ollama

from app.services.vector_store import add_to_vector_db

from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 本番ではフロントのURLに絞りますが、開発中は "*" でOK
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/admin/products",status_code=status.HTTP_201_CREATED)
async def add_products(products: List[Product]):
    """process of registering products in VectorDB"""
    await add_to_vector_db(products)
    return {"message":f"{len(products)}件の商品を登録しました"}

@app.post("/chat", response_model=ChatResponse) # returnの時のresponseのschema構造が定義した構造に沿っているかをcheckしてくれる
async def chat_endpoint(request: ChatRequest):
    """process of chat with AI"""    
    user_name = request.external_data.get("user_nickname","飼い主")
    cat_name = request.external_data.get("cat_name","猫ちゃん")
    
    system_prompt = (f"あなたは猫専門の獣医師です。{user_name}さんの愛猫の名前は{cat_name}です。"
                     f"体調に合わせたアドバイスをしてください")
    answer = await ask_ollama(request.message, system_prompt)
    
    # 4. レスポンスを組み立てて返す
    return ChatResponse(
        answer=answer,
        recommended_products=[], # 今は商品を登録してないため空
    )

"""
stream前のcode
@app.post("/chat", response_model=ChatResponse) # returnの時のresponseのschema構造が定義した構造に沿っているかをcheckしてくれる



実務想定の構造
my-cat-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIの起動・エントリーポイント
│   ├── schemas.py           # JSONの定義（Pydanticモデル）
│   ├── services/            # ロジック（Ollama通信やRAG）
│   │   ├── __init__.py
│   │   ├── ollama_client.py # Ollamaとの通信担当
│   │   └── rag_engine.py    # VectorDBや検索担当（後で作成）
│   └── database/            # 履歴保存などのDB関連
│       └── history_db.py
├── data/                    # RAG用の商品データ（JSON/CSVなど）
├── .env                     # 環境変数（OllamaのURLなど）
├── requirements.txt         # 必要なライブラリ
└── README.md
"""
