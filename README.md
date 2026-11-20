# AI Attendance System (Python)

## Features
- Streamlit dashboard
- Webcam snapshot capture (browser camera)
- DeepFace ArcFace embeddings and cosine similarity matching
- SQLite student roster and attendance
- Teacher confirmation before attendance is committed
- Duplicate prevention (one record/student/day)
- Excel export and attendance summary

## Setup (Windows)
Use Python 3.10 or 3.11 (recommended).

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```
If PowerShell blocks activation, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Run
The browser opens a local dashboard. Go to **Students**, register a test student with a clear, consented face photo and unique roll number. Then use **Recognition** to take a camera photo, analyze it, review the suggested match, and check the confirmation box before marking attendance.

## Database
`attendance.db` is created on first run. It contains names, IDs, face embeddings (biometric data), and attendance records. Keep it private; do not commit or upload it. Add `attendance.db` to `.gitignore`.

## Recognition notes
- Enrollment image must contain exactly one face.
- Recognition works best with good lighting, frontal faces, and a similar camera distance.
- `threshold=0.68` is an initial cosine-distance threshold, not a guaranteed accuracy value. Validate/tune using a consented local test set; always review matches.
- This is a classroom demonstration/prototype, not a validated production attendance system. Do not use it to make consequential attendance decisions without institutional approval, privacy safeguards, testing, and a non-biometric alternative.
- Browser camera permissions are required. `st.camera_input` captures a still image, not a continuous video stream.
