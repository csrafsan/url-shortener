# database.py
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# Default fallback points to our upcoming docker container name 'db'
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/minilink")

# Postgres works over a network connection pool, so we remove SQLite-specific arguments
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class URLModel(Base):
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, index=True)
    long_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True, nullable=False)

# This securely creates our tables inside PostgreSQL if they don't exist yet
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()