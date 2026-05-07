# Interior AI Backend — MVP

Backend API for an AI-powered interior design platform. Allows creating real estate projects, uploading interior images, generating commercial design variants with AI, analyzing scenes, comparing results, and manually evaluating viability.

## Tech Stack

- **FastAPI** — async REST API
- **PostgreSQL** — relational database with JSONB
- **Redis + Celery** — async task processing
- **OpenAI Images API** — AI image generation (gpt-image-1)
- **Pillow** — thumbnails and image processing
- **SQLAlchemy 2.0 + Alembic** — ORM and migrations
- **Docker Compose** — full stack orchestration
- **structlog** — JSON structured logging

## Architecture

Hexagonal Architecture (Ports & Adapters) with Clean Architecture principles:

```
app/
├── domain/          # Pure business logic (no framework dependencies)
├── application/     # Use cases + port interfaces
├── infrastructure/  # Adapters (DB, storage, AI providers, Celery)
├── api/             # FastAPI routers, schemas, middleware
└── config/          # Settings and logging
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- An OpenAI API key (for AI generation features)
- `make` (comes pre-installed on macOS and Linux)

### 1. Clone and configure

```bash
git clone <repo-url>
cd bob-api

# Create .env from example (only needed for local tooling outside Docker)
cp .env.example .env
```

The `OPENAI_API_KEY` can be passed as an environment variable when starting:

```bash
OPENAI_API_KEY=sk-proj-your-key docker compose up --build
```

Or set it in your shell before running any `make` command:

```bash
export OPENAI_API_KEY=sk-proj-your-key
```

### 2. Start the stack

```bash
make build
```

This will:
- Build the FastAPI app image
- Start PostgreSQL, Redis, the API server, and a Celery worker
- Run database migrations automatically
- Serve the API at `http://localhost:8010`

### 3. Verify it's running

```bash
curl http://localhost:8010/api/v1/health
```

Expected response:
```json
{"status": "ok", "env": "development", "db": "ok", "redis": "ok", "version": "1.0.0"}
```

### 4. Open API docs

Visit: http://localhost:8010/docs

---

## Make Commands

All operations go through Docker. Run `make help` to see all available commands.

### Stack

```bash
make build        # Build and start all services
make up           # Start services (no rebuild)
make down         # Stop and remove containers
make down-v       # Stop and remove containers + volumes (clean slate)
make restart      # Restart all services
make ps           # Show running containers
```

### Logs

```bash
make logs         # Tail all logs
make logs-api     # Tail API logs only
make logs-worker  # Tail Celery worker logs only
```

### Database

```bash
make migrate                    # Run pending migrations
make migration m="add users"    # Create a new migration
make migrate-down               # Rollback last migration
make db-refresh                 # Drop all tables and re-run migrations (fresh start)
```

### Testing

```bash
make test         # Run all tests
make test-unit    # Unit tests only (use cases with mocks)
make test-int     # Integration tests only (API endpoints)
make test-props   # Property-based tests only (Hypothesis)
make test-e2e     # End-to-end flow tests
make test-cov     # All tests with coverage report
```

### Shell

```bash
make shell        # Open bash inside the API container
```

---

## Testing with Postman

### Import the collection

1. Open Postman
2. Import → File → select `postman/Interior_AI_Backend.postman_collection.json`
3. The collection uses a `base_url` variable set to `http://localhost:8010/api/v1`

### Testing flow (step by step)

Follow this order to test the complete system:

#### Step 1: Health Check
- Run **Health Check** → verify `status: "ok"`

#### Step 2: Create a Project
- Run **Create Project** → saves `project_id` automatically

#### Step 3: Upload an Image
- Run **Upload Image** → select a JPEG/PNG/WebP file from your computer
- Saves `image_id` automatically
- Verify: response has `url` and `thumbnail_url`, no `storage_path`

#### Step 4: Request a Generation
- Run **Request Generation - Commercial Enhancement**
- Verify: status 202, `status: "pending"`
- Saves `generation_id` automatically

#### Step 5: Check Generation Status
- Run **Get Generation Status**
- If using mock provider: status will stay "pending" (worker needs real OpenAI key)
- With real OpenAI key: status transitions pending → analyzing → generating → completed

#### Step 6: Scene Analysis
- Run **Request Scene Analysis** → status 202
- Run **Get Scene Inventory** → returns structured JSON of the scene

#### Step 7: Compare Results
- Run **Get Image Comparison** → returns original + all variants with URLs

#### Step 8: Evaluate a Result
- You need a `variant_id` (from a completed generation)
- Run **Create Evaluation** with scores 1-5 for each dimension
- Run **Get Evaluation** to verify
- Run **Update Evaluation** to change specific scores

#### Step 9: Check Stats
- Run **Get Stats by Provider** → see generation counts grouped by AI provider

---

## API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/health` | Health check (DB + Redis) |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects` | List projects (paginated) |
| GET | `/api/v1/projects/{id}` | Get project |
| PATCH | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Delete project |
| POST | `/api/v1/projects/{id}/images` | Upload image (multipart) |
| GET | `/api/v1/projects/{id}/images` | List images (paginated) |
| GET | `/api/v1/images/{id}` | Get image metadata |
| GET | `/api/v1/images/{id}/download` | Download image file |
| DELETE | `/api/v1/images/{id}` | Delete image |
| POST | `/api/v1/images/{id}/generations` | Request AI generation |
| GET | `/api/v1/images/{id}/generations` | List generations (paginated) |
| GET | `/api/v1/generations/{id}` | Get generation status |
| POST | `/api/v1/images/{id}/scene-inventory` | Request scene analysis |
| GET | `/api/v1/images/{id}/scene-inventory` | Get scene inventory |
| GET | `/api/v1/images/{id}/comparison` | Compare original vs variants |
| POST | `/api/v1/image-variants/{id}/evaluation` | Create evaluation |
| GET | `/api/v1/image-variants/{id}/evaluation` | Get evaluation |
| PATCH | `/api/v1/evaluations/{id}` | Update evaluation |
| GET | `/api/v1/stats/generations` | Generation statistics |

---

## Generation Modes

| Mode | Description | Example Presets |
|---|---|---|
| `commercial_enhancement` | Enhance for commercial appeal | (default) |
| `style_redesign` | Full style transformation | `modern_mediterranean`, `premium_contemporary`, `urban_contemporary` |
| `functional_variant` | Change room function | `living_tv_wall`, `dining_room`, `home_office_lounge` |
| `localized_edit` | Change one element only | `localized_wall_art`, `localized_sofa`, `localized_rug`, `localized_tv_cabinet`, `localized_remove_plants`, `localized_wall_color` |

---

## Configuration

All configuration via environment variables (`.env` file):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `REDIS_URL` | — | Redis connection string |
| `OPENAI_API_KEY` | — | OpenAI API key for image generation |
| `STORAGE_LOCAL_PATH` | `/app/media` | Local path for image storage |
| `MAX_UPLOAD_SIZE_MB` | `20` | Max upload file size |
| `ALLOWED_MIME_TYPES` | `image/jpeg,image/png,image/webp` | Allowed upload types |
| `RATE_LIMIT_ENABLED` | `false` | Enable rate limiting |
| `RATE_LIMIT_GENERATIONS_PER_DAY` | `50` | Max generations per day (when enabled) |
| `FLUX_ENABLED` | `false` | Enable FLUX as secondary AI provider |
| `APP_ENV` | `development` | Environment name |
| `LOG_LEVEL` | `INFO` | Logging level |

---

### Development

### Hot reload (local development)

```bash
make build
```

The `docker-compose.override.yml` automatically enables:
- Hot reload (`--reload` flag)
- Source code mounted as volume
- DB exposed on port `5433`, Redis on `6380`

### Add a new migration

```bash
make migration m="add owner table"
make migrate
```

### Production deployment

```bash
docker compose -f docker-compose.prod.yml up -d
```

Production config:
- No exposed DB/Redis ports
- Celery worker with concurrency=4
- No hot reload
- Rate limiting enabled

---

## Project Structure

```
bob-api/
├── app/
│   ├── domain/              # Business entities and rules
│   ├── application/         # Use cases and port interfaces
│   ├── infrastructure/      # DB repos, storage, AI providers, Celery
│   ├── api/                 # FastAPI routers, schemas, middleware
│   └── config/              # Settings and logging
├── tests/
│   ├── unit/                # Use case tests with mocks
│   ├── properties/          # Hypothesis property-based tests
│   └── integration/         # API endpoint tests + e2e flows
├── alembic/                 # Database migrations
├── postman/                 # Postman collection
├── docker-compose.yml       # Development stack
├── docker-compose.prod.yml  # Production stack
├── Dockerfile               # Multi-stage build
├── requirements.txt         # Production dependencies
└── requirements-dev.txt     # Test dependencies
```
