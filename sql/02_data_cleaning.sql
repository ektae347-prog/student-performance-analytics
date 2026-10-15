-- =====================================================================
-- 02_data_cleaning.sql  |  Raw -> clean dimension & fact tables
-- Issues found during profiling (see 04_analysis_queries.sql  Q0):
--   * 25 duplicate rows in raw_marks
--   * 15 gender values in lower case
--   * 12 missing parental_education, 18 missing study_hours_week
-- =====================================================================
DROP TABLE IF EXISTS dim_subject;
DROP TABLE IF EXISTS dim_student;
DROP TABLE IF EXISTS fact_attendance;
DROP TABLE IF EXISTS fact_assignments;
DROP TABLE IF EXISTS fact_marks;

CREATE TABLE dim_subject AS
SELECT subject_id, subject_name FROM raw_subjects;

-- Standardise case; label unknown education; impute missing study hours
-- with the average of the student's own grade (documented assumption).
CREATE TABLE dim_student AS
SELECT
    s.student_id,
    UPPER(SUBSTR(TRIM(s.gender),1,1)) || LOWER(SUBSTR(TRIM(s.gender),2)) AS gender,
    s.grade,
    s.section,
    COALESCE(s.parental_education, 'Unknown')                           AS parental_education,
    COALESCE(s.study_hours_week,
             (SELECT ROUND(AVG(x.study_hours_week),1) FROM raw_students x
               WHERE x.grade = s.grade))                                AS study_hours_week,
    CASE WHEN s.study_hours_week IS NULL THEN 1 ELSE 0 END              AS study_hours_imputed,
    s.internet_access,
    s.extracurricular,
    s.tutoring
FROM raw_students s;

CREATE TABLE fact_attendance AS SELECT * FROM raw_attendance;
CREATE TABLE fact_assignments AS SELECT * FROM raw_assignments;

-- De-duplicate marks
CREATE TABLE fact_marks AS
SELECT DISTINCT student_id, subject_id, exam_type, max_marks, marks_obtained
FROM raw_marks;

-- Integrity checks (should all return 0 rows / 0)
-- SELECT COUNT(*) FROM fact_marks WHERE marks_obtained > max_marks OR marks_obtained < 0;
-- SELECT COUNT(*) FROM fact_attendance WHERE days_present > working_days;
-- SELECT student_id, subject_id, exam_type, COUNT(*) FROM fact_marks
--   GROUP BY 1,2,3 HAVING COUNT(*) > 1;
