from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv  # Added
import os  # Added
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Contact Form API",
    description="API for handling contact form submissions",
    version="1.0.0"
)

# Allow Next.js to connect (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],  # Use env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure MySQL database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")
engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl": {"ssl_ca": os.getenv("SSL_CERT_PATH", "DigiCertGlobalRootCA.crt.pem")}}
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

# Pydantic model for input validation
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

# Root endpoint for health check
@app.get("/")
def read_root():
    return {"message": "Contact Form API is running"}

# Endpoint to save contact (POST)
@app.post("/api/contact")
def create_contact(contact: ContactCreate, db=Depends(get_db)):
    try:
        db_contact = Contact(**contact.dict())
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        logger.info(f"Contact saved: {contact.email}")
        return {"message": "Contact saved successfully"}
    except Exception as e:
        logger.error(f"Error saving contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save contact")

# Endpoint to get all contacts (GET)
@app.get("/api/contacts")
def get_contacts(db=Depends(get_db)):
    try:
        contacts = db.query(Contact).all()
        logger.info("Retrieved all contacts")
        return [{"id": c.id, "name": c.name, "email": c.email, "message": c.message} for c in contacts]
    except Exception as e:
        logger.error(f"Error retrieving contacts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve contacts")




# DATABASE_URL="mysql+pymysql://trinav@trinav:Password123@trinav.mysql.database.azure.com:3306/contacts_db?ssl_ca=/home/site/wwwroot/DigiCertGlobalRootCA.crt.pem" gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000