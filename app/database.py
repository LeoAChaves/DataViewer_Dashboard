import os
import asyncpg
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/weatherdb")


async def get_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)


_pool: asyncpg.Pool | None = None


async def init_db(pool: asyncpg.Pool):
    """Create tables and seed a default session if needed."""
    async with pool.acquire() as conn:
        # Sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Readings table  — one row per sensor reading
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id          BIGSERIAL,
                session_id  TEXT        NOT NULL REFERENCES sessions(id),
                topic       TEXT        NOT NULL,
                value       DOUBLE PRECISION NOT NULL,
                ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, ts)
            )
        """)

        # Try to enable TimescaleDB hypertable (optional — works without it too)
        try:
            await conn.execute("""
                SELECT create_hypertable('readings','ts',
                    if_not_exists => TRUE,
                    migrate_data  => TRUE)
            """)
        except Exception:
            pass  # Plain Postgres without TimescaleDB — still works fine

        # Index for fast session+topic queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_session_topic
            ON readings (session_id, topic, ts DESC)
        """)

        # Seed the default demo session
        await conn.execute("""
            INSERT INTO sessions (id) VALUES ('demo')
            ON CONFLICT DO NOTHING
        """)