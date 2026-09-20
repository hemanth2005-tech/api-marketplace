from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db
from models import APIKey

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_api_key(
    api_key_header: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    active_keys = db.query(APIKey).filter(APIKey.is_active == True).all()
    
    for key_record in active_keys:
        if pwd_context.verify(api_key_header, key_record.hashed_key):
            return key_record
            
    raise HTTPException(status_code=401, detail="Invalid or missing API Key")