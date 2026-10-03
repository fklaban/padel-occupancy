# Prague padel occupancy

Measures how busy Prague's padel courts are by reading each club's public
booking calendar every 30 minutes (GitHub Actions) and keeping, for every
court and half hour, the last status seen **before the slot started**.

Dashboard: https://fklaban.github.io/padel-occupancy/ (source: `docs/index.html`).

## What's tracked

| Venue | Booking system | Status |
|---|---|---|
| Padel Club Spoje | Playtomic | ✅ |
| Tenis & Padel klub Písečná | Playtomic | ✅ |
| Hagibor Padel Bohemians | rogeronline.cz | ✅ |
| Padel Satalice | rogeronline.cz | ✅ |
| Padel Powers Smíchov | padelos.co | ✅ |
| TK Neridé | Sportelo | ✅ (hours counted 06–24; venue is bookable 24/7) |
| Areál Císařská louka | Reenio | ✅ (3 courts, booked count only — per-court split is virtual) |
| Sky Sport City Prosek | Clubspire | ✅ (4 outdoor courts) |
| Wilson Tenis Centrum | jdemenato.cz | ✅ |
| TK Sparta Praha | rogeronline.cz | ⏸ padel courts couldn't be identified in the grid |
| PADEL Slavia Praha | own system | ⛔ WEDOS bot protection |
| CPA Arena, For Padel Zdiměřice, LTC Modřany, Padel Radotín, PLECHOVKA Dubeč, HEAD Vestec, The Court | iSportSystem | ⛔ Cloudflare bot challenge |
| Padel Džus | bookaball | ⛔ calendar needs login |
| HECTOR Sport Centre | R2S | ⛔ calendar needs login |
| One Padel Zličín | CourtyONE | ⛔ no stable public endpoint (partner API needs a key) |

Sites behind bot protection or a login are deliberately **not** worked
around. If a club gives you an API key or a public feed, add an adapter.

## How it works

```
padel/
  core.py          shared types: Venue, CourtDay, 30-min grid helpers
  venues.py        the 21 venues and their booking-system parameters
  adapters/*.py    one module per booking system → {court: {"HH:MM": free|booked}}
  scrape.py        snapshot every enabled venue, merge into data/cells/YYYY-MM/DATE.csv
  report.py        build data/daily.csv and docs/data.json for the dashboard
```

- **Cells:** each court's opening hours are split into 30-minute cells marked
  `free` or `booked` (anything not bookable: reservations, lessons, blocks).
- **Freezing:** a cell is updated on every run until it starts. Systems that
  only list *free* slots (Playtomic, padelos, Clubspire) drop past slots, so
  their past cells are never overwritten. Systems that keep showing past
  reservations (`shows_past=True`) can fill in the whole day at once.
- **Occupancy** = booked cells ÷ observed cells. Playtomic and padelos only
  sell ≥60-minute slots, so an isolated free half hour counts as booked
  (it can't be sold either).

### Output files

- `data/cells/YYYY-MM/YYYY-MM-DD.csv` — `venue, court_id, court, slot, status, observed_at`
- `data/daily.csv` — per venue per day: courts, observed/booked slots, occupancy
- `data/runs.csv` — one row per venue per run (`ok` / `empty` / `error`)
- `docs/data.json` — everything the dashboard needs

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m padel.scrape          # one snapshot (today)
.venv/bin/python -m padel.scrape --only powers,neride
.venv/bin/python -m padel.report
```

To view the dashboard locally, serve the folder (`python3 -m http.server -d docs`)
— `fetch()` doesn't work from `file://`.

## Adding a venue

1. Write `padel/adapters/<platform>.py` with `fetch(venue, day) -> Day`.
2. Add a `Venue(...)` line to `padel/venues.py`.
3. `python -m padel.scrape --only <id>` and eyeball the cell file.
