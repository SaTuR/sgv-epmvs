from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.business import router as business_router
from app.api.finance import router as finance_router
from app.api.documents import router as documents_router
from app.api.reports import router as reports_router
from app.api.security_admin import router as security_router
from app.api.settings import router as settings_router
from app.config import settings
from app.db import db_health

app = FastAPI(title=settings.app_name, version="0.7.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)
app.include_router(business_router)
app.include_router(finance_router)
app.include_router(documents_router)
app.include_router(reports_router)
app.include_router(security_router)
app.include_router(settings_router)

@app.get("/api/health")
def health():
    ok=db_health()
    return {"status":"ok" if ok else "degraded","database":"ok" if ok else "error","application":settings.app_name}

@app.get("/api")
def api_root():
    return {"name":settings.app_name,"version":"0.7.0","project":"San Joaquín"}
