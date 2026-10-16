"""Run local backend commands with database settings from the ignored root .env.

Examples: .venv/bin/python scripts/backend.py test
          .venv/bin/python scripts/backend.py migrate
          .venv/bin/python scripts/backend.py serve
"""

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
values = dotenv_values(ROOT / ".env")
password = quote(values["POSTGRES_PASSWORD"], safe="")
user = quote(values.get("POSTGRES_USER", "teamdesk"), safe="")
database = quote(values.get("POSTGRES_DB", "teamdesk"), safe="")
env = os.environ.copy()
env["DATABASE_URL"] = (
    f"postgresql+psycopg://{user}:{password}@127.0.0.1:5433/{database}"
)
env["TEST_DATABASE_URL"] = (
    f"postgresql+psycopg://teamdesk:{password}@127.0.0.1:5434/teamdesk_test"
)
commands = {
    "test": ["-m", "pytest", "-v"],
    "migrate": ["-m", "alembic", "upgrade", "head"],
    "migration-check": ["-m", "alembic", "check"],
    "serve": ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
}
if len(sys.argv) != 2 or sys.argv[1] not in commands:
    raise SystemExit("Usage: backend.py test|migrate|migration-check|serve")
raise SystemExit(
    subprocess.call(
        [sys.executable, *commands[sys.argv[1]]], cwd=ROOT / "backend", env=env
    )
)
