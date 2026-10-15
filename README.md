🔗 **Live demo:** https://ishachand03.github.io/SmartComplaint/

The live demo is a browser-only version with sample data (login: `isha@test.com`, password `123456`). The full application, with Flask and MySQL, is in this repository.
# SmartComplaint

A complaint and ticket management system built with Python Flask, MySQL, HTML, CSS and JavaScript.

## Features
- Registration and login with JWT, four roles: Admin, Manager, Support Agent, Customer
- Raise complaints with an automatic reference number (CMP-YYYYMMDD-XXXXXX)
- Rule-based sentiment analysis, priority engine, SLA due dates and department routing
- Ticket lifecycle: Open, Assigned, In Progress, Resolved, Closed, Escalated
- Comments and a unified activity feed
- Automatic escalation of overdue complaints (APScheduler, every 5 minutes)
- Notifications (email switched off by default, mock WhatsApp) with a log
- Dashboards, search, filters and pagination, scoped by role
- Admin configuration and an audit log

## Setup
1. Install Python 3.10+ and MySQL.
2. Create a virtual environment and install packages:
   python -m venv venv
   venv\Scripts\Activate.ps1
   pip install -r requirements.txt
3. Create an empty MySQL database called smartresolve, then import sql/smartresolve.sql.
4. Copy .env.example to .env and fill in your MySQL password and a long JWT_SECRET_KEY.
5. Run: python app.py
6. Open http://127.0.0.1:5000

## Project structure
- app.py, config.py, database.py: application start, settings, database connection
- routes/: API endpoints (auth, complaints, dashboard, admin, users)
- services/: business logic (sentiment, priority, SLA, escalation, notifications, audit)
- templates/ and static/: HTML pages, CSS and JavaScript
- sql/: database export

## Notes
- Demo passwords are for testing only. Change them for real use.
- Never upload the .env file.