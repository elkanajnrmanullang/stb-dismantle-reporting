from logic.database import Base, engine
from logic import models 

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Tables dropped.")

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Tables created.")
