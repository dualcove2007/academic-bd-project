-- =============================================================
-- ARCHIVO 07_announcements_learning.sql
-- Anuncios y actividades extracurriculares
-- Dependen de: institutions, campuses, users, courses,
--              academic_periods
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: announcements
-- -------------------------------------------------------------
CREATE TABLE academic.announcements (
    announcement_id     INT             GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    institution_id      INT             NOT NULL,
    campus_id           INT,
    created_by_user_id  INT             NOT NULL,
    title               VARCHAR(255)    NOT NULL,
    content             TEXT            NOT NULL,
    image_url VARCHAR(500),
    publication_date    DATE            NOT NULL DEFAULT CURRENT_DATE,
    expiration_date     DATE,
    status              VARCHAR(20)     NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive', 'archived')),
    CONSTRAINT fk_ann_institution
        FOREIGN KEY (institution_id) REFERENCES academic.institutions (institution_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_ann_campus
        FOREIGN KEY (campus_id) REFERENCES academic.campuses (campus_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_ann_user
        FOREIGN KEY (created_by_user_id) REFERENCES academic.users (user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_announcement_dates
    CHECK (
        expiration_date IS NULL
        OR expiration_date >= publication_date
    )
);

