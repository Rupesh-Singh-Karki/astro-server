# Email OTP Authentication System

A complete email-based One-Time Password (OTP) authentication system for FastAPI.

## Features

- ✅ Email-based authentication using OTP
- ✅ JWT token generation and validation
- ✅ Secure OTP hashing with bcrypt
- ✅ OTP expiration and attempt limiting
- ✅ HTML email templates
- ✅ User creation and email verification
- ✅ Protected route dependencies
- ✅ Token validation endpoints

## Architecture

```
src/auth/
├── model.py                    # SQLAlchemy ORM models
├── schema.py                   # Pydantic schemas
├── services/
│   ├── auth_service.py         # User authentication logic
│   ├── email_service.py        # SMTP email sending
│   ├── otp_service.py          # OTP generation & validation
│   └── dependencies.py         # FastAPI auth dependencies
└── routes/
    └── auth_routes.py          # API endpoints
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# SMTP Configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Astro Server

# OTP Configuration
OTP_LENGTH=6
OTP_EXPIRE_MINUTES=10
OTP_MAX_ATTEMPTS=5

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS512
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=720
```

### Gmail Setup (for SMTP)

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: Mail
   - Select device: Other (Custom name)
   - Copy the generated password
3. Use the app password in `SMTP_PASSWORD`

## API Endpoints

### 1. Send OTP

```http
POST /auth/send-otp
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "OTP sent successfully",
  "email": "user@example.com",
  "expires_in_minutes": 10
}
```

### 2. Verify OTP

```http
POST /auth/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 43200,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "is_email_verified": true,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
}
```

### 3. Get Current User

```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "is_email_verified": true,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

### 4. Verify Token

```http
GET /auth/verify-token
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Token is valid",
  "user_id": "uuid",
  "email": "user@example.com"
}
```

### 5. Logout

```http
POST /auth/logout
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

## Usage in Routes

### Protect Routes with Authentication

```python
from fastapi import APIRouter, Depends
from src.auth.services.dependencies import get_current_user, get_current_verified_user
from src.auth.model import User

router = APIRouter()

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    """Requires valid JWT token."""
    return {"message": f"Hello {current_user.email}"}

@router.get("/verified-only")
async def verified_route(current_user: User = Depends(get_current_verified_user)):
    """Requires valid JWT token AND verified email."""
    return {"message": "This user has verified their email"}
```

### Optional Authentication

```python
from src.auth.services.dependencies import get_optional_user

@router.get("/optional-auth")
async def optional_route(current_user: User | None = Depends(get_optional_user)):
    """Works with or without authentication."""
    if current_user:
        return {"message": f"Hello {current_user.email}"}
    return {"message": "Hello guest"}
```

## Authentication Flow

1. **User requests OTP**: `POST /auth/send-otp`
   - System generates 6-digit OTP
   - OTP is hashed with bcrypt
   - OTP is stored in database with expiration
   - Email sent to user with OTP

2. **User submits OTP**: `POST /auth/verify-otp`
   - System validates OTP against hash
   - Checks expiration and attempt limits
   - Creates user if doesn't exist
   - Marks email as verified
   - Returns JWT access token

3. **User accesses protected routes**
   - Include token in header: `Authorization: Bearer <token>`
   - System validates token signature and expiration
   - Retrieves user from database
   - Provides user object to route handler

## Security Features

- ✅ **OTP Hashing**: All OTPs hashed with bcrypt before storage
- ✅ **Expiration**: OTPs expire after configurable minutes
- ✅ **Attempt Limiting**: Maximum attempts before OTP invalidation
- ✅ **Previous OTP Invalidation**: Old OTPs invalidated when new one requested
- ✅ **JWT Signing**: Tokens signed with HS512 algorithm
- ✅ **Token Expiration**: JWT tokens expire after configurable time
- ✅ **Automatic Cleanup**: Expired OTPs can be cleaned periodically

## Database Models

### User
- `id`: UUID (primary key)
- `email`: String (unique, indexed)
- `is_email_verified`: Boolean
- `created_at`: Timestamp
- `updated_at`: Timestamp

### OTPCode
- `id`: UUID (primary key)
- `email`: String (indexed)
- `otp`: String (hashed)
- `expires_at`: Timestamp
- `attempts`: Integer
- `is_used`: Boolean
- `created_at`: Timestamp

## Running the Application

```bash
# Install dependencies
pip install -r pyproject.toml

# Run database migrations (if using Alembic)
alembic upgrade head

# Or initialize tables directly
# Tables are auto-created on startup via init_models()

# Run the application
python src/main.py

# Or with uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing

Test the authentication flow:

```bash
# 1. Send OTP
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 2. Check email for OTP, then verify
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp": "123456"}'

# 3. Use the returned access_token
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Production Considerations

1. **Use HTTPS**: Always use HTTPS in production
2. **Secure JWT Secret**: Use a strong, randomly generated JWT secret
3. **Rate Limiting**: Implement rate limiting on OTP endpoints
4. **Email Service**: Consider using dedicated email service (SendGrid, AWS SES)
5. **Token Blacklisting**: Implement token blacklisting for logout
6. **Refresh Tokens**: Implement refresh tokens for long-lived sessions
7. **Account Lockout**: Lock accounts after repeated failed attempts
8. **Audit Logging**: Log all authentication events
9. **OTP Cleanup**: Set up periodic task to clean expired OTPs

## Troubleshooting

### OTP Email Not Received

1. Check SMTP credentials in `.env`
2. Verify SMTP port (587 for TLS, 465 for SSL)
3. Check spam folder
4. Verify email service allows less secure apps or use app password
5. Check server logs for email sending errors

### Token Invalid/Expired

1. Tokens expire after `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
2. Request new OTP and verify to get fresh token
3. Check system clocks are synchronized

### Database Errors

1. Ensure database is running
2. Verify `DB_URI` in `.env`
3. Run migrations if using Alembic
4. Check database logs

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
