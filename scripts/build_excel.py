"""Build the Excel workbook: live formulas, editable thresholds, native charts."""
import pandas as pd
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
stu = pd.read_csv(P / "student_summary.csv").drop(columns=["risk_flags", "risk_level"])
sub = pd.read_csv(P / "student_subject.csv")
plan = pd.read_csv(P / "intervention_plan.csv")
plan["_o"] = plan.risk_level.map({"High": 0, "Medium": 1})
plan = plan.sort_values(["_o", "overall_pct"]).drop(columns="_o")
NS, NB = len(stu), len(sub)

F = "Arial"
NAVY, TEAL, LIGHT, GREY = "1F3A5F", "2A9D8F", "EAF2F8", "F4F6F7"
hdr_font = Font(name=F, bold=True, color="FFFFFF", size=10)
hdr_fill = PatternFill("solid", fgColor=NAVY)
base = Font(name=F, size=10)
bold = Font(name=F, size=10, bold=True)
blue = Font(name=F, size=10, color="0000FF", bold=True)
title = Font(name=F, size=16, bold=True, color=NAVY)
thin = Side(style="thin", color="D0D7DE")
box = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()

def header(ws, row, cols, start=1):
    for i, c in enumerate(cols):
        cell = ws.cell(row=row, column=start + i, value=c)
        cell.font, cell.fill = hdr_font, hdr_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def dump(ws, df, widths=None):
    header(ws, 1, df.columns)
    for r, row in enumerate(df.itertuples(index=False), start=2):
        for c, v in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=(None if pd.isna(v) else v))
            cell.font = base
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    for i, col in enumerate(df.columns, start=1):
        ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(col, max(12, len(col) + 3))

# ------------------------------------------------------------------ Assumptions
wa = wb.active; wa.title = "Assumptions"
wa["A1"] = "Assumptions & Thresholds"; wa["A1"].font = title
wa["A2"] = "Blue cells are inputs - change them and every sheet recalculates. Defaults match sql/03_views.sql."
wa["A2"].font = Font(name=F, size=9, italic=True)
header(wa, 3, ["Parameter", "Value", "Why / source"])
rows = [
    ("Pass mark (subject score %)", 40, "Typical school board pass mark (assumption)"),
    ("Low attendance below (%)", 75, "Common eligibility cut-off for exams (assumption)"),
    ("Low overall score below (%)", 50, "Risk flag trigger (assumption)"),
    ("Low assignment completion below (%)", 65, "Risk flag trigger (assumption)"),
    ("Needs-support score band below (%)", 45, "Matches performance_band in SQL"),
    ("Subject 'high priority' if fail rate >= ", 0.10, "Fail rate above 10% flags a subject for support"),
]
for i, (a, b, c) in enumerate(rows, start=4):
    wa.cell(i, 1, a).font = base
    v = wa.cell(i, 2, b); v.font = blue; v.fill = PatternFill("solid", fgColor="FFFF99")
    wa.cell(i, 3, c).font = base
wa["B9"].number_format = "0%"
wa["A11"] = "Data note"; wa["A11"].font = bold
wa["A12"] = "All data is SYNTHETIC (seeded generator in scripts/generate_data.py). 600 students, 6 subjects, 3 exams each."
wa["A12"].font = base
wa["A13"] = "Study hours missing for 18 students were imputed with the grade average (column G flags them)."
wa["A13"].font = base
for col, w in zip("ABC", (42, 12, 60)): wa.column_dimensions[col].width = w
# Named positions
PASS, LOWATT, LOWSCORE, LOWASG, NEEDS, FAILHI = ("Assumptions!$B$4", "Assumptions!$B$5", "Assumptions!$B$6",
                                                "Assumptions!$B$7", "Assumptions!$B$8", "Assumptions!$B$9")

# ------------------------------------------------------------------ Student_Data
ws = wb.create_sheet("Student_Data")
dump(ws, stu, {"performance_band": 22, "attendance_band": 16, "assignment_band": 16, "study_band": 14,
               "parental_education": 20})
header(ws, 1, ["risk_flags (live)", "risk_level (live)"], start=len(stu.columns) + 1)
cols = {c: get_column_letter(i) for i, c in enumerate(stu.columns, start=1)}
T, U = get_column_letter(len(stu.columns) + 1), get_column_letter(len(stu.columns) + 2)
for r in range(2, NS + 2):
    ws[f"{T}{r}"] = (f"=({cols['attendance_pct']}{r}<{LOWATT})+({cols['overall_pct']}{r}<{LOWSCORE})"
                     f"+({cols['assignment_pct']}{r}<{LOWASG})")
    ws[f"{U}{r}"] = f'=IF({T}{r}>=2,"High",IF({T}{r}=1,"Medium","Low"))'
    ws[f"{T}{r}"].font = base; ws[f"{U}{r}"].font = base
ws.column_dimensions[T].width = 16; ws.column_dimensions[U].width = 16
ws.auto_filter.ref = f"A1:{U}{NS+1}"
rng = lambda name: f"Student_Data!${cols[name]}$2:${cols[name]}${NS+1}"
RISK = f"Student_Data!${U}$2:${U}${NS+1}"

# ------------------------------------------------------------------ Subject_Data
wsd = wb.create_sheet("Subject_Data")
dump(wsd, sub)
srng = lambda name: f"Subject_Data!${get_column_letter(list(sub.columns).index(name)+1)}$2:${get_column_letter(list(sub.columns).index(name)+1)}${NB+1}"

# ------------------------------------------------------------------ Subject_Analysis
wsa = wb.create_sheet("Subject_Analysis")
wsa["A1"] = "Which subjects need support?"; wsa["A1"].font = title
header(wsa, 3, ["Subject", "Avg Score %", "Fail Rate %", "Below 50% Rate", "Avg Assignment %",
                "Students", "Support Priority"])
subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Computer Science"]
for i, s in enumerate(subjects, start=4):
    wsa.cell(i, 1, s).font = base
    wsa.cell(i, 2, f"=AVERAGEIFS({srng('score_pct')},{srng('subject_name')},A{i})")
    wsa.cell(i, 3, f'=COUNTIFS({srng("subject_name")},A{i},{srng("score_pct")},"<"&{PASS})/F{i}')
    wsa.cell(i, 4, f'=COUNTIFS({srng("subject_name")},A{i},{srng("score_pct")},"<50")/F{i}')
    wsa.cell(i, 5, f"=AVERAGEIFS({srng('assignment_pct')},{srng('subject_name')},A{i})")
    wsa.cell(i, 6, f"=COUNTIF({srng('subject_name')},A{i})")
    wsa.cell(i, 7, f'=IF(C{i}>={FAILHI},"HIGH","Monitor")')
    for c in range(2, 8): wsa.cell(i, c).font = base
    wsa.cell(i, 2).number_format = wsa.cell(i, 5).number_format = "0.0"
    wsa.cell(i, 3).number_format = wsa.cell(i, 4).number_format = "0.0%"
wsa.conditional_formatting.add("G4:G9", CellIsRule(operator="equal", formula=['"HIGH"'],
                               fill=PatternFill("solid", bgColor="F5B7B1"), font=Font(name=F, bold=True, color="922B21")))
for col, w in zip("ABCDEFG", (20, 13, 12, 15, 17, 10, 16)): wsa.column_dimensions[col].width = w
wsa["A11"] = "Fail rate = share of students whose weighted subject score is below the pass mark (Assumptions!B4)."
wsa["A11"].font = Font(name=F, size=9, italic=True)

# ------------------------------------------------------------------ Factor_Analysis
wf = wb.create_sheet("Factor_Analysis")
wf["A1"] = "What drives academic performance?"; wf["A1"].font = title

def band_table(top, label, colname, bands):
    header(wf, top, [label, "Students", "Avg Score %", "% Needs Support"])
    for i, b in enumerate(bands, start=top + 1):
        wf.cell(i, 1, b).font = base
        wf.cell(i, 2, f"=COUNTIF({rng(colname)},A{i})")
        wf.cell(i, 3, f"=AVERAGEIF({rng(colname)},A{i},{rng('overall_pct')})")
        wf.cell(i, 4, f'=COUNTIFS({rng(colname)},A{i},{rng("overall_pct")},"<"&{NEEDS})/B{i}')
        for c in (2, 3, 4): wf.cell(i, c).font = base
        wf.cell(i, 3).number_format = "0.0"; wf.cell(i, 4).number_format = "0.0%"

att_b = ["1. 90%+", "2. 80-89%", "3. 75-79%", "4. Below 75%"]
asg_b = ["1. 90%+", "2. 75-89%", "3. 65-74%", "4. Below 65%"]
stu_b = ["1. 15+ hrs", "2. 10-14 hrs", "3. 5-9 hrs", "4. <5 hrs"]
band_table(3, "Attendance band", "attendance_band", att_b)       # rows 4-7
band_table(10, "Assignment completion band", "assignment_band", asg_b)   # rows 11-14
band_table(17, "Weekly study hours band", "study_band", stu_b)   # rows 18-21
perf_b = ["1. Excellent (75+)", "2. Good (60-74)", "3. Average (45-59)", "4. Needs Support (<45)"]
header(wf, 24, ["Performance band", "Students", "% of Students"])
for i, b in enumerate(perf_b, start=25):
    wf.cell(i, 1, b).font = base
    wf.cell(i, 2, f"=COUNTIF({rng('performance_band')},A{i})").font = base
    wf.cell(i, 3, f"=B{i}/SUM($B$25:$B$28)").font = base
    wf.cell(i, 3).number_format = "0.0%"

header(wf, 3, ["Factor", "Correlation with score", "Strength"], start=7)
facs = [("Assignment completion %", "assignment_pct"), ("On-time submission %", "on_time_pct"),
        ("Attendance %", "attendance_pct"), ("Study hours / week", "study_hours_week")]
for i, (lab, col) in enumerate(facs, start=4):
    wf.cell(i, 7, lab).font = base
    wf.cell(i, 8, f"=CORREL({rng(col)},{rng('overall_pct')})").font = base
    wf.cell(i, 8).number_format = "0.00"
    wf.cell(i, 9, f'=IF(ABS(H{i})>=0.7,"Strong",IF(ABS(H{i})>=0.4,"Moderate","Weak"))').font = base

header(wf, 10, ["Other factor", "Group", "Students", "Avg Score %"], start=7)
others = [("Tutoring", "tutoring", ["Yes", "No"]), ("Internet access", "internet_access", ["Yes", "No"]),
          ("Extracurricular", "extracurricular", ["Yes", "No"]), ("Gender", "gender", ["Female", "Male"]),
          ("Parental education", "parental_education",
           ["Below High School", "High School", "Graduate", "Postgraduate"])]
r = 11
for lab, col, vals in others:
    for v in vals:
        wf.cell(r, 7, lab).font = base; wf.cell(r, 8, v).font = base
        wf.cell(r, 9, f"=COUNTIF({rng(col)},H{r})").font = base
        wf.cell(r, 10, f"=AVERAGEIF({rng(col)},H{r},{rng('overall_pct')})").font = base
        wf.cell(r, 10).number_format = "0.0"; r += 1
wf["G29"] = "Correlation shows association, not proof of cause: stronger students may also submit more work."
wf["G29"].font = Font(name=F, size=9, italic=True)
for col, w in zip("ABCDEFGHIJ", (26, 10, 13, 16, 3, 3, 26, 22, 12, 13)): wf.column_dimensions[col].width = w

# ------------------------------------------------------------------ Interventions
wi = wb.create_sheet("Interventions")
dump(wi, plan, {"recommended_intervention": 62, "weakest_subject": 18})
wi.freeze_panes = "A2"

# ------------------------------------------------------------------ Dashboard
wd = wb.create_sheet("Dashboard", 0)
wd.sheet_view.showGridLines = False
wd["A1"] = "Student Performance Dashboard"; wd["A1"].font = title
wd["A2"] = "Academic year 2025-26 | 600 students | Synthetic data"; wd["A2"].font = Font(name=F, size=9, italic=True)
kpis = [
    ("Students", f"=COUNTA({rng('student_id')})", "0"),
    ("Avg Score %", f"=AVERAGE({rng('overall_pct')})", "0.0"),
    ("Avg Attendance %", f"=AVERAGE({rng('attendance_pct')})", "0.0"),
    ("Avg Assignment %", f"=AVERAGE({rng('assignment_pct')})", "0.0"),
    ("High-Risk Students", f'=COUNTIF({RISK},"High")', "0"),
    ("% High-Risk", f'=COUNTIF({RISK},"High")/COUNTA({rng("student_id")})', "0.0%"),
]
for i, (lab, f, nf) in enumerate(kpis):
    c = 1 + i * 2
    wd.merge_cells(start_row=4, start_column=c, end_row=4, end_column=c + 1)
    wd.merge_cells(start_row=5, start_column=c, end_row=5, end_column=c + 1)
    a = wd.cell(4, c, lab); a.font = Font(name=F, size=9, color="FFFFFF", bold=True)
    a.fill = PatternFill("solid", fgColor=TEAL); a.alignment = Alignment(horizontal="center")
    b = wd.cell(5, c, f); b.font = Font(name=F, size=20, bold=True, color=NAVY); b.number_format = nf
    b.fill = PatternFill("solid", fgColor=LIGHT); b.alignment = Alignment(horizontal="center")
    wd.cell(4, c + 1).fill = PatternFill("solid", fgColor=TEAL); wd.cell(5, c + 1).fill = PatternFill("solid", fgColor=LIGHT)
for c in range(1, 13): wd.column_dimensions[get_column_letter(c)].width = 11
wd.row_dimensions[5].height = 34

def bar(title_, sheet, cats, vals, anchor, ytitle, color, fmt="0.0", horizontal=False):
    ch = BarChart(); ch.type = "bar" if horizontal else "col"; ch.title = title_
    ch.add_data(vals, titles_from_data=True); ch.set_categories(cats)
    ch.legend = None; ch.height, ch.width = 7.5, 12.5
    ch.y_axis.title = ytitle; ch.y_axis.majorGridlines = None
    ch.x_axis.delete = False; ch.y_axis.delete = False
    ch.series[0].graphicalProperties.solidFill = color
    ch.dataLabels = DataLabelList(); ch.dataLabels.showVal = True
    ch.dataLabels.showSerName = ch.dataLabels.showCatName = ch.dataLabels.showLegendKey = False
    ch.dataLabels.numFmt = fmt
    wd.add_chart(ch, anchor)

bar("Average score by subject (%)", wsa, Reference(wsa, min_col=1, min_row=4, max_row=9),
    Reference(wsa, min_col=2, min_row=3, max_row=9), "A7", "Avg score %", NAVY, horizontal=True)
bar("Fail rate by subject", wsa, Reference(wsa, min_col=1, min_row=4, max_row=9),
    Reference(wsa, min_col=3, min_row=3, max_row=9), "G7", "Fail rate", "C0392B", "0.0%", horizontal=True)
bar("Score by attendance band", wf, Reference(wf, min_col=1, min_row=4, max_row=7),
    Reference(wf, min_col=3, min_row=3, max_row=7), "A23", "Avg score %", TEAL)
bar("Score by assignment completion", wf, Reference(wf, min_col=1, min_row=11, max_row=14),
    Reference(wf, min_col=3, min_row=10, max_row=14), "G23", "Avg score %", TEAL)
bar("Score by weekly study hours", wf, Reference(wf, min_col=1, min_row=18, max_row=21),
    Reference(wf, min_col=3, min_row=17, max_row=21), "A39", "Avg score %", "E9C46A")
bar("Students by performance band", wf, Reference(wf, min_col=1, min_row=25, max_row=28),
    Reference(wf, min_col=2, min_row=24, max_row=28), "G39", "Students", NAVY, "0")

out = ROOT / "excel" / "Student_Performance_Analysis.xlsx"
wb.save(out); print("saved", out)
