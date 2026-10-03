"""Shared types and helpers.

Every adapter turns a booking system's view of one day into the same shape:
a dict of courts, each with a 30-minute grid of cells marked "free" or
"booked". Only cells inside opening hours are included.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

import requests

TZ = ZoneInfo("Europe/Prague")
CELL = 30  # minutes
FREE, BOOKED = "free", "booked"

UA = (
    "padel-occupancy/1.0 (+https://github.com/fklaban/padel-occupancy; "
    "occupancy statistics, a few requests per hour)"
)


@dataclass
class Venue:
    id: str
    name: str
    platform: str
    params: dict = field(default_factory=dict)
    # Set when a venue can't be scraped; the reason is shown in the report.
    disabled: str | None = None
    # True when the booking system still shows reservations for times that
    # already started, so past cells can be trusted on first sight.
    shows_past: bool = False


@dataclass
class CourtDay:
    name: str
    cells: dict[str, str]  # "HH:MM" -> FREE | BOOKED


Day = dict[str, CourtDay]  # court id -> CourtDay


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    s.headers["Accept-Language"] = "cs,en;q=0.8"
    return s


def hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def minutes(t: str) -> int:
    h, m = t.split(":")[:2]
    return int(h) * 60 + int(m)


def grid(open_min: int, close_min: int, status: str = BOOKED) -> dict[str, str]:
    """All cells from opening to closing, prefilled with `status`."""
    return {hhmm(m): status for m in range(open_min, close_min, CELL)}


def mark(cells: dict[str, str], start: int, duration: int, status: str) -> None:
    """Set every existing cell in [start, start+duration) to `status`."""
    for m in range(start - start % CELL, start + duration, CELL):
        key = hhmm(m)
        if key in cells:
            cells[key] = status


def now_local() -> datetime:
    return datetime.now(TZ)


def is_past(day: date, cell: str, now: datetime) -> bool:
    start = datetime(day.year, day.month, day.day, tzinfo=TZ).replace(
        hour=minutes(cell) // 60, minute=minutes(cell) % 60
    )
    return start <= now
