# AI-Based Student Attendance System

Flask + SQLAlchemy university attendance platform with PostgreSQL support and SQLite local fallback.

## Live Demo

**Student Attendance System:** https://student-attendance-system-pbl.onrender.com

## Core Workflow

```text
Login
 │
 ├── Admin ──────► University / Attendance Management
 ├── Teacher ────► Assigned Lecture Attendance
 └── Student ────► Personal Attendance Dashboard
                         │
                         ▼
                 Recognition / Manual Review
                         │
                         ▼
                  Attendance + Audit Logs
                         │
                         ▼
                    CSV Reports
```

## Included

- One login page with automatic Admin / Teacher / Student role interface
- Password hashing and server-side role authorization
- Subject-wise and overall attendance
- Attendance threshold visualization
- Lecture identification by date, course, section, slot and room
- Teacher attendance override restricted to assigned lectures
- Admin attendance control and manual lecture creation
- Student directory and PDF import preview/confirmation
- University camera management with browser-compatible WebRTC/HLS preview
- Recognition review queue with conservative UNKNOWN handling
- Recognition API with confidence tracking and AI/manual attendance source
- Audit logs
- CSV attendance reports

## Local

```powershell
python -m venv .venv
pip install -r requirements.txt
python app.py
```

## Deployment / Data

Render start command: `gunicorn app:app`.

The current deployed build uses SQLite. A managed PostgreSQL `DATABASE_URL` should be used for persistent production data. Render's ephemeral filesystem should not be treated as permanent storage.

## Demo Access

The application contains seeded demo accounts for evaluation. **Demo credentials are intentionally not published in this README.** Change/remove seeded credentials before any real deployment.

## AI / Camera Notes

The project includes the attendance/recognition data model and API. A production-grade recognition pipeline requires calibrated cameras, validated face embeddings, enrollment quality controls, multi-frame verification and a validated confidence threshold.

RTSP camera streams require an RTSP-to-WebRTC/HLS gateway for browser playback.

## PDF

Text-based PDFs are parsed and shown in a confirmation preview. Image-only/scanned PDFs require OCR infrastructure for reliable import.

## Security Note

This is a portfolio/demo application. Do not use default seeded accounts, demo data, SQLite storage, or an unvalidated recognition pipeline for real university operations without appropriate security, privacy, access-control, database, and recognition validation.
