-- =============================================================
-- ARCHIVO 06_activities_attendance_remedial.sql
-- Actividades, asistencia, recuperaciones y record estudiantil
-- Dependen de: academic_load, enrollments, schedules,
--              grade_records (ya creada)
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: activities
-- -------------------------------------------------------------
CREATE TABLE activities (
    activity_id         INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    academic_load_id    INT             NOT NULL,
    name                VARCHAR(180)    NOT NULL,
    description         TEXT,
    percentage          DECIMAL(5,2)    NOT NULL CHECK (percentage > 0 AND percentage <= 100),
    activity_date       DATE,
    CONSTRAINT fk_act_al
        FOREIGN KEY (academic_load_id) REFERENCES academic_load (academic_load_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT uq_activity UNIQUE (academic_load_id, name, activity_date)
);

-- Ahora que activities existe, agregamos la FK diferida en grade_records
ALTER TABLE grade_records
    ADD CONSTRAINT fk_gr_activity
        FOREIGN KEY (activity_id) REFERENCES activities (activity_id)
        ON UPDATE CASCADE ON DELETE SET NULL;

-- -------------------------------------------------------------
-- TABLA: attendance
-- -------------------------------------------------------------
CREATE TABLE attendance (
    attendance_id       INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enrollment_id       INT             NOT NULL,
    schedule_id         INT             NOT NULL,
    attendance_date     DATE            NOT NULL,
    attendance_status   VARCHAR(20)     NOT NULL
                        CHECK (attendance_status IN ('present','absent','late','excused')),
    comments            TEXT,
    CONSTRAINT uq_attendance UNIQUE (enrollment_id, schedule_id, attendance_date),
    CONSTRAINT fk_att_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (enrollment_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_att_schedule
        FOREIGN KEY (schedule_id) REFERENCES schedules (schedule_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);
