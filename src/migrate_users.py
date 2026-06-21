import asyncio, uuid, asyncpg, bcrypt
from datetime import datetime, timezone

ROLE_MAP = {1: "admin", 2: "docente", 3: "estudiante"}

async def migrate():
    conn = await asyncpg.connect(
        'postgresql://academic_db_hum7_user:9a8QgYQA20dhqUBAShty63vwqnH6yKi7@dpg-d8rb58cm0tmc73c02nqg-a.oregon-postgres.render.com/academic_db_hum7'
    )

    users = await conn.fetch("SELECT * FROM users")
    print(f"Encontrados {len(users)} usuarios en tabla 'users'")

    migrated = 0
    skipped = 0
    for u in users:
        exists = await conn.fetchrow(
            "SELECT id FROM usuarios WHERE username = $1 OR numero_documento = $2",
            u["username"], u["document_number"]
        )
        if exists:
            print(f"  Saltando {u['username']} — ya existe en usuarios")
            skipped += 1
            continue

        full_name = " ".join(filter(None, [u["first_name"], u["middle_name"], u["last_name"], u["second_last_name"]])) or u["username"]
        hashed = bcrypt.hashpw(u["password_hash"].encode(), bcrypt.gensalt()).decode()
        new_id = str(uuid.uuid4())

        await conn.execute("""
            INSERT INTO usuarios (id, username, nombre_completo, tipo_documento, numero_documento,
                                  correo, password_hash, rol, estado, creado_en)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
            new_id, u["username"], full_name, u["document_type"], u["document_number"],
            u["email"] or f"{u['username']}@email.com", hashed, ROLE_MAP.get(u["role_id"], "desconocido"),
            u["status"] == "active", datetime.utcnow()
        )
        print(f"  Migrado {u['username']} -> {full_name} (rol={ROLE_MAP.get(u['role_id'])})")
        migrated += 1

    print(f"\nResumen: {migrated} migrados, {skipped} saltados")
    await conn.close()

asyncio.run(migrate())
