from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, text
from sqlalchemy.exc import IntegrityError
from datetime import date, time
from typing import Optional
from app.db.database import get_db
from app.db.models import (
    User, Teacher, Student, Role, Subject,
    Enrollment, AcademicLoad, Grade,
    AcademicPeriod, Schedule, Classroom, Campus,
    GradeRecord, Activity, Attendance, Observador
)
from app.core.security import require_rol, hash_password

router = APIRouter(prefix="/admin", tags=["Administrador"])
only_admin = Depends(require_rol("admin"))

def full_name(u):
    parts = [u.first_name, u.middle_name or "", u.last_name, u.second_last_name or ""]
    return " ".join(p for p in parts if p).strip()

# ─────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────
@router.get("/usuarios")
async def listar_usuarios(
    rol: Optional[str] = None,
    estado: Optional[str] = None,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=only_admin
):
    query = select(User)
    role_map = {"admin": 1, "estudiante": 2, "docente": 3, "acudiente": 4}
    if rol and rol in role_map:
        query = query.where(User.role_id == role_map[rol])
    if estado:
        if estado in ("activo", "active"):
            query = query.where(User.status == "active")
        elif estado in ("inactivo", "inactive"):
            query = query.where(User.status != "active")
    if q:
        like = f"%{q}%"
        query = query.where(
            or_(User.first_name.ilike(like), User.middle_name.ilike(like),
                User.last_name.ilike(like), User.second_last_name.ilike(like),
                User.document_number.ilike(like), User.username.ilike(like))
        )
    result = await db.execute(query)
    users = result.scalars().all()

    output = []
    for u in users:
        role_name = {1: "admin", 2: "estudiante", 3: "docente", 4: "acudiente"}.get(u.role_id, "desconocido")
        output.append({
            "id": u.user_id,
            "username": u.username,
            "nombre_completo": full_name(u),
            "tipo_documento": u.document_type,
            "numero_documento": u.document_number,
            "correo": u.email or "",
            "telefono": u.phone or "",
            "rol": role_name,
            "estado": u.status == "active",
            "creado_en": str(u.last_login) if u.last_login else "",
        })
    return output

@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
async def crear_usuario(data: dict, db: AsyncSession = Depends(get_db), _=only_admin):
    username = data.get("username") or data.get("usuario")
    password = data.get("password") or data.get("contrasena")
    email = data.get("email") or data.get("correo")
    phone = data.get("telefono") or data.get("phone") or ""
    rol_str = data.get("rol") or "estudiante"
    role_id = {"admin": 1, "estudiante": 2, "docente": 3, "acudiente": 4}.get(rol_str, 2)
    doc_type = data.get("tipo_documento") or data.get("document_type") or "CC"
    doc_number = data.get("numero_documento") or data.get("document_number") or ""
    middle_name = ""
    second_last_name = ""
    first_name = ""
    last_name = ""
    full_name = data.get("nombre_completo") or ""
    parts = full_name.split()
    if len(parts) >= 1:
        first_name = data.get("first_name") or parts[0]
    if len(parts) == 2:
        last_name = parts[1]
    elif len(parts) == 3:
        last_name = parts[1]
        second_last_name = parts[2]
    elif len(parts) >= 4:
        middle_name = parts[1]
        last_name = parts[2]
        second_last_name = parts[3]

    existe = await db.execute(select(User).where(User.username == username))
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Usuario ya registrado")

    user = User(
        role_id=role_id,
        campus_id=1,
        username=username,
        password_hash=hash_password(password),
        document_type=doc_type,
        document_number=doc_number,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        second_last_name=second_last_name,
        email=email,
        phone=phone,
        status="active",
    )
    db.add(user)
    await db.flush()

    if role_id == 2:
        dup = await db.execute(
            select(Student).where(
                Student.document_type == doc_type,
                Student.document_number == doc_number
            )
        )
        existing = dup.scalar_one_or_none()
        if existing:
            if existing.user_id:
                raise HTTPException(status_code=400, detail=f"Ya existe un estudiante con documento {doc_type} {doc_number}")
            existing.user_id = user.user_id
        else:
            guardian_id = data.get("guardian_id") or data.get("acudiente_id") or None
            db.add(Student(
                user_id=user.user_id, document_type=doc_type,
                document_number=doc_number, first_name=first_name,
                middle_name=middle_name, last_name=last_name,
                second_last_name=second_last_name, email=email, phone=phone, status="active",
                guardian_id=int(guardian_id) if guardian_id else None,
            ))
    elif role_id == 3:
        dup = await db.execute(
            select(Teacher).where(
                Teacher.document_type == doc_type,
                Teacher.document_number == doc_number
            )
        )
        existing = dup.scalar_one_or_none()
        if existing:
            if existing.user_id:
                raise HTTPException(status_code=400, detail=f"Ya existe un docente con documento {doc_type} {doc_number}")
            existing.user_id = user.user_id
        else:
            db.add(Teacher(
                user_id=user.user_id, document_type=doc_type,
                document_number=doc_number, first_name=first_name,
                middle_name=middle_name, last_name=last_name,
                second_last_name=second_last_name, email=email, phone=phone, status="active",
            ))

    await db.flush()
    return {"mensaje": "Usuario creado", "id": user.user_id, "username": user.username}

@router.get("/usuarios/{user_id}")
async def obtener_usuario(user_id: int, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(User).where(User.user_id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    role_name = {1: "admin", 2: "estudiante", 3: "docente", 4: "acudiente"}.get(u.role_id, "desconocido")
    return {
        "id": u.user_id,
        "username": u.username,
        "nombre_completo": full_name(u),
        "tipo_documento": u.document_type,
        "numero_documento": u.document_number,
        "correo": u.email or "",
        "telefono": u.phone or "",
        "phone": u.phone or "",
        "rol": role_name,
        "estado": u.status == "active",
    }

@router.put("/usuarios/{user_id}")
async def editar_usuario(user_id: int, data: dict, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.get("tipo_documento"): user.document_type = data["tipo_documento"]
    if data.get("numero_documento"): user.document_number = data["numero_documento"]
    if data.get("correo") or data.get("email"): user.email = data.get("correo") or data["email"]
    if data.get("telefono") or data.get("phone"): user.phone = data.get("telefono") or data["phone"]
    if data.get("nombre_completo"):
        parts = data["nombre_completo"].split()
        if len(parts) >= 1: user.first_name = parts[0]
        if len(parts) == 2: user.last_name = parts[1]
        elif len(parts) == 3:
            user.last_name = parts[1]
            user.second_last_name = parts[2]
        elif len(parts) >= 4:
            user.middle_name = parts[1]
            user.last_name = parts[2]
            user.second_last_name = parts[3]
    password = data.get("password") or data.get("contrasena")
    if password:
        user.password_hash = hash_password(password)

    await db.flush()
    return {"mensaje": "Usuario actualizado"}

@router.patch("/usuarios/{user_id}/estado")
async def cambiar_estado(user_id: int, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.status = "inactive" if user.status == "active" else "active"
    await db.flush()
    return {"id": user.user_id, "estado": user.status == "active"}

@router.delete("/usuarios/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(user_id: int, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    await db.delete(user)

@router.patch("/usuarios/{user_id}/guardian")
async def asignar_acudiente(user_id: int, data: dict, db: AsyncSession = Depends(get_db), _=only_admin):
    """Asigna un acudiente a un estudiante"""
    guardian_id = data.get("guardian_id") or data.get("acudiente_id")
    if not guardian_id:
        raise HTTPException(status_code=422, detail="Se requiere guardian_id o acudiente_id")
    guardian = (await db.execute(select(User).where(User.user_id == int(guardian_id)))).scalar_one_or_none()
    if not guardian or guardian.role_id != 4:
        raise HTTPException(status_code=404, detail="Acudiente no encontrado")
    student = (await db.execute(select(Student).where(Student.user_id == user_id))).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    student.guardian_id = int(guardian_id)
    await db.flush()
    return {"mensaje": "Acudiente asignado", "estudiante_id": student.student_id, "guardian_id": student.guardian_id}

@router.get("/acudientes")
async def listar_acudientes(db: AsyncSession = Depends(get_db), _=only_admin):
    """Lista todos los acudientes registrados"""
    result = await db.execute(select(User).where(User.role_id == 4, User.status == "active"))
    users = result.scalars().all()
    return [{"user_id": u.user_id, "nombre": full_name(u), "username": u.username} for u in users]

# ─────────────────────────────────────────
# MATERIAS (subjects)
# ─────────────────────────────────────────
@router.get("/materias")
async def listar_materias(db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Subject))
    subjects = result.scalars().all()
    return [{"id": s.subject_id, "nombre": s.name, "codigo": s.subject_id, "descripcion": s.description or "", "horas": s.weekly_hours, "estado": s.status == "active"} for s in subjects]

@router.post("/materias")
async def crear_materia(data: dict, db: AsyncSession = Depends(get_db), _=only_admin):
    subject = Subject(
        name=data.get("nombre") or data.get("name"),
        description=data.get("descripcion") or data.get("description"),
        weekly_hours=data.get("weekly_hours", 1),
    )
    db.add(subject)
    await db.flush()
    await db.refresh(subject)
    return {"id": subject.subject_id, "nombre": subject.name}

@router.put("/materias/{subject_id}")
async def editar_materia(subject_id: int, data: dict, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Subject).where(Subject.subject_id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    if "nombre" in data or "name" in data:
        subject.name = data.get("nombre") or data.get("name")
    if "descripcion" in data or "description" in data:
        subject.description = data.get("descripcion") or data.get("description")
    if "weekly_hours" in data:
        subject.weekly_hours = int(data["weekly_hours"])
    await db.flush()
    return {"id": subject.subject_id, "nombre": subject.name}

@router.delete("/materias/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_materia(subject_id: int, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Subject).where(Subject.subject_id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    await db.delete(subject)

# ─────────────────────────────────────────
# MATRÍCULAS (enrollments)
# ─────────────────────────────────────────
@router.get("/matriculas")
async def listar_matriculas(db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Enrollment))
    enrollments = result.scalars().all()
    output = []
    for e in enrollments:
        s_result = await db.execute(select(Student).where(Student.student_id == e.student_id))
        student = s_result.scalar_one_or_none()
        user = None
        if student and student.user_id:
            u_result = await db.execute(select(User).where(User.user_id == student.user_id))
            user = u_result.scalar_one_or_none()
        grado_nombre = ""
        c_result = await db.execute(select(Grade).where(Grade.grade_id == e.grade_id))
        grade = c_result.scalar_one_or_none()
        if grade:
            grado_nombre = grade.name
        output.append({
            "id": e.enrollment_id,
            "usuario_id": student.user_id if student else None,
            "estudiante_id": e.student_id,
            "estudiante_nombre": f"{student.first_name} {student.last_name}" if student else "N/A",
            "nombre_completo": f"{student.first_name} {student.last_name}" if student else "N/A",
            "numero_documento": student.document_number if student else "",
            "grado": grado_nombre or f"{e.grade_id}",
            "periodo": e.period_id,
            "estado": e.status != "inactive",
        })
    return output

@router.post("/matriculas", status_code=status.HTTP_201_CREATED)
async def crear_matricula(data: dict, db: AsyncSession = Depends(get_db), _=only_admin):
    student_id = data.get("estudiante_id") or data.get("student_id")
    usuario_id = data.get("usuario_id") or data.get("user_id")
    if usuario_id:
        usuario_id = int(usuario_id)
    if not student_id and usuario_id:
        s_result = await db.execute(select(Student).where(Student.user_id == usuario_id))
        student = s_result.scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=400, detail="No hay registro de estudiante para ese usuario")
        student_id = student.student_id
    grade_id = int(data.get("grado_id") or data.get("grade_id") or 0)
    period_id = int(data.get("periodo_id") or data.get("period_id") or 0)
    if not period_id:
        p_result = await db.execute(select(AcademicPeriod).where(AcademicPeriod.status == "active").limit(1))
        active_period = p_result.scalar_one_or_none()
        if active_period:
            period_id = active_period.period_id
        else:
            p_result = await db.execute(select(AcademicPeriod).limit(1))
            first_period = p_result.scalar_one_or_none()
            period_id = first_period.period_id if first_period else 1
    if student_id:
        student_id = int(student_id)
    enrollment = Enrollment(
        student_id=student_id,
        grade_id=grade_id,
        period_id=period_id,
        enrollment_date=date.today(),
        status=data.get("status", "active"),
    )
    db.add(enrollment)
    await db.flush()
    return {"mensaje": "Matrícula creada", "id": enrollment.enrollment_id}

@router.patch("/matriculas/{enrollment_id}")
@router.patch("/matriculas/{enrollment_id}/finalizar")
async def finalizar_matricula(enrollment_id: int, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Enrollment).where(Enrollment.enrollment_id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    enrollment.status = "completed"
    await db.flush()
    return {"mensaje": "Matrícula finalizada"}

# ─────────────────────────────────────────
# CARGA ACADÉMICA
# ─────────────────────────────────────────
@router.get("/carga-academica")
async def listar_carga(db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(
        select(AcademicLoad).join(Teacher, AcademicLoad.teacher_id == Teacher.teacher_id)
        .where(Teacher.user_id.isnot(None))
    )
    loads = result.scalars().all()
    output = []
    for l in loads:
        t_result = await db.execute(select(Teacher).where(Teacher.teacher_id == l.teacher_id))
        teacher = t_result.scalar_one_or_none()
        s_result = await db.execute(select(Subject).where(Subject.subject_id == l.subject_id))
        subject = s_result.scalar_one_or_none()
        c_result = await db.execute(select(Grade).where(Grade.grade_id == l.grade_id))
        grade = c_result.scalar_one_or_none()
        sched_result = await db.execute(
            select(Schedule).where(Schedule.academic_load_id == l.academic_load_id)
        )
        schedules = sched_result.scalars().all()
        horario_str = ""
        salon_str = ""
        if schedules:
            horario_str = f"{schedules[0].start_time.strftime('%H:%M')} - {schedules[0].end_time.strftime('%H:%M')}"
            rev_map = {"Monday":"Lunes","Tuesday":"Martes","Wednesday":"Miércoles","Thursday":"Jueves","Friday":"Viernes"}
            dias_str = ", ".join(rev_map.get(s.day_of_week, s.day_of_week) for s in schedules)
            horario_str = f"{dias_str} | {horario_str}"
            if schedules[0].classroom_id:
                cr = await db.execute(select(Classroom).where(Classroom.classroom_id == schedules[0].classroom_id))
                classroom = cr.scalar_one_or_none()
                salon_str = classroom.name if classroom else ""
        output.append({
            "id": l.academic_load_id,
            "docente": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
            "docente_nombre": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
            "materia": subject.name if subject else "N/A",
            "materia_nombre": subject.name if subject else "N/A",
            "horario": horario_str,
            "grado": grade.name if grade else "N/A",
            "salon": salon_str,
        })
    return output

@router.post("/carga-academica", status_code=status.HTTP_201_CREATED)
async def crear_carga(data: dict, db: AsyncSession = Depends(get_db), _=only_admin):
    teacher_id = int(data.get("docente_id") or data.get("teacher_id") or 0)
    grade_id = int(data.get("grado_id") or data.get("grade_id") or 0)
    subject_id = int(data.get("materia_id") or data.get("subject_id") or 0)
    period_id = int(data.get("periodo_id") or data.get("period_id") or 0)
    if not period_id:
        p_result = await db.execute(select(AcademicPeriod).where(AcademicPeriod.status == "active").limit(1))
        active_period = p_result.scalar_one_or_none()
        if active_period:
            period_id = active_period.period_id
        else:
            p_result = await db.execute(select(AcademicPeriod).limit(1))
            first_period = p_result.scalar_one_or_none()
            period_id = first_period.period_id if first_period else 1
    classroom_id = int(data.get("classroom_id") or 1)
    hora_inicio = data.get("hora_inicio") or "06:00"
    hora_fin = data.get("hora_fin") or "07:00"
    dias = data.get("dias") or ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

    load = AcademicLoad(
        teacher_id=teacher_id, grade_id=grade_id,
        subject_id=subject_id, period_id=period_id,
    )
    db.add(load)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Esa combinación de docente, grado, materia y periodo ya existe")

    hi = time.fromisoformat(hora_inicio)
    hf = time.fromisoformat(hora_fin)
    dia_map = {"lunes":"Monday","martes":"Tuesday","miércoles":"Wednesday","jueves":"Thursday","viernes":"Friday"}
    for dia in dias if isinstance(dias, list) else dias.split(","):
        dia_en = dia_map.get(dia.strip().lower(), dia)
        db.add(Schedule(
            academic_load_id=load.academic_load_id,
            classroom_id=classroom_id,
            day_of_week=dia_en,
            start_time=hi,
            end_time=hf,
        ))
    await db.flush()
    return {"mensaje": "Carga creada", "id": load.academic_load_id}

@router.delete("/carga-academica/{academic_load_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_carga(academic_load_id: int, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(AcademicLoad).where(AcademicLoad.academic_load_id == academic_load_id))
    load = result.scalar_one_or_none()
    if not load:
        raise HTTPException(status_code=404, detail="Carga no encontrada")
    sched_result = await db.execute(
        select(Schedule).where(Schedule.academic_load_id == academic_load_id)
    )
    for s in sched_result.scalars().all():
        await db.delete(s)
    await db.delete(load)

@router.get("/horarios")
async def listar_horarios(_=only_admin):
    blocks = [
        (time(6, 0), time(7, 0)),
        (time(7, 0), time(8, 0)),
        (time(8, 0), time(9, 0)),
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(12, 0), time(13, 0)),
    ]
    return [
        {
            "id": i + 1,
            "nombre": f"{b[0].strftime('%H:%M')} - {b[1].strftime('%H:%M')}",
            "hora_inicio": b[0].strftime('%H:%M'),
            "hora_fin": b[1].strftime('%H:%M'),
        }
        for i, b in enumerate(blocks)
    ]

# ─────────────────────────────────────────
# LOOKUP ENDPOINTS (for selects)
# ─────────────────────────────────────────
@router.get("/roles")
async def listar_roles(db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Role))
    roles = result.scalars().all()
    role_map = {"Administrativo": "admin", "Docente": "docente", "Estudiante": "estudiante", "Acudiente": "acudiente"}
    return [{"role_id": r.role_id, "nombre": r.name, "rol": role_map.get(r.name, r.name.lower())} for r in roles]

@router.get("/docentes")
async def listar_docentes(db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Teacher).where(Teacher.user_id.isnot(None)))
    teachers = result.scalars().all()
    return [{"teacher_id": t.teacher_id, "nombre": f"{t.first_name} {t.last_name}"} for t in teachers]

@router.get("/grados")
async def listar_grados(db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Grade))
    grades = result.scalars().all()
    return [{
        "grade_id": g.grade_id,
        "nombre": g.name,
        "education_level": g.education_level,
        "capacidad_maxima": g.maximum_capacity,
        "anio": g.academic_year,
        "estado": g.status == "active"
    } for g in grades]

@router.get("/grados-capacidad")
async def listar_grados_capacidad(db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Grade))
    grades = result.scalars().all()
    output = []
    for g in grades:
        count_result = await db.execute(
            select(func.count(Enrollment.enrollment_id)).where(
                Enrollment.grade_id == g.grade_id,
                Enrollment.status == "completed"
            )
        )
        matriculados = count_result.scalar() or 0
        output.append({
            "grade_id": g.grade_id,
            "nombre": g.name,
            "capacidad_maxima": g.maximum_capacity,
            "matriculados": matriculados,
            "disponible": g.maximum_capacity - matriculados,
        })
    return output

@router.post("/grados", status_code=status.HTTP_201_CREATED)
async def crear_grado(data: dict, db: AsyncSession = Depends(get_db), _=only_admin):
    grade = Grade(
        name=data.get("nombre") or data.get("name") or "",
        education_level=data.get("education_level") or data.get("nivel_educativo") or "Básica",
        campus_id=int(data.get("campus_id", 1)),
        maximum_capacity=int(data.get("maximum_capacity", 40)),
        academic_year=int(data.get("academic_year", 2026)),
    )
    db.add(grade)
    await db.flush()
    await db.refresh(grade)
    return {"grade_id": grade.grade_id, "nombre": grade.name}

@router.put("/grados/{grade_id}")
async def editar_grado(grade_id: int, data: dict, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Grade).where(Grade.grade_id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    if "nombre" in data or "name" in data:
        grade.name = data.get("nombre") or data.get("name")
    if "maximum_capacity" in data:
        grade.maximum_capacity = int(data["maximum_capacity"])
    if "academic_year" in data:
        grade.academic_year = int(data["academic_year"])
    if "education_level" in data:
        grade.education_level = str(data["education_level"])
    await db.flush()
    return {"grade_id": grade.grade_id, "nombre": grade.name}

@router.delete("/grados/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_grado(grade_id: int, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Grade).where(Grade.grade_id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    await db.delete(grade)

@router.get("/salones")
async def listar_salones(db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Classroom).where(Classroom.status == "active"))
    classrooms = result.scalars().all()
    return [{"classroom_id": c.classroom_id, "nombre": c.name, "capacidad": c.capacity, "ubicacion": c.location or ""} for c in classrooms]
@router.get("/periodos")
async def listar_periodos(db: AsyncSession = Depends(get_db), _=Depends(require_rol("docente", "admin"))):
    result = await db.execute(select(AcademicPeriod))
    return result.scalars().all()

# ─────────────────────────────────────────
# REPORTES
# ─────────────────────────────────────────
@router.get("/reportes")
async def reportes(db: AsyncSession = Depends(get_db), _=only_admin):
    records_result = await db.execute(select(GradeRecord))
    records = records_result.scalars().all()

    total = len(records)
    aprobadas = sum(1 for r in records if float(r.score) >= 3.0)
    reprobadas = total - aprobadas

    ausencias_result = await db.execute(select(Attendance).where(Attendance.attendance_status == "absent"))
    total_ausencias = len(ausencias_result.scalars().all())

    obs_result = await db.execute(
        select(Observador.tipo, func.count(Observador.id))
        .group_by(Observador.tipo)
    )
    observador_counts = {}
    tipo_map = {"leve": 0, "grave": 0, "gravisima": 0, "gravísima": 0}
    for row in obs_result:
        key = row.tipo.lower().replace("í", "i")
        observador_counts[key] = row[1]
        if key in tipo_map:
            tipo_map[key] = row[1]

    return {
        "periodo": "todos",
        "total_notas_registradas": total,
        "aprobados": aprobadas,
        "reprobados": reprobadas,
        "tasa_aprobacion": round((aprobadas / total * 100), 2) if total > 0 else 0,
        "total_ausencias": total_ausencias,
        "observador": tipo_map,
    }
