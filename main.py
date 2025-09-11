from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://ismt-frontend.vercel.app"],  # Update to ["https://ismt-frontend.vercel.app"] after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure MySQL database setup
DATABASE_URL = os.getenv("DATABASE_URL")  # Load from .env or Azure settings
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")
engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl": {"ssl_ca": "DigiCertGlobalRootCA.crt.pem"}}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Contact model
class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    email = Column(String(100), index=True)
    message = Column(String(500))

Base.metadata.create_all(bind=engine)

# Pydantic model for input with validation
class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=1, max_length=500)

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root endpoint (optional, to avoid "Method Not Allowed")
@app.get("/")
def read_root():
    return {"message": "Welcome to the Contact API"}

# Endpoint to save contact (POST)
@app.post("/api/contact")
def create_contact(contact: ContactCreate, db=Depends(get_db)):
    # Check for duplicate email
    existing_contact = db.query(Contact).filter(Contact.email == contact.email).first()
    if existing_contact:
        raise HTTPException(status_code=400, detail="Email already exists")
    db_contact = Contact(**contact.dict())
    try:
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return {"message": "Contact saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Endpoint to get all contacts (GET)
@app.get("/api/contacts")
def get_contacts(db=Depends(get_db)):
    contacts = db.query(Contact).all()
    return [{"id": c.id, "name": c.name, "email": c.email, "message": c.message} for c in contacts]