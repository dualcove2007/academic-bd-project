-- =============================================================
-- ARCHIVO 05_enrollments_grades.sql
-- Matrículas, boletines y calificaciones
-- Dependen de: students, courses, academic_periods,
--              academic_load, guardians
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: enrollments
-- -------------------------------------------------------------
CREATE TABLE enrollments (
    enrollment_id   INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id      INT             NOT NULL,
    course_id       INT             NOT NULL,
    period_id       INT             NOT NULL,
    enrollment_date DATE            NOT NULL DEFAULT CURRENT_DATE,
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'withdrawn', 'completed')),
    CONSTRAINT uq_enrollment UNIQUE (student_id, course_id, period_id),
    CONSTRAINT fk_enroll_student
        FOREIGN KEY (student_id) REFERENCES students (student_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_enroll_course
        FOREIGN KEY (course_id) REFERENCES courses (course_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_enroll_period
        FOREIGN KEY (period_id) REFERENCES academic_periods (period_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

------------------------------------------------------
-- TABLA: grade_records  (historial de notas por actividad)
-- -------------------------------------------------------------
CREATE TABLE grade_records (
    grade_record_id INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activity_id     INT,            -- FK añadida en archivo 06
    enrollment_id   INT             NOT NULL,
    score           DECIMAL(5,2)    NOT NULL
                    CHECK (score >= 0 AND score <= 5),
    comments        TEXT,
    record_date     DATE            NOT NULL DEFAULT CURRENT_DATE,
    CONSTRAINT fk_gr_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (enrollment_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);


CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE observador (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(), 
    estudiante_id   INT             NOT NULL,                             
    docente_id      INT             NOT NULL,                              
    tipo            VARCHAR(50)     NOT NULL,                             
    descripcion     TEXT            NOT NULL,                              
    fecha           TIMESTAMP       NOT NULL DEFAULT NOW(),                
    periodo         VARCHAR(10)     NOT NULL,                              
    compromiso      TEXT,                                                  
    estado_firma    VARCHAR(50)     NOT NULL DEFAULT 'Pendiente',          
    
    -- Llaves foráneas apuntando al modelo base
    CONSTRAINT fk_obs_estudiante
        FOREIGN KEY (estudiante_id) REFERENCES students (student_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_obs_docente
        FOREIGN KEY (docente_id) REFERENCES teachers (teacher_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);



