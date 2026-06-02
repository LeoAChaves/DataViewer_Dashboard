"""
Weather API — FastAPI application
──────────────────────────────────
Endpoints (100% compatible with the legacy PHP API):

  GET  /session/{session_id}              → list of topics
  GET  /data/{session_id}/{topic}         → raw readings
  POST /ingest                            → manual sensor push
  GET  /sessions                          → list all sessions
  POST /sessions/{session_id}             → create a new session
  GET  /                                  → dashboard (dataViewer.html)
  GET  /docs                              → auto-generated Swagger UI
"""

import asyncio
import asyncpg
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db, DATABASE_URL
from app.models import SessionResponse, TopicResponse, Reading, IngestPayload, TOPICS
from app.simulator import generate_readings


# ── State shared between background task and request handlers ─────────────────

_pool: asyncpg.Pool | None = None
_sim_state: dict = {}           # persists simulator continuity across intervals


# ── Background task: generate data every 5 minutes ───────────────────────────

async def _simulation_loop(pool: asyncpg.Pool):
    """Inserts one reading per topic every 5 minutes for every session."""
    while True:
        try:
            now = datetime.now(timezone.utc)
            readings = generate_readings(now, _sim_state)

            async with pool.acquire() as conn:
                sessions = await conn.fetch("SELECT id FROM sessions")
                rows = [
                    (s["id"], topic, value, now)
                    for s in sessions
                    for topic, value in readings.items()
                ]
                await conn.executemany(
                    "INSERT INTO readings (session_id, topic, value, ts) VALUES ($1,$2,$3,$4)",
                    rows,
                )
        except Exception as exc:
            print(f"[simulator] error: {exc}")

        # Sleep until the next 5-minute boundary
        await asyncio.sleep(300)


# ── Backfill: populate the last 7 days on first run ──────────────────────────

async def _backfill(pool: asyncpg.Pool):
    """If the DB has no readings, generate 7 days of historical data instantly."""
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM readings")
        if count > 0:
            return

        print("[backfill] Generating 7 days of historical data …")
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=7)

        # Walk every 5-minute slot
        state: dict = {}
        slot = start
        rows: list[tuple] = []
        sessions = await conn.fetch("SELECT id FROM sessions")

        while slot <= now:
            readings = generate_readings(slot, state)
            for s in sessions:
                for topic, value in readings.items():
                    rows.append((s["id"], topic, value, slot))
            slot += timedelta(minutes=5)

        # Bulk insert in chunks of 5000
        chunk = 5000
        for i in range(0, len(rows), chunk):
            await conn.executemany(
                "INSERT INTO readings (session_id, topic, value, ts) VALUES ($1,$2,$3,$4)",
                rows[i : i + chunk],
            )
        print(f"[backfill] Done — {len(rows):,} rows inserted.")


# ── App lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    await init_db(_pool)
    await _backfill(_pool)
    asyncio.create_task(_simulation_loop(_pool))
    yield
    await _pool.close()


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Weather Sensor API",
    description="Drop-in replacement for the legacy PHP API, with simulated sensor data.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files and dashboard ───────────────────────────────────────────────

# Serve static assets
if Path("src").exists():
    app.mount("/src", StaticFiles(directory="src"), name="src")

if Path("js").exists():
    app.mount("/js", StaticFiles(directory="js"), name="js")

# Serve the dashboard
@app.get("/")
@app.get("/dashboard")
async def serve_dashboard():
    """Serve the main dashboard (dataViewer.html)"""
    if Path("dataViewer.html").exists():
        return FileResponse("dataViewer.html")
    raise HTTPException(404, "Dashboard file not found. Make sure dataViewer.html exists in the root directory.")

# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", include_in_schema=False)
async def health():
    try:
        async with _pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _require_session(session_id: str) -> None:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM sessions WHERE id=$1", session_id)
    if not row:
        raise HTTPException(404, f"Session '{session_id}' not found")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get(
    "/session/{session_id}",
    response_model=SessionResponse,
    summary="List topics available for a session",
    tags=["Legacy compatible"],
)
async def get_session(session_id: str):
    """
    Replaces `getsession.php?session=X`.
    Returns `{ success, result: [topic, ...] }`.
    """
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM sessions WHERE id=$1", session_id)
        if not row:
            raise HTTPException(404, f"Session '{session_id}' not found or has no data yet")
        topics = await conn.fetch(
            "SELECT DISTINCT topic FROM readings WHERE session_id=$1 ORDER BY topic",
            session_id,
        )
    return SessionResponse(success=True, result=[t["topic"] for t in topics])


@app.get(
    "/data/{session_id}/{topic}",
    response_model=TopicResponse,
    summary="Get raw readings for a topic",
    tags=["Legacy compatible"],
)
async def get_topic_data(
    session_id: str,
    topic: str,
    limit: int = Query(default=2016, ge=1, le=50000, description="Max rows returned"),
):
    """
    Replaces `gettopic.php?session=X&topic=Y`.
    Returns `{ success, result: [{timestamp, data}, ...] }`.
    `timestamp` is a Unix epoch in **seconds** to match the legacy format.
    """
    await _require_session(session_id)
    if topic not in TOPICS:
        raise HTTPException(400, f"Unknown topic '{topic}'. Valid: {list(TOPICS)}")

    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT EXTRACT(EPOCH FROM ts)::BIGINT AS ts, value
            FROM readings
            WHERE session_id=$1 AND topic=$2
            ORDER BY ts DESC
            LIMIT $3
            """,
            session_id, topic, limit,
        )

    result = [Reading(timestamp=r["ts"], data=str(r["value"])) for r in rows]
    return TopicResponse(success=True, result=result)


@app.post(
    "/ingest",
    summary="Push a sensor reading manually",
    tags=["Ingestion"],
    status_code=201,
)
async def ingest(payload: IngestPayload):
    """
    Accepts a single reading from a physical sensor (or any HTTP client).
    Body: `{ session_id, topic, value }`.
    """
    await _require_session(payload.session_id)
    if payload.topic not in TOPICS:
        raise HTTPException(400, f"Unknown topic '{payload.topic}'")

    async with _pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO readings (session_id, topic, value, ts) VALUES ($1,$2,$3,NOW())",
            payload.session_id, payload.topic, payload.value,
        )
    return {"success": True, "message": "Reading saved"}


@app.get("/sessions", summary="List all sessions", tags=["Management"])
async def list_sessions():
    async with _pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, created_at FROM sessions ORDER BY created_at DESC")
    return {"sessions": [{"id": r["id"], "created_at": r["created_at"].isoformat()} for r in rows]}


@app.post("/sessions/{session_id}", summary="Create a new session", tags=["Management"], status_code=201)
async def create_session(session_id: str):
    async with _pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM sessions WHERE id=$1", session_id)
        if existing:
            raise HTTPException(409, f"Session '{session_id}' already exists")
        await conn.execute("INSERT INTO sessions (id) VALUES ($1)", session_id)
    return {"success": True, "session_id": session_id}