-- =============================================================
-- ARCHIVO 04_courses_academic_load.sql
-- Cursos y carga académica
-- Dependen de: campuses, grades, teachers, subjects,
--              academic_periods, classrooms
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: academic_load
-- (qué docente imparte qué materia en qué período para qué curso)
-- -------------------------------------------------------------
CREATE TABLE academic_load (
    academic_load_id    INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    teacher_id          INT             NOT NULL,
    course_id           INT             NOT NULL,
    subject_id          INT             NOT NULL,
    period_id           INT             NOT NULL,
    CONSTRAINT fk_al_teacher
        FOREIGN KEY (teacher_id) REFERENCES teachers (teacher_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_al_course
        FOREIGN KEY (course_id) REFERENCES courses (course_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_al_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_al_period
        FOREIGN KEY (period_id) REFERENCES academic_periods (period_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_academic_load
        UNIQUE (teacher_id, course_id, subject_id, period_id)
);

-- -------------------------------------------------------------
-- TABLA: schedules
-- (horario de cada carga académica en una aula concreta)
-- -------------------------------------------------------------
CREATE TABLE schedules (
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
        FOREIGN KEY (academic_load_id) REFERENCES academic_load (academic_load_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_schedule_classroom
        FOREIGN KEY (classroom_id) REFERENCES classrooms (classroom_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

ALTER TABLE schedules
ADD CONSTRAINT chk_school_schedule
CHECK (
    start_time IN (
        '06:00',
        '07:00',
        '08:00',
        '10:00',
        '11:00',
        '12:00'
    )
    AND
    (
        end_time = start_time + INTERVAL '1 hour' OR
        end_time = start_time + INTERVAL '2 hours' OR
        end_time = start_time + INTERVAL '3 hours'
    )
);




