#!/usr/bin/env python3
import os
import datetime as dt
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

BASE = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE / "templates"),
    static_folder=str(BASE / "static"),
)

ADMIN_CODE = os.getenv("ADMIN_CODE", "changeme")
SIGNUPS_OPEN = os.getenv("SIGNUPS_OPEN", "true").lower() == "true"

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///signups.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=dt.datetime.utcnow)
    display_name = db.Column(db.String(80), nullable=False)
    discord = db.Column(db.String(80), nullable=False)
    epic_id = db.Column(db.String(120), nullable=True)
    rank = db.Column(db.String(40), nullable=True)
    region = db.Column(db.String(40), nullable=True)
    notes = db.Column(db.String(280), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="registered")

    __table_args__ = (
        db.UniqueConstraint("discord", name="uq_discord"),
    )


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

        if not display_name or not discord:
            flash("Display name and Discord are required.", "danger")
            return redirect(url_for("index"))

        existing = Signup.query.filter(func.lower(Signup.discord) == discord).first()
        if existing:
            flash("That Discord is already registered.", "warning")
            return redirect(url_for("index"))

        signup = Signup(
            display_name=display_name,
            discord=discord,
            epic_id=epic_id,
            rank=rank,
            region=region,
            notes=notes,
            status="registered",
        )
        db.session.add(signup)
        db.session.commit()
        return render_template("thanks.html")

    entries = Signup.query.order_by(Signup.timestamp.asc()).all()
    return render_template("index.html", entries=entries, signups_open=SIGNUPS_OPEN)


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
        "timestamp": r.timestamp.isoformat(),
    } for r in all_rows]
    return jsonify({"signups_open": SIGNUPS_OPEN, "entries": data})


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
        elif action == "toggle_signups":
            global SIGNUPS_OPEN
            SIGNUPS_OPEN = not SIGNUPS_OPEN

    entries = Signup.query.order_by(Signup.timestamp.asc()).all()
    return render_template(
        "admin.html",
        entries=entries,
        signups_open=SIGNUPS_OPEN,
        code=request.args.get("code") or request.form.get("code"),
    )


@app.route("/export.csv")
def export_csv():
    if not is_admin(request):
        return "Unauthorized", 401

    import csv
    from io import StringIO

    output = StringIO()
    w = csv.writer(output)
    w.writerow(["id", "timestamp", "display_name", "discord", "epic_id", "rank", "region", "notes"])

    rows = Signup.query.order_by(Signup.timestamp.asc()).all()
    for r in rows:
        w.writerow([r.id, r.timestamp.isoformat(), r.display_name, r.discord, r.epic_id, r.rank, r.region, r.notes])

    output.seek(0)
    return app.response_class(
        output.read(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=roster.csv"},
    )


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
