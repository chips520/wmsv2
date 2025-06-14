from fastapi import FastAPI, Depends, HTTPException, Body, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from . import crud, models, schemas # models needed for init_db if models are not imported elsewhere before init_db
from .database import SessionLocal, engine, init_db

try:
    init_db()
except Exception as e:
    print(f"Error initializing DB during app startup: {e}")

app = FastAPI(
    title="WMS API - Warehouse Management System",
    version="0.2.0",
    description="API for managing trays and material locations within a warehouse.",
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Tray Endpoints ---

@app.post("/trays/", response_model=schemas.Tray, status_code=201, summary="Create a new tray", tags=["Trays"])
def create_new_tray(tray: schemas.TrayCreate, db: Session = Depends(get_db)):
    # Creates a new tray. Slots are auto-initialized.
    try:
        db_tray = crud.create_tray(db=db, tray=tray)
        return db_tray
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/trays/", response_model=List[schemas.Tray], summary="List all trays", tags=["Trays"])
def read_all_trays(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Retrieves a list of all trays.
    return crud.get_trays(db, skip=skip, limit=limit)

@app.get("/trays/{tray_id}/", response_model=schemas.TrayWithLocations, summary="Get a specific tray and its locations", tags=["Trays"])
def read_single_tray(tray_id: str = Path(..., description="The ID of the tray to retrieve"), db: Session = Depends(get_db)):
    # Retrieves details for a specific tray and all its material locations.
    db_tray = crud.get_tray(db, tray_id=tray_id)
    if db_tray is None:
        raise HTTPException(status_code=404, detail=f"Tray '{tray_id}' not found")
    locations = crud.get_material_locations_by_tray(db, tray_id=tray_id, limit=None)
    tray_with_locations = schemas.TrayWithLocations.model_validate(db_tray) # Use model_validate for Pydantic V2
    tray_with_locations.material_locations = locations
    return tray_with_locations

@app.post("/trays/{tray_id}/update/", response_model=schemas.Tray, summary="Update tray details", tags=["Trays"])
def update_existing_tray(
    tray_id: str = Path(..., description="The ID of the tray to update"),
    tray_update: schemas.TrayUpdate = Body(...),
    db: Session = Depends(get_db)
):
    # Updates a tray's description.
    db_tray = crud.update_tray(db, tray_id=tray_id, tray_update=tray_update)
    if db_tray is None:
        raise HTTPException(status_code=404, detail=f"Tray '{tray_id}' not found for updating")
    return db_tray

@app.post("/trays/{tray_id}/delete/", response_model=schemas.Tray, summary="Delete a tray", tags=["Trays"])
def delete_existing_tray(tray_id: str = Path(..., description="The ID of the tray to delete"), db: Session = Depends(get_db)):
    # Deletes a tray and all its associated material locations.
    db_tray = crud.delete_tray(db, tray_id=tray_id)
    if db_tray is None:
        raise HTTPException(status_code=404, detail=f"Tray '{tray_id}' not found for deletion")
    return db_tray

@app.post("/trays/{tray_id}/initialize_slots/", status_code=200, summary="Initialize/Re-initialize slots for a tray", tags=["Trays"])
def initialize_tray_slots(
    tray_id: str = Path(..., description="The ID of the tray for which to initialize slots"),
    db: Session = Depends(get_db)
):
    # Ensures all slots for a given tray are created as empty.
    db_tray = crud.get_tray(db, tray_id=tray_id)
    if db_tray is None:
        raise HTTPException(status_code=404, detail=f"Tray '{tray_id}' not found")
    try:
        count = crud.initialize_slots_for_tray(db, tray_id=db_tray.tray_id, max_slots=db_tray.max_slots)
        return {"message": f"Slot initialization complete for tray '{tray_id}'. {count} new slots created."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- MaterialLocation Endpoints (Tray-Centric) ---

@app.get("/trays/{tray_id}/locations/", response_model=List[schemas.MaterialLocation], summary="List all locations (slots) for a tray", tags=["Material Locations"])
def read_locations_for_tray(
    tray_id: str = Path(..., description="The ID of the tray"),
    skip: int = 0, limit: int = Query(100, description="Number of locations to return, 0 for no limit."),
    db: Session = Depends(get_db)
):
    # Retrieves all material location slots for a specific tray.
    if not crud.get_tray(db, tray_id):
        raise HTTPException(status_code=404, detail=f"Tray '{tray_id}' not found.")
    effective_limit = None if limit == 0 else limit
    locations = crud.get_material_locations_by_tray(db, tray_id=tray_id, skip=skip, limit=effective_limit)
    return locations

@app.get("/trays/{tray_id}/locations/{slot_index}/", response_model=schemas.MaterialLocation, summary="Get a specific slot on a tray", tags=["Material Locations"])
def read_specific_slot(
    tray_id: str = Path(..., description="Tray ID"),
    slot_index: int = Path(..., description="Slot index on the tray", ge=1),
    db: Session = Depends(get_db)
):
    # Retrieves details of a specific slot on a specific tray.
    location = crud.get_material_location_by_tray_and_slot(db, tray_id=tray_id, slot_index=slot_index)
    if location is None:
        raise HTTPException(status_code=404, detail=f"Slot {slot_index} on tray '{tray_id}' not found.")
    return location

@app.post("/trays/{tray_id}/locations/{slot_index}/item/", response_model=schemas.MaterialLocation, summary="Place or update an item in a specific slot", tags=["Material Locations"])
def place_or_update_item_in_slot(
    tray_id: str = Path(..., description="Tray ID"),
    slot_index: int = Path(..., description="Slot index on the tray", ge=1),
    item_request: schemas.PlaceItemRequest = Body(...),
    allow_overwrite: bool = Query(False, description="Allow overwriting an existing item in the slot."),
    db: Session = Depends(get_db)
):
    # Places an item into a specific slot on a tray.
    try:
        location = crud.place_item_in_slot(
            db, tray_id=tray_id, slot_index=slot_index,
            item_id=item_request.item_id, process_info=item_request.process_info,
            allow_overwrite=allow_overwrite
        )
        return location
    except ValueError as e:
        if "occupied" in str(e).lower() and not allow_overwrite:
            raise HTTPException(status_code=409, detail=str(e))
        if "not found" in str(e).lower() or "out of range" in str(e).lower() or "does not exist" in str(e).lower(): # Added "does not exist"
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/trays/{tray_id}/locations/{slot_index}/clear/", response_model=schemas.MaterialLocation, summary="Clear an item from a slot", tags=["Material Locations"])
def clear_item_from_a_slot(
    tray_id: str = Path(..., description="Tray ID"),
    slot_index: int = Path(..., description="Slot index on the tray", ge=1),
    set_item_id_to: str = Query("", description="Value for item_id when clearing (e.g. empty, 'DISABLED')."),
    db: Session = Depends(get_db)
):
    # Sets the item_id of a specific slot to empty or another value.
    db_location = crud.get_material_location_by_tray_and_slot(db, tray_id, slot_index)
    if not db_location:
        raise HTTPException(status_code=404, detail=f"Slot {slot_index} on tray '{tray_id}' not found for clearing.")

    try:
        updated_location = crud.clear_item_from_slot(db, tray_id=tray_id, slot_index=slot_index, new_item_id_value=set_item_id_to)
        return updated_location
    except ValueError as e: # Catch potential errors from underlying CRUD
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/trays/{tray_id}/available_slot/", response_model=Optional[schemas.MaterialLocation], summary="Find first available empty slot on a tray", tags=["Material Locations"])
def find_first_available_slot(tray_id: str = Path(..., description="Tray ID"), db: Session = Depends(get_db)):
    # Finds the first slot on the specified tray that has an empty item_id.
    try:
        location = crud.find_available_slot_on_tray(db, tray_id=tray_id)
        # No need to raise 404 if location is None, FastAPI handles Optional response
        return location
    except ValueError as e: # Raised if tray itself not found
        raise HTTPException(status_code=404, detail=str(e))


# --- Item-Centric Endpoints ---

@app.get("/items/{item_id}/locations/", response_model=List[schemas.MaterialLocation], summary="Find all locations for a specific item ID", tags=["Items"])
def find_item_locations(
    item_id: str = Path(..., description="The item ID to search for"),
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db)
):
    # Retrieves a list of all tray/slot locations where a given item_id is found.
    if not item_id or item_id == "":
        raise HTTPException(status_code=400, detail="A non-empty item_id must be provided for this search.")
    locations = crud.get_material_locations_by_item_id(db, item_id=item_id, skip=skip, limit=limit)
    return locations


# --- Generic/Admin Location Endpoints (using MaterialLocation.id PK) ---

@app.get("/locations/", response_model=List[schemas.MaterialLocation], summary="List all material locations globally (Admin)", tags=["Admin - Locations"])
def read_all_material_locations_globally(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # (Admin) Retrieves all material location records globally.
    return crud.get_all_material_locations(db, skip=skip, limit=limit)

@app.get("/locations/{location_id}/", response_model=schemas.MaterialLocation, summary="Get a location by its database ID (Admin)", tags=["Admin - Locations"])
def read_location_by_db_id(location_id: int = Path(..., description="DB PK of the MaterialLocation record"), db: Session = Depends(get_db)):
    # (Admin) Retrieves a specific material location record by its database ID.
    location = crud.get_material_location_by_id(db, location_id=location_id)
    if location is None:
        raise HTTPException(status_code=404, detail=f"MaterialLocation with DB ID {location_id} not found.")
    return location

@app.post("/locations/batch_update_content/", response_model=List[schemas.MaterialLocation], summary="Batch update content of locations by DB IDs (Admin)", tags=["Admin - Locations"])
def batch_update_locations_content_by_ids(updates: List[schemas.MaterialLocationBulkUpdateItem], db: Session = Depends(get_db)):
    # (Admin) Batch updates item_id and process_info for MaterialLocations by DB IDs.
    if not updates:
        raise HTTPException(status_code=400, detail="No update data provided.")
    try:
        updated_locations = crud.batch_update_material_location_content_by_ids(db=db, updates=updates)
        return updated_locations
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/locations/batch_clear_by_ids/", response_model=List[schemas.MaterialLocation], summary="Batch clear items from locations by DB IDs (Admin)", tags=["Admin - Locations"])
def batch_clear_locations_by_ids(
    location_ids: List[int] = Body(..., embed=True, description="List of MaterialLocation DB IDs to clear"),
    set_item_id_to: str = Query("", description="Value for item_id when clearing."),
    db: Session = Depends(get_db)
):
    # (Admin) Batch clears item_id for MaterialLocations by DB IDs.
    if not location_ids:
        raise HTTPException(status_code=400, detail="No location IDs provided.")
    try:
        cleared_locations = crud.batch_clear_material_locations_by_slot_ids(db=db, location_ids=location_ids, new_item_id_value=set_item_id_to)
        return cleared_locations
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- System Endpoints ---
@app.get("/health", summary="Health Check", tags=["System"])
def health_check():
    # Basic health check.
    return {"status": "ok", "message": "WMS API is running."}
