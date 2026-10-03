# AI-Based Student Attendance System

Flask + SQLAlchemy university attendance platform with PostgreSQL support and SQLite local fallback.

## Live Demo

**Student Attendance System:** https://student-attendance-system-pbl.onrender.com

## Included

- One secure login page with automatic Admin / Teacher / Student role interface.
- Password hashing and server-side role authorization.
- Subject-wise and overall attendance.
- Student attendance thresholds: 0–25 black, 25–50 red, 50–75 orange, 75–100 green.
- Lecture identification by date, course, section, slot and room.
- Teacher attendance override restricted to assigned lectures.
- Admin attendance control and manual lecture creation.
- Student directory and safe PDF import preview/confirmation.
- University camera management with browser-compatible WebRTC/HLS preview.
- Recognition review queue and conservative UNKNOWN handling.
- Recognition API with confidence tracking and AI/manual attendance source.
- Audit logs.
- CSV attendance report.
- Production database migration is planned; the current deployed build continues to use SQLite. Do not treat Render's ephemeral filesystem as permanent production storage.

## Demo Access

The application includes seeded demo accounts for evaluation.

**Demo credentials are intentionally not published in this repository README.** Change/remove seeded demo credentials before any real deployment or use with real university data.

## Local

```powershell
python -m venv .venv
pip install -r requirements.txt
python app.py
```

## Render

Start command: `gunicorn app:app`

Use a managed PostgreSQL `DATABASE_URL` for persistent production data.

## AI/camera integration

The application includes the attendance/recognition data model and API. The actual high-accuracy face engine should be connected to a calibrated university-camera pipeline. For high-quality recognition, use deep face embeddings (ArcFace/InsightFace style), multiple enrollment images, quality filtering, multi-frame verification and a validated threshold. Weak matches remain UNKNOWN.

RTSP camera streams are not directly playable by normal browsers; use an RTSP-to-WebRTC/HLS gateway.

## PDF

Text-based PDFs are parsed and shown in a confirmation preview. Image-only/scanned PDFs require OCR infrastructure before reliable import.

## Security Note

This project is a portfolio/demo application. Do not use the default seeded accounts, demo data, SQLite storage, or unvalidated recognition pipeline for production university operations without appropriate security, privacy, access-control, database, and recognition validation work.
