from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str
    slug: str
    display_order: Optional[int] = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    display_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MenuItemBase(BaseModel):
    name: str
    category_id: int
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    photo_url: Optional[str] = None
    tags: Optional[str] = ""
    in_stock: Optional[bool] = True
    is_top_recipe: Optional[bool] = False
    is_chef_special: Optional[bool] = False


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    photo_url: Optional[str] = None
    tags: Optional[str] = None
    in_stock: Optional[bool] = None
    is_top_recipe: Optional[bool] = None
    is_chef_special: Optional[bool] = None


class MenuItemResponse(MenuItemBase):
    id: int
    created_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)
