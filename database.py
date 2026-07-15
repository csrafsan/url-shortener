# database.py
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./minilink.db")

# Engine handles actual communication with the database file
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Our Database Model (The blueprint of our table)
class URLModel(Base):
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, index=True)
    long_url = Column(String, nullable=False)
    # Notice the index=True here. In system design, indexing makes lookups take O(1) time 
    # instead of scanning the whole table. Crucial for scaling reads!
    short_code = Column(String, unique=True, index=True, nullable=False)

# Create the table columns automatically
Base.metadata.create_all(bind=engine)

# Dependency to safely open and close DB connections per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()