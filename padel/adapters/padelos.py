"""padelos.co / ClubOS (Padel Powers).

`searchByDate` returns, for every club of a company, the *free* slots with the
courts available in each. Fully booked courts don't appear at all, so the
court list and opening hours come from the venue config.
"""

from __future__ import annotations

from datetime import date

from ..core import BOOKED, FREE, CourtDay, Day, Venue, grid, mark, minutes, session

URL = "https://api.padelos.co/customers/searchByDate"


def fetch(venue: Venue, day: date) -> Day:
    p = venue.params
    s = session()
    s.headers.update(
        {
            "Accept": "application/json",
            "x-clubos-channel": "CLUBOS-WEB",
            "x-clubos-domain": "PADELOSCO",
            "x-clubos-company": str(p["company"]),
            "version": "2.4",
        }
    )
    body = {k: "" for k in ("courtType", "courtSize", "courtTurf", "courtFeature", "searchTerm", "limit", "offset", "type")}
    r = s.post(URL, json={"date": day.isoformat(), "sport": "padel", **body}, timeout=60)
    r.raise_for_status()
    data = r.json()["data"]
    club = next((c for c in data if str(c["id"]) == str(p["club"])), None)
    if club is None:
        raise RuntimeError(f"club {p['club']} missing from padelos response")

    open_m, close_m = (minutes(t) for t in p["hours"])
    courts: Day = {cid: CourtDay(name, grid(open_m, close_m, BOOKED)) for cid, name in p["courts"].items()}
    for option in club.get("availability", []):
        for slot in option["slots"]:
            start = minutes(slot["startTime"])
            duration = minutes(slot["endTime"]) - start
            for c in slot["courts"]:
                if c["id"] in courts:
                    mark(courts[c["id"]].cells, start, duration, FREE)
    return courts
