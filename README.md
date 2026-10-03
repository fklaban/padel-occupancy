# Prague padel occupancy

Measures how busy Prague's padel courts are by reading each club's public
booking calendar every 30 minutes and keeping, for every court and half hour,
the last status seen **before the slot started**.

Dashboard: https://fklaban.github.io/padel-occupancy/ (source: `docs/index.html`).

## What's tracked

| Venue | Booking system | Fetched from |
|---|---|---|
| Hagibor Padel Bohemians | rogeronline.cz | GitHub Actions |
| Padel Satalice | rogeronline.cz | GitHub Actions |
| Padel Powers Smíchov | padelos.co | GitHub Actions |
| TK Neridé | Sportelo (GraphQL) | GitHub Actions — hours counted 06–24; bookable 24/7 |
| Areál Císařská louka | Reenio | GitHub Actions — booked count only; per-court split is virtual |
| Sky Sport City Prosek | Clubspire | GitHub Actions — 4 outdoor courts |
| One Padel Zličín | CourtyONE (public `fetchPublicDayOccupancyAction`) | GitHub Actions |
| Padel Džus | bookaball (guest booking wizard, no login) | GitHub Actions |
| CPA Arena, For Padel Zdiměřice, LTC Modřany, Padel Radotín, PLECHOVKA Dubeč, HEAD Vestec, The Court | iSportSystem (public `/api/get-times.php`) | GitHub Actions |
| Padel Club Spoje, Tenis & Padel klub Písečná | Playtomic | **home runner** — Playtomic returns HTTP 403 to cloud IPs |
| Wilson Tenis Centrum, TK Sparta Praha | jdemenato.cz | **home runner** — Cloudflare challenge for cloud IPs |
| PADEL Slavia Praha | own system | ⛔ WEDOS bot protection — needs the club to allowlist us or share data |
| HECTOR Sport Centre | R2S | ⛔ calendar only after login — needs the club to share data |

Rules this project keeps: requests carry an honest User-Agent naming this
repo, run at most every 30 minutes, and never solve/dodge bot challenges,
spoof browsers, rotate proxies or log in. Where a site serves its data
openly (an API path, a guest flow, a home connection) we use it; where it
doesn't, we ask the club.

## Home runner

Playtomic and jdemenato refuse GitHub's datacenter IPs but serve a normal
home connection. `scripts/home-scrape.sh` fetches just those venues
(`Venue.where == "home"`) from a separate clone (`~/.padel-occupancy`) and
pushes only `*.home.csv` files, so it never conflicts with the cloud job.

```bash
scripts/install-home-runner.sh              # launchd agent: :05 and :35 every hour while the Mac is awake
scripts/install-home-runner.sh --uninstall
tail -f ~/Library/Logs/padel-occupancy.log
```

When the Mac is asleep or offline those four venues simply have gaps; the
dashboard counts only observed half hours.

## How it works

```
padel/
  core.py          shared types: Venue, CourtDay, 30-min grid helpers
  venues.py        the 21 venues, their booking-system parameters, cloud/home
  adapters/*.py    one module per booking system → {court: {"HH:MM": free|booked}}
  scrape.py        snapshot venues, merge into data/cells/YYYY-MM/DATE.<cloud|home>.csv
  report.py        build data/daily.csv and docs/data.json for the dashboard
scripts/           home runner + launchd installer
```

- **Cells:** each court's opening hours are split into 30-minute cells marked
  `free` or `booked` (reservations, lessons, blocks). Closures/maintenance are
  left out of capacity where the system labels them (iSportSystem, jdemenato).
- **Freezing:** a cell is updated on every run until it starts. Systems that
  only list *free* slots drop past slots, so their past cells are never
  overwritten. Systems that keep showing past reservations (`shows_past=True`)
  can fill in the whole day at once.
- **Occupancy** = booked cells ÷ observed cells. Systems that only sell
  ≥60-minute slots make an isolated free half hour count as booked (it can't
  be sold either).

### Output files

- `data/cells/YYYY-MM/YYYY-MM-DD.<cloud|home>.csv` — `venue, court_id, court, slot, status, observed_at`
- `data/runs.<cloud|home>.csv` — one row per venue per run (`ok` / `empty` / `error`)
- `data/daily.csv` — per venue per day: courts, observed/booked slots, occupancy
- `docs/data.json` — everything the dashboard needs

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m padel.scrape --where all       # one snapshot (today), both sides
.venv/bin/python -m padel.scrape --where home --only spoje
.venv/bin/python -m padel.report
python3 -m http.server -d docs                     # fetch() doesn't work from file://
```

## Adding a venue

1. Write `padel/adapters/<platform>.py` with `fetch(venue, day) -> Day`.
2. Add a `Venue(...)` line to `padel/venues.py` (`where="home"` if it blocks cloud IPs).
3. `python -m padel.scrape --where all --only <id>` and eyeball the cell file.
