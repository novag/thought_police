from database import Base, engine
from models import Node, Trace, NodeType

def create_database():
    print("Creating database tables...")
    Base.metadata.drop_all(bind=engine)  # Drop all tables first
    Base.metadata.create_all(bind=engine)  # Create all tables
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_database() 