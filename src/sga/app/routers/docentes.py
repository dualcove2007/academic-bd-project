from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import date, datetime
from app.db.database import get_db
from app.db.models import (
    AcademicLoad, Attendance, Activity, GradeRecord,
    Observador, Teacher, Student, Enrollment, User,
    Schedule, Subject, Course, AcademicPeriod, Classroom, Grade
)
from app.core.security import require_rol
import uuid

router = APIRouter(prefix="/docentes", tags=["Docentes"])
only_docente = Depends(require_rol("docente", "admin"))

async def get_teacher_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(Teacher).where(Teacher.user_id == user_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return teacher

async def verificar_carga_de_docente(carga_id: int, db: AsyncSession, teacher_id: int):
    result = await db.execute(
        select(AcademicLoad).where(
            AcademicLoad.academic_load_id == carga_id,
            AcademicLoad.teacher_id == teacher_id,
        )
    )
    carga = result.scalar_one_or_none()
    if not carga:
        raise HTTPException(status_code=403, detail="Esta carga académica no le pertenece")
    return carga

async def verificar_actividad_de_docente(actividad_id: int, db: AsyncSession, teacher_id: int):
    result = await db.execute(
        select(Activity).join(AcademicLoad).where(
            Activity.activity_id == actividad_id,
            AcademicLoad.teacher_id == teacher_id,
        )
    )
    act = result.scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=403, detail="Esta actividad no le pertenece")
    return act

async def verificar_estudiante_de_docente(estudiante_id: int, db: AsyncSession, teacher_id: int):
    """Verify the student is enrolled in at least one course taught by this teacher."""
    result = await db.execute(
        select(Enrollment).join(AcademicLoad, AcademicLoad.course_id == Enrollment.course_id)
        .where(
            Enrollment.student_id == estudiante_id,
            AcademicLoad.teacher_id == teacher_id,
            Enrollment.status == "active",
        ).limit(1)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Este estudiante no está en sus cursos")
    return True

# ─────────────────────────────────────────
# CARGA ACADÉMICA DEL DOCENTE
# ─────────────────────────────────────────
@router.get("/mi-carga")
async def mi_carga_academica(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin"))
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    tid = teacher.teacher_id

    loads = (await db.execute(
        select(AcademicLoad).where(AcademicLoad.teacher_id == tid)
    )).scalars().all()

    if not loads:
        return []

    load_ids = [l.academic_load_id for l in loads]
    course_ids = list(set(l.course_id for l in loads))
    subject_ids = list(set(l.subject_id for l in loads))

    subjects_map = {}
    if subject_ids:
        res = await db.execute(select(Subject).where(Subject.subject_id.in_(subject_ids)))
        for s in res.scalars().all():
            subjects_map[s.subject_id] = s

    courses_map = {}
    grade_ids = []
    if course_ids:
        res = await db.execute(select(Course).where(Course.course_id.in_(course_ids)))
        for c in res.scalars().all():
            courses_map[c.course_id] = c
            if c.grade_id:
                grade_ids.append(c.grade_id)

    grades_map = {}
    if grade_ids:
        res = await db.execute(select(Grade).where(Grade.grade_id.in_(grade_ids)))
        for g in res.scalars().all():
            grades_map[g.grade_id] = g

    schedules_by_load = {}
    if load_ids:
        res = await db.execute(select(Schedule).where(Schedule.academic_load_id.in_(load_ids)))
        for sch in res.scalars().all():
            schedules_by_load.setdefault(sch.academic_load_id, []).append(sch)

    classroom_ids = []
    for schs in schedules_by_load.values():
        for sch in schs:
            if sch.classroom_id:
                classroom_ids.append(sch.classroom_id)
    classrooms_map = {}
    if classroom_ids:
        res = await db.execute(select(Classroom).where(Classroom.classroom_id.in_(list(set(classroom_ids)))))
        for cr in res.scalars().all():
            classrooms_map[cr.classroom_id] = cr

    enrollments_by_course = {}
    if course_ids:
        res = await db.execute(
            select(Enrollment).where(
                Enrollment.course_id.in_(course_ids),
                Enrollment.status == "active",
            )
        )
        for e in res.scalars().all():
            enrollments_by_course.setdefault(e.course_id, []).append(e)

    all_student_ids = []
    for enr_list in enrollments_by_course.values():
        for e in enr_list:
            all_student_ids.append(e.student_id)
    students_map = {}
    if all_student_ids:
        res = await db.execute(select(Student).where(Student.student_id.in_(list(set(all_student_ids)))))
        for st in res.scalars().all():
            students_map[st.student_id] = st

    day_map = {"monday":1,"tuesday":2,"wednesday":3,"thursday":4,"friday":5}

    output = []
    for l in loads:
        subject = subjects_map.get(l.subject_id)
        course = courses_map.get(l.course_id)
        grade = grades_map.get(course.grade_id) if course else None
        schedules = schedules_by_load.get(l.academic_load_id, [])
        enrollments = enrollments_by_course.get(l.course_id, []) if course else []

        students_list = []
        for e in enrollments:
            student = students_map.get(e.student_id)
            if student:
                students_list.append({
                    "id": student.student_id,
                    "nombre": f"{student.first_name} {student.last_name}",
                })

        grado_str = f"{grade.name} {course.name}" if grade and course else (course.name if course else "N/A")
        num_schedules = len(schedules)

        for s in schedules:
            classroom = classrooms_map.get(s.classroom_id)
            dia = day_map.get(s.day_of_week.strip().lower(), 1)
            hora_inicio = str(s.start_time)
            hora_fin = str(s.end_time)
            output.append({
                "id": l.academic_load_id,
                "materia_id": l.academic_load_id,
                "materia_nombre": subject.name if subject else "N/A",
                "grado": grado_str,
                "curso": course.name if course else "N/A",
                "dia_semana": dia,
                "salon": classroom.name if classroom else "",
                "nh_semanales": str(num_schedules),
                "estudiantes": students_list,
                "total_estudiantes": len(students_list),
                "hora_inicio": hora_inicio,
                "hora_fin": hora_fin,
            })

        if not schedules:
            output.append({
                "id": l.academic_load_id,
                "materia_id": l.academic_load_id,
                "materia_nombre": subject.name if subject else "N/A",
                "grado": grado_str,
                "curso": course.name if course else "N/A",
                "dia_semana": 1,
                "salon": "",
                "nh_semanales": "0",
                "estudiantes": students_list,
                "total_estudiantes": len(students_list),
                "hora_inicio": "",
                "hora_fin": "",
            })

    unique_inicios = sorted(set(
        e["hora_inicio"] for e in output if e["hora_inicio"]
    ))
    time_to_bloque = {t: i + 1 for i, t in enumerate(unique_inicios)}

    for e in output:
        e["bloque"] = time_to_bloque.get(e["hora_inicio"], 0) if e["hora_inicio"] else 0

    return output

# ─────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────
@router.get("/mi-carga/{carga_id}/estudiantes")
async def ver_estudiantes_carga(
    carga_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    await verificar_carga_de_docente(carga_id, db, teacher.teacher_id)

    enroll_result = await db.execute(
        select(Enrollment)
        .join(AcademicLoad, AcademicLoad.course_id == Enrollment.course_id)
        .where(AcademicLoad.academic_load_id == carga_id, Enrollment.status == "active")
    )
    enrollments = enroll_result.scalars().all()

    student_ids = list(set(e.student_id for e in enrollments))
    students_map = {}
    if student_ids:
        res = await db.execute(select(Student).where(Student.student_id.in_(student_ids)))
        for s in res.scalars().all():
            students_map[s.student_id] = s

    output = []
    for e in enrollments:
        student = students_map.get(e.student_id)
        output.append({
            "estudiante_id": e.student_id,
            "estudiante_nombre": f"{student.first_name} {student.last_name}" if student else "N/A",
            "enrollment_id": e.enrollment_id,
        })
    return output

@router.get("/asistencia/{carga_id}")
async def ver_asistencia_clase(
    carga_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    await verificar_carga_de_docente(carga_id, db, teacher.teacher_id)

    enroll_result = await db.execute(
        select(Enrollment)
        .join(AcademicLoad, AcademicLoad.course_id == Enrollment.course_id)
        .where(AcademicLoad.academic_load_id == carga_id, Enrollment.status == "active")
    )
    enrollments = enroll_result.scalars().all()

    all_schedules = (await db.execute(
        select(Schedule).where(Schedule.academic_load_id == carga_id)
    )).scalars().all()
    schedule_ids = [s.schedule_id for s in all_schedules]

    student_ids = list(set(e.student_id for e in enrollments))
    students_map = {}
    users_map = {}
    if student_ids:
        res = await db.execute(select(Student).where(Student.student_id.in_(student_ids)))
        for s in res.scalars().all():
            students_map[s.student_id] = s
            if s.user_id:
                u_res = await db.execute(select(User).where(User.user_id == s.user_id))
                u = u_res.scalar_one_or_none()
                if u:
                    users_map[s.student_id] = u

    enr_ids = [e.enrollment_id for e in enrollments]
    att_map = {}
    if schedule_ids and enr_ids:
        res = await db.execute(select(Attendance).where(
            Attendance.enrollment_id.in_(enr_ids),
            Attendance.schedule_id.in_(schedule_ids),
            Attendance.attendance_date == date.today(),
        ))
        for a in res.scalars().all():
            att_map[a.enrollment_id] = a

    output = []
    for e in enrollments:
        student = students_map.get(e.student_id)
        user = users_map.get(e.student_id)
        att = att_map.get(e.enrollment_id)
        output.append({
            "estudiante_id": e.student_id,
            "estudiante_nombre": f"{student.first_name} {student.last_name}" if student else "N/A",
            "estudiante_usuario": user.username if user else "",
            "estado": att.attendance_status if att else "",
            "observacion": att.comments or "" if att else "",
        })
    return output

@router.post("/asistencia", status_code=status.HTTP_201_CREATED)
async def registrar_asistencia(
    registros: list,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])

    carga_ids = list(set(
        r.get("carga_id") or r.get("academic_load_id") for r in registros
    ))
    for cid in carga_ids:
        await verificar_carga_de_docente(cid, db, teacher.teacher_id)

    schedules_by_load = {}
    for cid in carga_ids:
        res = await db.execute(select(Schedule).where(Schedule.academic_load_id == cid))
        schedules_by_load[cid] = res.scalars().all()

    guardados = 0
    for r in registros:
        carga_id = r.get("carga_id") or r.get("academic_load_id")
        estudiante_id = r.get("estudiante_id") or r.get("student_id")
        estado = r.get("estado") or r.get("attendance_status")
        observacion = r.get("observacion") or r.get("comments")

        enroll = (await db.execute(
            select(Enrollment)
            .join(AcademicLoad, AcademicLoad.course_id == Enrollment.course_id)
            .where(AcademicLoad.academic_load_id == carga_id, Enrollment.student_id == estudiante_id)
        )).scalar_one_or_none()

        schedules = schedules_by_load.get(carga_id, [])
        schedule = schedules[0] if schedules else None

        if not enroll or not schedule:
            continue

        att = (await db.execute(
            select(Attendance).where(
                Attendance.enrollment_id == enroll.enrollment_id,
                Attendance.schedule_id == schedule.schedule_id,
                Attendance.attendance_date == date.today(),
            )
        )).scalar_one_or_none()

        if att:
            att.attendance_status = estado
            att.comments = observacion
        else:
            att = Attendance(
                enrollment_id=enroll.enrollment_id,
                schedule_id=schedule.schedule_id,
                attendance_date=date.today(),
                attendance_status=estado,
                comments=observacion,
            )
            db.add(att)
        guardados += 1

    await db.flush()
    return {"mensaje": f"{guardados} registros guardados"}

# ─────────────────────────────────────────
# ACTIVIDADES
# ─────────────────────────────────────────
@router.get("/actividades/{materia_id}")
async def listar_actividades(
    materia_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    await verificar_carga_de_docente(materia_id, db, teacher.teacher_id)

    activities = (await db.execute(
        select(Activity).where(Activity.academic_load_id == materia_id)
    )).scalars().all()

    act_ids = [a.activity_id for a in activities]
    notas_map = set()
    if act_ids:
        res = await db.execute(
            select(GradeRecord.activity_id).where(GradeRecord.activity_id.in_(act_ids)).distinct()
        )
        for row in res:
            notas_map.add(row[0])

    output = []
    for a in activities:
        output.append({
            "id": a.activity_id,
            "nombre": a.name,
            "descripcion": a.description or "",
            "fecha_entrega": str(a.activity_date) if a.activity_date else "",
            "porcentaje": float(a.percentage),
            "tiene_notas": a.activity_id in notas_map,
        })
    return output

@router.post("/actividades", status_code=status.HTTP_201_CREATED)
async def crear_actividad(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    materia_id = data.get("materia_id") or data.get("academic_load_id")
    await verificar_carga_de_docente(materia_id, db, teacher.teacher_id)

    pct_val = data.get("porcentaje") if "porcentaje" in data else data.get("percentage")
    activity = Activity(
        academic_load_id=materia_id,
        name=data.get("nombre") or data.get("name"),
        description=data.get("descripcion") or data.get("description"),
        percentage=float(pct_val) if pct_val is not None else 0,
    )
    raw_date = data.get("fecha_entrega") or data.get("activity_date")
    if raw_date:
        try:
            activity.activity_date = date.fromisoformat(raw_date)
        except (ValueError, TypeError):
            pass

    db.add(activity)
    await db.flush()
    await db.refresh(activity)
    return {
        "id": activity.activity_id,
        "nombre": activity.name,
        "descripcion": activity.description or "",
        "fecha_entrega": str(activity.activity_date) if activity.activity_date else "",
        "porcentaje": float(activity.percentage),
        "tiene_notas": False,
    }

@router.put("/actividades/{activity_id}")
async def editar_actividad(
    activity_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    activity = await verificar_actividad_de_docente(activity_id, db, teacher.teacher_id)

    if "nombre" in data or "name" in data:
        activity.name = data.get("nombre") or data.get("name") or activity.name
    if "descripcion" in data or "description" in data:
        activity.description = data.get("descripcion") if "descripcion" in data else data.get("description")
    if "porcentaje" in data:
        activity.percentage = float(data["porcentaje"])
    elif "percentage" in data:
        activity.percentage = float(data["percentage"])
    if "fecha_entrega" in data or "activity_date" in data:
        raw = data.get("fecha_entrega") or data.get("activity_date")
        if raw:
            try:
                activity.activity_date = date.fromisoformat(raw)
            except (ValueError, TypeError):
                pass
        else:
            activity.activity_date = None

    await db.flush()
    await db.refresh(activity)
    return {
        "id": activity.activity_id,
        "nombre": activity.name,
        "descripcion": activity.description or "",
        "fecha_entrega": str(activity.activity_date) if activity.activity_date else "",
        "porcentaje": float(activity.percentage),
    }

@router.delete("/actividades/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_actividad(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    activity = await verificar_actividad_de_docente(activity_id, db, teacher.teacher_id)

    tiene_notas = (await db.execute(
        select(GradeRecord.grade_record_id).where(GradeRecord.activity_id == activity_id).limit(1)
    )).scalar_one_or_none()
    if tiene_notas:
        raise HTTPException(status_code=409, detail="No se puede eliminar: la actividad tiene notas registradas")

    db.delete(activity)

# ─────────────────────────────────────────
# NOTAS
# ─────────────────────────────────────────
@router.get("/notas/{activity_id}")
async def ver_notas_actividad(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    await verificar_actividad_de_docente(activity_id, db, teacher.teacher_id)

    records = (await db.execute(
        select(GradeRecord).where(GradeRecord.activity_id == activity_id)
    )).scalars().all()

    enr_ids = [r.enrollment_id for r in records]
    enrollments_map = {}
    student_ids = []
    if enr_ids:
        res = await db.execute(select(Enrollment).where(Enrollment.enrollment_id.in_(enr_ids)))
        for e in res.scalars().all():
            enrollments_map[e.enrollment_id] = e
            student_ids.append(e.student_id)

    students_map = {}
    if student_ids:
        res = await db.execute(select(Student).where(Student.student_id.in_(student_ids)))
        for s in res.scalars().all():
            students_map[s.student_id] = s

    output = []
    for r in records:
        enrollment = enrollments_map.get(r.enrollment_id)
        student = students_map.get(enrollment.student_id) if enrollment else None
        output.append({
            "id": r.grade_record_id,
            "estudiante_id": enrollment.student_id if enrollment else None,
            "valor": float(r.score),
            "estudiante_nombre": f"{student.first_name} {student.last_name}" if student else "N/A",
            "definitiva": float(r.score),
        })
    return output

@router.post("/notas", status_code=status.HTTP_201_CREATED)
async def registrar_notas(
    notas: list,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])

    act_ids = list(set(
        n.get("actividad_id") or n.get("activity_id") for n in notas
    ))
    for aid in act_ids:
        await verificar_actividad_de_docente(aid, db, teacher.teacher_id)

    guardados = 0
    for n in notas:
        estudiante_id = n.get("estudiante_id") or n.get("student_id")
        actividad_id = n.get("actividad_id") or n.get("activity_id")
        valor_raw = n.get("valor") if "valor" in n else n.get("score")
        try:
            valor = float(valor_raw) if valor_raw not in (None, "") else None
        except (ValueError, TypeError):
            continue

        enroll = (await db.execute(
            select(Enrollment).join(AcademicLoad, AcademicLoad.course_id == Enrollment.course_id)
            .join(Activity, Activity.academic_load_id == AcademicLoad.academic_load_id)
            .where(
                Enrollment.student_id == estudiante_id,
                Activity.activity_id == actividad_id,
            )
        )).scalar_one_or_none()
        if not enroll:
            continue

        record = (await db.execute(
            select(GradeRecord).where(
                GradeRecord.activity_id == actividad_id,
                GradeRecord.enrollment_id == enroll.enrollment_id,
            )
        )).scalar_one_or_none()

        if valor is not None:
            if record:
                record.score = valor
                record.record_date = date.today()
            else:
                record = GradeRecord(
                    activity_id=actividad_id,
                    enrollment_id=enroll.enrollment_id,
                    score=valor,
                    record_date=date.today(),
                )
                db.add(record)
            guardados += 1
        elif record:
            db.delete(record)
            guardados += 1

    await db.flush()
    return {"mensaje": f"{guardados} notas guardadas"}

@router.put("/notas/{nota_id}")
async def editar_nota(
    nota_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    record = (await db.execute(
        select(GradeRecord).where(GradeRecord.grade_record_id == nota_id)
    )).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    await verificar_actividad_de_docente(record.activity_id, db, teacher.teacher_id)

    if "valor" in data:
        record.score = float(data["valor"])
    elif "score" in data:
        record.score = float(data["score"])
    if "observacion" in data or "comments" in data:
        record.comments = data.get("observacion") or data.get("comments")
    await db.flush()
    await db.refresh(record)
    return {
        "id": record.grade_record_id,
        "valor": float(record.score),
    }

# ─────────────────────────────────────────
# OBSERVADOR
# ─────────────────────────────────────────
TIPOS_PERMITIDOS = {"FELICITACION", "FALTA LEVE", "FALTA GRAVE", "COMPROMISO"}

@router.post("/observador", status_code=status.HTTP_201_CREATED)
async def registrar_anotacion(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin"))
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    estudiante_id = data.get("estudiante_id")
    tipo = (data.get("tipo") or "").strip().upper()
    descripcion = (data.get("descripcion") or "").strip()

    if not estudiante_id:
        raise HTTPException(status_code=422, detail="Se requiere estudiante_id")
    if not tipo or tipo not in TIPOS_PERMITIDOS:
        raise HTTPException(status_code=422, detail=f"Tipo inválido. Permitidos: {', '.join(sorted(TIPOS_PERMITIDOS))}")
    if not descripcion:
        raise HTTPException(status_code=422, detail="La descripción es obligatoria")

    student_exists = (await db.execute(
        select(Student.student_id).where(Student.student_id == int(estudiante_id))
    )).scalar_one_or_none()
    if not student_exists:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    periodo_str = data.get("periodo", "")

    observador = Observador(
        id=str(uuid.uuid4()),
        docente_id=teacher.teacher_id,
        estudiante_id=estudiante_id,
        tipo=tipo,
        descripcion=descripcion,
        periodo=periodo_str if periodo_str else "",
        fecha=datetime.utcnow(),
    )
    db.add(observador)
    await db.flush()
    await db.refresh(observador)
    return {
        "id": observador.id,
        "estudiante_id": observador.estudiante_id,
        "tipo": observador.tipo,
        "descripcion": observador.descripcion,
        "fecha": str(observador.fecha),
        "periodo": observador.periodo,
        "reportado_por": f"{teacher.first_name} {teacher.last_name}",
    }

@router.get("/observador/{estudiante_id}")
async def ver_observador_estudiante(
    estudiante_id: int,
    periodo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin")),
):
    teacher = await get_teacher_by_user(db, current_user["user_id"])
    await verificar_estudiante_de_docente(estudiante_id, db, teacher.teacher_id)

    query = select(Observador).where(Observador.estudiante_id == estudiante_id)
    if periodo:
        query = query.where(Observador.periodo == periodo)
    records = (await db.execute(query)).scalars().all()

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
            "estudiante_id": obs.estudiante_id,
            "tipo": obs.tipo,
            "descripcion": obs.descripcion,
            "fecha": str(obs.fecha),
            "periodo": obs.periodo,
            "reportado_por": f"{teacher.first_name} {teacher.last_name}" if teacher else "Docente",
        })
    return output
