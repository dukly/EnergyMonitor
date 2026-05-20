import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://sunhors:sunhors@localhost:5432/sunhors',
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TelemetryRow(Base):
    __tablename__ = 'telemetry'

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(64), index=True, nullable=False)
    agent_measurement_id = Column(Integer, index=True)
    timestamp = Column(String(32), nullable=False)
    voltage_dc = Column(Float)
    current_dc = Column(Float)
    power_ac = Column(Float)
    temp = Column(Float)
    freq = Column(Float)
    pf = Column(Float)
    energy_total = Column(Float)
    energy_day = Column(Float)
    runtime = Column(Float)
    status = Column(Integer)
    error = Column(Integer)
    status_text = Column(String(128))
    error_text = Column(String(128))
    received_at = Column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
