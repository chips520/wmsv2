from sqlalchemy.orm import Session
from sqlalchemy import exc # For catching integrity errors
from . import models, schemas
from typing import List, Optional

# --- Tray CRUD Functions ---

def create_tray(db: Session, tray: schemas.TrayCreate) -> models.Tray:
    db_tray_model = models.Tray(**tray.model_dump())
    db.add(db_tray_model)
    try:
        db.commit()
        db.refresh(db_tray_model)
        # After successfully creating a tray, initialize its slots
        initialize_slots_for_tray(db, tray_id=db_tray_model.tray_id, max_slots=db_tray_model.max_slots)
        return db_tray_model
    except exc.IntegrityError as e:
        db.rollback()
        raise ValueError(f"Tray with ID '{tray.tray_id}' already exists or another integrity error occurred: {str(e)}")


def get_tray(db: Session, tray_id: str) -> Optional[models.Tray]:
    return db.query(models.Tray).filter(models.Tray.tray_id == tray_id).first()

def get_trays(db: Session, skip: int = 0, limit: int = 100) -> List[models.Tray]:
    return db.query(models.Tray).order_by(models.Tray.tray_id).offset(skip).limit(limit).all()

def update_tray(db: Session, tray_id: str, tray_update: schemas.TrayUpdate) -> Optional[models.Tray]:
    db_tray = get_tray(db, tray_id)
    if db_tray:
        update_data = tray_update.model_dump(exclude_unset=True)
        if "max_slots" in update_data and db_tray.max_slots != update_data["max_slots"]:
             # This logic should be carefully considered - changing max_slots has implications.
             # For now, we allow the field to be set, but no automatic slot adjustment is done here.
             pass

        for key, value in update_data.items():
            setattr(db_tray, key, value)
        db.commit()
        db.refresh(db_tray)
    return db_tray

def delete_tray(db: Session, tray_id: str) -> Optional[models.Tray]:
    db_tray = get_tray(db, tray_id)
    if db_tray:
        db.query(models.MaterialLocation).filter(models.MaterialLocation.tray_id == tray_id).delete(synchronize_session='fetch')
        db.delete(db_tray)
        db.commit()
    return db_tray

# --- MaterialLocation Specific Logic & CRUD ---

def initialize_slots_for_tray(db: Session, tray_id: str, max_slots: int, default_item_id: Optional[str] = ""):
    # Populates MaterialLocation with empty slots for a specified tray.
    # If slots already exist, it avoids adding duplicates.
    db_tray = get_tray(db, tray_id)
    if not db_tray:
        raise ValueError(f"Tray with ID '{tray_id}' does not exist. Cannot initialize slots.")
    if max_slots != db_tray.max_slots:
        raise ValueError(f"Provided max_slots ({max_slots}) for initialization does not match tray's configured max_slots ({db_tray.max_slots}).")

    new_slots_to_add = []
    for i in range(1, max_slots + 1):
        existing_slot = get_material_location_by_tray_and_slot(db, tray_id, i)
        if not existing_slot:
            new_slots_to_add.append(models.MaterialLocation(
                tray_id=tray_id,
                slot_index=i,
                item_id=default_item_id
            ))

    if new_slots_to_add:
        db.add_all(new_slots_to_add)
        try:
            db.commit()
        except exc.IntegrityError as e:
            db.rollback()
            raise ValueError(f"Failed to initialize some slots for tray {tray_id} due to integrity error: {str(e)}.")
    return len(new_slots_to_add)


def create_material_location(db: Session, location: schemas.MaterialLocationCreate) -> models.MaterialLocation:
    # Creates a single MaterialLocation record.
    # Usually, slots are created via initialize_slots_for_tray.
    db_tray = get_tray(db, location.tray_id)
    if not db_tray:
        raise ValueError(f"Tray with ID '{location.tray_id}' does not exist.")
    if not (1 <= location.slot_index <= db_tray.max_slots):
        raise ValueError(f"Slot index {location.slot_index} is out of range for tray '{location.tray_id}' (1-{db_tray.max_slots}).")

    existing_slot = get_material_location_by_tray_and_slot(db, location.tray_id, location.slot_index)
    if existing_slot:
        raise ValueError(f"Slot {location.slot_index} on tray '{location.tray_id}' already exists.")

    db_location_model = models.MaterialLocation(**location.model_dump())
    db.add(db_location_model)
    try:
        db.commit()
        db.refresh(db_location_model)
        return db_location_model
    except exc.IntegrityError:
        db.rollback()
        raise ValueError(f"Slot {location.slot_index} on tray '{location.tray_id}' could not be created (conflict).")


def get_material_location_by_tray_and_slot(db: Session, tray_id: str, slot_index: int) -> Optional[models.MaterialLocation]:
    return db.query(models.MaterialLocation).filter(
        models.MaterialLocation.tray_id == tray_id,
        models.MaterialLocation.slot_index == slot_index
    ).first()

def get_material_location_by_id(db: Session, location_id: int) -> Optional[models.MaterialLocation]:
    # Gets a material location by its own primary key 'id'.
    return db.query(models.MaterialLocation).filter(models.MaterialLocation.id == location_id).first()

def get_material_locations_by_tray(db: Session, tray_id: str, skip: int = 0, limit: Optional[int] = None) -> List[models.MaterialLocation]:
    # Gets all material locations for a specific tray, ordered by slot_index.
    query = db.query(models.MaterialLocation).filter(models.MaterialLocation.tray_id == tray_id).order_by(models.MaterialLocation.slot_index)
    if skip > 0:
        query = query.offset(skip)
    if limit is not None and limit > 0:
        query = query.limit(limit)
    return query.all()

def get_material_locations_by_item_id(db: Session, item_id: str, skip: int = 0, limit: int = 100) -> List[models.MaterialLocation]:
    if item_id is None: return []
    return db.query(models.MaterialLocation).filter(models.MaterialLocation.item_id == item_id).offset(skip).limit(limit).all()

def get_all_material_locations(db: Session, skip: int = 0, limit: int = 100) -> List[models.MaterialLocation]:
    # Gets all material locations across all trays, ordered by tray_id then slot_index.
    return db.query(models.MaterialLocation).order_by(models.MaterialLocation.tray_id, models.MaterialLocation.slot_index).offset(skip).limit(limit).all()


def update_material_location_content(db: Session, tray_id: str, slot_index: int, item_update: schemas.MaterialLocationUpdate) -> Optional[models.MaterialLocation]:
    # Updates the item_id and/or process_info for a specific slot on a tray.
    db_location = get_material_location_by_tray_and_slot(db, tray_id, slot_index)
    if db_location:
        update_data = item_update.model_dump(exclude_unset=True)
        if not update_data: return db_location

        for key, value in update_data.items():
            setattr(db_location, key, value)
        try:
            db.commit()
            db.refresh(db_location)
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error updating slot {slot_index} on tray '{tray_id}': {str(e)}")
    return db_location


def place_item_in_slot(db: Session, tray_id: str, slot_index: int, item_id: str, process_info: Optional[str] = None, allow_overwrite: bool = False) -> models.MaterialLocation:
    # Places an item into a specified slot. Fails if the slot is already occupied, unless allow_overwrite is True.
    db_tray = get_tray(db, tray_id)
    if not db_tray:
        raise ValueError(f"Tray '{tray_id}' not found.")
    if not (1 <= slot_index <= db_tray.max_slots):
        raise ValueError(f"Slot index {slot_index} is out of range (1-{db_tray.max_slots}) for tray '{tray_id}'.")

    db_location = get_material_location_by_tray_and_slot(db, tray_id, slot_index)

    if not db_location:
        # This case implies that the slot wasn't pre-initialized.
        # As per design, slots should be pre-initialized.
        # However, if we want to be robust or allow dynamic slot creation (not current design):
        # db_location = models.MaterialLocation(tray_id=tray_id, slot_index=slot_index, item_id="")
        # db.add(db_location)
        # try:
        #     db.commit()
        #     db.refresh(db_location)
        # except exc.IntegrityError:
        #     db.rollback()
        #     # Re-fetch in case of race condition where another process created it.
        #     db_location = get_material_location_by_tray_and_slot(db, tray_id, slot_index)
        #     if not db_location: # Still not found, something is wrong.
        #          raise ValueError(f"Failed to create or retrieve slot {slot_index} on tray '{tray_id}' after initial miss.")
        raise ValueError(f"Slot {slot_index} on tray '{tray_id}' does not exist. Slots must be pre-initialized.")


    if not allow_overwrite and db_location.item_id and db_location.item_id != "":
        raise ValueError(f"Slot {slot_index} on tray '{tray_id}' is already occupied by item '{db_location.item_id}'. Overwrite not allowed.")

    db_location.item_id = item_id
    db_location.process_info = process_info
    try:
        db.commit()
        db.refresh(db_location)
        return db_location
    except Exception as e:
        db.rollback()
        raise ValueError(f"Could not place item in slot {slot_index} on tray '{tray_id}': {str(e)}")


def clear_item_from_slot(db: Session, tray_id: str, slot_index: int, new_item_id_value: str = "") -> Optional[models.MaterialLocation]:
    # Clears the item_id of a specific slot (sets to empty string by default or a specified value e.g. 'DISABLED').
    return update_material_location_content(db, tray_id, slot_index, schemas.MaterialLocationUpdate(item_id=new_item_id_value))


def find_available_slot_on_tray(db: Session, tray_id: str) -> Optional[models.MaterialLocation]:
    # Finds the first available (empty or None item_id) slot on a given tray, ordered by slot_index.
    db_tray = get_tray(db, tray_id)
    if not db_tray:
        raise ValueError(f"Tray '{tray_id}' not found.")

    return db.query(models.MaterialLocation).filter(
        models.MaterialLocation.tray_id == tray_id,
        ((models.MaterialLocation.item_id == "") | (models.MaterialLocation.item_id == None))
    ).order_by(models.MaterialLocation.slot_index).first()


# --- Batch Operations (operating on MaterialLocation.id PK) ---

def batch_update_material_location_content_by_ids(db: Session, updates: List[schemas.MaterialLocationBulkUpdateItem]) -> List[models.MaterialLocation]:
    # Updates content (item_id, process_info) of multiple MaterialLocation records identified by their PK 'id'.
    updated_location_ids = []
    successfully_updated_locations = []

    for item_update_data in updates:
        db_loc = get_material_location_by_id(db, item_update_data.id)
        if db_loc:
            update_args = item_update_data.model_dump(exclude={'id'}, exclude_unset=True)
            if not update_args: continue

            for key, value in update_args.items():
                setattr(db_loc, key, value)
            db.add(db_loc)
            updated_location_ids.append(db_loc.id)

    if updated_location_ids:
        try:
            db.commit()
            successfully_updated_locations = db.query(models.MaterialLocation).filter(models.MaterialLocation.id.in_(updated_location_ids)).all()
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error during batch update: {str(e)}")
    return successfully_updated_locations


def batch_clear_material_locations_by_slot_ids(db: Session, location_ids: List[int], new_item_id_value: str = "") -> List[models.MaterialLocation]:
    # Clears item_id for a list of material locations identified by their PK IDs.
    if not location_ids: return []

    locations_to_clear = db.query(models.MaterialLocation).filter(models.MaterialLocation.id.in_(location_ids)).all()
    if not locations_to_clear: return []

    for loc in locations_to_clear:
        loc.item_id = new_item_id_value
        db.add(loc)

    try:
        db.commit()
        return db.query(models.MaterialLocation).filter(models.MaterialLocation.id.in_([loc.id for loc in locations_to_clear])).all()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error during batch clear by slot IDs: {str(e)}")


def delete_material_location_by_id(db: Session, location_id: int) -> Optional[models.MaterialLocation]:
    # Deletes a material_location record by its primary key 'id'.
    # This removes the slot record itself. Use with caution.
    db_location = get_material_location_by_id(db, location_id)
    if db_location:
        db.delete(db_location)
        db.commit()
    return db_location
