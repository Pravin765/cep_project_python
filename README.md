# Technical Support for Rural Startups — CEP Report Web App

A Flask + MySQL web application presenting a Community Engagement Program
(CEP) report documenting technical support visits to micro-enterprises near
Bhiwandi, Thane District, Maharashtra.

## Stack
- **Backend:** Flask, Flask-SQLAlchemy
- **Database:** MySQL (via PyMySQL) — configured for an Aiven-hosted instance over TLS
- **Photo storage:** Cloudinary (persistent) with a local-disk fallback for development
- **Frontend:** Jinja2 templates + Tailwind CSS (CDN)

## Project structure
```
app.py                      # Routes, config, validation, DB bootstrap
models.py                    # SQLAlchemy Startup model
schema.sql                    # Standalone MySQL schema + example seed data
requirements.txt
static/
├── css/style.css             # "Field-notebook stamp" signature styling
├── uploads/                   # Local-disk photo fallback (dev only)
├── resources/
│   └── Cybersecurity_Awareness.pptx
└── CEP_Report_Technical_Support_Rural_Startups.pdf
templates/
├── base.html                 # Navbar, footer, Tailwind config
├── home.html
├── dashboard.html
├── field_work.html
└── resources.html
```

## ⚠️ Secrets — environment variables only

**No real credentials live in this codebase.** `app.py` reads every MySQL
and Cloudinary setting from environment variables and will not start
against a real database unless they're set — a missing `DB_PASSWORD`
prints a loud warning rather than silently falling back to something real.

Set these wherever you run the app (Render's dashboard → Environment, or
your local shell):

| Variable | Purpose |
|---|---|
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | MySQL connection (Aiven or otherwise) |
| `DB_SSL_MODE` | Set to `DISABLED` to turn off TLS for a local non-SSL MySQL; defaults to required |
| `CLOUDINARY_URL` | Enables persistent photo uploads. Format: `cloudinary://<api_key>:<api_secret>@<cloud_name>` |
| `SECRET_KEY` | Flask session/flash-message signing key |

If your Aiven (or any other) MySQL password has ever been committed to
git or exposed in a public repo, **rotate it** before deploying — treat it
as compromised even after removing it from the code.

## 1. Set up MySQL

Create the database and table:

```bash
mysql -u root -p < schema.sql
```

`schema.sql` also inserts two example field-visit records — drop those
INSERT statements if you'd rather start with an empty table (the app no
longer auto-seeds on first run).

## 2. Configure environment variables

```bash
# macOS/Linux (bash)
export DB_USER=your_db_user
export DB_PASSWORD=your_db_password
export DB_HOST=your_db_host
export DB_PORT=3306
export DB_NAME=rural_startups_db
export CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
```

```powershell
# Windows PowerShell
$env:DB_USER="your_db_user"
$env:DB_PASSWORD="your_db_password"
$env:DB_HOST="your_db_host"
$env:DB_PORT="3306"
$env:DB_NAME="rural_startups_db"
$env:CLOUDINARY_URL="cloudinary://<api_key>:<api_secret>@<cloud_name>"
```

If `CLOUDINARY_URL` isn't set, uploaded photos save to `static/uploads/`
instead — fine for local development, but Render's disk is wiped on every
restart/redeploy, so photos won't persist there in production.

## 3. Install dependencies & run

```bash
python3 -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
python3 app.py
```

Table creation runs automatically on import (so it also works under
gunicorn in production, not just `python app.py` locally), then the app
starts on `http://127.0.0.1:5000`.

## Routes

| Route | Method | Description |
|---|---|---|
| `/` , `/home` | GET | Project overview, objectives, team, methodology |
| `/dashboard` | GET | Metrics + full data table of every visit |
| `/field-work` | GET, POST | Card grid of visits; POST adds a new record with photo upload |
| `/resources` | GET | Intervention areas with downloadable training materials + report PDF |

## Validation

- **Client-side** (`field_work.html`): HTML5 `required` on every text
  field, plus JS that blocks a future visit date and enforces the
  9:00 AM–6:00 PM visit-time window before the form submits.
- **Server-side** (`app.py`): the same date/time window is re-checked
  after submission (protects against JS being disabled or a direct POST),
  every required text field is rejected if blank or whitespace-only, and
  an unsupported photo file type is reported back to the user instead of
  silently dropped — the rest of the record still saves.

## Notes
- Smoke-tested end-to-end against SQLite during development (all five
  routes, blank-field rejection, future-date rejection, a valid save) —
  swap in your real MySQL/Cloudinary credentials as above for production,
  no code changes needed.
- The Resources page links four downloadable files under
  `static/resources/` plus the report PDF at the top level of `static/`.
  This package includes a freshly generated `Cybersecurity_Awareness.pptx`
  (the previously broken link). If your live site already serves the
  other three — `Automated_Inventory_Management.xlsx`,
  `UPI_Setup_and_First_Payment_Guide.pptx`, and
  `Online_Discoverability.pptx` — carry those over from your existing
  `static/resources/` folder; they aren't included here since I don't have
  copies of their original content.
