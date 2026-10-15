-- =====================================================================
-- 01_schema.sql  |  Raw landing tables
-- Dialect: ANSI SQL, tested on SQLite 3. Works on PostgreSQL / MySQL /
-- SQL Server with trivial type changes (noted inline).
-- =====================================================================
DROP TABLE IF EXISTS raw_students;
DROP TABLE IF EXISTS raw_subjects;
DROP TABLE IF EXISTS raw_attendance;
DROP TABLE IF EXISTS raw_assignments;
DROP TABLE IF EXISTS raw_marks;

CREATE TABLE raw_subjects (
    subject_id    INTEGER PRIMARY KEY,
    subject_name  VARCHAR(50) NOT NULL
);

CREATE TABLE raw_students (
    student_id          VARCHAR(10) PRIMARY KEY,
    gender              VARCHAR(10),
    grade               INTEGER,
    section             CHAR(1),
    parental_education  VARCHAR(30),
    study_hours_week    DECIMAL(4,1),            -- contains NULLs
    internet_access     VARCHAR(3),
    extracurricular     VARCHAR(3),
    tutoring            VARCHAR(3)
);

CREATE TABLE raw_attendance (                     -- one row per student per month
    student_id    VARCHAR(10) REFERENCES raw_students(student_id),
    month         CHAR(7),                        -- 'YYYY-MM'
    working_days  INTEGER,
    days_present  INTEGER
);

CREATE TABLE raw_assignments (                    -- one row per student per subject
    student_id             VARCHAR(10) REFERENCES raw_students(student_id),
    subject_id             INTEGER REFERENCES raw_subjects(subject_id),
    assignments_total      INTEGER,
    assignments_submitted  INTEGER,
    assignments_on_time    INTEGER
);

CREATE TABLE raw_marks (                          -- one row per student/subject/exam (has duplicates)
    student_id      VARCHAR(10) REFERENCES raw_students(student_id),
    subject_id      INTEGER REFERENCES raw_subjects(subject_id),
    exam_type       VARCHAR(20),                  -- Unit Test | Midterm | Final
    max_marks       INTEGER,
    marks_obtained  INTEGER
);
