"""Load raw CSVs into SQLite, run the SQL pipeline, export Power BI-ready CSVs."""
import sqlite3, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "student_analytics.db"
DB.unlink(missing_ok=True)
con = sqlite3.connect(DB)

def run(name):
    con.executescript((ROOT / "sql" / name).read_text())

run("01_schema.sql")
for t in ["subjects", "students", "attendance", "assignments", "marks"]:
    pd.read_csv(ROOT / "data" / "raw" / f"{t}.csv").to_sql(f"raw_{t}", con, if_exists="append", index=False)
run("02_data_cleaning.sql")
run("03_views.sql")

out = ROOT / "data" / "processed"
out.mkdir(exist_ok=True)
for name in ["vw_student_summary", "vw_student_subject", "vw_intervention_plan"]:
    pd.read_sql(f"SELECT * FROM {name}", con).to_csv(out / f"{name[3:]}.csv", index=False)
pd.read_sql("SELECT * FROM dim_subject", con).to_csv(out / "dim_subject.csv", index=False)
pd.read_sql("SELECT * FROM fact_attendance", con).to_csv(out / "fact_attendance.csv", index=False)
pd.read_sql("SELECT * FROM fact_marks", con).to_csv(out / "fact_marks.csv", index=False)
print("Built", DB.name)
con.close()
