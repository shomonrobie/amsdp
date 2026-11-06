"""AMSDP Queue Management Service — BR §24–§25, §30–§31."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

app = FastAPI(title="AMSDP Queue Management Service")
_queues_db: dict[str, list[dict]] = {}
_next_token: dict[str, int] = {}

class QueueEntryCreate(BaseModel):
    organization_id: str; branch_id: str; doctor_id: str; date: str
    patient_id: str; appointment_id: Optional[str] = None
    entry_source: str = "appointment"; notes: str = ""; added_by: str = ""

class QueueReorder(BaseModel): entry_ids: list[str]

class QueueAction(BaseModel):
    action: str; actor: str = ""; reason: str = ""

@app.get("/api/v1/queue")
def get_queue(
    organization_id: str = Query(...), branch_id: str = Query(...),
    doctor_id: str = Query(...), date: str = Query(...),
):
    key = f"{organization_id}:{branch_id}:{doctor_id}:{date}"
    entries = _queues_db.get(key, [])
    waiting = [e for e in entries if e["status"] not in ("served", "absent", "cancelled")]
    return {"date": date, "doctor_id": doctor_id, "waiting": len(waiting),
            "entries": sorted(waiting, key=lambda x: x["position"])}

@app.post("/api/v1/queue/enqueue", status_code=201)
def enqueue_patient(data: QueueEntryCreate):
    if data.entry_source not in ("appointment", "walk_in", "extra"):
        raise HTTPException(422, f"invalid entry_source: {data.entry_source}")
    key = f"{data.organization_id}:{data.branch_id}:{data.doctor_id}:{data.date}"
    n = _next_token.get(key, 0) + 1; _next_token[key] = n
    entry_id = str(uuid.uuid4())
    entry = {
        "queue_entry_id": entry_id, "position": n,
        "token": f"T-{data.doctor_id[:6]}-{n:03d}",
        "patient_id": data.patient_id,
        "appointment_id": data.appointment_id,
        "entry_source": data.entry_source, "status": "waiting",
        "status_history": [{"status": "waiting", "at": str(datetime.utcnow())}],
        "notes": data.notes, "added_by": data.added_by,
        "created_at": str(datetime.utcnow()),
    }
    _queues_db.setdefault(key, []).append(entry)
    return entry

@app.patch("/api/v1/queue/{entry_id}")
def queue_action(entry_id: str, data: QueueAction):
    entry = _find_entry(entry_id)
    if not entry: raise HTTPException(404)
    transitions = {
        "waiting": ["call", "mark_absent", "skip"],
        "called": ["mark_arrived", "skip", "mark_absent"],
        "arrived": ["complete_service", "skip"],
        "skipped": ["call", "mark_absent"],
    }
    allowed = transitions.get(entry["status"], [])
    if data.action not in allowed:
        raise HTTPException(422, f"cannot {data.action} from {entry['status']}")
    new_status = {
        "call": "called", "mark_arrived": "arrived",
        "mark_absent": "absent", "complete_service": "served",
        "skip": "skipped",
    }.get(data.action, entry["status"])
    entry["status_history"].append({
        "from": entry["status"], "to": new_status, "action": data.action,
        "actor": data.actor or "system", "reason": data.reason,
        "at": str(datetime.utcnow()),
    })
    entry["status"] = new_status
    return entry

@app.post("/api/v1/queue/reorder")
def reorder_queue(data: QueueReorder):
    ordered = data.entry_ids; found = 0
    for entries in _queues_db.values():
        for entry in entries:
            if entry["queue_entry_id"] in ordered:
                entry["position"] = ordered.index(entry["queue_entry_id"]) + 1
                found += 1
    return {"reordered": len(ordered), "matched": found}

@app.get("/api/v1/queue/history")
def queue_history(
    organization_id: str = Query(...), branch_id: str = Query(...),
    doctor_id: str = Query(...), date: str = Query(...),
    status: str = Query(None),
):
    key = f"{organization_id}:{branch_id}:{doctor_id}:{date}"
    entries = _queues_db.get(key, [])
    if status: entries = [e for e in entries if e["status"] == status]
    return sorted(entries, key=lambda x: x["position"])

def _find_entry(entry_id: str) -> dict | None:
    for entries in _queues_db.values():
        for entry in entries:
            if entry["queue_entry_id"] == entry_id: return entry
    return None