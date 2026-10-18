from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class SiteContentBase(BaseModel):
    key: str
    value: str
    category: Optional[str] = "general"
    description: Optional[str] = None


class SiteContentCreate(SiteContentBase):
    pass


class SiteContentUpdate(BaseModel):
    value: str
    description: Optional[str] = None


class SiteContentResponse(SiteContentBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SiteContentBulkUpdate(BaseModel):
    contents: Dict[str, str]  # key: value map for instant batch updates
