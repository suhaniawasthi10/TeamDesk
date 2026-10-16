"""Create ignored local settings without displaying or overwriting passwords."""

import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
env = ROOT / ".env"
if not env.exists():
    password = secrets.token_hex(24)
    fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write(
            f"POSTGRES_DB=teamdesk\nPOSTGRES_USER=teamdesk\nPOSTGRES_PASSWORD={password}\n"
        )
    print("Created ignored .env with a generated local database password.")
else:
    print("Preserved existing .env.")
