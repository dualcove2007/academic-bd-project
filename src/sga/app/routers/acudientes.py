from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.db.database import get_db
from app.db.models import (
    Student, StudentGuardian, Guardian, Enrollment, AcademicLoad, Schedule,
    Attendance, GradeRecord, Activity, Observador, Subject,
    Grade, AcademicPeriod, Teacher
)
from app.core.security import require_rol

router = APIRouter(prefix="/acudientes", tags=["Acudientes"])


async def get_acudiente_guardian(db: AsyncSession, user_id: int) -> Guardian | None:
    result = await db.execute(select(Guardian).where(Guardian.user_id == user_id))
    return result.scalar_one_or_none()


async def get_acudiente_students(db: AsyncSession, guardian_id: int):
    """Devuelve los estudiantes vinculados a un guardian via student_guardian"""
    result = await db.execute(
        select(Student, StudentGuardian.parentesco)
        .join(StudentGuardian, StudentGuardian.student_id == Student.student_id)
        .where(StudentGuardian.guardian_id == guardian_id)
    )
    return result.all()


# ─────────────────────────────────────────
# MIS ESTUDIANTES
# ─────────────────────────────────────────
@router.get("/mis-estudiantes")
async def mis_estudiantes(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("acudiente", "admin"))
):
    guardian = await get_acudiente_guardian(db, current_user["user_id"])
    if not guardian:
        return []

    rows = await get_acudiente_students(db, guardian.guardian_id)
    if not rows:
        return []

    student_ids = [r[0].student_id for r in rows]
    parentesco_map = {r[0].student_id: r[1] for r in rows}

    enrollments_map = {}
    enr_result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id.in_(student_ids),
            Enrollment.status.in_(["active", "completed"])
        )
    )
    for e in enr_result.scalars().all():
        if e.student_id not in enrollments_map:
            enrollments_map[e.student_id] = e

    grade_ids = list(set(e.grade_id for e in enrollments_map.values()))
    grades_map = {}
    if grade_ids:
        res = await db.execute(select(Grade).where(Grade.grade_id.in_(grade_ids)))
        for g in res.scalars().all():
            grades_map[g.grade_id] = g.name

    output = []
    for s, _ in rows:
        enr = enrollments_map.get(s.student_id)
        grado = grades_map.get(enr.grade_id, "Sin grado") if enr else "Sin matricula"
        output.append({
            "id": s.student_id,
            "nombre": f"{s.first_name} {s.last_name}",
            "documento": s.document_number,
            "grado": grado,
            "grado_id": enr.grade_id if enr else None,
            "parentesco": parentesco_map.get(s.student_id, "Tutor"),
        })
    return output


# ─────────────────────────────────────────
# NOTAS
# ─────────────────────────────────────────
@router.get("/notas/{student_id}")
async def ver_notas_estudiante(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("acudiente", "admin"))
):
    guardian = await get_acudiente_guardian(db, current_user["user_id"])
    if not guardian and current_user["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Acudiente no encontrado")

    if current_user["rol"] != "admin" and guardian:
        rows = await get_acudiente_students(db, guardian.guardian_id)
        if not any(r[0].student_id == student_id for r in rows):
            raise HTTPException(status_code=403, detail="Este estudiante no esta asignado a usted")

    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.status.in_(["active", "completed"])
        ).order_by(Enrollment.enrollment_id.desc()).limit(1)
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        return {"materias": [], "promedio": 0}

    records = (await db.execute(
        select(GradeRecord).where(GradeRecord.enrollment_id == enrollment.enrollment_id)
    )).scalars().all()

    if not records:
        return {"materias": [], "promedio": 0}

    activity_ids = list(set(r.activity_id for r in records))
    activities_map = {}
    if activity_ids:
        res = await db.execute(select(Activity).where(Activity.activity_id.in_(activity_ids)))
        for a in res.scalars().all():
            activities_map[a.activity_id] = a

    load_ids = list(set(a.academic_load_id for a in activities_map.values()))
    loads_map = {}
    if load_ids:
        res = await db.execute(select(AcademicLoad).where(AcademicLoad.academic_load_id.in_(load_ids)))
        for l in res.scalars().all():
            loads_map[l.academic_load_id] = l

    subject_ids = list(set(l.subject_id for l in loads_map.values()))
    teacher_ids = list(set(l.teacher_id for l in loads_map.values()))
    subjects_map = {}
    teachers_map = {}
    if subject_ids:
        res = await db.execute(select(Subject).where(Subject.subject_id.in_(subject_ids)))
        for s in res.scalars().all():
            subjects_map[s.subject_id] = s
    if teacher_ids:
        res = await db.execute(select(Teacher).where(Teacher.teacher_id.in_(teacher_ids)))
        for t in res.scalars().all():
            teachers_map[t.teacher_id] = t

    subjects_data = {}
    for r in records:
        activity = activities_map.get(r.activity_id)
        if not activity: continue
        load = loads_map.get(activity.academic_load_id)
        if not load: continue
        subject = subjects_map.get(load.subject_id)
        teacher = teachers_map.get(load.teacher_id)
        nombre = subject.name if subject else "N/A"
        if nombre not in subjects_data:
            subjects_data[nombre] = {
                "materia": nombre,
                "docente": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
                "promedio": 0.0,
                "actividades": [],
            }
        subjects_data[nombre]["actividades"].append({
            "actividad": activity.name,
            "porcentaje": float(activity.percentage),
            "calificacion": float(r.score),
        })

    for s in subjects_data.values():
        acts = s["actividades"]
        if acts:
            s["promedio"] = round(sum(a["calificacion"] for a in acts) / len(acts), 2)

    return {
        "materias": list(subjects_data.values()),
        "promedio": round(sum(s["promedio"] for s in subjects_data.values()) / len(subjects_data), 2) if subjects_data else 0,
    }


# ─────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────
@router.get("/asistencia/{student_id}")
async def ver_asistencia_estudiante(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("acudiente", "admin"))
):
    guardian = await get_acudiente_guardian(db, current_user["user_id"])
    if not guardian and current_user["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Acudiente no encontrado")
    if current_user["rol"] != "admin" and guardian:
        rows = await get_acudiente_students(db, guardian.guardian_id)
        if not any(r[0].student_id == student_id for r in rows):
            raise HTTPException(status_code=403, detail="Este estudiante no esta asignado a usted")

    result = await db.execute(select(Enrollment).where(Enrollment.student_id == student_id))
    enrollments = result.scalars().all()

    registros = []
    JUST = {"presente", "present", "excusado", "excused", "justified", "justificada"}
    AUS = {"ausente", "absent"}
    TAR = {"tarde", "late"}

    for e in enrollments:
        att_result = await db.execute(select(Attendance).where(Attendance.enrollment_id == e.enrollment_id))
        for a in att_result.scalars().all():
            schedule = (await db.execute(select(Schedule).where(Schedule.schedule_id == a.schedule_id))).scalar_one_or_none()
            if not schedule: continue
            load = (await db.execute(select(AcademicLoad).where(AcademicLoad.academic_load_id == schedule.academic_load_id))).scalar_one_or_none()
            if not load: continue
            subject = (await db.execute(select(Subject).where(Subject.subject_id == load.subject_id))).scalar_one_or_none()
            sl = (a.attendance_status or "").strip().lower()
            estado_str = "justificada" if sl in JUST else "sin_justificar"
            registros.append({
                "id": a.attendance_id, "fecha": str(a.attendance_date),
                "materia": subject.name if subject else "N/A",
                "tipo_falta": a.attendance_status or "", "estado": estado_str,
                "observacion": a.comments or "",
            })
    return registros


# ─────────────────────────────────────────
# OBSERVADOR
# ─────────────────────────────────────────
@router.get("/observador/{student_id}")
async def ver_observador_estudiante(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("acudiente", "admin"))
):
    guardian = await get_acudiente_guardian(db, current_user["user_id"])
    if not guardian and current_user["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Acudiente no encontrado")
    if current_user["rol"] != "admin" and guardian:
        rows = await get_acudiente_students(db, guardian.guardian_id)
        if not any(r[0].student_id == student_id for r in rows):
            raise HTTPException(status_code=403, detail="Este estudiante no esta asignado a usted")

    result = await db.execute(select(Observador).where(Observador.estudiante_id == student_id))
    records = result.scalars().all()

    teacher_ids = list(set(r.docente_id for r in records if r.docente_id))
    teachers_map = {}
    if teacher_ids:
        res = await db.execute(select(Teacher).where(Teacher.teacher_id.in_(teacher_ids)))
        for t in res.scalars().all():
            teachers_map[t.teacher_id] = t

    output = []
    for obs in records:
        t = teachers_map.get(obs.docente_id)
        output.append({
            "id": obs.id, "tipo": obs.tipo, "descripcion": obs.descripcion,
            "fecha": str(obs.fecha), "reportado_por": f"{t.first_name} {t.last_name}" if t else "Docente",
        })
    return output
