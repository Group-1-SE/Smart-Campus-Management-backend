from pydantic import BaseModel
from typing import Optional, Dict, Any

class Record(BaseModel):
    data: Dict[str, Any]

class Filter(BaseModel):
    filters: Optional[Dict[str, Any]] = None

class UpdateRequest(BaseModel):
    filters: Dict[str, Any]
    updates: Dict[str, Any]