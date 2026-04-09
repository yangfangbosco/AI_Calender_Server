from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, family, sync
from app.database import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="AI Calendar Server", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(family.router, prefix="/api/family", tags=["family"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
