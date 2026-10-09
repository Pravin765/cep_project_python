"""
CEP Report — Technical Support for Rural Startups
Flask + Flask-SQLAlchemy (MySQL via PyMySQL) backend.
"""

import os
import threading
import time
import urllib.request
from datetime import datetime, date, time as dtime

import cloudinary
import cloudinary.uploader
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_from_directory, abort
)
from werkzeug.utils import secure_filename
from sqlalchemy import func, text

from models import db, Startup

# ------------------------------------------------------------------
# App configuration
# ------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cep-rural-startups-dev-key")

# MySQL connection — defaults point at the Aiven-hosted MySQL instance;
# override any of these with environment variables if you ever move to a
# different database.
DB_USER = os.environ.get("DB_USER", "avnadmin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "AVNS_fF_fOUGsItnRLvORNbA")
DB_HOST = os.environ.get("DB_HOST", "cepproject-cepproject8485202526.c.aivencloud.com")
DB_PORT = os.environ.get("DB_PORT", "21206")
DB_NAME = os.environ.get("DB_NAME", "defaultdb")
# Aiven requires TLS. PyMySQL has no "ssl_mode" connect argument (that's a
# mysql-connector-python convention) — it takes a plain "ssl" dict instead,
# which must be passed through SQLAlchemy's connect_args, not the URL.
DB_SSL_REQUIRED = os.environ.get("DB_SSL_MODE", "REQUIRED").upper() not in ("", "DISABLED", "0", "FALSE")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
_engine_options = {
    # Test a pooled connection before using it and recycle idle ones, so the
    # first request after a quiet period never hits a dead MySQL socket.
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "connect_args": {"connect_timeout": 10},
}
if DB_SSL_REQUIRED:
    _engine_options["connect_args"]["ssl"] = {}
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = _engine_options
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB max upload

db.init_app(app)

# Cloudinary — persistent photo storage. Render's local disk is wiped on
# every restart/redeploy, so uploaded photos can't live there long-term.
# The SDK auto-configures itself from the CLOUDINARY_URL env var at import
# time — there's no config(cloudinary_url=...) kwarg, so we just check the
# env var is present and let cloudinary.config() below confirm it parsed.
USE_CLOUDINARY = bool(os.environ.get("CLOUDINARY_URL"))
if USE_CLOUDINARY:
    cloudinary.config(secure=True)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value: str) -> dtime:
    # Accept both HH:MM and HH:MM:SS from <input type="time">
    fmt = "%H:%M:%S" if value.count(":") == 2 else "%H:%M"
    return datetime.strptime(value, fmt).time()


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/dashboard")
def dashboard():
    startups = Startup.query.order_by(Startup.date_visited.desc()).all()
    places_visited = db.session.query(func.count(func.distinct(Startup.village))).scalar() or 0
    return render_template(
        "dashboard.html",
        startups=startups,
        places_visited=places_visited,
        total_visits=len(startups),
    )


@app.route("/field-work", methods=["GET", "POST"])
def field_work():
    if request.method == "POST":
        photo_filename = None
        photo = request.files.get("photo_with_members")
        if photo and photo.filename and allowed_file(photo.filename):
            if USE_CLOUDINARY:
                # Cloudinary persists the file and hands back a permanent
                # HTTPS URL — that URL is what we store, straight into the
                # photo_filename column.
                upload_result = cloudinary.uploader.upload(
                    photo, folder="cep_rural_startups"
                )
                photo_filename = upload_result["secure_url"]
            else:
                # Local-disk fallback for development without Cloudinary
                # configured. Not persistent on Render.
                safe_name = secure_filename(photo.filename)
                base, ext = os.path.splitext(safe_name)
                candidate = safe_name
                counter = 1
                while os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], candidate)):
                    candidate = f"{base}_{counter}{ext}"
                    counter += 1
                photo.save(os.path.join(app.config["UPLOAD_FOLDER"], candidate))
                photo_filename = candidate

        try:
            new_entry = Startup(
                startup_name=request.form["startup_name"].strip(),
                founder_name=request.form["founder_name"].strip(),
                photo_filename=photo_filename,
                village=request.form["village"].strip(),
                address=request.form["address"].strip(),
                date_visited=parse_date(request.form["date_visited"]),
                time_visited=parse_time(request.form["time_visited"]),
                technical_support=request.form["technical_support"].strip(),
                statement_before=request.form["statement_before"].strip(),
                before_tech_support=request.form["before_tech_support"].strip(),
                after_tech_support=request.form["after_tech_support"].strip(),
            )
            db.session.add(new_entry)
            db.session.commit()
            flash(f"Field record for {new_entry.startup_name} saved successfully.", "success")
        except (KeyError, ValueError) as exc:
            flash(f"Could not save record — please check the form fields ({exc}).", "error")

        return redirect(url_for("field_work"))

    startups = Startup.query.order_by(Startup.date_visited.desc()).all()
    return render_template("field_work.html", startups=startups)


# ------------------------------------------------------------------
# Product demos
# ------------------------------------------------------------------
def _demo_catalogue():
    return [
        {
            "slug": "auto-crop",
            "number": "01",
            "title": "Auto Face & Shoulder Cropping",
            "tagline": "RetinaFace + Pillow",
            "description": "A web app that detects every face, infers the shoulder line, and auto-crops to standard ID / portrait ratios.",
            "stack": ["Python", "RetinaFace", "Pillow", "Flask"],
            "video": os.environ.get("DEMO_VIDEO_CROP_URL",
                url_for("static", filename="demos/auto_crop.mp4")),
            "poster": url_for("static", filename="demos/auto_crop_poster.jpg"),
        },
        {
            "slug": "bulk-bg-removal",
            "number": "02",
            "title": "Bulk Background Removal",
            "tagline": "withoutbg model",
            "description": "Drops the background from every photo in a folder in one pass.",
            "stack": ["Python", "withoutbg", "Pillow"],
            "video": os.environ.get("DEMO_VIDEO_BG_URL",
                url_for("static", filename="demos/withoutbg_bulk_demo.mp4")),
            "poster": url_for("static", filename="demos/withoutbg_bulk_poster.jpg"),
        },
        {
            "slug": "dslr-renamer",
            "number": "03",
            "title": "Smart Camera Renamer",
            "tagline": "DSLR-style sequential naming",
            "description": "Android companion app that captures a photo and renames it with a DSLR-style serial.",
            "stack": ["Android", "Kotlin", "EXIF"],
            "video": os.environ.get("DEMO_VIDEO_RENAMER_URL",
                url_for("static", filename="demos/dslr_renamer_demo.mp4")),
            "poster": url_for("static", filename="demos/dslr_renamer_poster.jpg"),
        },
    ]


@app.route("/demos")
def demos():
    return render_template(
        "demos.html",
        demos=_demo_catalogue(),
        site_image=os.environ.get("DEMO_SITE_IMAGE_URL",
            url_for("static", filename="demos/class_mgmt_site.png")),
    )


# ------------------------------------------------------------------
# Report download
# ------------------------------------------------------------------
REPORT_FILENAME = "CEP_Report_Technical_Support_Rural_Startups.pdf"


def _report_path_ok():
    return os.path.exists(os.path.join(BASE_DIR, "static", REPORT_FILENAME))


@app.route("/report")
def report():
    """Show the CEP report PDF inside the browser."""
    if not _report_path_ok():
        abort(404)
    return render_template("report.html")


@app.route("/report/file")
def report_file():
    """The PDF itself, served inline so browsers render it (used by /report)."""
    if not _report_path_ok():
        abort(404)
    return send_from_directory(os.path.join(BASE_DIR, "static"), REPORT_FILENAME,
                               as_attachment=False, mimetype="application/pdf")


@app.route("/report/download")
def download_report():
    """Serve the final CEP report PDF as a download."""
    if not _report_path_ok():
        abort(404)
    return send_from_directory(os.path.join(BASE_DIR, "static"), REPORT_FILENAME,
                               as_attachment=True)


# ------------------------------------------------------------------
# Health check (for uptime pingers / keep-warm)
# ------------------------------------------------------------------
@app.route("/healthz")
def healthz():
    """Cheap endpoint that also touches the DB, so one ping keeps both the
    web dyno and the MySQL connection warm."""
    try:
        db.session.execute(text("SELECT 1"))
        return "ok", 200
    except Exception:
        return "db unavailable", 503


# ------------------------------------------------------------------
# Keep-alive (prevents Render free-tier spin-down)
# ------------------------------------------------------------------
def _keep_alive(url: str, interval: int = 600):
    """Ping our own public URL every `interval` seconds. Render spins a free
    web service down after ~15 min without inbound traffic; a request that
    arrives via the public URL counts as traffic."""
    while True:
        time.sleep(interval)
        try:
            urllib.request.urlopen(url, timeout=20).read()
        except Exception:
            pass  # never let a failed ping kill the thread


# Render sets RENDER_EXTERNAL_URL automatically. Locally it's absent, so no
# thread is started during development.
_KEEP_ALIVE_URL = os.environ.get("KEEP_ALIVE_URL") or (
    os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/") + "/healthz"
    if os.environ.get("RENDER_EXTERNAL_URL") else ""
)
if _KEEP_ALIVE_URL and os.environ.get("KEEP_ALIVE", "1") != "0":
    threading.Thread(target=_keep_alive, args=(_KEEP_ALIVE_URL,), daemon=True).start()


# ------------------------------------------------------------------
# App bootstrap
# ------------------------------------------------------------------
def init_db():
    """Create tables (if needed). A slow or sleeping database must not
    stop the web process from booting, so failures are logged, not raised."""
    try:
        with app.app_context():
            db.create_all()
    except Exception as exc:
        app.logger.warning("init_db skipped: %s", exc)



# Run once whenever the module is imported — this covers both `python
# app.py` locally AND a WSGI server (gunicorn) importing `app:app` in
# production, since gunicorn never executes the __main__ block below.
init_db()

if __name__ == "__main__":
    app.run(debug=True)