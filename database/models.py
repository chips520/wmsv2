from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MaterialLocation(Base):
    __tablename__ = "material_locations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_id = Column(String(255), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tray_number = Column(String(255), nullable=False, index=True)
    process_id = Column(String(255), nullable=True)
    task_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default='empty')

    __table_args__ = (
        Index('ix_material_locations_material_id', 'material_id'),
        Index('ix_material_locations_tray_number', 'tray_number'),
    )
