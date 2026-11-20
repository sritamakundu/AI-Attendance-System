import sqlite3, json, os
from datetime import datetime
import numpy as np
from io import BytesIO
import pandas as pd
DB_PATH=os.getenv("ATTENDANCE_DB","attendance.db")

def conn():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c

def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS students(
          student_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          roll_no TEXT UNIQUE NOT NULL, class_section TEXT, embedding TEXT NOT NULL,
          created_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS attendance(
          id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
          attendance_date TEXT NOT NULL, timestamp TEXT NOT NULL, note TEXT,
          UNIQUE(student_id,attendance_date),
          FOREIGN KEY(student_id) REFERENCES students(student_id))""")

def list_students():
    with conn() as c: return [dict(r) for r in c.execute("SELECT student_id,name,roll_no,class_section,created_at FROM students ORDER BY roll_no")]

def get_embeddings():
    with conn() as c: rows=c.execute("SELECT student_id,name,roll_no,embedding FROM students").fetchall()
    return [{"student_id":r["student_id"],"name":r["name"],"roll_no":r["roll_no"],"embedding":np.array(json.loads(r["embedding"]),dtype=np.float32)} for r in rows]

def add_student(name,roll,class_section,embedding):
    with conn() as c:
        c.execute("INSERT INTO students(name,roll_no,class_section,embedding,created_at) VALUES(?,?,?,?,?)",
                  (name,roll,class_section,json.dumps(np.asarray(embedding).tolist()),datetime.now().isoformat(timespec="seconds")))

def delete_student(sid):
    with conn() as c:
        c.execute("DELETE FROM attendance WHERE student_id=?",(sid,))
        c.execute("DELETE FROM students WHERE student_id=?",(sid,))

def mark_attendance(sid,day,note="Teacher-confirmed"):
    try:
        with conn() as c:
            c.execute("INSERT INTO attendance(student_id,attendance_date,timestamp,note) VALUES(?,?,?,?)",
                      (int(sid),day,datetime.now().isoformat(timespec="seconds"),note))
        return True,"Attendance recorded."
    except sqlite3.IntegrityError: return False,"Already marked present for this date."

def attendance_for_date(day):
    with conn() as c:
        return [dict(r) for r in c.execute("""SELECT s.roll_no AS 'Roll No',s.name AS Name,
        s.class_section AS Class,a.attendance_date AS Date,a.timestamp AS Time,a.note AS Note
        FROM attendance a JOIN students s ON s.student_id=a.student_id
        WHERE a.attendance_date=? ORDER BY s.roll_no""",(day,))]

def attendance_summary():
    with conn() as c:
        return [dict(r) for r in c.execute("""SELECT s.roll_no AS 'Roll No',s.name AS Name,
          COUNT(a.id) AS 'Days Present' FROM students s LEFT JOIN attendance a
          ON s.student_id=a.student_id GROUP BY s.student_id ORDER BY s.roll_no""")]

def export_attendance(day):
    df=pd.DataFrame(attendance_for_date(day))
    buf=BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as writer: df.to_excel(writer,index=False,sheet_name="Attendance")
    return buf.getvalue()
