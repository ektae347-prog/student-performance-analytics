# Findings and recommended interventions

*Dataset: 600 students, 6 subjects, academic year 2025-26 (synthetic). Figures come from
`sql/04_analysis_queries.sql` and match the Excel workbook.*

## 1. Snapshot
| Metric | Value |
|---|---|
| Average score | 59.3% |
| Average attendance | 85.9% |
| Average assignment completion | 80.5% |
| Students scoring < 45% ("needs support") | 77 (12.8%) |
| High-risk students (2+ risk flags) | 55 (9.2%) |
| Medium-risk students (1 flag) | 116 (19.3%) |

## 2. Which subjects need support?
| Subject | Avg score | Fail rate (<40%) | Below 50% |
|---|---|---|---|
| Mathematics | 53.8% | **16.2%** | 40.0% |
| Physics | 54.9% | **13.7%** | 34.8% |
| Chemistry | 57.8% | **10.2%** | 27.3% |
| Biology | 60.8% | 5.8% | 21.2% |
| English | 63.8% | 3.3% | 15.0% |
| Computer Science | 64.6% | 4.2% | 14.0% |

* **Mathematics, Physics and Chemistry** are the support priorities. Maths alone has 40% of students below 50%.
* Maths is also the weakest subject for **92 of the 171** at-risk students, Physics for 45, Chemistry for 23.
* Maths and Physics are the most attendance-sensitive: the gap between 90%+ and <75% attendance is
  **20.4 and 19.1 points**, against 14.5 for Biology.
* Scores rise slightly through the year (Unit Test 57.5% -> Midterm 59.1% -> Final 59.9%), so there is no sign of a late-term collapse.

## 3. What is associated with performance?
| Factor | Finding |
|---|---|
| **Assignment completion** | Strongest link (r = 0.89). 90%+ completers average **75.6%**; under 65% average **38.1%** (a 37-point gap). On-time submission is similar (r = 0.91). |
| **Attendance** | Moderate link (r = 0.50). 90%+ attendance averages **66.2%**; under 75% averages **49.3%**. 34% of students under 75% attendance need support vs 2% of those above 90%. |
| **Study hours** | Moderate link (r = 0.48). 15+ hrs/week: **69.8%**; under 5 hrs: **46.2%**. |
| Tutoring | Small (+1.9 points for tutored students) |
| Internet access | Small (+1.3 points) |
| Extracurriculars, parental education | Negligible spread (57.9%-59.8% across education levels) |
| Gender, section, grade | Small differences (about 2 points); not a basis for targeting |

**Reading these correctly:** these are associations. Assignment completion is probably as much a *symptom*
of engagement and ability as a cause of marks, so the 37-point gap should not be promised as the gain from
a homework club. A pilot with a comparison group is the way to measure the real effect.

## 4. Recommended interventions
171 students (28.5%) are flagged. The plan matches support to the cause:

| Priority | Who | Count | Action | Owner |
|---|---|---|---|---|
| **1** | Low attendance **and** low assignments | 15 | Weekly mentor check-in, parent meeting within 2 weeks, homework club, attendance contract | Class teacher + counsellor |
| **2a** | Attendance < 75% | 46 | Absence-reason call to parents, transport/health follow-up, make-up sessions for missed Maths/Physics topics | Class teacher |
| **2b** | Assignments < 65% | 26 | Homework club, assignment tracker shared with parents, deadline reminders | Subject teacher |
| **3** | Overall < 50%, attendance and assignments OK | 84 | Targeted remedial classes in weakest subject (mostly Maths) | Subject teacher |

**School-level actions**
1. Run **Maths and Physics remedial batches** first: they hold 137 of the 171 flagged students as their weakest subject.
2. Add an **early-warning rule**: alert when attendance falls under 80% or two assignments in a row are missed, before the student reaches the risk threshold.
3. Introduce an **assignment-tracking routine** (weekly submission report per section).
4. Keep a monthly **attendance review** for the 84 students between 75% and 79% who are one bad month away from the cut-off.
5. Don't spend budget targeting by gender, parental education or extracurricular activity: the data shows no useful signal there.

## 5. How to measure whether it worked
| KPI | Baseline | Target (next term) |
|---|---|---|
| High-risk students | 55 | 35 or fewer |
| Maths fail rate | 16.2% | under 10% |
| Students under 75% attendance | 61 | under 40 |
| Avg assignment completion | 80.5% | 85%+ |

Compare supported students with similar un-supported ones (or stagger the roll-out by section) to separate
the programme's effect from natural improvement.

## 6. Limitations
* Synthetic data: effect sizes reflect the simulation settings, not a real school.
* Single academic year; no student-level history, so progress over time cannot be tracked.
* Risk thresholds (75 / 50 / 65) are assumptions; they are adjustable and should be tuned to the real board rules.
