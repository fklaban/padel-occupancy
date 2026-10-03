"""jdemenato.cz / CentiSport (Wilson Tenis Centrum).

The public "reservation calendar overview" is a table with one column per
court and a row per half hour. Cells carry classes like `timetableFree`,
`timetableOccupied` and `time480` (minutes since midnight) and use rowspan
for longer blocks. Past cells keep their status. Only today is reachable
without following session-bound links, which is all we need.
"""

from __future__ import annotations

import re
from datetime import date

from bs4 import BeautifulSoup

from ..core import BOOKED, FREE, CourtDay, Day, Venue, describe, hhmm, now_local, session

URL = "https://jdemenato.cz/reservation/{slug}/reservationcalendaroverview"
TIME = re.compile(r"^time(\d+)$")


def _status(classes: list[str]) -> str | None:
    if "timetableFree" in classes:
        return FREE
    if any(c.startswith("timetable") and ("Occupied" in c or "Lesson" in c or "Reserv" in c) for c in classes):
        return BOOKED
    return None  # closed / unavailable


def fetch(venue: Venue, day: date) -> Day:
    if day != now_local().date():
        return {}
    r = session().get(URL.format(slug=venue.params["slug"]), timeout=30)
    table = BeautifulSoup(r.text, "html.parser").find("table", class_="verticalTimetable")
    if table is None:
        raise RuntimeError(f"jdemenato timetable not found: {describe(r)}")

    rows = table.find_all("tr", recursive=False) or table.find_all("tr")
    names = [th.get_text(" ", strip=True) for th in rows[0].find_all("th", class_="serviceTop")]
    courts: Day = {str(i): CourtDay(n, {}) for i, n in enumerate(names)}
    pending = [0] * len(names)  # half-hour rows still covered by a rowspan

    for tr in rows[1:]:
        cells = iter(tr.find_all("td", recursive=False))
        for col in range(len(names)):
            if pending[col]:
                pending[col] -= 1
                continue
            td = next(cells, None)
            if td is None:
                break
            classes = td.get("class", [])
            span = int(td.get("rowspan", 1))
            pending[col] = span - 1
            start = next((int(m.group(1)) for c in classes if (m := TIME.match(c))), None)
            status = _status(classes)
            if start is None or status is None:
                continue
            for k in range(span):
                courts[str(col)].cells[hhmm(start + 30 * k)] = status

    pattern = re.compile(venue.params.get("court_filter", "padel"), re.I)
    return {k: v for k, v in courts.items() if pattern.search(v.name)}
