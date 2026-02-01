import fastapi
from contextlib import asynccontextmanager

from api.routes import router
from api.routes_v2 import router as router_v2
from api.test_routes import test_router
from api.auth_routes import router as auth_router
from api.review_routes import router as review_router
from api.chat_routes import router as chat_router
from api.diff_routes import router as diff_router
from api.recovery_routes import router as recovery_router
from api.websocket import router as ws_router
from db.database import init_db


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    init_db()
    print("✓ Database initialized")
    yield


app = fastapi.FastAPI(
    title="APP_Builder API",
    description="Production-Grade Agentic RAG Code Generator",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/health", status_code=fastapi.status.HTTP_200_OK)
async def health_check():
    return {"status": "ok", "version": "2.0.0"}


app.include_router(router, prefix="/api")
app.include_router(router_v2, prefix="/api")
app.include_router(test_router, prefix="/api/test")
app.include_router(auth_router, prefix="/api")
app.include_router(review_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(diff_router, prefix="/api")
app.include_router(recovery_router, prefix="/api")
app.include_router(ws_router, prefix="/api")