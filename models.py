from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base
import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    is_developer = Column(Boolean, default=False)

class ListedAPI(Base):
    __tablename__ = "listed_apis"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    developer_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    description = Column(String)
    endpoint_path = Column(String, unique=True)
    
class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    consumer_id = Column(String, ForeignKey("users.id"))
    hashed_key = Column(String, unique=True, index=True)
    prefix = Column(String)
    is_active = Column(Boolean, default=True)

class UsageLog(Base):
    __tablename__ = "usage_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_id = Column(String, ForeignKey("listed_apis.id"))
    consumer_id = Column(String, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    latency_ms = Column(Float)
    status_code = Column(Integer)