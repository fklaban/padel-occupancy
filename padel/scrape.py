"""Take one snapshot of every venue and merge it into today's cell file.

Run this several times a day. Each half-hour cell keeps the last status seen
*before it started*, which is the best available answer to "was this court
booked?". Systems that only list free slots stop listing a slot once it has
passed, so for them past cells are never overwritten (`Venue.shows_past`).

    python -m padel.scrape [--date YYYY-MM-DD] [--only venue_id,...]
"""

from __future__ import annotations

import argparse
import csv
import importlib
import sys
import traceback
from datetime import date
from pathlib import Path

from .core import is_past, now_local
from .venues import VENUES

DATA = Path(__file__).resolve().parent.parent / "data"
FIELDS = ["venue", "court_id", "court", "slot", "status", "observed_at"]


def cell_file(day: date) -> Path:
    return DATA / "cells" / f"{day:%Y-%m}" / f"{day.isoformat()}.csv"


def load(path: Path) -> dict[tuple, dict]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        return {(r["venue"], r["court_id"], r["slot"]): r for r in csv.DictReader(f)}


def save(path: Path, rows: dict[tuple, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows[k] for k in sorted(rows))


def log_run(rows: list[dict]) -> None:
    path = DATA / "runs.csv"
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["observed_at", "date", "venue", "result", "courts", "cells", "error"])
        if new:
            w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat)
    ap.add_argument("--only", help="comma-separated venue ids")
    args = ap.parse_args(argv)

    now = now_local()
    day = args.date or now.date()
    stamp = now.isoformat(timespec="seconds")
    only = set(args.only.split(",")) if args.only else None

    path = cell_file(day)
    rows = load(path)
    runs, failures = [], 0

    for v in VENUES:
        if v.disabled or (only and v.id not in only):
            continue
        try:
            adapter = importlib.import_module(f".adapters.{v.platform}", __package__)
            courts = adapter.fetch(v, day)
        except Exception as e:  # one broken site must not stop the others
            failures += 1
            traceback.print_exc()
            runs.append({"observed_at": stamp, "date": day, "venue": v.id, "result": "error",
                         "courts": 0, "cells": 0, "error": f"{type(e).__name__}: {e}"[:300]})
            print(f"✗ {v.id}: {e}", file=sys.stderr)
            continue

        if not courts:
            runs.append({"observed_at": stamp, "date": day, "venue": v.id, "result": "empty",
                         "courts": 0, "cells": 0, "error": "no padel courts in response"})
            print(f"? {v.id}: no padel courts in response", file=sys.stderr)
            continue

        written = 0
        for cid, court in courts.items():
            for slot, status in court.cells.items():
                key = (v.id, cid, slot)
                if is_past(day, slot, now) and not v.shows_past:
                    continue  # this snapshot can't tell us anything reliable about it
                rows[key] = {"venue": v.id, "court_id": cid, "court": court.name,
                             "slot": slot, "status": status, "observed_at": stamp}
                written += 1
        runs.append({"observed_at": stamp, "date": day, "venue": v.id, "result": "ok",
                     "courts": len(courts), "cells": written, "error": ""})
        print(f"✓ {v.id}: {len(courts)} courts, {written} cells updated")

    save(path, rows)
    log_run(runs)
    # Fail the job only when everything failed (likely our bug, not one site).
    return 1 if runs and failures == len(runs) else 0


if __name__ == "__main__":
    sys.exit(main())
