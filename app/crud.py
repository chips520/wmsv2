from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

def get_material_location(db: Session, location_id: int) -> Optional[models.MaterialLocation]:
    return db.query(models.MaterialLocation).filter(models.MaterialLocation.id == location_id).first()

def get_material_locations_by_item_id(db: Session, item_id: str, skip: int = 0, limit: int = 100) -> List[models.MaterialLocation]:
    return db.query(models.MaterialLocation).filter(models.MaterialLocation.item_id == item_id).offset(skip).limit(limit).all()

def get_material_locations_by_tray_id(db: Session, tray_id: str, skip: int = 0, limit: int = 100) -> List[models.MaterialLocation]:
    return db.query(models.MaterialLocation).filter(models.MaterialLocation.tray_id == tray_id).offset(skip).limit(limit).all()

def get_all_material_locations(db: Session, skip: int = 0, limit: int = 100) -> List[models.MaterialLocation]:
    return db.query(models.MaterialLocation).offset(skip).limit(limit).all()

def create_material_location(db: Session, location: schemas.MaterialLocationCreate) -> models.MaterialLocation:
    db_location = models.MaterialLocation(
        item_id=location.item_id,
        tray_id=location.tray_id,
        process_info=location.process_info
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def update_material_location(db: Session, location_id: int, location_update: schemas.MaterialLocationUpdate) -> Optional[models.MaterialLocation]:
    db_location = get_material_location(db, location_id)
    if db_location:
        update_data = location_update.model_dump(exclude_unset=True) # Use model_dump in Pydantic v2
        for key, value in update_data.items():
            setattr(db_location, key, value)
        db.commit()
        db.refresh(db_location)
    return db_location

def delete_material_location(db: Session, location_id: int) -> Optional[models.MaterialLocation]:
    db_location = get_material_location(db, location_id)
    if db_location:
        db.delete(db_location)
        db.commit()
    return db_location

def clear_material_location_item(db: Session, location_id: int) -> Optional[models.MaterialLocation]:
    return update_material_location(db, location_id, schemas.MaterialLocationUpdate(item_id=""))

def batch_update_material_locations(db: Session, updates: List[schemas.MaterialLocationBulkUpdateItem]) -> List[models.MaterialLocation]:
    updated_location_ids = []
    locations_to_return = []

    for loc_update_data in updates:
        db_loc = db.query(models.MaterialLocation).filter(models.MaterialLocation.id == loc_update_data.id).first()
        if db_loc:
            update_args = {k: v for k, v in loc_update_data.model_dump().items() if k != 'id' and v is not None}

            if not update_args: # No actual fields to update for this item
                # If you want to return even non-updated items that were found:
                # locations_to_return.append(db_loc)
                continue

            for key, value in update_args.items():
                setattr(db_loc, key, value)
            db.add(db_loc) # Mark as dirty
            updated_location_ids.append(db_loc.id)

    if updated_location_ids:
        db.commit()
        # Fetch all successfully updated and committed items to return them with refreshed data
        locations_to_return = db.query(models.MaterialLocation).filter(models.MaterialLocation.id.in_(updated_location_ids)).all()

    return locations_to_return

def batch_clear_material_locations_by_ids(db: Session, location_ids: List[int]) -> List[models.MaterialLocation]:
    locations_to_clear = db.query(models.MaterialLocation).filter(models.MaterialLocation.id.in_(location_ids)).all()

    if not locations_to_clear:
        return []

    cleared_ids = []
    for loc in locations_to_clear:
        loc.item_id = "" # Set item_id to empty
        db.add(loc) # Mark as dirty
        cleared_ids.append(loc.id)

    if cleared_ids:
        db.commit()
        # Re-fetch the cleared locations to return their updated state
        return db.query(models.MaterialLocation).filter(models.MaterialLocation.id.in_(cleared_ids)).all()
    return []
