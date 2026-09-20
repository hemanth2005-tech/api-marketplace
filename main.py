from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Depends, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import time
import secrets
from database import engine, get_db
from models import Base, UsageLog, ListedAPI, APIKey, User
from auth import verify_api_key, pwd_context

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Marketplace Setup")
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

class KeyRequest(BaseModel):
    email: str

def log_api_usage(db: Session, api_id: str, consumer_id: str, latency: float, status: int):
    log_entry = UsageLog(
        api_id=api_id,
        consumer_id=consumer_id,
        latency_ms=latency,
        status_code=status
    )
    db.add(log_entry)
    db.commit()

@app.post("/api/v1/generate-key")
def generate_api_key(req: KeyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        user = User(email=req.email)
        db.add(user)
        db.commit()
        db.refresh(user)
        
    raw_key = f"sk_live_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:12]
    
    hashed_key = pwd_context.hash(raw_key)
    api_key_record = APIKey(
        consumer_id=user.id,
        hashed_key=hashed_key,
        prefix=prefix
    )
    db.add(api_key_record)
    db.commit()
    
    return {
        "message": "Copy this key now! You will not be able to see it again.",
        "api_key": raw_key,
        "prefix": prefix,
        "user_id": user.id
    }

@app.get("/api/v1/sample-microservice")
async def sample_microservice(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key)
):
    start_time = time.time()
    payload = {"data": "This is the scraped data or parsed text"}
    latency_ms = (time.time() - start_time) * 1000
    
    background_tasks.add_task(
        log_api_usage, 
        db=db, 
        api_id="sample_api_id",
        consumer_id=api_key.consumer_id, 
        latency=latency_ms, 
        status=200
    )
    return payload

@app.get("/api/v1/analytics")
def get_product_metrics(db: Session = Depends(get_db)):
    total_calls = db.query(UsageLog).count()
    avg_latency = db.query(func.avg(UsageLog.latency_ms)).scalar() or 0.0
    success_calls = db.query(UsageLog).filter(UsageLog.status_code == 200).count()
    recent_logs = db.query(UsageLog).order_by(UsageLog.timestamp.desc()).limit(5).all()
    
    return {
        "kpis": {
            "total_api_consumption": total_calls,
            "success_rate": f"{(success_calls / total_calls * 100) if total_calls else 0}%",
            "average_latency_ms": round(avg_latency, 2),
        },
        "recent_activity": recent_logs
    }