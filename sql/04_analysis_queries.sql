-- =====================================================================
-- 04_analysis_queries.sql  |  Business questions answered in SQL
-- Run after 01-03. Each query is independent.
-- =====================================================================

-- Q0. Data profiling: what needed cleaning?
SELECT 'duplicate marks rows'   AS issue, (SELECT COUNT(*) FROM raw_marks) - (SELECT COUNT(*) FROM fact_marks) AS n
UNION ALL SELECT 'lower-case gender',      COUNT(*) FROM raw_students WHERE gender <> UPPER(SUBSTR(gender,1,1)) || LOWER(SUBSTR(gender,2))
UNION ALL SELECT 'missing parental edu',   COUNT(*) FROM raw_students WHERE parental_education IS NULL
UNION ALL SELECT 'missing study hours',    COUNT(*) FROM raw_students WHERE study_hours_week IS NULL;

-- Q1. Headline KPIs
SELECT COUNT(*)                                   AS students,
       ROUND(AVG(overall_pct),1)                  AS avg_score_pct,
       ROUND(AVG(attendance_pct),1)               AS avg_attendance_pct,
       ROUND(AVG(assignment_pct),1)               AS avg_assignment_pct,
       ROUND(100.0*SUM(risk_level='High')/COUNT(*),1) AS high_risk_pct
FROM vw_student_summary;

-- Q2. Which subjects need support?  (lowest average, highest fail / below-50 rate)
SELECT subject_name,
       ROUND(AVG(score_pct),1)                                AS avg_score_pct,
       ROUND(100.0*SUM(score_pct < 40)/COUNT(*),1)            AS fail_rate_pct,
       ROUND(100.0*SUM(score_pct < 50)/COUNT(*),1)            AS below_50_pct,
       ROUND(AVG(assignment_pct),1)                           AS avg_assignment_pct
FROM vw_student_subject
GROUP BY subject_name
ORDER BY avg_score_pct;

-- Q3. Attendance band vs marks
SELECT attendance_band, COUNT(*) AS students, ROUND(AVG(overall_pct),1) AS avg_score_pct,
       ROUND(100.0*SUM(overall_pct < 45)/COUNT(*),1) AS pct_needs_support
FROM vw_student_summary GROUP BY attendance_band ORDER BY attendance_band;

-- Q4. Assignment completion band vs marks
SELECT assignment_band, COUNT(*) AS students, ROUND(AVG(overall_pct),1) AS avg_score_pct,
       ROUND(100.0*SUM(overall_pct < 45)/COUNT(*),1) AS pct_needs_support
FROM vw_student_summary GROUP BY assignment_band ORDER BY assignment_band;

-- Q5. Study hours band vs marks
SELECT study_band, COUNT(*) AS students, ROUND(AVG(overall_pct),1) AS avg_score_pct
FROM vw_student_summary GROUP BY study_band ORDER BY study_band;

-- Q6. Pearson correlation of each factor with overall score (portable: no CORR() needed)
WITH t AS (SELECT overall_pct y, attendance_pct x, 'attendance_pct' f FROM vw_student_summary
           UNION ALL SELECT overall_pct, assignment_pct, 'assignment_pct' FROM vw_student_summary
           UNION ALL SELECT overall_pct, on_time_pct,    'on_time_pct'    FROM vw_student_summary
           UNION ALL SELECT overall_pct, study_hours_week,'study_hours_week' FROM vw_student_summary)
SELECT f AS factor,
       ROUND((AVG(x*y) - AVG(x)*AVG(y)) /
             (SQRT(AVG(x*x) - AVG(x)*AVG(x)) * SQRT(AVG(y*y) - AVG(y)*AVG(y))), 2) AS correlation_with_score
FROM t GROUP BY f ORDER BY correlation_with_score DESC;

-- Q7. Demographic / support factors (check whether they really matter)
SELECT 'tutoring' AS factor, tutoring AS value, COUNT(*) n, ROUND(AVG(overall_pct),1) avg_score FROM vw_student_summary GROUP BY tutoring
UNION ALL SELECT 'internet_access', internet_access, COUNT(*), ROUND(AVG(overall_pct),1) FROM vw_student_summary GROUP BY internet_access
UNION ALL SELECT 'extracurricular', extracurricular, COUNT(*), ROUND(AVG(overall_pct),1) FROM vw_student_summary GROUP BY extracurricular
UNION ALL SELECT 'gender', gender, COUNT(*), ROUND(AVG(overall_pct),1) FROM vw_student_summary GROUP BY gender
UNION ALL SELECT 'parental_education', parental_education, COUNT(*), ROUND(AVG(overall_pct),1) FROM vw_student_summary GROUP BY parental_education;

-- Q8. Heat-map: subject x attendance band (where does low attendance hurt most?)
SELECT ss.subject_name, st.attendance_band, ROUND(AVG(ss.score_pct),1) AS avg_score_pct
FROM vw_student_subject ss JOIN vw_student_summary st ON st.student_id = ss.student_id
GROUP BY ss.subject_name, st.attendance_band ORDER BY ss.subject_name, st.attendance_band;

-- Q9. Grade and section comparison
SELECT grade, section, COUNT(*) AS students, ROUND(AVG(overall_pct),1) AS avg_score_pct,
       SUM(risk_level='High') AS high_risk_students
FROM vw_student_summary GROUP BY grade, section ORDER BY avg_score_pct;

-- Q10. Exam progression: are students improving from Unit Test -> Midterm -> Final?
SELECT d.subject_name, m.exam_type, ROUND(100.0*SUM(m.marks_obtained)/SUM(m.max_marks),1) AS avg_pct
FROM fact_marks m JOIN dim_subject d ON d.subject_id = m.subject_id
GROUP BY d.subject_name, m.exam_type
ORDER BY d.subject_name, CASE m.exam_type WHEN 'Unit Test' THEN 1 WHEN 'Midterm' THEN 2 ELSE 3 END;

-- Q11. Monthly attendance trend
SELECT month, ROUND(100.0*SUM(days_present)/SUM(working_days),1) AS attendance_pct
FROM fact_attendance GROUP BY month ORDER BY month;

-- Q12. Risk profile: how many students per risk level and overlapping flags
SELECT risk_level, COUNT(*) AS students, ROUND(AVG(overall_pct),1) AS avg_score_pct
FROM vw_student_summary GROUP BY risk_level;

-- Q13. Intervention workload: who gets which support
SELECT recommended_intervention, COUNT(*) AS students
FROM vw_intervention_plan GROUP BY recommended_intervention ORDER BY recommended_intervention;

-- Q14. Where do remedial classes need to run?  (weakest subject among at-risk students)
SELECT weakest_subject, COUNT(*) AS at_risk_students
FROM vw_intervention_plan GROUP BY weakest_subject ORDER BY at_risk_students DESC;

-- Q15. Top 20 highest-priority students (named list for teachers)
SELECT student_id, grade, section, overall_pct, attendance_pct, assignment_pct,
       weakest_subject, recommended_intervention
FROM vw_intervention_plan
WHERE risk_level = 'High'
ORDER BY overall_pct ASC
LIMIT 20;
