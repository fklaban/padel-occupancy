"""Clubspire (e.g. Sky Sport City).

The public day timeline has one row per court (`tr[data-row-id]`, grouped by
activity via `data-parent-row-id`) and one cell per hour classed `can_book`,
`full`, `blocked` or `disabled` (closed). Partly booked hours are `zoom`
cells holding a small table of 15-minute sub-cells. A half hour counts as
free only if all of its quarters are bookable.
"""

from __future__ import annotations

import re
from datetime import date

from bs4 import BeautifulSoup

from ..core import BOOKED, FREE, CourtDay, Day, Venue, hhmm, now_local, session

START = re.compile(r"(\d{1,2})\s*:\s*(\d{2})")


def _start(td) -> int | None:
    el = td.select_one(".time.start")
    m = START.search(el.get_text("", strip=True)) if el else None
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def _state(classes: list[str]) -> str | None:
    if "disabled" in classes:
        return None
    if "full" in classes or "blocked" in classes:
        return BOOKED
    if "can_book" in classes:
        return FREE
    return None


def fetch(venue: Venue, day: date) -> Day:
    if day != now_local().date():
        return {}
    p = venue.params
    url = f"https://{p['host']}/timeline/day"
    html = session().get(url, params={"tabIdx": p.get("tab", 0), "criteriaTimestamp": "", "resetFilter": "true"},
                         timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    names = {li["id"]: li.get_text(" ", strip=True) for li in soup.select("li.hall[id]")}
    courts: Day = {}
    for tr in soup.select("tr[data-row-id]"):
        if tr.get("data-parent-row-id") != p.get("group", "activity_hall_0"):
            continue
        cid = tr["data-row-id"]
        quarters: dict[int, str] = {}  # minute -> status, at 15-min resolution
        for td in tr.find_all("td", recursive=False):
            classes = td.get("class", [])
            if "zoom" in classes:
                for sub in td.select("table.table_zoom td"):
                    start, state = _start(sub), _state(sub.get("class", []))
                    if start is not None and state:
                        quarters[start] = state
            else:
                start, state = _start(td), _state(classes)
                if start is not None and state:
                    for q in range(start, start + 60, 15):
                        quarters[q] = state

        cells: dict[str, str] = {}
        for m in sorted({q - q % 30 for q in quarters}):
            parts = [quarters.get(m), quarters.get(m + 15)]
            if None in parts:
                continue
            cells[hhmm(m)] = FREE if all(s == FREE for s in parts) else BOOKED
        if cells:
            courts[cid] = CourtDay(names.get(cid, cid), cells)
    return courts
