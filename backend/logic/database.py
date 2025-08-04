from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from logic.models import Base

# Ubah ini sesuai konfigurasi PostgreSQL kamu
DATABASE_URL = "postgresql://postgres:jnrm_812@localhost:5432/stb_reporting"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
