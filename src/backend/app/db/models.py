import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Numeric, Text, Integer, Date, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base

def gen_uuid():
    return str(uuid.uuid4())

# ─────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────
class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    nombre_completo: Mapped[str] = mapped_column(String(150))
    tipo_documento: Mapped[str] = mapped_column(String(10))  # CC, TI, CE
    numero_documento: Mapped[str] = mapped_column(String(20), unique=True)
    correo: Mapped[str] = mapped_column(String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20))  # admin, docente, estudiante
    estado: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    matriculas: Mapped[list["Matricula"]] = relationship(back_populates="estudiante")
    cargas_docente: Mapped[list["CargaAcademica"]] = relationship(back_populates="docente")
    asistencias: Mapped[list["Asistencia"]] = relationship(back_populates="estudiante")
    notas: Mapped[list["Nota"]] = relationship(back_populates="estudiante")
    observaciones: Mapped[list["Observador"]] = relationship(back_populates="estudiante", foreign_keys="Observador.estudiante_id")

# ─────────────────────────────────────────
# MATRÍCULAS
# ─────────────────────────────────────────
class Matricula(Base):
    __tablename__ = "matriculas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    estudiante_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id"))
    grado: Mapped[str] = mapped_column(String(10))
    grupo: Mapped[str] = mapped_column(String(5))
    periodo: Mapped[str] = mapped_column(String(10))  # ej: 2026-1
    sede: Mapped[str] = mapped_column(String(100))
    estado: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    estudiante: Mapped["Usuario"] = relationship(back_populates="matriculas")

# ─────────────────────────────────────────
# MATERIAS
# ─────────────────────────────────────────
class Materia(Base):
    __tablename__ = "materias"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    nombre: Mapped[str] = mapped_column(String(100))
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    estado: Mapped[bool] = mapped_column(Boolean, default=True)

    cargas: Mapped[list["CargaAcademica"]] = relationship(back_populates="materia")
    actividades: Mapped[list["Actividad"]] = relationship(back_populates="materia")

# ─────────────────────────────────────────
# CARGA ACADÉMICA
# ─────────────────────────────────────────
class CargaAcademica(Base):
    __tablename__ = "carga_academica"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    docente_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id"))
    materia_id: Mapped[str] = mapped_column(ForeignKey("materias.id"))
    grado: Mapped[str] = mapped_column(String(10))
    grupo: Mapped[str] = mapped_column(String(5))
    periodo: Mapped[str] = mapped_column(String(10))
    dia_semana: Mapped[str] = mapped_column(String(15))   # Lunes, Martes...
    hora_inicio: Mapped[str] = mapped_column(String(10))  # HH:MM
    hora_fin: Mapped[str] = mapped_column(String(10))
    salon: Mapped[str] = mapped_column(String(20))
    estado: Mapped[bool] = mapped_column(Boolean, default=True)

    docente: Mapped["Usuario"] = relationship(back_populates="cargas_docente")
    materia: Mapped["Materia"] = relationship(back_populates="cargas")
    asistencias: Mapped[list["Asistencia"]] = relationship(back_populates="carga")

# ─────────────────────────────────────────
# ACTIVIDADES (evaluaciones)
# ─────────────────────────────────────────
class Actividad(Base):
    __tablename__ = "actividades"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    materia_id: Mapped[str] = mapped_column(ForeignKey("materias.id"))
    nombre: Mapped[str] = mapped_column(String(150))
    porcentaje: Mapped[float] = mapped_column(Numeric(5, 2))
    fecha_entrega: Mapped[datetime] = mapped_column(DateTime)
    periodo: Mapped[str] = mapped_column(String(10))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")  # pendiente, calificada

    materia: Mapped["Materia"] = relationship(back_populates="actividades")
    notas: Mapped[list["Nota"]] = relationship(back_populates="actividad")

# ─────────────────────────────────────────
# NOTAS
# ─────────────────────────────────────────
class Nota(Base):
    __tablename__ = "notas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    estudiante_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id"))
    actividad_id: Mapped[str] = mapped_column(ForeignKey("actividades.id"))
    valor: Mapped[float] = mapped_column(Numeric(4, 2))
    observacion: Mapped[str] = mapped_column(Text, nullable=True)
    registrado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    estudiante: Mapped["Usuario"] = relationship(back_populates="notas")
    actividad: Mapped["Actividad"] = relationship(back_populates="notas")

# ─────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────
class Asistencia(Base):
    __tablename__ = "asistencia"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    estudiante_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id"))
    carga_id: Mapped[str] = mapped_column(ForeignKey("carga_academica.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime)
    estado: Mapped[str] = mapped_column(String(20))  # presente, ausente, tarde, excusado
    observacion: Mapped[str] = mapped_column(Text, nullable=True)

    estudiante: Mapped["Usuario"] = relationship(back_populates="asistencias")
    carga: Mapped["CargaAcademica"] = relationship(back_populates="asistencias")

# ─────────────────────────────────────────
# OBSERVADOR
# ─────────────────────────────────────────
class Observador(Base):
    __tablename__ = "observador"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    estudiante_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id"))
    docente_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20))  # falta, felicitacion, anotacion
    descripcion: Mapped[str] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    periodo: Mapped[str] = mapped_column(String(10))

    estudiante: Mapped["Usuario"] = relationship(back_populates="observaciones", foreign_keys=[estudiante_id])
