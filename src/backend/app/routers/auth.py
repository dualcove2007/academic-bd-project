from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import Usuario
from app.schemas.schemas import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.username == data.usuario))
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    if not usuario.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador."
        )

    token = create_access_token({"sub": usuario.id, "rol": usuario.rol})

    return TokenResponse(
        access_token=token,
        rol=usuario.rol,
        nombre=usuario.nombre_completo
    )
