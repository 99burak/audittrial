# AuditTrail

AuditTrail is a full-stack web application that collects user activity records from multiple applications in one central place. Authorized panel users can view, filter, and inspect these audit events.

Applications send events with their own API keys. Panel users have either the `admin` or `viewer` role. Public user registration is not available.

## Technology stack

- Backend: Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic, and Pytest
- Database: PostgreSQL
- Frontend: React, Vite, JavaScript, React Router, and CSS
- Infrastructure: Docker, Docker Compose, and `.env` configuration

## Main features

- Cookie-based panel login and logout
- Admin and viewer roles
- User and application management for admins
- Secure API key creation and revocation
- API keys stored only as hashes
- Audit event ingestion through the `X-API-Key` header
- Event listing, filtering, pagination, and detail views
- Immutable events with no update or delete endpoints

## Requirements

- Docker Desktop or Docker Engine
- Docker Compose
- Git, if the repository needs to be cloned

Python, Node.js, and PostgreSQL do not need to be installed separately. They run inside Docker containers.

## Initial setup

Open PowerShell and move to the repository root:

```powershell
cd "<project-directory>"
```

Create `.env` from the example file only if `.env` does not already exist:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Generate a secure session secret:

```powershell
[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

Open `.env` and replace these example values:

- `SESSION_SECRET`: Use the random value generated above.
- `POSTGRES_PASSWORD`: Choose a strong password used only for local development.

Never put real secrets, passwords, or API keys in `.env.example` or source code.

## Start the application

Build and start the services in the background:

```powershell
docker compose up -d --build
```

Check the service status:

```powershell
docker compose ps
```

The `database`, `api`, and `frontend` services should show a running or healthy status.

## Database migrations

Create or update the database tables with Alembic:

```powershell
docker compose exec api alembic upgrade head
```

Display the current migration revision:

```powershell
docker compose exec api alembic current
```

## Create the first admin

Run the secure CLI command after applying the migration:

```powershell
docker compose exec api python -m app.cli create-admin
```

The command asks for a username, password, and password confirmation. The password is hidden while typing and must contain at least 12 characters.

## Application URLs

- Web panel: http://localhost:5173
- API documentation: http://localhost:8000/docs
- API health check: http://localhost:8000/api/health
- Database readiness check: http://localhost:8000/api/health/ready

## Roles

### Admin

- Create and activate or deactivate panel users.
- Create and activate or deactivate applications.
- Create, list, and revoke API keys.
- View and filter audit events.

### Viewer

- View and filter audit events.
- Requests to admin endpoints receive a `403 Forbidden` response.

## Create an API key

1. Sign in to the web panel as an admin.
2. Open the "Administration" page.
3. Create an application or select an existing application.
4. Enter a key name and select "Create API key".
5. Copy the complete key immediately.

The complete API key is displayed only once. The database stores the hash instead of the original key. A lost key cannot be recovered, so a new key must be created.

## Send an example audit event

Run the following commands in PowerShell. The first command requests the API key at runtime, so the key is not written into source code or command history:

```powershell
$apiKey = Read-Host "Paste the API key"
$headers = @{ "X-API-Key" = $apiKey }
$eventBody = @{
    actor_id = "user-42"
    action = "invoice.updated"
    resource_type = "invoice"
    resource_id = "inv-1001"
    old_values = @{ status = "draft" }
    new_values = @{ status = "sent" }
    ip_address = "192.0.2.10"
    metadata = @{ source = "billing-api" }
    occurred_at = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/events" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $eventBody

Remove-Variable apiKey, headers, eventBody
```

A successful request returns `201 Created`. The backend automatically records the source application and the server receipt time.

An audit event contains:

- `actor_id`
- `action`
- `resource_type`
- `resource_id`
- Optional `old_values` and `new_values` JSON objects
- Optional `ip_address`
- Optional `metadata` JSON object
- `occurred_at` with timezone information

## Event filters

The web panel supports these filters:

- Application ID
- Actor ID
- Action
- Resource type
- Start and end date

Text filters use exact matching. The event list displays 20 records per page.

## Run tests

Run all backend tests:

```powershell
docker compose exec api python -m pytest
```

Verify that the frontend can produce a production build:

```powershell
docker compose exec frontend npm run build
```

## View logs

Follow the API logs:

```powershell
docker compose logs -f api
```

Press `Ctrl+C` to stop following the logs. The application does not intentionally log passwords or API keys.

## Stop the services

Stop the containers:

```powershell
docker compose down
```

This command does not remove the Docker volume that stores PostgreSQL data.

## Security notes

- Panel passwords are hashed with Argon2id.
- API keys are cryptographically secure random values, and only their SHA-256 hashes are stored.
- The session cookie uses `HttpOnly` and `SameSite=Lax` settings.
- In production mode, the session cookie is sent only over HTTPS.
- CORS allows only the `FRONTEND_ORIGIN` value configured in `.env`.
- Authorization checks are enforced by the backend as well as the React interface.
- `.env`, cache files, `node_modules`, build output, and local database files are excluded from Git.

