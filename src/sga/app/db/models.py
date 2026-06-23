from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Numeric, Text, Integer, Date, Time, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

# ─────────────────────────────────────────
# ROLES
# ─────────────────────────────────────────
class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")

# ─────────────────────────────────────────
# INSTITUTIONS
# ─────────────────────────────────────────
class Institution(Base):
    __tablename__ = "institutions"

    institution_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(180))
    tax_id: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(280), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    email: Mapped[str] = mapped_column(String(180), nullable=True)
    logo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    flag_url: Mapped[str] = mapped_column(String(500), nullable=True)
    shield_url: Mapped[str] = mapped_column(String(500), nullable=True)
    banner_url: Mapped[str] = mapped_column(String(500), nullable=True)
    slogan: Mapped[str] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(20), nullable=True)
    secondary_color: Mapped[str] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

# ─────────────────────────────────────────
# CAMPUSES
# ─────────────────────────────────────────
class Campus(Base):
    __tablename__ = "campuses"

    campus_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.institution_id"))
    name: Mapped[str] = mapped_column(String(180))
    address: Mapped[str] = mapped_column(String(280), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    email: Mapped[str] = mapped_column(String(180), nullable=True)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")

    institution: Mapped["Institution"] = relationship()
    classrooms: Mapped[list["Classroom"]] = relationship(back_populates="campus")
    courses: Mapped[list["Course"]] = relationship(back_populates="campus")

# ─────────────────────────────────────────
# GRADES (grade levels)
# ─────────────────────────────────────────
class Grade(Base):
    __tablename__ = "grades"

    grade_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    education_level: Mapped[str] = mapped_column(String(100))

# ─────────────────────────────────────────
# CLASSROOMS
# ─────────────────────────────────────────
class Classroom(Base):
    __tablename__ = "classrooms"

    classroom_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.campus_id"))
    name: Mapped[str] = mapped_column(String(100))
    capacity: Mapped[int] = mapped_column(Integer)
    location: Mapped[str] = mapped_column(String(180), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    campus: Mapped["Campus"] = relationship(back_populates="classrooms")

# ─────────────────────────────────────────
# ACADEMIC PERIODS
# ─────────────────────────────────────────
class AcademicPeriod(Base):
    __tablename__ = "academic_periods"

    period_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(180))
    academic_year: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")

# ─────────────────────────────────────────
# COURSES (course sections per grade)
# ─────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"

    course_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.grade_id"))
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.campus_id"))
    name: Mapped[str] = mapped_column(String(180))
    maximum_capacity: Mapped[int] = mapped_column(Integer)
    academic_year: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")

    campus: Mapped["Campus"] = relationship(back_populates="courses")

# ─────────────────────────────────────────
# SUBJECTS
# ─────────────────────────────────────────
class Subject(Base):
    __tablename__ = "subjects"

    subject_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    weekly_hours: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="active")

    academic_loads: Mapped[list["AcademicLoad"]] = relationship(back_populates="subject")

# ─────────────────────────────────────────
# USERS
# ─────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"))
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.campus_id"))
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    profile_picture: Mapped[str] = mapped_column(String(500), nullable=True)
    document_type: Mapped[str] = mapped_column(String(30))
    document_number: Mapped[str] = mapped_column(String(50))
    first_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100))
    second_last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    email: Mapped[str] = mapped_column(String(180), nullable=True)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    role: Mapped["Role"] = relationship(back_populates="users")
    teacher: Mapped["Teacher"] = relationship(back_populates="user", uselist=False)
    student: Mapped["Student"] = relationship(back_populates="user", uselist=False)

# ─────────────────────────────────────────
# TEACHERS
# ─────────────────────────────────────────
class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=True, unique=True)
    document_type: Mapped[str] = mapped_column(String(30))
    document_number: Mapped[str] = mapped_column(String(50))
    first_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100))
    second_last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    email: Mapped[str] = mapped_column(String(180), nullable=True)
    hire_date: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    user: Mapped["User"] = relationship(back_populates="teacher")
    academic_loads: Mapped[list["AcademicLoad"]] = relationship(back_populates="teacher")

# ─────────────────────────────────────────
# STUDENTS
# ─────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"

    student_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=True, unique=True)
    document_type: Mapped[str] = mapped_column(String(30))
    document_number: Mapped[str] = mapped_column(String(50))
    first_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100))
    second_last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=True)
    address: Mapped[str] = mapped_column(String(280), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    email: Mapped[str] = mapped_column(String(180), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    user: Mapped["User"] = relationship(back_populates="student")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")

# ─────────────────────────────────────────
# ENROLLMENTS
# ─────────────────────────────────────────
class Enrollment(Base):
    __tablename__ = "enrollments"

    enrollment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.course_id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("academic_periods.period_id"))
    enrollment_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    grade_records: Mapped[list["GradeRecord"]] = relationship(back_populates="enrollment")

# ─────────────────────────────────────────
# ACADEMIC LOAD
# ─────────────────────────────────────────
class AcademicLoad(Base):
    __tablename__ = "academic_load"

    academic_load_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.teacher_id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.course_id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.subject_id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("academic_periods.period_id"))

    teacher: Mapped["Teacher"] = relationship(back_populates="academic_loads")
    subject: Mapped["Subject"] = relationship(back_populates="academic_loads")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="academic_load")
    activities: Mapped[list["Activity"]] = relationship(back_populates="academic_load")

# ─────────────────────────────────────────
# SCHEDULES
# ─────────────────────────────────────────
class Schedule(Base):
    __tablename__ = "schedules"

    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    academic_load_id: Mapped[int] = mapped_column(ForeignKey("academic_load.academic_load_id"))
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.classroom_id"))
    day_of_week: Mapped[str] = mapped_column(String(15))
    start_time: Mapped[datetime] = mapped_column(Time)
    end_time: Mapped[datetime] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(20), default="active")

    academic_load: Mapped["AcademicLoad"] = relationship(back_populates="schedules")

# ─────────────────────────────────────────
# ACTIVITIES
# ─────────────────────────────────────────
class Activity(Base):
    __tablename__ = "activities"

    activity_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    academic_load_id: Mapped[int] = mapped_column(ForeignKey("academic_load.academic_load_id"))
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2))
    activity_date: Mapped[date] = mapped_column(Date, nullable=True)

    academic_load: Mapped["AcademicLoad"] = relationship(back_populates="activities")
    grade_records: Mapped[list["GradeRecord"]] = relationship(back_populates="activity")

# ─────────────────────────────────────────
# GRADE RECORDS
# ─────────────────────────────────────────
class GradeRecord(Base):
    __tablename__ = "grade_records"

    grade_record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"), nullable=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.enrollment_id"))
    score: Mapped[float] = mapped_column(Numeric(5, 2))
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    record_date: Mapped[date] = mapped_column(Date)

    activity: Mapped["Activity"] = relationship(back_populates="grade_records")
    enrollment: Mapped["Enrollment"] = relationship(back_populates="grade_records")

# ─────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────
class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.enrollment_id"))
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.schedule_id"))
    attendance_date: Mapped[date] = mapped_column(Date)
    attendance_status: Mapped[str] = mapped_column(String(20))
    comments: Mapped[str] = mapped_column(Text, nullable=True)

    enrollment: Mapped["Enrollment"] = relationship()
    schedule: Mapped["Schedule"] = relationship()

# ─────────────────────────────────────────
# OBSERVADOR (keep our table)
# ─────────────────────────────────────────
class Observador(Base):
    __tablename__ = "observador"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    docente_id: Mapped[int] = mapped_column(ForeignKey("teachers.teacher_id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20))
    descripcion: Mapped[str] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(DateTime)
    periodo: Mapped[str] = mapped_column(String(50))
