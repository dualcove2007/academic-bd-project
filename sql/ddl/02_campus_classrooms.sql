-- =============================================================
-- ARCHIVO 02_campus_classrooms.sql
-- Campus y aulas — dependen de institutions
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: campuses
-- -------------------------------------------------------------
CREATE TABLE campuses (
    campus_id       INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    institution_id  INT             NOT NULL,
    name            VARCHAR(180)    NOT NULL,
    address         VARCHAR(280),
    phone           VARCHAR(30),
    email           VARCHAR(180),
    is_main         BOOLEAN         NOT NULL DEFAULT FALSE,
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive')),
    CONSTRAINT fk_campus_institution
        FOREIGN KEY (institution_id) REFERENCES institutions (institution_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE UNIQUE INDEX uq_main_campus
ON campuses (institution_id)
WHERE is_main = TRUE;


-- -------------------------------------------------------------
-- TABLA: classrooms
-- -------------------------------------------------------------
CREATE TABLE classrooms (
    classroom_id    INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campus_id       INT             NOT NULL,
    name            VARCHAR(100)    NOT NULL,
    capacity        INT             NOT NULL CHECK (capacity > 0),
    location        VARCHAR(180),
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive')),
    CONSTRAINT fk_classroom_campus
        FOREIGN KEY (campus_id) REFERENCES campuses (campus_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);