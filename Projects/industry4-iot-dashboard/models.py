import math
import os
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = "sqlite:///" + os.path.join(DATA_DIR, "sensors.db").replace("\\", "/")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# --- Reference Tables ---
# Reference entities connect generic sensor readings to the dashboard's
# industrial scenarios: workers, machines, and packages.

class Person(Base):
    __tablename__ = "person"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    # relationship
    workers = relationship("Worker", back_populates="person")


class Machine(Base):
    __tablename__ = "machine"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    # relationships
    tool_drops = relationship("ToolDrop", back_populates="machine")
    vibrations = relationship("MachineVibration", back_populates="machine")
    agvs = relationship("AGV", back_populates="machine")


class Package(Base):
    __tablename__ = "package"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    # relationship
    package_drops = relationship("PackageDrop", back_populates="package")


# --- Reading (generic, no FK) ---

class Reading(Base):
    __tablename__ = "readings"
    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(String)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    light = Column(Float)
    temp = Column(Float)
    tilt = Column(Float)
    mag = Column(Float)
    sound = Column(Float)
    flame = Column(Float)


# --- Linked Entities ---
# Each linked table stores the module-specific view of the same incoming sensor
# stream, so pages can query/export records in terms of their use case.

class ToolDrop(Base):
    __tablename__ = "tool_drop"
    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(String)
    magnetic = Column(Float)
    magnitude = Column(Float)
    sound = Column(Float)
    machine_id = Column(Integer, ForeignKey("machine.id"))
    machine = relationship("Machine", back_populates="tool_drops")


class MachineVibration(Base):
    __tablename__ = "machine_vibration"
    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(String)
    tilt = Column(Float)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    magnitude = Column(Float)
    machine_id = Column(Integer, ForeignKey("machine.id"))
    machine = relationship("Machine", back_populates="vibrations")


class AGV(Base):
    __tablename__ = "agv"
    id = Column(Integer, primary_key=True, index=True)
    magnitude = Column(Float)
    time_stamp = Column(String)
    tilt = Column(Float)
    pitch = Column(Float)
    roll = Column(Float)
    machine_id = Column(Integer, ForeignKey("machine.id"))
    machine = relationship("Machine", back_populates="agvs")


class PackageDrop(Base):
    __tablename__ = "package_drop"
    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(String)
    magnitude = Column(Float)
    sound = Column(Float)
    package_id = Column(Integer, ForeignKey("package.id"))
    package = relationship("Package", back_populates="package_drops")


class Worker(Base):
    __tablename__ = "worker"
    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(String)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    posture = Column(Float)
    motion = Column(Float)
    alertness = Column(Float)
    magnitude = Column(Float)
    temperature = Column(Float)
    light = Column(Float)
    person_id = Column(Integer, ForeignKey("person.id"))
    person = relationship("Person", back_populates="workers")

# Recreate all tables
Base.metadata.create_all(bind=engine)


