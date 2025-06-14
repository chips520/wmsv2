from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func, event
from sqlalchemy.orm import relationship
from .database import Base

class Tray(Base):
    __tablename__ = "trays"

    tray_id = Column(String, primary_key=True, index=True, comment="Unique identifier for the tray (e.g., AGV1, TS01).")
    description = Column(String, nullable=True, comment="Brief description of the tray.")
    max_slots = Column(Integer, nullable=False, comment="Total number of material location slots on this tray.")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Timestamp of tray registration.")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Timestamp of last update to tray info.")

    # Relationship (optional but good for ORM use if needed, though not strictly required for this design's core logic)
    # material_locations = relationship("MaterialLocation", back_populates="tray")

    def __repr__(self):
        return f"<Tray(tray_id='{self.tray_id}', max_slots={self.max_slots})>"


class MaterialLocation(Base):
    __tablename__ = "material_locations"

    id = Column(Integer, primary_key=True, index=True, comment="Auto-incrementing primary key for the location record.")

    tray_id = Column(String, ForeignKey("trays.tray_id"), nullable=False, index=True)
    slot_index = Column(Integer, nullable=False, index=True, comment="Specific index or position of this slot on the tray (1 to max_slots).")

    item_id = Column(String, nullable=True, index=True, comment="ID of the material/sample. Empty or NULL if slot is available. Special value if disabled.")

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Timestamp of the last modification to this slot's state.")
    process_info = Column(String, nullable=True, comment="Optional: Information about the last operation or process.")

    # Define a composite unique constraint
    __table_args__ = (UniqueConstraint('tray_id', 'slot_index', name='_tray_slot_uc'),)

    # Relationship (optional)
    # tray = relationship("Tray", back_populates="material_locations")

    def __repr__(self):
        return f"<MaterialLocation(tray_id='{self.tray_id}', slot_index={self.slot_index}, item_id='{self.item_id}')>"

# After models are defined, they are registered with Base.metadata.
# The actual table creation happens when Base.metadata.create_all(engine) is called,
# typically in database.py's init_db() or via Alembic migrations.

# Example of how to auto-populate slots after a Tray is created (using SQLAlchemy event listeners).
# This is more advanced and might be better handled in a CRUD operation for explicitness.
# For now, manual population via a CRUD/service layer function is assumed as per design.md.
#
# def after_tray_inserted(mapper, connection, target):
#     from .crud import create_initial_slots_for_tray # Avoid circular import
#     from .database import SessionLocal
#     db = SessionLocal()
#     try:
#         create_initial_slots_for_tray(db, target.tray_id, target.max_slots)
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         # Log error appropriately
#         print(f"Error auto-populating slots for tray {target.tray_id}: {e}")
#     finally:
#         db.close()
#
# event.listen(Tray, 'after_insert', after_tray_inserted)
