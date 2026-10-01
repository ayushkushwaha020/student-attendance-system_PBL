# AI-Based Student Attendance System

Flask + SQLite university attendance application for the PBL project.

## Included
- Role-based login: Admin, Teacher, Student
- Student overall/attendance history
- Teacher-scoped attendance marking
- Admin attendance control
- Student directory
- University camera management
- PDF upload and text extraction/classification
- Modern responsive dark dashboard UI
- Render deployment configuration

## Demo accounts
- Admin: admin / admin123
- Teacher: teacher / teacher123
- Student: student / student123

## Run locally
```bash
python -m venv .venv
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Deploy
The repository includes `render.yaml` for a Python/Gunicorn web service.

Note: SQLite is suitable for the demo/prototype. For persistent production data on a cloud deployment, move the database to a managed database or persistent storage.

## Camera / recognition
The camera-management interface stores authorized camera metadata. Browser-compatible WebRTC/HLS streaming and production-grade face-recognition inference require the university camera gateway and recognition runtime to be connected separately.
