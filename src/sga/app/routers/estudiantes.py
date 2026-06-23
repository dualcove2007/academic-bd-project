from fastapi import APIRouter, Depends, HTTPException
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.db.database import get_db
from app.db.models import (
    Student, Enrollment, AcademicLoad, Schedule, Attendance,
    GradeRecord, Activity, Observador, Subject, User,
    Grade, AcademicPeriod, Teacher, Classroom
)
from app.core.security import require_rol

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])

async def get_student_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return student


def _slot_index(t):
    h = t.hour + t.minute / 60
    if 6 <= h < 7: return 0
    if 7 <= h < 8: return 1
    if 8 <= h < 9: return 2
    if 9 <= h < 10: return 3
    if 10 <= h < 11: return 4
    if 11 <= h < 12: return 5
    return 6


TIME_SLOTS = [
    ("6:00-7:00", 6, 0, 7, 0),
    ("7:00-8:00", 7, 0, 8, 0),
    ("8:00-9:00", 8, 0, 9, 0),
    ("9:00-10:00", 9, 0, 10, 0),
    ("10:00-11:00", 10, 0, 11, 0),
    ("11:00-12:00", 11, 0, 12, 0),
    ("12:00-13:00", 12, 0, 13, 0),
]
DAY_MAP = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4}
DAY_KEYS = ["lunes", "martes", "miercoles", "jueves", "viernes"]
JUSTIFICADA_STATUSES = {"presente", "present", "excusado", "excused", "justified", "justificada"}
AUSENTE_STATUSES = {"ausente", "absent"}
TARDE_STATUSES = {"tarde", "late"}
STATUS_ES_FALTA = AUSENTE_STATUSES | TARDE_STATUSES


# ─────────────────────────────────────────
# MATRÍCULA
# ─────────────────────────────────────────
@router.get("/mi-matricula")
async def mi_matricula(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    student = await get_student_by_user(db, current_user["user_id"])
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.student_id,
            Enrollment.status == "active"
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="No tienes matrícula activa")

    grade = (await db.execute(
        select(Grade).where(Grade.grade_id == enrollment.grade_id)
    )).scalar_one_or_none()
    period = (await db.execute(
        select(AcademicPeriod).where(AcademicPeriod.period_id == enrollment.period_id)
    )).scalar_one_or_none()

    return {
        "id": enrollment.enrollment_id,
        "periodo": period.name if period else str(enrollment.period_id),
        "grado": grade.name if grade else "",
        "sede": "Sede Principal",
        "estado": enrollment.status == "active",
    }


# ─────────────────────────────────────────
# HORARIO
# ─────────────────────────────────────────
@router.get("/horario")
async def mi_horario(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    student = await get_student_by_user(db, current_user["user_id"])
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.student_id,
            Enrollment.status == "active"
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="No tienes matrícula activa")

    grade = (await db.execute(
        select(Grade).where(Grade.grade_id == enrollment.grade_id)
    )).scalar_one_or_none()

    loads = (await db.execute(
        select(AcademicLoad).where(AcademicLoad.grade_id == grade.grade_id)
    )).scalars().all()

    if not loads:
        return []

    load_ids = [l.academic_load_id for l in loads]
    subject_ids = list(set(l.subject_id for l in loads))
    teacher_ids = list(set(l.teacher_id for l in loads))

    subjects_map = {}
    if subject_ids:
        res = await db.execute(select(Subject).where(Subject.subject_id.in_(subject_ids)))
        for s in res.scalars().all():
            subjects_map[s.subject_id] = s

    teachers_map = {}
    if teacher_ids:
        res = await db.execute(select(Teacher).where(Teacher.teacher_id.in_(teacher_ids)))
        for t in res.scalars().all():
            teachers_map[t.teacher_id] = t

    all_schedules = (await db.execute(
        select(Schedule).where(Schedule.academic_load_id.in_(load_ids))
    )).scalars().all()

    classroom_ids = list(set(s.classroom_id for s in all_schedules if s.classroom_id))
    classrooms_map = {}
    if classroom_ids:
        res = await db.execute(select(Classroom).where(Classroom.classroom_id.in_(classroom_ids)))
        for c in res.scalars().all():
            classrooms_map[c.classroom_id] = c

    schedules_by_load = {}
    for s in all_schedules:
        schedules_by_load.setdefault(s.academic_load_id, []).append(s)

    grid = {}
    for l in loads:
        subject = subjects_map.get(l.subject_id)
        teacher = teachers_map.get(l.teacher_id)
        for s in schedules_by_load.get(l.academic_load_id, []):
            classroom = classrooms_map.get(s.classroom_id)
            dia = DAY_MAP.get(s.day_of_week.strip().lower(), 0)
            blq = _slot_index(s.start_time)
            if blq not in grid:
                grid[blq] = {"hora": TIME_SLOTS[blq][0], "lunes": None, "martes": None, "miercoles": None, "jueves": None, "viernes": None}
            grid[blq][DAY_KEYS[dia]] = {
                "materia": subject.name if subject else "N/A",
                "docente": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
                "salon": classroom.name if classroom else "N/A",
                "estado": "",
            }

    return [grid[i] for i in sorted(grid.keys())]


# ─────────────────────────────────────────
# NOTAS
# ─────────────────────────────────────────
@router.get("/notas")
async def mis_notas(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    student = await get_student_by_user(db, current_user["user_id"])
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.student_id,
            Enrollment.status == "active"
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        return []

    records = (await db.execute(
        select(GradeRecord).where(GradeRecord.enrollment_id == enrollment.enrollment_id)
    )).scalars().all()

    if not records:
        return []

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
    if subject_ids:
        res = await db.execute(select(Subject).where(Subject.subject_id.in_(subject_ids)))
        for s in res.scalars().all():
            subjects_map[s.subject_id] = s

    teachers_map = {}
    if teacher_ids:
        res = await db.execute(select(Teacher).where(Teacher.teacher_id.in_(teacher_ids)))
        for t in res.scalars().all():
            teachers_map[t.teacher_id] = t

    subjects_data = {}
    for r in records:
        activity = activities_map.get(r.activity_id)
        if not activity:
            continue
        load = loads_map.get(activity.academic_load_id)
        if not load:
            continue
        subject = subjects_map.get(load.subject_id)
        teacher = teachers_map.get(load.teacher_id)

        nombre_materia = subject.name if subject else "N/A"
        if nombre_materia not in subjects_data:
            subjects_data[nombre_materia] = {
                "materia": nombre_materia,
                "docente": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
                "carga_horaria": subject.weekly_hours if subject else 0,
                "promedio": 0.0,
                "actividades": [],
            }
        subjects_data[nombre_materia]["actividades"].append({
            "actividad": activity.name,
            "porcentaje": float(activity.percentage),
            "fecha_entrega": str(activity.activity_date) if activity.activity_date else "",
            "estado": "calificado",
            "calificacion": float(r.score),
        })

    for s in subjects_data.values():
        acts = s["actividades"]
        if acts:
            s["promedio"] = round(sum(a["calificacion"] for a in acts) / len(acts), 2)

    return list(subjects_data.values())


# ─────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────
@router.get("/asistencia")
async def mi_asistencia(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    student = await get_student_by_user(db, current_user["user_id"])
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.student_id,
            Enrollment.status == "active"
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        return []

    attendance_records = (await db.execute(
        select(Attendance).where(Attendance.enrollment_id == enrollment.enrollment_id)
    )).scalars().all()

    if not attendance_records:
        return []

    schedule_ids = list(set(a.schedule_id for a in attendance_records))
    schedules_map = {}
    if schedule_ids:
        res = await db.execute(select(Schedule).where(Schedule.schedule_id.in_(schedule_ids)))
        for s in res.scalars().all():
            schedules_map[s.schedule_id] = s

    load_ids = list(set(s.academic_load_id for s in schedules_map.values()))
    loads_map = {}
    if load_ids:
        res = await db.execute(select(AcademicLoad).where(AcademicLoad.academic_load_id.in_(load_ids)))
        for l in res.scalars().all():
            loads_map[l.academic_load_id] = l

    subject_ids = list(set(l.subject_id for l in loads_map.values()))
    subjects_map = {}
    if subject_ids:
        res = await db.execute(select(Subject).where(Subject.subject_id.in_(subject_ids)))
        for s in res.scalars().all():
            subjects_map[s.subject_id] = s

    registros = []
    for a in attendance_records:
        schedule = schedules_map.get(a.schedule_id)
        if not schedule:
            continue
        load = loads_map.get(schedule.academic_load_id)
        if not load:
            continue
        subject = subjects_map.get(load.subject_id)

        status_lower = (a.attendance_status or "").strip().lower()

        if status_lower in JUSTIFICADA_STATUSES:
            estado_str = "justificada"
        elif status_lower in AUSENTE_STATUSES:
            estado_str = "sin_justificar"
        elif status_lower in TARDE_STATUSES:
            estado_str = "sin_justificar"
        else:
            estado_str = "sin_justificar"

        registros.append({
            "id": a.attendance_id,
            "fecha": str(a.attendance_date),
            "materia": subject.name if subject else "N/A",
            "tipo_falta": a.attendance_status or "",
            "estado": estado_str,
            "observacion": a.comments or "",
        })

    return registros


# ─────────────────────────────────────────
# BOLETÍN
# ─────────────────────────────────────────
@router.get("/boletin")
async def mi_boletin(
    periodo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    student = await get_student_by_user(db, current_user["user_id"])
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.student_id,
            Enrollment.status == "active"
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="No tienes matrícula activa")

    grade_id = enrollment.grade_id

    records = (await db.execute(
        select(GradeRecord).where(GradeRecord.enrollment_id == enrollment.enrollment_id)
    )).scalars().all()

    activity_ids = list(set(r.activity_id for r in records)) if records else []
    activities_map = {}
    grades_load_ids = set()
    if activity_ids:
        res = await db.execute(select(Activity).where(Activity.activity_id.in_(activity_ids)))
        for a in res.scalars().all():
            activities_map[a.activity_id] = a
            grades_load_ids.add(a.academic_load_id)

    attendance_records = (await db.execute(
        select(Attendance).where(Attendance.enrollment_id == enrollment.enrollment_id)
    )).scalars().all()

    att_schedule_ids = list(set(a.schedule_id for a in attendance_records)) if attendance_records else []
    att_schedules_map = {}
    if att_schedule_ids:
        res = await db.execute(select(Schedule).where(Schedule.schedule_id.in_(att_schedule_ids)))
        for s in res.scalars().all():
            att_schedules_map[s.schedule_id] = s

    att_load_ids = set(s.academic_load_id for s in att_schedules_map.values())

    all_load_ids = list(grades_load_ids | att_load_ids)
    loads_map = {}
    if all_load_ids:
        res = await db.execute(select(AcademicLoad).where(AcademicLoad.academic_load_id.in_(all_load_ids)))
        for l in res.scalars().all():
            loads_map[l.academic_load_id] = l

    all_subject_ids = list(set(l.subject_id for l in loads_map.values()))
    all_teacher_ids = list(set(l.teacher_id for l in loads_map.values()))

    subjects_map = {}
    if all_subject_ids:
        res = await db.execute(select(Subject).where(Subject.subject_id.in_(all_subject_ids)))
        for s in res.scalars().all():
            subjects_map[s.subject_id] = s

    teachers_map = {}
    if all_teacher_ids:
        res = await db.execute(select(Teacher).where(Teacher.teacher_id.in_(all_teacher_ids)))
        for t in res.scalars().all():
            teachers_map[t.teacher_id] = t

    fallas_por_materia = {}
    for a in attendance_records:
        schedule = att_schedules_map.get(a.schedule_id)
        if not schedule:
            continue
        load = loads_map.get(schedule.academic_load_id)
        if not load:
            continue
        status_lower = (a.attendance_status or "").strip().lower()
        if status_lower in STATUS_ES_FALTA:
            subj = subjects_map.get(load.subject_id)
            if subj:
                fallas_por_materia[subj.name] = fallas_por_materia.get(subj.name, 0) + 1

    materias_dict = {}
    for r in records:
        activity = activities_map.get(r.activity_id)
        if not activity:
            continue
        load = loads_map.get(activity.academic_load_id)
        if not load:
            continue
        subject = subjects_map.get(load.subject_id)
        teacher = teachers_map.get(load.teacher_id)

        nombre_materia = subject.name if subject else "N/A"
        if nombre_materia not in materias_dict:
            materias_dict[nombre_materia] = {
                "notas": [],
                "docente": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
            }
        materias_dict[nombre_materia]["notas"].append(
            float(r.score) * float(activity.percentage) / 100
        )

    boletin = []
    for materia, datos in materias_dict.items():
        nota_final = round(sum(datos["notas"]), 2)
        nivel = (
            "Superior" if nota_final >= 4.6 else
            "Alto" if nota_final >= 4.0 else
            "Básico" if nota_final >= 3.0 else
            "Bajo"
        )
        boletin.append({
            "materia": materia,
            "docente": datos["docente"],
            "fallas": str(fallas_por_materia.get(materia, 0)),
            "nivel_desempeno": nivel,
            "nota_final": nota_final,
        })

    total_est_result = await db.execute(
        select(Enrollment).where(
            Enrollment.grade_id == grade_id,
            Enrollment.status == "active"
        )
    )
    total_estudiantes = len(total_est_result.scalars().all())

    all_enrollments = (await db.execute(
        select(Enrollment).where(Enrollment.student_id == student.student_id)
    )).scalars().all()

    period_ids = list(set(e.period_id for e in all_enrollments if e.period_id))
    periodos_nombres = []
    if period_ids:
        res = await db.execute(select(AcademicPeriod).where(AcademicPeriod.period_id.in_(period_ids)))
        for p in res.scalars().all():
            periodos_nombres.append(p.name)

    historial = []
    for enr in all_enrollments:
        year = enr.enrollment_date.year if enr.enrollment_date else date.today().year
        if enr.period_id:
            p_res = await db.execute(
                select(AcademicPeriod).where(AcademicPeriod.period_id == enr.period_id)
            )
            p = p_res.scalar_one_or_none()
            label = p.name if p else str(enr.period_id)
        else:
            label = str(enr.period_id)
        historial.append({"titulo": f"Periodo {label}", "anio": year})

    return {
        "materias": boletin,
        "resumen": {
            "promedio": round(sum(m["nota_final"] for m in boletin) / len(boletin), 2) if boletin else 0,
            "puesto": 1,
            "total_estudiantes": total_estudiantes,
        },
        "periodos": periodos_nombres,
        "historial": historial if historial else [{"titulo": "Periodo actual", "anio": date.today().year}],
    }


# ─────────────────────────────────────────
# OBSERVADOR
# ─────────────────────────────────────────
@router.get("/observador")
async def mi_observador(
    periodo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    student = await get_student_by_user(db, current_user["user_id"])
    query = select(Observador).where(Observador.estudiante_id == student.student_id)
    if periodo:
        query = query.where(Observador.periodo == periodo)
    result = await db.execute(query)
    records = result.scalars().all()

    teacher_ids = list(set(r.docente_id for r in records if r.docente_id))
    teachers_map = {}
    if teacher_ids:
        res = await db.execute(select(Teacher).where(Teacher.teacher_id.in_(teacher_ids)))
        for t in res.scalars().all():
            teachers_map[t.teacher_id] = t

    output = []
    for obs in records:
        teacher = teachers_map.get(obs.docente_id)
        output.append({
            "id": obs.id,
            "tipo": obs.tipo,
            "descripcion": obs.descripcion,
            "fecha": str(obs.fecha),
            "reportado_por": f"{teacher.first_name} {teacher.last_name}" if teacher else "Docente",
            "compromiso": getattr(obs, "compromiso", "") or "",
            "estado_firma": getattr(obs, "estado_firma", "") or "Firma del Acudiente: ⌛ PENDIENTE",
        })
    return output
