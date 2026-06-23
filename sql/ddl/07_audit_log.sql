-- =============================================================
-- ARCHIVO 08_audit_log.sql
-- Tabla de auditoría del sistema
-- Sin dependencias de FK (tabla de log genérica)
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: audit_log
-- -------------------------------------------------------------
CREATE TABLE audit_log (
    id_audit            BIGINT          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_user             VARCHAR(180)    NOT NULL,
    action              VARCHAR(10)     NOT NULL
                        CHECK (action IN ('INSERT', 'UPDATE', 'DELETE', 'SELECT')),
    table_name          VARCHAR(100)    NOT NULL,
    affected_table      VARCHAR(100),
    action_type         VARCHAR(50),
    operation_timestamp TIMESTAMP       NOT NULL DEFAULT NOW(),
    old_value           TEXT,
    new_value           TEXT,
    user_name           VARCHAR(180),
    ip_address          VARCHAR(45)
);

-- Índices para consultas de auditoría frecuentes
CREATE INDEX idx_audit_table   ON audit_log (table_name);
CREATE INDEX idx_audit_ts      ON audit_log (operation_timestamp DESC);
CREATE INDEX idx_audit_user    ON audit_log (db_user);
CREATE INDEX idx_audit_action  ON audit_log (action);