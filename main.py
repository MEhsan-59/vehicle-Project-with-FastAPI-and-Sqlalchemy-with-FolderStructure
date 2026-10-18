from fastapi import FastAPI

from core.database import SessionLocal, initialize_database
from routers import accounts, cars, expiry, history, maintenance, parts
from services.default_part_service import seed_default_parts
import default_parts

initialize_database()
with SessionLocal() as db:
    seed_default_parts(db, default_parts.DEFAULT_PARTS)

app = FastAPI(title="Vehicle Maintenance API")
app.include_router(accounts.router)
app.include_router(parts.router, prefix="/parts", tags=["parts"])
app.include_router(cars.router, prefix="/cars", tags=["cars"])
app.include_router(history.router, prefix="/history", tags=["history"])
app.include_router(maintenance.router, prefix="/cars", tags=["maintenance"])
app.include_router(expiry.router, prefix="/expiry", tags=["expiry"])
