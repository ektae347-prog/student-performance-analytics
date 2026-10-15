# Power BI dashboard - build guide

Power BI `.pbix` files are binary, so this folder gives you everything needed to rebuild the
report in about 30-45 minutes: the model, every DAX measure, a theme and the page layout.
Once built, save your report here as `Student_Performance.pbix` and add screenshots to `/images`.

## 1. Load data
`Home > Get data > Text/CSV`, load these from `data/processed/`:

| Table | File | Grain |
|---|---|---|
| `student_summary` | student_summary.csv | 1 row per student |
| `student_subject` | student_subject.csv | 1 row per student x subject |
| `intervention_plan` | intervention_plan.csv | 1 row per at-risk student |
| `fact_attendance` | fact_attendance.csv | 1 row per student x month |
| `fact_marks` | fact_marks.csv | 1 row per student x subject x exam |
| `dim_subject` | dim_subject.csv | 1 row per subject |

> Alternative: connect straight to the SQL database and import the views
> `vw_student_summary`, `vw_student_subject`, `vw_intervention_plan` (SQL Server/MySQL/PostgreSQL connector).

In Power Query set `risk_level`, `performance_band` etc. as Text, `*_pct` as Decimal Number.

## 2. Model (Model view)
```
dim_subject (1) ----< student_subject (*) >---- (1) student_summary (1) ----< fact_attendance
                                                       |  (1)                          
                                                       +---- (1) intervention_plan (1:1)
dim_subject (1) ----< fact_marks (*) >---- (1) student_summary
```
All relationships are single-direction, one-to-many from `student_summary[student_id]` /
`dim_subject[subject_id]`. Sort `attendance_band`, `assignment_band`, `study_band` and
`performance_band` by themselves (the leading number keeps the order correct).

## 3. Measures and theme
* Create an empty `_Measures` table and paste everything from [`measures.dax`](measures.dax).
* Create the three What-if parameters listed at the top of that file.
* `View > Themes > Browse for themes` -> [`theme.json`](theme.json).

## 4. Pages

**Page 1 - Executive Overview**
* Cards: Total Students, Avg Score %, Avg Attendance %, Avg Assignment %, High Risk Students, High Risk %
* Clustered bar: `Subject Avg Score %` by subject (conditional colour on `Subject Support Flag`)
* Donut/column: students by `performance_band`
* Slicers: grade, section, gender

**Page 2 - Subject Deep-Dive** ("Where do students need support?")
* Bar: `Subject Fail Rate` by subject, sorted descending
* Matrix (heat-map): subject (rows) x `attendance_band` (columns), value `Subject Avg Score %`, colour scale red-yellow-green
* Line: average % by `exam_type` (Unit Test -> Midterm -> Final) per subject, from `fact_marks`
* Tooltip page: score distribution for the hovered subject

**Page 3 - What Drives Performance?**
* Scatter: x = `attendance_pct`, y = `overall_pct`, legend = `risk_level` (turn on the trend line)
* Column charts: avg score by `attendance_band`, `assignment_band`, `study_band`
* Cards: `Attendance Score Gap`, `Assignment Score Gap`, `Corr Attendance vs Score`, `Corr Assignment vs Score`
* Line: `Monthly Attendance %` by month
* Small multiples: avg score by tutoring / internet access / parental education (shows which factors do *not* matter)

**Page 4 - Intervention Planner**
* Table from `intervention_plan` (student_id, grade, section, overall_pct, attendance_pct, assignment_pct, weakest_subject, recommended_intervention), conditional formatting on `risk_level`
* Bar: students per `recommended_intervention`; bar: at-risk students per `weakest_subject`
* Slicers: grade, section, risk level, weakest subject - lets a teacher export their own class list
* Card: `Students Needing Intervention`, `Priority 1 Students`

## 5. Finishing touches
* Page navigation buttons, consistent 16:9 layout, titles that state the insight ("Maths has the highest fail rate").
* Row-level security (optional): role per `section` so class teachers see only their students.
* Export 4 PNGs of the pages into `/images` and link them in the main README.
