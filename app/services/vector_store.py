import os
import json
from typing import List

from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

from app.schemas import Product,Knowledge

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:12000")

# 1. 埋め込み（テキストを数値にする）モデルの設定
embeddings = OllamaEmbeddings(model="mxbai-embed-large",
                              base_url=OLLAMA_URL)

# 2. VectorDBの初期化（フォルダ名を指定して保存できるようにする）
# 商品用のコレクション
product_db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embeddings,
    collection_name="cat_products"
)

# 知識用のコレクション
knowledge_db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embeddings,
    collection_name="cat_knowledge"
)

# 商品データ登録用
async def add_to_product_db(products: List[Product]):
    documents = []
    for p in products:
        # 検索対象にするテキスト（名前と説明を合体させるのがコツ）
        content = f"商品名: {p.product_name}\n説明: {p.description}\n原材料: {p.ingredients}"
        
        # LangChainの形式に変換（メタデータにIDなどを入れる）
        doc = Document(
            page_content=content,
            metadata={
                "id": p.id,
                "price": p.price,
                "category_id": p.category_name,
                "image_url": p.image_url,
                "type":"product" # メタデータで種類を示しておく
            }
        )
        documents.append(doc)
    
    # ChromaDBに保存
    product_db.add_documents(documents)
    
    log_file_path = "registered_products_log.jsonl"
    
    with open(log_file_path, mode="a", encoding="utf-8") as f:
        for p in products:
            # Pydanticモデルを辞書に変換して、1行のJSONとして書き出し
            line = json.dumps(p.model_dump(), ensure_ascii=False)
            f.write(line + "\n")

# 知識データ登録用 
async def add_knowledge_to_db(knowledge_list: List[Knowledge]):
    documents = []
    for item in knowledge_list:
        doc = Document(
            page_content=item.to_content_for_vector_db(), # 結合したテキストを使用
            metadata={
                "title": item.title,
                "category": item.category,
                "source": item.source,
                "type": "knowledge",
                **item.metadata # 残りの自由枠を展開
            }
        )
        documents.append(doc)
    
    knowledge_db.add_documents(documents)

# 閾値を設定してRetrieverを作成する関数
def get_custom_retriever(db: Chroma, k: int, threshold: float):
    return db.as_retriever(
        # 類似度スコアでフィルタリングするモード
        search_type="similarity_score_threshold", 
        search_kwargs={
            "k": k, 
            "score_threshold": threshold  # ここで閾値を設定
        }
    )

# --- 検索用（両方から取得する関数） ---
def search_all_contexts(query: str, k_product: int = 3, k_knowledge: int = 3, threshold: float = 0.5):
    """
    Retrieverを使用して検索を実行する。
    閾値に満たない（似ていない）データは自動的に除外される。
    """
    
    # 1. 各DBからRetrieverを生成
    product_retriever = get_custom_retriever(product_db, k_product, threshold)
    knowledge_retriever = get_custom_retriever(knowledge_db, k_knowledge, threshold)
    
    # 2. 検索の実行 (invokeメソッドを使用)
    # 閾値以下の場合は空のリスト [] が返る
    product_results = product_retriever.invoke(query)
    knowledge_results = knowledge_retriever.invoke(query)
    
    return {
        "products": product_results,
        "knowledge": knowledge_results
    }