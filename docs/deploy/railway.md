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
| `SYNER_ADMIN_EMAIL` | email del admin inicial | ✅ (para poder entrar) |
| `SYNER_ADMIN_PASSWORD` | contraseña del admin inicial | ✅ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `120` (default) | opcional |
| `MIN_PASSWORD_LENGTH` | `8` (default) | opcional |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | claves de IA | opcional (RAG/agentes; la app arranca sin ellas) |

> El esquema `postgres://` se normaliza a `postgresql://` automáticamente.

## 3. Qué hace el arranque

`railway.json → deploy.startCommand` ejecuta, en orden:

1. `alembic upgrade head` — crea/actualiza el esquema (40+ tablas).
2. `python -m app.scripts.bootstrap_admin` — crea (o rota) el admin desde
   `SYNER_ADMIN_*`. Es idempotente y **no bloquea** el arranque si las vars no
   están (`|| true`); en ese caso configúralas y redeploy.
3. `uvicorn app.main:app` — sirve API + SPA en `$PORT`.

Healthcheck: `GET /api/health`.

## 4. Build (Nixpacks)

- Python 3.11 + Node 20.
- `pip install -r requirements.txt` en `.venv`.
- `npm ci --include=dev` en `frontend` — **`--include=dev` es necesario** porque
  `vite`/`typescript`/`tailwind` son `devDependencies` y Nixpacks instala con
  `NODE_ENV=production`; sin esa bandera el build falla con `vite: not found`.
- `npm run build` → genera `frontend/dist` (servido por FastAPI).

## 5. Primer login

Tras el primer deploy con `SYNER_ADMIN_*` configuradas, entra con ese
email/contraseña. Desde ahí se dan de alta clientes y usuarios en la consola de
administración.
