-- =============================================================
-- ARCHIVO 09_audit_triggers.sql
-- Función y disparadores automáticos de auditoría
-- Debe ejecutarse después de todos los archivos anteriores
-- =============================================================

-- -------------------------------------------------------------
-- FUNCIÓN GENÉRICA de auditoría (usada por todos los triggers)
-- -------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_audit_log()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (
            db_user, action, table_name, operation_timestamp, old_value, new_value
        ) VALUES (
            current_user,
            'DELETE',
            TG_TABLE_NAME,
            NOW(),
            row_to_json(OLD)::TEXT,
            NULL
        );
        RETURN OLD;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (
            db_user, action, table_name, operation_timestamp, old_value, new_value
        ) VALUES (
            current_user,
            'UPDATE',
            TG_TABLE_NAME,
            NOW(),
            row_to_json(OLD)::TEXT,
            row_to_json(NEW)::TEXT
        );
        RETURN NEW;

    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (
            db_user, action, table_name, operation_timestamp, old_value, new_value
        ) VALUES (
            current_user,
            'INSERT',
            TG_TABLE_NAME,
            NOW(),
            NULL,
            row_to_json(NEW)::TEXT
        );
        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$;

-- -------------------------------------------------------------
-- MACRO para crear triggers (ejecutar para cada tabla clave)
-- -------------------------------------------------------------
-- institutions
CREATE TRIGGER trg_audit_institutions
    AFTER INSERT OR UPDATE OR DELETE ON institutions
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

-- campuses
CREATE TRIGGER trg_audit_campuses
    AFTER INSERT OR UPDATE OR DELETE ON campuses
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

-- users
CREATE TRIGGER trg_audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

-- teachers
CREATE TRIGGER trg_audit_teachers
    AFTER INSERT OR UPDATE OR DELETE ON teachers
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

-- students
CREATE TRIGGER trg_audit_students
    AFTER INSERT OR UPDATE OR DELETE ON students
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

-- guardians
CREATE TRIGGER trg_audit_guardians
    AFTER INSERT OR UPDATE OR DELETE ON guardians
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

-- enrollments
CREATE TRIGGER trg_audit_enrollments
    AFTER INSERT OR UPDATE OR DELETE ON enrollments
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

-- attendance
CREATE TRIGGER trg_audit_attendance
    AFTER INSERT OR UPDATE OR DELETE ON attendance
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

-- academic_load
CREATE TRIGGER trg_audit_academic_load
    AFTER INSERT OR UPDATE OR DELETE ON academic_load
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log();


