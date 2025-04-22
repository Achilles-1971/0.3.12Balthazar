from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Настройки подключения к БД
DATABASE_URL = "postgresql://postgres:111@localhost:5432/0.3.12"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# ----------------------------- SQLAlchemy модели -----------------------------
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(Text)

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

class MachineType(Base):
    __tablename__ = "machine_types"
    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("countries.id"))
    year_of_manufacture = Column(Integer)
    brand = Column(String)

class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True)
    machine_type_id = Column(Integer, ForeignKey("machine_types.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    serial_number = Column(String, unique=True)
    repair_count = Column(Integer, default=0)

class RepairType(Base):
    __tablename__ = "repair_types"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    duration_days = Column(Integer)
    cost = Column(Numeric(10, 2))
    notes = Column(Text)

class Repair(Base):
    __tablename__ = "repairs"
    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    repair_type_id = Column(Integer, ForeignKey("repair_types.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    notes = Column(Text)

# ----------------------------- Pydantic схемы -----------------------------
class ClientOut(BaseModel):
    id: int
    name: str
    address: Optional[str]
    class Config:
        orm_mode = True

class MachineOut(BaseModel):
    id: int
    serial_number: str
    repair_count: int
    class Config:
        orm_mode = True

class RepairCreate(BaseModel):
    machine_id: int
    repair_type_id: int
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None

class RepairOut(RepairCreate):
    id: int
    class Config:
        orm_mode = True

# ----------------------------- Эндпоинты -----------------------------
@app.get("/")
def root():
    return {"message": "Maintenance API работает!"}

@app.get("/clients/", response_model=List[ClientOut])
def get_clients():
    db = SessionLocal()
    clients = db.query(Client).all()
    db.close()
    return clients

@app.get("/machines/", response_model=List[MachineOut])
def get_machines():
    db = SessionLocal()
    machines = db.query(Machine).all()
    db.close()
    return machines

@app.post("/repairs/", response_model=RepairOut)
def create_repair(repair: RepairCreate):
    db = SessionLocal()
    machine = db.query(Machine).filter(Machine.id == repair.machine_id).first()
    if not machine:
        db.close()
        raise HTTPException(status_code=404, detail="Станок не найден")
    new_repair = Repair(**repair.dict())
    db.add(new_repair)
    machine.repair_count += 1
    db.commit()
    db.refresh(new_repair)
    db.close()
    return new_repair

@app.get("/repairs/", response_model=List[RepairOut])
def list_repairs():
    db = SessionLocal()
    repairs = db.query(Repair).all()
    db.close()
    return repairs
