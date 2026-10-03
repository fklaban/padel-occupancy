#!/bin/bash
# Fetch the venues that refuse cloud IPs (Venue.where == "home") from this
# machine and push only their data files. Runs from its own clone so it never
# touches a working copy you're editing. Scheduled by the launchd agent that
# scripts/install-home-runner.sh installs.
set -euo pipefail

REPO="${PADEL_REPO:-$HOME/.padel-occupancy}"
REMOTE="${PADEL_REMOTE:-https://github.com/fklaban/padel-occupancy.git}"

# Same window as the cloud job: skip the night.
hour=$(TZ=Europe/Prague date +%H)
if (( 10#$hour < 6 )); then exit 0; fi

[ -d "$REPO/.git" ] || git clone -q "$REMOTE" "$REPO"
cd "$REPO"
git pull -q --rebase
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
.venv/bin/pip install -q -r requirements.txt >/dev/null

echo "== $(date '+%F %T') home snapshot"
.venv/bin/python -m padel.scrape --where home || true

git add data/cells/*/*.home.csv data/runs.home.csv
git diff --cached --quiet && exit 0
git commit -q -m "data: home snapshot $(TZ=Europe/Prague date '+%Y-%m-%d %H:%M')"
for _ in 1 2 3; do
  git pull -q --rebase && git push -q && exit 0
  sleep 5
done
exit 1
