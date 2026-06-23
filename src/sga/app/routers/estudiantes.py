from fastapi import APIRouter, Depends, HTTPException
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.db.database import get_db
from app.db.models import (
    Student, Enrollment, AcademicLoad, Schedule, Attendance,
    GradeRecord, Activity, Observador, Subject, User,
    Course, AcademicPeriod, Teacher, Classroom, Grade
)
from app.core.security import require_rol

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])

async def get_student_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return student

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

    course = await db.execute(select(Course).where(Course.course_id == enrollment.course_id))
    course = course.scalar_one_or_none()
    period = await db.execute(select(AcademicPeriod).where(AcademicPeriod.period_id == enrollment.period_id))
    period = period.scalar_one_or_none()

    return {
        "id": enrollment.enrollment_id,
        "periodo": period.name if period else str(enrollment.period_id),
        "grado": course.name if course else "",
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

    course = await db.execute(select(Course).where(Course.course_id == enrollment.course_id))
    course = course.scalar_one_or_none()

    load_result = await db.execute(
        select(AcademicLoad).where(AcademicLoad.course_id == course.course_id)
    )
    loads = load_result.scalars().all()

    day_map = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4}
    time_slots = [
        ("7:00AM-7:55AM", 7, 0, 7, 55),
        ("7:55AM-8:50AM", 7, 55, 8, 50),
        ("8:50AM-9:45AM", 8, 50, 9, 45),
        ("10:15AM-11:10AM", 10, 15, 11, 10),
        ("11:10AM-12:05AM", 11, 10, 12, 5),
        ("12:05AM-1:00PM", 12, 5, 13, 0),
    ]
    def slot_index(t):
        h = t.hour + t.minute / 60
        if 7 <= h < 7.92: return 0
        if 7.92 <= h < 8.83: return 1
        if 8.83 <= h < 9.75: return 2
        if 10.25 <= h < 11.17: return 3
        if 11.17 <= h < 12.08: return 4
        return 5

    grid = {}
    for l in loads:
        subj = await db.execute(select(Subject).where(Subject.subject_id == l.subject_id))
        subject = subj.scalar_one_or_none()
        teacher = await db.execute(select(Teacher).where(Teacher.teacher_id == l.teacher_id))
        teacher = teacher.scalar_one_or_none()
        schedules = await db.execute(
            select(Schedule).where(Schedule.academic_load_id == l.academic_load_id)
        )
        for s in schedules.scalars().all():
            classroom = await db.execute(select(Classroom).where(Classroom.classroom_id == s.classroom_id))
            classroom = classroom.scalar_one_or_none()
            dia = day_map.get(s.day_of_week.strip().lower(), 0)
            blq = slot_index(s.start_time)
            if blq not in grid:
                grid[blq] = {"hora": time_slots[blq][0], "lunes": None, "martes": None, "miercoles": None, "jueves": None, "viernes": None}
            day_key = ["lunes","martes","miercoles","jueves","viernes"][dia]
            grid[blq][day_key] = {
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
        select(Enrollment).where(Enrollment.student_id == student.student_id)
    )
    enrollments = result.scalars().all()

    subjects_data = {}
    for e in enrollments:
        rec_result = await db.execute(
            select(GradeRecord).where(GradeRecord.enrollment_id == e.enrollment_id)
        )
        for r in rec_result.scalars().all():
            act = await db.execute(select(Activity).where(Activity.activity_id == r.activity_id))
            activity = act.scalar_one_or_none()
            if not activity:
                continue
            load = await db.execute(select(AcademicLoad).where(AcademicLoad.academic_load_id == activity.academic_load_id))
            load = load.scalar_one_or_none()
            subj = await db.execute(select(Subject).where(Subject.subject_id == load.subject_id))
            subject = subj.scalar_one_or_none()
            teacher = await db.execute(select(Teacher).where(Teacher.teacher_id == load.teacher_id))
            teacher = teacher.scalar_one_or_none()

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
        select(Enrollment).where(Enrollment.student_id == student.student_id)
    )
    enrollments = result.scalars().all()

    registros = []
    for e in enrollments:
        att_result = await db.execute(
            select(Attendance).where(Attendance.enrollment_id == e.enrollment_id)
        )
        for a in att_result.scalars().all():
            schedule = await db.execute(select(Schedule).where(Schedule.schedule_id == a.schedule_id))
            schedule = schedule.scalar_one_or_none()
            load = await db.execute(select(AcademicLoad).where(AcademicLoad.academic_load_id == schedule.academic_load_id))
            load = load.scalar_one_or_none()
            subj = await db.execute(select(Subject).where(Subject.subject_id == load.subject_id))
            subject = subj.scalar_one_or_none()

            estado_str = "sin_justificar"
            if a.attendance_status == "present" or a.attendance_status == "justified":
                estado_str = "justificada"
            elif a.attendance_status == "absent":
                estado_str = "sin_justificar"
            elif a.attendance_status == "late":
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
        select(Enrollment).where(Enrollment.student_id == student.student_id)
    )
    enrollments = result.scalars().all()

    materias_dict = {}
    for e in enrollments:
        rec_result = await db.execute(
            select(GradeRecord).where(GradeRecord.enrollment_id == e.enrollment_id)
        )
        for r in rec_result.scalars().all():
            act = await db.execute(select(Activity).where(Activity.activity_id == r.activity_id))
            activity = act.scalar_one_or_none()
            if not activity:
                continue
            load = await db.execute(select(AcademicLoad).where(AcademicLoad.academic_load_id == activity.academic_load_id))
            load = load.scalar_one_or_none()
            subj = await db.execute(select(Subject).where(Subject.subject_id == load.subject_id))
            subject = subj.scalar_one_or_none()
            teacher = await db.execute(select(Teacher).where(Teacher.teacher_id == load.teacher_id))
            teacher = teacher.scalar_one_or_none()

            nombre_materia = subject.name if subject else "N/A"
            if nombre_materia not in materias_dict:
                materias_dict[nombre_materia] = {
                    "notas": [],
                    "docente": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
                }
            materias_dict[nombre_materia]["notas"].append(float(r.score) * float(activity.percentage) / 100)

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
            "fallas": "N",
            "nivel_desempeno": nivel,
            "nota_final": nota_final,
        })

    total_est = await db.execute(select(Enrollment).where(Enrollment.course_id == enrollments[0].course_id if enrollments else 0))
    total_estudiantes = len(total_est.scalars().all()) if enrollments else 0

    return {
        "materias": boletin,
        "resumen": {
            "promedio": round(sum(m["nota_final"] for m in boletin) / len(boletin), 2) if boletin else 0,
            "puesto": 1,
            "total_estudiantes": total_estudiantes,
        },
        "periodos": [],
        "historial": [{"titulo": "Periodo actual", "anio": date.today().year}],
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

    output = []
    for obs in records:
        teacher = None
        if obs.docente_id:
            t_result = await db.execute(select(Teacher).where(Teacher.teacher_id == obs.docente_id))
            teacher = t_result.scalar_one_or_none()

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
