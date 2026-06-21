from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.db.database import get_db
from app.db.models import Usuario, Matricula, CargaAcademica, Materia, Nota, Asistencia
from app.schemas.schemas import (
    UsuarioCreate, UsuarioUpdate, UsuarioOut,
    MatriculaCreate, MatriculaOut,
    CargaAcademicaCreate, CargaAcademicaOut,
    MateriaCreate, MateriaOut
)
from app.core.security import require_rol, hash_password
import uuid

router = APIRouter(prefix="/admin", tags=["Administrador"])
only_admin = Depends(require_rol("admin"))

# ─────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────
@router.get("/usuarios", response_model=List[UsuarioOut])
async def listar_usuarios(
    rol: Optional[str] = None,
    estado: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _=only_admin
):
    query = select(Usuario)
    if rol:
        query = query.where(Usuario.rol == rol)
    if estado is not None:
        query = query.where(Usuario.estado == estado)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def crear_usuario(data: UsuarioCreate, db: AsyncSession = Depends(get_db), _=only_admin):
    existe = await db.execute(
        select(Usuario).where(
            (Usuario.username == data.username) |
            (Usuario.correo == data.correo) |
            (Usuario.numero_documento == data.numero_documento)
        )
    )
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Usuario, correo o documento ya registrado")

    nuevo = Usuario(
        id=str(uuid.uuid4()),
        username=data.username,
        nombre_completo=data.nombre_completo,
        tipo_documento=data.tipo_documento,
        numero_documento=data.numero_documento,
        correo=data.correo,
        password_hash=hash_password(data.password),
        rol=data.rol,
        estado=True
    )
    db.add(nuevo)
    await db.flush()
    await db.refresh(nuevo)
    return nuevo

@router.get("/usuarios/{usuario_id}", response_model=UsuarioOut)
async def obtener_usuario(usuario_id: str, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.put("/usuarios/{usuario_id}", response_model=UsuarioOut)
async def editar_usuario(usuario_id: str, data: UsuarioUpdate, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(usuario, field, value)

    await db.flush()
    await db.refresh(usuario)
    return usuario

@router.patch("/usuarios/{usuario_id}/estado", response_model=UsuarioOut)
async def cambiar_estado(usuario_id: str, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.estado = not usuario.estado
    await db.flush()
    await db.refresh(usuario)
    return usuario

@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(usuario_id: str, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    await db.delete(usuario)

# ─────────────────────────────────────────
# MATRÍCULAS
# ─────────────────────────────────────────
@router.get("/matriculas", response_model=List[MatriculaOut])
async def listar_matriculas(
    grado: Optional[str] = None,
    grupo: Optional[str] = None,
    periodo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=only_admin
):
    query = select(Matricula)
    if grado:
        query = query.where(Matricula.grado == grado)
    if grupo:
        query = query.where(Matricula.grupo == grupo)
    if periodo:
        query = query.where(Matricula.periodo == periodo)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/matriculas", response_model=MatriculaOut, status_code=status.HTTP_201_CREATED)
async def crear_matricula(data: MatriculaCreate, db: AsyncSession = Depends(get_db), _=only_admin):
    nueva = Matricula(id=str(uuid.uuid4()), **data.model_dump())
    db.add(nueva)
    await db.flush()
    await db.refresh(nueva)
    return nueva

@router.patch("/matriculas/{matricula_id}/finalizar", response_model=MatriculaOut)
async def finalizar_matricula(matricula_id: str, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Matricula).where(Matricula.id == matricula_id))
    matricula = result.scalar_one_or_none()
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    matricula.estado = True
    await db.flush()
    await db.refresh(matricula)
    return matricula

# ─────────────────────────────────────────
# MATERIAS
# ─────────────────────────────────────────
@router.get("/materias", response_model=List[MateriaOut])
async def listar_materias(db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(Materia))
    return result.scalars().all()

@router.post("/materias", response_model=MateriaOut, status_code=status.HTTP_201_CREATED)
async def crear_materia(data: MateriaCreate, db: AsyncSession = Depends(get_db), _=only_admin):
    nueva = Materia(id=str(uuid.uuid4()), **data.model_dump())
    db.add(nueva)
    await db.flush()
    await db.refresh(nueva)
    return nueva

# ─────────────────────────────────────────
# CARGA ACADÉMICA
# ─────────────────────────────────────────
@router.get("/carga-academica", response_model=List[CargaAcademicaOut])
async def listar_carga(
    periodo: Optional[str] = None,
    docente_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=only_admin
):
    query = select(CargaAcademica)
    if periodo:
        query = query.where(CargaAcademica.periodo == periodo)
    if docente_id:
        query = query.where(CargaAcademica.docente_id == docente_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/carga-academica", response_model=CargaAcademicaOut, status_code=status.HTTP_201_CREATED)
async def crear_carga(data: CargaAcademicaCreate, db: AsyncSession = Depends(get_db), _=only_admin):
    nueva = CargaAcademica(id=str(uuid.uuid4()), **data.model_dump())
    db.add(nueva)
    await db.flush()
    await db.refresh(nueva)
    return nueva

@router.delete("/carga-academica/{carga_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_carga(carga_id: str, db: AsyncSession = Depends(get_db), _=only_admin):
    result = await db.execute(select(CargaAcademica).where(CargaAcademica.id == carga_id))
    carga = result.scalar_one_or_none()
    if not carga:
        raise HTTPException(status_code=404, detail="Carga no encontrada")
    await db.delete(carga)

# ─────────────────────────────────────────
# REPORTES Y ESTADÍSTICAS
# ─────────────────────────────────────────
@router.get("/reportes")
async def reportes(periodo: Optional[str] = None, db: AsyncSession = Depends(get_db), _=only_admin):
    query_notas = select(Nota)
    notas_result = await db.execute(query_notas)
    notas = notas_result.scalars().all()

    total = len(notas)
    aprobadas = sum(1 for n in notas if float(n.valor) >= 3.0)
    reprobadas = total - aprobadas

    query_asistencia = select(Asistencia).where(Asistencia.estado == "ausente")
    ausencias_result = await db.execute(query_asistencia)
    total_ausencias = len(ausencias_result.scalars().all())

    return {
        "periodo": periodo or "todos",
        "total_notas_registradas": total,
        "aprobados": aprobadas,
        "reprobados": reprobadas,
        "tasa_aprobacion": round((aprobadas / total * 100), 2) if total > 0 else 0,
        "total_ausencias": total_ausencias
    }
