# Rocket League 1v1 Signups (Flask)

A tiny Flask app to collect signups for a 12‑player + 2‑sub (14 total) tournament, with automatic waitlist.

## Features
- Public signup form (Display name, Discord, Epic ID, Rank, Region, Notes)
- Capacity logic: first 12 = players, next 2 = subs, rest = waitlist
- Duplicate prevention by Discord handle
- Public roster view + JSON (`/roster.json`)
- Admin dashboard (`/admin?code=YOUR_ADMIN_CODE`):
  - Promote/demote between player/sub/waitlist
  - Delete entries
  - Toggle signups open/closed
  - "Shuffle Fill" to auto-assign by timestamp
  - Export CSV (`/export.csv`)

## Quick start (local)
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export ADMIN_CODE="set-a-strong-code"
export SECRET_KEY="change-me"
# Optional overrides:
# export CAP_PLAYERS=12
# export CAP_SUBS=2
# export SIGNUPS_OPEN=true
python app.py
```
Open http://localhost:8000

## Deploy (Render)
1. Create a new **Web Service** from this repo/folder.
2. Runtime: Python; Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn app:app`
4. Add Environment Variables:
   - `ADMIN_CODE` – a strong secret you will append as `?code=...`
   - `SECRET_KEY` – random string
   - (Optional) `CAP_PLAYERS`, `CAP_SUBS`, `SIGNUPS_OPEN`
5. Deploy; share your service URL.

## Deploy (Railway / Fly.io / Heroku)
- Use the same `gunicorn app:app` start command and add the same env vars.
- SQLite works fine for a single instance. If you scale horizontally, use a hosted Postgres and set `DATABASE_URL` accordingly.
