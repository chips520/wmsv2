from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class MaterialLocationBase(BaseModel):
    material_id: Optional[str] = None
    tray_number: str
    process_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str = 'empty'

class MaterialLocationCreate(MaterialLocationBase):
    pass

class MaterialLocationUpdate(BaseModel):
    material_id: Optional[str] = None
    tray_number: Optional[str] = None
    process_id: Optional[str] = None
    task_id: Optional[str] = None
    status: Optional[str] = None

class MaterialLocation(MaterialLocationBase):
    id: int
    timestamp: datetime

    class Config:
        from_orm = True
