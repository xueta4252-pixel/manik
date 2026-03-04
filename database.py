import aiosqlite
from datetime import date, datetime, timedelta
from typing import Optional
from config import DEFAULT_SLOTS, MONTH_AHEAD, DB_PATH


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS working_days (
                date      TEXT PRIMARY KEY,
                is_closed INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS time_slots (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date      TEXT    NOT NULL,
                time      TEXT    NOT NULL,
                is_booked INTEGER DEFAULT 0,
                UNIQUE(date, time)
            );
            CREATE TABLE IF NOT EXISTS bookings (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                username     TEXT,
                name         TEXT    NOT NULL,
                phone        TEXT    NOT NULL,
                date         TEXT    NOT NULL,
                time         TEXT    NOT NULL,
                created_at   TEXT    DEFAULT (datetime('now','localtime')),
                reminded_24h INTEGER DEFAULT 0,
                reminded_5h  INTEGER DEFAULT 0
            );
        """)
        await db.commit()


async def add_working_day(d: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO working_days (date, is_closed) VALUES (?, 0)", (d,)
        )
        for slot in DEFAULT_SLOTS:
            await db.execute(
                "INSERT OR IGNORE INTO time_slots (date, time, is_booked) VALUES (?, ?, 0)",
                (d, slot)
            )
        await db.commit()


async def close_day(d: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO working_days (date, is_closed) VALUES (?, 1) "
            "ON CONFLICT(date) DO UPDATE SET is_closed = 1", (d,)
        )
        await db.commit()


async def get_available_dates() -> list[str]:
    today = str(date.today())
    end = str(date.today() + timedelta(days=MONTH_AHEAD))
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT DISTINCT ts.date
            FROM time_slots ts
            JOIN working_days wd ON wd.date = ts.date
            WHERE ts.is_booked = 0
              AND wd.is_closed = 0
              AND ts.date >= ?
              AND ts.date <= ?
            ORDER BY ts.date
        """, (today, end))
        rows = await cursor.fetchall()
    return [r["date"] for r in rows]


async def get_all_working_days_in_range() -> list[str]:
    today = str(date.today())
    end = str(date.today() + timedelta(days=MONTH_AHEAD))
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT date FROM working_days WHERE date >= ? AND date <= ? ORDER BY date",
            (today, end)
        )
        rows = await cursor.fetchall()
    return [r["date"] for r in rows]


async def add_slot(d: str, t: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO time_slots (date, time, is_booked) VALUES (?, ?, 0)", (d, t)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def delete_slot(d: str, t: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM time_slots WHERE date = ? AND time = ? AND is_booked = 0", (d, t)
        )
        await db.commit()


async def get_free_slots(d: str) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT time FROM time_slots WHERE date = ? AND is_booked = 0 ORDER BY time", (d,)
        )
        rows = await cursor.fetchall()
    return [r["time"] for r in rows]


async def get_all_slots(d: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT time, is_booked FROM time_slots WHERE date = ? ORDER BY time", (d,)
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def mark_slot_booked(d: str, t: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE time_slots SET is_booked = 1 WHERE date = ? AND time = ?", (d, t)
        )
        await db.commit()


async def mark_slot_free(d: str, t: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE time_slots SET is_booked = 0 WHERE date = ? AND time = ?", (d, t)
        )
        await db.commit()


async def is_slot_free(d: str, t: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT is_booked FROM time_slots WHERE date = ? AND time = ?", (d, t)
        )
        row = await cursor.fetchone()
    if not row:
        return False
    return row["is_booked"] == 0


async def create_booking(
    user_id: int, username: Optional[str],
    name: str, phone: str, d: str, t: str
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO bookings (user_id, username, name, phone, date, time) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, name, phone, d, t)
        )
        booking_id = cursor.lastrowid
        await db.commit()
    await mark_slot_booked(d, t)
    return booking_id


async def get_user_active_bookings(user_id: int) -> list[dict]:
    today = str(date.today())
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM bookings WHERE user_id = ? AND date >= ? ORDER BY date, time",
            (user_id, today)
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_booking_by_id(booking_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM bookings WHERE id = ?", (booking_id,)
        )
        row = await cursor.fetchone()
    return dict(row) if row else None


async def get_bookings_for_date(d: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM bookings WHERE date = ? ORDER BY time", (d,)
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def delete_booking(booking_id: int) -> None:
    b = await get_booking_by_id(booking_id)
    if not b:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        await db.commit()
    await mark_slot_free(b["date"], b["time"])


async def get_pending_reminders(hours: int) -> list[dict]:
    from datetime import datetime, timedelta
    now = datetime.now()
    target = now + timedelta(hours=hours)
    window_start = (target - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M")
    window_end = (target + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M")
    col = "reminded_24h" if hours == 24 else "reminded_5h"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(f"""
            SELECT * FROM bookings
            WHERE {col} = 0
              AND (date || ' ' || time) >= ?
              AND (date || ' ' || time) <= ?
        """, (window_start, window_end))
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def mark_reminded(booking_id: int, hours: int) -> None:
    col = "reminded_24h" if hours == 24 else "reminded_5h"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE bookings SET {col} = 1 WHERE id = ?", (booking_id,)
        )
        await db.commit()
