"""iSportSystem — public JSON endpoint `/api/get-times.php`.

The HTML booking pages sit behind a Cloudflare challenge, but this endpoint
is served directly. It returns, for one sport and day, every lane (court)
with a map of 30-minute UNIX timestamps -> 0 (free) / 1 (taken). Only
opening hours are listed, and `event_info` labels taken half hours
("Obsazeno", or a closure such as "Zavřeno"/"Údržba kurtů"). Past half hours
read as free, so past cells are never overwritten (`shows_past=False`).
"""

from __future__ import annotations

from datetime import date, datetime

from ..core import BOOKED, FREE, TZ, CourtDay, Day, Venue, describe, hhmm, session

# Labels on taken half hours that mean "closed", not "booked".
CLOSED = ("zavřeno", "uzavřeno", "údržba", "mimo provoz", "closed")


def fetch(venue: Venue, day: date) -> Day:
    p = venue.params
    r = session().get(
        f"https://{p['host']}.isportsystem.cz/api/get-times.php",
        params={"date": day.strftime("%Y%m%d"), "id_sport": p["sport"]},
        headers={"Accept": "application/json"},
        timeout=30,
    )
    try:
        lanes = r.json()
    except ValueError:
        raise RuntimeError(f"iSportSystem API did not return JSON: {describe(r)}") from None

    exclude = [x.lower() for x in p.get("exclude", [])]
    courts: Day = {}
    for lane in lanes:
        name = lane["lane_name"]
        if any(x in name.lower() for x in exclude):
            continue
        labels = lane.get("event_info") or {}
        cells = {}
        for ts, taken in lane["times"].items():
            t = datetime.fromtimestamp(int(ts), TZ)
            if t.date() != day:
                continue
            if int(taken) and any(w in labels.get(ts, "").lower() for w in CLOSED):
                continue  # maintenance / closure: not sellable, so not part of capacity
            cells[hhmm(t.hour * 60 + t.minute)] = BOOKED if int(taken) else FREE
        if cells:
            courts[str(lane["lane_id"])] = CourtDay(name, cells)
    return courts
