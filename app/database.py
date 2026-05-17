import os

# load_dotenv reads the .env file and loads its values into environment variables
from dotenv import load_dotenv


from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

# Load the .env file 
load_dotenv()

# Read the DATABASE_URL from the .env file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./library.db")


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


def get_db():
    db = SessionLocal()     
    try:
        yield db            
    finally:
        db.close()          