from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime

class HistoryRecord(BaseModel):
    id: int = None
    type: str
    input_text: str
    output_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)