import time

from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine

expected = set(ScriptDirectory("alembic").get_heads())
deadline = time.monotonic() + 600
while time.monotonic() < deadline:
    try:
        with get_engine().connect() as connection:
            current = set(MigrationContext.configure(connection).get_current_heads())
            if current == expected:
                print("Database schema is ready", flush=True)
                break
    except SQLAlchemyError:
        pass
    print("Waiting for database migration", flush=True)
    time.sleep(3)
else:
    raise SystemExit("Timed out waiting for the database schema")
