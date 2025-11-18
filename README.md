# Astro Server

A production-ready FastAPI backend with email OTP authentication, user management, and chat functionality.

## Features

- ✅ **Email OTP Authentication** - Secure passwordless login via email
- ✅ **JWT Token Management** - Stateless authentication with HS512
- ✅ **User Management** - User profiles with astrological details
- ✅ **Chat System** - Multi-session chat with AI integration ready
- ✅ **Vedic Astrology** - Kundli computation with Jyotishyamitra
- ✅ **AI Astrologer** - Natural language astrology consultations
- ✅ **Keep-Alive Service** - Automatic background pings (14-minute intervals)
- ✅ **SQLAlchemy 2.0** - Modern async ORM with proper typing
- ✅ **Pydantic V2** - Fast data validation and serialization
- ✅ **PostgreSQL** - Reliable async database with connection pooling
- ✅ **SMTP Email** - HTML email templates with SMTP support

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd astro-server

# Install dependencies
pip install -e .
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: DB_URI, JWT_SECRET_KEY, SMTP credentials, LLM API key
```

**Important:** For chat/astrology features to work, you **must** configure at least one LLM provider:
- **Gemini** (Recommended): Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenAI**: Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)

Add to your `.env` file:
```bash
# Option 1: Use Gemini (free tier available)
GEMINI_API_KEY=your-gemini-api-key-here

# Option 2: Use OpenAI
# OPENAI_API_KEY=your-openai-api-key-here
```

### 3. Initialize Database

```bash
# Option 1: Run init script
python scripts/init_db.py

# Option 2: Let app auto-create tables on startup
```

### 4. Verify Setup

```bash
# Run verification script
python scripts/verify_setup.py
```

### 5. Start Application

```bash
# Development mode
python src/main.py

# Production mode with Gunicorn
gunicorn src.main:app -c gunicorn_conf.py
```

### 6. Test Authentication

```bash
# Send OTP
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com"}'

# Verify OTP (check your email for code)
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "otp": "123456"}'
```

## Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running quickly
- **[Setup Checklist](SETUP_CHECKLIST.md)** - Comprehensive setup verification
- **[Auth Setup](dev_docs/auth_setup.md)** - Complete authentication documentation
- **[Architecture](dev_docs/auth_architecture.md)** - System architecture diagrams
- **[API Docs](http://localhost:8000/docs)** - Interactive Swagger UI (when running)

## Project Structure

```
astro-server/
├── src/
│   ├── auth/                  # Authentication module
│   │   ├── model.py          # User, OTPCode models
│   │   ├── schema.py         # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── otp_service.py
│   │   │   ├── email_service.py
│   │   │   └── dependencies.py
│   │   └── routes/           # API endpoints
│   │       └── auth_routes.py
│   ├── chat/                  # Chat module
│   │   ├── model.py          # ChatSession, ChatMessage models
│   │   ├── schema.py         # Pydantic schemas
│   │   ├── services/         # Business logic (to be implemented)
│   │   └── routes/           # API endpoints (to be implemented)
│   ├── utils/                 # Shared utilities
│   │   ├── db.py             # Database connection
│   │   ├── jwt.py            # JWT utilities
│   │   └── logger.py         # Logging setup
│   ├── config.py             # Configuration management
│   └── main.py               # FastAPI application
├── test/                      # Test suite
│   └── test_auth.py          # Auth tests
├── scripts/                   # Utility scripts
│   ├── init_db.py            # Database initialization
│   └── verify_setup.py       # Setup verification
├── dev_docs/                  # Documentation
│   ├── auth_setup.md
│   ├── auth_architecture.md
│   └── pythonic_guidelines.md
├── .env.example              # Environment template
├── pyproject.toml            # Dependencies
├── docker-compose.yaml       # Docker setup
└── README.md                 # This file
```

## API Endpoints

### Authentication

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/send-otp` | POST | No | Send OTP to email |
| `/auth/verify-otp` | POST | No | Verify OTP and get token |
| `/auth/me` | GET | Yes | Get current user |
| `/auth/me` | DELETE | Yes | Delete user account |
| `/auth/verify-token` | GET | Yes | Verify token validity |
| `/auth/logout` | POST | Yes | Logout user |
| `/auth/register-details` | POST | Yes | Register user details |
| `/auth/user-details` | GET | Yes | Get user details |
| `/auth/user-details` | PUT | Yes | Update user details |

### Chat & Astrology

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/chat/astrologer` | POST | Yes | Chat with AI astrologer |
| `/chat/sessions` | GET | Yes | Get user's chat sessions |
| `/chat/sessions/{session_id}` | GET | Yes | Get session with messages |
| `/chat/sessions/{session_id}` | DELETE | Yes | Delete chat session |
| `/chat/sessions/{session_id}/messages/{message_id}` | DELETE | Yes | Delete specific message |

### Health

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | No | Health check |
| `/health` | GET | No | Health check (for keep-alive) |

## Environment Variables

### Required

```bash
# Database
DB_URI=postgresql+asyncpg://user:password@localhost:5432/astro_db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key

# SMTP
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

### Optional

```bash
# Application
ROOT_PATH=
LOGGING_LEVEL=INFO

# Backend URL (for keep-alive pings)
BASE_URL=http://localhost:8000  # Change to your production URL

# JWT
JWT_ALGORITHM=HS512
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=720

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM_NAME=Astro Server

# OTP
OTP_LENGTH=6
OTP_EXPIRE_MINUTES=10
OTP_MAX_ATTEMPTS=5
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest test/test_auth.py -v
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

### Database Migrations

```bash
# Create migration (if using Alembic)
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Using Authentication

### Protect Routes

```python
from fastapi import APIRouter, Depends
from src.auth.services.dependencies import get_current_user
from src.auth.model import User

router = APIRouter()

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}"}
```

### Optional Authentication

```python
from src.auth.services.dependencies import get_optional_user

@router.get("/optional")
async def optional_route(current_user: User | None = Depends(get_optional_user)):
    if current_user:
        return {"message": f"Hello {current_user.email}"}
    return {"message": "Hello guest"}
```

## Database Models

### Users & Authentication

- **User** - User accounts with email verification
- **UserDetails** - Extended user profile with astrological data
- **OTPCode** - One-time password codes for authentication

### Chat System

- **ChatSession** - Chat conversation sessions
- **ChatMessage** - Individual messages in sessions

## Security Features

- ✅ OTP hashing with bcrypt
- ✅ JWT token signing with HS512
- ✅ Token expiration management
- ✅ Rate limiting on OTP attempts
- ✅ OTP expiration (10 minutes)
- ✅ Previous OTP invalidation
- ✅ Email verification tracking
- ✅ Secure password handling

## Deployment

### Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Checklist

- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure BASE_URL for keep-alive service
- [ ] Use HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Use production email service
- [ ] Set up monitoring
- [ ] Enable rate limiting
- [ ] Configure database backups
- [ ] Set up logging aggregation
- [ ] Implement token refresh
- [ ] Add audit logging

## Background Services

### Keep-Alive Service

The application includes an automatic keep-alive service that pings the `/health` endpoint every 14 minutes. This is useful for:

- **Free-tier hosting**: Prevents apps from sleeping on platforms like Render, Railway, etc.
- **Health monitoring**: Regular health checks ensure the app is responsive
- **Automatic restart**: Helps detect and recover from failures

**Configuration:**
```bash
# Set your production URL in .env
BASE_URL=https://your-app.onrender.com
```

The service starts automatically when the application launches and stops gracefully on shutdown. Logs are available to monitor ping status.

## Troubleshooting

### OTP Email Not Received

1. Check spam folder
2. Verify SMTP credentials in `.env`
3. Use Gmail App Password (not regular password)
4. Check server logs for errors

### Database Connection Error

1. Verify PostgreSQL is running
2. Check DB_URI format
3. Ensure database exists
4. Verify credentials

### Token Validation Error

1. Check JWT_SECRET_KEY is correct
2. Verify token hasn't expired
3. Ensure proper Authorization header format

## Contributing

1. Follow pythonic guidelines in `dev_docs/pythonic_guidelines.md`
2. Write tests for new features
3. Update documentation
4. Run code quality checks before committing

## License

[Your License Here]

## Support

For issues and questions:
- Check documentation in `dev_docs/`
- Review API docs at `/docs`
- Check logs for error details

---

**Made with ❤️ using FastAPI, SQLAlchemy, and Pydantic**
