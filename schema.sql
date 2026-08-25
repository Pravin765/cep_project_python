-- ============================================================
-- CEP Report: Technical Support for Rural Startups
-- Database schema for MySQL
-- ============================================================

CREATE DATABASE IF NOT EXISTS rural_startups_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE rural_startups_db;

DROP TABLE IF EXISTS startups;

CREATE TABLE startups (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    startup_name        VARCHAR(150)  NOT NULL,
    founder_name        VARCHAR(150)  NOT NULL,
    photo_filename      VARCHAR(255),
    village             VARCHAR(100)  NOT NULL,
    address             TEXT          NOT NULL,
    date_visited        DATE          NOT NULL,
    time_visited        TIME          NOT NULL,
    technical_support   TEXT          NOT NULL,
    statement_before     TEXT         NOT NULL,
    before_tech_support  TEXT         NOT NULL,
    after_tech_support    TEXT        NOT NULL,
    created_at          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
