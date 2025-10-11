from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# === 数据模型 ===
class Relationship(BaseModel):
    name: str
    relation: str
    status: str

class InventoryItem(BaseModel):
    item_name: str
    description: str

class Protagonist(BaseModel):
    name: str
    age: int
    level: str
    status: str
    personality: str
    abilities: List[str]
    goal: str

class ChapterState(BaseModel):
    chapter_index: int
    protagonist: Protagonist
    inventory: List[InventoryItem]
    relationships: List[Relationship]
    current_plot_summary: str