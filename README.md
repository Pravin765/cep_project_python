# Technical Support for Rural Startups — CEP Report Web App

A Flask + MySQL web application presenting a Community Engagement Program (CEP)
report documenting technical support visits to micro-enterprises near
Kolhapur, Maharashtra.

## Stack
- **Backend:** Flask, Flask-SQLAlchemy
- **Database:** MySQL (via PyMySQL driver)
- **Frontend:** Jinja2 templates + Tailwind CSS (CDN)

## Project structure
```
cep_app/
├── app.py                 # Routes, config, DB bootstrap
├── models.py               # SQLAlchemy Startup model
├── schema.sql               # Standalone MySQL schema + seed data
├── requirements.txt
├── static/
│   ├── css/style.css        # Signature "field-notebook stamp" styling
│   ├── uploads/              # Uploaded + seed photos
│   └── CEP_Report_Technical_Support_Rural_Startups.pdf
└── templates/
    ├── base.html            # Navbar, footer, Tailwind config
    ├── home.html
    ├── dashboard.html
    ├── field_work.html
    └── resources.html
```

## 1. Set up MySQL

Create the database and table (this also inserts the two baseline visit
records — skip the seed rows here if you'd rather let the app seed them
automatically on first run):

```bash
mysql -u root -p < schema.sql
```

Or just create the empty database and let `app.py` create the table and
seed data on first run:

```sql
CREATE DATABASE rural_startups_db CHARACTER SET utf8mb4;
```

## 2. Configure the connection

The app reads MySQL credentials from environment variables (with local
defaults for `root` / `password` / `localhost`):

```bash
export DB_USER=root
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=rural_startups_db
```

## 3. Install dependencies & run

```bash
python3 -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
python3 app.py
```

The app creates the table (if it doesn't already exist) and seeds the two
baseline field-visit records automatically on first run, then starts on
`http://127.0.0.1:5000`.

## Routes

| Route | Method | Description |
|---|---|---|
| `/` , `/home` | GET | Project overview, objectives, team, methodology |
| `/dashboard` | GET | Metrics + full data table of every visit |
| `/field-work` | GET, POST | Card grid of visits; POST adds a new record with photo upload |
| `/resources` | GET | Intervention areas + downloadable report PDF |

Uploaded photos are saved to `static/uploads/`.

## Notes
- This was smoke-tested end-to-end against SQLite during development (all
  five routes plus the field-work form submission); swap in your MySQL
  credentials as above for production use — no code changes needed.
- The "Download CEP Report" button on the Resources page links to a
  companion PDF summary already included at
  `static/CEP_Report_Technical_Support_Rural_Startups.pdf`.
