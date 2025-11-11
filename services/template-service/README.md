# Template Service

A FastAPI-based microservice for managing notification templates with versioning, multi-language support, and Jinja2 rendering.

## Features

- ✅ Template CRUD operations
- ✅ Template versioning with history tracking
- ✅ Multi-language support
- ✅ Jinja2 template rendering with variable substitution
- ✅ Support for EMAIL and PUSH notification templates
- ✅ Automatic variable extraction from templates
- ✅ Template status workflow (DRAFT → ACTIVE → ARCHIVED → DEPRECATED)
- ✅ SQLite for development, PostgreSQL for production
- ✅ RESTful API with OpenAPI/Swagger documentation
- ✅ Predefined templates for common use cases

## Quick Start

### 1. Setup Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
# Copy example env file
Copy-Item .env.example .env

# Edit .env with your settings (optional for defaults)
```

### 3. Seed Database

```powershell
# Run seed script to create predefined templates
python seed_templates.py
```

### 4. Run the Service

```powershell
# Start the server
uvicorn app.main:app --reload --port 8001
```

The service will be available at:
- API: http://localhost:8001
- Swagger Docs: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## API Endpoints

### Template Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/templates/` | Create new template |
| GET | `/api/v1/templates/` | List templates (with filters) |
| GET | `/api/v1/templates/{id}` | Get template by ID |
| GET | `/api/v1/templates/code/{code}` | Get template by code (used by Email Service) |
| PUT | `/api/v1/templates/{id}` | Update template |
| DELETE | `/api/v1/templates/{id}` | Archive template |
| GET | `/api/v1/templates/{id}/versions` | Get version history |
| POST | `/api/v1/templates/{id}/render` | Test render template |
| GET | `/api/v1/templates/health` | Health check |

### Query Parameters

**List Templates** (`GET /api/v1/templates/`):
- `skip`: Number of records to skip (default: 0)
- `limit`: Max records to return (default: 20, max: 100)
- `template_type`: Filter by EMAIL or PUSH
- `status`: Filter by DRAFT, ACTIVE, ARCHIVED, DEPRECATED
- `language`: Filter by language code (e.g., "en", "es")

## Template Structure

### Creating a Template

```json
{
  "template_code": "welcome_email",
  "template_type": "EMAIL",
  "language": "en",
  "subject": "Welcome {{user_name}}!",
  "content": "<h1>Welcome {{user_name}}</h1><p>Your email is {{user_email}}</p>",
  "description": "Welcome email for new users",
  "status": "ACTIVE"
}
```

### Variable Syntax

Templates use Jinja2 syntax for variables:
- `{{variable_name}}` - Simple variable substitution
- Variables are automatically extracted from content
- Required variables are validated before rendering

### Template Types

1. **EMAIL**: Requires `subject` field
2. **PUSH**: No subject needed

### Template Status Workflow

```
DRAFT → ACTIVE → ARCHIVED
           ↓
      DEPRECATED
```

- **DRAFT**: Under development
- **ACTIVE**: Ready for use
- **ARCHIVED**: No longer in use
- **DEPRECATED**: Marked for removal

## Predefined Templates

The seed script creates these templates:
1. `welcome_email` - Welcome email for new users
2. `password_reset` - Password reset email
3. `email_verification` - Email verification
4. `order_confirmation` - Order confirmation email
5. `new_message_push` - Push notification for messages
6. `system_alert_push` - System alert push notification

## Usage Examples

### 1. Create a Template

```bash
curl -X POST "http://localhost:8001/api/v1/templates/" \
  -H "Content-Type: application/json" \
  -d '{
    "template_code": "custom_email",
    "template_type": "EMAIL",
    "language": "en",
    "subject": "Hello {{name}}",
    "content": "<p>Welcome {{name}}, your code is {{code}}</p>",
    "status": "DRAFT"
  }'
```

### 2. Test Render a Template

```bash
curl -X POST "http://localhost:8001/api/v1/templates/{template_id}/render" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "name": "John Doe",
      "code": "ABC123"
    }
  }'
```

### 3. Get Template by Code (Email Service Integration)

```bash
curl "http://localhost:8001/api/v1/templates/code/welcome_email?language=en"
```

### 4. Update Template (Auto-versioning)

```bash
curl -X PUT "http://localhost:8001/api/v1/templates/{template_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "<p>Updated content with {{variable}}</p>",
    "change_log": "Updated wording for clarity"
  }'
```

## Project Structure

```
template-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── templates.py        # Template API routes
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Settings and configuration
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py          # Database session management
│   ├── models/
│   │   ├── __init__.py
│   │   └── template.py         # SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── template.py         # Pydantic schemas
│   └── services/
│       ├── __init__.py
│       └── template_service.py # Business logic
├── tests/                      # Test files (to be added)
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── seed_templates.py           # Database seeding script
└── README.md                   # This file
```

## Database Schema

### Template Table
- `id` (UUID): Primary key
- `template_code` (String): Unique identifier
- `template_type` (Enum): EMAIL or PUSH
- `language` (String): Language code
- `subject` (String): Email subject (nullable)
- `content` (Text): Template content with {{variables}}
- `description` (String): Template description
- `required_variables` (JSON): List of required variables
- `status` (Enum): Template status
- `version` (Integer): Current version number
- `created_at`, `updated_at` (DateTime): Timestamps

### TemplateVersion Table
- `id` (UUID): Primary key
- `template_id` (UUID): Foreign key to Template
- `version_number` (Integer): Version number
- `content`, `subject`, etc.: Historical data
- `change_log` (String): What changed
- `created_at` (DateTime): Timestamp

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| APP_NAME | Application name | "Template Service" |
| PORT | Service port | 8001 |
| DATABASE_URL | Database connection string | "sqlite:///./template_service.db" |
| CORS_ORIGINS | Allowed CORS origins | "http://localhost:3000,http://localhost:8000" |
| DEFAULT_PAGE_SIZE | Default pagination size | 20 |
| MAX_PAGE_SIZE | Max pagination size | 100 |

## Integration with Email Service

The Email Service will call the Template Service to:
1. Fetch templates by code: `GET /api/v1/templates/code/{code}`
2. Render templates with variables (optional, can be done in Email Service)

Example Email Service integration:
```python
# Fetch template
response = httpx.get(f"http://template-service:8001/api/v1/templates/code/welcome_email")
template_data = response.json()["data"]

# Render in Email Service using Jinja2
from jinja2 import Template
template = Template(template_data["content"])
rendered = template.render(user_name="John", user_email="john@example.com")
```

## Development Notes

- **SQLite**: Used for development (single file database)
- **PostgreSQL**: Configure in `.env` for production
- **Versioning**: All template updates create a version history entry
- **Soft Delete**: Templates are archived, not deleted
- **Variable Extraction**: Automatic from `{{variable}}` syntax
- **Validation**: Pydantic schemas enforce data integrity

## Next Steps

1. ✅ Template Service complete
2. 🔄 Add pytest test suite
3. 🔄 Build Email Service
4. 🔄 Add RabbitMQ integration
5. 🔄 Add authentication/authorization
6. 🔄 Deploy to production

## Testing

```powershell
# Install pytest (when ready)
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v
```

## License

Part of HNG Internship Stage 4 - Notification System Project
