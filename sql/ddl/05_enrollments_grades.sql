-- =============================================================
-- ARCHIVO 05_enrollments_grades.sql
-- Matrículas, boletines y calificaciones
-- Dependen de: students, courses, academic_periods,
--              academic_load, guardians
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: enrollments
-- -------------------------------------------------------------
CREATE TABLE academic.enrollments (
    enrollment_id   INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id      INT             NOT NULL,
    course_id       INT             NOT NULL,
    period_id       INT             NOT NULL,
    enrollment_date DATE            NOT NULL DEFAULT CURRENT_DATE,
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'withdrawn', 'completed')),
    CONSTRAINT uq_enrollment UNIQUE (student_id, course_id, period_id),
    CONSTRAINT fk_enroll_student
        FOREIGN KEY (student_id) REFERENCES academic.students (student_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_enroll_course
        FOREIGN KEY (course_id) REFERENCES academic.courses (course_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_enroll_period
        FOREIGN KEY (period_id) REFERENCES academic.academic_periods (period_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- -------------------------------------------------------------
-- TABLA: grade_sheets  (planilla de notas por carga académica)
-- -------------------------------------------------------------
CREATE TABLE academic.grade_sheets (
    grade_sheet_id      INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    academic_load_id    INT             NOT NULL,
    period_id           INT             NOT NULL,
    generation_date     DATE            NOT NULL DEFAULT CURRENT_DATE,
    status              VARCHAR(20)     NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'closed', 'approved')),
    CONSTRAINT fk_gs_al
        FOREIGN KEY (academic_load_id) REFERENCES academic.academic_load (academic_load_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_gs_period
        FOREIGN KEY (period_id) REFERENCES academic.academic_periods (period_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_grade_sheet UNIQUE (academic_load_id, period_id)
);

-- -------------------------------------------------------------
-- TABLA: grade_sheet_details
-- (calificación individual por estudiante en una planilla)
-- -------------------------------------------------------------
CREATE TABLE academic.grade_sheet_details (
    detail_id       INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grade_sheet_id  INT             NOT NULL,
    enrollment_id   INT             NOT NULL,
    score           DECIMAL(5,2)
                    CHECK (score >= 0 AND score <= 5),
    final_grade     DECIMAL(5,2)
                    CHECK (final_grade >= 0 AND final_grade <= 5),
    performance_level VARCHAR(50),
    CONSTRAINT fk_gsd_sheet
        FOREIGN KEY (grade_sheet_id) REFERENCES academic.grade_sheets (grade_sheet_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_gsd_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES academic.enrollments (enrollment_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_sheet_student UNIQUE (grade_sheet_id, enrollment_id)
);

-- -------------------------------------------------------------
-- TABLA: report_cards  (boletines de calificaciones)
-- -------------------------------------------------------------
CREATE TABLE academic.report_cards (
    report_card_id  INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enrollment_id   INT             NOT NULL,
    period_id       INT             NOT NULL,
    overall_average DECIMAL(5,2)
    CHECK (
        overall_average >= 0
        AND overall_average <= 5
    ),
    generation_date DATE            NOT NULL DEFAULT CURRENT_DATE,
    CONSTRAINT uq_report_card UNIQUE (enrollment_id, period_id),
    CONSTRAINT fk_rc_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES academic.enrollments (enrollment_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_rc_period
        FOREIGN KEY (period_id) REFERENCES academic.academic_periods (period_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- -------------------------------------------------------------
-- TABLA: grade_records  (historial de notas por actividad)
-- -------------------------------------------------------------
CREATE TABLE academic.grade_records (
    grade_record_id INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activity_id     INT,            -- FK añadida en archivo 06
    enrollment_id   INT             NOT NULL,
    score           DECIMAL(5,2)    NOT NULL
                    CHECK (score >= 0 AND score <= 5),
    comments        TEXT,
    record_date     DATE            NOT NULL DEFAULT CURRENT_DATE,
    CONSTRAINT fk_gr_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES academic.enrollments (enrollment_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);