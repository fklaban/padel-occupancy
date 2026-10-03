"""CourtyONE (e.g. One Padel Zličín) — public Next.js server action.

The club's /book page embeds the court list and loads data through Next.js
server actions. One of them, `fetchPublicDayOccupancyAction`, returns every
court's booked blocks for a day (past ones included). Action IDs change with
each deploy, so we look the ID up by name in the page's JS chunks each run.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime

from ..core import BOOKED, FREE, TZ, CourtDay, Day, Venue, describe, grid, mark, minutes, session

ACTION = "fetchPublicDayOccupancyAction"
CHUNKS = re.compile(r'/_next/static/chunks/[A-Za-z0-9_.~-]+\.js')
REF = re.compile(r'createServerReference\)\("([0-9a-f]{40,})",[^)]*?"(\w+)"\)')


def _local_minutes(iso: str, day: date) -> int:
    t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TZ)
    return (t.date() - day).days * 1440 + t.hour * 60 + t.minute


def fetch(venue: Venue, day: date) -> Day:
    p = venue.params
    base = f"https://{p['host']}"
    s = session()
    page = s.get(f"{base}/book", timeout=30)
    html = page.text
    props = html.replace('\\"', '"')
    m = re.search(r'"courts":(\[\{.*?\}\]),"floorPlan"', props)
    if not m:
        raise RuntimeError(f"court list not found: {describe(page)}")
    court_list = [c for c in json.loads(m.group(1)) if "PADEL" in (c.get("surfaceKind") or "")]

    action = None
    for path in sorted(set(CHUNKS.findall(html))):
        js = s.get(base + path, timeout=30).text
        action = next((aid for aid, name in REF.findall(js) if name == ACTION), None)
        if action:
            break
    if not action:
        raise RuntimeError(f"{ACTION} not found in page scripts")

    r = s.post(
        f"{base}/book",
        headers={"Accept": "text/x-component", "Next-Action": action, "Content-Type": "text/plain;charset=UTF-8"},
        data=json.dumps([{"tenantSlug": p["tenant"], "venueSlug": p["venue"], "ymd": day.isoformat(), "durationMinutes": 60}]),
        timeout=30,
    )
    r.raise_for_status()
    # RSC stream: one "<id>:<json>" per line; the action result is the line whose JSON has "occupancy".
    result = next((json.loads(line.split(":", 1)[1]) for line in r.text.splitlines()
                   if '"occupancy"' in line), None)
    if not result or not result.get("ok"):
        raise RuntimeError(f"unexpected {ACTION} response: {r.text[:200]!r}")

    open_m, close_m = (minutes(t) for t in p["hours"])
    courts: Day = {c["id"]: CourtDay(c.get("publicName") or c["name"], grid(open_m, close_m, FREE)) for c in court_list}
    for entry in result["occupancy"]:
        court = courts.get(entry["courtId"])
        if not court:
            continue
        for b in entry["blocks"]:
            start = _local_minutes(b["startsAt"], day)
            mark(court.cells, start, _local_minutes(b["endsAt"], day) - start, BOOKED)
    return courts
