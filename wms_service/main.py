from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from . import crud
from . import schemas
from database.database_config import engine # For metadata creation if chosen, not strictly for Alembic
# Assuming Base is in database.models as per typical structure
from database.models import Base, MaterialLocation as DBMaterialLocation # Renamed to avoid conflict
from .crud import get_db

# Create all tables (Not strictly necessary if using Alembic for migrations, but often included)
# Base.metadata.create_all(bind=engine) # This line is commented out as we use Alembic

app = FastAPI(title="WMS Service", description="Service for Material Location Management")

# Pydantic model for batch update payload, can also be in schemas.py
class LocationBatchUpdateItem(schemas.BaseModel): # Use schemas.BaseModel to ensure pydantic features
    id: int
    data: schemas.MaterialLocationUpdate


@app.get("/")
async def root():
    return {"message": "WMS Service is running"}

@app.post("/locations/", response_model=schemas.MaterialLocation, status_code=201)
async def api_create_location(location: schemas.MaterialLocationCreate, db: Session = Depends(get_db)):
    return crud.create_location(db=db, location_schema=location)

@app.get("/locations/{location_id}", response_model=schemas.MaterialLocation)
async def api_get_location(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.get_location(db=db, location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

@app.get("/locations/", response_model=List[schemas.MaterialLocation])
async def api_query_locations(
    tray_number: Optional[str] = None,
    material_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud.query_locations(
        db=db, tray_number=tray_number, material_id=material_id, status=status, skip=skip, limit=limit
    )

@app.put("/locations/{location_id}", response_model=schemas.MaterialLocation)
async def api_update_location(location_id: int, location: schemas.MaterialLocationUpdate, db: Session = Depends(get_db)):
    db_location = crud.update_location(db=db, location_id=location_id, location_schema=location)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

@app.delete("/locations/{location_id}", response_model=schemas.MaterialLocation)
async def api_delete_location(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.delete_location(db=db, location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

@app.post("/locations/{location_id}/clear", response_model=schemas.MaterialLocation)
async def api_clear_location(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.clear_location_by_id(db=db, location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

@app.post("/locations/batch-update", response_model=List[schemas.MaterialLocation])
async def api_batch_update_locations(updates: List[LocationBatchUpdateItem], db: Session = Depends(get_db)):
    # Convert updates from List[LocationBatchUpdateItem] to List[Dict[str, Any]]
    # as expected by crud.batch_update_locations
    updates_data = [{"id": item.id, "data": item.data.dict(exclude_unset=True)} for item in updates]
    return crud.batch_update_locations(db=db, updates_list=updates_data)

@app.post("/locations/batch-clear-by-ids", response_model=List[schemas.MaterialLocation])
async def api_batch_clear_locations_by_ids(location_ids: List[int], db: Session = Depends(get_db)):
    # Ensure crud.batch_clear_locations_by_ids can handle cases where some IDs might not be found
    # The current crud function iterates and calls clear_location_by_id, which returns None for not found.
    # The result will be a list of successfully cleared locations.
    return crud.batch_clear_locations_by_ids(db=db, location_ids=location_ids)

@app.post("/locations/batch-clear-by-tray/{tray_number}", response_model=List[schemas.MaterialLocation])
async def api_batch_clear_locations_by_tray(tray_number: str, db: Session = Depends(get_db)):
    return crud.batch_clear_locations_by_tray(db=db, tray_number=tray_number)
