import aiosqlite
import os
from contextlib import asynccontextmanager

os.makedirs("data", exist_ok=True)
DB = "data/void.db"


@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def setup_database():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            start_time TEXT,
            end_time TEXT,
            start_ts INTEGER,
            end_ts INTEGER,
            team_size INTEGER,
            ctftime_link TEXT,
            channel_id INTEGER,
            notified INTEGER DEFAULT 0
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS interested(
            event_id INTEGER,
            user_id INTEGER
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS event_users(
            event_id INTEGER,
            user_id INTEGER,
            role TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS event_selected(
            event_id INTEGER,
            user_id INTEGER
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS clock_sessions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            user_id INTEGER,
            clock_in_time INTEGER,
            clock_out_time INTEGER,
            is_active INTEGER DEFAULT 1
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS activity_proofs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            user_id INTEGER,
            event_id INTEGER,
            proof_url TEXT,
            challenge_type TEXT,
            submitted_at INTEGER
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_messages(
            channel_id INTEGER,
            message_id INTEGER
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS player_stats(
            user_id INTEGER,
            event_id INTEGER,
            total_minutes INTEGER DEFAULT 0,
            proof_count INTEGER DEFAULT 0,
            flags_captured INTEGER DEFAULT 0,
            level TEXT DEFAULT 'rookie'
        )
        """)
        try:
            await db.execute(
                "ALTER TABLE events ADD COLUMN notified INTEGER DEFAULT 0")
        except:
            pass
        await db.commit()