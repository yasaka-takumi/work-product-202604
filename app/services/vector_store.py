from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

from typing import List
from app.schemas import Product
import json
import os

# 1. 埋め込み（テキストを数値にする）モデルの設定
embeddings = OllamaEmbeddings(model="mxbai-embed-large",
                              base_url="http://localhost:12000")

# 2. VectorDBの初期化（フォルダ名を指定して保存できるようにする）
vector_db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embeddings,
    collection_name="cat_products"
)

async def add_to_vector_db(products: List[Product]):
    documents = []
    for p in products:
        # 検索対象にするテキスト（名前と説明を合体させるのがコツ）
        content = f"商品名: {p.name}\n説明: {p.description}\n原材料: {p.ingredients}"
        
        # LangChainの形式に変換（メタデータにIDなどを入れる）
        doc = Document(
            page_content=content,
            metadata={
                "id": p.id,
                "price": p.price,
                "category_id": p.category_id,
                "image_url": p.image_url
            }
        )
        documents.append(doc)
    
    # ChromaDBに保存
    vector_db.add_documents(documents)
    
    log_file_path = "registered_products_log.jsonl"
    
    with open(log_file_path, mode="a", encoding="utf-8") as f:
        for p in products:
            # Pydanticモデルを辞書に変換して、1行のJSONとして書き出し
            line = json.dumps(p.model_dump(), ensure_ascii=False)
            f.write(line + "\n")

# 