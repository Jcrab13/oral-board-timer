from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from datetime import datetime, timedelta
from uuid import uuid4

app = FastAPI(title="Oral Board Timer")

# in-memory store: { (userId, caseNumber): timer }
timers = {}

class Timer(BaseModel):
    timerId: str
    userId: str
    caseNumber: int
    durationSeconds: int
    remainingSeconds: int
    status: str
    startedAt: datetime

def tick():
    """Decrease remaining seconds once per call."""
    now = datetime.utcnow()
    for key, t in list(timers.items()):
        if t.status == "running":
            elapsed = (now - t.startedAt).total_seconds()
            new_remaining = max(t.durationSeconds - int(elapsed), 0)
            t.remainingSeconds = new_remaining
            if new_remaining == 0:
                t.status = "expired"

@app.post("/api/v1/users/{userId}/cases/{caseNumber}/timer", status_code=201)
def start_case_timer(
    userId: str,
    caseNumber: int = Path(..., ge=1, le=4),
    durationSeconds: int = 420,
):
    tick()
    key = (userId, caseNumber)
    if key in timers and timers[key].status == "running":
        raise HTTPException(409, "Timer already running")
    timer = Timer(
        timerId=str(uuid4()),
        userId=userId,
        caseNumber=caseNumber,
        durationSeconds=durationSeconds,
        remainingSeconds=durationSeconds,
        status="running",
        startedAt=datetime.utcnow(),
    )
    timers[key] = timer
    return timer

@app.get("/api/v1/users/{userId}/cases/{caseNumber}/timer")
def get_case_timer(userId: str, caseNumber: int = Path(..., ge=1, le=4)):
    tick()
    key = (userId, caseNumber)
    if key not in timers:
        raise HTTPException(404, "Timer not found")
    return timers[key]

@app.delete("/api/v1/users/{userId}/cases/{caseNumber}/timer", status_code=204)
def cancel_case_timer(userId: str, caseNumber: int = Path(..., ge=1, le=4)):
    key = (userId, caseNumber)
    if key in timers:
        timers[key].status = "canceled"
