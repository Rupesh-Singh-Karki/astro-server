# API Endpoints Reference

Complete reference for all available API endpoints in the astro-server application.

**Base URL:** `http://localhost:8000` (Development) | `https://your-domain.com` (Production)

**Version:** 1.0.0

**Architecture:** RESTful API with JWT authentication

---

## Quick Integration Guide

### Authentication Flow
1. Send OTP → `POST /auth/send-otp`
2. Verify OTP → `POST /auth/verify-otp` (returns token + `has_profile` flag)
3. If `has_profile: false` → Register details → `POST /auth/register-details`
4. If `has_profile: true` → Access chat features

### Authorization Header
All authenticated endpoints require:
```
Authorization: Bearer <access_token>
```

### Response Format
- **Success:** JSON object with requested data
- **Error:** `{"detail": "Error message"}`

### Content Type
All requests/responses use `application/json`

---

## Table of Contents

1. [Health Check](#health-check)
2. [Authentication Endpoints](#authentication-endpoints)
   - [Detecting First-Time Users](#detecting-first-time-users)
3. [Chat & Astrology Endpoints](#chat--astrology-endpoints)

---

## Health Check

### GET `/`

Check if the API is running and healthy.

**Authentication:** Not required

**Request:**
```http
GET / HTTP/1.1
```

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "astro-server API is running"
}
```

---

## Authentication Endpoints

All authentication endpoints are prefixed with `/auth`.

### Detecting First-Time Users

The `/auth/verify-otp` endpoint returns a `has_profile` boolean field that indicates whether the user has completed their profile:

- **`has_profile: false`** → First-time user who needs to complete profile via `/auth/register-details`
- **`has_profile: true`** → Returning user with existing profile who can directly access chat features

This eliminates the need for an additional API call to check profile status. Simply check the `has_profile` field in the verify-otp response to determine the user's onboarding flow.

**Example Response:**
```json
{
  "access_token": "...",
  "has_profile": false,  // ← Check this field
  "user": {...}
}
```

---

### POST `/auth/send-otp`

Send a one-time password (OTP) to the specified email address for authentication.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "OTP sent successfully",
  "email": "user@example.com",
  "expires_in_minutes": 10
}
```

**Error Responses:**
- `500 Internal Server Error` - Failed to send OTP

**Example:**
```bash
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

---

### POST `/auth/verify-otp`

Verify the OTP sent to the email and return an access token if valid.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "is_email_verified": true,
    "created_at": "2025-11-17T10:30:00Z",
    "updated_at": "2025-11-17T10:30:00Z"
  },
  "has_profile": false
}
```

**Response Fields:**
- `access_token` - JWT token for authentication
- `token_type` - Always "bearer"
- `expires_in` - Token expiration time in seconds
- `user` - User information
- `has_profile` - **Boolean indicating if user has completed profile details** (false = first-time user, true = returning user)

**Error Responses:**
- `401 Unauthorized` - Invalid OTP
- `500 Internal Server Error` - Failed to generate authentication token

**Example:**
```bash
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "otp": "123456"}'
```

---

### GET `/auth/me`

Get the currently authenticated user's information.

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "is_email_verified": true,
  "created_at": "2025-11-17T10:30:00Z",
  "updated_at": "2025-11-17T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token

**Example:**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

### POST `/auth/logout`

Logout the current user. Since we use stateless JWT tokens, actual logout should be handled client-side by removing the token.

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token

**Example:**
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

---

### GET `/auth/verify-token`

Verify if the provided JWT token is valid and not expired.

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Token is valid",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token

**Example:**
```bash
curl -X GET http://localhost:8000/auth/verify-token \
  -H "Authorization: Bearer <access_token>"
```

---

### POST `/auth/register-details`

Register detailed information for the authenticated user. This is required before using chat/astrology features.

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "full_name": "John Doe",
  "gender": "male",
  "marital_status": "single",
  "date_of_birth": "1990-05-15",
  "time_of_birth": "14:30:00",
  "place_of_birth": "Mumbai, Maharashtra, India",
  "timezone": "Asia/Kolkata"
}
```

**Field Specifications:**
- `full_name` (string): User's full name
- `gender` (enum): **"male"**, **"female"**, or **"other"**
- `marital_status` (enum): **"single"** or **"married"**
- `date_of_birth` (date): Format **"YYYY-MM-DD"**
- `time_of_birth` (time): Format **"HH:MM:SS"** (24-hour format)
- `place_of_birth` (string): Birth location (city, state, country)
- `timezone` (string): Timezone identifier (e.g., "Asia/Kolkata", "America/New_York")

**Response:** `201 Created`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "gender": "male",
  "marital_status": "single",
  "date_of_birth": "1990-05-15",
  "time_of_birth": "14:30:00",
  "place_of_birth": "Mumbai, Maharashtra, India",
  "timezone": "Asia/Kolkata",
  "created_at": "2025-11-17T10:35:00Z",
  "updated_at": "2025-11-17T10:35:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - User details already exist
- `401 Unauthorized` - Invalid or expired token

**Example:**
```bash
curl -X POST http://localhost:8000/auth/register-details \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "gender": "male",
    "marital_status": "single",
    "date_of_birth": "1990-05-15",
    "time_of_birth": "14:30:00",
    "place_of_birth": "Mumbai, Maharashtra, India",
    "timezone": "Asia/Kolkata"
  }'
```

---

### GET `/auth/user-details`

Get detailed information for the authenticated user.

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "gender": "male",
  "marital_status": "single",
  "date_of_birth": "1990-05-15",
  "time_of_birth": "14:30:00",
  "place_of_birth": "Mumbai, Maharashtra, India",
  "timezone": "Asia/Kolkata",
  "created_at": "2025-11-17T10:35:00Z",
  "updated_at": "2025-11-17T10:35:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token
- `404 Not Found` - User details not found (need to register details first)

**Example:**
```bash
curl -X GET http://localhost:8000/auth/user-details \
  -H "Authorization: Bearer <access_token>"
```

---

### PUT `/auth/user-details`

Update detailed information for the authenticated user. All fields are optional - only provided fields will be updated.

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body (all fields optional):**
```json
{
  "full_name": "Jane Doe",
  "gender": "female",
  "marital_status": "married",
  "date_of_birth": "1990-05-15",
  "time_of_birth": "15:45:00",
  "place_of_birth": "New Delhi, India",
  "timezone": "Asia/Kolkata"
}
```

**Field Specifications:**
- `full_name` (string, optional): User's full name
- `gender` (enum, optional): **"male"**, **"female"**, or **"other"**
- `marital_status` (enum, optional): **"single"** or **"married"**
- `date_of_birth` (date, optional): Format **"YYYY-MM-DD"**
- `time_of_birth` (time, optional): Format **"HH:MM:SS"** (24-hour format)
- `place_of_birth` (string, optional): Birth location (city, state, country)
- `timezone` (string, optional): Timezone identifier (e.g., "Asia/Kolkata", "America/New_York")

**Note:** You can update one or more fields. Fields not included in the request will remain unchanged.

**Response:** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "Jane Doe",
  "gender": "female",
  "marital_status": "married",
  "date_of_birth": "1990-05-15",
  "time_of_birth": "15:45:00",
  "place_of_birth": "New Delhi, India",
  "timezone": "Asia/Kolkata",
  "created_at": "2025-11-17T10:35:00Z",
  "updated_at": "2025-11-17T14:20:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token
- `404 Not Found` - User details not found (must register details first via POST endpoint)

**Example (Update only full name and marital status):**
```bash
curl -X PUT http://localhost:8000/auth/user-details \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Doe",
    "marital_status": "married"
  }'
```

**Example (Update birth location and timezone):**
**Example (Update birth location and timezone):**
```bash
curl -X PUT http://localhost:8000/auth/user-details \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "place_of_birth": "London, United Kingdom",
    "timezone": "Europe/London"
  }'
```

---

### DELETE `/auth/me`

Permanently delete the authenticated user's account and all associated data.

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

No response body is returned on successful deletion.

**What gets deleted:**
- User account
- User details (profile information)
- All chat sessions
- All chat messages
- All OTP codes

**⚠️ Warning:** This action is permanent and cannot be undone. All user data will be permanently deleted from the system.

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token
- `500 Internal Server Error` - Failed to delete user account

**Example:**
```bash
curl -X DELETE http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

## Chat & Astrology Endpoints

---

### DELETE `/auth/me`

Permanently delete the authenticated user's account and all associated data.

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

No response body is returned on successful deletion.

**What gets deleted:**
- User account
- User details (profile information)
- All chat sessions
- All chat messages
- All OTP codes

**⚠️ Warning:** This action is permanent and cannot be undone. All user data will be permanently deleted from the system.

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token
- `500 Internal Server Error` - Failed to delete user account

**Example:**
```bash
curl -X DELETE http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

## Chat & Astrology Endpoints

All chat/astrology endpoints are prefixed with `/chat` and require authentication.

### POST `/chat/astrologer`

Chat with a Vedic astrologer AI. Computes a kundli (birth chart) based on provided birth details and returns personalized astrology insights.

**Authentication:** Required (Bearer token + Verified email)

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "birth_year": 1990,
  "birth_month": 5,
  "birth_day": 15,
  "birth_hour": 14,
  "birth_minute": 30,
  "location": {
    "latitude": 19.0760,
    "longitude": 72.8777,
    "timezone": "Asia/Kolkata"
  },
  "question": "What does my birth chart say about my career prospects?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Field Specifications:**
- `birth_year` (integer): Birth year (1900-2100)
- `birth_month` (integer): Birth month (1-12)
- `birth_day` (integer): Birth day (1-31)
- `birth_hour` (integer): Birth hour in 24-hour format (0-23)
- `birth_minute` (integer): Birth minute (0-59)
- `location` (object):
  - `latitude` (float): Latitude in degrees (-90 to 90)
  - `longitude` (float): Longitude in degrees (-180 to 180)
  - `timezone` (string): Timezone identifier
- `question` (string): Question for the astrologer (minimum 1 character)
- `session_id` (string, optional): UUID of existing chat session to continue conversation

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "Based on your birth chart, I can see that your Sun is positioned in Taurus in the 10th house, which is highly favorable for career success. The 10th house represents career, profession, and public standing. With the Sun in this position, you have strong leadership qualities and a natural ability to take charge...",
  "kundli": {
    "planets": {
      "Sun": {
        "sign": "Taurus",
        "house": 10,
        "longitude": 54.23,
        "latitude": 0.0,
        "speed": 0.95
      },
      "Moon": {
        "sign": "Cancer",
        "house": 1,
        "longitude": 102.45,
        "latitude": 5.12,
        "speed": 13.2
      },
      "Mars": {
        "sign": "Leo",
        "house": 2,
        "longitude": 134.67,
        "latitude": 1.23,
        "speed": 0.52
      }
    },
    "houses": {
      "1": {
        "sign": "Cancer",
        "degree": 15.23
      },
      "2": {
        "sign": "Leo",
        "degree": 10.45
      },
      "3": {
        "sign": "Virgo",
        "degree": 8.67
      }
    },
    "ascendant": {
      "sign": "Cancer",
      "degree": 15.23
    },
    "dashas": {
      "mahadasha": "Venus",
      "antardasha": "Sun",
      "pratyantar": "Moon",
      "remaining_years": 12.5
    }
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid birth details
- `401 Unauthorized` - Invalid or expired token, or email not verified
- `404 Not Found` - Session ID not found or access denied
- `500 Internal Server Error` - Failed to process astrology request

**Example (New Chat):**
```bash
curl -X POST http://localhost:8000/chat/astrologer \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "birth_year": 1990,
    "birth_month": 5,
    "birth_day": 15,
    "birth_hour": 14,
    "birth_minute": 30,
    "location": {
      "latitude": 19.0760,
      "longitude": 72.8777,
      "timezone": "Asia/Kolkata"
    },
    "question": "What does my birth chart say about my career?"
  }'
```

**Example (Continue Existing Chat):**
```bash
curl -X POST http://localhost:8000/chat/astrologer \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "birth_year": 1990,
    "birth_month": 5,
    "birth_day": 15,
    "birth_hour": 14,
    "birth_minute": 30,
    "location": {
      "latitude": 19.0760,
      "longitude": 72.8777,
      "timezone": "Asia/Kolkata"
    },
    "question": "What about my relationships?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

### GET `/chat/sessions`

Retrieve all chat sessions for the authenticated user.

**Authentication:** Required (Bearer token + Verified email)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (integer, optional): Maximum number of sessions to return (default: 50)

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "What does my birth chart say about my career...",
    "created_at": "2025-11-17T10:30:00Z",
    "message_count": 8
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "Tell me about my health and wellness",
    "created_at": "2025-11-16T15:20:00Z",
    "message_count": 4
  }
]
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token, or email not verified

**Example:**
```bash
curl -X GET "http://localhost:8000/chat/sessions?limit=20" \
  -H "Authorization: Bearer <access_token>"
```

---

### GET `/chat/sessions/{session_id}`

Retrieve a specific chat session with all its messages.

**Authentication:** Required (Bearer token + Verified email)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `session_id` (UUID): ID of the chat session

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "What does my birth chart say about my career...",
  "created_at": "2025-11-17T10:30:00Z",
  "messages": [
    {
      "id": "msg-uuid-1",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "sender": "USER",
      "message": "What does my birth chart say about my career prospects?",
      "created_at": "2025-11-17T10:30:00Z"
    },
    {
      "id": "msg-uuid-2",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "sender": "AI",
      "message": "Based on your birth chart, I can see that your Sun is positioned in Taurus in the 10th house...",
      "created_at": "2025-11-17T10:30:05Z"
    },
    {
      "id": "msg-uuid-3",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "sender": "USER",
      "message": "What about my relationships?",
      "created_at": "2025-11-17T10:32:00Z"
    },
    {
      "id": "msg-uuid-4",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "sender": "AI",
      "message": "Regarding relationships, your Venus is placed in the 7th house...",
      "created_at": "2025-11-17T10:32:05Z"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token, or email not verified
- `404 Not Found` - Session not found or access denied

**Example:**
```bash
curl -X GET http://localhost:8000/chat/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <access_token>"
```

---

### DELETE `/chat/sessions/{session_id}`

Permanently delete a chat session and all its messages.

**Authentication:** Required (Bearer token + Verified email)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `session_id` (UUID): ID of the chat session to delete

**Response:** `204 No Content`

No response body is returned on successful deletion.

**What gets deleted:**
- The chat session
- All messages in the session (cascade delete)

**⚠️ Warning:** This action is permanent and cannot be undone.

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token, or email not verified
- `404 Not Found` - Session not found or access denied
- `500 Internal Server Error` - Failed to delete session

**Example:**
```bash
curl -X DELETE http://localhost:8000/chat/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <access_token>"
```

---

### DELETE `/chat/sessions/{session_id}/messages/{message_id}`

Delete a specific message from a chat session.

**Authentication:** Required (Bearer token + Verified email)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `session_id` (UUID): ID of the chat session
- `message_id` (UUID): ID of the message to delete

**Response:** `204 No Content`

No response body is returned on successful deletion.

**Security:**
- Verifies the session belongs to the authenticated user
- Verifies the message belongs to the specified session
- Returns 404 if either verification fails

**Error Responses:**
- `401 Unauthorized` - Invalid or expired token, or email not verified
- `404 Not Found` - Session/message not found, message not in session, or access denied

**Example:**
```bash
curl -X DELETE http://localhost:8000/chat/sessions/550e8400-e29b-41d4-a716-446655440000/messages/msg-uuid-1 \
  -H "Authorization: Bearer <access_token>"
```

---

## Common Response Codes

| Status Code | Description |
|-------------|-------------|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created successfully |
| `204 No Content` | Request succeeded with no content returned (used for deletions) |
| `400 Bad Request` | Invalid request data |
| `401 Unauthorized` | Authentication required or token invalid |
| `404 Not Found` | Resource not found |
| `500 Internal Server Error` | Server error occurred |

---

## Authentication Flow

1. **Send OTP**: `POST /auth/send-otp` with email
2. **Verify OTP**: `POST /auth/verify-otp` with email and OTP → Receive access token + `has_profile` flag
   - `has_profile: false` → First-time user, redirect to profile setup
   - `has_profile: true` → Returning user, redirect to chat
3. **Register Details** (if `has_profile: false`): `POST /auth/register-details` with user profile (required for chat)
4. **Use Chat**: `POST /chat/astrologer` with access token in Authorization header

---

## Authorization Header Format

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Data Types

### Enums

**GenderEnum:**
- `male`
- `female`
- `other`

**MaritalStatusEnum:**
- `single`
- `married`

**MessageSenderEnum:**
- `USER`
- `AI`

### Date/Time Formats

- **Date**: `YYYY-MM-DD` (e.g., "1990-05-15")
- **Time**: `HH:MM:SS` (24-hour format, e.g., "14:30:00")
- **DateTime**: ISO 8601 format (e.g., "2025-11-17T10:30:00Z")
- **UUID**: Standard UUID format (e.g., "550e8400-e29b-41d4-a716-446655440000")

---

## Rate Limiting

Currently, no rate limiting is implemented. For production deployments, consider adding rate limiting to prevent abuse.

---

## CORS

CORS is enabled for all origins in the current configuration. For production, restrict to specific allowed origins.

---

## Error Response Format

All error responses follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

For validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Interactive API Documentation

The API provides interactive documentation at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to explore and test the API directly from your browser.

---

**Document Version:** 1.1  
**Last Updated:** November 18, 2025
