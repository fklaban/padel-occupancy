"""rogeronline.cz (also onlinehq.cz) — public court grid.

The grid page lists every court of a "set" with a row per half hour, and each
reservation as a `reservation-block` with its court, start minute and length.
Past reservations stay visible, so the whole day can be read at any time.
"""

from __future__ import annotations

import re
from datetime import date

from ..core import BOOKED, FREE, CourtDay, Day, Venue, mark, minutes, session

URL = "https://www.rogeronline.cz/v2/index.php"

COURT_HEADERS = re.compile(r'<span class="court-header-name">\s*([^<]*?)\s*</span>')
COURT_IDS = re.compile(r'class="court-cell[^>]*?data-court="(\d+)"')
TIMES = re.compile(r'<div class="time-cell[^"]*">\s*(\d{2}:\d{2})')
BLOCKS = re.compile(
    r'class="reservation-block[^"]*"\s+data-rec-id="[^"]*"\s+data-court="(\d+)"\s+'
    r'data-start-minutes="(\d+)"\s+data-duration="(\d+)"'
)


def fetch(venue: Venue, day: date) -> Day:
    s = session()
    html = s.get(
        URL,
        params={
            "klub": venue.params["klub"],
            "set": venue.params["set"],
            "rok": day.year,
            "mesic": day.month,
            "den": day.day,
            "view": "grid",
        },
        timeout=30,
    ).text
    body = html[html.find("<body") :]

    names = COURT_HEADERS.findall(body)
    ids = list(dict.fromkeys(COURT_IDS.findall(body)))
    times = TIMES.findall(body)
    if not names or len(names) != len(ids) or not times:
        raise RuntimeError(f"unexpected rogeronline grid for klub={venue.params['klub']}")

    # The grid's own rows are the opening hours; rows may be 30 or 60 min.
    step = minutes(times[1]) - minutes(times[0]) if len(times) > 1 else 30
    open_cells = {}
    for t in times:
        for m in range(minutes(t), minutes(t) + step, 30):
            open_cells[f"{m // 60:02d}:{m % 60:02d}"] = FREE

    pattern = re.compile(venue.params.get("court_filter", "padel"), re.I)
    courts: Day = {
        cid: CourtDay(name, dict(open_cells)) for cid, name in zip(ids, names) if pattern.search(name)
    }
    for cid, start, duration in BLOCKS.findall(body):
        if cid in courts:
            mark(courts[cid].cells, int(start), int(duration), BOOKED)
    return courts
