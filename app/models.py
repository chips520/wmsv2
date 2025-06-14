from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func # For server-side default timestamp
from .database import Base
# import datetime # Not strictly needed if using server_default for timestamp

class MaterialLocation(Base):
    __tablename__ = "material_locations"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, index=True, comment="ID of the material. Empty if no material, '-99' or '-1' if disabled.")
    # Use server_default for timestamp for database-managed creation/update times
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Timestamp of when the information was stored or modified.")
    tray_id = Column(String, index=True, comment="Corresponding tray number.")
    process_info = Column(String, nullable=True, comment="Optional: Information about the process or task ID.")
