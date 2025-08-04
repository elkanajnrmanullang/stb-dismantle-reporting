from logic.models import Base
from logic.database import engine

if __name__ == "__main__":
    print("Membuat semua tabel di database stb_reporting...")
    Base.metadata.create_all(bind=engine)
    print("Tabel berhasil dibuat!")
