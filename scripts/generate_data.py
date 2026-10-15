"""
Generate a realistic SYNTHETIC student performance dataset.

Why synthetic?  Real student records are private. The data below is simulated
with documented relationships (attendance, study habits, assignment completion
and subject difficulty all influence marks) so the analysis workflow is
realistic and fully reproducible.  Seed is fixed -> same data every run.

Run:  python scripts/generate_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

N = 600
# ---------------------------------------------------------------- subjects
subjects = pd.DataFrame({
    "subject_id": [1, 2, 3, 4, 5, 6],
    "subject_name": ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Computer Science"],
    "difficulty_offset": [-7, -6, -3, 0, 3, 4],     # baseline score shift (hidden driver)
    "attendance_sensitivity": [0.45, 0.40, 0.30, 0.25, 0.20, 0.25],
})

# ---------------------------------------------------------------- students
grade = rng.choice([9, 10, 11, 12], N)
section = rng.choice(list("ABCD"), N)
gender = rng.choice(["Female", "Male"], N, p=[0.49, 0.51])
parent_edu = rng.choice(
    ["Below High School", "High School", "Graduate", "Postgraduate"], N, p=[0.12, 0.33, 0.38, 0.17])
edu_score = pd.Series(parent_edu).map(
    {"Below High School": -1, "High School": 0, "Graduate": 0.5, "Postgraduate": 1.0}).values
ability = rng.normal(0, 1, N)
study_hours = np.clip(rng.normal(10 + 1.5 * ability + 0.8 * edu_score, 3.5), 1, 25).round(1)
internet = rng.choice(["Yes", "No"], N, p=[0.82, 0.18])
extracurricular = rng.choice(["Yes", "No"], N, p=[0.45, 0.55])
tutoring = rng.choice(["Yes", "No"], N, p=[0.25, 0.75])
base_att = np.clip(rng.normal(0.865 + 0.025 * ability + 0.01 * edu_score, 0.075), 0.45, 0.995)

students = pd.DataFrame({
    "student_id": [f"S{str(i).zfill(4)}" for i in range(1, N + 1)],
    "gender": gender, "grade": grade, "section": section,
    "parental_education": parent_edu, "study_hours_week": study_hours,
    "internet_access": internet, "extracurricular": extracurricular, "tutoring": tutoring,
})

# ---------------------------------------------------------------- attendance (monthly)
months = ["2025-08", "2025-09", "2025-10", "2025-11", "2025-12", "2026-01"]
working_days = {"2025-08": 24, "2025-09": 22, "2025-10": 20, "2025-11": 22, "2025-12": 21, "2026-01": 22}
rows = []
for i, sid in enumerate(students.student_id):
    for m in months:
        wd = working_days[m]
        p = np.clip(base_att[i] + rng.normal(0, 0.04), 0.3, 1)
        rows.append((sid, m, wd, int(rng.binomial(wd, p))))
attendance = pd.DataFrame(rows, columns=["student_id", "month", "working_days", "days_present"])
g = attendance.groupby("student_id")
att_rate = g.days_present.sum() / g.working_days.sum() * 100

# ---------------------------------------------------------------- assignments
rows = []
for i, sid in enumerate(students.student_id):
    for _, s in subjects.iterrows():
        total = int(rng.integers(16, 25))
        p = np.clip(0.80 + 0.07 * ability[i] + 0.004 * (study_hours[i] - 10)
                    + 0.05 * (att_rate[sid] - 85) / 10 + rng.normal(0, 0.07), 0.15, 1)
        submitted = int(rng.binomial(total, p))
        on_time = int(rng.binomial(submitted, np.clip(0.8 + 0.05 * ability[i], 0.4, 0.98))) if submitted else 0
        rows.append((sid, int(s.subject_id), total, submitted, on_time))
assignments = pd.DataFrame(rows, columns=["student_id", "subject_id", "assignments_total",
                                          "assignments_submitted", "assignments_on_time"])
assignments["rate"] = assignments.assignments_submitted / assignments.assignments_total * 100
asg_lookup = assignments.set_index(["student_id", "subject_id"])["rate"]
assignments = assignments.drop(columns="rate")

# ---------------------------------------------------------------- marks
exams = [("Unit Test", 25, -1.5), ("Midterm", 50, 0.0), ("Final", 100, 1.0)]
rows = []
for i, sid in enumerate(students.student_id):
    for _, s in subjects.iterrows():
        subj_aptitude = rng.normal(0, 4)          # student-specific strength per subject
        for ename, mx, drift in exams:
            pct = (60 + 9.5 * ability[i] + s.difficulty_offset + subj_aptitude + drift
                   + s.attendance_sensitivity * (att_rate[sid] - 85)
                   + 0.12 * (asg_lookup[(sid, int(s.subject_id))] - 80)
                   + 0.55 * (study_hours[i] - 10)
                   + (2.0 if tutoring[i] == "Yes" else 0)
                   + rng.normal(0, 6))
            rows.append((sid, int(s.subject_id), ename, mx, int(np.clip(round(pct / 100 * mx), 0, mx))))
marks = pd.DataFrame(rows, columns=["student_id", "subject_id", "exam_type", "max_marks", "marks_obtained"])

# ---------------------------------------------------------------- realistic imperfections
# (so the SQL cleaning step has something real to do)
students.loc[rng.choice(N, 18, replace=False), "study_hours_week"] = np.nan
students.loc[rng.choice(N, 12, replace=False), "parental_education"] = None
low = rng.choice(N, 15, replace=False)
students.loc[low, "gender"] = students.loc[low, "gender"].str.lower()
marks = pd.concat([marks, marks.sample(25, random_state=1)], ignore_index=True)   # duplicate rows

subjects[["subject_id", "subject_name"]].to_csv(OUT / "subjects.csv", index=False)
students.to_csv(OUT / "students.csv", index=False)
attendance.to_csv(OUT / "attendance.csv", index=False)
assignments.to_csv(OUT / "assignments.csv", index=False)
marks.to_csv(OUT / "marks.csv", index=False)
print({k: len(v) for k, v in dict(students=students, attendance=attendance,
                                   assignments=assignments, marks=marks).items()})
