from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.types import Enum
from config import DB_SETTINGS
from enum import Enum as PyEnum

class StatusEnum(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

DATABASE_URL = f"postgresql://{DB_SETTINGS['user']}:{DB_SETTINGS['password']}@" \
         f"{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['dbname']}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    recovery_email = Column(String(100), nullable=False)
    recovery_password = Column(String(100), nullable=False)
    status = Column(Enum(StatusEnum), nullable=True)  

# Выполнить создание таблиц (один раз)
Base.metadata.create_all(engine)