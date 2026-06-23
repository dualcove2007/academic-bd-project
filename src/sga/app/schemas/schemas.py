from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

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
# USER (combined view for admin)
# ─────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str
    role_id: int
    campus_id: int = 1
    document_type: str
    document_number: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    second_last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    # Teacher/Student specific
    hire_date: Optional[date] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None

class UserUpdate(BaseModel):
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    second_last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class UserOut(BaseModel):
    user_id: int
    username: str
    role_id: int
    role_name: str
    campus_id: int
    document_type: str
    document_number: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    second_last_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    status: str
    profile_type: str  # 'admin', 'teacher', 'student'

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# SUBJECTS
# ─────────────────────────────────────────
class SubjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    weekly_hours: int = 1

class SubjectOut(BaseModel):
    subject_id: int
    name: str
    description: Optional[str]
    weekly_hours: int
    status: str

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# ENROLLMENTS
# ─────────────────────────────────────────
class EnrollmentCreate(BaseModel):
    student_id: int
    grade_id: int
    period_id: int
    enrollment_date: date

class EnrollmentOut(BaseModel):
    enrollment_id: int
    student_id: int
    grade_id: int
    period_id: int
    enrollment_date: date
    status: str

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# ACADEMIC LOAD
# ─────────────────────────────────────────
class AcademicLoadCreate(BaseModel):
    teacher_id: int
    grade_id: int
    subject_id: int
    period_id: int

class AcademicLoadOut(BaseModel):
    academic_load_id: int
    teacher_id: int
    grade_id: int
    subject_id: int
    period_id: int

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# SCHEDULES
# ─────────────────────────────────────────
class ScheduleOut(BaseModel):
    schedule_id: int
    academic_load_id: int
    classroom_id: int
    day_of_week: str
    start_time: datetime
    end_time: datetime
    status: str

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# ACTIVITIES
# ─────────────────────────────────────────
class ActivityCreate(BaseModel):
    academic_load_id: int
    name: str
    description: Optional[str] = None
    percentage: float
    activity_date: Optional[date] = None

class ActivityOut(BaseModel):
    activity_id: int
    academic_load_id: int
    name: str
    description: Optional[str]
    percentage: float
    activity_date: Optional[date]

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# GRADE RECORDS
# ─────────────────────────────────────────
class GradeRecordCreate(BaseModel):
    activity_id: int
    enrollment_id: int
    score: float
    comments: Optional[str] = None

class GradeRecordOut(BaseModel):
    grade_record_id: int
    activity_id: Optional[int]
    enrollment_id: int
    score: float
    comments: Optional[str]
    record_date: date

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────
class AttendanceCreate(BaseModel):
    enrollment_id: int
    schedule_id: int
    attendance_date: date
    attendance_status: str
    comments: Optional[str] = None

class AttendanceOut(BaseModel):
    attendance_id: int
    enrollment_id: int
    schedule_id: int
    attendance_date: date
    attendance_status: str
    comments: Optional[str]

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# OBSERVADOR
# ─────────────────────────────────────────
class ObservadorCreate(BaseModel):
    estudiante_id: int
    tipo: str
    descripcion: str
    periodo: str

class ObservadorOut(BaseModel):
    id: str
    estudiante_id: int
    docente_id: Optional[int]
    tipo: str
    descripcion: str
    fecha: datetime
    periodo: str

    class Config:
        from_attributes = True
