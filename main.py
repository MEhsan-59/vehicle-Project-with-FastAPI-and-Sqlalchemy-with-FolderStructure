from fastapi import FastAPI

from core.database import SessionLocal, initialize_database
from routers import accounts, parts
from services.default_part_service import seed_default_parts
import default_parts

initialize_database()
with SessionLocal() as db:
    seed_default_parts(db, default_parts.DEFAULT_PARTS)

app = FastAPI(title="Account and Part API")
app.include_router(accounts.router)
app.include_router(parts.router, prefix="/parts", tags=["parts"])
