from fastapi import FastAPI,status
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ChatRequest, ChatResponse,Product,Knowledge
from app.services.ollama_client import ask_ollama,ask_ollama_streaming

from app.services.vector_store import add_to_product_db,add_knowledge_to_db, search_all_contexts, get_custom_retriever

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
    await add_to_product_db(products)
    return {"message":f"{len(products)}件の商品を登録しました"}

@app.post("/admin/knowledge", status_code=status.HTTP_201_CREATED)
async def add_knowlege(knowledge: List[Knowledge]):
    """process of registering knowledge in VectorDB"""
    await add_knowledge_to_db(knowledge)
    return {"message":f"{len(knowledge)}件の商品を登録しました"}



import json
from fastapi.responses import StreamingResponse
from typing import Dict, List

# --- メモリ保持用の変数を定義 (サーバー起動中のみ有効) ---
# 構造: { "session_id": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}] }
chat_memory: Dict[str, List[dict]] = {}

@app.post("/chat", responses={200: {"description": "streaming text and recommend product data"}})
async def chat_endpoint(request: ChatRequest):
    """process of chat with AI"""    
    user_name = request.external_data.get("user_nickname","飼い主")
    cat_name = request.external_data.get("cat_name","猫ちゃん")
    session_id = request.session_id 
    
    # --- このセッションの過去ログを取得 ---
    # 存在しない場合は空リスト。直近10件（5往復）程度に絞っておくと動作が安定します
    history = chat_memory.get(session_id, [])
    
# --- RAG: 両方のCollectionから情報を取得 ---
    # 検索関数を実行（k数は必要に応じて調整）
    retrieved_data = search_all_contexts(request.message, k_product=2, k_knowledge=3,threshold=0.6)
    
    # 取得した情報をテキストに整形
    knowledge_text = "\n".join([doc.page_content for doc in retrieved_data["knowledge"]])
    product_info = "\n".join([doc.page_content for doc in retrieved_data["products"]])

        # システムプロンプトの構築（FT済みの性格を補強）
    system_prompt = (
        f"あなたは猫に関して専門的な知識を持っている、聞き上手なコンシェルジュです。\n"
        f"【飼い主さんの名前,愛猫の名前】 : 【{user_name}さん, {cat_name}ちゃん】"
        f"以下の【専門知識】を参考に、寄り添うアドバイスをしてください。\n"
        f"【専門知識】:\n{knowledge_text}\n\n"
        f"※商品情報はユーザーから『おすすめは？』など具体的な要望があった時のみ紹介してください。"
        f"【商品情報】:\n{product_info}"
    )
    
    # 推奨商品のリスト作成（メタデータからIDなどを抽出）
    recommended = [
        {"id": doc.metadata["id"], "image_url":doc.metadata["image_url"]} 
        for doc in retrieved_data["products"]
    ]

    # 内部ジェネレーター関数
    async def stream_generator():
        # --- 生成された全回答を保持する変数 ---
        full_answer = ""
        # AIの回答をストリーミング
        has_answer = False # デバッグ用：回答が届いたかチェック
        
        async for chunk in ask_ollama_streaming(request.message, system_prompt, history):
            if chunk:
                has_answer = True
                full_answer += chunk # 履歴保存のために回答を繋げる
                yield chunk

    # 回答が空だった場合のデバッグ表示（ターミナル等で見える）
        if not has_answer:
            yield "AIの回答が空です。Ollamaの設定を確認してください。"

        # 2. 回答が終わったら、特殊な区切り文字を送信
        yield "---PRODUCTS---"

        # 3. 推奨商品のデータをJSON文字列として送信
        # ユーザーが「おすすめ」を求めている場合のみデータを送るロジック
        if "おすすめ" in request.message or "商品" in request.message:
            yield json.dumps(recommended, ensure_ascii=False)
        else:
            yield json.dumps([], ensure_ascii=False)
        
        # --- 会話が終わったら履歴を更新 ---
        # ユーザーの発言と、AIが今回生成した回答をセットで保存
        if has_answer:
            history.append({"role": "user", "content": request.message})
            history.append({"role": "assistant", "content": full_answer})
            
            # メモリ節約と精度維持のため、直近10メッセージ分を保持して更新
            chat_memory[session_id] = history[-10:]

    # text/plain または text/event-stream で送信
    return StreamingResponse(stream_generator(), media_type="text/plain")









# stream = Falseでの実装コード↓

@app.post("/chat/not_stream", response_model=ChatResponse) # returnの時のresponseのschema構造が定義した構造に沿っているかをcheckしてくれる
async def chat_endpoint(request: ChatRequest):
    """process of chat with AI"""    
    user_name = request.external_data.get("user_nickname","飼い主")
    cat_name = request.external_data.get("cat_name","猫ちゃん")
    
# --- RAG: 両方のCollectionから情報を取得 ---
    # 検索関数を実行（k数は必要に応じて調整）
    retrieved_data = search_all_contexts(request.message, k_product=2, k_knowledge=3,threshold=0.6)
    
    # 取得した情報をテキストに整形
    knowledge_text = "\n".join([doc.page_content for doc in retrieved_data["knowledge"]])
    product_info = "\n".join([doc.page_content for doc in retrieved_data["products"]])
    
    """
    取得情報のイメージ(keyはcollection name)
    {
    "products": [
        Document(page_content="商品名: 腎臓サポート...", metadata={"id": "p1", "price": 1200, ...}),
        Document(page_content="商品名: 無添加おやつ...", metadata={"id": "p2", "price": 800, ...})
    ],
    "knowledge": [
        Document(page_content="項目: 腎不全のサイン...", metadata={"source": "medical_book", ...}),
        Document(page_content="項目: 水を飲ませるコツ...", metadata={"source": "blog", ...})
    ]
}
    """
    
    # システムプロンプトの構築（FT済みの性格を補強）
    system_prompt = (
        f"あなたは猫に関して専門的な知識を持っている、聞き上手な人です。\n"
        f"【飼い主さんの名前,愛猫の名前】 : 【{user_name}さん, {cat_name}ちゃん】"
        f"アドバイスを求められたら、以下の【専門知識】を参考に、寄り添うアドバイスをしてください。\n"
        f"【専門知識】:{knowledge_text}\n\n"
        f"※商品情報はユーザーから『おすすめは？』など具体的な要望があった時のみ、上記【商品情報】から選んで紹介してください。\n\n"
        f"【商品情報】:{product_info}\n"
        f"- 商品を紹介する際は、最大で {len(retrieved_data['products'])} 件（提供された情報の数）までに絞ってください。"
    )
# Ollamaに問い合わせ（必要に応じて product_info もプロンプトに含める）
    answer = await ask_ollama(request.message, system_prompt)   #  context_products=product_info
    
    # 推奨商品のリスト作成（メタデータからIDなどを抽出）
    recommended = [
        {"id": doc.metadata["id"], "image_url":doc.metadata["image_url"]} 
        for doc in retrieved_data["products"]
    ]

    return ChatResponse(
        answer=answer,
        recommended_products=recommended if "おすすめ" in request.message else [], 
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
