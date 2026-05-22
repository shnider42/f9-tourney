# Rocket League 2v2 Signups (Flask)

A tiny Flask app to collect signups for an F9 Rocket League 2v2 tournament.

## Features
- Public signup form (Display name, Discord, RL Tracker link, Region)
- Duplicate prevention by Discord handle
- Public roster view + JSON (`/roster.json`)
- Admin dashboard (`/admin?code=YOUR_ADMIN_CODE`):
  - Delete entries
  - Toggle signups open/closed
  - Export CSV (`/export.csv`)

## Quick start (local)
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export ADMIN_CODE="set-a-strong-code"
export SECRET_KEY="change-me"
# Optional override:
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
   - (Optional) `SIGNUPS_OPEN`
5. Deploy; share your service URL.

## Deploy (Railway / Fly.io / Heroku)
- Use the same `gunicorn app:app` start command and add the same env vars.
- SQLite works fine for a single instance. If you scale horizontally, use a hosted Postgres and set `DATABASE_URL` accordingly.
