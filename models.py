"""SQLAlchemy models for the CEP Rural Startups database."""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Startup(db.Model):
    __tablename__ = "startups"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    startup_name = db.Column(db.String(150), nullable=False)
    founder_name = db.Column(db.String(150), nullable=False)
    photo_filename = db.Column(db.String(255), nullable=True)
    village = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    date_visited = db.Column(db.Date, nullable=False)
    time_visited = db.Column(db.Time, nullable=False)
    technical_support = db.Column(db.Text, nullable=False)
    statement_before = db.Column(db.Text, nullable=False)
    before_tech_support = db.Column(db.Text, nullable=False)
    after_tech_support = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<Startup {self.startup_name} ({self.village})>"
