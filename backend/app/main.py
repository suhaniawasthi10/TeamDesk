from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import get_engine
from app.routes import router

app = FastAPI(title="TeamDesk API", version="1.0.0")
app.include_router(router)


@app.get("/health", tags=["Operations"])
def health():
    return {"status": "ok", "version": get_settings().app_version}


@app.get("/ready", tags=["Operations"])
def ready():
    try:
        with get_engine().connect() as connection:
            # Check connectivity AND that the migration has created our table.
            connection.execute(text("SELECT 1 FROM employees LIMIT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}


Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/health", "/ready", "/metrics"],
).instrument(app).expose(app, include_in_schema=False)
