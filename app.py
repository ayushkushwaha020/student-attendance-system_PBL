from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3, os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")
DB = os.path.join(os.path.dirname(__file__), "attendance.db")
UPLOADS = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS, exist_ok=True)

CSS = """
*{box-sizing:border-box}body{margin:0;background:#07101d;color:#edf3ff;font:14px Inter,system-ui,sans-serif}
a{color:inherit;text-decoration:none}.shell{display:flex;min-height:100vh}.side{position:fixed;left:0;top:0;bottom:0;width:245px;background:#091321;border-right:1px solid #20304a;padding:22px 15px;z-index:3}
.brand{display:flex;gap:10px;align-items:center;padding:4px 10px 25px}.logo{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;background:linear-gradient(135deg,#6978ff,#43d7ff);font-weight:900}
.brand b{display:block}.brand small{color:#7d8ca5}.nav{color:#8f9db4;font-weight:700;font-size:12px}.nav a{display:block;padding:12px 11px;border-radius:10px;margin:4px 0}.nav a:hover{background:#15233a;color:#fff}
.main{margin-left:245px;width:calc(100% - 245px)}.top{height:82px;border-bottom:1px solid #20304a;padding:18px 30px;display:flex;justify-content:space-between;align-items:center;background:#091321dd;backdrop-filter:blur(12px);position:sticky;top:0;z-index:2}
.top h1{font-size:22px;margin:3px 0}.muted{color:#8291aa}.content{padding:28px;max-width:1500px}.hero,.card{background:linear-gradient(145deg,#101d30,#0b1525);border:1px solid #22344f;border-radius:17px;box-shadow:0 18px 45px #0004}.hero{padding:26px;display:flex;justify-content:space-between;gap:20px;margin-bottom:18px}.hero h2{margin:8px 0;font-size:28px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}.stat{padding:18px}.stat span{display:block;color:#8492aa;font-size:11px}.stat b{display:block;font-size:27px;margin-top:5px}.card{overflow:hidden;margin-bottom:18px}.head{padding:17px 19px;border-bottom:1px solid #22344f;display:flex;justify-content:space-between;align-items:center}.head h3{margin:3px 0}.table{overflow:auto}table{width:100%;border-collapse:collapse;min-width:650px}th,td{text-align:left;padding:12px 15px;border-bottom:1px solid #1b2a40}th{font-size:10px;color:#7888a1;text-transform:uppercase}td b{color:#fff}.btn{display:inline-block;padding:10px 14px;border-radius:10px;border:1px solid #304565;background:#15243a;font-weight:800}.btn.primary{background:linear-gradient(135deg,#6978ff,#4d60dd);border-color:#7180ff}.btn.green{background:#10392f;border-color:#246b55}.form{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;padding:18px}.form label{color:#8492aa;font-size:11px;font-weight:700}.form input,.form select{width:100%;margin-top:6px;padding:11px;border-radius:9px;border:1px solid #2a3d59;background:#07111e;color:#fff}.form .wide{grid-column:1/-1}.flash{padding:12px 15px;border:1px solid #2c4262;background:#101e31;border-radius:10px;margin-bottom:12px}.pill{display:inline-block;padding:5px 8px;border-radius:999px;background:#17294a;color:#9eb0ff;font-size:10px;font-weight:900}.login{min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 70% 10%,#1d2d61,#07101d 45%)}.loginbox{width:min(430px,92vw);padding:30px}.loginbox input{display:block;width:100%;padding:13px;margin:8px 0 14px;border:1px solid #2a3d59;background:#07111e;color:#fff;border-radius:10px}.loginbox button{width:100%;padding:13px;border:0;border-radius:10px;background:#6575ff;color:#fff;font-weight:900}.ring{font-size:38px;font-weight:900;color:#66dfb5}.greenText{color:#55d9ad}.orange{color:#ffb15e}.red{color:#ff6878}.black{color:#fff}.small{font-size:11px}
@media(max-width:900px){.side{width:70px}.brand div:not(.logo),.nav a span{display:none}.main{margin-left:70px;width:calc(100% - 70px)}.grid{grid-template-columns:repeat(2,1fr)}.form{grid-template-columns:1fr}.hero{flex-direction:column}}
"""

def db():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    return c

def init():
    c=db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password TEXT,role TEXT,display_name TEXT,student_id INTEGER,teacher_id INTEGER);
    CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY,enrollment_no TEXT UNIQUE,name TEXT,course TEXT DEFAULT 'BCA',semester INTEGER DEFAULT 3,section TEXT DEFAULT 'G');
    CREATE TABLE IF NOT EXISTS teachers(id INTEGER PRIMARY KEY,employee_code TEXT UNIQUE,name TEXT);
    CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY,code TEXT UNIQUE,name TEXT,semester INTEGER,section TEXT);
    CREATE TABLE IF NOT EXISTS lectures(id INTEGER PRIMARY KEY,subject_id INTEGER,teacher_id INTEGER,lecture_no INTEGER,course TEXT,section TEXT,room TEXT,lecture_date TEXT);
    CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY,student_id INTEGER,subject_id INTEGER,lecture_id INTEGER,attendance_date TEXT,source TEXT,marked_by INTEGER,UNIQUE(student_id,lecture_id,attendance_date));
    CREATE TABLE IF NOT EXISTS cameras(id INTEGER PRIMARY KEY,camera_name TEXT,location TEXT,stream_url TEXT,authorized INTEGER DEFAULT 0);
    """)
    if c.execute("select count(*) from users").fetchone()[0] == 0:
        c.execute("insert into teachers(employee_code,name) values('T001','Demo Teacher')")
        tid=c.execute("select last_insert_rowid()").fetchone()[0]
        c.execute("insert into students(enrollment_no,name,course,semester,section) values('DEMO001','Demo Student','BCA',3,'G')")
        sid=c.execute("select last_insert_rowid()").fetchone()[0]
        c.execute("insert into users(username,password,role,display_name,teacher_id) values('teacher','teacher123','TEACHER','Demo Teacher',?)",(tid,))
        c.execute("insert into users(username,password,role,display_name,student_id) values('student','student123','STUDENT','Demo Student',?)",(sid,))
        c.execute("insert into users(username,password,role,display_name) values('admin','admin123','ADMIN','University Administrator')")
        for code,name in [('DSA','Data Structures & Algorithms'),('AIML','Introduction to AI & ML'),('IOT','Introduction to IOT'),('MATH','Engineering Maths III')]:
            c.execute("insert into subjects(code,name,semester,section) values(?,?,3,'G')",(code,name))
        c.execute("insert into cameras(camera_name,location,stream_url) values('Demo Classroom Camera','Room 222','')")
    c.commit(); c.close()

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
    nav=""
    if u:
        nav=f'<aside class="side"><div class="brand"><div class="logo">AI</div><div><b>AttendAI</b><small>University System</small></div></div><nav class="nav"><a href="/dashboard">⌂ Dashboard</a>'
        if u["role"] in ("ADMIN","TEACHER"): nav+='<a href="/attendance">✓ Attendance</a><a href="/lectures">◷ Lectures</a>'
        if u["role"]=="ADMIN": nav+='<a href="/import">⇧ PDF Import</a><a href="/students">♙ Students</a><a href="/lectures">◷ Lectures</a><a href="/cameras">◉ Cameras</a><a href="/recognition">◎ Recognition</a><a href="/reports">▥ Reports</a><a href="/audit">⌁ Audit Logs</a>'
        if u["role"]=="STUDENT": nav+='<a href="/student/attendance">▤ My Attendance</a>'
        nav+='<a href="/logout">↪ Logout</a></nav></aside>'
    flashes="".join(f'<div class="flash">{m}</div>' for m in [x[1] for x in []])
    html=f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body>
    <div class="shell">{nav}<main class="main"><header class="top"><div><span class="pill">AI ATTENDANCE</span><h1>{title}</h1></div><div class="muted">{u["display_name"] if u else "Secure Login"}</div></header><section class="content">{flashes}{body}</section></main></div></body></html>"""
    return html

@app.route("/")
def home(): return redirect(url_for("dashboard") if me() else url_for("login"))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        c=db(); u=c.execute("select * from users where username=? and password=?",(request.form["username"].strip(),request.form["password"])).fetchone(); c.close()
        if u: session["uid"]=u["id"]; return redirect(url_for("dashboard"))
        flash("Invalid credentials.","danger")
    return render_template_string("""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>""" + CSS + """</style></head><body class="login"><form class="loginbox card" method="post"><div class="brand"><div class="logo">AI</div><div><b>AttendAI</b><small>University Attendance System</small></div></div><h2>Sign in</h2><p class="muted">Role is loaded automatically from your account.</p><input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Password" required><button>Sign in</button><p class="small muted">Demo: admin/admin123 · teacher/teacher123 · student/student123</p></form></body></html>""")

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
@need()
def dashboard():
    u=me(); c=db()
    if u["role"]=="STUDENT":
        st=c.execute("select * from students where id=?",(u["student_id"],)).fetchone()
        rows=c.execute("""select s.name,s.code,count(l.id) total,
        (select count(*) from attendance a where a.student_id=? and a.subject_id=s.id) present
        from subjects s left join lectures l on l.subject_id=s.id and l.course=? and l.section=? group by s.id""",(st["id"],st["course"],st["section"])).fetchall()
        total=sum(r["total"] for r in rows); present=sum(r["present"] for r in rows); overall=(present/total*100 if total else 0)
        cards="".join(f'<div class="card stat"><span>{r["code"]}</span><b>{(r["present"]/r["total"]*100 if r["total"] else 0):.0f}%</b><small>{r["name"]}</small></div>' for r in rows)
        c.close()
        body=f'<div class="hero"><div><span class="pill">STUDENT PORTAL</span><h2>{st["name"]}</h2><p class="muted">{st["enrollment_no"]} · {st["course"]} · Semester {st["semester"]} · Section {st["section"]}</p></div><div class="ring">{overall:.0f}%<div class="small muted">overall</div></div></div><div class="grid">{cards}</div><a class="btn primary" href="/student/attendance">View attendance history →</a>'
        return page("My Attendance",body)
    if u["role"]=="TEACHER":
        t=c.execute("select * from teachers where id=?",(u["teacher_id"],)).fetchone()
        ls=c.execute("select l.*,s.code,s.name subject_name from lectures l join subjects s on s.id=l.subject_id where l.teacher_id=? order by l.id desc limit 30",(u["teacher_id"],)).fetchall(); c.close()
        rows="".join(f'<tr><td>{l["lecture_date"]}</td><td>{l["lecture_no"]}</td><td><b>{l["subject_name"]}</b><small>{l["code"]}</small></td><td>{l["room"]}</td><td>{l["section"]}</td></tr>' for l in ls) or '<tr><td colspan="5">No assigned lectures.</td></tr>'
        return page("Teacher Dashboard",f'<div class="hero"><div><span class="pill">TEACHER WORKSPACE</span><h2>Hello, {t["name"]}</h2><p class="muted">Mark attendance only for lectures assigned to your account.</p></div><a class="btn primary" href="/attendance">Open register →</a></div><div class="card"><div class="head"><h3>Assigned lectures</h3></div><div class="table"><table><tr><th>Date</th><th>Slot</th><th>Subject</th><th>Room</th><th>Section</th></tr>{rows}</table></div></div>')
    stats=[("Students",c.execute("select count(*) from students").fetchone()[0]),("Teachers",c.execute("select count(*) from teachers").fetchone()[0]),("Cameras",c.execute("select count(*) from cameras").fetchone()[0]),("Attendance",c.execute("select count(*) from attendance").fetchone()[0])]; c.close()
    cards="".join(f'<div class="card stat"><span>{n}</span><b>{v}</b></div>' for n,v in stats)
    return page("Admin Dashboard",f'<div class="hero"><div><span class="pill">ADMIN CONTROL CENTER</span><h2>University Attendance</h2><p class="muted">Manage students, cameras, PDF data and attendance overrides.</p></div><a class="btn primary" href="/import">Import PDF →</a></div><div class="grid">{cards}</div>')

@app.route("/attendance",methods=["GET","POST"])
@need("ADMIN","TEACHER")
def attendance():
    c=db(); u=me()
    if request.method=="POST":
        lecture_id=int(request.form["lecture_id"]); students=request.form.getlist("student_id")
        lec=c.execute("select * from lectures where id=?",(lecture_id,)).fetchone()
        if u["role"]=="TEACHER" and (not lec or lec["teacher_id"]!=u["teacher_id"]): c.close(); flash("This lecture is not assigned to you.","danger"); return redirect(url_for("attendance"))
        for sid in students:
            c.execute("insert or ignore into attendance(student_id,subject_id,lecture_id,attendance_date,source,marked_by) values(?,?,?,?,?,?)",(sid,lec["subject_id"],lecture_id,lec["lecture_date"],"TEACHER_OVERRIDE" if u["role"]=="TEACHER" else "ADMIN_OVERRIDE",u["id"]))
        c.commit(); flash("Attendance saved.","success")
    if u["role"]=="TEACHER": lectures=c.execute("select l.*,s.code,s.name subject_name from lectures l join subjects s on s.id=l.subject_id where l.teacher_id=? order by l.lecture_date desc,l.lecture_no",(u["teacher_id"],)).fetchall()
    else: lectures=c.execute("select l.*,s.code,s.name subject_name from lectures l join subjects s on s.id=l.subject_id order by l.lecture_date desc,l.lecture_no").fetchall()
    students=c.execute("select * from students where 1=1 order by name").fetchall(); c.close()
    opts="".join(f'<option value="{l["id"]}">{l["lecture_date"]} · Slot {l["lecture_no"]} · {l["subject_name"]} · Room {l["room"]}</option>' for l in lectures)
    checks="".join(f'<label><input type="checkbox" name="student_id" value="{s["id"]}"> {s["name"]} <span class="muted">({s["enrollment_no"]})</span></label><br>' for s in students)
    return page("Attendance Register",f'<div class="card"><div class="head"><h3>Select lecture</h3></div><form class="form" method="post"><label class="wide">Lecture<select name="lecture_id" required>{opts}</select></label><div class="wide">{checks}</div><div><button class="btn green">Save Present Marks</button></div></form></div>')

@app.route("/student/attendance")
@need("STUDENT")
def student_history():
    c=db(); rows=c.execute("select a.attendance_date,a.source,s.code,s.name from attendance a join subjects s on s.id=a.subject_id where a.student_id=? order by a.id desc",(me()["student_id"],)).fetchall(); c.close()
    trs="".join(f'<tr><td>{r["attendance_date"]}</td><td>{r["code"]}</td><td>{r["name"]}</td><td>{r["source"]}</td></tr>' for r in rows) or '<tr><td colspan="4">No attendance records.</td></tr>'
    return page("Attendance History",f'<div class="card"><div class="table"><table><tr><th>Date</th><th>Code</th><th>Subject</th><th>Source</th></tr>{trs}</table></div></div>')

@app.route("/students")
@need("ADMIN")
def students():
    c=db(); rows=c.execute("select * from students order by name").fetchall(); c.close()
    trs="".join(f'<tr><td><b>{s["name"]}</b></td><td>{s["enrollment_no"]}</td><td>{s["course"]}</td><td>{s["semester"]}</td><td>{s["section"]}</td></tr>' for s in rows)
    return page("Student Directory",f'<div class="hero"><div><span class="pill">UNIVERSITY DIRECTORY</span><h2>{len(rows)} active students</h2></div></div><div class="card"><div class="table"><table><tr><th>Name</th><th>Enrollment</th><th>Course</th><th>Semester</th><th>Section</th></tr>{trs}</table></div></div>')

@app.route("/cameras",methods=["GET","POST"])
@need("ADMIN")
def cameras():
    c=db()
    if request.method=="POST":
        c.execute("insert into cameras(camera_name,location,stream_url,authorized) values(?,?,?,1)",(request.form["name"],request.form["location"],request.form.get("url",""))); c.commit(); flash("Camera added.","success")
    rows=c.execute("select * from cameras order by id desc").fetchall(); c.close()
    cards="".join(f'<div class="card stat"><span>AUTHORIZED CAMERA</span><b>{x["camera_name"]}</b><small>{x["location"]} · {x["stream_url"] or "No browser stream configured"}</small></div>' for x in rows)
    return page("Camera Management",f'<div class="card"><div class="head"><h3>Add university camera</h3></div><form class="form" method="post"><label>Name<input name="name" required></label><label>Location<input name="location" required></label><label>Stream URL<input name="url" placeholder="WebRTC/HLS URL"></label><div><button class="btn primary">Authorize Camera</button></div></form></div><div class="grid">{cards}</div>')

@app.route("/import",methods=["GET","POST"])
@need("ADMIN")
def import_pdf():
    result=""
    if request.method=="POST" and "pdf" in request.files:
        f=request.files["pdf"]
        if f.filename.lower().endswith(".pdf"):
            path=os.path.join(UPLOADS,f.filename.replace("/","_").replace("\\","_")); f.save(path)
            try:
                from pypdf import PdfReader
                text="\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
                kind="TIMETABLE" if "time table" in text.lower() or "class time table" in text.lower() else "STUDENT LIST" if "student list" in text.lower() else "GENERIC PDF"
                result=f"<b>{kind}</b> detected · {len(text)} extracted characters. The original PDF is stored for the next import/parser stage."
            except Exception as e: result=f"PDF saved, but extraction failed: {e}"
        else: result="Please upload a PDF file."
    return page("PDF Import",f'<div class="hero"><div><span class="pill">AUTOMATIC DOCUMENT INGESTION</span><h2>Upload university PDF</h2><p class="muted">Timetable and student-list PDFs can be analyzed here.</p></div></div><div class="card"><form class="form" method="post" enctype="multipart/form-data"><label class="wide">PDF file<input type="file" name="pdf" accept=".pdf" required></label><div><button class="btn primary">Analyze PDF</button></div></form></div>{("<div class=card><div class=head><h3>Result</h3></div><div style=padding:20px>"+result+"</div></div>") if result else ""}')

if __name__=="__main__":
    init()
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
else:
    init()

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
    u=me()
    c=db(); c.execute("insert into audit_logs(user_id,action,entity,entity_id,detail) values(?,?,?,?,?)",(u["id"] if u else None,action,entity,entity_id,detail)); c.commit(); c.close()

@app.route("/lectures",methods=["GET","POST"])
@need("ADMIN","TEACHER")
def lecture_manager():
    u=me(); c=db()
    if request.method=="POST":
        sid=int(request.form["subject_id"]); slot=int(request.form["lecture_no"])
        teacher_id=u["teacher_id"] if u["role"]=="TEACHER" else (int(request.form.get("teacher_id")) if request.form.get("teacher_id") else None)
        times=[("09:30","10:15"),("10:20","11:05"),("11:10","11:55"),("12:00","12:45"),("12:50","13:35"),("13:40","14:25"),("14:30","15:15"),("15:20","16:05"),("16:10","16:55")]
        st,en=times[slot-1]
        c.execute("insert into lectures(subject_id,teacher_id,lecture_no,course,section,room,lecture_date) values(?,?,?,?,?,?,?)",(sid,teacher_id,slot,request.form.get("course","BCA"),request.form.get("section","G"),request.form.get("room","222"),request.form["lecture_date"]))
        audit("CREATE_LECTURE","lecture",c.execute("select last_insert_rowid()").fetchone()[0],"manual lecture")
        c.commit(); flash("Lecture created.","success")
    subjects=c.execute("select * from subjects order by code").fetchall()
    teachers=c.execute("select * from teachers order by name").fetchall()
    lectures=c.execute("select l.*,s.code,s.name subject_name from lectures l join subjects s on s.id=l.subject_id order by l.lecture_date desc,l.lecture_no limit 100").fetchall()
    c.close()
    opts="".join(f'<option value="{s["id"]}">{s["code"]} - {s["name"]}</option>' for s in subjects)
    tops="".join(f'<option value="{t["id"]}">{t["name"]}</option>' for t in teachers)
    slots="".join(f'<option value="{i}">Slot {i} ({a}-{b})</option>' for i,(a,b) in enumerate([("09:30","10:15"),("10:20","11:05"),("11:10","11:55"),("12:00","12:45"),("12:50","13:35"),("13:40","14:25"),("14:30","15:15"),("15:20","16:05"),("16:10","16:55")],1))
    rows="".join(f'<tr><td>{x["lecture_date"]}</td><td>{x["lecture_no"]}</td><td>{x["code"]}</td><td>{x["room"]}</td><td>{x["section"]}</td></tr>' for x in lectures)
    teacher_field=f'<label>Teacher<select name="teacher_id">{tops}</select></label>' if u["role"]=="ADMIN" else ""
    body=f'<div class="card"><div class="head"><h3>Add lecture manually</h3></div><form class="form" method="post"><label>Subject<select name="subject_id">{opts}</select></label><label>Date<input type="date" name="lecture_date" value="{datetime.now().date()}" required></label><label>Slot<select name="lecture_no">{slots}</select></label><label>Course<input name="course" value="BCA"></label><label>Section<input name="section" value="G"></label><label>Room<input name="room" value="222"></label>{teacher_field}<div><button class="btn primary">Create Lecture</button></div></form></div><div class="card"><div class="head"><h3>Lecture schedule</h3></div><div class="table"><table><tr><th>Date</th><th>Slot</th><th>Subject</th><th>Room</th><th>Section</th></tr>{rows}</table></div></div>'
    return page("Lecture Management",body)

@app.route("/reports")
@need("ADMIN")
def reports():
    c=db()
    students=c.execute("select * from students order by name").fetchall()
    rows=[]
    for s in students:
        total=c.execute("select count(*) from lectures where course=? and section=?",(s["course"],s["section"])).fetchone()[0]
        present=c.execute("select count(*) from attendance where student_id=?",(s["id"],)).fetchone()[0]
        pct=(present/total*100) if total else 0
        rows.append(f'<tr><td>{s["name"]}</td><td>{s["enrollment_no"]}</td><td>{s["course"]}</td><td>{s["section"]}</td><td>{pct:.1f}%</td><td>{present}/{total}</td></tr>')
    c.close()
    return page("Attendance Reports",'<div class="hero"><div><span class="pill">REPORTING</span><h2>Overall attendance</h2><p class="muted">Export the current register as CSV.</p></div><a class="btn primary" href="/reports.csv">Export CSV</a></div><div class="card"><div class="table"><table><tr><th>Student</th><th>Enrollment</th><th>Course</th><th>Section</th><th>Attendance</th><th>Present/Total</th></tr>'+''.join(rows)+'</table></div></div>')

@app.route("/reports.csv")
@need("ADMIN")
def reports_csv():
    c=db(); out=io.StringIO(); w=csv.writer(out); w.writerow(["Student","Enrollment","Course","Section","Attendance Percent","Present","Total"])
    for s in c.execute("select * from students order by name").fetchall():
        total=c.execute("select count(*) from lectures where course=? and section=?",(s["course"],s["section"])).fetchone()[0]
        present=c.execute("select count(*) from attendance where student_id=?",(s["id"],)).fetchone()[0]
        w.writerow([s["name"],s["enrollment_no"],s["course"],s["section"],f"{(present/total*100 if total else 0):.1f}",present,total])
    c.close(); data=io.BytesIO(out.getvalue().encode()); data.seek(0)
    return send_file(data,mimetype="text/csv",as_attachment=True,download_name="attendance_report.csv")

@app.route("/audit")
@need("ADMIN")
def audit_logs():
    c=db(); logs=c.execute("select a.*,u.display_name from audit_logs a left join users u on u.id=a.user_id order by a.id desc limit 200").fetchall(); c.close()
    rows="".join(f'<tr><td>{x["created_at"]}</td><td>{x["display_name"] or "System"}</td><td>{x["action"]}</td><td>{x["entity"]}</td><td>{x["detail"]}</td></tr>' for x in logs)
    return page("Audit Logs",f'<div class="card"><div class="table"><table><tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Details</th></tr>{rows}</table></div></div>')

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
        if lec and not c.execute("select id from attendance where student_id=? and lecture_id=?",(sid,lid)).fetchone():
            c.execute("insert into attendance(student_id,subject_id,lecture_id,attendance_date,source,confidence,note) values(?,?,?,?,?,?,?)",(sid,lec["subject_id"],lid,lec["lecture_date"],"AI_RECOGNITION",confidence,"Recognition API"))
    c.commit(); c.close(); return {"ok":True,"result":result,"confidence":confidence}

upgrade_schema()
