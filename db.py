from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv
import os


load_dotenv()


engine = create_engine(os.environ.get("DATABASE_URL"), echo=True, connect_args={"ssl": "strict"})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
