from flask import Flask, request, redirect, url_for, session, render_template_string, flash, send_file
import sqlite3, os, json, csv, io, base64, re, smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from functools import wraps
from html import escape

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")
DB = os.path.join(os.path.dirname(__file__), "attendance.db")
UPLOADS = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS, exist_ok=True)

CSS = """
*{box-sizing:border-box}body{margin:0;background:#07101d;color:#edf3ff;font:14px Inter,system-ui,sans-serif}
a{color:inherit;text-decoration:none}.shell{display:flex;min-height:100vh}.side{position:fixed;left:0;top:0;bottom:0;width:245px;background:#091321;border-right:1px solid #20304a;padding:22px 15px;z-index:3}
.brand{display:flex;gap:10px;align-items:center;padding:4px 10px 25px}.logo{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;overflow:hidden;background:#07101d;border:1px solid #29466f;box-shadow:0 8px 20px #0005}.logo img{width:100%;height:100%;display:block;object-fit:cover;border-radius:inherit}
.brand b{display:block}.brand small{color:#7d8ca5}.nav{color:#8f9db4;font-weight:700;font-size:12px}.nav a{display:block;padding:12px 11px;border-radius:10px;margin:4px 0}.nav a:hover{background:#15233a;color:#fff}
.main{margin-left:245px;width:calc(100% - 245px)}.top{height:82px;border-bottom:1px solid #20304a;padding:18px 30px;display:flex;justify-content:space-between;align-items:center;background:#091321dd;backdrop-filter:blur(12px);position:sticky;top:0;z-index:2}
.top h1{font-size:22px;margin:3px 0}.muted{color:#8291aa}.content{padding:28px;max-width:1500px}.hero,.card{background:linear-gradient(145deg,#101d30,#0b1525);border:1px solid #22344f;border-radius:17px;box-shadow:0 18px 45px #0004}.hero{padding:26px;display:flex;justify-content:space-between;gap:20px;margin-bottom:18px}.hero h2{margin:8px 0;font-size:28px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}.stat{padding:18px}.stat span{display:block;color:#8492aa;font-size:11px}.stat b{display:block;font-size:27px;margin-top:5px}.card{overflow:hidden;margin-bottom:18px}.head{padding:17px 19px;border-bottom:1px solid #22344f;display:flex;justify-content:space-between;align-items:center}.head h3{margin:3px 0}.table{overflow:auto}table{width:100%;border-collapse:collapse;min-width:650px}th,td{text-align:left;padding:12px 15px;border-bottom:1px solid #1b2a40}th{font-size:10px;color:#7888a1;text-transform:uppercase}td b{color:#fff}.btn{display:inline-block;padding:10px 14px;border-radius:10px;border:1px solid #304565;background:#15243a;font-weight:800}.btn.primary{background:linear-gradient(135deg,#6978ff,#4d60dd);border-color:#7180ff}.btn.green{background:#10392f;border-color:#246b55}.form{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;padding:18px}.form label{color:#8492aa;font-size:11px;font-weight:700}.form input,.form select{width:100%;margin-top:6px;padding:11px;border-radius:9px;border:1px solid #2a3d59;background:#07111e;color:#fff}.form .wide{grid-column:1/-1}.flash{padding:12px 15px;border:1px solid #2c4262;background:#101e31;border-radius:10px;margin-bottom:12px}.pill{display:inline-block;padding:5px 8px;border-radius:999px;background:#17294a;color:#9eb0ff;font-size:10px;font-weight:900}.login{min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 70% 10%,#1d2d61,#07101d 45%)}.loginbox{width:min(430px,92vw);padding:30px}.loginbox input{display:block;width:100%;padding:13px;margin:8px 0 14px;border:1px solid #2a3d59;background:#07111e;color:#fff;border-radius:10px}.loginbox button{width:100%;padding:13px;border:0;border-radius:10px;background:#6575ff;color:#fff;font-weight:900}.ring{font-size:38px;font-weight:900;color:#66dfb5}.greenText{color:#55d9ad}.orange{color:#ffb15e}.red{color:#ff6878}.black{color:#fff}.small{font-size:11px}
.stat small{display:block;line-height:1.45}
.attendance-card{position:relative;padding:20px;min-height:182px;display:flex;flex-direction:column;justify-content:space-between;transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease}
.attendance-card:hover{transform:translateY(-3px);border-color:#3a5278;box-shadow:0 22px 50px #0006}
.attendance-code{font-size:11px;color:#91a5c2;font-weight:800;letter-spacing:.04em}
.attendance-name{font-size:14px;font-weight:750;line-height:1.4;min-height:40px;margin-top:8px}
.attendance-percent{font-size:30px;font-weight:950;line-height:1;margin:12px 0}
.attendance-meta{display:flex;gap:16px;flex-wrap:wrap;color:#8fa0b8;font-size:11px}
.attendance-meta b{color:#f4f7ff;font-size:13px;margin-right:3px}
.attendance-status{display:inline-flex;align-items:center;width:max-content;margin-top:10px;padding:5px 9px;border-radius:999px;font-size:10px;font-weight:900;letter-spacing:.02em}
.status-black{background:#151b24;color:#fff;border:1px solid #3b4553}
.status-red{background:#3b1820;color:#ff8793;border:1px solid #71303d}
.status-orange{background:#3a2815;color:#ffc277;border:1px solid #775022}
.status-green{background:#10372d;color:#70e4bd;border:1px solid #246b55}
.overall-box{min-width:245px;padding:18px 20px;border:1px solid #273b59;border-radius:15px;background:#0a1728}
.overall-box .value{font-size:40px;font-weight:950;line-height:1}
.overall-box .label{font-size:11px;color:#8291aa;margin-top:4px}
.overall-breakdown{display:flex;gap:18px;margin-top:14px}
.overall-breakdown span{font-size:10px;color:#8291aa}
.overall-breakdown b{display:block;font-size:16px;color:#fff;margin-top:2px}
.top-profile{display:flex;align-items:center;gap:10px}.initial-avatar{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#6978ff,#43d7ff);color:#fff;border:1px solid #7180ff;font-weight:950;letter-spacing:.02em}.top-profile-name{white-space:nowrap}.top-profile-avatar{width:40px;height:40px;border-radius:50%;object-fit:cover;border:1px solid #304565;display:block}.profile-avatar{width:38px;height:38px;border-radius:12px;object-fit:cover;display:block}.profile-link{display:inline-flex;align-items:center;gap:9px;padding:8px 10px;border:1px solid #273b59;border-radius:11px;background:#0b1728;color:#dce6f8;font-weight:800;transition:.2s}
.profile-link:hover{background:#14243b;border-color:#46618a;transform:translateY(-1px)}
.settings-icon{width:30px;height:30px;display:grid;place-items:center;border-radius:9px;background:#17294a;font-size:16px}
.profile-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:18px}.profile-card{padding:0}.face-panel{padding:22px}
.face-camera{width:100%;aspect-ratio:4/3;max-height:420px;object-fit:cover;border-radius:15px;background:#02070d;border:1px solid #2a3d59;display:block}
.profile-preview{width:110px;height:110px;border-radius:18px;object-fit:cover;display:block;margin:12px 0;border:1px solid #2a3d59}.profile-placeholder{width:110px;height:110px;border-radius:18px;display:grid;place-items:center;background:linear-gradient(135deg,#6978ff,#43d7ff);font-size:28px;font-weight:900;margin:12px 0}.face-preview{display:none}.face-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.timetable-hero{align-items:center}.tt-badge{min-width:145px;text-align:center;padding:14px 18px;border:1px solid #304565;border-radius:14px;background:#0b1728;font-weight:900;font-size:16px}.tt-badge small{font-size:10px;color:#8291aa}.tt-wrap{overflow:auto;padding:4px}.tt-grid{display:grid;grid-template-columns:92px repeat(5,minmax(150px,1fr));grid-template-rows:64px repeat(9,94px);gap:8px;min-width:850px}.tt-day{border:1px solid #263a58;border-radius:13px;background:#111f33;display:flex;flex-direction:column;align-items:center;justify-content:center;font-weight:900}.tt-day small{font-size:10px;color:#8291aa;margin-top:3px}.tt-time{border:1px solid #1f314b;border-radius:12px;background:#0b1728;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#9eacc1}.tt-time b{font-size:12px;color:#dfe8f7}.tt-time small{font-size:10px;margin-top:4px}.tt-cell{border-radius:13px;padding:11px;display:flex;flex-direction:column;justify-content:center;overflow:hidden;transition:.2s}.tt-cell.subject{background:linear-gradient(145deg,#152a49,#102039);border:1px solid #34527b}.tt-cell.subject:hover{transform:translateY(-2px);border-color:#667dff;box-shadow:0 12px 28px #0005}.tt-code{font-size:9px;color:#91a9ff;font-weight:900;letter-spacing:.04em}.tt-cell b{font-size:12px;line-height:1.25;margin:4px 0}.tt-cell small{font-size:9px;color:#91a0b6}.tt-cell em{font-style:normal;font-size:8px;color:#71829b;margin-top:4px}.tt-cell.free{background:#0a1422;border:1px dashed #23354f;align-items:center;color:#51627a;font-size:10px}.tt-legend{display:flex;gap:22px;flex-wrap:wrap;margin-top:14px;color:#8291aa;font-size:11px}.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px}.classdot{background:#6678ff}.freedot{background:#46566c}.face-note{font-size:11px;color:#8291aa;line-height:1.6;margin-top:12px}.face-status{margin-top:12px;min-height:20px;color:#8fa0b8;font-size:12px}
@media(max-width:900px){.profile-grid{grid-template-columns:1fr}}
@media(max-width:900px){.overall-box{min-width:0}}
@media(max-width:900px){.side{width:70px}.brand div:not(.logo),.nav a span{display:none}.main{margin-left:70px;width:calc(100% - 70px)}.grid{grid-template-columns:repeat(2,1fr)}.form{grid-template-columns:1fr}.hero{flex-direction:column}}
"""

IST=ZoneInfo("Asia/Kolkata")

def student_email(name):
    parts=[re.sub(r"[^a-z0-9]","",p.lower()) for p in (name or "").split() if re.sub(r"[^a-z0-9]","",p.lower())]
    if len(parts)<2:
        local_name="".join(parts)
    else:
        local_name=parts[0]+parts[-1]
    return f"{local_name}.aiml2025@agra.sharda.ac.in"

def send_lecture_notification(subject_name, code, lecture_date, start_time, end_time, room, section, course):
    host=os.environ.get("SMTP_HOST","smtp.gmail.com")
    port=int(os.environ.get("SMTP_PORT","587"))
    username=os.environ.get("SMTP_USERNAME","")
    password=os.environ.get("SMTP_PASSWORD","")
    sender=os.environ.get("SMTP_FROM",username)
    if not username or not password or not sender:
        return False, "SMTP credentials are not configured on the server."
    c=db()
    students=c.execute("select name from students where course=? and section=? order by name",(course,section)).fetchall()
    c.close()
    recipients=[student_email(s["name"]) for s in students]
    if not recipients:
        return False, "No student email recipients were found."
    msg=EmailMessage()
    msg["Subject"]=f"Lecture Scheduled: {subject_name} — {lecture_date}"
    msg["From"]=sender
    msg["To"]=sender
    msg.set_content(f"""Dear Students,

A lecture has been scheduled for your class.

Subject: {subject_name}
Subject Code: {code}
Date: {lecture_date}
Time: {start_time} – {end_time}
Room: {room}
Section: {section}
Course: {course}

Please be present on time.

Regards,
Sharda University Agra
Student Attendance System
""")
    try:
        with smtplib.SMTP(host,port,timeout=20) as smtp:
            smtp.starttls()
            smtp.login(username,password)
            smtp.send_message(msg,to_addrs=recipients)
        return True, f"Notification email sent to {len(recipients)} students."
    except Exception as exc:
        return False, f"Lecture was created, but email notification failed: {exc}"

def db():
    c=sqlite3.connect(DB, timeout=15)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA busy_timeout=15000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    return c

def init():
    c=db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password TEXT,role TEXT,display_name TEXT,student_id INTEGER,teacher_id INTEGER);
    CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY,enrollment_no TEXT UNIQUE,roll_no TEXT,name TEXT,course TEXT DEFAULT 'B.Tech',semester INTEGER DEFAULT 3,section TEXT DEFAULT 'C',group_name TEXT);
    CREATE TABLE IF NOT EXISTS teachers(id INTEGER PRIMARY KEY,employee_code TEXT UNIQUE,name TEXT);
    CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY,code TEXT UNIQUE,name TEXT,semester INTEGER,section TEXT,teacher_id INTEGER);
    CREATE TABLE IF NOT EXISTS lectures(id INTEGER PRIMARY KEY,subject_id INTEGER,teacher_id INTEGER,lecture_no INTEGER,course TEXT,section TEXT,room TEXT,lecture_date TEXT,start_time TEXT,end_time TEXT,group_name TEXT,slot_label TEXT,lecture_day TEXT,effective_from TEXT,status TEXT DEFAULT 'SCHEDULED',source_file_id INTEGER);
    CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY,student_id INTEGER,subject_id INTEGER,lecture_id INTEGER,attendance_date TEXT,source TEXT,marked_by INTEGER,UNIQUE(student_id,lecture_id,attendance_date));
    CREATE TABLE IF NOT EXISTS cameras(id INTEGER PRIMARY KEY,camera_name TEXT,location TEXT,stream_url TEXT,authorized INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS student_face_profiles(id INTEGER PRIMARY KEY,student_id INTEGER NOT NULL,image_data TEXT NOT NULL,captured_at TEXT DEFAULT CURRENT_TIMESTAMP,is_active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS document_configs(kind TEXT PRIMARY KEY,payload TEXT NOT NULL,source_name TEXT,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    cols={row["name"] for row in c.execute("pragma table_info(students)").fetchall()}
    if "roll_no" not in cols:
        c.execute("alter table students add column roll_no text")
    if "group_name" not in cols:
        c.execute("alter table students add column group_name text")
    if "profile_picture" not in cols:
        c.execute("alter table students add column profile_picture text")
    subject_cols={row["name"] for row in c.execute("pragma table_info(subjects)").fetchall()}
    if "teacher_id" not in subject_cols:
        c.execute("alter table subjects add column teacher_id integer")
    lecture_cols={row["name"] for row in c.execute("pragma table_info(lectures)").fetchall()}
    for col,typ in [("start_time","text"),("end_time","text"),("group_name","text"),("slot_label","text"),("lecture_day","text"),("effective_from","text"),("status","text"),("source_file_id","integer")]:
        if col not in lecture_cols:
            c.execute(f"alter table lectures add column {col} {typ}")
    data_path=os.path.join(os.path.dirname(__file__),"data","semester_3_c.json")
    if os.path.exists(data_path):
        with open(data_path,"r",encoding="utf-8") as f:
            seed=json.load(f)

        target=next((s for s in seed.get("students",[]) if s["name"].upper()=="DIVYAANSH VASHISTHA"),None)
        demo=c.execute("select * from students where enrollment_no='DEMO001'").fetchone()
        target_row=c.execute("select * from students where enrollment_no=?",(target["admission_no"],)).fetchone() if target else None
        if demo and target and not target_row:
            c.execute("update students set enrollment_no=?,roll_no=?,name=?,course=?,semester=?,section=?,group_name=? where id=?",(target["admission_no"],target["roll_no"],target["name"],seed["course"],seed["semester"],"C",target.get("group"),demo["id"]))
            c.execute("update users set username=?,password=?,display_name=?,student_id=? where student_id=?",(target["admission_no"],target["roll_no"],target["name"],demo["id"],demo["id"]))

        for s in seed.get("students",[]):
            row=c.execute("select id from students where enrollment_no=?",(s["admission_no"],)).fetchone()
            if row:
                sid=row["id"]
                c.execute("update students set roll_no=?,name=?,course=?,semester=?,section=?,group_name=? where id=?",(s["roll_no"],s["name"],seed["course"],seed["semester"],"C",s.get("group"),sid))
            else:
                c.execute("insert into students(enrollment_no,roll_no,name,course,semester,section,group_name) values(?,?,?,?,?,?,?)",(s["admission_no"],s["roll_no"],s["name"],seed["course"],seed["semester"],"C",s.get("group")))
                sid=c.execute("select last_insert_rowid()").fetchone()[0]
            user=c.execute("select id from users where student_id=?",(sid,)).fetchone()
            if user:
                c.execute("update users set username=?,password=?,role='STUDENT',display_name=? where id=?",(s["admission_no"],s["roll_no"],s["name"],user["id"]))
            else:
                c.execute("insert or ignore into users(username,password,role,display_name,student_id) values(?,?,?,?,?)",(s["admission_no"],s["roll_no"],"STUDENT",s["name"],sid))

        teacher_ids={}
        for t in seed.get("teachers",[]):
            row=c.execute("select id from teachers where employee_code=?",(t["employee_code"],)).fetchone()
            if row:
                tid=row["id"]
                c.execute("update teachers set name=? where id=?",(t["name"],tid))
            else:
                c.execute("insert into teachers(employee_code,name) values(?,?)",(t["employee_code"],t["name"]))
                tid=c.execute("select last_insert_rowid()").fetchone()[0]
            teacher_ids[t["employee_code"]]=tid
            existing=c.execute("select id from users where teacher_id=?",(tid,)).fetchone()
            if existing:
                teacher_subject_codes=[x["code"] for x in seed.get("subjects",[]) if x.get("teacher_code")==t["employee_code"]]
                teacher_password=teacher_subject_codes[0] if teacher_subject_codes else t["employee_code"]
                teacher_username=t["name"].replace("Prof. Dr. ","").replace("Dr. ","").replace("Prof. ","").strip().upper()
                c.execute("update users set username=?,password=?,role='TEACHER',display_name=? where id=?",(teacher_username,teacher_password,t["name"],existing["id"]))
            else:
                teacher_subject_codes=[x["code"] for x in seed.get("subjects",[]) if x.get("teacher_code")==t["employee_code"]]
                teacher_password=teacher_subject_codes[0] if teacher_subject_codes else t["employee_code"]
                teacher_username=t["name"].replace("Prof. Dr. ","").replace("Dr. ","").replace("Prof. ","").strip().upper()
                c.execute("insert or ignore into users(username,password,role,display_name,teacher_id) values(?,?,?,?,?)",(teacher_username,teacher_password,"TEACHER",t["name"],tid))

        legacy={"DSA":"BECS301A","AIML":"BEAI302A","IOT":"BEAI301","MATH":"BEMT301"}
        for old,new in legacy.items():
            if c.execute("select id from subjects where code=?",(old,)).fetchone() and not c.execute("select id from subjects where code=?",(new,)).fetchone():
                c.execute("update subjects set code=? where code=?",(new,old))
        old_ai=c.execute("select id from subjects where code='BEAI302'").fetchone()
        new_ai=c.execute("select id from subjects where code='BEAI302A'").fetchone()
        if old_ai and new_ai:
            c.execute("update lectures set subject_id=? where subject_id=?",(new_ai["id"],old_ai["id"]))
            c.execute("update attendance set subject_id=? where subject_id=?",(new_ai["id"],old_ai["id"]))
            c.execute("delete from subjects where id=?",(old_ai["id"],))

        for s in seed.get("subjects",[]):
            tid=teacher_ids.get(s.get("teacher_code"))
            row=c.execute("select id from subjects where code=?",(s["code"],)).fetchone()
            if row:
                c.execute("update subjects set name=?,semester=?,section=?,teacher_id=? where id=?",(s["name"],seed["semester"],"C",tid,row["id"]))
            else:
                c.execute("insert into subjects(code,name,semester,section,teacher_id) values(?,?,?,?,?)",(s["code"],s["name"],seed["semester"],"C",tid))
            if tid:
                c.execute("update lectures set teacher_id=? where subject_id=(select id from subjects where code=?) and teacher_id is null",(tid,s["code"]))

        # The browser login-device camera is the default camera. It is a
        # virtual camera entry backed by navigator.mediaDevices.getUserMedia().
        # Never recreate the old Room 222 camera.
        c.execute("delete from cameras where lower(camera_name) like '%room 222%' or lower(location)=? or lower(camera_name)=?",(str(seed.get("room","222")).lower(),"login device camera"))
        if c.execute("select count(*) from cameras").fetchone()[0]==0:
            c.execute("insert into cameras(camera_name,location,stream_url,authorized) values(?,?,?,1)",("Login Device Camera","This device","LOCAL_DEVICE"))
        elif not c.execute("select 1 from cameras where lower(camera_name)=? limit 1",("login device camera",)).fetchone():
            c.execute("insert into cameras(camera_name,location,stream_url,authorized) values(?,?,?,1)",("Login Device Camera","This device","LOCAL_DEVICE"))
    else:
        if c.execute("select count(*) from users").fetchone()[0]==0:
            c.execute("insert into teachers(employee_code,name) values('T001','Demo Teacher')")
            tid=c.execute("select last_insert_rowid()").fetchone()[0]
            c.execute("insert into students(enrollment_no,roll_no,name,course,semester,section,group_name) values('DEMO001','DEMO001','Demo Student','B.Tech',3,'C','25aiml(26c1)')")
            sid=c.execute("select last_insert_rowid()").fetchone()[0]
            c.execute("insert into users(username,password,role,display_name,teacher_id) values('teacher','teacher123','TEACHER','Demo Teacher',?)",(tid,))
            c.execute("insert into users(username,password,role,display_name,student_id) values('student','student123','STUDENT','Demo Student',?)",(sid,))
    saved_students=c.execute("select payload from document_configs where kind='STUDENT_LIST'").fetchone()
    if saved_students:
        try:
            imported=json.loads(saved_students["payload"])
            for s in imported:
                row=c.execute("select id from students where enrollment_no=?",(s["admission_no"],)).fetchone()
                if row:
                    sid=row["id"]
                    c.execute("update students set roll_no=?,name=?,course=?,semester=?,section=?,group_name=? where id=?",
                              (s["roll_no"],s["name"],s["course"],s["semester"],s["section"],s.get("group"),sid))
                else:
                    c.execute("insert into students(enrollment_no,roll_no,name,course,semester,section,group_name) values(?,?,?,?,?,?,?)",
                              (s["admission_no"],s["roll_no"],s["name"],s["course"],s["semester"],s["section"],s.get("group")))
                    sid=c.execute("select last_insert_rowid()").fetchone()[0]
                user=c.execute("select id from users where student_id=?",(sid,)).fetchone()
                if user:
                    c.execute("update users set username=?,password=?,role='STUDENT',display_name=? where id=?",
                              (s["admission_no"],s["roll_no"],"STUDENT",s["name"],user["id"]))
                else:
                    c.execute("insert or ignore into users(username,password,role,display_name,student_id) values(?,?,?,?,?)",
                              (s["admission_no"],s["roll_no"],"STUDENT",s["name"],sid))
        except Exception:
            pass

    admin_user=c.execute("select id from users where role='ADMIN' order by id limit 1").fetchone()
    if not admin_user:
        c.execute("insert into users(username,password,role,display_name) values('SHARDA.AGRA','admin123','ADMIN','Sharda University Agra Administrator')")
    else:
        c.execute("update users set username='SHARDA.AGRA', display_name='Sharda University Agra Administrator' where id=?",(admin_user["id"],))
    c.commit(); c.close()

def sync_admin_accounts():
    """Replace all ADMIN accounts with the credentials configured in Render."""
    raw=os.environ.get("ADMIN_ACCOUNTS_JSON","").strip()
    if not raw:
        return
    try:
        accounts=json.loads(raw)
        if not isinstance(accounts,list) or not accounts:
            return
    except Exception:
        return
    c=db()
    c.execute("delete from users where role='ADMIN'")
    for account in accounts:
        username=str(account.get("username","")).strip()
        password=str(account.get("password",""))
        if username and password:
            c.execute("insert into users(username,password,role,display_name) values(?,?,?,?)",
                      (username,password,"ADMIN",username))
    c.commit()
    c.close()

def me():
    if "uid" not in session:return None
    c=db(); u=c.execute("select * from users where id=?",(session["uid"],)).fetchone(); c.close(); return u

def need(*roles):
    def deco(f):
        @wraps(f)
        def w(*a,**k):
            u=me()
            if not u:return redirect(url_for("login"))
            if roles and u["role"] not in roles:
                flash("Access denied.","danger"); return redirect(url_for("dashboard"))
            return f(*a,**k)
        return w
    return deco

def page(title,body,**ctx):
    u=me()
    profile_picture=""
    initials=""
    if u and u["role"]=="STUDENT":
        cc=db(); pp=cc.execute("select profile_picture from students where id=?",(u["student_id"],)).fetchone(); cc.close()
        profile_picture=pp["profile_picture"] if pp and pp["profile_picture"] else ""
        initials="".join(part[0] for part in (u["display_name"] or "").split() if part)[:2].upper() or "A"
    nav=""
    if u:
        nav=f'<aside class="side"><div class="brand"><div class="logo"><img src="/static/attendai-logo.svg" alt="Sharda University Agra"></div><div><b>Sharda University Agra</b><small>Student Attendance System</small></div></div><nav class="nav"><a href="/dashboard">⌂ Dashboard</a>'
        if u["role"] in ("ADMIN","TEACHER"): nav+='<a href="/attendance">✓ Attendance</a><a href="/lectures">◷ Lectures</a>'
        if u["role"]=="ADMIN": nav+='<a href="/import">⇧ PDF Import</a><a href="/students">♙ Students</a><a href="/lectures">◷ Lectures</a><a href="/cameras">◉ Cameras</a><a href="/recognition">◎ Recognition</a><a href="/reports">▥ Reports</a><a href="/audit">⌁ Audit Logs</a>'
        if u["role"]=="STUDENT": nav+='<a href="/student/attendance">▤ My Attendance</a><a href="/student/timetable">▦ Time Table</a>'
        nav+='<a href="/logout">↪ Logout</a></nav></aside>'
    flashes="".join(f'<div class="flash">{m}</div>' for m in [x[1] for x in []])
    html=f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body>
    <div class="shell">{nav}<main class="main"><header class="top"><div><span class="pill">AI ATTENDANCE</span><h1>{title}</h1></div><div class="top-profile">{(f'<a class="profile-link" href="/student/profile" title="Edit profile"><span class="settings-icon">⚙</span></a><span class="top-profile-name">{u["display_name"]}</span>{f'<img class="top-profile-avatar" src="{profile_picture}" alt="Profile">' if profile_picture else f'<div class="initial-avatar">{initials}</div>'}' if u and u["role"]=="STUDENT" else f'<span class="muted">{u["display_name"] if u else "Secure Login"}</span>')}</div></header><section class="content">{flashes}{body}</section></main></div></body></html>"""
    return html

@app.route("/")
def home(): return redirect(url_for("dashboard") if me() else url_for("login"))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        c=db(); username=request.form["username"].strip()
        password=request.form["password"]
        u=c.execute("select * from users where username=? and password=?",(username,password)).fetchone()
        if not u:
            # Teacher login: username is the teacher's full name in ALL CAPS.
            # Accept any subject code assigned to that teacher as the password.
            u=c.execute("""select u.* from users u join teachers t on t.id=u.teacher_id
                           join subjects s on s.teacher_id=t.id
                           where u.role='TEACHER' and upper(trim(replace(replace(replace(t.name,'Prof. Dr. ',''),'Dr. ',''),'Prof. ','')))=? and (s.teacher_id=t.id or exists (select 1 from lectures lx where lx.subject_id=s.id and lx.teacher_id=t.id)) and s.code=?""",
                        (username.upper(),password.upper())).fetchone()
        c.close()
        if u:
            session["uid"]=u["id"]
            audit("LOGIN_SUCCESS","user",u["id"],"Successful "+u["role"]+" login")
            return redirect(url_for("dashboard"))
        audit("LOGIN_FAILED","user",None,"Failed login attempt for username: "+username)
        flash("Invalid credentials.","danger")
    return render_template_string("""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>""" + CSS + """</style></head><body class="login"><form class="loginbox card" method="post"><div class="brand"><div class="logo"><img src="/static/attendai-logo.svg" alt="Sharda University Agra"></div><div><b>Sharda University Agra</b><small>Student Attendance System</small></div></div><h2>Sign in</h2><p class="muted">Role is loaded automatically from your account.</p><input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Password" required><button>Sign in</button><p class="small muted" style="text-align:center;margin-top:16px">New student? <a href="/register" style="color:#8d9aff;font-weight:800">Register here</a></p></form></body></html>""")

@app.route("/register",methods=["GET","POST"])
def register():
    if me():
        return redirect(url_for("dashboard"))
    error=""
    if request.method=="POST":
        name=request.form.get("name","").strip()
        enrollment=request.form.get("enrollment_no","").strip()
        username=request.form.get("username","").strip()
        password=request.form.get("password","")
        confirm=request.form.get("confirm_password","")
        course=request.form.get("course","B.Tech").strip() or "B.Tech"
        try:
            semester=int(request.form.get("semester","3"))
        except ValueError:
            semester=3
        section=request.form.get("section","C").strip() or "C"

        if not all([name,enrollment,username,password,confirm]):
            error="Please fill in all required fields."
        elif password != confirm:
            error="Passwords do not match."
        elif len(password) < 6:
            error="Password must be at least 6 characters."
        else:
            c=db()
            try:
                if c.execute("select id from students where enrollment_no=?",(enrollment,)).fetchone():
                    error="This enrollment number is already registered."
                elif c.execute("select id from users where username=?",(username,)).fetchone():
                    error="This username is already taken."
                else:
                    c.execute("insert into students(enrollment_no,name,course,semester,section,group_name) values(?,?,?,?,?,?)",(enrollment,name,course,semester,section,""))
                    sid=c.execute("select last_insert_rowid()").fetchone()[0]
                    c.execute("insert into users(username,password,role,display_name,student_id) values(?,?,?,?,?)",(username,password,"STUDENT",name,sid))
                    c.commit()
                    c.close()
                    return redirect(url_for("login",registered="1"))
            except sqlite3.IntegrityError:
                c.rollback()
                error="Registration could not be completed. Please check your details."
            c.close()

    return render_template_string("""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>""" + CSS + """</style></head><body class="login"><form class="loginbox card" method="post">
    <div class="brand"><div class="logo"><img src="/static/attendai-logo.svg" alt="Sharda University Agra"></div><div><b>Sharda University Agra</b><small>Student Attendance System</small></div></div>
    <h2>Register New Student</h2><p class="muted">Create your student account to access your attendance portal.</p>
    {% if error %}<div class="flash">{{ error }}</div>{% endif %}
    <input name="name" placeholder="Full Name" required>
    <input name="enrollment_no" placeholder="Enrollment Number" required>
    <input name="username" placeholder="Create Username" required>
    <input name="password" type="password" placeholder="Create Password" required>
    <input name="confirm_password" type="password" placeholder="Confirm Password" required>
    <input name="course" value="B.Tech" placeholder="Course" required>
    <input name="semester" type="number" min="1" max="10" value="3" placeholder="Semester" required>
    <input name="section" value="C" placeholder="Section" required>
    <button>Register Student</button>
    <p class="small muted" style="text-align:center;margin-top:16px">Already registered? <a href="/login" style="color:#8d9aff;font-weight:800">Back to Login</a></p>
    </form></body></html>""", error=error)

@app.route("/logout")
def logout():
    u=me()
    if u: audit("LOGOUT","user",u["id"],"User logged out")
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@need()
def dashboard():
    u=me(); c=db()
    if u["role"]=="STUDENT":
        st=c.execute("select * from students where id=?",(u["student_id"],)).fetchone()
        rows=c.execute("""select s.name,s.code,count(l.id) total,
        (select count(*) from attendance a where a.student_id=? and a.subject_id=s.id and a.source in ('TEACHER_OVERRIDE','ADMIN_OVERRIDE','AI_RECOGNITION')) present
        from subjects s left join lectures l on l.subject_id=s.id and l.course=? and l.section=?
          and l.status='PDF_SCHEDULED'
          and s.code not in ('SELF','MENTOR')
          and (l.group_name is null or l.group_name='' or l.group_name=?)
        where s.semester=? and s.section=? and s.code not in ('SELF','MENTOR') group by s.id order by s.code""",
        (st["id"],st["course"],st["section"],st["group_name"],st["semester"],st["section"])).fetchall()
        total=sum(r["total"] for r in rows); present=sum(min(r["present"],r["total"]) for r in rows); absent=max(total-present,0); overall=(present/total*100 if total else 0)
        def att_class(p):
            return "black" if p<=25 else "red" if p<50 else "orange" if p<75 else "greenText"
        def att_class(p):
            return "black" if p <= 25 else "red" if p < 50 else "orange" if p < 75 else "greenText"

        def status_class(p):
            return "status-black" if p <= 25 else "status-red" if p < 50 else "status-orange" if p < 75 else "status-green"

        def status_label(p):
            return "0–25% · Low" if p <= 25 else "25–50% · Needs Improvement" if p < 50 else "50–75% · Average" if p < 75 else "75–100% · Good"

        cards=""
        for r in rows:
            pct=(r["present"]/r["total"]*100 if r["total"] else 0)
            present_count=min(r["present"],r["total"])
            absent_count=max(r["total"]-present_count,0)
            cards += f'''<div class="card attendance-card">
                <div>
                    <div class="attendance-code">{r["code"]}</div>
                    <div class="attendance-name">{r["name"]}</div>
                    <div class="attendance-percent {att_class(pct)}">{pct:.0f}%</div>
                    <div class="attendance-meta">
                        <span><b>{present_count}</b> Present</span>
                        <span><b>{absent_count}</b> Absent</span>
                        <span><b>{r["total"]}</b> Total</span>
                    </div>
                </div>
                <span class="attendance-status {status_class(pct)}">{status_label(pct)}</span>
            </div>'''
        c.close()
        body=f'''<div class="hero">
            <div>
                <span class="pill">STUDENT PORTAL</span>
                <h2>{st["name"]}</h2>
                <p class="muted">Admission: {st["enrollment_no"]} · Roll No: {st["roll_no"] or "—"} · {st["course"]} · Semester {st["semester"]} · Section {st["section"]}</p>
            </div>
            <div class="overall-box">
                <div class="value {att_class(overall)}">{overall:.0f}%</div>
                <div class="label">OVERALL ATTENDANCE</div>
                <div class="overall-breakdown">
                    <div><span>Present</span><b>{present}</b></div>
                    <div><span>Absent</span><b>{absent}</b></div>
                    <div><span>Total</span><b>{total}</b></div>
                </div>
            </div>
        </div>
        <div class="head" style="padding:0 2px 12px;border:0"><h3>Subject-wise Attendance</h3><span class="muted small">{len(rows)} subjects</span></div>
        <div class="grid">{cards}</div>
        <div class="card">
            <div class="head"><h3>Attendance Summary</h3><span class="pill">{overall:.0f}% overall</span></div>
            <div style="padding:20px;display:flex;gap:35px;flex-wrap:wrap">
                <div><span class="muted">Present</span><b style="display:block;font-size:25px">{present}</b></div>
                <div><span class="muted">Absent</span><b style="display:block;font-size:25px">{absent}</b></div>
                <div><span class="muted">Total Lectures</span><b style="display:block;font-size:25px">{total}</b></div>
            </div>
        </div>
        <a class="btn primary" href="/student/attendance">View attendance history →</a>'''
        return page("My Attendance",body)
    if u["role"]=="TEACHER":
        t=c.execute("select * from teachers where id=?",(u["teacher_id"],)).fetchone()
        ls=c.execute("select l.*,s.code,s.name subject_name from lectures l join subjects s on s.id=l.subject_id where (l.teacher_id=? or s.teacher_id=?) and s.code not in ('SELF','MENTOR') order by l.lecture_date desc,l.lecture_no",(u["teacher_id"],u["teacher_id"])).fetchall(); c.close()
        rows="".join(f'<tr onclick="location.href=\'/attendance?lecture_id={l["id"]}\'" style="cursor:pointer"><td>{l["lecture_date"]}</td><td>Slot {l["lecture_no"]}</td><td><b>{l["subject_name"]}</b><small>{l["code"]}</small></td><td>{l["start_time"] or ""}–{l["end_time"] or ""}</td><td>{l["room"]}</td></tr>' for l in ls) or '<tr><td colspan="5">No assigned lectures.</td></tr>'
        return page("Teacher Dashboard",f'<div class="hero"><div><span class="pill">TEACHER WORKSPACE</span><h2>Hello, {t["name"]}</h2><p class="muted">Click any lecture to open its attendance sheet.</p></div></div><div class="card"><div class="head"><h3>All Assigned Lectures</h3><span class="pill">{len(ls)} lectures</span></div><div class="table"><table><tr><th>Date</th><th>Slot</th><th>Subject</th><th>Time</th><th>Room</th></tr>{rows}</table></div></div>')
    students=c.execute("select * from students order by name").fetchall()
    teachers=c.execute("select * from teachers order by name").fetchall()
    stats=[("Students",len(students)),("Teachers",len(teachers)),("Cameras",c.execute("select count(*) from cameras").fetchone()[0]),("Attendance",c.execute("select count(*) from attendance").fetchone()[0])]
    c.close()
    cards="".join(f'<div class="card stat"><span>{n}</span><b>{v}</b></div>' for n,v in stats)
    student_rows="".join(f'<tr><td><b>{st["name"]}</b></td><td>{st["enrollment_no"]}</td><td>{st["roll_no"] or "—"}</td><td>{st["course"]}</td><td>Sem {st["semester"]}</td><td>{st["section"]}</td><td>{st["group_name"] or "—"}</td></tr>' for st in students)
    teacher_rows="".join(f'<tr><td><b>{t["name"]}</b></td><td>{t["employee_code"]}</td><td>{t["id"]}</td></tr>' for t in teachers)
    body=f'''<div class="hero"><div><span class="pill">ADMIN CONTROL CENTER</span><h2>University Attendance</h2><p class="muted">Manage students, teachers, cameras, PDF data and attendance overrides.</p></div><a class="btn primary" href="/import">Import PDF →</a></div>
    <div class="grid">{cards}</div>
    <div class="grid" style="grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:start">
      <div class="card"><div class="head"><h3>Students</h3><span class="pill">{len(students)} students</span></div><div class="table" style="max-height:650px;overflow:auto"><table><tr><th>Name</th><th>Admission</th><th>Roll No.</th><th>Course</th><th>Semester</th><th>Section</th><th>Group</th></tr>{student_rows}</table></div></div>
      <div class="card"><div class="head"><h3>Teachers</h3><span class="pill">{len(teachers)} teachers</span></div><div class="table" style="max-height:650px;overflow:auto"><table><tr><th>Name</th><th>Employee Code</th><th>ID</th></tr>{teacher_rows}</table></div></div>
    </div>'''
    return page("Admin Dashboard",body)

@app.route("/attendance",methods=["GET","POST"])
@need("ADMIN","TEACHER")
def attendance():
    c=db(); u=me()
    if u["role"]=="TEACHER":
        # A teacher owns every lecture whose subject is assigned to their
        # teacher profile. The lecture-level teacher_id is kept as a fallback
        # for older records created before subject assignments were corrected.
        lectures=c.execute("""select l.*,s.code,s.name subject_name from lectures l join subjects s on s.id=l.subject_id
            where (l.teacher_id=? or s.teacher_id=?) and s.code not in ('SELF','MENTOR')
            order by l.lecture_date desc,l.lecture_no""",(u["teacher_id"],u["teacher_id"])).fetchall()
    else:
        lectures=c.execute("""select l.*,s.code,s.name subject_name from lectures l join subjects s on s.id=l.subject_id
            where s.code not in ('SELF','MENTOR') order by l.lecture_date desc,l.lecture_no""").fetchall()
    requested=int(request.args.get("lecture_id","0") or 0)
    selected=next((l for l in lectures if l["id"]==requested), lectures[0] if lectures else None)
    if request.method=="POST":
        lecture_id=int(request.form["lecture_id"]); selected=next((l for l in lectures if l["id"]==lecture_id),None)
        if not selected or (u["role"]=="TEACHER" and selected["teacher_id"]!=u["teacher_id"]):
            c.close(); flash("Lecture not found or not assigned to you.","danger"); return redirect(url_for("attendance"))
        if selected["group_name"]:
            students=c.execute("""select * from students where course=? and section=? and group_name=? order by cast(roll_no as integer)""",(selected["course"],selected["section"],selected["group_name"])).fetchall()
        else:
            students=c.execute("""select * from students where course=? and section=? order by cast(roll_no as integer)""",(selected["course"],selected["section"])).fetchall()
        ps="TEACHER_OVERRIDE" if u["role"]=="TEACHER" else "ADMIN_OVERRIDE"; aas="TEACHER_ABSENT" if u["role"]=="TEACHER" else "ADMIN_ABSENT"
        for st in students:
            src=ps if request.form.get(f"status_{st['id']}","A")=="P" else aas
            marked=u["id"] if src==ps else None
            c.execute("""insert into attendance(student_id,subject_id,lecture_id,attendance_date,source,marked_by) values(?,?,?,?,?,?)
                on conflict(student_id,lecture_id,attendance_date) do update set subject_id=excluded.subject_id,source=excluded.source,marked_by=excluded.marked_by""",
                (st["id"],selected["subject_id"],lecture_id,selected["lecture_date"],src,marked))
        c.commit()
        audit("SAVE_ATTENDANCE","lecture",lecture_id,"Attendance saved for "+str(len(students))+" students by "+u["display_name"])
        c.close(); flash("Attendance saved successfully.","success")
        return redirect(url_for("attendance",lecture_id=lecture_id))
    if selected:
        # For an all-section lecture, show every student in the course/section.
        # Only group-specific lectures are filtered to that group.
        if selected["group_name"]:
            students=c.execute("""select * from students where course=? and section=? and group_name=? order by cast(roll_no as integer)""",(selected["course"],selected["section"],selected["group_name"])).fetchall()
        else:
            students=c.execute("""select * from students where course=? and section=? order by cast(roll_no as integer)""",(selected["course"],selected["section"])).fetchall()
        present={x["student_id"] for x in c.execute("select student_id from attendance where lecture_id=? and source in ('TEACHER_OVERRIDE','ADMIN_OVERRIDE','AI_RECOGNITION')",(selected["id"],)).fetchall()}
    else: students=[]; present=set()
    c.close()
    lecture_cards="".join(f'<a class="lec-link {"active" if selected and l["id"]==selected["id"] else ""}" href="/attendance?lecture_id={l["id"]}"><b>{l["lecture_date"]} · Slot {l["lecture_no"]}</b><small>{l["subject_name"]} · {l["code"]}<br>{l["start_time"] or ""}–{l["end_time"] or ""} · Room {l["room"]}</small></a>' for l in lectures)
    rows=""
    for i,st in enumerate(students):
        p=st["id"] in present
        rows+=f'<div class="student-row {"is-present" if p else ""}" id="student-row-{i}" onclick="selectStudent({i})"><span class="student-no">{i+1}</span><div class="student-info"><b>{st["name"]}</b><small>{st["enrollment_no"]}</small></div><button type="button" class="status-toggle {"on" if p else ""}" id="toggle-{i}" onclick="event.stopPropagation();toggleStudent({i})"><span></span></button><input type="hidden" name="status_{st["id"]}" id="status-{i}" value="{"P" if p else "A"}"><span class="status-text" id="status-text-{i}">{"PRESENT" if p else "ABSENT"}</span></div>'
    body=f"""<style>
.att-layout{{display:grid;grid-template-columns:300px 1fr;gap:18px;align-items:start}}.lecture-list{{max-height:70vh;overflow:auto}}.lec-link{{display:block;padding:12px 14px;margin:6px 0;border:1px solid #24354f;border-radius:12px;text-decoration:none;color:#fff;background:#0c1728}}.lec-link.active,.lec-link:hover{{border-color:#557dbb;background:#142747}}.lec-link small{{display:block;color:#8293ac;margin-top:5px;line-height:1.6}}.student-row{{display:flex;align-items:center;gap:14px;padding:13px 15px;margin:7px 0;border:1px solid #24354f;border-radius:13px;background:#0b1627;cursor:pointer}}.student-row.active{{border-color:#557dbb;background:#11213a}}.student-row.is-present{{border-color:#285b4b}}.student-no{{width:28px;color:#7f91ab;font-weight:800}}.student-info{{flex:1}}.student-info b,.student-info small{{display:block}}.student-info small{{color:#71829c;margin-top:3px}}.status-toggle{{width:54px;height:29px;border:0;border-radius:20px;background:#303e52;padding:3px;cursor:pointer}}.status-toggle span{{display:block;width:23px;height:23px;border-radius:50%;background:#aab6c7;transition:.18s}}.status-toggle.on{{background:#19a56f}}.status-toggle.on span{{transform:translateX(25px);background:#fff}}.status-text{{width:72px;font-size:10px;font-weight:900;color:#8c9bb0}}.is-present .status-text{{color:#35d89a}}.key-btn{{min-width:48px;padding:9px 15px;border-radius:10px;font-weight:900}}@media(max-width:900px){{.att-layout{{grid-template-columns:1fr}}.lecture-list{{max-height:280px}}}}
</style><div class="att-layout"><div class="card"><div class="head"><h3>All Lectures</h3><span class="pill">{len(lectures)}</span></div><div class="lecture-list">{lecture_cards or '<p class="muted">No lectures assigned.</p>'}</div></div><div class="card"><div class="head"><div><span class="pill">ATTENDANCE SHEET</span><h2 style="margin:8px 0 3px">{selected["subject_name"] if selected else "No Lecture Selected"}</h2><p class="muted">{selected["lecture_date"] if selected else ""} · Slot {selected["lecture_no"] if selected else ""} · {selected["start_time"] if selected else ""}–{selected["end_time"] if selected else ""} · Room {selected["room"] if selected else ""}</p></div><span class="pill">{len(students)} students</span></div>{f'''<form method="post" id="attendance-form"><input type="hidden" name="lecture_id" value="{selected["id"]}"><div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0 15px"><span class="muted small">Click a student, then press <b>P</b> or <b>A</b>. It automatically moves to the next student.</span><div><button type="button" class="btn key-btn" onclick="markCurrent('P')">P</button> <button type="button" class="btn key-btn" onclick="markCurrent('A')">A</button></div></div>{rows}<div style="margin-top:16px;text-align:right"><button class="btn green" type="submit">Save Attendance</button></div></form><script>
let current=0,total={len(students)};function selectStudent(i){{if(i<0||i>=total)return;current=i;document.querySelectorAll(".student-row").forEach(x=>x.classList.remove("active"));let r=document.getElementById("student-row-"+i);if(r){{r.classList.add("active");r.scrollIntoView({{block:"nearest",behavior:"smooth"}})}}}}function setStudent(i,v,next){{document.getElementById("status-"+i).value=v;let t=document.getElementById("toggle-"+i),r=document.getElementById("student-row-"+i),s=document.getElementById("status-text-"+i);t.classList.toggle("on",v==="P");r.classList.toggle("is-present",v==="P");s.textContent=v==="P"?"PRESENT":"ABSENT";selectStudent(i);if(next&&i+1<total)setTimeout(()=>selectStudent(i+1),120)}}function toggleStudent(i){{setStudent(i,document.getElementById("status-"+i).value==="P"?"A":"P",true)}}function markCurrent(v){{setStudent(current,v,true)}}document.addEventListener("keydown",e=>{{if(e.target.matches("input,textarea"))return;if(e.key.toLowerCase()==="p"||e.key.toLowerCase()==="a"){{e.preventDefault();markCurrent(e.key.toUpperCase())}}if(e.key==="ArrowDown")selectStudent(Math.min(current+1,total-1));if(e.key==="ArrowUp")selectStudent(Math.max(current-1,0))}});if(total)selectStudent(0);
</script>''' if selected else '<p class="muted">Select a lecture from the left.</p>'}</div></div>"""
    return page("Attendance Sheet",body)

@app.route("/student/timetable")
@need("STUDENT")
def student_timetable():
    u=me(); c=db()
    student=c.execute("select * from students where id=?",(u["student_id"],)).fetchone()
    c.close()
    tt=_load_timetable()
    slots=tt["slots"]
    day_names=["Monday","Tuesday","Wednesday","Thursday","Friday"]
    group=student["group_name"] or ""
    cells=[]
    for day in day_names:
        day_entries=[e for e in tt["entries"] if e.get("day")==day and (not e.get("group") or e.get("group")==group)]
        by_slot={}
        for e in day_entries:
            for no in e["slots"]:
                by_slot[no]=e
        for sl in slots:
            e=by_slot.get(sl["no"])
            if e:
                code=e["subject_code"]; name=e["subject_name"]
                cells.append(f'<div class="tt-cell subject" style="grid-column:{day_names.index(day)+2};grid-row:{sl["no"]+1}"><span class="tt-code">{code}</span><b>{name}</b><small>{sl["start"]}–{sl["end"]}</small><em>Slot {sl["label"]}</em></div>')
            else:
                cells.append(f'<div class="tt-cell free" style="grid-column:{day_names.index(day)+2};grid-row:{sl["no"]+1}"><span>Free</span></div>')
    rows="".join(cells)
    head="".join(f'<div class="tt-day" style="grid-column:{i+2};grid-row:1">{d[:3]}<small>{d}</small></div>' for i,d in enumerate(day_names))
    timecol="".join(f'<div class="tt-time" style="grid-column:1;grid-row:{i+2}"><b>{sl["label"]}</b><small>{sl["start"]}</small></div>' for i,sl in enumerate(slots))
    body=f'''<div class="hero timetable-hero"><div><span class="pill">WEEKLY SCHEDULE</span><h2>Your Class Time Table</h2><p class="muted">B.Tech · Semester III · Section C · Room {tt["room"]}</p></div><div class="tt-badge">09:30 → 16:55<br><small>9 lecture slots</small></div></div>
    <div class="tt-wrap"><div class="tt-grid">{head}{timecol}{rows}</div></div>
    <div class="tt-legend"><span><i class="dot classdot"></i> Scheduled class</span><span><i class="dot freedot"></i> Free period</span><span>Group: <b>{group or "All students"}</b></span></div>'''
    return page("Time Table",body)

@app.route("/student/profile",methods=["GET","POST"])
@need("STUDENT")
def student_profile():
    u=me(); c=db()
    st=c.execute("select * from students where id=?",(u["student_id"],)).fetchone()
    if request.method=="POST":
        username=request.form.get("username","").strip()
        new_password=request.form.get("password","").strip()
        profile_picture=request.form.get("profile_picture","").strip()
        remove_profile_picture=request.form.get("remove_profile_picture")=="1"
        if not username:
            flash("Username is required.","danger")
        else:
            conflict=c.execute("select id from users where username=? and id<>?",(username,u["id"])).fetchone()
            if conflict:
                flash("That username is already in use.","danger")
            else:
                if remove_profile_picture:
                    profile_picture=""
                elif profile_picture:
                    try:
                        header,payload=profile_picture.split(",",1); raw=base64.b64decode(payload,validate=True)
                        if not header.startswith("data:image/") or len(raw)>2_500_000: raise ValueError()
                    except Exception:
                        profile_picture=""
                        flash("Profile picture could not be saved. Please use a smaller image.","danger")
                saved_picture = "" if remove_profile_picture else (profile_picture or st["profile_picture"])
                c.execute("update students set profile_picture=? where id=?",(saved_picture,st["id"]))
                if new_password:
                    c.execute("update users set username=?,password=? where id=?",(username,new_password,u["id"]))
                else:
                    c.execute("update users set username=? where id=?",(username,u["id"]))
                c.commit(); c.close()
                flash("Profile updated successfully.","success")
                return redirect(url_for("student_profile"))
    face_count=c.execute("select count(*) from student_face_profiles where student_id=? and is_active=1",(st["id"],)).fetchone()[0]
    c.close()
    profile_src=st["profile_picture"] or ""
    profile_preview=f'<img class="profile-preview" src="{profile_src}" alt="Profile picture">' if profile_src else '<div class="profile-placeholder">AI</div>'
    body=f'''<div class="hero"><div><span class="pill">STUDENT PROFILE</span><h2>Edit Profile</h2><p class="muted">Update your username, profile picture and face-recognition enrollment.</p></div><a class="btn" href="/dashboard">← Back to dashboard</a></div>
    <div class="profile-grid">
      <div class="card profile-card">
        <div class="head"><h3>Personal & Account Details</h3><span class="pill">SELF EDIT</span></div>
        <form class="form" method="post" id="profileForm">
          <label>Username<input name="username" value="{u["username"]}" required></label>
          <label>New Password<input name="password" type="password" placeholder="Leave blank to keep current password"></label>
          <label>Name<input value="{st["name"]}" disabled></label>
          <label>Admission No.<input value="{st["enrollment_no"]}" disabled></label>
          <label>Roll No.<input value="{st["roll_no"] or "—"}" disabled></label>
          <label>Course / Semester<input value="{st["course"]} · Semester {st["semester"]}" disabled></label>
          <label>Section / Group<input value="{st["section"]} · {st["group_name"] or "—"}" disabled></label>
          <div class="wide"><small class="muted">Name and all university-issued academic details are protected from student-side editing.</small></div>
          <div class="wide profile-picture-box"><h3 style="margin:0 0 5px">Profile Picture</h3><p class="muted small">Choose a picture to replace the app logo shown beside your account.</p>{profile_preview}<input id="profilePictureFile" type="file" accept="image/*"><input id="profilePictureData" name="profile_picture" type="hidden">
            {('<button class="btn danger" type="submit" name="remove_profile_picture" value="1" onclick="return confirm(\'Remove your profile picture?\')">Remove PFP</button>' if profile_src else '')}</div>
          <div class="wide"><button class="btn primary" type="submit">Save Profile Changes</button></div>
        </form>
      </div>
      <div class="card profile-card"><div class="head"><h3>Face Recognition</h3><span class="pill">{face_count} saved scans</span></div><div class="face-panel">
        <video id="faceCamera" class="face-camera" autoplay playsinline muted></video><canvas id="faceCanvas" class="face-preview"></canvas>
        <div class="face-actions"><button type="button" class="btn primary" id="startFace">◉ Start Camera</button><button type="button" class="btn green" id="captureFace" disabled>◎ Scan & Save Face</button><button type="button" class="btn" id="stopFace" disabled>■ Stop</button></div>
        <div id="faceStatus" class="face-status">Camera is off. Click Start Camera to add another face scan.</div>
        <div class="face-note"><b>Multiple scans are kept.</b> Every scan becomes a separate enrollment sample. Existing face-recognition data is never deleted when you scan again.</div>
      </div></div>
    </div>
    <script>
    (()=>{{
      const video=document.getElementById('faceCamera'),canvas=document.getElementById('faceCanvas'),start=document.getElementById('startFace'),capture=document.getElementById('captureFace'),stop=document.getElementById('stopFace'),status=document.getElementById('faceStatus');let stream=null;
      const file=document.getElementById('profilePictureFile'),hidden=document.getElementById('profilePictureData');
      if(file) file.onchange=()=>{{const f=file.files[0];if(!f)return;const reader=new FileReader();reader.onload=()=>hidden.value=reader.result;reader.readAsDataURL(f)}};
      start.onclick=async()=>{{try{{stream=await navigator.mediaDevices.getUserMedia({{video:{{facingMode:"user",width:{{ideal:1280}},height:{{ideal:720}}}},audio:false}});video.srcObject=stream;capture.disabled=false;stop.disabled=false;start.disabled=true;status.textContent="Camera active. Center your face and click Scan & Save Face."}}catch(e){{status.textContent="Camera access failed. Please allow camera permission and use HTTPS."}}}};
      stop.onclick=()=>{{if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;video.srcObject=null;capture.disabled=true;stop.disabled=true;start.disabled=false;status.textContent="Camera stopped."}};
      capture.onclick=async()=>{{if(!stream)return;canvas.width=video.videoWidth||640;canvas.height=video.videoHeight||480;canvas.getContext("2d").drawImage(video,0,0,canvas.width,canvas.height);const data=canvas.toDataURL("image/jpeg",0.88);capture.disabled=true;status.textContent="Saving new face enrollment…";try{{const res=await fetch("/student/face",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{image:data}})}});const out=await res.json();status.textContent=out.message||"Face saved.";if(out.ok)setTimeout(()=>location.reload(),700)}}catch(e){{status.textContent="Could not save face enrollment. Please try again.";capture.disabled=false}}}};
      window.addEventListener("beforeunload",()=>{{if(stream)stream.getTracks().forEach(t=>t.stop())}});
    }})();
    </script>'''
    return page("Edit Profile",body)

@app.route("/student/face",methods=["POST"])
@need("STUDENT")
def student_face():
    u=me(); data=request.get_json(silent=True) or {{}}
    image=data.get("image","")
    if not image.startswith("data:image/"): return {{"ok":False,"message":"Invalid face image."}},400
    try:
        _,payload=image.split(",",1); raw=base64.b64decode(payload,validate=True)
        if len(raw)>2_500_000: return {{"ok":False,"message":"Image is too large. Please retry."}},400
    except Exception: return {{"ok":False,"message":"Could not read the captured image."}},400
    c=db(); c.execute("insert into student_face_profiles(student_id,image_data,captured_at,is_active) values(?,?,CURRENT_TIMESTAMP,1)",(u["student_id"],image)); c.commit(); c.close()
    return {{"ok":True,"message":"New face enrollment saved. Existing face scans were kept."}}

@app.route("/student/attendance")
@need("STUDENT")
def student_history():
    u=me(); c=db()
    st=c.execute("select * from students where id=?",(u["student_id"],)).fetchone()
    today=datetime.now(IST).date().isoformat()
    rows=c.execute("""select l.lecture_date,l.lecture_day,l.lecture_no,l.slot_label,l.start_time,l.end_time,l.room,
        s.code,s.name subject_name,a.source
        from lectures l join subjects s on s.id=l.subject_id
        left join attendance a on a.lecture_id=l.id and a.student_id=?
        where l.lecture_date>=? and l.lecture_date<=?
          and l.course=? and l.section=? and l.status='PDF_SCHEDULED'
          and s.code not in ('SELF','MENTOR')
          and (l.group_name is null or l.group_name='' or l.group_name=?)
        order by l.lecture_date desc,l.lecture_no desc""",
        (u["student_id"],APP_START_DATE.isoformat(),today,st["course"],st["section"],st["group_name"] or "")).fetchall()
    c.close()
    present_sources=("TEACHER_OVERRIDE","ADMIN_OVERRIDE","AI_RECOGNITION")
    present_count=sum(1 for r in rows if r["source"] in present_sources)
    total_count=len(rows); absent_count=total_count-present_count
    trs=""
    for r in rows:
        status="Present" if r["source"] in present_sources else "Absent"
        source=r["source"] or "AUTO_ABSENT"
        status_cls="green" if status=="Present" else "red"
        trs += f'<tr><td>{r["lecture_date"]}<small>{r["lecture_day"]}</small></td><td>Slot {r["lecture_no"]}<small>{r["slot_label"] or ""} · {r["start_time"] or ""}-{r["end_time"] or ""}</small></td><td><b>{r["code"]}</b><small>{r["subject_name"]}</small></td><td>{r["room"]}</td><td><span class="pill {status_cls}">{status}</span></td><td>{source}</td></tr>'
    if not trs:
        trs='<tr><td colspan="6">No scheduled attendance records found for the app period.</td></tr>'
    body=f'<div class="hero"><div><span class="pill">COMPLETE HISTORY</span><h2>Attendance History</h2><p class="muted">Every scheduled class from {APP_START_DATE.isoformat()} through {today} is shown according to the timetable.</p></div><div class="overall-box"><div class="value">{present_count}/{total_count}</div><div class="label">PRESENT / TOTAL</div><div class="overall-breakdown"><div><span>Present</span><b>{present_count}</b></div><div><span>Absent</span><b>{absent_count}</b></div><div><span>Total</span><b>{total_count}</b></div></div></div></div><div class="card"><div class="head"><h3>Class-by-Class Attendance</h3><span class="pill">{total_count} scheduled classes</span></div><div class="table"><table><tr><th>Date</th><th>Slot / Time</th><th>Subject</th><th>Room</th><th>Status</th><th>Source</th></tr>{trs}</table></div></div>'
    return page("Attendance History",body)

@app.route("/students")
@need("ADMIN")
def students():
    c=db(); rows=c.execute("select * from students order by name").fetchall(); c.close()
    trs="".join(f'<tr><td><b>{s["name"]}</b></td><td>{s["enrollment_no"]}</td><td>{s["roll_no"] or "—"}</td><td>{s["course"]}</td><td>{s["semester"]}</td><td>{s["section"]}</td></tr>' for s in rows)
    return page("Student Directory",f'<div class="hero"><div><span class="pill">UNIVERSITY DIRECTORY</span><h2>{len(rows)} active students</h2></div></div><div class="card"><div class="table"><table><tr><th>Name</th><th>Admission No.</th><th>Roll No.</th><th>Course</th><th>Semester</th><th>Section</th></tr>{trs}</table></div></div>')

@app.route("/cameras",methods=["GET","POST"])
@need("ADMIN")
def cameras():
    c=db()
    # Keep the old Room 222 camera removed even on existing databases.
    c.execute("delete from cameras where lower(camera_name) like '%room 222%' or lower(location)=?",("222",))
    if not c.execute("select 1 from cameras where lower(camera_name)=? limit 1",("login device camera",)).fetchone():
        c.execute("insert into cameras(camera_name,location,stream_url,authorized) values(?,?,?,1)",("Login Device Camera","This device","LOCAL_DEVICE"))
    if request.method=="POST":
        name=request.form["name"].strip()
        location=request.form["location"].strip()
        stream_url=request.form.get("url","").strip()
        c.execute("insert into cameras(camera_name,location,stream_url,authorized) values(?,?,?,1)",(name,location,stream_url))
        camera_id=c.execute("select last_insert_rowid()").fetchone()[0]
        c.commit()
        audit("ADD_CAMERA","camera",camera_id,"Added camera: "+name+" at "+location)
        flash("Camera added.","success")
    rows=c.execute("select * from cameras where lower(camera_name) not like '%room 222%' order by case when lower(camera_name)=? then 0 else 1 end,id desc",("login device camera",)).fetchall()
    c.commit()
    c.close()

    cards=[]
    camera_config=[]
    for x in rows:
        is_local=(x["stream_url"] or "")=="LOCAL_DEVICE"
        source="Browser device camera" if is_local else (x["stream_url"] or "No browser-compatible stream configured")
        badge="DEFAULT · LOGIN DEVICE" if is_local else "AUTHORIZED CAMERA"
        camera_config.append({"id":x["id"],"name":x["camera_name"],"location":x["location"],"stream_url":x["stream_url"] or "","local":is_local})
        cards.append(f'''<button type="button" class="camera-card" data-camera-id="{x["id"]}">
          <div class="camera-card-top"><span class="pill">{badge}</span><span class="camera-open">OPEN FEED</span></div>
          <b class="camera-card-title">{escape(x["camera_name"])}</b>
          <small>{escape(x["location"])} · {escape(source)}</small>
          <div class="camera-thumb"><span>{'◉' if is_local else '▣'}</span><em>Click to add this camera to live view</em></div>
        </button>''')

    camera_json=json.dumps(camera_config)
    body='''<style>
      .camera-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,260px));gap:12px;padding:14px;align-items:start}
      .camera-card{display:block;width:240px;max-width:100%;text-align:left;padding:11px;transition:.2s ease;border:1px solid #22344f;background:#0d1a2c;color:#eef4ff;border-radius:13px;cursor:pointer}
      .camera-card:hover{transform:translateY(-2px);border-color:#667dff;box-shadow:0 12px 26px #0006}
      .camera-card.active{border-color:#6e82ff;box-shadow:0 0 0 2px #667dff33}
      .camera-card-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
      .camera-open{font-size:8px;font-weight:950;color:#8fa7ff;letter-spacing:.06em}
      .camera-card-title{display:block;font-size:13px;margin-bottom:4px}
      .camera-card small{display:block;color:#8291aa;min-height:24px;line-height:1.35;font-size:9px}
      .camera-thumb{height:68px;margin-top:9px;border-radius:9px;border:1px dashed #304565;background:radial-gradient(circle at 50% 40%,#1b3150,#091321 68%);display:flex;flex-direction:column;align-items:center;justify-content:center;color:#7e91ad}
      .camera-thumb span{font-size:19px;color:#7387ff}.camera-thumb em{font-style:normal;font-size:8px;margin-top:4px}
      .live-modal{display:none;position:fixed;inset:0;z-index:9999;background:rgba(2,7,14,.82);backdrop-filter:blur(7px);padding:22px;box-sizing:border-box}
      .live-modal.open{display:flex;align-items:center;justify-content:center}
      .live-panel{width:min(1180px,calc(100vw - 44px));height:min(720px,calc(100vh - 44px));min-width:520px;min-height:380px;max-width:95vw;max-height:92vh;margin:0;background:#081321;border:1px solid #304565;border-radius:20px;box-shadow:0 30px 90px #000b;display:flex;flex-direction:column;overflow:hidden;resize:both}
      .live-head{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 18px;border-bottom:1px solid #223752}
      .live-title{font-size:18px;font-weight:950}.live-sub{font-size:10px;color:#8291aa;margin-top:3px}
      .live-actions{display:flex;gap:8px;align-items:center}
      .live-actions button{border:1px solid #304565;background:#10213a;color:#dce7f8;border-radius:10px;padding:9px 12px;font-weight:850;cursor:pointer}
      .live-actions button:hover{border-color:#657cff}
      .camera-picker{display:none;padding:10px 14px;border-bottom:1px solid #223752;background:#0a1727}
      .camera-picker.open{display:block}
      .camera-picker-title{font-size:10px;font-weight:900;color:#8291aa;margin-bottom:8px}
      .camera-picker-list{display:flex;gap:8px;flex-wrap:wrap}
      .camera-picker-item{border:1px solid #304565;background:#10213a;color:#dce7f8;border-radius:9px;padding:7px 10px;font-size:10px;font-weight:850;cursor:pointer}
      .camera-picker-item:hover{border-color:#657cff}
      .camera-picker-item.active{border-color:#6e82ff;background:#172b4d;color:#9eb0ff}
      .feed-grid{padding:14px;display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px;overflow:auto;flex:1;align-content:start}
      .feed-tile{position:relative;min-height:235px;aspect-ratio:16/10;background:#02070d;border:1px solid #263c59;border-radius:14px;overflow:hidden}
      .feed-video{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#02070d}
      .feed-overlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
      .feed-label{position:absolute;left:10px;top:10px;z-index:3;padding:6px 9px;border-radius:8px;background:rgba(3,10,20,.72);border:1px solid rgba(125,153,205,.35);font-size:10px;font-weight:900;color:#edf4ff}
      .face-count{position:absolute;right:10px;top:10px;z-index:3;padding:6px 9px;border-radius:8px;background:rgba(3,10,20,.68);font-size:9px;color:#b9c9df}
      .feed-status{position:absolute;left:10px;bottom:10px;z-index:3;padding:5px 8px;border-radius:7px;background:rgba(3,10,20,.7);font-size:9px;color:#aebdd2}
      .empty-feeds{grid-column:1/-1;display:grid;place-items:center;min-height:260px;color:#71829b;border:1px dashed #2a3f5e;border-radius:14px}
      .detection-on{color:#80d7b2!important}
      @media(max-width:700px){.live-modal{padding:8px}.live-panel{width:96vw;height:92vh;min-width:0;min-height:300px;border-radius:14px}.feed-grid{grid-template-columns:1fr;padding:9px}.feed-tile{min-height:210px}.camera-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;padding:10px}.camera-card{width:100%;padding:10px}.camera-thumb{height:62px}}
    </style>
    <div class="card"><div class="head"><div><span class="pill">CAMERA MANAGEMENT</span><h2 style="margin:8px 0 5px">University Cameras</h2><p class="muted">Click one or more cameras to add them to the live popup. AI face detection runs on every active feed.</p></div></div>
      <form class="form" method="post"><label>Name<input name="name" required></label><label>Location<input name="location" required></label><label>Stream URL<input name="url" placeholder="Browser-compatible HLS/WebRTC URL"></label><div><button class="btn primary">Authorize Camera</button></div></form>
    </div>
    <div class="card"><div class="head"><h3>Available Cameras</h3><span class="pill" id="selectedCount">0 selected</span></div><div class="camera-grid">__CAMERA_CARDS__</div></div>

    <div class="live-modal" id="liveModal" aria-hidden="true">
      <div class="live-panel">
        <div class="live-head">
          <div><div class="live-title">Live Camera Feeds</div><div class="live-sub"><span id="feedCount">0</span> active camera(s) · <span id="aiStatus">Preparing AI face detection…</span></div></div>
          <div class="live-actions"><button type="button" id="addCameraBtn">＋ Add Camera</button><button type="button" id="clearFeeds">Clear All</button><button type="button" id="closeFeeds">✕ Close</button></div>
        </div>
        <div class="camera-picker" id="cameraPicker">
          <div class="camera-picker-title">Add cameras to this live view</div>
          <div class="camera-picker-list" id="cameraPickerList"></div>
        </div>
        <div class="feed-grid" id="feedGrid"><div class="empty-feeds">Add one or more cameras to start their live feeds.</div></div>
      </div>
    </div>

    <script type="module">
    const CAMERA_CONFIG=__CAMERA_JSON__;
    const modal=document.getElementById("liveModal");
    const feedGrid=document.getElementById("feedGrid");
    const selectedCount=document.getElementById("selectedCount");
    const feedCount=document.getElementById("feedCount");
    const aiStatus=document.getElementById("aiStatus");
    const addCameraBtn=document.getElementById("addCameraBtn");
    const cameraPicker=document.getElementById("cameraPicker");
    const cameraPickerList=document.getElementById("cameraPickerList");
    const active=new Map();
    let detector=null;
    let detectorPromise=null;
    let detectionTimer=null;

    function escapeHtml(v){return String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}

    async function getDetector(){
      if(detector) return detector;
      if(detectorPromise) return detectorPromise;
      detectorPromise=(async()=>{
        try{
          aiStatus.textContent="Loading AI face detector…";
          const {FaceDetector,FilesetResolver}=await import("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22/vision_bundle.mjs");
          const vision=await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22/wasm");
          const model="https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite";
          try{
            detector=await FaceDetector.createFromOptions(vision,{baseOptions:{modelAssetPath:model,delegate:"GPU"},runningMode:"VIDEO",minDetectionConfidence:.5,minSuppressionThreshold:.3});
          }catch(gpuError){
            detector=await FaceDetector.createFromOptions(vision,{baseOptions:{modelAssetPath:model,delegate:"CPU"},runningMode:"VIDEO",minDetectionConfidence:.5,minSuppressionThreshold:.3});
          }
          aiStatus.textContent="AI face detection ON";
          aiStatus.classList.add("detection-on");
          return detector;
        }catch(error){
          console.error("Face detector initialization failed",error);
          aiStatus.textContent="AI detector unavailable — feeds still active";
          throw error;
        }
      })();
      return detectorPromise;
    }

    function renderCameraPicker(){
      cameraPickerList.innerHTML="";
      CAMERA_CONFIG.forEach(camera=>{
        const btn=document.createElement("button");
        btn.type="button";
        btn.className="camera-picker-item"+(active.has(camera.id)?" active":"");
        btn.textContent=(active.has(camera.id)?"✓ ":"＋ ")+camera.name;
        btn.onclick=()=>openCamera(camera.id);
        cameraPickerList.appendChild(btn);
      });
    }

    function syncCounts(){
      selectedCount.textContent=active.size+" selected";
      feedCount.textContent=active.size;
      document.querySelectorAll(".camera-card").forEach(card=>card.classList.toggle("active",active.has(Number(card.dataset.cameraId))));
      renderCameraPicker();
    }

    function fitRect(video,canvas){
      const vw=video.videoWidth||1280,vh=video.videoHeight||720;
      const cw=canvas.clientWidth,ch=canvas.clientHeight;
      const scale=Math.min(cw/vw,ch/vh);
      return {scale,ox:(cw-vw*scale)/2,oy:(ch-vh*scale)/2};
    }

    function drawBoxes(item,detections){
      const {video,canvas,ctx,count}=item;
      const cw=canvas.clientWidth,ch=canvas.clientHeight;
      const dpr=window.devicePixelRatio||1;
      canvas.width=Math.max(1,Math.round(cw*dpr));canvas.height=Math.max(1,Math.round(ch*dpr));
      ctx.setTransform(dpr,0,0,dpr,0,0);
      ctx.clearRect(0,0,cw,ch);
      const fit=fitRect(video,canvas);
      let faces=0;
      for(const detection of (detections?.detections||[])){
        const b=detection.boundingBox;
        if(!b) continue;
        faces++;
        const x=fit.ox+b.originX*fit.scale;
        const y=fit.oy+b.originY*fit.scale;
        const w=b.width*fit.scale;
        const h=b.height*fit.scale;
        ctx.save();
        ctx.fillStyle="rgba(74,126,255,.16)";
        ctx.strokeStyle="rgba(116,168,255,.95)";
        ctx.lineWidth=2;
        ctx.fillRect(x,y,w,h);
        ctx.strokeRect(x,y,w,h);
        const score=(detection.categories?.[0]?.score||0)*100;
        const label="FACE "+score.toFixed(0)+"%";
        ctx.font="700 11px Inter,Arial,sans-serif";
        const tw=ctx.measureText(label).width+14;
        const lh=21;
        const ly=Math.max(0,y-lh);
        ctx.fillStyle="rgba(5,13,27,.78)";
        ctx.fillRect(x,ly,tw,lh);
        ctx.fillStyle="#eef5ff";
        ctx.fillText(label,x+7,ly+15);
        ctx.restore();
      }
      count.textContent=faces+" face"+(faces===1?"":"s");
    }

    async function detectAll(){
      if(!active.size) return;
      let d;
      try{d=await getDetector();}catch(_){return;}
      for(const item of active.values()){
        if(!item.video.videoWidth||item.video.readyState<2) continue;
        try{
          const result=d.detectForVideo(item.video,performance.now());
          drawBoxes(item,result);
        }catch(error){console.warn("Face detection frame failed",error);}
      }
    }

    function startDetectionLoop(){
      if(detectionTimer) return;
      detectionTimer=setInterval(detectAll,110);
    }

    function makeFeed(camera){
      const id=String(camera.id);
      const tile=document.createElement("div");
      tile.className="feed-tile";
      tile.dataset.cameraId=id;
      const label=document.createElement("div");
      label.className="feed-label";
      label.textContent=camera.name;
      const count=document.createElement("div");
      count.className="face-count";
      count.textContent="0 faces";
      const status=document.createElement("div");
      status.className="feed-status";
      status.textContent="Starting feed…";
      const video=document.createElement("video");
      video.className="feed-video";
      video.autoplay=true;video.playsInline=true;video.muted=true;
      const canvas=document.createElement("canvas");
      canvas.className="feed-overlay";
      tile.append(label,count,status,video,canvas);
      feedGrid.appendChild(tile);
      const item={camera,tile,video,canvas,ctx:canvas.getContext("2d"),count,stream:null};
      active.set(camera.id,item);

      if(camera.local){
        navigator.mediaDevices.getUserMedia({video:{facingMode:"user",width:{ideal:1280},height:{ideal:720}},audio:false}).then(stream=>{
          if(!active.has(camera.id)){stream.getTracks().forEach(t=>t.stop());return;}
          item.stream=stream;video.srcObject=stream;status.textContent="LIVE · Device Camera";
          return video.play();
        }).catch(error=>{
          console.error(error);status.textContent="Camera access denied or unavailable.";
        });
      }else if(camera.stream_url){
        video.src=camera.stream_url;
        video.onloadedmetadata=()=>{status.textContent="LIVE · Stream connected";video.play().catch(()=>{});};
        video.onerror=()=>{status.textContent="Stream unavailable or not browser-compatible.";};
      }else{
        status.textContent="No browser-compatible stream configured.";
      }
      getDetector().catch(()=>{});
      syncCounts();
      startDetectionLoop();
    }

    function removeFeed(cameraId){
      const item=active.get(cameraId);
      if(!item) return;
      if(item.stream) item.stream.getTracks().forEach(t=>t.stop());
      item.video.pause();item.video.srcObject=null;item.video.removeAttribute("src");item.video.load();
      item.tile.remove();
      active.delete(cameraId);
      syncCounts();
      if(!active.size){
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden","true");
        feedGrid.innerHTML='<div class="empty-feeds">Select a camera above to start its live feed.</div>';
      }
    }

    function openCamera(cameraId){
      const camera=CAMERA_CONFIG.find(x=>Number(x.id)===Number(cameraId));
      if(!camera) return;
      if(active.has(camera.id)){removeFeed(camera.id);return;}
      modal.classList.add("open");modal.setAttribute("aria-hidden","false");
      const empty=feedGrid.querySelector(".empty-feeds");if(empty)empty.remove();
      makeFeed(camera);
      cameraPicker.classList.remove("open");
    }

    document.querySelectorAll(".camera-card").forEach(card=>card.addEventListener("click",()=>openCamera(Number(card.dataset.cameraId))));
    addCameraBtn.onclick=()=>cameraPicker.classList.toggle("open");
    document.getElementById("clearFeeds").onclick=()=>Array.from(active.keys()).forEach(id=>removeFeed(id));
    document.getElementById("closeFeeds").onclick=()=>Array.from(active.keys()).forEach(id=>removeFeed(id));
    modal.addEventListener("click",e=>{if(e.target===modal)Array.from(active.keys()).forEach(id=>removeFeed(id));});
    document.addEventListener("keydown",e=>{if(e.key==="Escape")Array.from(active.keys()).forEach(id=>removeFeed(id));});
    window.addEventListener("beforeunload",()=>Array.from(active.values()).forEach(item=>{if(item.stream)item.stream.getTracks().forEach(t=>t.stop());}));

    syncCounts();
    </script>'''
    body=body.replace("__CAMERA_CARDS__","".join(cards) or '<div style="padding:20px" class="muted">No cameras available.</div>')
    body=body.replace("__CAMERA_JSON__",camera_json)
    return page("Camera Management",body)

@app.route("/cameras/<int:camera_id>")
@need("ADMIN")
def camera_view(camera_id):
    # Kept as a compatibility route for old bookmarks; new camera access uses the popup.
    return redirect(url_for("cameras"))


# --- Fail-safe PDF document ingestion ---------------------------------------
# The parser deliberately refuses to write anything when the PDF is ambiguous.
# This is more important for attendance/timetable data than guessing.
DAY_NAMES=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
DAY_ALIASES={
    "MON":"Monday","MONDAY":"Monday","TUE":"Tuesday","TUES":"Tuesday","TUESDAY":"Tuesday",
    "WED":"Wednesday","WEDNESDAY":"Wednesday","THU":"Thursday","THUR":"Thursday","THURS":"Thursday","THURSDAY":"Thursday",
    "FRI":"Friday","FRIDAY":"Friday","SAT":"Saturday","SATURDAY":"Saturday","SUN":"Sunday","SUNDAY":"Sunday"
}
ADMISSION_RE=re.compile(r"\b\d{2}[A-Z]{2,12}[A-Z0-9]{2,}\b",re.I)
ROLL_RE=re.compile(r"\b\d{10,13}\b")
GROUP_RE=re.compile(r"\b\d{2}\s*[a-z]{3}\s*\(\s*\d{2}\s*c\s*[12]\s*\)",re.I)
SUBJECT_CODE_RE=re.compile(r"\b[A-Z]{2,8}\d{3}[A-Z]{0,2}\b")
TIME_RANGE_RE=re.compile(r"\b\d{1,2}[:.]\d{2}\s*[-–—]\s*\d{1,2}[:.]\d{2}\b")
SINGLE_TIME_RE=re.compile(r"\b\d{1,2}[:.]\d{2}\b")

def _clean_pdf_text(value):
    return re.sub(r"\s+"," ",str(value or "")).strip()

def _norm_group(value):
    if not value:
        return None
    m=GROUP_RE.search(str(value))
    if not m:
        return None
    return re.sub(r"\s+","",m.group(0)).lower()

def _norm_person(value):
    return re.sub(r"[^a-z0-9]","",str(value or "").lower())

def _extract_pdf_document(path):
    try:
        import pymupdf
    except Exception as exc:
        raise ValueError(f"PDF extraction engine is unavailable: {exc}")
    doc=pymupdf.open(path)
    pages=[]
    total_text=[]
    for page in doc:
        text=page.get_text("text",sort=True) or ""
        words=page.get_text("words",sort=True) or []
        blocks=page.get_text("blocks",sort=True) or []
        pages.append({"number":page.number+1,"text":text,"words":words,"blocks":blocks})
        total_text.append(text)
    doc.close()
    combined="\n".join(total_text)
    if len(re.sub(r"\s+","",combined)) < 30:
        raise ValueError("This PDF has no readable text layer. The import was stopped instead of guessing from an image-only/scanned PDF.")
    return pages,combined

def _guess_document_type(text):
    t=text.upper()
    student_score=sum(x in t for x in ("STUDENT","ROLL","ADMISSION","ENROLLMENT","NAME"))
    timetable_score=sum(x in t for x in ("TIME TABLE","TIMETABLE","SLOT","MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"))
    if student_score>=2 and student_score>timetable_score:
        return "STUDENT_LIST"
    if timetable_score>=2 and timetable_score>=student_score:
        return "TIMETABLE"
    # Structural fallback: roll/admission patterns are much stronger than title wording.
    if len(ROLL_RE.findall(text))>=2 and len(ADMISSION_RE.findall(text))>=2:
        return "STUDENT_LIST"
    if len(SUBJECT_CODE_RE.findall(text))>=2 and len(TIME_RANGE_RE.findall(text))>=2:
        return "TIMETABLE"
    return "UNKNOWN"

def _student_rows_from_lines(text):
    rows=[]
    seen=set()
    for raw in text.splitlines():
        line=_clean_pdf_text(raw)
        if not line:
            continue
        admissions=ADMISSION_RE.findall(line)
        rolls=ROLL_RE.findall(line)
        if len(admissions)!=1 or len(rolls)!=1:
            continue
        admission=admissions[0].upper()
        roll=rolls[0]
        if admission in seen or roll in {x["roll_no"] for x in rows}:
            continue
        group=_norm_group(line)
        work=ADMISSION_RE.sub(" ",line)
        work=ROLL_RE.sub(" ",work)
        work=GROUP_RE.sub(" ",work)
        # Remove common table labels/serial numbers, but never invent a name.
        work=re.sub(r"\b(?:S\.?NO\.?|SR\.?\s*NO\.?|ROLL\s*NO\.?|ADMISSION\s*NO\.?|ENROLLMENT\s*NO\.?|NAME|GROUP)\b"," ",work,flags=re.I)
        work=re.sub(r"\b\d{1,3}\b"," ",work)
        name=_clean_pdf_text(work).strip(" -|,:;")
        if len(name)<2:
            continue
        rows.append({"admission_no":admission,"roll_no":roll,"name":name,"group":group})
        seen.add(admission)
    return rows

def _student_rows_from_words(pages):
    rows=[]
    for p in pages:
        words=p["words"]
        # Reconstruct visual lines using PyMuPDF line numbers; this survives
        # different column ordering much better than plain text alone.
        grouped={}
        for w in words:
            key=(w[5],w[6])
            grouped.setdefault(key,[]).append(w)
        lines=[" ".join(x[4] for x in sorted(ws,key=lambda z:z[0])) for ws in grouped.values()]
        rows.extend(_student_rows_from_lines("\n".join(lines)))
    unique={}
    for x in rows:
        unique[(x["admission_no"],x["roll_no"])]=x
    return list(unique.values())

def _validate_students(rows,base):
    errors=[]
    if not rows:
        errors.append("No student rows could be read.")
        return errors
    admissions=[x["admission_no"] for x in rows]
    rolls=[x["roll_no"] for x in rows]
    if len(set(admissions))!=len(admissions): errors.append("Duplicate admission numbers detected.")
    if len(set(rolls))!=len(rolls): errors.append("Duplicate roll numbers detected.")
    for i,x in enumerate(rows,1):
        if not ADMISSION_RE.fullmatch(x["admission_no"]): errors.append(f"Row {i}: invalid admission number {x['admission_no']}.")
        if not ROLL_RE.fullmatch(x["roll_no"]): errors.append(f"Row {i}: invalid roll number {x['roll_no']}.")
        if len(x["name"])<2: errors.append(f"Row {i}: missing student name.")
    if len(rows)>500: errors.append("More than 500 students were detected; import stopped.")
    return errors

def _parse_student_pdf(pages,text):
    rows=_student_rows_from_lines(text)
    if len(rows)<2:
        rows=_student_rows_from_words(pages)
    errors=_validate_students(rows,None)
    # Extract class metadata without depending on one exact heading format.
    upper=text.upper()
    course="B.Tech" if "B.TECH" in upper or "BTECH" in upper else "B.Tech"
    semester=3
    sm=re.search(r"\bSEM(?:ESTER)?\s*[-:]?\s*(\d+)\b",upper)
    if sm: semester=int(sm.group(1))
    section="C"
    sec=re.search(r"\bSECTION\s*[-:]?\s*([A-Z])\b",upper)
    if sec: section=sec.group(1).upper()
    # The imported list must be internally coherent.
    for x in rows: x.update(course=course,semester=semester,section=section)
    return {"kind":"STUDENT_LIST","rows":rows,"errors":errors,"count":len(rows)}

def _time_to_minutes(value):
    h,m=re.split(r"[:.]",value)
    return int(h)*60+int(m)

def _parse_time_range(value):
    m=TIME_RANGE_RE.search(value or "")
    if not m:return None
    a,b=re.split(r"\s*[-–—]\s*",m.group(0))
    return (_time_to_minutes(a),_time_to_minutes(b))

def _extract_slot_rows(pages):
    found=[]
    for p in pages:
        for block in p["blocks"]:
            txt=_clean_pdf_text(block[4])
            tr=_parse_time_range(txt)
            if tr:
                found.append({"start":tr[0],"end":tr[1],"y0":block[1],"y1":block[3],"page":p["number"]})
    # Keep one row per time range, in document order.
    unique={}
    for x in found:
        unique[(x["page"],x["start"],x["end"],round(x["y0"],1))]=x
    return sorted(unique.values(),key=lambda x:(x["page"],x["y0"]))

def _find_day_headers(pages):
    headers=[]
    for p in pages:
        for block in p["blocks"]:
            txt=_clean_pdf_text(block[4]).upper()
            for token,name in DAY_ALIASES.items():
                if re.search(r"\b"+re.escape(token)+r"\b",txt):
                    headers.append({"day":name,"x":(block[0]+block[2])/2,"page":p["number"]})
                    break
    # Prefer one x-position per day on each page.
    out={}
    for x in headers:
        out[(x["page"],x["day"])]=x
    return list(out.values())

def _closest_day(x,page,headers):
    candidates=[h for h in headers if h["page"]==page]
    if not candidates:return None
    return min(candidates,key=lambda h:abs(h["x"]-x))["day"]

def _slot_definitions(pages):
    rows=_extract_slot_rows(pages)
    # If a PDF contains explicit time rows, use them. Otherwise use roman/numbered
    # slot labels and let validation reject ambiguous layouts.
    out=[]
    seen=set()
    for r in rows:
        key=(r["start"],r["end"])
        if key in seen: continue
        seen.add(key)
        out.append(r)
    return out

def _parse_timetable_spatial(pages):
    codes=[]
    for p in pages:
        headers=_find_day_headers([p])
        slot_rows=_slot_definitions([p])
        if not headers or not slot_rows: continue
        for block in p["blocks"]:
            txt=_clean_pdf_text(block[4])
            code_match=SUBJECT_CODE_RE.search(txt.upper())
            if not code_match: continue
            code=code_match.group(0).upper()
            # Ignore generic non-course identifiers.
            if code in {"SECTION","SEMESTER"}: continue
            cx=(block[0]+block[2])/2
            day=_closest_day(cx,p["number"],headers)
            if not day: continue
            cy=(block[1]+block[3])/2
            touched=[]
            for i,sr in enumerate(slot_rows,1):
                center=(sr["y0"]+sr["y1"])/2
                # A merged cell can cover several slot rows; use block vertical
                # overlap/containment instead of assuming one code = one slot.
                if block[1] <= center <= block[3]:
                    touched.append(i)
            if not touched:
                nearest=min(range(len(slot_rows)),key=lambda i:abs(((slot_rows[i]["y0"]+slot_rows[i]["y1"])/2)-cy))
                touched=[nearest+1]
            teacher_code=None
            group=_norm_group(txt)
            codes.append({"day":day,"subject_code":code,"subject_text":txt,"slots":sorted(set(touched)),"group":group})
    # Deduplicate exact observations.
    out={}
    for x in codes:
        key=(x["day"],x["subject_code"],tuple(x["slots"]),x.get("group") or "")
        out[key]=x
    return list(out.values())

def _parse_timetable_lines(text):
    entries=[]
    current_day=None
    for raw in text.splitlines():
        line=_clean_pdf_text(raw)
        if not line: continue
        up=line.upper()
        for token,day in DAY_ALIASES.items():
            if re.search(r"\b"+re.escape(token)+r"\b",up):
                current_day=day
                break
        cm=SUBJECT_CODE_RE.search(up)
        if not cm: continue
        code=cm.group(0).upper()
        if code in {"SECTION","SEMESTER"}: continue
        day=current_day
        if not day: continue
        slots=[]
        for tr in TIME_RANGE_RE.findall(line):
            slots.append(tr)
        # Match exact slot times to a generic slot index only after the parser
        # has collected the distinct time ranges from the document.
        entries.append({"day":day,"subject_code":code,"subject_text":line,"time_ranges":slots,"group":_norm_group(line)})
    return entries

def _normalize_timetable_entries(spatial,lines,text):
    # Build slot definitions from the PDF where possible.
    time_pairs=[]
    for tr in TIME_RANGE_RE.findall(text):
        pair=_parse_time_range(tr)
        if pair and pair not in time_pairs: time_pairs.append(pair)
    time_pairs=sorted(time_pairs)
    slots=[]
    for i,(a,b) in enumerate(time_pairs,1):
        slots.append({"no":i,"label":str(i),"start":f"{a//60:02d}:{a%60:02d}","end":f"{b//60:02d}:{b%60:02d}"})
    by_code={}
    for x in spatial:
        by_code.setdefault((x["day"],x["subject_code"],x.get("group") or ""),[]).append(x)
    out=[]
    for key,items in by_code.items():
        day,code,group=key
        allslots=sorted(set(n for item in items for n in item["slots"]))
        if not allslots: continue
        text_parts=" ".join(item["subject_text"] for item in items)
        out.append({"day":day,"subject_code":code,"subject_name":_clean_pdf_text(re.sub(r"\b"+re.escape(code)+r"\b","",text_parts,flags=re.I)),
                    "teacher_code":None,"group":group,"slots":allslots,"source_text":text_parts})
    # Line parser can rescue documents whose words are not spatially arranged.
    if not out:
        for x in lines:
            if x["time_ranges"] and x["subject_code"]:
                out.append({"day":x["day"],"subject_code":x["subject_code"],"subject_name":_clean_pdf_text(re.sub(r"\b"+re.escape(x["subject_code"])+r"\b","",x["subject_text"],flags=re.I)),
                            "teacher_code":None,"group":x.get("group"),"slots":[],"source_text":x["subject_text"]})
    return slots,out

def _match_teacher_code(c,source_text):
    text=_norm_person(source_text)
    teachers=c.execute("select employee_code,name from teachers").fetchall()
    exact=[]
    for t in teachers:
        if _norm_person(t["name"]) and _norm_person(t["name"]) in text:
            exact.append(t["employee_code"])
    return exact[0] if len(exact)==1 else (None if not exact else "__AMBIGUOUS__")

def _validate_timetable(c,slots,entries):
    errors=[]
    if len(slots)<1: errors.append("No timetable time slots could be extracted.")
    if not entries: errors.append("No timetable subject entries could be extracted.")
    slot_nos={s["no"] for s in slots}
    occupied=set()
    for i,e in enumerate(entries,1):
        if e["day"] not in DAY_NAMES[:5]:
            errors.append(f"Entry {i}: unsupported day {e['day']}.")
        if not e["slots"]:
            errors.append(f"Entry {i} ({e['subject_code']}): no slot could be mapped.")
        for n in e["slots"]:
            if n not in slot_nos:
                errors.append(f"Entry {i} ({e['subject_code']}): slot {n} is outside extracted slot range.")
            key=(e["day"],n,e.get("group") or "")
            # Same slot is allowed for C1/C2, but never for two entries with the same group.
            if key in occupied:
                errors.append(f"Duplicate timetable occupancy: {e['day']} slot {n} group {e.get('group') or 'ALL'}.")
            occupied.add(key)
        e["teacher_code"]=_match_teacher_code(c,e.get("source_text",""))
        if e["teacher_code"]=="__AMBIGUOUS__":
            errors.append(f"Entry {i} ({e['subject_code']}): teacher could not be uniquely identified.")
        if e["teacher_code"] is None and e["subject_code"] not in ("SELF","MENTOR"):
            errors.append(f"Entry {i} ({e['subject_code']}): teacher could not be matched to an existing teacher account.")
        if e["subject_code"] in ("SELF","MENTOR"):
            e["teacher_code"]=None
    # If the PDF explicitly has a lunch/free row, it must not become a lecture.
    for e in entries:
        if any(k in e.get("source_text","").upper() for k in ("LUNCH","BREAK")):
            e["_ignore"]=True
    return [e for e in entries if not e.get("_ignore")],errors

def _parse_timetable_pdf(pages,text,c):
    spatial=_parse_timetable_spatial(pages)
    lines=_parse_timetable_lines(text)
    slots,entries=_normalize_timetable_entries(spatial,lines,text)
    entries,errors=_validate_timetable(c,slots,entries)
    # A timetable import must have a coherent slot grid. We do not guess slot
    # numbers from subject order.
    if len(slots)>15: errors.append("More than 15 distinct time slots were detected; import stopped.")
    if len(entries)>300: errors.append("More than 300 timetable entries were detected; import stopped.")
    upper=text.upper()
    course="B.Tech" if "B.TECH" in upper or "BTECH" in upper else "B.Tech"
    semester=3
    sm=re.search(r"\bSEM(?:ESTER)?\s*[-:]?\s*(\d+)\b",upper)
    if sm: semester=int(sm.group(1))
    section="C"
    sec=re.search(r"\bSECTION\s*[-:]?\s*([A-Z])\b",upper)
    if sec: section=sec.group(1).upper()
    room="222"
    rm=re.search(r"\bROOM\s*[-:]?\s*([A-Z0-9-]+)\b",upper)
    if rm: room=rm.group(1)
    effective_from=datetime.now(IST).date().isoformat()
    em=re.search(r"\b(?:EFFECTIVE\s*(?:FROM|DATE)|FROM)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",text,re.I)
    if em:
        raw=em.group(1).replace("/","-")
        try:
            if re.match(r"^\d{4}-",raw): effective_from=datetime.strptime(raw,"%Y-%m-%d").date().isoformat()
            else:
                parts=raw.split("-"); y=int(parts[2]); y+=2000 if y<100 else 0
                effective_from=datetime(y,int(parts[1]),int(parts[0])).date().isoformat()
        except Exception: pass
    # Map extracted slot number to the standard scheduler shape.
    for s in slots:
        s["label"]=["I","II","III","IV","V","VI","VII","VIII","IX"][s["no"]-1] if 1<=s["no"]<=9 else str(s["no"])
    normalized={"source":"Validated PDF import","effective_from":effective_from,"app_start_date":_timetable_start_date().isoformat(),
                "course":course,"semester":semester,"section":section,"room":room,"slots":slots,
                "entries":[{k:e[k] for k in ("day","subject_code","subject_name","teacher_code","group","slots")} for e in entries]}
    return normalized,errors

def _apply_imported_students(c,rows):
    for s in rows:
        row=c.execute("select id from students where enrollment_no=?",(s["admission_no"],)).fetchone()
        if row:
            sid=row["id"]
            c.execute("update students set roll_no=?,name=?,course=?,semester=?,section=?,group_name=? where id=?",
                      (s["roll_no"],s["name"],s["course"],s["semester"],s["section"],s.get("group"),sid))
        else:
            c.execute("insert into students(enrollment_no,roll_no,name,course,semester,section,group_name) values(?,?,?,?,?,?,?)",
                      (s["admission_no"],s["roll_no"],s["name"],s["course"],s["semester"],s["section"],s.get("group")))
            sid=c.execute("select last_insert_rowid()").fetchone()[0]
        user=c.execute("select id from users where student_id=?",(sid,)).fetchone()
        if user:
            c.execute("update users set username=?,password=?,role='STUDENT',display_name=? where id=?",
                      (s["admission_no"],s["roll_no"],s["name"],user["id"]))
        else:
            c.execute("insert or ignore into users(username,password,role,display_name,student_id) values(?,?,?,?,?)",
                      (s["admission_no"],s["roll_no"],"STUDENT",s["name"],sid))

def _apply_imported_timetable(c,tt,source_name):
    c.execute("""insert into document_configs(kind,payload,source_name,updated_at)
                 values('TIMETABLE',?,?,CURRENT_TIMESTAMP)
                 on conflict(kind) do update set payload=excluded.payload,source_name=excluded.source_name,updated_at=CURRENT_TIMESTAMP""",
              (json.dumps(tt),source_name))
    # Keep subject/teacher records synchronized with the imported timetable.
    for e in tt["entries"]:
        tid=_get_schedule_teacher(c,e.get("teacher_code"))
        row=c.execute("select id from subjects where code=?",(e["subject_code"],)).fetchone()
        if row:
            c.execute("update subjects set name=?,semester=?,section=?,teacher_id=? where id=?",
                      (e["subject_name"],tt["semester"],tt["section"],tid,row["id"]))
        else:
            c.execute("insert into subjects(code,name,semester,section,teacher_id) values(?,?,?,?,?)",
                      (e["subject_code"],e["subject_name"],tt["semester"],tt["section"],tid))

@app.route("/import",methods=["GET","POST"])
@need("ADMIN")
def import_pdf():
    result=""
    if request.method=="POST" and "pdf" in request.files:
        f=request.files["pdf"]
        if not f.filename.lower().endswith(".pdf"):
            result="<b>Import stopped:</b> Please upload a PDF file."
        else:
            safe_name=re.sub(r"[^A-Za-z0-9._-]+","_",f.filename)
            path=os.path.join(UPLOADS,safe_name)
            f.save(path)
            try:
                pages,text=_extract_pdf_document(path)
                kind=_guess_document_type(text)
                c=db()
                if kind=="STUDENT_LIST":
                    parsed=_parse_student_pdf(pages,text)
                    errors=parsed["errors"]
                    if not errors:
                        # Refuse suspicious roster changes instead of silently
                        # replacing a large existing class with bad extraction.
                        existing=c.execute("select count(*) from students where course=? and section=?",(parsed["rows"][0]["course"],parsed["rows"][0]["section"])).fetchone()[0]
                        if existing and abs(existing-len(parsed["rows"])) > max(10,round(existing*0.25)):
                            errors.append(f"PDF contains {len(parsed['rows'])} students but the current section has {existing}. Change is too large for automatic import.")
                    if not errors:
                        _apply_imported_students(c,parsed["rows"])
                        c.execute("""insert into document_configs(kind,payload,source_name,updated_at)
                                     values('STUDENT_LIST',?,?,CURRENT_TIMESTAMP)
                                     on conflict(kind) do update set payload=excluded.payload,source_name=excluded.source_name,updated_at=CURRENT_TIMESTAMP""",
                                  (json.dumps(parsed["rows"]),safe_name))
                        c.commit()
                        result=f"<b>Student list imported safely.</b> {len(parsed['rows'])} students validated. Attendance history was not deleted."
                    else:
                        c.rollback()
                        result="<b>Import stopped — no database changes were made.</b><ul>"+''.join(f"<li>{escape(x)}</li>" for x in errors)+"</ul>"
                elif kind=="TIMETABLE":
                    tt,errors=_parse_timetable_pdf(pages,text,c)
                    if not errors:
                        _apply_imported_timetable(c,tt,safe_name)
                        c.commit()
                        # Reconcile old official records only after the new
                        # timetable has passed all validation checks.
                        try:
                            repair_timetable_records()
                            ensure_timetable_and_absences()
                        except Exception as exc:
                            result=f"<b>Timetable saved, but scheduler reconciliation reported an error:</b> {escape(str(exc))}"
                        else:
                            result=f"<b>Timetable imported safely.</b> {len(tt['entries'])} entries and {len(tt['slots'])} time slots validated. Existing attendance was preserved where possible."
                    else:
                        c.rollback()
                        result="<b>Import stopped — no database changes were made.</b><ul>"+''.join(f"<li>{escape(x)}</li>" for x in errors)+"</ul>"
                else:
                    c.close()
                    result="<b>Import stopped:</b> The PDF could not be reliably identified as a student list or timetable."
                    return page("PDF Import",f'<div class="hero"><div><span class="pill">FAIL-SAFE DOCUMENT IMPORT</span><h2>Upload university PDF</h2><p class="muted">The parser supports different table layouts and will refuse ambiguous documents instead of guessing.</p></div></div><div class="card"><form class="form" method="post" enctype="multipart/form-data"><label class="wide">PDF file<input type="file" name="pdf" accept=".pdf" required></label><div><button class="btn primary">Read & Validate PDF</button></div></form></div><div class="card"><div style="padding:20px">{result}</div></div>')
            except Exception as exc:
                try: c.close()
                except Exception: pass
                result=f"<b>Import stopped — no database changes were made.</b><br>{escape(str(exc))}"
            else:
                try: c.close()
                except Exception: pass
    return page("PDF Import",f'<div class="hero"><div><span class="pill">FAIL-SAFE DOCUMENT IMPORT</span><h2>Upload university PDF</h2><p class="muted">Student lists and timetables can use different layouts. The parser validates identifiers, table structure, slots, teachers and duplicates before any update.</p></div></div><div class="card"><form class="form" method="post" enctype="multipart/form-data"><label class="wide">PDF file<input type="file" name="pdf" accept=".pdf" required></label><div><button class="btn primary">Read & Validate PDF</button></div></form></div>{("<div class=card><div class=head><h3>Import Result</h3></div><div style=padding:20px>"+result+"</div></div>") if result else ""}')

# Production upgrade staging enabled.

# --- Production feature pack ---
def upgrade_schema():
    c=db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, entity TEXT, entity_id INTEGER, detail TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS recognition_events(id INTEGER PRIMARY KEY, camera_id INTEGER, student_id INTEGER, lecture_id INTEGER, captured_at TEXT DEFAULT CURRENT_TIMESTAMP, confidence REAL, result TEXT, snapshot_path TEXT, review_status TEXT DEFAULT 'PENDING');
    CREATE TABLE IF NOT EXISTS import_jobs(id INTEGER PRIMARY KEY, filename TEXT, doc_type TEXT, status TEXT, preview TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, imported_by INTEGER);
    """)
    c.commit(); c.close()

def audit(action,entity="",entity_id=None,detail=""):
    c=None
    try:
        u=me(); c=db()
        c.execute("insert into audit_logs(user_id,action,entity,entity_id,detail,created_at) values(?,?,?,?,?,?)",
                  (u["id"] if u else None,action,entity,entity_id,detail,datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")))
        c.commit(); c.close(); return True
    except Exception as exc:
        try:
            if c: c.close()
        except Exception: pass
        app.logger.exception("Audit logging failed: %s",exc)
        return False

@app.route("/lectures",methods=["GET","POST"])
@need("ADMIN","TEACHER")
def lectures():
    u=me(); c=db()
    times=[("09:30","10:15"),("10:20","11:05"),("11:10","11:55"),("12:00","12:45"),("12:50","13:35"),("13:40","14:25"),("14:30","15:15"),("15:20","16:05"),("16:10","16:55")]
    if request.method=="POST":
        sid=int(request.form["subject_id"]); slot=int(request.form["lecture_no"]); lecture_date=request.form["lecture_date"].strip()
        course=request.form.get("course","B.Tech").strip(); section=request.form.get("section","C").strip(); room=request.form.get("room","222").strip()
        teacher_id=u["teacher_id"] if u["role"]=="TEACHER" else (int(request.form.get("teacher_id")) if request.form.get("teacher_id") else None)
        try: chosen_date=datetime.strptime(lecture_date,"%Y-%m-%d").date()
        except ValueError:
            c.close(); flash("Please select a valid date.","danger"); return redirect(url_for("lectures"))
        now_ist=datetime.now(IST)
        if chosen_date == now_ist.date():
            slot_start=datetime.strptime(times[slot-1][0],"%H:%M").time()
            if now_ist.time().replace(second=0,microsecond=0) >= slot_start:
                c.close(); flash(f"Slot {slot} has already started or passed. You can only add a lecture today if its starting time has not passed.","danger"); return redirect(url_for("lectures"))
        if chosen_date.weekday()>=5:
            c.close(); flash("Lectures cannot be added on Saturday or Sunday.","danger"); return redirect(url_for("lectures"))
        if chosen_date < datetime.now().date() or chosen_date > (datetime(datetime.now().year + (1 if datetime.now().month==12 else 0), 1 if datetime.now().month==12 else datetime.now().month+1, 1).date() + timedelta(days=9)):
            c.close(); flash("You can only add lectures from today through the current month and the first 10 days of next month.","danger"); return redirect(url_for("lectures"))
        if slot<1 or slot>len(times):
            c.close(); flash("Invalid lecture slot.","danger"); return redirect(url_for("lectures"))
        subject=c.execute("select * from subjects where id=?",(sid,)).fetchone()
        teacher_teaches_subject = subject and (subject["teacher_id"]==u["teacher_id"] or c.execute("select 1 from lectures where subject_id=? and teacher_id=? limit 1",(sid,u["teacher_id"])).fetchone())
        if not subject or (u["role"]=="TEACHER" and not teacher_teaches_subject):
            c.close(); flash("You can only add lectures for subjects assigned to you.","danger"); return redirect(url_for("lectures"))
        occupied=c.execute("select id from lectures where lecture_date=? and lecture_no=? and course=? and section=? and room=?",(lecture_date,slot,course,section,room)).fetchone()
        timetable_busy=False
        try:
            tt=_load_timetable()
            timetable_busy=(course==tt.get("course","B.Tech") and section==tt.get("section","C") and room==tt.get("room","222") and any(e.get("day")==chosen_date.strftime("%A") and slot in [int(x) for x in e.get("slots",[])] for e in tt.get("entries",[])))
        except Exception:
            pass
        if occupied or timetable_busy:
            c.close(); flash("This slot is already occupied by the official timetable." if timetable_busy else "This slot is already occupied for the selected date, course, section and room.","danger"); return redirect(url_for("lectures"))
        st,en=times[slot-1]
        c.execute("insert into lectures(subject_id,teacher_id,lecture_no,course,section,room,lecture_date,start_time,end_time,slot_label,status) values(?,?,?,?,?,?,?,?,?,?,?)",(sid,teacher_id,slot,course,section,room,lecture_date,st,en,f"Slot {slot}","MANUAL"))
        audit("CREATE_LECTURE","lecture",c.execute("select last_insert_rowid()").fetchone()[0],"manual lecture")
        c.commit()
        email_message=""
        now_ist=datetime.now(IST)
        if chosen_date in (now_ist.date(), now_ist.date()+timedelta(days=1)):
            subject_code=subject["code"]
            sent,email_message=send_lecture_notification(subject["name"],subject_code,lecture_date,st,en,room,section,course)
            if sent:
                flash(f"Lecture created successfully. {email_message}","success")
            else:
                flash(f"Lecture created successfully. {email_message}","warning")
        else:
            flash("Lecture created successfully.","success")
    if u["role"]=="TEACHER":
        subjects=c.execute("""select distinct s.* from subjects s left join lectures l on l.subject_id=s.id where s.teacher_id=? or l.teacher_id=? order by s.name""",(u["teacher_id"],u["teacher_id"])).fetchall()
        lectures=c.execute("select l.*,s.code,s.name subject_name from lectures l join subjects s on s.id=l.subject_id where (l.teacher_id=? or s.teacher_id=?) and s.code not in ('SELF','MENTOR') order by l.lecture_date desc,l.lecture_no",(u["teacher_id"],u["teacher_id"])).fetchall()
    else:
        subjects=c.execute("select * from subjects order by name").fetchall()
        lectures=c.execute("select l.*,s.code,s.name subject_name from lectures l join subjects s on s.id=l.subject_id order by l.lecture_date desc,l.lecture_no limit 100").fetchall()
    teachers=c.execute("select * from teachers order by name").fetchall()
    schedule_rows=c.execute("select lecture_date,lecture_no,course,section,room from lectures").fetchall()
    timetable_busy=[]
    try:
        tt=_load_timetable()
        days=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        for e in tt.get("entries",[]):
            for n in e.get("slots",[]):
                timetable_busy.append({"weekday":days.index(e["day"]),"course":tt.get("course","B.Tech"),"section":tt.get("section","C"),"room":tt.get("room","222"),"slot":int(n)})
    except Exception:
        pass
    c.close()
    subject_opts="".join(f'<option value="{s["id"]}">{s["name"]}</option>' for s in subjects)
    teacher_opts="".join(f'<option value="{t["id"]}">{t["name"]}</option>' for t in teachers)
    rows="".join(f'<tr><td>{x["lecture_date"]}</td><td>Slot {x["lecture_no"]}</td><td>{x["subject_name"]}</td><td>{x["room"]}</td><td>{x["section"]}</td><td>{x["course"]}</td></tr>' for x in lectures) or '<tr><td colspan="6">No lectures scheduled.</td></tr>'
    schedule_json=json.dumps([dict(x) for x in schedule_rows]); today_obj=datetime.now().date()
    next_month_start=datetime(today_obj.year + (1 if today_obj.month==12 else 0), 1 if today_obj.month==12 else today_obj.month+1, 1).date()
    month_end=(next_month_start-timedelta(days=1)).isoformat()
    # Allow the rest of the current month + first 10 days of the next month.
    next_month_limit=(next_month_start+timedelta(days=9)).isoformat()
    today=today_obj.isoformat()
    teacher_field=f'<label>Teacher<select name="teacher_id">{teacher_opts}</select></label>' if u["role"]=="ADMIN" else ""
    body=f"""<style>.lecture-form{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;padding-top:8px}}.lecture-form .wide{{grid-column:1/-1}}.date-picker{{position:relative}}.date-picker>input{{cursor:pointer}}.calendar-pop{{display:none;position:absolute;z-index:100;top:58px;left:0;width:330px;padding:15px;border:1px solid #304563;border-radius:16px;background:#0c182a;box-shadow:0 18px 45px #0008}}.calendar-pop.open{{display:block}}.cal-head{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}.cal-head button{{width:34px;height:34px;border:1px solid #304563;border-radius:9px;background:#13243b;color:#fff;font-size:20px;cursor:pointer}}.cal-head button:disabled{{opacity:.25;cursor:not-allowed}}.cal-week,.cal-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:5px}}.cal-week span{{font-size:10px;text-align:center;color:#72849f;font-weight:800;padding:5px 0}}.cal-week .weekend{{color:#46546a}}.cal-day,.cal-empty{{height:35px}}.cal-day{{border:0;border-radius:9px;background:#13243b;color:#eaf0fa;cursor:pointer}}.cal-day:hover:not(:disabled),.cal-day.selected{{background:#526dff;color:#fff}}.cal-day.disabled{{background:#0a1422;color:#3d4b60;cursor:not-allowed;text-decoration:line-through}}.lecture-form label{{display:flex;flex-direction:column;gap:8px;font-size:12px;font-weight:850;color:#9dafc8;text-transform:uppercase;letter-spacing:.04em}}.lecture-form input,.lecture-form select{{box-sizing:border-box;width:100%;min-height:48px;border:1px solid #304563;border-radius:12px;background:#101f34;color:#f4f7ff;padding:0 14px;font-size:14px;outline:none}}.lecture-form input:focus,.lecture-form select:focus{{border-color:#637dff;box-shadow:0 0 0 3px #526eff22}}.lecture-form select option{{background:#101f34;color:#fff}}.lecture-form .wide:last-child{{display:flex;justify-content:center;align-items:center;padding-top:8px}}.lecture-form .wide:last-child .btn{{min-width:210px;min-height:50px;border-radius:14px;font-size:15px;box-shadow:0 8px 20px #526dff33}}.slot-help{{padding:15px 17px;border:1px solid #263c5d;border-radius:13px;background:#0a1628;color:#8fa0b8;font-size:12px}}.slot-help b{{color:#fff}}@media(max-width:800px){{.lecture-form{{grid-template-columns:1fr}}.lecture-form .wide{{grid-column:auto}}}}</style>
<div class="card"><div class="head"><div><span class="pill">LECTURE MANAGEMENT</span><h2 style="margin:8px 0 6px;font-size:28px">Add a New Lecture</h2><p class="muted">Choose one of your assigned subjects, a weekday, and an available timetable slot.</p></div></div>
<form class="lecture-form" method="post" id="lecture-form"><label>Subject<select name="subject_id" required>{subject_opts}</select></label><label class="date-field">Date<div class="date-picker" id="date-picker"><input type="text" id="lecture-date-display" placeholder="Select a weekday" readonly required><input type="hidden" name="lecture_date" id="lecture-date" required><div class="calendar-pop" id="calendar-pop"><div class="cal-head"><button type="button" id="cal-prev">‹</button><b id="cal-title"></b><button type="button" id="cal-next">›</button></div><div class="cal-week"><span>MON</span><span>TUE</span><span>WED</span><span>THU</span><span>FRI</span><span class="weekend">SAT</span><span class="weekend">SUN</span></div><div class="cal-grid" id="cal-grid"></div></div></div></label><label>Course<input name="course" id="lecture-course" value="B.Tech" required></label><label>Section<input name="section" id="lecture-section" value="C" required></label><label>Room Number<input name="room" id="lecture-room" value="222" required></label><label>Slot<select name="lecture_no" id="lecture-slot" required></select></label>{teacher_field}<div class="wide slot-help" id="slot-help">Choose the date, course, section and room. Only free slots will be available.</div><div class="wide"><button class="btn primary" type="submit">Create Lecture</button></div></form></div>
<div class="card"><div class="head"><h3>Lecture Schedule</h3><span class="pill">{len(lectures)} lectures</span></div><div class="table"><table><tr><th>Date</th><th>Slot</th><th>Subject</th><th>Room</th><th>Section</th><th>Course</th></tr>{rows}</table></div></div>
<script>
const lectureSchedule={schedule_json}, timetableBusy={json.dumps(timetable_busy)}, slots={json.dumps(times)}, d=document.getElementById("lecture-date"), dd=document.getElementById("lecture-date-display"), c=document.getElementById("lecture-course"), s=document.getElementById("lecture-section"), r=document.getElementById("lecture-room"), sl=document.getElementById("lecture-slot"), h=document.getElementById("slot-help");
const minDate=new Date("{today}T00:00:00"), maxDate=new Date("{next_month_limit}T00:00:00"); let calMonth=new Date(minDate.getFullYear(),minDate.getMonth(),1);
function iso(x){{return x.getFullYear()+"-"+String(x.getMonth()+1).padStart(2,"0")+"-"+String(x.getDate()).padStart(2,"0")}}
function weekend(x){{return x.getDay()===0||x.getDay()===6}}
function renderCalendar(){{const grid=document.getElementById("cal-grid"),title=document.getElementById("cal-title");title.textContent=calMonth.toLocaleString("en-IN",{{month:"long",year:"numeric"}});grid.innerHTML="";const first=new Date(calMonth.getFullYear(),calMonth.getMonth(),1),offset=(first.getDay()+6)%7,days=new Date(calMonth.getFullYear(),calMonth.getMonth()+1,0).getDate();for(let i=0;i<offset;i++)grid.insertAdjacentHTML("beforeend",'<span class="cal-empty"></span>');for(let day=1;day<=days;day++){{const x=new Date(calMonth.getFullYear(),calMonth.getMonth(),day),v=iso(x),disabled=x<minDate||x>maxDate||weekend(x),b=document.createElement("button");b.type="button";b.className="cal-day"+(disabled?" disabled":"")+(v===d.value?" selected":"");b.textContent=day;b.disabled=disabled;b.title=disabled?(weekend(x)?"Weekend — not available":x<minDate?"Past date — not available":"Only the first 10 days of next month are available"):"Select date";b.onclick=()=>{{d.value=v;dd.value=x.toLocaleDateString("en-IN",{{day:"2-digit",month:"short",year:"numeric"}});document.getElementById("calendar-pop").classList.remove("open");refreshSlots();renderCalendar()}};grid.appendChild(b)}}const currentMonth=new Date(minDate.getFullYear(),minDate.getMonth(),1),maximumMonth=new Date(maxDate.getFullYear(),maxDate.getMonth(),1);document.getElementById("cal-prev").disabled=calMonth<=currentMonth;document.getElementById("cal-next").disabled=calMonth>=maximumMonth}}
dd.onclick=()=>document.getElementById("calendar-pop").classList.toggle("open");
document.getElementById("cal-prev").onclick=()=>{{const currentMonth=new Date(minDate.getFullYear(),minDate.getMonth(),1);if(calMonth>currentMonth){{calMonth=new Date(calMonth.getFullYear(),calMonth.getMonth()-1,1);renderCalendar()}}}};
document.getElementById("cal-next").onclick=()=>{{const maximumMonth=new Date(maxDate.getFullYear(),maxDate.getMonth(),1);if(calMonth<maximumMonth){{calMonth=new Date(calMonth.getFullYear(),calMonth.getMonth()+1,1);renderCalendar()}}}};
document.addEventListener("click",e=>{{if(!document.getElementById("date-picker").contains(e.target))document.getElementById("calendar-pop").classList.remove("open")}});
function refreshSlots(){{const date=d.value,course=c.value.trim(),section=s.value.trim(),room=r.value.trim();sl.innerHTML="";if(!date||date<iso(minDate)||date>iso(maxDate)||weekend(new Date(date+"T00:00:00")) ){{sl.disabled=true;h.innerHTML="<b>Only Monday–Friday dates from today through this month and the first 10 days of next month are available.</b>";return}}sl.disabled=false;let free=0;slots.forEach((t,i)=>{{const n=i+1,weekday=(new Date(date+"T00:00:00").getDay()+6)%7,manualBusy=lectureSchedule.some(x=>x.lecture_date===date&&Number(x.lecture_no)===n&&x.course===course&&x.section===section&&x.room===room),officialBusy=timetableBusy.some(x=>x.weekday===weekday&&x.slot===n&&x.course===course&&x.section===section&&x.room===room);if(manualBusy||officialBusy)return;const o=document.createElement("option");o.value=n;o.textContent="Slot "+n+" ("+t[0]+"–"+t[1]+")";free++;sl.appendChild(o)}});sl.disabled=!free;h.innerHTML=free?"<b>"+free+" slots available.</b> Occupied slots are unavailable.":"<b>No free slots.</b> Change room, section, course or date."}}
[c,s,r].forEach(x=>x.addEventListener("input",refreshSlots));
document.getElementById("lecture-form").addEventListener("submit",e=>{{if(!d.value||d.value<iso(minDate)||d.value>iso(maxDate)||weekend(new Date(d.value+"T00:00:00"))){{e.preventDefault();alert("Please select a weekday from today through this month or the first 10 days of next month.")}}}});
renderCalendar();refreshSlots();
</script></script>"""
    return page("Lecture Management",body)

@app.route("/reports")
@need("ADMIN")
def reports():
    c=db()
    students=c.execute("select * from students order by name").fetchall()
    rows=[]
    for s in students:
        total=c.execute("select count(*) from lectures l join subjects s2 on s2.id=l.subject_id where l.course=? and l.section=? and l.status='PDF_SCHEDULED' and s2.code not in ('SELF','MENTOR') and (l.group_name is null or l.group_name='' or l.group_name=?)",(s["course"],s["section"],s["group_name"] or "")).fetchone()[0]
        present=c.execute("""select count(*) from attendance a join lectures l on l.id=a.lecture_id join subjects s2 on s2.id=l.subject_id
            where a.student_id=? and a.source in ('TEACHER_OVERRIDE','ADMIN_OVERRIDE','AI_RECOGNITION') and s2.code not in ('SELF','MENTOR')""",(s["id"],)).fetchone()[0]
        pct=(present/total*100) if total else 0
        rows.append(f'<tr><td>{s["name"]}</td><td>{s["enrollment_no"]}</td><td>{s["course"]}</td><td>{s["section"]}</td><td>{pct:.1f}%</td><td>{present}/{total}</td></tr>')
    c.close()
    return page("Attendance Reports",'<div class="hero"><div><span class="pill">REPORTING</span><h2>Overall attendance</h2><p class="muted">Export the current register as CSV.</p></div><a class="btn primary" href="/reports.csv">Export CSV</a></div><div class="card"><div class="table"><table><tr><th>Student</th><th>Enrollment</th><th>Course</th><th>Section</th><th>Attendance</th><th>Present/Total</th></tr>'+''.join(rows)+'</table></div></div>')

@app.route("/reports.csv")
@need("ADMIN")
def reports_csv():
    c=db(); out=io.StringIO(); w=csv.writer(out); w.writerow(["Student","Enrollment","Course","Section","Attendance Percent","Present","Total"])
    for s in c.execute("select * from students order by name").fetchall():
        total=c.execute("select count(*) from lectures l join subjects s2 on s2.id=l.subject_id where l.course=? and l.section=? and l.status='PDF_SCHEDULED' and s2.code not in ('SELF','MENTOR') and (l.group_name is null or l.group_name='' or l.group_name=?)",(s["course"],s["section"],s["group_name"] or "")).fetchone()[0]
        present=c.execute("""select count(*) from attendance a join lectures l on l.id=a.lecture_id join subjects s2 on s2.id=l.subject_id
            where a.student_id=? and a.source in ('TEACHER_OVERRIDE','ADMIN_OVERRIDE','AI_RECOGNITION') and s2.code not in ('SELF','MENTOR')""",(s["id"],)).fetchone()[0]
        w.writerow([s["name"],s["enrollment_no"],s["course"],s["section"],f"{(present/total*100 if total else 0):.1f}",present,total])
    c.close(); data=io.BytesIO(out.getvalue().encode()); data.seek(0)
    return send_file(data,mimetype="text/csv",as_attachment=True,download_name="attendance_report.csv")

@app.route("/audit")
@need("ADMIN")
def audit_logs():
    c=db()
    logs=c.execute("select a.*,u.display_name from audit_logs a left join users u on u.id=a.user_id order by a.id desc limit 200").fetchall()
    c.close()
    rows="".join(f'<tr><td>{x["created_at"]}</td><td>{x["display_name"] or "System"}</td><td><b>{x["action"]}</b></td><td>{x["entity"] or "—"}</td><td>{x["detail"] or "—"}</td></tr>' for x in logs)
    if not rows:
        rows='<tr><td colspan="5" style="padding:28px;text-align:center;color:#8291aa">No audit events recorded yet. New logins, logouts, attendance saves, lecture changes and camera additions will appear here.</td></tr>'
    return page("Audit Logs",f'<div class="hero"><div><span class="pill">SYSTEM ACTIVITY</span><h2>Audit Logs</h2><p class="muted">Security and administrative actions are recorded with date, user and details.</p></div><div class="overall-box"><div class="value">{len(logs)}</div><div class="label">RECENT EVENTS</div></div></div><div class="card"><div class="table"><table><tr><th>Time (IST)</th><th>User</th><th>Action</th><th>Entity</th><th>Details</th></tr>{rows}</table></div></div>')

@app.route("/recognition")
@need("ADMIN")
def recognition_review():
    c=db(); events=c.execute("select r.*,s.name student_name,c.camera_name from recognition_events r left join students s on s.id=r.student_id left join cameras c on c.id=r.camera_id order by r.id desc limit 100").fetchall(); c.close()
    rows="".join(f'<tr><td>{x["captured_at"]}</td><td>{x["camera_name"] or "—"}</td><td>{x["student_name"] or "UNKNOWN"}</td><td>{x["result"]}</td><td>{(str(round(x["confidence"],1))+"%") if x["confidence"] is not None else "—"}</td><td>{x["review_status"]}</td></tr>' for x in events)
    return page("Recognition Review",f'<div class="hero"><div><span class="pill">REVIEW QUEUE</span><h2>Recognition events</h2><p class="muted">Uncertain matches stay UNKNOWN until reviewed.</p></div></div><div class="card"><div class="table"><table><tr><th>Time</th><th>Camera</th><th>Student</th><th>Result</th><th>Confidence</th><th>Review</th></tr>{rows or "<tr><td colspan=6>No recognition events.</td></tr>"}</table></div></div>')

@app.route("/api/recognition",methods=["POST"])
@need("ADMIN")
def recognition_api():
    data=request.get_json(silent=True) or {}
    confidence=float(data.get("confidence",0)); sid=data.get("student_id"); lid=data.get("lecture_id"); cid=data.get("camera_id")
    result="MATCH" if sid and confidence>=85 else "UNKNOWN"
    c=db(); c.execute("insert into recognition_events(camera_id,student_id,lecture_id,confidence,result) values(?,?,?,?,?)",(cid,sid if result=="MATCH" else None,lid,confidence,result))
    if result=="MATCH" and lid and sid:
        lec=c.execute("select * from lectures where id=?",(lid,)).fetchone()
        if lec:
            c.execute("""insert into attendance(student_id,subject_id,lecture_id,attendance_date,source,marked_by)
                values(?,?,?,?,?,?)
                on conflict(student_id,lecture_id,attendance_date) do update set subject_id=excluded.subject_id,source=excluded.source,marked_by=excluded.marked_by""",
                (sid,lec["subject_id"],lid,lec["lecture_date"],"AI_RECOGNITION",None))
    c.commit(); c.close(); return {"ok":True,"result":result,"confidence":confidence}


# --- PDF timetable scheduler + automatic absence engine ---
from datetime import date, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# Keep attendance-history generation tied to the timetable source. This means
# when timetable slots are added later, the startup reconciliation below
# backfills the missing lecture + AUTO_ABSENT records from the app start date
# through today instead of requiring manual attendance-history edits.
def _timetable_start_date():
    try:
        value = _load_timetable().get("app_start_date", "2026-10-01")
        return date.fromisoformat(value)
    except Exception:
        return date(2026, 10, 1)

APP_START_DATE = _timetable_start_date()

def _load_timetable():
    # A validated PDF import becomes the authoritative timetable and survives
    # Render/container restarts because it is stored in SQLite.
    try:
        c=db()
        row=c.execute("select payload from document_configs where kind='TIMETABLE'").fetchone()
        c.close()
        if row and row["payload"]:
            return json.loads(row["payload"])
    except Exception:
        pass
    with open(os.path.join(os.path.dirname(__file__),"data","timetable_3_c.json"),"r",encoding="utf-8") as f:
        return json.load(f)

def _get_schedule_teacher(c, employee_code):
    if not employee_code:
        return None
    row=c.execute("select id from teachers where employee_code=?",(employee_code,)).fetchone()
    return row["id"] if row else None

def _get_schedule_subject(c, code, name, teacher_id):
    row=c.execute("select id from subjects where code=?",(code,)).fetchone()
    if row:
        c.execute("update subjects set name=?,semester=3,section='C',teacher_id=? where id=?",(name,teacher_id,row["id"]))
        return row["id"]
    c.execute("insert into subjects(code,name,semester,section,teacher_id) values(?,?,?,?,?)",(code,name,3,"C",teacher_id))
    return c.execute("select last_insert_rowid()").fetchone()[0]

def repair_timetable_records():
    """Reconcile previously generated PDF timetable lectures after timetable corrections."""
    tt=_load_timetable()
    today=datetime.now(IST).date()
    slots={int(x["no"]):x for x in tt["slots"]}
    day_numbers={"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4}
    expected={}
    d=APP_START_DATE
    while d<=today:
        day=d.strftime("%A")
        for e in tt.get("entries",[]):
            if day_numbers.get(e.get("day")) != d.weekday():
                continue
            for n in e.get("slots",[]):
                expected[(d.isoformat(),e.get("subject_code"),int(n),e.get("group") or "")]=e
        d += timedelta(days=1)

    c=db()
    old=c.execute("""select l.*,s.code subject_code from lectures l
        join subjects s on s.id=l.subject_id
        where l.status='PDF_SCHEDULED' and l.lecture_date>=? and l.lecture_date<=?
        and l.course=? and l.section=?""",
        (APP_START_DATE.isoformat(),today.isoformat(),tt.get("course","B.Tech"),tt.get("section","C"))).fetchall()

    # Remove timetable-generated records that no longer belong to the official
    # timetable. Preserve any attendance by moving it to the first corrected
    # lecture for the same subject/date/group when possible.
    for lec in old:
        key=(lec["lecture_date"],lec["subject_code"],int(lec["lecture_no"]),lec["group_name"] or "")
        if key in expected:
            continue
        candidates=[x for x in old if x["lecture_date"]==lec["lecture_date"] and x["subject_code"]==lec["subject_code"] and (x["group_name"] or "")==(lec["group_name"] or "") and
                    (x["lecture_date"],x["subject_code"],int(x["lecture_no"]),x["group_name"] or "") in expected]
        target=candidates[0] if candidates else None
        if target and target["id"] != lec["id"]:
            rows=c.execute("select * from attendance where lecture_id=?",(lec["id"],)).fetchall()
            for a in rows:
                exists=c.execute("select id from attendance where student_id=? and lecture_id=? and attendance_date=?",
                                 (a["student_id"],target["id"],a["attendance_date"])).fetchone()
                if not exists:
                    c.execute("""insert into attendance(student_id,subject_id,lecture_id,attendance_date,source,marked_by)
                        values(?,?,?,?,?,?)""",
                        (a["student_id"],target["subject_id"],target["id"],a["attendance_date"],a["source"],a["marked_by"]))
        c.execute("delete from attendance where lecture_id=?",(lec["id"],))
        c.execute("delete from lectures where id=?",(lec["id"],))

    # Update the slot metadata for surviving official records.
    for key,e in expected.items():
        dstr,code,n,group=key
        sl=slots[n]
        sid=c.execute("select id from subjects where code=?",(code,)).fetchone()
        if not sid:
            continue
        row=c.execute("""select id from lectures where subject_id=? and lecture_date=? and lecture_no=?
            and course=? and section=? and ifnull(group_name,'')=ifnull(?, '') and status='PDF_SCHEDULED'""",
            (sid["id"],dstr,n,tt.get("course","B.Tech"),tt.get("section","C"),group)).fetchone()
        if row:
            teacher_id=_get_schedule_teacher(c,e.get("teacher_code"))
            c.execute("""update lectures set teacher_id=?,room=?,start_time=?,end_time=?,slot_label=?,lecture_day=?,effective_from=?
                where id=?""",
                (teacher_id,tt.get("room","222"),sl["start"],sl["end"],"Slot "+sl["label"],dstr and datetime.fromisoformat(dstr).strftime("%A"),
                 tt.get("effective_from"),row["id"]))
    c.commit()
    c.close()

def ensure_timetable_and_absences():
    tt=_load_timetable()
    today=datetime.now(IST).date()
    end_date=max(today,APP_START_DATE)
    slots={int(x["no"]):x for x in tt["slots"]}
    labels={x["label"]:int(x["no"]) for x in tt["slots"]}
    day_numbers={"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4}
    c=db()

    # Migrate old multi-slot lecture records into one lecture per slot.
    # Older builds stored e.g. Slot III-V as a single lecture, which caused
    # one attendance mark to count for three timetable periods.
    combined=c.execute("""select * from lectures
        where status='PDF_SCHEDULED' and lecture_date>=? and course='B.Tech' and section='C'
        and instr(ifnull(slot_label,''),'-')>0""",(APP_START_DATE.isoformat(),)).fetchall()
    for old in combined:
        label=(old["slot_label"] or "").replace("Slot ","").strip()
        parts=label.split("-",1)
        if len(parts)!=2 or parts[0] not in labels or parts[1] not in labels:
            continue
        first_no,last_no=labels[parts[0]],labels[parts[1]]
        if last_no<=first_no:
            continue

        old_attendance=c.execute("select * from attendance where lecture_id=?",(old["id"],)).fetchall()
        first_slot=slots[first_no]
        c.execute("""update lectures set lecture_no=?,start_time=?,end_time=?,slot_label=?
            where id=?""",
            (first_no,first_slot["start"],first_slot["end"],"Slot "+first_slot["label"],old["id"]))

        for slot_no in range(first_no+1,last_no+1):
            if slot_no not in slots:
                continue
            sl=slots[slot_no]
            existing=c.execute("""select id from lectures where subject_id=? and lecture_date=? and
                lecture_no=? and course='B.Tech' and section='C' and ifnull(group_name,'')=ifnull(?, '')""",
                (old["subject_id"],old["lecture_date"],slot_no,old["group_name"])).fetchone()
            if existing:
                new_id=existing["id"]
            else:
                c.execute("""insert into lectures(subject_id,teacher_id,lecture_no,course,section,room,lecture_date,
                    start_time,end_time,group_name,slot_label,lecture_day,effective_from,status,source_file_id)
                    values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (old["subject_id"],old["teacher_id"],slot_no,old["course"],old["section"],old["room"],
                     old["lecture_date"],sl["start"],sl["end"],old["group_name"],"Slot "+sl["label"],
                     old["lecture_day"],old["effective_from"],old["status"],old["source_file_id"]))
                new_id=c.execute("select last_insert_rowid()").fetchone()[0]
            for a in old_attendance:
                c.execute("""insert into attendance(student_id,subject_id,lecture_id,attendance_date,source,marked_by)
                    values(?,?,?,?,?,?)
                    on conflict(student_id,lecture_id,attendance_date) do update set
                    subject_id=excluded.subject_id,source=excluded.source,marked_by=excluded.marked_by""",
                    (a["student_id"],a["subject_id"],new_id,a["attendance_date"],a["source"],a["marked_by"]))

    # Generate one lecture record for EVERY timetable slot, not one record
    # for a block of continuous slots.
    for n in range((end_date-APP_START_DATE).days+1):
        d=APP_START_DATE+timedelta(days=n)
        day=d.strftime("%A")
        for e in tt["entries"]:
            if day_numbers.get(e["day"])!=d.weekday():
                continue
            tid=_get_schedule_teacher(c,e.get("teacher_code"))
            sid=_get_schedule_subject(c,e["subject_code"],e["subject_name"],tid)
            group=e.get("group")
            for slot_no in e["slots"]:
                sl=slots[slot_no]
                exists=c.execute("""select id from lectures where subject_id=? and lecture_date=? and lecture_no=? and
                    course='B.Tech' and section='C' and ifnull(group_name,'')=ifnull(?, '')""",
                    (sid,d.isoformat(),slot_no,group)).fetchone()
                if not exists:
                    c.execute("""insert into lectures(subject_id,teacher_id,lecture_no,course,section,room,lecture_date,
                        start_time,end_time,group_name,slot_label,lecture_day,effective_from,status)
                        values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (sid,tid,slot_no,"B.Tech","C",tt["room"],d.isoformat(),sl["start"],sl["end"],
                         group,"Slot "+sl["label"],day,tt["effective_from"],"PDF_SCHEDULED"))
                else:
                    # Keep official timetable records synchronized with the
                    # current timetable/teacher assignments. This is important
                    # when a teacher teaches multiple subjects or an assignment
                    # is corrected after records were already generated.
                    c.execute("""update lectures
                        set teacher_id=?, subject_id=?, room=?, start_time=?, end_time=?,
                            slot_label=?, lecture_day=?, effective_from=?, status='PDF_SCHEDULED'
                        where id=?""",
                        (tid,sid,tt["room"],sl["start"],sl["end"],"Slot "+sl["label"],
                         day,tt["effective_from"],exists["id"]))
    c.commit()

    # Every completed timetable slot gets an attendance row. If nobody has
    # marked the student present, the slot is explicitly AUTO_ABSENT.
    now=datetime.now(IST)
    lectures=c.execute("""select * from lectures where lecture_date>=? and lecture_date<=?
        and course='B.Tech' and section='C' and status='PDF_SCHEDULED'""",
        (APP_START_DATE.isoformat(),today.isoformat())).fetchall()
    for lec in lectures:
        if lec["subject_id"] is None:
            continue
        subject_row=c.execute("select code from subjects where id=?",(lec["subject_id"],)).fetchone()
        if subject_row and subject_row["code"] in ("SELF","MENTOR"):
            continue
        try:
            end_dt=datetime.fromisoformat(lec["lecture_date"]+"T"+(lec["end_time"] or "23:59")).replace(tzinfo=IST)
        except Exception:
            end_dt=datetime.fromisoformat(lec["lecture_date"]+"T23:59").replace(tzinfo=IST)
        if end_dt>now:
            continue
        students=c.execute("""select * from students where course='B.Tech' and section='C'
            and (group_name is null or group_name='' or group_name=?)""",(lec["group_name"] or "",)).fetchall()
        for st in students:
            if not c.execute("select id from attendance where student_id=? and lecture_id=? and attendance_date=?",
                             (st["id"],lec["id"],lec["lecture_date"])).fetchone():
                c.execute("""insert into attendance(student_id,subject_id,lecture_id,attendance_date,source,marked_by)
                    values(?,?,?,?,?,NULL)""",
                    (st["id"],lec["subject_id"],lec["id"],lec["lecture_date"],"AUTO_ABSENT"))
    c.commit()
    c.close()

init()
upgrade_schema()
sync_admin_accounts()
repair_timetable_records()
ensure_timetable_and_absences()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
