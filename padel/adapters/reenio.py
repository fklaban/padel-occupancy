"""Reenio (e.g. Areál Císařská louka).

`/api/Term/List` returns today's bookable "events" per service with a total
capacity (number of courts) and every reservation's UTC span and capacity.
Courts aren't individually identified, so the booked count per half hour is
spread over virtual courts "Court 1..N" (fine for occupancy, not for
per-court stats). Past reservations stay listed.
"""

from __future__ import annotations

from datetime import date, datetime

from ..core import BOOKED, TZ, CourtDay, Day, Venue, grid, hhmm, minutes, now_local, session


def _local_minutes(iso: str, day: date) -> int:
    t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TZ)
    return (t.date() - day).days * 24 * 60 + t.hour * 60 + t.minute


def fetch(venue: Venue, day: date) -> Day:
    if day != now_local().date():
        return {}
    p = venue.params
    r = session().post(
        f"https://{p['slug']}.reenio.cz/cs/api/Term/List",
        json={"date": f"{day.isoformat()}T00:00:00", "endDate": None, "viewMode": "1-day", "page": None,
              "filter": None, "includeColors": False, "findNearestAvailable": False},
        timeout=30,
    )
    r.raise_for_status()
    events = [
        e for e in r.json()["data"]["events"]
        if any(p["service"].lower() in (res["service"]["name"] or "").lower() for res in e["eventResources"])
    ]
    if not events:
        return {}
    event = events[0]
    spans = [(_local_minutes(x["start"], day), _local_minutes(x["end"], day), x["capacity"]) for x in event["reservations"]]

    open_m, close_m = (minutes(t) for t in p["hours"])
    open_m = min([open_m] + [s for s, _, _ in spans])
    close_m = max([close_m] + [e for _, e, _ in spans])
    taken = {m: 0 for m in range(open_m - open_m % 30, close_m, 30)}
    for start, end, cap in spans:
        for m in taken:
            if start < m + 30 and end > m:
                taken[m] += cap

    n = event["maxCapacity"]
    courts: Day = {str(i): CourtDay(f"Court {i}", grid(open_m, close_m, "free")) for i in range(1, n + 1)}
    for m, k in taken.items():
        for i in range(1, min(k, n) + 1):
            courts[str(i)].cells[hhmm(m)] = BOOKED
    return courts
