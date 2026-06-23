-- =============================================================
-- ARCHIVO 03_users_people.sql
-- Usuarios, docentes y estudiantes
-- Dependen de: institutions, campuses, roles, grades
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: users  (cuentas de acceso al sistema)
-- -------------------------------------------------------------





CREATE TABLE users (
    user_id         INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_id         INT             NOT NULL,
    campus_id       INT             NOT NULL,
    username        VARCHAR(100)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    profile_picture    VARCHAR(500),
    document_type VARCHAR(30)   NOT NULL,
    document_number VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100)  NOT NULL,
    second_last_name VARCHAR(100),
    phone VARCHAR(30),
    email VARCHAR(180),
    last_login      TIMESTAMP,
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'suspended')),
    CONSTRAINT fk_user_role
        FOREIGN KEY (role_id) REFERENCES roles (role_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_user_campus
        FOREIGN KEY (campus_id) REFERENCES campuses (campus_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- -------------------------------------------------------------
-- TABLA: teachers
-- -------------------------------------------------------------
CREATE TABLE teachers (
    teacher_id          INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id             INT UNIQUE,
    document_type       VARCHAR(30)     NOT NULL,
    document_number     VARCHAR(50)     NOT NULL,
    first_name          VARCHAR(100)    NOT NULL,
    middle_name         VARCHAR(100),
    last_name           VARCHAR(100)    NOT NULL,
    second_last_name    VARCHAR(100),
    phone               VARCHAR(30),
    email               VARCHAR(180),
    hire_date           DATE,
    status              VARCHAR(20)     NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive')),
    CONSTRAINT uq_teacher_doc UNIQUE (document_type, document_number),
    CONSTRAINT fk_teacher_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- -------------------------------------------------------------
-- TABLA: students
-- -------------------------------------------------------------
CREATE TABLE students (
    student_id          INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id             INT UNIQUE,
    document_type       VARCHAR(30)     NOT NULL,
    document_number     VARCHAR(50)     NOT NULL,
    first_name          VARCHAR(100)    NOT NULL,
    middle_name         VARCHAR(100),
    last_name           VARCHAR(100)    NOT NULL,
    second_last_name    VARCHAR(100),
    birth_date          DATE,
    address             VARCHAR(280),
    phone               VARCHAR(30),
    email               VARCHAR(180),
    status              VARCHAR(20)     NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive', 'graduated', 'suspended')),
    CONSTRAINT uq_student_doc UNIQUE (document_type, document_number),
    CONSTRAINT fk_student_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- -------------------------------------------------------------
-- TABLA: student_guardian  (relación estudiante ↔ acudiente)
-- -------------------------------------------------------------
CREATE TABLE student_guardian (
    student_id      INT             NOT NULL,
    guardian_id     INT             NOT NULL,
    relationship    VARCHAR(100)
                    CHECK (relationship IN ('mother','father','guardian','grandmother','grandfather','uncle','aunt','other') ),
    primary_contact BOOLEAN         NOT NULL DEFAULT FALSE,
    PRIMARY KEY (student_id, guardian_id),
    CONSTRAINT fk_sg_student
        FOREIGN KEY (student_id) REFERENCES students (student_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_sg_guardian
        FOREIGN KEY (guardian_id) REFERENCES guardians (guardian_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);


-- -------------------------------------------------------------
-- TABLA: user_sessions
-- -------------------------------------------------------------
CREATE TABLE user_sessions (
    session_id      INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         INT             NOT NULL,
    token           VARCHAR(255)    NOT NULL UNIQUE,
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(255),
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMP       NOT NULL,
    closed_at       TIMESTAMP,
    CONSTRAINT fk_session_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);