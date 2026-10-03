"""Aggregate the cell files into `data/daily.csv` and `docs/data.json`.

Occupancy = booked half-hours / observed half-hours within opening hours.

    python -m padel.report
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date

from .core import now_local
from .scrape import DATA
from .venues import VENUES

DOCS = DATA.parent / "docs"


def main() -> None:
    daily = defaultdict(lambda: [0, 0, set()])  # (date, venue) -> [booked, total, courts]
    heat = defaultdict(lambda: [0, 0])  # (venue, weekday, hour) -> [booked, total]

    enabled = {v.id for v in VENUES if not v.disabled}
    for path in sorted((DATA / "cells").glob("*/*.csv")):
        day = date.fromisoformat(path.stem)
        with path.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["venue"] not in enabled:
                    continue
                booked = r["status"] == "booked"
                d = daily[(day.isoformat(), r["venue"])]
                d[0] += booked
                d[1] += 1
                d[2].add(r["court_id"])
                h = heat[(r["venue"], day.weekday(), int(r["slot"][:2]))]
                h[0] += booked
                h[1] += 1

    names = {v.id: v.name for v in VENUES}
    with (DATA / "daily.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "venue", "name", "courts", "observed_slots", "booked_slots", "occupancy"])
        for (day, vid), (b, t, courts) in sorted(daily.items()):
            w.writerow([day, vid, names.get(vid, vid), len(courts), t, b, f"{b / t:.4f}" if t else ""])

    last_run = {}
    runs_path = DATA / "runs.csv"
    if runs_path.exists():
        with runs_path.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                last_run[r["venue"]] = {"at": r["observed_at"], "result": r["result"], "error": r["error"]}

    DOCS.mkdir(exist_ok=True)
    payload = {
        "generated_at": now_local().isoformat(timespec="seconds"),
        "venues": [
            {"id": v.id, "name": v.name, "platform": v.platform, "disabled": v.disabled,
             "last_run": last_run.get(v.id)}
            for v in VENUES
        ],
        "daily": [
            {"date": day, "venue": vid, "courts": len(c), "booked": b, "total": t}
            for (day, vid), (b, t, c) in sorted(daily.items())
        ],
        "heat": [
            {"venue": vid, "weekday": wd, "hour": hr, "booked": b, "total": t}
            for (vid, wd, hr), (b, t) in sorted(heat.items())
        ],
    }
    (DOCS / "data.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"report: {len(daily)} venue-days, {len(payload['heat'])} heatmap cells")


if __name__ == "__main__":
    main()
