"""AMSDP Audit Service — centralized event recording."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

app = FastAPI(title="AMSDP Audit Service")
_audit_db: dict[str, list[dict]] = {}

class AuditEvent(BaseModel):
    service: str
    organization_id: str
    action: str
    target_type: str
    target_id: str
    actor_id: str
    actor_role: str
    before: Optional[dict] = None
    after: Optional[dict] = None
    reason: str = ""

@app.post("/api/v1/audit", status_code=201)
def record_event(data: AuditEvent):
    event = {**data.dict(), "event_id": str(uuid.uuid4()),
             "timestamp": str(datetime.utcnow())}
    _audit_db.setdefault(data.target_id, []).append(event)
    return {"event_id": event["event_id"]}

@app.get("/api/v1/audit/{target_id}")
def get_events(target_id: str, action: str = Query(None), actor: str = Query(None)):
    events = _audit_db.get(target_id, [])
    if action: events = [e for e in events if e["action"] == action]
    if actor: events = [e for e in events if e["actor_id"] == actor]
    return sorted(events, key=lambda x: x["timestamp"], reverse=True)

@app.get("/api/v1/audit/organization/{org_id}")
def get_org_events(org_id: str):
    events = []
    for evts in _audit_db.values():
        for e in evts:
            if e["organization_id"] == org_id: events.append(e)
    return sorted(events, key=lambda x: x["timestamp"], reverse=True)