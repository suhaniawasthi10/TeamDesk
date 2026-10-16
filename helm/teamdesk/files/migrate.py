import time

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine

deadline = time.monotonic() + 540
while time.monotonic() < deadline:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        break
    except SQLAlchemyError:
        print("Waiting for PostgreSQL", flush=True)
        time.sleep(3)
else:
    raise SystemExit("Timed out waiting for PostgreSQL")

command.upgrade(Config("alembic.ini"), "head")
