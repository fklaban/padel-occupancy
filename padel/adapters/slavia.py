"""SK Slavia Praha Padel — own reservation system (rezervace.padelslavia.cz).

The public page shows today's table: one column per court, one row per half
hour, cells classed `volno` (free) or `obsazeno` (taken), with rowspans for
longer bookings. Anonymous visitors only see today.
"""

from __future__ import annotations

from datetime import date

from bs4 import BeautifulSoup

from ..core import BOOKED, FREE, CourtDay, Day, Venue, now_local, session

URL = "https://rezervace.padelslavia.cz/"


def fetch(venue: Venue, day: date) -> Day:
    if day != now_local().date():
        return {}
    soup = BeautifulSoup(session().get(URL, timeout=30).text, "html.parser")
    table = soup.select_one("section.tabulka-rezervace table") or soup.find("table")
    if table is None:
        raise RuntimeError("Slavia reservation table not found")

    names = [th.get_text(strip=True) for th in table.select("thead th")][1:]
    courts: Day = {str(i): CourtDay(n, {}) for i, n in enumerate(names)}
    skip = [0] * len(names)  # rows still covered by a rowspan, per column

    for tr in table.select("tbody tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        time = tds[0].get_text(strip=True)
        cells = iter(tds[1:])
        for col in range(len(names)):
            if skip[col]:
                skip[col] -= 1
                prev = courts[str(col)].cells
                prev[time] = list(prev.values())[-1]
                continue
            td = next(cells, None)
            if td is None:
                break
            classes = td.get("class", [])
            status = FREE if "volno" in classes else BOOKED if "obsazeno" in classes else None
            if status:
                courts[str(col)].cells[time] = status
            skip[col] = int(td.get("rowspan", 1)) - 1

    pattern = venue.params.get("exclude")
    if pattern:
        courts = {k: v for k, v in courts.items() if pattern.lower() not in v.name.lower()}
    return courts
