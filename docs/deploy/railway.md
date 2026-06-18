# Deploy en Railway

Syner Cortex se despliega como **un solo servicio** (FastAPI sirve la API bajo
`/api` y la SPA de React compilada desde `frontend/dist`) más un servicio
**PostgreSQL** gestionado por Railway.

## 1. Servicios

1. **Postgres**: añade el plugin *PostgreSQL* en el proyecto de Railway.
2. **App** (este repo): builder **Nixpacks** (ya configurado en `railway.json` /
   `nixpacks.toml`).

## 2. Variables de entorno (servicio App)

| Variable | Valor | Obligatoria |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (referencia al servicio Postgres) | ✅ |
| `JWT_SECRET` | secreto fuerte — `python -c "import secrets; print(secrets.token_urlsafe(48))"` | ✅ (la app no arranca sin él en prod) |
| `ENV` | `production` | ✅ |
| `CORS_ORIGINS` | el dominio público, p. ej. `https://<tu-app>.up.railway.app` | recomendada |
| `CREW_SEED_PASSWORD` | contraseña temporal inicial para los 4 usuarios crew | recomendada |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `120` (default) | opcional |
| `MIN_PASSWORD_LENGTH` | `8` (default) | opcional |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | claves de IA | opcional (RAG/agentes; la app arranca sin ellas) |

> El esquema `postgres://` se normaliza a `postgresql://` automáticamente.

## 3. Qué hace el arranque

`railway.json → deploy.startCommand` ejecuta, en orden:

1. `alembic upgrade head` — crea/actualiza el esquema (40+ tablas).
2. `python -m app.scripts.seed_crew` — crea módulos de referencia, la org Syner y
   los 4 usuarios crew (ver abajo). Idempotente y **no bloquea** el arranque
   (`|| true`). La contraseña temporal sale de `CREW_SEED_PASSWORD`; si no está,
   se genera una y se imprime en los logs del deploy.
3. `uvicorn app.main:app` — sirve API + SPA en `$PORT`.

### Usuarios crew provisionados

| Email | Rol |
|---|---|
| `ecg@syner.mx` | superadmin (SYNER_CREW, is_superadmin, org SUPERADMIN) |
| `humberto@syner.mx` | admin (SYNER_CREW, org SYNER_PARTNER) |
| `alan@syner.mx` | admin (SYNER_CREW, org SYNER_PARTNER) |
| `damian@syner.mx` | admin (SYNER_CREW, org SYNER_PARTNER) |

Todos arrancan con `must_change_password=True`: en el primer login se les obliga
a definir su propia contraseña. Re-deployar no sobrescribe usuarios existentes.

Healthcheck: `GET /api/health`.

## 4. Build (Nixpacks)

- Python 3.11 + Node 20.
- `pip install -r requirements.txt` en `.venv`.
- `npm ci --include=dev` en `frontend` — **`--include=dev` es necesario** porque
  `vite`/`typescript`/`tailwind` son `devDependencies` y Nixpacks instala con
  `NODE_ENV=production`; sin esa bandera el build falla con `vite: not found`.
- `npm run build` → genera `frontend/dist` (servido por FastAPI).

## 5. Primer login

Tras el primer deploy, entra como `ecg@syner.mx` (superadmin) con la
`CREW_SEED_PASSWORD` (o la generada que aparece en los logs). Se te pedirá
cambiarla. Desde ahí se dan de alta clientes y usuarios en la consola de
administración.
