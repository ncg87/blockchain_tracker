from typing import Generator
from sqlalchemy.orm import Session
from database import SQLDatabase

from typing import Generator
from functools import lru_cache
from fastapi import Depends

@lru_cache()
def get_settings():
    from config.settings import Settings  # Import here to avoid circular imports
    return Settings()

def get_db() -> Generator[Session, None, None]:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    
    from database import SQLDatabase
    from config import Settings
    
    db = SQLDatabase(**Settings().POSTGRES_CONFIG)
    try:
        yield db
    finally:
        db.close()