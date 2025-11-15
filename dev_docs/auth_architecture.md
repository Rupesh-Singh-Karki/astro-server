# Authentication System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐         ┌──────────────────┐              │
│  │   Auth Routes   │────────>│  Auth Service    │              │
│  │                 │         │                  │              │
│  │ • send-otp     │         │ • send_otp()     │              │
│  │ • verify-otp   │         │ • verify_otp...()│              │
│  │ • /me          │         │ • create_user()  │              │
│  │ • verify-token │         │ • get_user...()  │              │
│  │ • logout       │         └────────┬─────────┘              │
│  └────────┬────────┘                 │                         │
│           │                          │                         │
│           │         ┌────────────────┴──────────────┐         │
│           │         │                                │         │
│           │    ┌────▼──────┐              ┌─────────▼────┐   │
│           │    │OTP Service│              │Email Service │   │
│           │    │           │              │              │   │
│           │    │• generate │              │• send_otp..()│   │
│           │    │• verify   │              │• HTML tmpl   │   │
│           │    │• hash     │              └──────┬───────┘   │
│           │    │• cleanup  │                     │           │
│           │    └─────┬─────┘                     │           │
│           │          │                           │           │
│           └──────────┼───────────────────────────┘           │
│                      │                                        │
│            ┌─────────▼────────┐                              │
│            │   Dependencies    │                              │
│            │                   │                              │
│            │ • get_current..() │                              │
│            │ • get_optional..()│                              │
│            └─────────┬─────────┘                              │
│                      │                                        │
└──────────────────────┼────────────────────────────────────────┘
                       │
            ┌──────────▼───────────┐
            │     Database         │
            │                      │
            │  • users table       │
            │  • otp_codes table   │
            │  • user_details      │
            └──────────────────────┘
```

## Authentication Flow Diagram

```
┌─────────┐                                              ┌─────────┐
│  User   │                                              │  Server │
└────┬────┘                                              └────┬────┘
     │                                                        │
     │ 1. POST /auth/send-otp                                │
     │    {"email": "user@example.com"}                      │
     ├──────────────────────────────────────────────────────>│
     │                                                        │
     │                                    2. Generate OTP     │
     │                                       • Create 6 digits│
     │                                       • Hash with bcrypt│
     │                                       • Store in DB    │
     │                                       • Set expiration │
     │                                                        │
     │                                    3. Send Email       │
     │                                       • SMTP connect   │
     │                                       • HTML template  │
     │<───────────────────────────────────────────────────────│
     │    Email: "Your OTP is: 123456"                       │
     │                                                        │
     │                                                        │
     │ 4. POST /auth/verify-otp                              │
     │    {"email": "user@example.com", "otp": "123456"}     │
     ├──────────────────────────────────────────────────────>│
     │                                                        │
     │                                    5. Validate OTP     │
     │                                       • Check expiry   │
     │                                       • Verify hash    │
     │                                       • Check attempts │
     │                                       • Create/get user│
     │                                       • Mark verified  │
     │                                       • Generate JWT   │
     │                                                        │
     │ 6. {"access_token": "eyJ...", "user": {...}}          │
     │<───────────────────────────────────────────────────────│
     │                                                        │
     │                                                        │
     │ 7. GET /auth/me                                        │
     │    Authorization: Bearer eyJ...                        │
     ├──────────────────────────────────────────────────────>│
     │                                                        │
     │                                    8. Validate Token   │
     │                                       • Verify signature│
     │                                       • Check expiry   │
     │                                       • Get user from DB│
     │                                                        │
     │ 9. {"id": "...", "email": "...", ...}                 │
     │<───────────────────────────────────────────────────────│
     │                                                        │
```

## Component Responsibilities

### 1. Auth Routes (`auth/routes/auth_routes.py`)
- **Purpose**: Handle HTTP requests/responses
- **Responsibilities**:
  - Validate request data
  - Call appropriate services
  - Return formatted responses
  - Handle HTTP errors

### 2. Auth Service (`auth/services/auth_service.py`)
- **Purpose**: Business logic for authentication
- **Responsibilities**:
  - User creation and retrieval
  - Email verification management
  - Coordinate OTP and email services
  - Generate JWT tokens

### 3. OTP Service (`auth/services/otp_service.py`)
- **Purpose**: OTP lifecycle management
- **Responsibilities**:
  - Generate random OTPs
  - Hash OTPs with bcrypt
  - Validate OTPs
  - Track attempts
  - Manage expiration
  - Cleanup expired OTPs

### 4. Email Service (`auth/services/email_service.py`)
- **Purpose**: Email delivery
- **Responsibilities**:
  - Connect to SMTP server
  - Create HTML email templates
  - Send OTP emails
  - Handle email errors

### 5. Dependencies (`auth/services/dependencies.py`)
- **Purpose**: FastAPI dependency injection
- **Responsibilities**:
  - Extract JWT from headers
  - Validate tokens
  - Retrieve user from database
  - Provide user context to routes

### 6. Models (`auth/model.py`)
- **Purpose**: Database table definitions
- **Responsibilities**:
  - Define table structure
  - Define relationships
  - Manage constraints

### 7. Schemas (`auth/schema.py`)
- **Purpose**: Data validation
- **Responsibilities**:
  - Validate request data
  - Format response data
  - Type checking

## Data Flow

### Send OTP Request
```
HTTP Request
    ↓
Auth Route (send_otp)
    ↓
Auth Service (send_otp)
    ↓
OTP Service (create_otp) → Database (save OTP)
    ↓
Email Service (send_otp_email) → SMTP Server → User Email
    ↓
HTTP Response
```

### Verify OTP Request
```
HTTP Request
    ↓
Auth Route (verify_otp)
    ↓
Auth Service (verify_otp_and_authenticate)
    ↓
OTP Service (verify_otp) → Database (check OTP)
    ↓
Auth Service (create_user / get_user) → Database (user)
    ↓
Auth Service (verify_user_email) → Database (update)
    ↓
JWT Utils (create_access_token)
    ↓
HTTP Response (token + user)
```

### Protected Route Access
```
HTTP Request (with Bearer token)
    ↓
Dependency (get_current_user)
    ↓
JWT Utils (decode_token) → Validate signature & expiry
    ↓
Auth Service (get_user_by_id) → Database (fetch user)
    ↓
Route Handler (with user context)
    ↓
HTTP Response
```

## Database Schema

```
┌─────────────────────────┐
│        users            │
├─────────────────────────┤
│ id: UUID (PK)           │
│ email: String (Unique)  │
│ is_email_verified: Bool │
│ created_at: Timestamp   │
│ updated_at: Timestamp   │
└────────┬────────────────┘
         │
         │ 1:1
         │
┌────────▼────────────────┐
│    user_details         │
├─────────────────────────┤
│ id: UUID (PK)           │
│ user_id: UUID (FK)      │
│ full_name: String       │
│ gender: Enum            │
│ marital_status: Enum    │
│ date_of_birth: Date     │
│ time_of_birth: Time     │
│ place_of_birth: String  │
│ timezone: String        │
│ created_at: Timestamp   │
│ updated_at: Timestamp   │
└─────────────────────────┘

┌─────────────────────────┐
│      otp_codes          │
├─────────────────────────┤
│ id: UUID (PK)           │
│ email: String (Indexed) │
│ otp: String (Hashed)    │
│ expires_at: Timestamp   │
│ attempts: Integer       │
│ is_used: Boolean        │
│ created_at: Timestamp   │
└─────────────────────────┘
```

## Security Layers

```
┌───────────────────────────────────────────┐
│          Security Layers                   │
├───────────────────────────────────────────┤
│                                           │
│  1. HTTPS/TLS                             │
│     └─> Encrypted communication           │
│                                           │
│  2. JWT Token Signature                   │
│     └─> HS512 algorithm                   │
│     └─> Secret key validation             │
│                                           │
│  3. Token Expiration                      │
│     └─> Time-limited tokens               │
│                                           │
│  4. OTP Hashing                           │
│     └─> Bcrypt with salt                  │
│                                           │
│  5. OTP Expiration                        │
│     └─> Time-limited codes                │
│                                           │
│  6. Attempt Limiting                      │
│     └─> Max 5 attempts per OTP            │
│                                           │
│  7. OTP Invalidation                      │
│     └─> Previous OTPs invalidated         │
│                                           │
│  8. Email Verification                    │
│     └─> Verified flag tracking            │
│                                           │
└───────────────────────────────────────────┘
```

## Configuration Flow

```
.env file
    ↓
Settings (Pydantic)
    ↓
    ├─> Database Configuration
    │   └─> AsyncEngine → Connection Pool
    │
    ├─> JWT Configuration
    │   └─> Token Creation/Validation
    │
    ├─> SMTP Configuration
    │   └─> Email Service
    │
    └─> OTP Configuration
        └─> OTP Service
```

## Error Handling

```
┌────────────────────────────────────────┐
│           Error Types                   │
├────────────────────────────────────────┤
│                                        │
│  HTTP 400 Bad Request                  │
│  └─> Invalid request format            │
│                                        │
│  HTTP 401 Unauthorized                 │
│  └─> Invalid/expired token             │
│  └─> Invalid OTP                       │
│                                        │
│  HTTP 403 Forbidden                    │
│  └─> Email not verified                │
│                                        │
│  HTTP 500 Internal Server Error        │
│  └─> SMTP connection failure           │
│  └─> Database errors                   │
│                                        │
└────────────────────────────────────────┘
```
