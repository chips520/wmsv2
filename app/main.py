from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from . import crud, models, schemas
from .database import SessionLocal, engine, init_db

# Initialize DB and create tables if they don't exist
# This should ideally be managed by Alembic for migrations in a production app,
# but for simplicity, we call it here.
try:
    init_db()
except Exception as e:
    print(f"Error initializing DB: {e}")
    # Depending on the setup, you might want to exit or handle this error
    # For now, we'll let it proceed, FastAPI might fail to start if DB is critical

app = FastAPI(title="WMS API", version="0.1.0")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/locations/", response_model=schemas.MaterialLocationInDB, summary="Create Material Location", tags=["Material Locations"])
def create_material_location(location: schemas.MaterialLocationCreate, db: Session = Depends(get_db)):
    return crud.create_material_location(db=db, location=location)

@app.get("/locations/", response_model=List[schemas.MaterialLocationInDB], summary="Read All Material Locations", tags=["Material Locations"])
def read_all_material_locations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    locations = crud.get_all_material_locations(db, skip=skip, limit=limit)
    return locations

@app.get("/locations/id/{location_id}", response_model=schemas.MaterialLocationInDB, summary="Read Material Location by ID", tags=["Material Locations"])
def read_material_location_by_id(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.get_material_location(db, location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="MaterialLocation not found")
    return db_location

@app.get("/locations/item/{item_id}/", response_model=List[schemas.MaterialLocationInDB], summary="Read Material Locations by Item ID", tags=["Material Locations"])
def read_material_locations_by_item_id(item_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    locations = crud.get_material_locations_by_item_id(db, item_id=item_id, skip=skip, limit=limit)
    if not locations:
        # Return empty list if no locations found, or 404 if that's preferred
        # raise HTTPException(status_code=404, detail=f"No MaterialLocations found for item_id {item_id}")
        pass
    return locations

@app.get("/locations/tray/{tray_id}/", response_model=List[schemas.MaterialLocationInDB], summary="Read Material Locations by Tray ID", tags=["Material Locations"])
def read_material_locations_by_tray_id(tray_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    locations = crud.get_material_locations_by_tray_id(db, tray_id=tray_id, skip=skip, limit=limit)
    if not locations:
        # Return empty list or 404
        pass
    return locations

# Using POST for update as per requirement "only GET, POST"
@app.post("/locations/update/{location_id}/", response_model=schemas.MaterialLocationInDB, summary="Update Material Location", tags=["Material Locations"])
def update_material_location_endpoint(location_id: int, location_update: schemas.MaterialLocationUpdate, db: Session = Depends(get_db)):
    db_location = crud.update_material_location(db, location_id=location_id, location_update=location_update)
    if db_location is None:
        raise HTTPException(status_code=404, detail="MaterialLocation not found for updating")
    return db_location

@app.post("/locations/batch_update/", response_model=List[schemas.MaterialLocationInDB], summary="Batch Update Material Locations", tags=["Material Locations"])
def batch_update_locations_endpoint(updates: List[schemas.MaterialLocationBulkUpdateItem], db: Session = Depends(get_db)):
    # Ensure updates list is not empty to prevent errors with some DB backends if IN clause is empty
    if not updates:
        raise HTTPException(status_code=400, detail="No update data provided")
    updated_locations = crud.batch_update_material_locations(db=db, updates=updates)
    if not updated_locations and updates: # If updates were provided but nothing came back (e.g. all IDs invalid)
        # This check might need refinement based on expected behavior for partial success
        raise HTTPException(status_code=404, detail="No locations found for batch update or failed to update.")
    return updated_locations

@app.post("/locations/clear/{location_id}/", response_model=schemas.MaterialLocationInDB, summary="Clear Material Location Item ID", tags=["Material Locations"])
def clear_location_item_endpoint(location_id: int, db: Session = Depends(get_db)):
    cleared_location = crud.clear_material_location_item(db, location_id=location_id)
    if cleared_location is None:
        raise HTTPException(status_code=404, detail="MaterialLocation not found for clearing")
    return cleared_location

@app.post("/locations/batch_clear/", response_model=List[schemas.MaterialLocationInDB], summary="Batch Clear Material Location Item IDs", tags=["Material Locations"])
def batch_clear_locations_endpoint(location_ids: List[int] = Body(..., embed=True, description="List of location IDs to clear"), db: Session = Depends(get_db)):
    if not location_ids:
        raise HTTPException(status_code=400, detail="No location IDs provided for batch clear")
    cleared_locations = crud.batch_clear_material_locations_by_ids(db=db, location_ids=location_ids)
    # batch_clear_material_locations_by_ids returns empty list if no valid IDs found or nothing to clear.
    # Consider if 404 is appropriate if no locations were affected.
    # For now, returning empty list is consistent.
    return cleared_locations

# Using POST for delete to adhere strictly to "only GET, POST" if DELETE verb is disallowed
@app.post("/locations/delete/{location_id}/", response_model=schemas.MaterialLocationInDB, summary="Delete Material Location (using POST)", tags=["Material Locations"])
def delete_material_location_endpoint(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.delete_material_location(db, location_id=location_id)
    if db_location is None:
        # The CRUD function already returns the deleted item or None if not found.
        # If it's None, it means it wasn't found to begin with.
        raise HTTPException(status_code=404, detail="MaterialLocation not found for deletion")
    return db_location # Returns the data of the deleted item

# Health check endpoint
@app.get("/health", summary="Health Check", tags=["System"])
def health_check():
    return {"status": "ok"}

# To run the app (from the project root directory):
# uvicorn app.main:app --reload
# Example: Creating __init__.py in the root of the project if needed for uvicorn pathing,
# or adjust PYTHONPATH. For now, assume uvicorn is run from one level above 'app'.
# e.g. if project root is 'wmsv2_project', and this file is 'wmsv2_project/app/main.py',
# run from 'wmsv2_project': uvicorn app.main:app --reload
