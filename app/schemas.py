from pydantic import BaseModel, Field, conint
from typing import Optional, List
import datetime

# --- Tray Schemas ---

class TrayBase(BaseModel):
    tray_id: str = Field(..., description="Unique identifier for the tray (e.g., AGV1, TS01).")
    description: Optional[str] = Field(None, description="Brief description of the tray.")
    max_slots: conint(gt=0) = Field(..., description="Total number of material location slots on this tray (must be > 0).")

class TrayCreate(TrayBase):
    pass

class TrayUpdate(BaseModel):
    description: Optional[str] = Field(None, description="Updated description for the tray.")
    # max_slots could be updatable, but this has implications if slots are already populated.
    # For now, let's assume max_slots is defined at creation and not easily changed post-population.
    # If it needs to be updatable, careful consideration of existing MaterialLocation records is needed.
    # max_slots: Optional[conint(gt=0)] = Field(None, description="Updated maximum slots. Careful if decreasing!")

class TrayInDBBase(TrayBase):
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True # Pydantic V2 uses from_attributes instead of orm_mode

class Tray(TrayInDBBase): # Tray schema for API responses
    pass


# --- MaterialLocation Schemas ---

class MaterialLocationBase(BaseModel):
    tray_id: str = Field(..., description="Identifier of the tray this slot belongs to.")
    slot_index: conint(ge=1) = Field(..., description="Specific index or position of this slot on the tray (must be >= 1).")
    item_id: Optional[str] = Field(None, description="ID of the material/sample. Empty or NULL if slot is available. Special value if disabled.")
    process_info: Optional[str] = Field(None, description="Optional: Information about the last operation or process.")

class MaterialLocationCreate(MaterialLocationBase):
    # item_id is explicitly part of base, can be None for creating an empty slot record
    pass

class MaterialLocationUpdate(BaseModel): # For updating an existing MaterialLocation record (identified by its PK 'id' or by tray_id/slot_index)
    item_id: Optional[str] = Field(None, description="Updated ID of the material/sample. Use empty string to clear.")
    process_info: Optional[str] = Field(None, description="Updated optional process information.")
    # tray_id and slot_index are typically not updatable for an existing location record,
    # as they form its composite identity. To "move" an item, you'd clear one and set another.

class MaterialLocationInDBBase(MaterialLocationBase):
    id: int # The unique PK of the MaterialLocation record
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

class MaterialLocation(MaterialLocationInDBBase): # MaterialLocation schema for API responses
    pass


# --- Schemas for specific complex operations ---

# For batch updating items within various locations (identified by MaterialLocation PK 'id')
class MaterialLocationBulkUpdateItem(BaseModel):
    id: int # PK of the MaterialLocation record to update
    item_id: Optional[str] = Field(None, description="New item ID for this specific location.")
    process_info: Optional[str] = Field(None, description="New process info for this specific location.")
    # tray_id and slot_index are not included here as they identify the slot, not what's being changed.

# For initializing all slots for a tray (used by a potential CRUD/service function)
class TraySlotInit(BaseModel):
    tray_id: str
    max_slots: int # To confirm against the tray's actual max_slots
    default_item_id: Optional[str] = "" # Default item_id for new slots (e.g., empty)

# For placing an item into a specific tray and slot
class PlaceItemRequest(BaseModel):
    item_id: str = Field(..., description="The ID of the item to place.")
    # tray_id and slot_index will likely be path parameters in the API endpoint
    process_info: Optional[str] = Field(None, description="Optional process information for this placement.")


# For API response when returning a Tray with its locations
class TrayWithLocations(Tray):
    material_locations: List[MaterialLocation] = []
