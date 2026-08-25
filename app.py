"""
CEP Report — Technical Support for Rural Startups
Flask + Flask-SQLAlchemy (MySQL via PyMySQL) backend.
"""

import os
from datetime import datetime, date, time as dtime

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash
)
from werkzeug.utils import secure_filename
from sqlalchemy import func

from models import db, Startup

# ------------------------------------------------------------------
# App configuration
# ------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cep-rural-startups-dev-key")

# MySQL connection — override with environment variables in production.
# DB_USER = os.environ.get("DB_USER", "root")
# DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
# DB_HOST = os.environ.get("DB_HOST", "localhost")
# DB_PORT = os.environ.get("DB_PORT", "3306")
# DB_NAME = os.environ.get("DB_NAME", "rural_startups_db")
# # Aiven (and most managed MySQL hosts) require TLS. PyMySQL 1.1.x understands
# # the ssl_mode query param directly, so this is a no-op for a local MySQL
# # that doesn't need TLS unless DB_SSL_MODE is set.
# DB_SSL_MODE = os.environ.get("DB_SSL_MODE")  # e.g. REQUIRED, VERIFY_CA

# _db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# if DB_SSL_MODE:
#     _db_uri += f"?ssl_mode={DB_SSL_MODE}"

# app.config["SQLALCHEMY_DATABASE_URI"] = _db_uri
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB max upload

# db.init_app(app)
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
if DB_SSL_REQUIRED:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"ssl": {}}}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB max upload

db.init_app(app)


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
            photo_filename = secure_filename(photo.filename)
            # avoid overwriting existing files with the same name
            base, ext = os.path.splitext(photo_filename)
            candidate = photo_filename
            counter = 1
            while os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], candidate)):
                candidate = f"{base}_{counter}{ext}"
                counter += 1
            photo_filename = candidate
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], photo_filename))

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


@app.route("/resources")
def resources():
    return render_template("resources.html")


# ------------------------------------------------------------------
# App bootstrap
# ------------------------------------------------------------------
def init_db():
    """Create tables (if needed)."""
    with app.app_context():
        db.create_all()



# Run once whenever the module is imported — this covers both `python
# app.py` locally AND a WSGI server (gunicorn) importing `app:app` in
# production, since gunicorn never executes the __main__ block below.
init_db()

if __name__ == "__main__":
    app.run(debug=True)
