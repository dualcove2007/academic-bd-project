from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.database import get_db
from app.db.models import Matricula, CargaAcademica, Asistencia, Nota, Actividad, Observador, Materia
from app.schemas.schemas import MatriculaOut, AsistenciaOut, NotaOut, ObservadorOut, CargaAcademicaOut
from app.core.security import require_rol

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])
only_estudiante = Depends(require_rol("estudiante", "admin", "docente"))

# ─────────────────────────────────────────
# MATRÍCULA
# ─────────────────────────────────────────
@router.get("/mi-matricula", response_model=MatriculaOut)
async def mi_matricula(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    result = await db.execute(
        select(Matricula).where(Matricula.estudiante_id == current_user["id"])
    )
    matricula = result.scalar_one_or_none()
    if not matricula:
        raise HTTPException(status_code=404, detail="No tienes matrícula activa")
    return matricula

# ─────────────────────────────────────────
# HORARIO
# ─────────────────────────────────────────
@router.get("/horario")
async def mi_horario(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    matricula_result = await db.execute(
        select(Matricula).where(
            Matricula.estudiante_id == current_user["id"],
            Matricula.estado == True
        )
    )
    matricula = matricula_result.scalar_one_or_none()
    if not matricula:
        raise HTTPException(status_code=404, detail="No tienes matrícula activa")

    carga_result = await db.execute(
        select(CargaAcademica).where(
            CargaAcademica.grado == matricula.grado,
            CargaAcademica.grupo == matricula.grupo,
            CargaAcademica.periodo == matricula.periodo,
            CargaAcademica.estado == True
        )
    )
    cargas = carga_result.scalars().all()

    horario = []
    for c in cargas:
        materia_result = await db.execute(select(Materia).where(Materia.id == c.materia_id))
        materia = materia_result.scalar_one_or_none()
        horario.append({
            "dia": c.dia_semana,
            "hora_inicio": c.hora_inicio,
            "hora_fin": c.hora_fin,
            "materia": materia.nombre if materia else "N/A",
            "salon": c.salon,
            "docente_id": c.docente_id
        })

    return {"horario": horario}

# ─────────────────────────────────────────
# NOTAS
# ─────────────────────────────────────────
@router.get("/notas")
async def mis_notas(
    periodo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    query = select(Nota).where(Nota.estudiante_id == current_user["id"])
    result = await db.execute(query)
    notas = result.scalars().all()

    detalle = []
    promedio_total = 0.0
    for n in notas:
        act_result = await db.execute(select(Actividad).where(Actividad.id == n.actividad_id))
        actividad = act_result.scalar_one_or_none()
        if actividad:
            mat_result = await db.execute(select(Materia).where(Materia.id == actividad.materia_id))
            materia = mat_result.scalar_one_or_none()
            detalle.append({
                "actividad": actividad.nombre,
                "materia": materia.nombre if materia else "N/A",
                "porcentaje": float(actividad.porcentaje),
                "nota": float(n.valor),
                "fecha_entrega": actividad.fecha_entrega,
                "estado": actividad.estado
            })
            promedio_total += float(n.valor)

    promedio = round(promedio_total / len(notas), 2) if notas else 0.0

    return {"notas": detalle, "promedio_general": promedio}

# ─────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────
@router.get("/asistencia", response_model=List[AsistenciaOut])
async def mi_asistencia(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    result = await db.execute(
        select(Asistencia).where(Asistencia.estudiante_id == current_user["id"])
    )
    return result.scalars().all()

# ─────────────────────────────────────────
# BOLETÍN
# ─────────────────────────────────────────
@router.get("/boletin")
async def mi_boletin(
    periodo: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    notas_result = await db.execute(
        select(Nota).where(Nota.estudiante_id == current_user["id"])
    )
    notas = notas_result.scalars().all()

    materias_dict: dict = {}
    for n in notas:
        act_result = await db.execute(select(Actividad).where(
            Actividad.id == n.actividad_id,
            Actividad.periodo == periodo
        ))
        actividad = act_result.scalar_one_or_none()
        if not actividad:
            continue

        mat_result = await db.execute(select(Materia).where(Materia.id == actividad.materia_id))
        materia = mat_result.scalar_one_or_none()
        nombre_materia = materia.nombre if materia else "N/A"

        if nombre_materia not in materias_dict:
            materias_dict[nombre_materia] = {"notas": [], "fallas": 0}

        materias_dict[nombre_materia]["notas"].append(float(n.valor) * float(actividad.porcentaje) / 100)

    boletin = []
    for materia, datos in materias_dict.items():
        nota_final = round(sum(datos["notas"]), 2)
        desempeño = (
            "Superior" if nota_final >= 4.6 else
            "Alto" if nota_final >= 4.0 else
            "Básico" if nota_final >= 3.0 else
            "Bajo"
        )
        boletin.append({
            "materia": materia,
            "nota_final": nota_final,
            "desempeño": desempeño,
            "fallas": datos["fallas"]
        })

    return {"periodo": periodo, "boletin": boletin}

# ─────────────────────────────────────────
# OBSERVADOR
# ─────────────────────────────────────────
@router.get("/observador", response_model=List[ObservadorOut])
async def mi_observador(
    periodo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("estudiante", "admin"))
):
    query = select(Observador).where(Observador.estudiante_id == current_user["id"])
    if periodo:
        query = query.where(Observador.periodo == periodo)
    result = await db.execute(query)
    return result.scalars().all()
