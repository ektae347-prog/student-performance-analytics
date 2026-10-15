"""Static preview of the dashboard (used in README). The interactive version is built in Power BI."""
import sqlite3, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "student_analytics.db")
s = pd.read_sql("SELECT * FROM vw_student_summary", con)
ss = pd.read_sql("SELECT * FROM vw_student_subject", con)
plan = pd.read_sql("SELECT * FROM vw_intervention_plan", con)

NAVY, TEAL, RED, GOLD, GREY = "#1F3A5F", "#2A9D8F", "#C0392B", "#E9C46A", "#F4F6F7"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
fig = plt.figure(figsize=(16, 10), facecolor="white")
fig.suptitle("Student Performance Analytics  |  Academic Year 2025-26", fontsize=20, fontweight="bold",
             color=NAVY, x=0.04, ha="left", y=0.975)

# KPI cards
kpis = [("Students", f"{len(s)}"), ("Avg Score", f"{s.overall_pct.mean():.1f}%"),
        ("Avg Attendance", f"{s.attendance_pct.mean():.1f}%"), ("Avg Assignments", f"{s.assignment_pct.mean():.1f}%"),
        ("High-Risk Students", f"{(s.risk_level=='High').sum()}"),
        ("Need Support (<45%)", f"{(s.overall_pct<45).sum()}")]
for i, (lab, val) in enumerate(kpis):
    ax = fig.add_axes([0.04 + i * 0.1575, 0.835, 0.145, 0.095]); ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, color=GREY, transform=ax.transAxes))
    ax.add_patch(plt.Rectangle((0, 0), 0.025, 1, color=TEAL if i < 4 else RED, transform=ax.transAxes))
    ax.text(0.12, 0.62, val, fontsize=22, fontweight="bold", color=NAVY, va="center")
    ax.text(0.12, 0.18, lab, fontsize=10, color="#555")

def style(ax, t):
    ax.set_title(t, loc="left", fontsize=12, fontweight="bold", color=NAVY, pad=10)
    ax.tick_params(labelsize=9)

# 1 subject avg + fail rate
a = fig.add_axes([0.05, 0.50, 0.28, 0.27])
g = ss.groupby("subject_name").agg(avg=("score_pct", "mean"), fail=("score_pct", lambda x: (x < 40).mean() * 100)).sort_values("avg")
cols = [RED if f >= 10 else NAVY for f in g.fail]
a.barh(g.index, g.avg, color=cols)
for y, (v, f) in enumerate(zip(g.avg, g.fail)): a.text(v + 0.8, y, f"{v:.1f}%  (fail {f:.0f}%)", va="center", fontsize=9)
a.set_xlim(0, 85); style(a, "Subjects needing support (red = fail rate >= 10%)")

# 2 attendance band
a = fig.add_axes([0.40, 0.50, 0.26, 0.27])
g = s.groupby("attendance_band").overall_pct.mean()
b = a.bar([x[3:] for x in g.index], g.values, color=TEAL)
a.bar_label(b, fmt="%.1f", fontsize=9); a.set_ylim(0, 80); style(a, "Avg score by attendance band")

# 3 assignment band
a = fig.add_axes([0.72, 0.50, 0.26, 0.27])
g = s.groupby("assignment_band").overall_pct.mean()
b = a.bar([x[3:] for x in g.index], g.values, color=TEAL)
a.bar_label(b, fmt="%.1f", fontsize=9); a.set_ylim(0, 90); style(a, "Avg score by assignment completion")

# 4 scatter attendance vs score
a = fig.add_axes([0.05, 0.08, 0.28, 0.30])
col = s.risk_level.map({"High": RED, "Medium": GOLD, "Low": TEAL})
a.scatter(s.attendance_pct, s.overall_pct, c=col, s=14, alpha=.65)
m, c = np.polyfit(s.attendance_pct, s.overall_pct, 1); xs = np.linspace(s.attendance_pct.min(), 100, 50)
a.plot(xs, m * xs + c, color="black", lw=1)
a.set_xlabel("Attendance %", fontsize=9); a.set_ylabel("Overall score %", fontsize=9)
style(a, f"Attendance vs score (r = {s.attendance_pct.corr(s.overall_pct):.2f})")

# 5 correlation
a = fig.add_axes([0.40, 0.08, 0.25, 0.30])
cr = s[["assignment_pct", "on_time_pct", "attendance_pct", "study_hours_week"]].corrwith(s.overall_pct).sort_values()
lab = {"assignment_pct": "Assignment %", "on_time_pct": "On-time %", "attendance_pct": "Attendance %", "study_hours_week": "Study hrs"}
b = a.barh([lab[i] for i in cr.index], cr.values, color=GOLD); a.bar_label(b, fmt="%.2f", fontsize=9, padding=3)
a.set_xlim(0, 1.2); style(a, "Correlation with overall score")

# 6 intervention
a = fig.add_axes([0.83, 0.08, 0.15, 0.30])
iv = plan.recommended_intervention.str.replace(r"^Priority \d: ", "", regex=True).str.replace(" + ", " +\n", regex=False)
iv = plan.assign(iv=iv).groupby("iv").size().sort_values()
b = a.barh(iv.index, iv.values, color=NAVY); a.bar_label(b, fontsize=9, padding=3)
a.tick_params(axis="y", labelsize=8)
a.tick_params(labelsize=9); a.set_title("Students per recommended intervention", x=-1.25, ha="left", fontsize=12, fontweight="bold", color=NAVY, pad=10)

fig.savefig(ROOT / "images" / "dashboard_preview.png", dpi=110, bbox_inches="tight")
print("saved")
