# Frontend API Integration Guide

This document explains all API endpoints, their inputs, responses, and how to use them in your frontend application.

---

## Table of Contents
1. [Authentication & Registration Flow](#authentication--registration-flow)
2. [Chat & Astrology Flow](#chat--astrology-flow)
3. [Complete API Reference](#complete-api-reference)
4. [Frontend Implementation Examples](#frontend-implementation-examples)

---

## Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

All endpoints return JSON responses.

---

## Authentication & Registration Flow

**Important:** Users must complete full registration (email + profile with birth details) before accessing chat features.

### Complete Registration Flow
```
1. User enters email → Receives OTP
2. User verifies OTP → Gets access token (account created if new)
3. User completes profile → Fills birth details and personal info
4. User can now chat → AI uses profile data for personalized astrology
```

---

### Step 1: Request OTP (Start Registration/Login)
**Endpoint:** `POST /auth/generate-otp`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "OTP sent to email successfully",
  "email": "user@example.com"
}
```

**Frontend Usage:**
```typescript
// When user enters email and clicks "Get Started" or "Login"
async function requestOTP(email: string) {
  const response = await fetch('http://localhost:8000/auth/generate-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  
  if (response.ok) {
    showOTPInput();
    showMessage('Check your email for the verification code');
  } else {
    const error = await response.json();
    showError(error.detail);
  }
}
```

---

### Step 2: Verify OTP (Complete Email Verification)
**Endpoint:** `POST /auth/verify-otp`

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
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "is_email_verified": true,
    "created_at": "2025-11-17T10:30:00Z"
  }
}
```

**Frontend Usage:**
```typescript
// When user enters OTP and clicks "Verify"
async function verifyOTP(email: string, otp: string) {
  const response = await fetch('http://localhost:8000/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp })
  });
  
  if (response.ok) {
    const data = await response.json();
    
    // Store token
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    // Check if user needs to complete profile
    const hasProfile = await checkUserProfile(data.access_token);
    
    if (!hasProfile) {
      // New user - redirect to profile setup
      navigateToProfileSetup();
    } else {
      // Existing user - redirect to chat
      navigateToChat();
    }
  } else {
    const error = await response.json();
    showError(error.detail);
  }
}
```

---

### Step 3: Complete User Profile (Required for New Users)
**Endpoint:** `POST /auth/register`

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

**Field Descriptions:**
- `full_name` (string): User's full name
- `gender` (enum): **"male"**, **"female"**, or **"other"**
- `marital_status` (enum): **"single"** or **"married"**
- `date_of_birth` (date): Format **"YYYY-MM-DD"**
- `time_of_birth` (time): Format **"HH:MM:SS"** (24-hour format)
- `place_of_birth` (string): Birth location (city, state, country)
- `timezone` (string): Timezone identifier (e.g., "Asia/Kolkata", "America/New_York")

**Why These Fields Matter:**
- Birth date, time, place, and timezone are used to compute accurate Vedic astrology kundli
- Gender and marital status provide context for personalized astrological insights
- This data is automatically used for all future astrology chats

**Response:** `200 OK`
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "full_name": "John Doe",
  "gender": "male",
  "marital_status": "single",
  "date_of_birth": "1990-05-15",
  "time_of_birth": "14:30:00",
  "place_of_birth": "Mumbai, Maharashtra, India",
  "timezone": "Asia/Kolkata",
  "is_email_verified": true,
  "created_at": "2025-11-17T10:30:00Z"
}
```

**Frontend Usage:**
```typescript
// After OTP verification, if new user
async function completeProfile(profileData: {
  full_name: string;
  gender: 'male' | 'female' | 'other';
  marital_status: 'single' | 'married';
  date_of_birth: string;  // YYYY-MM-DD
  time_of_birth: string;  // HH:MM:SS
  place_of_birth: string;
  timezone: string;
}) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(profileData)
  });
  
  if (response.ok) {
    const userData = await response.json();
    
    // Update stored user data
    localStorage.setItem('user', JSON.stringify(userData));
    
    // Now user can access chat
    navigateToChat();
    showMessage('Profile completed! Your birth chart is ready for consultation.');
  } else {
    const error = await response.json();
    showError(error.detail);
  }
}

// Helper to check if profile exists
async function checkUserProfile(token: string) {
  const response = await fetch('http://localhost:8000/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.ok) {
    const user = await response.json();
    // Check if all required profile fields are filled
    return user.full_name && user.date_of_birth && user.time_of_birth && user.place_of_birth;
  }
  return false;
}
```

---

### Step 4: Access Protected Endpoints (After Registration)
For all authenticated endpoints, include the token in the `Authorization` header:

**Note:** Chat endpoints require completed user registration with all birth details filled.

```typescript
const token = localStorage.getItem('access_token');

fetch('http://localhost:8000/chat/astrologer', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(payload)
});
```

---

## User Profile Management

### Get Current User Info
**Endpoint:** `GET /auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "full_name": "John Doe",
  "gender": "male",
  "marital_status": "single",
  "date_of_birth": "1990-05-15",
  "time_of_birth": "14:30:00",
  "place_of_birth": "Mumbai, Maharashtra, India",
  "timezone": "Asia/Kolkata",
  "is_email_verified": true,
  "created_at": "2025-11-17T10:30:00Z"
}
```

**Frontend Usage:**
```typescript
// Check if user profile is complete
async function getCurrentUser() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.ok) {
    const user = await response.json();
    return user;
  } else if (response.status === 401) {
    // Token expired, redirect to login
    logout();
    navigateToLogin();
  }
}
```

---

## Chat & Astrology Flow

**Prerequisites:** User must be registered with completed profile including birth details.

### Flow Overview
```
1. User completes registration (email + profile with birth details)
2. User asks astrology question (no need to re-enter birth info)
3. Backend automatically retrieves birth data from user profile
4. Backend computes kundli using profile data + gets AI response + saves to DB
5. Frontend receives session_id + answer + kundli
6. User asks follow-up question with same session_id
7. Backend uses same profile birth data from database
8. User can view all chat sessions via /chat/sessions
```

**Key Advantage:** Birth details from user profile are automatically used for all astrology calculations. Users don't need to re-enter birth information for each chat - it's seamlessly integrated from their profile!

---

### 1. Ask Astrology Question (New Chat)

**Endpoint:** `POST /chat/astrologer`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "What does my birth chart say about my career prospects?"
}
```

**Note:** Birth details are automatically retrieved from the user's profile. The backend uses:
- `date_of_birth` → Birth date for kundli
- `time_of_birth` → Birth time for accurate planetary positions  
- `place_of_birth` → Converted to latitude/longitude coordinates
- `timezone` → Used for precise time calculations
- `gender` & `marital_status` → For personalized context in AI responses

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "Based on your birth chart, I can see that your Sun is positioned in Taurus in the 10th house, which is highly favorable for career success. Given your marital status as single, this is an excellent time to focus on professional growth. The 10th house represents career, profession, and public standing...",
  "kundli": {
    "planets": {
      "Sun": {"sign": "Taurus", "house": 10, "longitude": 54.23},
      "Moon": {"sign": "Cancer", "house": 1, "longitude": 102.45},
      "Mars": {"sign": "Leo", "house": 2, "longitude": 134.67}
    },
    "houses": {
      "1": {"sign": "Cancer", "degree": 15.23},
      "2": {"sign": "Leo", "degree": 10.45}
    },
    "ascendant": "Cancer",
    "dashas": {
      "mahadasha": "Venus",
      "antardasha": "Sun",
      "pratyantar": "Moon"
    }
  }
}
```

**Frontend Usage:**
```typescript
// User simply asks a question - birth data comes from profile
async function askAstrologer(question: string, sessionId?: string) {
  const token = localStorage.getItem('access_token');
  
  const payload: any = { question };
  if (sessionId) {
    payload.session_id = sessionId;
  }
  
  const response = await fetch('http://localhost:8000/chat/astrologer', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  
  if (response.ok) {
    const data = await response.json();
    
    // Store session_id for follow-up questions
    currentSessionId = data.session_id;
    
    // Display answer to user
    displayAIResponse(data.answer);
    
    // Optionally display kundli chart
    if (showKundli) {
      renderKundliChart(data.kundli);
    }
    
    return data;
  } else {
    const error = await response.json();
    showError(error.detail);
  }
}

// Example: Initial question
askAstrologer("Tell me about my career prospects");
```

---

### 2. Continue Existing Conversation

**Endpoint:** `POST /chat/astrologer` (same endpoint)

**Request Body:**
```json
{
  "question": "What about my relationships and marriage timing?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "Regarding relationships, your Venus is placed in the 7th house which governs partnerships and marriage. Considering you're currently single, the current Mahadasha of Venus suggests...",
  "kundli": { /* same kundli data from profile */ }
}
```

**Frontend Usage:**
```typescript
// When user asks follow-up question
async function askFollowUpQuestion(question: string) {
  const response = await askAstrologer(question, currentSessionId);
  
  // Add to conversation history in UI
  addToConversationHistory({
    type: 'user',
    message: question
  });
  
  addToConversationHistory({
    type: 'ai',
    message: response.answer
  });
}
```

---

### 3. Get All User's Chat Sessions

**Endpoint:** `GET /chat/sessions?limit=50`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (optional): Maximum sessions to return (default: 50)

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

**Frontend Usage:**
```typescript
// Load user's chat history (for sidebar or history page)
async function loadChatSessions() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/chat/sessions?limit=50', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.ok) {
    const sessions = await response.json();
    renderChatList(sessions);
    return sessions;
  }
}
```

---

### 4. Get Specific Chat Session with Full History

**Endpoint:** `GET /chat/sessions/{session_id}`

**Headers:**
```
Authorization: Bearer <access_token>
```

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
      "message": "Based on your birth chart, I can see that your Sun is positioned in Taurus...",
      "created_at": "2025-11-17T10:30:05Z"
    }
  ]
}
```

**Frontend Usage:**
```typescript
// When user clicks on a chat session in sidebar
async function openChatSession(sessionId: string) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`http://localhost:8000/chat/sessions/${sessionId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.ok) {
    const session = await response.json();
    
    currentSessionId = session.id;
    clearConversation();
    
    // Render all messages
    session.messages.forEach(msg => {
      addMessageToUI({
        type: msg.sender === 'USER' ? 'user' : 'ai',
        message: msg.message,
        timestamp: msg.created_at
      });
    });
    
    return session;
  }
}
```

---

## Complete API Reference

### Authentication Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/auth/generate-otp` | POST | No | Request OTP for email |
| `/auth/verify-otp` | POST | No | Verify OTP and get access token |
| `/auth/register` | POST | Yes | Complete user profile with birth details (required before chat) |
| `/auth/me` | GET | Yes | Get current user info |

### Chat/Astrology Endpoints

**Note:** All chat endpoints require completed user registration with birth details.

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/chat/astrologer` | POST | Yes (+ Profile) | Ask astrology question - birth data from profile |
| `/chat/sessions` | GET | Yes (+ Profile) | List all user's chat sessions |
| `/chat/sessions/{id}` | GET | Yes (+ Profile) | Get specific session with messages |

### Health Check

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/` | GET | No | Health check |

---

## Frontend Implementation Examples

### React Example - Complete Flow

```typescript
// hooks/useAuth.ts
import { useState, useEffect } from 'react';

interface User {
  id: string;
  email: string;
  full_name?: string;
  gender?: 'male' | 'female' | 'other';
  marital_status?: 'single' | 'married';
  date_of_birth?: string;
  time_of_birth?: string;
  place_of_birth?: string;
  timezone?: string;
  is_email_verified: boolean;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isRegistered, setIsRegistered] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      const userData = JSON.parse(savedUser);
      setUser(userData);
      
      // Check if profile is complete
      setIsRegistered(
        !!userData.full_name && 
        !!userData.date_of_birth &&
        !!userData.time_of_birth &&
        !!userData.place_of_birth
      );
    }
  }, []);

  const requestOTP = async (email: string) => {
    const response = await fetch('http://localhost:8000/auth/generate-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    
    if (!response.ok) throw new Error('Failed to send OTP');
    return response.json();
  };

  const verifyOTP = async (email: string, otp: string) => {
    const response = await fetch('http://localhost:8000/auth/verify-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp })
    });
    
    if (!response.ok) throw new Error('Invalid OTP');
    
    const data = await response.json();
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    // Check if profile is complete
    setIsRegistered(
      !!data.user.full_name && 
      !!data.user.date_of_birth &&
      !!data.user.time_of_birth &&
      !!data.user.place_of_birth
    );
    
    return data;
  };

  const completeProfile = async (profileData: {
    full_name: string;
    gender: 'male' | 'female' | 'other';
    marital_status: 'single' | 'married';
    date_of_birth: string;
    time_of_birth: string;
    place_of_birth: string;
    timezone: string;
  }) => {
    const response = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(profileData)
    });
    
    if (!response.ok) throw new Error('Failed to complete profile');
    
    const userData = await response.json();
    setUser(userData);
    setIsRegistered(true);
    localStorage.setItem('user', JSON.stringify(userData));
    
    return userData;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setIsRegistered(false);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  };

  return { 
    user, 
    token, 
    isRegistered,
    requestOTP, 
    verifyOTP, 
    completeProfile,
    logout 
  };
}

// components/ProfileSetup.tsx
import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export function ProfileSetup() {
  const { completeProfile } = useAuth();
  const [formData, setFormData] = useState({
    full_name: '',
    gender: 'male' as 'male' | 'female' | 'other',
    marital_status: 'single' as 'single' | 'married',
    date_of_birth: '',
    time_of_birth: '',
    place_of_birth: '',
    timezone: 'Asia/Kolkata'
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await completeProfile(formData);
      window.location.href = '/chat';
    } catch (error) {
      alert('Failed to complete profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-setup">
      <h2>Complete Your Birth Profile</h2>
      <p>We need your birth details to create an accurate astrological chart.</p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Full Name *</label>
          <input
            type="text"
            required
            value={formData.full_name}
            onChange={(e) => setFormData({...formData, full_name: e.target.value})}
          />
        </div>
        
        <div className="form-group">
          <label>Gender *</label>
          <select
            value={formData.gender}
            onChange={(e) => setFormData({...formData, gender: e.target.value as any})}
          >
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>Marital Status *</label>
          <select
            value={formData.marital_status}
            onChange={(e) => setFormData({...formData, marital_status: e.target.value as any})}
          >
            <option value="single">Single</option>
            <option value="married">Married</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>Date of Birth *</label>
          <input
            type="date"
            required
            value={formData.date_of_birth}
            onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})}
          />
        </div>
        
        <div className="form-group">
          <label>Time of Birth * (24-hour format)</label>
          <input
            type="time"
            required
            step="1"
            value={formData.time_of_birth}
            onChange={(e) => setFormData({...formData, time_of_birth: e.target.value + ':00'})}
          />
        </div>
        
        <div className="form-group">
          <label>Place of Birth *</label>
          <input
            type="text"
            required
            value={formData.place_of_birth}
            onChange={(e) => setFormData({...formData, place_of_birth: e.target.value})}
            placeholder="e.g., Mumbai, Maharashtra, India"
          />
        </div>
        
        <div className="form-group">
          <label>Timezone *</label>
          <select
            value={formData.timezone}
            onChange={(e) => setFormData({...formData, timezone: e.target.value})}
          >
            <option value="Asia/Kolkata">IST (Asia/Kolkata)</option>
            <option value="America/New_York">EST (America/New_York)</option>
            <option value="Europe/London">GMT (Europe/London)</option>
            <option value="Asia/Dubai">GST (Asia/Dubai)</option>
          </select>
        </div>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Creating Your Chart...' : 'Complete Profile & Start Chat'}
        </button>
      </form>
    </div>
  );
}

// components/AstrologerChat.tsx
import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export function AstrologerChat() {
  const { token, isRegistered, user } = useAuth();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // Redirect if not registered
  if (!isRegistered) {
    return (
      <div className="registration-required">
        <h2>Complete your profile to start chatting</h2>
        <p>We need your birth details to provide accurate astrological insights.</p>
        <button onClick={() => window.location.href = '/register'}>
          Complete Birth Profile
        </button>
      </div>
    );
  }

  const askQuestion = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    
    try {
      const payload: any = { question };
      if (currentSessionId) {
        payload.session_id = currentSessionId;
      }
      
      const response = await fetch('http://localhost:8000/chat/astrologer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentSessionId(data.session_id);
        
        setMessages(prev => [
          ...prev,
          { sender: 'USER', message: question },
          { sender: 'AI', message: data.answer }
        ]);
        
        setQuestion('');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="user-info">
        <p>Chatting as: {user?.full_name}</p>
        <p>Birth: {user?.date_of_birth} at {user?.time_of_birth}</p>
      </div>
      
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender.toLowerCase()}`}>
            <div className="message-content">{msg.message}</div>
          </div>
        ))}
        {loading && <div className="loading">Consulting your birth chart...</div>}
      </div>
      
      <div className="input-form">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
          placeholder="Ask about career, relationships, health..."
          disabled={loading}
        />
        <button onClick={askQuestion} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │   1. POST /auth/generate-otp         │
        │      { email }                       │
        └──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │   2. POST /auth/verify-otp           │
        │      { email, otp }                  │
        │   → Returns: { access_token, user }  │
        └──────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
    ┌───────────────────┐   ┌─────────────────────┐
    │ 3a. NEW USER      │   │ 3b. EXISTING USER   │
    │ Profile Incomplete│   │ Profile Complete    │
    └───────────────────┘   └─────────────────────┘
                │                     │
                ▼                     │
    ┌───────────────────────────────┐│
    │ 4. POST /auth/register        ││
    │ (complete birth profile)      ││
    │ {full_name, gender,           ││
    │  marital_status, dob, tob,    ││
    │  place, timezone}             ││
    │                               ││
    │ ✓ Birth data saved to DB      ││
    │ ✓ Used for all future chats   ││
    └───────────────────────────────┘│
                │                     │
                └──────────┬──────────┘
                           ▼
             ┌─────────────────────────────┐
             │ NOW CAN ACCESS CHAT         │
             │ (Birth data auto-applied)   │
             └─────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
   ┌────────────────────┐   ┌────────────────────┐
   │ 5a. POST           │   │ 5b. GET            │
   │ /chat/astrologer   │   │ /chat/sessions     │
   │ (with token)       │   │ (with token)       │
   │                    │   │                    │
   │ New chat:          │   │ Returns list of    │
   │ {question}         │   │ previous chats     │
   │                    │   │                    │
   │ Continue:          │   └────────────────────┘
   │ {question,         │            │
   │  session_id}       │            ▼
   │                    │   ┌────────────────────┐
   │ Backend uses       │   │ 6. GET             │
   │ profile birth data │   │ /chat/sessions/{id}│
   │ automatically      │   │ (with token)       │
   │                    │   │                    │
   │ Returns:           │   │ Returns full       │
   │ {session_id,       │   │ conversation       │
   │  answer, kundli}   │   │ history            │
   └────────────────────┘   └────────────────────┘
```

---

## Quick Start Checklist

### For Frontend Developers

**Phase 1: Authentication**
- [ ] Set up base URL constant
- [ ] Implement auth token storage (localStorage/sessionStorage)
- [ ] Create API client with Authorization header
- [ ] Implement OTP flow (email → OTP → token)
- [ ] Store user data after login

**Phase 2: User Registration (Birth Profile)**
- [ ] Check if user profile is complete after OTP verification
- [ ] Create profile setup form with birth details:
  - [ ] Full name
  - [ ] Gender (male/female/other dropdown)
  - [ ] Marital status (single/married dropdown)
  - [ ] Date of birth (date picker)
  - [ ] Time of birth (time picker with seconds)
  - [ ] Place of birth (text input)
  - [ ] Timezone (dropdown with common zones)
- [ ] Implement profile completion endpoint call
- [ ] Guard chat routes - redirect to profile setup if incomplete
- [ ] Update stored user data after profile completion
- [ ] Show helpful tooltips explaining why birth data is needed

**Phase 3: Chat Features**
- [ ] Implement chat interface (only accessible after registration)
- [ ] Display user's birth info in UI (for reference)
- [ ] Simple question input (no birth data entry needed)
- [ ] Store session_id for follow-up questions
- [ ] Add chat history sidebar
- [ ] Implement session loading
- [ ] Add loading states ("Consulting your birth chart...")
- [ ] Add error handling

**Phase 4: Security & UX**
- [ ] Handle 401 errors (token expiration)
- [ ] Implement logout functionality
- [ ] Add "Complete Profile" prompts with birth data emphasis
- [ ] Add loading spinners
- [ ] Add error messages
- [ ] Show "using birth data from profile" indicators

---

### Testing Your Integration

```bash
# 1. Start the backend
cd astro-server
uv run uvicorn src.main:app --reload

# 2. Test health check
curl http://localhost:8000/

# 3. Test OTP generation
curl -X POST http://localhost:8000/auth/generate-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 4. Check your email for OTP, then verify
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp": "123456"}'

# Save the access_token from response

# 5. Complete profile with birth details (required for new users)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "full_name": "Test User",
    "gender": "male",
    "marital_status": "single",
    "date_of_birth": "1990-05-15",
    "time_of_birth": "14:30:00",
    "place_of_birth": "Mumbai, Maharashtra, India",
    "timezone": "Asia/Kolkata"
  }'

# 6. Check user profile (should have all birth details)
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# 7. Now you can chat - no need to send birth data again!
curl -X POST http://localhost:8000/chat/astrologer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "question": "Tell me about my career prospects"
  }'
```

---

## Environment Setup

Make sure these environment variables are set on the backend:

```bash
# Required for authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Required for LLM (choose one or both)
GEMINI_API_KEY=your-gemini-api-key
# OR
OPENAI_API_KEY=your-openai-api-key

# Email (for OTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

---

## Key Benefits of This Flow

1. **One-Time Birth Data Entry**: Users enter their birth details once during registration
2. **Seamless Chat Experience**: No need to repeatedly enter birth information for each question
3. **Personalized Responses**: AI has access to complete birth profile for contextual answers
4. **Data Consistency**: Same accurate birth data used for all astrological calculations
5. **User Convenience**: Focus on asking questions, not filling forms

---

## Support

For questions or issues:
1. Check this documentation
2. Review the API response errors
3. Check backend logs
4. Open an issue on GitHub

---

**Document Version:** 2.0  
**Last Updated:** November 17, 2025
