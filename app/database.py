import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Retrieve database URL from environment or fallback to local SQLite for rapid prototyping
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./syner_cortex.db")

# Setup connection arguments based on database engine
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Create engine
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for SQLAlchemy models (SQLAlchemy 2.0 compatible)
Base = declarative_base()

def get_db():
    """
    FastAPI Dependency to yield a database session and close it afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
