import os
import json
from typing import List

from janome.tokenizer import Tokenizer as JanomeTokenizer
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

from app.schemas import Product,Knowledge

# BM25用の日本語トークナイザ（インスタンス化コストが高いためモジュールレベルで使い回す）
_janome_tokenizer = JanomeTokenizer()

def _japanese_preprocessing_func(text: str) -> List[str]:
    """
    BM25はデフォルトで英語向けの空白区切り(str.split)を使うため、
    スペースを含まない日本語文章では単語単位に分割できない。
    Janomeで形態素解析した表層形をトークンとして使うことで、日本語のキーワード一致を可能にする。
    """
    return [token.surface for token in _janome_tokenizer.tokenize(text)]

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

# 閾値を設定してRetrieverを作成する関数（ベクトル検索側）
def get_custom_retriever(db: Chroma, k: int, threshold: float):
    return db.as_retriever(
        # 類似度スコアでフィルタリングするモード
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": k,
            "score_threshold": threshold  # ここで閾値を設定
        }
    )

# Chromaコレクションに登録済みの全ドキュメントをDocument形式で取得する
# （BM25インデックスは検索のたびにこの結果から構築し、常にChromaの内容と同期させる）
def _load_all_documents(db: Chroma) -> List[Document]:
    raw = db.get(include=["documents", "metadatas"])
    return [
        Document(page_content=content, metadata=metadata or {})
        for content, metadata in zip(raw["documents"], raw["metadatas"])
    ]

# BM25（キーワード一致による検索）のRetrieverを作成する関数
def get_bm25_retriever(db: Chroma, k: int):
    documents = _load_all_documents(db)
    if not documents:
        return None
    retriever = BM25Retriever.from_documents(
        documents, preprocess_func=_japanese_preprocessing_func
    )
    retriever.k = k
    return retriever

# ベクトル検索(閾値フィルタあり)とBM25キーワード検索をRRFで統合したハイブリッドRetrieverを作成する関数
def get_hybrid_retriever(db: Chroma, k: int, threshold: float):
    vector_retriever = get_custom_retriever(db, k, threshold)
    bm25_retriever = get_bm25_retriever(db, k)

    # コレクションが空でBM25側の対象データが無い場合はベクトル検索のみを使う
    if bm25_retriever is None:
        return vector_retriever

    return EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.5, 0.5],
    )

# --- 検索用（両方から取得する関数） ---
def search_all_contexts(query: str, k_product: int = 3, k_knowledge: int = 3, threshold: float = 0.5):
    """
    ベクトル検索とBM25キーワード検索を組み合わせたハイブリッド検索を実行する。
    ベクトル検索側は閾値に満たない（似ていない）データを自動的に除外し、
    BM25側はキーワードの一致度で上位k件を取得したうえで、両者をRRF（Reciprocal Rank Fusion）で統合する。
    """

    # 1. 各DBからハイブリッドRetrieverを生成
    product_retriever = get_hybrid_retriever(product_db, k_product, threshold)
    knowledge_retriever = get_hybrid_retriever(knowledge_db, k_knowledge, threshold)

    # 2. 検索の実行 (invokeメソッドを使用)
    # EnsembleRetrieverは2つのRetrieverの結果を統合した件数を返すため、
    # 呼び出し側のk指定（推奨件数の上限など）を保つためにk件までに切り詰める
    product_results = product_retriever.invoke(query)[:k_product]
    knowledge_results = knowledge_retriever.invoke(query)[:k_knowledge]

    return {
        "products": product_results,
        "knowledge": knowledge_results
    }