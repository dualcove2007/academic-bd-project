from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.database import get_db
from app.db.models import CargaAcademica, Asistencia, Actividad, Nota, Observador, Usuario
from app.schemas.schemas import (
    AsistenciaCreate, AsistenciaOut,
    ActividadCreate, ActividadOut,
    NotaCreate, NotaOut,
    ObservadorCreate, ObservadorOut,
    CargaAcademicaOut
)
from app.core.security import require_rol
import uuid

router = APIRouter(prefix="/docentes", tags=["Docentes"])
only_docente = Depends(require_rol("docente", "admin"))

# ─────────────────────────────────────────
# CARGA ACADÉMICA DEL DOCENTE
# ─────────────────────────────────────────
@router.get("/mi-carga", response_model=List[CargaAcademicaOut])
async def mi_carga_academica(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin"))
):
    result = await db.execute(
        select(CargaAcademica).where(CargaAcademica.docente_id == current_user["id"])
    )
    return result.scalars().all()

# ─────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────
@router.post("/asistencia", response_model=List[AsistenciaOut], status_code=status.HTTP_201_CREATED)
async def registrar_asistencia(
    registros: List[AsistenciaCreate],
    db: AsyncSession = Depends(get_db),
    _=only_docente
):
    nuevos = []
    for r in registros:
        nuevo = Asistencia(id=str(uuid.uuid4()), **r.model_dump())
        db.add(nuevo)
        nuevos.append(nuevo)
    await db.flush()
    for n in nuevos:
        await db.refresh(n)
    return nuevos

@router.get("/asistencia/{carga_id}", response_model=List[AsistenciaOut])
async def ver_asistencia_clase(
    carga_id: str,
    fecha: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=only_docente
):
    query = select(Asistencia).where(Asistencia.carga_id == carga_id)
    result = await db.execute(query)
    return result.scalars().all()

# ─────────────────────────────────────────
# ACTIVIDADES
# ─────────────────────────────────────────
@router.get("/actividades/{materia_id}", response_model=List[ActividadOut])
async def listar_actividades(
    materia_id: str,
    periodo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=only_docente
):
    query = select(Actividad).where(Actividad.materia_id == materia_id)
    if periodo:
        query = query.where(Actividad.periodo == periodo)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/actividades", response_model=ActividadOut, status_code=status.HTTP_201_CREATED)
async def crear_actividad(
    data: ActividadCreate,
    db: AsyncSession = Depends(get_db),
    _=only_docente
):
    nueva = Actividad(id=str(uuid.uuid4()), **data.model_dump())
    db.add(nueva)
    await db.flush()
    await db.refresh(nueva)
    return nueva

@router.delete("/actividades/{actividad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_actividad(
    actividad_id: str,
    db: AsyncSession = Depends(get_db),
    _=only_docente
):
    result = await db.execute(select(Actividad).where(Actividad.id == actividad_id))
    actividad = result.scalar_one_or_none()
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    await db.delete(actividad)

# ─────────────────────────────────────────
# NOTAS
# ─────────────────────────────────────────
@router.get("/notas/{actividad_id}", response_model=List[NotaOut])
async def ver_notas_actividad(
    actividad_id: str,
    db: AsyncSession = Depends(get_db),
    _=only_docente
):
    result = await db.execute(select(Nota).where(Nota.actividad_id == actividad_id))
    return result.scalars().all()

@router.post("/notas", response_model=List[NotaOut], status_code=status.HTTP_201_CREATED)
async def registrar_notas(
    notas: List[NotaCreate],
    db: AsyncSession = Depends(get_db),
    _=only_docente
):
    nuevas = []
    for n in notas:
        nueva = Nota(id=str(uuid.uuid4()), **n.model_dump())
        db.add(nueva)
        nuevas.append(nueva)
    await db.flush()
    for n in nuevas:
        await db.refresh(n)
    return nuevas

@router.put("/notas/{nota_id}", response_model=NotaOut)
async def editar_nota(
    nota_id: str,
    data: NotaCreate,
    db: AsyncSession = Depends(get_db),
    _=only_docente
):
    result = await db.execute(select(Nota).where(Nota.id == nota_id))
    nota = result.scalar_one_or_none()
    if not nota:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    nota.valor = data.valor
    nota.observacion = data.observacion
    await db.flush()
    await db.refresh(nota)
    return nota

# ─────────────────────────────────────────
# OBSERVADOR
# ─────────────────────────────────────────
@router.post("/observador", response_model=ObservadorOut, status_code=status.HTTP_201_CREATED)
async def registrar_anotacion(
    data: ObservadorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_rol("docente", "admin"))
):
    nueva = Observador(
        id=str(uuid.uuid4()),
        docente_id=current_user["id"],
        **data.model_dump()
    )
    db.add(nueva)
    await db.flush()
    await db.refresh(nueva)
    return nueva

@router.get("/observador/{estudiante_id}", response_model=List[ObservadorOut])
async def ver_observador_estudiante(
    estudiante_id: str,
    periodo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=only_docente
):
    query = select(Observador).where(Observador.estudiante_id == estudiante_id)
    if periodo:
        query = query.where(Observador.periodo == periodo)
    result = await db.execute(query)
    return result.scalars().all()
