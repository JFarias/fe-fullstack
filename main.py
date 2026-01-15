from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ALLOWED_ORIGINS
from app.services.homepage import build_homepage_payload

app = FastAPI(title="Fundamentos Economicos API", version="1.0.0")

# CORS
allow_origins = ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/homepage/v1")
def homepage_v1():
    return build_homepage_payload()
