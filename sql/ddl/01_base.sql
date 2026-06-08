-- =============================================================
-- ARCHIVO 01_base.sql
-- Tablas maestras sin dependencias externas
-- Sistema de Gestión Académica
-- =============================================================

-- Extensión para UUIDs si se requiere en el futuro
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -------------------------------------------------------------
-- TABLA: institutions
-- -------------------------------------------------------------
CREATE TABLE academic.institutions (
    institution_id  INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(180)    NOT NULL,
    tax_id          VARCHAR(50)     UNIQUE,
    address         VARCHAR(280)    NOT NULL,
    phone           VARCHAR(30),
    email           VARCHAR(180),
    logo_url        VARCHAR(500),
    flag_url        VARCHAR(500),
    shield_url      VARCHAR(500),
    banner_url      VARCHAR(500),
    slogan          VARCHAR(255),
    primary_color   VARCHAR(7),
    secondary_color VARCHAR(7),
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive'))
);

-- -------------------------------------------------------------
-- TABLA: roles
-- -------------------------------------------------------------
CREATE TABLE academic.roles (
    role_id     INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL UNIQUE
);

-- -------------------------------------------------------------
-- TABLA: grades  (niveles educativos, p.ej. Kinder, 1°, 2°…)
-- -------------------------------------------------------------
CREATE TABLE academic.grades (
    grade_id        INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    education_level VARCHAR(100)    NOT NULL
);

-- -------------------------------------------------------------
-- TABLA: subjects  (materias/asignaturas de catálogo)
-- -------------------------------------------------------------
CREATE TABLE academic.subjects (
    subject_id      INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(180)    NOT NULL,
    description     TEXT,
    weekly_hours    INT             NOT NULL DEFAULT 1 CHECK (weekly_hours > 0),
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive'))
);

-- -------------------------------------------------------------
-- TABLA: academic_periods
-- -------------------------------------------------------------
CREATE TABLE academic.academic_periods (
    period_id       INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(180)    NOT NULL,
    academic_year   INT             NOT NULL,
    start_date      DATE            NOT NULL,
    end_date        DATE            NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'closed')),
    CONSTRAINT chk_period_dates CHECK (end_date > start_date),
    CONSTRAINT uq_period UNIQUE (name, academic_year)
);

-- -------------------------------------------------------------
-- TABLA: guardians
-- -------------------------------------------------------------
CREATE TABLE academic.guardians (
    guardian_id     INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_type   VARCHAR(30)     NOT NULL,
    document_number VARCHAR(50)     NOT NULL,
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100)    NOT NULL,
    middle_name     VARCHAR(100),
    second_last_name VARCHAR(100),
    phone           VARCHAR(30),
    email           VARCHAR(180),
    address         VARCHAR(280),
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive')),
    CONSTRAINT uq_guardian_doc UNIQUE (document_type, document_number)
);