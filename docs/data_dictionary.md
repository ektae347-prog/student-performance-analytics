# Data dictionary

All data is **synthetic** (`scripts/generate_data.py`, seed 42). Relationships between variables
are simulated, so findings illustrate the *method*, not real-world effect sizes.

## Raw tables (`data/raw/`)
| Table | Grain | Rows |
|---|---|---|
| students | 1 per student | 600 |
| subjects | 1 per subject | 6 |
| attendance | student x month (Aug 2025 - Jan 2026) | 3,600 |
| assignments | student x subject | 3,600 |
| marks | student x subject x exam (Unit Test /25, Midterm /50, Final /100) | 10,825 (25 duplicates) |

### students
| Column | Description |
|---|---|
| student_id | Unique id (S0001-S0600) |
| gender, grade (9-12), section (A-D) | Demographics / class |
| parental_education | Below High School / High School / Graduate / Postgraduate (12 missing) |
| study_hours_week | Self-reported weekly study hours (18 missing) |
| internet_access, extracurricular, tutoring | Yes / No |

## Analytical views (`data/processed/`)
### student_summary (1 row per student)
| Column | Definition |
|---|---|
| attendance_pct | Days present / working days over 6 months |
| overall_pct | Mean of the 6 subject scores |
| assignment_pct | Mean assignment submission rate across subjects |
| on_time_pct | Assignments submitted on time / assigned |
| subjects_failed | Number of subjects with weighted score < 40% |
| performance_band | Excellent 75+, Good 60-74, Average 45-59, Needs Support <45 |
| attendance_band / assignment_band / study_band | Bucketed versions for charts |
| risk_flags | Count of: attendance < 75, overall < 50, assignment < 65 |
| risk_level | High (2-3 flags), Medium (1), Low (0) |

### student_subject (1 row per student x subject)
`score_pct` = total marks / total possible across the three exams (the Final carries the most weight),
`final_pct`, `assignment_pct`, `on_time_pct`.

### intervention_plan (at-risk students only)
Weakest subject plus a rule-based recommendation:
| Rule | Recommendation |
|---|---|
| attendance < 75 **and** assignments < 65 | Priority 1: attendance counselling + parent meeting + homework club |
| attendance < 75 | Priority 2: attendance counselling + parent meeting |
| assignments < 65 | Priority 2: homework club + assignment tracker |
| otherwise (overall < 50) | Priority 3: remedial classes in weakest subject |

## Cleaning log
| Issue | Rows | Treatment |
|---|---|---|
| Duplicate mark records | 25 | `SELECT DISTINCT` into `fact_marks` |
| Lower-case gender values | 15 | Standardised to Title Case |
| Missing parental_education | 12 | Labelled `Unknown` (not guessed) |
| Missing study_hours_week | 18 | Imputed with the student's grade mean; `study_hours_imputed = 1` |

## Assumptions
Pass mark 40%, low attendance < 75%, low assignments < 65%, needs-support < 45%. All are
configurable in `sql/03_views.sql`, the Excel `Assumptions` sheet and Power BI What-if parameters.
