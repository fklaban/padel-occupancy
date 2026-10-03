"""Sportelo (e.g. Padel Neridé) — public GraphQL behind the booking embed.

`reservations` returns every reservation (and lesson) of a court group in a
time window, past ones included. The venue advertises 00:00–24:00 opening
hours, which would make occupancy meaningless, so the hours we count come
from the venue config.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from ..core import BOOKED, FREE, TZ, CourtDay, Day, Venue, grid, mark, minutes, session

URL = "https://sportelo-reservation-embed.vercel.app/graphql"
QUERY = """
query R($input: ReservationsArgs!) {
  reservations(input: $input) {
    __typename
    ... on Reservation { timeFrom timeTo field { id } }
    ... on Lesson { timeFrom timeTo fields { id } }
  }
}
"""


def fetch(venue: Venue, day: date) -> Day:
    p = venue.params
    start = datetime(day.year, day.month, day.day, tzinfo=TZ)
    s = session()
    s.headers.update({"x-sport-center-subdomain": p["subdomain"], "x-platform": "embed"})
    r = s.post(URL, json={"query": QUERY, "variables": {"input": {
        "fieldGroupId": p["field_group"],
        "timeFrom": start.isoformat(),
        "timeTo": (start + timedelta(days=1)).isoformat(),
    }}}, timeout=30)
    r.raise_for_status()
    body = r.json()
    if body.get("errors"):
        raise RuntimeError(body["errors"][0]["message"])

    open_m, close_m = (minutes(t) for t in p["hours"])
    courts: Day = {cid: CourtDay(name, grid(open_m, close_m, FREE)) for cid, name in p["courts"].items()}
    for res in body["data"]["reservations"]:
        a = datetime.fromisoformat(res["timeFrom"].replace("Z", "+00:00")).astimezone(TZ)
        b = datetime.fromisoformat(res["timeTo"].replace("Z", "+00:00")).astimezone(TZ)
        begin = (a.date() - day).days * 1440 + a.hour * 60 + a.minute
        end = (b.date() - day).days * 1440 + b.hour * 60 + b.minute
        ids = [res["field"]["id"]] if res.get("field") else [f["id"] for f in res.get("fields") or []]
        for cid in ids:
            if cid in courts:
                mark(courts[cid].cells, begin, end - begin, BOOKED)
    return courts
