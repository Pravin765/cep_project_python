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

-- ------------------------------------------------------------
-- Seed data: two pre-populated field visit records
-- (also inserted automatically by app.py on first run,
--  kept here so the schema can be loaded standalone too)
-- ------------------------------------------------------------

INSERT INTO startups
    (startup_name, founder_name, photo_filename, village, address,
     date_visited, time_visited, technical_support,
     statement_before, before_tech_support, after_tech_support)
VALUES
    (
        'Sunrise Agro Foods',
        'Sunita Patil',
        'team_group_photo.jpg',
        'Vadgaon, Kolhapur',
        'Near Gram Panchayat Office, Vadgaon, Kolhapur, Maharashtra 416003',
        '2025-11-08',
        '11:30:00',
        'UPI Setup, WhatsApp Business, Google Business Listing, Excel Sales/Stock Tracker, Cybersecurity Awareness',
        'We used cash-only transactions and handwritten paper ledgers, and had no way of tracking inventory.',
        'Cash-only sales, no digital records, stock counted by hand once a week, no online presence.',
        'Accepts UPI payments daily, maintains a shared Excel stock sheet, and receives inquiries through a Google Business listing.'
    ),
    (
        'Kalamandir Handicrafts',
        'Ramesh Chavan',
        'team_group_photo.jpg',
        'Panhala, Kolhapur',
        'Main Bazar Road, Panhala, Kolhapur, Maharashtra 416201',
        '2025-11-15',
        '10:00:00',
        'UPI Setup, WhatsApp Business Catalogue, Google Business Listing, Fraud Awareness Training',
        'We relied on word-of-mouth and exhibition sales, and kept zero digital customer records.',
        'No customer database, sales limited to local exhibitions, no awareness of digital payment fraud.',
        'Runs a WhatsApp catalogue reaching buyers outside the village, accepts UPI, and can spot common OTP scams.'
    );
