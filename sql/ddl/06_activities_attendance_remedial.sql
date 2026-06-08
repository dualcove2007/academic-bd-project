-- =============================================================
-- ARCHIVO 06_activities_attendance_remedial.sql
-- Actividades, asistencia, recuperaciones y record estudiantil
-- Dependen de: academic_load, enrollments, schedules,
--              grade_records (ya creada)
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: activities
-- -------------------------------------------------------------
CREATE TABLE academic.activities (
    activity_id         INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    academic_load_id    INT             NOT NULL,
    name                VARCHAR(180)    NOT NULL,
    description         TEXT,
    percentage          DECIMAL(5,2)    NOT NULL CHECK (percentage > 0 AND percentage <= 100),
    activity_date       DATE,
    CONSTRAINT fk_act_al
        FOREIGN KEY (academic_load_id) REFERENCES academic.academic_load (academic_load_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT uq_activity UNIQUE (academic_load_id, name, activity_date)
);

-- Ahora que activities existe, agregamos la FK diferida en grade_records
ALTER TABLE academic.grade_records
    ADD CONSTRAINT fk_gr_activity
        FOREIGN KEY (activity_id) REFERENCES academic.activities (activity_id)
        ON UPDATE CASCADE ON DELETE SET NULL;

-- -------------------------------------------------------------
-- TABLA: attendance
-- -------------------------------------------------------------
CREATE TABLE academic.attendance (
    attendance_id       INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enrollment_id       INT             NOT NULL,
    schedule_id         INT             NOT NULL,
    attendance_date     DATE            NOT NULL,
    attendance_status   VARCHAR(20)     NOT NULL
                        CHECK (attendance_status IN ('present','absent','late','excused')),
    comments            TEXT,
    CONSTRAINT uq_attendance UNIQUE (enrollment_id, schedule_id, attendance_date),
    CONSTRAINT fk_att_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES academic.enrollments (enrollment_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_att_schedule
        FOREIGN KEY (schedule_id) REFERENCES academic.schedules (schedule_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- -------------------------------------------------------------
-- TABLA: remedial_exams  (exámenes de recuperación)
-- -------------------------------------------------------------
CREATE TABLE academic.remedial_exams (
    remedial_id         INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enrollment_id       INT             NOT NULL,
    academic_load_id    INT             NOT NULL,
    period_id           INT             NOT NULL,
    exam_date           DATE            NOT NULL,
    score               DECIMAL(5,2)
    CHECK (
        score >= 0
        AND score <= 5
    ),
    comments            TEXT,
    CONSTRAINT fk_re_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES academic.enrollments (enrollment_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_re_al
        FOREIGN KEY (academic_load_id) REFERENCES academic.academic_load (academic_load_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_re_period
        FOREIGN KEY (period_id) REFERENCES academic.academic_periods (period_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- -------------------------------------------------------------
-- TABLA: student_record  (hoja de vida / observador del estudiante)
-- -------------------------------------------------------------
CREATE TABLE academic.student_record (
    record_id       INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id      INT             NOT NULL,
    teacher_id      INT,
    record_date     DATE            NOT NULL DEFAULT CURRENT_DATE,
    type            VARCHAR(50)
    CHECK (type IN ('positive', 'disciplinary', 'academic', 'behavioral')),
    description     TEXT,
    commitment      TEXT,
    CONSTRAINT fk_sr_student
        FOREIGN KEY (student_id) REFERENCES academic.students (student_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_sr_teacher
        FOREIGN KEY (teacher_id) REFERENCES academic.teachers (teacher_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- -------------------------------------------------------------
-- TABLA: learning_outcomes  (logros/resultados de aprendizaje)
-- -------------------------------------------------------------
CREATE TABLE academic.learning_outcomes (
    outcome_id          INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subject_id          INT             NOT NULL,
    period_id           INT             NOT NULL,
    academic_load_id    INT             NOT NULL,
    enrollment_id       INT,
    description         TEXT,
    CONSTRAINT fk_lo_subject
        FOREIGN KEY (subject_id) REFERENCES academic.subjects (subject_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_lo_period
        FOREIGN KEY (period_id) REFERENCES academic.academic_periods (period_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_lo_al
        FOREIGN KEY (academic_load_id) REFERENCES academic.academic_load (academic_load_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_lo_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES academic.enrollments (enrollment_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT uq_learning_outcome UNIQUE (subject_id, period_id, academic_load_id, enrollment_id)
);