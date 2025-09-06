import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import uvicorn

app = FastAPI()

# Allow Next.js and Azure to connect (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ismt-frontend.vercel.app",
        "https://mycontactapi123.azurewebsites.net"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure MySQL database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://trinav:Password123@trinav.mysql.database.azure.com:3306/contacts_db"
)
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

# Pydantic model for input
class ContactCreate(BaseModel):
    name: str
    email: str
    message: str

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI backend!"}

@app.get("/port")
def read_port():
    return {"port": os.environ.get("PORT")}

@app.post("/api/contact")
def create_contact(contact: ContactCreate, db=Depends(get_db)):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return {"message": "Contact saved successfully"}

@app.get("/api/contacts")
def get_contacts(db=Depends(get_db)):
    contacts = db.query(Contact).all()
    return [{"id": c.id, "name": c.name, "email": c.email, "message": c.message} for c in contacts]

# --- Only add this for Azure deployment ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Azure sets PORT env variable
    uvicorn.run(app, host="0.0.0.0", port=port)
