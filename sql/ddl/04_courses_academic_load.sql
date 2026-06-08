-- =============================================================
-- ARCHIVO 04_courses_academic_load.sql
-- Cursos y carga académica
-- Dependen de: campuses, grades, teachers, subjects,
--              academic_periods, classrooms
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: courses  (grupos/cursos asignados a un grado en un campus)
-- -------------------------------------------------------------
CREATE TABLE academic.courses (
    course_id           INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grade_id            INT             NOT NULL,
    campus_id           INT             NOT NULL,
    name                VARCHAR(180)    NOT NULL,
    maximum_capacity    INT             NOT NULL CHECK (maximum_capacity > 0),
    academic_year       INT             NOT NULL,
    status              VARCHAR(20)     NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive')),
    CONSTRAINT fk_course_grade
        FOREIGN KEY (grade_id) REFERENCES academic.grades (grade_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_course_campus
        FOREIGN KEY (campus_id) REFERENCES academic.campuses (campus_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_course UNIQUE (campus_id, grade_id, name, academic_year)
);

-- -------------------------------------------------------------
-- TABLA: academic_load
-- (qué docente imparte qué materia en qué período para qué curso)
-- -------------------------------------------------------------
CREATE TABLE academic.academic_load (
    academic_load_id    INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    teacher_id          INT             NOT NULL,
    course_id           INT             NOT NULL,
    subject_id          INT             NOT NULL,
    period_id           INT             NOT NULL,
    CONSTRAINT fk_al_teacher
        FOREIGN KEY (teacher_id) REFERENCES academic.teachers (teacher_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_al_course
        FOREIGN KEY (course_id) REFERENCES academic.courses (course_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_al_subject
        FOREIGN KEY (subject_id) REFERENCES academic.subjects (subject_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_al_period
        FOREIGN KEY (period_id) REFERENCES academic.academic_periods (period_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_academic_load
        UNIQUE (teacher_id, course_id, subject_id, period_id)
);

-- -------------------------------------------------------------
-- TABLA: schedules
-- (horario de cada carga académica en una aula concreta)
-- -------------------------------------------------------------
CREATE TABLE academic.schedules (
    schedule_id         INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    academic_load_id    INT             NOT NULL,
    classroom_id        INT             NOT NULL,
    day_of_week         VARCHAR(15)     NOT NULL
                        CHECK (day_of_week IN ('Monday','Tuesday','Wednesday',
                                               'Thursday','Friday','Saturday','Sunday')),
    start_time          TIME            NOT NULL,
    end_time            TIME            NOT NULL,
    status              VARCHAR(20)     NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive')),
    CONSTRAINT chk_schedule_times CHECK (end_time > start_time),
    CONSTRAINT fk_schedule_al
        FOREIGN KEY (academic_load_id) REFERENCES academic.academic_load (academic_load_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_schedule_classroom
        FOREIGN KEY (classroom_id) REFERENCES academic.classrooms (classroom_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);