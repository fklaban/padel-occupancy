"""bookaball (e.g. Padel Džus) — the public guest booking wizard.

Anonymous visitors can step through /cs/bookings/create: pick the location
(which lists its courts), pick a court, then ask which start times are
available for a 60-minute booking. Nothing is ever booked. A half hour is
free if some available 60-minute start covers it; the rest of the listed
day counts as booked. Past times come back `disabled`, so past cells are
never overwritten.
"""

from __future__ import annotations

import re
from datetime import date

from ..core import BOOKED, FREE, CourtDay, Day, Venue, describe, grid, mark, minutes, session

DURATION = 60


def fetch(venue: Venue, day: date) -> Day:
    p = venue.params
    base = f"https://{p['host']}"
    s = session()
    page = s.get(f"{base}/cs/bookings/create", timeout=30)
    token = re.search(r'<meta\s+name="csrf-token"\s+content="([^"]+)"', page.text)
    if not token:
        raise RuntimeError(f"bookaball CSRF token not found: {describe(page)}")
    s.headers.update({"Accept": "application/json", "X-CSRF-TOKEN": token.group(1),
                      "X-Requested-With": "XMLHttpRequest"})

    def post(path: str, body: dict):
        r = s.post(f"{base}/api/{path}", json=body, timeout=30)
        r.raise_for_status()
        return r.json()

    s.get(f"{base}/api/bookings/reset", timeout=30).raise_for_status()
    location = post("bookings/create", {"step": "STEP_LOCATION", "location_id": p["location"]})
    padel = sorted((c for c in location["prebooking"]["location"]["courts"] if c["sport_type"] == "padel"),
                   key=lambda c: c.get("sort_order") or c["id"])

    courts: Day = {}
    for i, c in enumerate(padel, 1):
        post("bookings/create", {"step": "STEP_SIZE", "sport_type": "padel", "court_size": c["size"],
                                 "court_count": 1, "court_type": c["type"], "court_id": c["id"]})
        times = post("bookings/times", {"date": day.isoformat(), "duration": DURATION})
        if not times:
            continue
        starts = [minutes(t["time"]) for t in times]
        cells = grid(min(starts), max(starts) + DURATION, BOOKED)
        for t in times:
            if t["available"] and not t["disabled"]:
                mark(cells, minutes(t["time"]), DURATION, FREE)
        courts[str(c["id"])] = CourtDay(f"Kurt {i}", cells)
    return courts
