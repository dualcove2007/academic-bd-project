from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────
class LoginRequest(BaseModel):
    usuario: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre: str

# ─────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────
class UsuarioCreate(BaseModel):
    username: str
    nombre_completo: str
    tipo_documento: str
    numero_documento: str
    correo: str
    password: str
    rol: str

class UsuarioUpdate(BaseModel):
    username: Optional[str] = None
    nombre_completo: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    correo: Optional[str] = None
    rol: Optional[str] = None

class UsuarioOut(BaseModel):
    id: str
    username: str
    nombre_completo: str
    tipo_documento: str
    numero_documento: str
    correo: str
    rol: str
    estado: bool
    creado_en: datetime

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# MATRÍCULAS
# ─────────────────────────────────────────
class MatriculaCreate(BaseModel):
    estudiante_id: str
    grado: str
    grupo: str
    periodo: str
    sede: str

class MatriculaOut(BaseModel):
    id: str
    estudiante_id: str
    grado: str
    grupo: str
    periodo: str
    sede: str
    estado: bool

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# MATERIAS
# ─────────────────────────────────────────
class MateriaCreate(BaseModel):
    nombre: str
    codigo: str

class MateriaOut(BaseModel):
    id: str
    nombre: str
    codigo: str
    estado: bool

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# CARGA ACADÉMICA
# ─────────────────────────────────────────
class CargaAcademicaCreate(BaseModel):
    docente_id: str
    materia_id: str
    grado: str
    grupo: str
    periodo: str
    dia_semana: str
    hora_inicio: str
    hora_fin: str
    salon: str

class CargaAcademicaOut(BaseModel):
    id: str
    docente_id: str
    materia_id: str
    grado: str
    grupo: str
    periodo: str
    dia_semana: str
    hora_inicio: str
    hora_fin: str
    salon: str
    estado: bool

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# ACTIVIDADES
# ─────────────────────────────────────────
class ActividadCreate(BaseModel):
    materia_id: str
    nombre: str
    porcentaje: float
    fecha_entrega: datetime
    periodo: str

class ActividadOut(BaseModel):
    id: str
    materia_id: str
    nombre: str
    porcentaje: float
    fecha_entrega: datetime
    periodo: str
    estado: str

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# NOTAS
# ─────────────────────────────────────────
class NotaCreate(BaseModel):
    estudiante_id: str
    actividad_id: str
    valor: float
    observacion: Optional[str] = None

class NotaOut(BaseModel):
    id: str
    estudiante_id: str
    actividad_id: str
    valor: float
    observacion: Optional[str]
    registrado_en: datetime

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────
class AsistenciaCreate(BaseModel):
    estudiante_id: str
    carga_id: str
    fecha: datetime
    estado: str
    observacion: Optional[str] = None

class AsistenciaOut(BaseModel):
    id: str
    estudiante_id: str
    carga_id: str
    fecha: datetime
    estado: str
    observacion: Optional[str]

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# OBSERVADOR
# ─────────────────────────────────────────
class ObservadorCreate(BaseModel):
    estudiante_id: str
    tipo: str
    descripcion: str
    periodo: str

class ObservadorOut(BaseModel):
    id: str
    estudiante_id: str
    docente_id: Optional[str]
    tipo: str
    descripcion: str
    fecha: datetime
    periodo: str

    class Config:
        from_attributes = True
