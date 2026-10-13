"""
FastAPI REST API Server for Hla Compatibility Matcher.
"""
import os
import hmac
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor


def require_api_token(authorization: str | None = Header(default=None)):
    """Require an operator-supplied bearer token for any sensitive API route."""
    token = os.getenv("API_ACCESS_TOKEN", "")
    if not token:
        raise HTTPException(status_code=503, detail="API_ACCESS_TOKEN must be configured")
    expected = "Bearer " + token
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Invalid API credentials", headers={"WWW-Authenticate": "Bearer"})


supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Hla Compatibility Matcher API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "hla-compatibility-matcher", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload, _auth: None = Depends(require_api_token)):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Sensitive identifier rejected")
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest, _auth: None = Depends(require_api_token)):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=422, detail="Sensitive identifier rejected")


@app.get("/api/audit/logs")
def api_audit_logs(_auth: None = Depends(require_api_token)):
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
