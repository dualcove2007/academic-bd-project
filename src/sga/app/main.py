from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.db.database import engine, Base
from app.routers import auth, admin, docentes, estudiantes, acudientes
from sqlalchemy import text
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

api_app = FastAPI(title="SGA API", lifespan=None)
api_app.include_router(auth.router)
api_app.include_router(admin.router)
api_app.include_router(docentes.router)
api_app.include_router(estudiantes.router)
api_app.include_router(acudientes.router)

@api_app.exception_handler(Exception)
async def api_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(status_code=500, content={"detail": str(exc) if str(exc) else "Internal Server Error"})

app = FastAPI(
    title="Sistema de Gestión Académica",
    description="API REST para la gestión académica — DUALCOVE",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def root_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(status_code=500, content={"detail": str(exc) if str(exc) else "Internal Server Error"})

app.mount("/api", api_app)

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = os.path.join(static_dir, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(static_dir, path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        if not path or not os.path.splitext(path)[1]:
            default = os.path.join(static_dir, "index.html")
            if os.path.isfile(default):
                return FileResponse(default)
        raise HTTPException(status_code=404, detail="Not Found")
