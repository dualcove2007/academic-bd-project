from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import User, Role
from app.schemas.schemas import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token, hash_password

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.usuario))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador."
        )

    if not user.password_hash.startswith("$2"):
        user.password_hash = hash_password(user.password_hash)
        db.add(user)

    role_result = await db.execute(select(Role).where(Role.role_id == user.role_id))
    role = role_result.scalar_one_or_none()
    role_name = role.name if role else "desconocido"

    role_map = {"Administrativo": "admin", "Docente": "docente", "Estudiante": "estudiante", "Acudiente": "acudiente"}
    rol_sistema = role_map.get(role_name, "desconocido")

    token = create_access_token({"sub": str(user.user_id), "rol": rol_sistema})

    return TokenResponse(
        access_token=token,
        rol=rol_sistema,
        nombre=f"{user.first_name} {user.last_name}"
    )
