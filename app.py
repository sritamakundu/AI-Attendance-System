import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np
from io import BytesIO
from datetime import date
from db import init_db, list_students, add_student, delete_student, mark_attendance, attendance_for_date, attendance_summary, export_attendance
from recognition import enroll_image, recognize_faces

st.set_page_config(page_title="AI Attendance", page_icon="🎓", layout="wide")
init_db()
st.title("🎓 AI Attendance System")
st.caption("Classroom attendance • Face recognition demo • Automatic demo marking")
st.warning("DEMO MODE: Use only consented test/student images with school approval. Face matches can be wrong; validate results and protect biometric data.")

tab1,tab2,tab3,tab4=st.tabs(["📊 Dashboard","📷 Recognition","👥 Students","📄 Reports"])

with tab1:
    today=date.today().isoformat()
    students=list_students()
    records=attendance_for_date(today)
    total=len(students); present=len(records)
    c1,c2,c3=st.columns(3)
    c1.metric("Registered students",total)
    c2.metric("Present today",present)
    c3.metric("Not marked present",max(total-present,0))
    st.subheader("Today's attendance")
    if records:
        st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True)
    else: st.info("No attendance has been recorded today.")

with tab2:
    st.subheader("Capture and recognize")
    st.write("Capture a frame using your browser camera. Confident roster matches are automatically recorded for today in demo mode.")
    photo=st.camera_input("Take a classroom/student photo")
    if photo:
        img=Image.open(photo).convert("RGB")
        st.image(img,caption="Captured image",width=500)
        if st.button("Analyze image",type="primary"):
            with st.spinner("Detecting faces and comparing embeddings…"):
                try:
                    results=recognize_faces(np.array(img))
                    st.session_state["recognition_results"]=results
                    st.session_state["recognition_date"]=date.today().isoformat()
                    auto_messages=[]
                    today=date.today().isoformat()
                    for r in results:
                        if r.get("student_id"):
                            ok,msg=mark_attendance(str(r["student_id"]),today,"Automatically marked from face-recognition demo")
                            auto_messages.append((r.get("name","Student"),ok,msg))
                    st.session_state["auto_attendance_messages"]=auto_messages
                except Exception as e:
                    st.error(f"Recognition failed: {e}")
    results=st.session_state.get("recognition_results",[])
    if results:
        st.markdown("### Recognition results")
        for i,r in enumerate(results):
            if r.get("student_id"):
                st.success(f"Face {i+1}: {r.get('name','Student')} matched • cosine distance: {r.get('score','—')}")
            else:
                st.warning(f"Face {i+1}: Unknown / no confident match • score: {r.get('score','—')}")
        for name,ok,msg in st.session_state.get("auto_attendance_messages",[]):
            (st.success if ok else st.info)(f"{name}: {msg}")
    st.caption("Demo safeguard: only matches under the recognition threshold are auto-marked; one student can be marked once per day. Use clear, consented test images and verify accuracy before any real use.")

with tab3:
    st.subheader("Student roster")
    with st.expander("Register student (consented image)"):
        name=st.text_input("Full name")
        roll=st.text_input("Roll number / student ID")
        cls=st.text_input("Class / section",value="XII")
        photo_reg=st.file_uploader("Upload a clear face photo",type=["jpg","jpeg","png"])
        if st.button("Register student",type="primary"):
            if not (name.strip() and roll.strip() and photo_reg):
                st.error("Enter name, ID, and upload a photo.")
            else:
                try:
                    emb=enroll_image(Image.open(photo_reg).convert("RGB"))
                    add_student(name.strip(),roll.strip(),cls.strip(),emb)
                    st.success("Student registered and embedding saved.")
                    st.rerun()
                except Exception as e: st.error(f"Could not enroll image: {e}")
    roster=list_students()
    if roster:
        df=pd.DataFrame([{k:s[k] for k in ["student_id","name","roll_no","class_section","created_at"]} for s in roster])
        st.dataframe(df,use_container_width=True,hide_index=True)
        selected=st.selectbox("Remove student (demo/admin action)",["—"]+[f'{s["student_id"]} • {s["name"]}' for s in roster])
        if selected!="—" and st.button("Delete selected student"):
            delete_student(selected.split(" • ")[0]); st.success("Student removed."); st.rerun()
    else: st.info("No students registered yet. Add consented test records above.")

with tab4:
    st.subheader("Attendance reports")
    report_date=st.date_input("Choose date",value=date.today())
    data=attendance_for_date(report_date.isoformat())
    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True) if data else st.info("No records for this date.")
    if st.button("Export selected date to Excel"):
        out=export_attendance(report_date.isoformat())
        st.download_button("Download Excel",data=out,file_name=f"attendance_{report_date.isoformat()}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown("### Attendance summary")
    summary=attendance_summary()
    if summary: st.dataframe(pd.DataFrame(summary),use_container_width=True,hide_index=True)
