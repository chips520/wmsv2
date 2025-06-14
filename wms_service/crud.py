from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from database import models
from . import schemas
from database.database_config import SessionLocal

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_location(db: Session, location_schema: schemas.MaterialLocationCreate) -> models.MaterialLocation:
    db_location = models.MaterialLocation(**location_schema.dict())

    if location_schema.material_id in ["-99", "-1"]:
        db_location.status = "disabled"
    elif location_schema.material_id and location_schema.material_id.strip():
        db_location.status = "active"
    else:
        db_location.status = "empty"
        db_location.material_id = None # Ensure material_id is None if status is empty

    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_location(db: Session, location_id: int) -> Optional[models.MaterialLocation]:
    return db.query(models.MaterialLocation).filter(models.MaterialLocation.id == location_id).first()

def get_locations_by_tray(db: Session, tray_number: str, skip: int = 0, limit: int = 100) -> List[models.MaterialLocation]:
    return db.query(models.MaterialLocation).filter(models.MaterialLocation.tray_number == tray_number).offset(skip).limit(limit).all()

def get_locations_by_material_id(db: Session, material_id: str, skip: int = 0, limit: int = 100) -> List[models.MaterialLocation]:
    return db.query(models.MaterialLocation).filter(models.MaterialLocation.material_id == material_id).offset(skip).limit(limit).all()

def update_location(db: Session, location_id: int, location_schema: schemas.MaterialLocationUpdate) -> Optional[models.MaterialLocation]:
    db_location = db.query(models.MaterialLocation).filter(models.MaterialLocation.id == location_id).first()
    if not db_location:
        return None

    update_data = location_schema.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_location, key, value)

    # Adjust status based on material_id, similar to create_location
    # Check if material_id was part of the update data, otherwise use existing
    current_material_id = update_data.get('material_id', db_location.material_id)
    if current_material_id in ["-99", "-1"]:
        db_location.status = "disabled"
    elif current_material_id and str(current_material_id).strip(): # Ensure it's treated as string for strip
        db_location.status = "active"
    else:
        db_location.status = "empty"
        db_location.material_id = None # Ensure material_id is None if status is empty

    # If status was explicitly provided in the update and material_id logic doesn't override, keep it
    # However, the logic above will always set status based on material_id.
    # If 'status' is in update_data and we want to allow direct status override,
    # this logic needs adjustment. For now, material_id drives status.
    if 'status' in update_data and update_data['status'] is not None:
        # If status is explicitly set and material_id is None or empty,
        # and the explicit status is not 'empty', this could be contradictory.
        # Current logic: material_id presence dictates active/disabled, otherwise empty.
        # Let's assume material_id based status is authoritative if material_id is being set.
        # If material_id is NOT in update_data, then an explicit status update could be allowed.
        if 'material_id' not in update_data:
             db_location.status = update_data['status']


    db.commit()
    db.refresh(db_location)
    return db_location

def delete_location(db: Session, location_id: int) -> Optional[models.MaterialLocation]:
    db_location = db.query(models.MaterialLocation).filter(models.MaterialLocation.id == location_id).first()
    if db_location:
        db.delete(db_location)
        db.commit()
        return db_location
    return None

def clear_location_by_id(db: Session, location_id: int) -> Optional[models.MaterialLocation]:
    db_location = db.query(models.MaterialLocation).filter(models.MaterialLocation.id == location_id).first()
    if db_location:
        db_location.material_id = None
        db_location.process_id = None # Also clear process_id and task_id as per common sense for "clear"
        db_location.task_id = None
        db_location.status = 'empty'
        db.commit()
        db.refresh(db_location)
        return db_location
    return None

def batch_update_locations(db: Session, updates_list: List[Dict[str, Any]]) -> List[models.MaterialLocation]:
    updated_locations = []
    for item in updates_list:
        location_id = item.get("id")
        data_dict = item.get("data")
        if location_id is None or data_dict is None:
            # Or handle error appropriately, e.g., log, raise exception, or add None to results
            continue

        # Ensure data_dict is a dictionary before creating MaterialLocationUpdate
        if not isinstance(data_dict, dict):
            # Handle error: data_dict is not a dictionary
            continue

        location_schema = schemas.MaterialLocationUpdate(**data_dict)

        # It's important that update_location can handle if db_location is None
        updated_location = update_location(db=db, location_id=location_id, location_schema=location_schema)
        if updated_location:
            updated_locations.append(updated_location)
        # else: handle case where a specific update failed, if necessary

    return updated_locations

def batch_clear_locations_by_ids(db: Session, location_ids: List[int]) -> List[models.MaterialLocation]:
    cleared_locations = []
    for loc_id in location_ids:
        cleared_loc = clear_location_by_id(db=db, location_id=loc_id)
        if cleared_loc:
            cleared_locations.append(cleared_loc)
    return cleared_locations

def batch_clear_locations_by_tray(db: Session, tray_number: str) -> List[models.MaterialLocation]:
    locations_to_clear = db.query(models.MaterialLocation).filter(models.MaterialLocation.tray_number == tray_number).all()
    cleared_locations = []
    for loc in locations_to_clear:
        loc.material_id = None
        loc.process_id = None # Also clear process_id and task_id
        loc.task_id = None
        loc.status = 'empty'
        cleared_locations.append(loc)

    if locations_to_clear: # Only commit if there's something to change
        db.commit()
        for loc in cleared_locations: # Refresh each object if needed, or re-fetch
            db.refresh(loc) # Refresh to get updated timestamp etc.

    return cleared_locations

def query_locations(db: Session, tray_number: Optional[str] = None, material_id: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.MaterialLocation]:
    query = db.query(models.MaterialLocation)
    if tray_number is not None:
        query = query.filter(models.MaterialLocation.tray_number == tray_number)
    if material_id is not None:
        query = query.filter(models.MaterialLocation.material_id == material_id)
    if status is not None:
        query = query.filter(models.MaterialLocation.status == status)

    return query.offset(skip).limit(limit).all()
