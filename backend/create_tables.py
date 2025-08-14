from logic.database import Base, engine
from logic.models import (
    ProgressDismantle, KendalaDismantle,
    STBProgress, KendalaSTB,
    VisitDismantle, VisitSTB,
)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
