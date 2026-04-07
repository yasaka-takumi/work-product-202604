from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# 商品情報の定義
class Product(BaseModel):
    id: str
    category_id: str
    name: str
    description: str
    price: int = Field(ge=0)
    image_url: str
    ingredients: str

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
    
# response (FastAPI -> Client)
class ChatResponse(BaseModel):
    answer : str
    recommended_products : List[Product]
    

