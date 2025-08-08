#!/usr/bin/env python3
"""
Complete FastAPI Backend for Agentic RAG Drive Monitor
Includes authentication, database, and integration with existing code
"""

import os
import json
import asyncio
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import jwt

# Pydantic Models
class UserRegistration(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class CredentialsSetup(BaseModel):
    google_credentials: str
    openai_api_key: str

class FolderSelection(BaseModel):
    folder_id: Optional[str] = None
    folder_name: Optional[str] = None
    include_subfolders: bool = True

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./drive_monitor.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    google_credentials = Column(Text)
    openai_api_key = Column(String)
    folder_config = Column(JSON)

class ProcessedDocument(Base):
    __tablename__ = "processed_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    file_id = Column(String)
    file_name = Column(String)
    summary = Column(Text)
    priority = Column(String)
    action_items = Column(JSON)
    follow_ups = Column(JSON)
    processed_at = Column(DateTime, default=datetime.utcnow)

class ScanHistory(Base):
    __tablename__ = "scan_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    documents_found = Column(Integer, default=0)
    status = Column(String)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(
    title="Agentic RAG Drive Monitor API",
    description="AI-powered document analysis and monitoring",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
security = HTTPBearer()

# Utility Functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(db: Session = Depends(get_db), user_id: str = Depends(verify_token)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Authentication Endpoints
@app.post("/api/auth/register")
async def register(user_data: UserRegistration, db: Session = Depends(get_db)):
    """Register a new user"""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name}
    }

@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or user.password_hash != hash_password(user_data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name}
    }

# Setup Endpoints
@app.post("/api/setup/credentials")
async def setup_credentials(
    credentials: CredentialsSetup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup API credentials"""
    try:
        # Validate Google credentials JSON
        json.loads(credentials.google_credentials)
        
        current_user.google_credentials = credentials.google_credentials
        current_user.openai_api_key = credentials.openai_api_key
        db.commit()
        
        return {"message": "Credentials saved successfully"}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid Google credentials format")

@app.get("/api/setup/folders")
async def list_folders(current_user: User = Depends(get_current_user)):
    """List available Google Drive folders"""
    if not current_user.google_credentials:
        raise HTTPException(status_code=400, detail="Google credentials not configured")
    
    # TODO: Integrate with your existing GoogleDriveMonitor
    # For now, return sample folders
    return {
        "folders": [
            {"id": "folder_1", "name": "Documents"},
            {"id": "folder_2", "name": "Projects"}, 
            {"id": "folder_3", "name": "Research"},
            {"id": "folder_4", "name": "Reports"},
            {"id": "folder_5", "name": "Meetings"}
        ]
    }

@app.post("/api/setup/folder")
async def select_folder(
    folder_data: FolderSelection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Select folder for monitoring"""
    current_user.folder_config = {
        "folder_id": folder_data.folder_id,
        "folder_name": folder_data.folder_name,
        "include_subfolders": folder_data.include_subfolders
    }
    db.commit()
    return {"message": "Folder configuration saved"}

# Document Processing Endpoints
@app.post("/api/scan/manual")
async def manual_scan(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start manual document scan"""
    if not current_user.google_credentials or not current_user.openai_api_key:
        raise HTTPException(status_code=400, detail="API credentials not configured")
    
    if not current_user.folder_config:
        raise HTTPException(status_code=400, detail="Folder not selected")
    
    # Create scan record
    scan_record = ScanHistory(user_id=current_user.id, status="running")
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)
    
    # Start background scan
    background_tasks.add_task(run_document_scan, current_user.id, scan_record.id)
    
    return {"scan_id": scan_record.id, "status": "started", "message": "Document scan initiated"}

async def run_document_scan(user_id: str, scan_id: str):
    """Background task to run document scan"""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        scan_record = db.query(ScanHistory).filter(ScanHistory.id == scan_id).first()
        
        # TODO: Integrate with your existing AgenticRAGApplication here
        # For now, simulate document processing
        print(f"🔍 Starting scan for user {user.email}")
        
        # Simulate processing time
        await asyncio.sleep(3)
        
        # Create sample processed document
        sample_doc = ProcessedDocument(
            user_id=user_id,
            file_id="sample_doc_001",
            file_name="Q4 Strategy Review.docx",
            summary="Quarterly business strategy review with key performance metrics and future planning initiatives.",
            priority="high",
            action_items=[
                "Schedule Q1 planning meeting with leadership team",
                "Review budget allocations for next quarter",
                "Prepare performance reports for stakeholders"
            ],
            follow_ups=[
                "Follow up on market research findings",
                "Update competitive analysis report",
                "Coordinate with sales team on targets"
            ]
        )
        
        db.add(sample_doc)
        
        # Update scan record
        scan_record.status = "completed"
        scan_record.completed_at = datetime.utcnow()
        scan_record.documents_found = 1
        
        db.commit()
        
        print(f"✅ Scan completed for user {user.email}")
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        scan_record.status = "failed"
        scan_record.completed_at = datetime.utcnow()
        db.commit()
        
    finally:
        db.close()

@app.get("/api/documents")
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get processed documents for current user"""
    documents = db.query(ProcessedDocument).filter(
        ProcessedDocument.user_id == current_user.id
    ).order_by(ProcessedDocument.processed_at.desc()).limit(50).all()
    
    return {
        "documents": [
            {
                "file_id": doc.file_id,
                "name": doc.file_name,
                "summary": doc.summary,
                "priority": doc.priority,
                "action_items": doc.action_items or [],
                "follow_ups": doc.follow_ups or [],
                "processed_at": doc.processed_at
            } for doc in documents
        ]
    }

@app.get("/api/status")
async def get_system_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system status for current user"""
    latest_scan = db.query(ScanHistory).filter(
        ScanHistory.user_id == current_user.id
    ).order_by(ScanHistory.started_at.desc()).first()
    
    total_docs = db.query(ProcessedDocument).filter(
        ProcessedDocument.user_id == current_user.id
    ).count()
    
    return {
        "status": "configured" if current_user.folder_config else "setup_needed",
        "last_scan": latest_scan.completed_at if latest_scan else None,
        "total_documents": total_docs,
        "pending_actions": sum(len(doc.action_items or []) for doc in db.query(ProcessedDocument).filter(ProcessedDocument.user_id == current_user.id).all()),
        "folder_name": current_user.folder_config.get('folder_name') if current_user.folder_config else None
    }

@app.get("/api/stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics"""
    docs_count = db.query(ProcessedDocument).filter(
        ProcessedDocument.user_id == current_user.id
    ).count()
    
    scans_count = db.query(ScanHistory).filter(
        ScanHistory.user_id == current_user.id
    ).count()
    
    latest_activity = db.query(ScanHistory).filter(
        ScanHistory.user_id == current_user.id
    ).order_by(ScanHistory.started_at.desc()).first()
    
    total_actions = sum(
        len(doc.action_items or []) for doc in 
        db.query(ProcessedDocument).filter(ProcessedDocument.user_id == current_user.id).all()
    )
    
    return {
        "documents_processed": docs_count,
        "actions_created": total_actions,
        "scans_performed": scans_count,
        "last_activity": latest_activity.started_at if latest_activity else None
    }

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/")
async def root():
    return {
        "message": "Agentic RAG Drive Monitor API",
        "status": "running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
