#!/usr/bin/env python3
import os
import datetime as dt
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

from pathlib import Path
from flask import Flask

BASE = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE / "templates"),
    static_folder=str(BASE / "static"),
)

CAP_PLAYERS = int(os.getenv("CAP_PLAYERS", "12"))
CAP_SUBS = int(os.getenv("CAP_SUBS", "2"))

ADMIN_CODE = os.getenv("ADMIN_CODE", "changeme")  # set a better secret in prod
SIGNUPS_OPEN = os.getenv("SIGNUPS_OPEN", "true").lower() == "true"

#app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-secret")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///signups.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=dt.datetime.utcnow)
    display_name = db.Column(db.String(80), nullable=False)  # in-stream name
    discord = db.Column(db.String(80), nullable=False)       # unique-ish
    epic_id = db.Column(db.String(120), nullable=True)
    rank = db.Column(db.String(40), nullable=True)
    region = db.Column(db.String(40), nullable=True)
    notes = db.Column(db.String(280), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="waitlist")  # player | sub | waitlist

    __table_args__ = (
        db.UniqueConstraint('discord', name='uq_discord'),
    )

def count_status(status):
    return db.session.query(func.count(Signup.id)).filter(Signup.status==status).scalar() or 0

@app.before_request
def init_db():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    global SIGNUPS_OPEN
    if request.method == "POST":
        if not SIGNUPS_OPEN:
            return render_template("closed.html")
        display_name = (request.form.get("display_name") or "").strip()
        discord = (request.form.get("discord") or "").strip().lower()
        epic_id = (request.form.get("epic_id") or "").strip()
        rank = (request.form.get("rank") or "").strip()
        region = (request.form.get("region") or "").strip()
        notes = (request.form.get("notes") or "").strip()[:280]

        # Basic validation
        if not display_name or not discord:
            flash("Display name and Discord are required.", "danger")
            return redirect(url_for("index"))

        # Check duplicate by discord
        existing = Signup.query.filter(func.lower(Signup.discord)==discord).first()
        if existing:
            flash("That Discord is already registered.", "warning")
            return redirect(url_for("index"))

        # Assign status based on capacity
        players = count_status("player")
        subs = count_status("sub")
        if players < CAP_PLAYERS:
            status = "player"
        elif subs < CAP_SUBS:
            status = "sub"
        else:
            status = "waitlist"

        s = Signup(display_name=display_name, discord=discord, epic_id=epic_id,
                   rank=rank, region=region, notes=notes, status=status)
        db.session.add(s)
        db.session.commit()
        return render_template("thanks.html", status=status, cap_players=CAP_PLAYERS, cap_subs=CAP_SUBS)

    # GET
    roster = {
        "players": Signup.query.filter_by(status="player").order_by(Signup.timestamp.asc()).all(),
        "subs": Signup.query.filter_by(status="sub").order_by(Signup.timestamp.asc()).all(),
        "waitlist": Signup.query.filter_by(status="waitlist").order_by(Signup.timestamp.asc()).all(),
    }
    return render_template("index.html", roster=roster, caps=(CAP_PLAYERS, CAP_SUBS), signups_open=SIGNUPS_OPEN)

@app.route("/roster.json")
def roster_json():
    all_rows = Signup.query.order_by(Signup.timestamp.asc()).all()
    data = [{
        "id": r.id,
        "display_name": r.display_name,
        "discord": r.discord,
        "epic_id": r.epic_id,
        "rank": r.rank,
        "region": r.region,
        "notes": r.notes,
        "status": r.status,
        "timestamp": r.timestamp.isoformat()
    } for r in all_rows]
    return jsonify({"cap_players": CAP_PLAYERS, "cap_subs": CAP_SUBS, "signups_open": SIGNUPS_OPEN, "entries": data})

# Very light admin: query param ?code=... on all admin routes
def is_admin(req):
    return (req.args.get("code") or req.form.get("code")) == ADMIN_CODE

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not is_admin(request):
        return "Unauthorized. Append ?code=YOUR_ADMIN_CODE", 401

    if request.method == "POST":
        action = request.form.get("action")
        sid = request.form.get("id")
        item = Signup.query.get(sid) if sid else None

        if action == "delete" and item:
            db.session.delete(item)
            db.session.commit()
        elif action == "status" and item:
            new_status = request.form.get("new_status")
            if new_status in ("player","sub","waitlist"):
                item.status = new_status
                db.session.commit()
        elif action == "toggle_signups":
            global SIGNUPS_OPEN
            SIGNUPS_OPEN = not SIGNUPS_OPEN
        elif action == "shuffle_fill":
            # Ensure top CAP_PLAYERS are players, next CAP_SUBS are subs, rest waitlist based on timestamp
            all_rows = Signup.query.order_by(Signup.timestamp.asc()).all()
            for idx, r in enumerate(all_rows):
                if idx < CAP_PLAYERS:
                    r.status = "player"
                elif idx < CAP_PLAYERS + CAP_SUBS:
                    r.status = "sub"
                else:
                    r.status = "waitlist"
            db.session.commit()

    players = Signup.query.filter_by(status="player").order_by(Signup.timestamp.asc()).all()
    subs = Signup.query.filter_by(status="sub").order_by(Signup.timestamp.asc()).all()
    waitlist = Signup.query.filter_by(status="waitlist").order_by(Signup.timestamp.asc()).all()
    return render_template("admin.html",
                           players=players, subs=subs, waitlist=waitlist,
                           cap_players=CAP_PLAYERS, cap_subs=CAP_SUBS, signups_open=SIGNUPS_OPEN,
                           code=request.args.get("code"))

@app.route("/export.csv")
def export_csv():
    if not is_admin(request):
        return "Unauthorized", 401
    import csv
    from io import StringIO
    output = StringIO()
    w = csv.writer(output)
    w.writerow(["id","timestamp","display_name","discord","epic_id","rank","region","notes","status"])
    rows = Signup.query.order_by(Signup.timestamp.asc()).all()
    for r in rows:
        w.writerow([r.id, r.timestamp.isoformat(), r.display_name, r.discord, r.epic_id, r.rank, r.region, r.notes, r.status])
    output.seek(0)
    return app.response_class(output.read(), mimetype="text/csv",
                              headers={"Content-Disposition": "attachment; filename=roster.csv"})

# Health check for PaaS
@app.route("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    # For local dev only
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
