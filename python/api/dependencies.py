# api/dependencies.py
from typing import Generator
from fastapi import Depends
from database.sql.base import SQLDatabase
from config.settings import Settings

def get_db() -> Generator[SQLDatabase, None, None]:
    db = SQLDatabase()
    try:
        yield db
    finally:
        db.close()