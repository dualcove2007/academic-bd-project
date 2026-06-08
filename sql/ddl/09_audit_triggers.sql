-- =============================================================
-- ARCHIVO 09_audit_triggers.sql
-- Función y disparadores automáticos de auditoría
-- Debe ejecutarse después de todos los archivos anteriores
-- =============================================================

-- -------------------------------------------------------------
-- FUNCIÓN GENÉRICA de auditoría (usada por todos los triggers)
-- -------------------------------------------------------------
CREATE OR REPLACE FUNCTION academic.fn_audit_log()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO academic.audit_log (
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
        INSERT INTO academic.audit_log (
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
        INSERT INTO academic.audit_log (
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
    AFTER INSERT OR UPDATE OR DELETE ON academic.institutions
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- campuses
CREATE TRIGGER trg_audit_campuses
    AFTER INSERT OR UPDATE OR DELETE ON academic.campuses
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- users
CREATE TRIGGER trg_audit_users
    AFTER INSERT OR UPDATE OR DELETE ON academic.users
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- teachers
CREATE TRIGGER trg_audit_teachers
    AFTER INSERT OR UPDATE OR DELETE ON academic.teachers
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- students
CREATE TRIGGER trg_audit_students
    AFTER INSERT OR UPDATE OR DELETE ON academic.students
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- guardians
CREATE TRIGGER trg_audit_guardians
    AFTER INSERT OR UPDATE OR DELETE ON academic.guardians
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- enrollments
CREATE TRIGGER trg_audit_enrollments
    AFTER INSERT OR UPDATE OR DELETE ON academic.enrollments
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- grade_sheets
CREATE TRIGGER trg_audit_grade_sheets
    AFTER INSERT OR UPDATE OR DELETE ON academic.grade_sheets
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- grade_sheet_details
CREATE TRIGGER trg_audit_grade_sheet_details
    AFTER INSERT OR UPDATE OR DELETE ON academic.grade_sheet_details
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- attendance
CREATE TRIGGER trg_audit_attendance
    AFTER INSERT OR UPDATE OR DELETE ON academic.attendance
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- academic_load
CREATE TRIGGER trg_audit_academic_load
    AFTER INSERT OR UPDATE OR DELETE ON academic.academic_load
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- courses
CREATE TRIGGER trg_audit_courses
    AFTER INSERT OR UPDATE OR DELETE ON academic.courses
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- announcements
CREATE TRIGGER trg_audit_announcements
    AFTER INSERT OR UPDATE OR DELETE ON academic.announcements
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- remedial_exams
CREATE TRIGGER trg_audit_remedial_exams
    AFTER INSERT OR UPDATE OR DELETE ON academic.remedial_exams
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();

-- student_record
CREATE TRIGGER trg_audit_student_record
    AFTER INSERT OR UPDATE OR DELETE ON academic.student_record
    FOR EACH ROW EXECUTE FUNCTION academic.fn_audit_log();