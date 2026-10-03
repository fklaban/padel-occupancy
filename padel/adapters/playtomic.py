"""Playtomic (playtomic.com).

The club page embeds the court list and opening hours; the availability
endpoint returns only *free* bookable slots, with start times in UTC.
Everything inside opening hours that no free slot covers counts as booked.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone

from ..core import BOOKED, FREE, TZ, CourtDay, Day, Venue, describe, grid, mark, minutes, session

BASE = "https://playtomic.com"
WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]


def _club_info(s, slug: str) -> dict:
    r = s.get(f"{BASE}/clubs/{slug}", timeout=30)
    html = r.text.replace('\\"', '"')
    resources = re.search(r'"resources":(\[.*?\]),"opening_hours"', html)
    hours = re.search(r'"opening_hours":(\{(?:[^{}]|\{[^{}]*\})*\})', html)
    if not resources or not hours:
        raise RuntimeError(f"no courts/opening hours on Playtomic page: {describe(r)}")
    return {"resources": json.loads(resources.group(1)), "hours": json.loads(hours.group(1))}


def fetch(venue: Venue, day: date) -> Day:
    s = session()
    info = _club_info(s, venue.params["slug"])
    hours = info["hours"].get(WEEKDAYS[day.weekday()])
    if not hours:
        return {}
    open_m, close_m = minutes(hours["opening_time"]), minutes(hours["closing_time"])
    if close_m <= open_m:  # closes at midnight
        close_m += 24 * 60

    courts: Day = {
        r["resourceId"]: CourtDay(r["name"], grid(open_m, close_m, BOOKED))
        for r in info["resources"]
        if r.get("sport") == "PADEL"
    }

    r = s.get(
        f"{BASE}/api/clubs/availability",
        params={"tenant_id": venue.params["tenant_id"], "date": day.isoformat(), "sport_id": "PADEL"},
        timeout=30,
    )
    r.raise_for_status()
    for res in r.json():
        court = courts.get(res["resource_id"])
        if not court:
            continue
        for slot in res["slots"]:
            utc = datetime.fromisoformat(f"{res['start_date']}T{slot['start_time']}").replace(tzinfo=timezone.utc)
            local = utc.astimezone(TZ)
            if local.date() != day:
                continue
            mark(court.cells, local.hour * 60 + local.minute, slot["duration"], FREE)
    return courts
