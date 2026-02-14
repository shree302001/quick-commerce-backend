from typing import Optional, List
from app.schemas.base import BaseSchema


class CategoryResponse(BaseSchema):
    id: int
    name: str
    parent_id: Optional[int] = None


class ProductBase(BaseSchema):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    sku: str
    name: str
    price: float


class ProductUpdate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    category: Optional[CategoryResponse] = None


class ProductListResponse(BaseSchema):
    items: List[ProductResponse]
    total: int
    skip: int
    limit: int
