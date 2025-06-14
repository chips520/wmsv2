from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class MaterialLocationBase(BaseModel):
    item_id: str = Field(..., description="ID of the material. Empty if no material, '-99' or '-1' if disabled.")
    tray_id: str = Field(..., description="Corresponding tray number.")
    process_info: Optional[str] = Field(None, description="Optional: Information about the process or task ID.")

class MaterialLocationCreate(MaterialLocationBase):
    pass

class MaterialLocationUpdate(BaseModel):
    item_id: Optional[str] = Field(None, description="ID of the material.")
    tray_id: Optional[str] = Field(None, description="Corresponding tray number.")
    process_info: Optional[str] = Field(None, description="Optional: Information about the process or task ID.")

class MaterialLocationInDB(MaterialLocationBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True # Replaces orm_mode in Pydantic v2

class MaterialLocationBulkUpdateItem(BaseModel):
    id: int
    item_id: Optional[str] = None
    tray_id: Optional[str] = None
    process_info: Optional[str] = None
