-- =====================================================================
-- 03_views.sql  |  Analytical views (these feed Excel and Power BI)
-- Business rules (edit in ONE place):
--   Pass mark ............ 40 %
--   Needs-support band ... overall < 45 %
--   Low attendance ....... < 75 %  (common board eligibility threshold)
--   Low assignments ...... < 65 % submitted
-- =====================================================================
DROP VIEW IF EXISTS vw_student_attendance;
DROP VIEW IF EXISTS vw_student_subject;
DROP VIEW IF EXISTS vw_student_summary;
DROP VIEW IF EXISTS vw_intervention_plan;

-- Attendance % per student (days present / working days, all months)
CREATE VIEW vw_student_attendance AS
SELECT student_id,
       SUM(days_present)  AS days_present,
       SUM(working_days)  AS working_days,
       ROUND(100.0 * SUM(days_present) / SUM(working_days), 1) AS attendance_pct
FROM fact_attendance
GROUP BY student_id;

-- One row per student x subject: weighted score % + assignment completion %
-- Weighted score = total marks obtained / total marks possible (Final counts most)
CREATE VIEW vw_student_subject AS
SELECT m.student_id,
       m.subject_id,
       d.subject_name,
       ROUND(100.0 * SUM(m.marks_obtained) / SUM(m.max_marks), 1)                       AS score_pct,
       ROUND(100.0 * MAX(CASE WHEN m.exam_type='Final' THEN m.marks_obtained END)
                   / MAX(CASE WHEN m.exam_type='Final' THEN m.max_marks END), 1)        AS final_pct,
       ROUND(100.0 * a.assignments_submitted / a.assignments_total, 1)                  AS assignment_pct,
       ROUND(100.0 * a.assignments_on_time   / a.assignments_total, 1)                  AS on_time_pct
FROM fact_marks m
JOIN dim_subject d      ON d.subject_id = m.subject_id
JOIN fact_assignments a ON a.student_id = m.student_id AND a.subject_id = m.subject_id
GROUP BY m.student_id, m.subject_id, d.subject_name,
         a.assignments_submitted, a.assignments_total, a.assignments_on_time;

-- One row per student with bands and risk flags
CREATE VIEW vw_student_summary AS
WITH perf AS (
    SELECT student_id,
           ROUND(AVG(score_pct),1)      AS overall_pct,
           ROUND(AVG(assignment_pct),1) AS assignment_pct,
           ROUND(AVG(on_time_pct),1)    AS on_time_pct,
           SUM(CASE WHEN score_pct < 40 THEN 1 ELSE 0 END) AS subjects_failed
    FROM vw_student_subject GROUP BY student_id
), flagged AS (
    SELECT s.*, a.attendance_pct, p.overall_pct, p.assignment_pct, p.on_time_pct, p.subjects_failed,
           (CASE WHEN a.attendance_pct < 75 THEN 1 ELSE 0 END)
         + (CASE WHEN p.overall_pct    < 50 THEN 1 ELSE 0 END)
         + (CASE WHEN p.assignment_pct < 65 THEN 1 ELSE 0 END) AS risk_flags
    FROM dim_student s
    JOIN vw_student_attendance a ON a.student_id = s.student_id
    JOIN perf p                  ON p.student_id = s.student_id
)
SELECT f.*,
       CASE WHEN overall_pct >= 75 THEN '1. Excellent (75+)'
            WHEN overall_pct >= 60 THEN '2. Good (60-74)'
            WHEN overall_pct >= 45 THEN '3. Average (45-59)'
            ELSE                        '4. Needs Support (<45)' END AS performance_band,
       CASE WHEN attendance_pct >= 90 THEN '1. 90%+'
            WHEN attendance_pct >= 80 THEN '2. 80-89%'
            WHEN attendance_pct >= 75 THEN '3. 75-79%'
            ELSE                           '4. Below 75%' END         AS attendance_band,
       CASE WHEN assignment_pct >= 90 THEN '1. 90%+'
            WHEN assignment_pct >= 75 THEN '2. 75-89%'
            WHEN assignment_pct >= 65 THEN '3. 65-74%'
            ELSE                           '4. Below 65%' END         AS assignment_band,
       CASE WHEN study_hours_week >= 15 THEN '1. 15+ hrs'
            WHEN study_hours_week >= 10 THEN '2. 10-14 hrs'
            WHEN study_hours_week >= 5  THEN '3. 5-9 hrs'
            ELSE                             '4. <5 hrs' END          AS study_band,
       CASE WHEN risk_flags >= 2 THEN 'High'
            WHEN risk_flags = 1  THEN 'Medium'
            ELSE                      'Low' END                       AS risk_level
FROM flagged f;

-- Intervention plan: weakest subject + rule-based recommendation per at-risk student
CREATE VIEW vw_intervention_plan AS
WITH ranked AS (
    SELECT student_id, subject_name, score_pct,
           ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY score_pct ASC) AS rn
    FROM vw_student_subject
)
SELECT s.student_id, s.grade, s.section, s.overall_pct, s.attendance_pct, s.assignment_pct,
       s.risk_level, r.subject_name AS weakest_subject, r.score_pct AS weakest_subject_pct,
       CASE WHEN s.attendance_pct < 75 AND s.assignment_pct < 65 THEN 'Priority 1: Attendance counselling + parent meeting + homework club'
            WHEN s.attendance_pct < 75                           THEN 'Priority 2: Attendance counselling + parent meeting'
            WHEN s.assignment_pct < 65                           THEN 'Priority 2: Homework club + assignment tracker'
            WHEN s.overall_pct < 50                              THEN 'Priority 3: Remedial classes in weakest subject'
            ELSE 'Monitor' END                                    AS recommended_intervention
FROM vw_student_summary s
JOIN ranked r ON r.student_id = s.student_id AND r.rn = 1
WHERE s.risk_level IN ('High','Medium');
