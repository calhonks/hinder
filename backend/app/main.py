import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import CORS_ORIGINS
from .db.session import init_db
from .routers.files import router as files_router
from .routers.profiles import router as profiles_router
from .routers.status import router as status_router
from .routers.matches import router as matches_router
from .routers.feedback import router as feedback_router
from .routers.intro import router as intro_router
from .routers.admin import router as admin_router
from .routers.brightdata import router as brightdata_router
from .routers.auth import router as auth_router


app = FastAPI(title="Hinder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"message": "Hinder API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"ok": True}


# Routers
app.include_router(files_router)
app.include_router(profiles_router)
app.include_router(status_router)
app.include_router(matches_router)
app.include_router(feedback_router)
app.include_router(intro_router)
app.include_router(admin_router)
app.include_router(brightdata_router)
app.include_router(auth_router)