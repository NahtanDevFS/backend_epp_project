import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# En producción, esto viene del archivo .env
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:pass123@localhost:5432/visionguard_db"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()