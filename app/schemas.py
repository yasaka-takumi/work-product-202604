from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# 商品情報の定義
class Product(BaseModel):
    id: str
    product_name: str
    category_name: str 
    tag_name: Optional[str] = None
    description: str
    price: int
    image_url: Optional[str] = None
    ingredients: str
    
# 知識情報の定義
class Knowledge(BaseModel):
    title: str = Field(...,description="記事やトピックのタイトル")
    body: str = Field(...,description="知識の本文。RAGの検索対象となる中心部分")
    
    # メタデータをより具体的に定義
    category: Optional[str] = Field(None, description="例: 病気、食事、しつけ、雑学")
    source: Optional[str] = Field(None, description="引用元URLや書籍名")
    tags: List[str] = Field(default_factory=list, description="検索の足しにするキーワード群")
    species: Optional[str] = Field(None, description="猫の種類")
    
    # その他、自由に入れられる枠も残しておく
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_content_for_vector_db(self) -> str:
        """VectorDBに登録するための『検索用テキスト』を生成するメソッド"""
        # タイトルと本文を合体させ、さらにタグも含めることで検索にヒットしやすくする
        tag_str = ", ".join(self.tags)
        return f"タイトル: {self.title}\nカテゴリー: {self.category}\n内容: {self.body}\nキーワード: {tag_str}"
    

# request (Client -> FastAPI)
class ChatRequest(BaseModel):
    user_id : str
    session_id : str
    message : str = Field(
        ...,
        examples=["こんにちは"],
        description="promptが入ります"
    )
    external_data : Optional[Dict[str, Any]] = Field(default_factory=dict)
    
"""
まだ、contextの中身が決まってなくて後で追加するときの書き方
    context : Optional[Dict[str, Any]] = Field(default_factory=dict)
"""

class SimpleProducts(BaseModel):
    id : str
    image_url : str
    
# response (FastAPI -> Client)
class ChatResponse(BaseModel):
    answer : str
    recommended_products : List[SimpleProducts]
    

