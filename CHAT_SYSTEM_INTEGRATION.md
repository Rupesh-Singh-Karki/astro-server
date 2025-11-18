# Chat System Integration for Vedic Astrologer

## Overview
The astrology service has been properly integrated with the chat system. The application now maintains persistent chat sessions and message history in the database.

## What Was Done

### 1. Created Chat Service (`src/chat/services/chat_service.py`)
A comprehensive service layer for managing chat sessions and messages:
- **`create_session()`** - Creates a new chat session for a user
- **`get_session()`** - Retrieves a specific session (with access control)
- **`get_user_sessions()`** - Lists all sessions for a user
- **`add_message()`** - Saves a message (USER or AI) to the database
- **`get_session_messages()`** - Retrieves all messages in a session
- **`update_session_title()`** - Updates session title
- **`delete_session()`** - Deletes a session and all its messages

### 2. Updated Schemas (`src/chat/schema.py`)
Added proper request/response schemas:
- **`KundliRequest`** - Now includes optional `session_id` field to continue existing conversations
- **`AstrologyResponse`** - Now includes `session_id` in response
- **`ChatMessageResponse`** - Schema for individual messages
- **`ChatSessionResponse`** - Schema for session list (with message count)
- **`ChatSessionWithMessagesResponse`** - Full session with all messages

### 3. Updated Astrology Routes (`src/chat/routes/astrology_routes.py`)

#### Enhanced `/chat/astrologer` Endpoint
Now properly integrates with chat system:
1. **Session Management**:
   - If `session_id` provided: Retrieves existing session
   - If no `session_id`: Creates new session with auto-generated title from question
   
2. **Message Persistence**:
   - Saves user question as `ChatMessage` with `sender=USER`
   - Saves AI response as `ChatMessage` with `sender=AI`
   - All messages linked to session and user

3. **Returns**:
   - `session_id` - To continue conversation in next request
   - `answer` - AI astrologer's response
   - `kundli` - Complete kundli JSON data

#### New `/chat/sessions` Endpoint
- **GET** `/chat/sessions` - List all user's chat sessions
- Returns: Array of sessions with ID, title, created_at, message_count

#### New `/chat/sessions/{session_id}` Endpoint
- **GET** `/chat/sessions/{session_id}` - Get specific session with all messages
- Returns: Full session data with complete message history
- Includes: sender type (USER/AI), message content, timestamps

### 4. Database Models (Already Existed, Now Used)
The existing chat models are now properly utilized:
- **`ChatSession`** - Stores chat sessions with user_id, title, timestamps
- **`ChatMessage`** - Stores individual messages with session_id, sender (USER/AI), message text

## API Usage Examples

### Starting a New Conversation
```json
POST /chat/astrologer
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
  "question": "What does my birth chart say about my career?"
}

Response:
{
  "session_id": "uuid-here",
  "answer": "Based on your kundli...",
  "kundli": { ... }
}
```

### Continuing Existing Conversation
```json
POST /chat/astrologer
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
  "question": "What about my relationships?",
  "session_id": "previous-session-uuid"
}
```

### Listing User's Sessions
```bash
GET /chat/sessions
```

### Getting Session History
```bash
GET /chat/sessions/{session_id}
```

## Key Features

### ✅ Session Persistence
- All chat sessions saved to database
- Can resume conversations using session_id
- Sessions linked to authenticated users

### ✅ Message History
- Complete message history maintained
- Sender type tracked (USER vs AI)
- Timestamps for all messages
- Messages retrieved in chronological order

### ✅ Access Control
- Sessions scoped to user (via authenticated user)
- Other users cannot access someone else's sessions
- Session validation on retrieval

### ✅ Auto Title Generation
- New sessions automatically titled with first question
- Titles truncated to 50 chars (with "..." suffix if longer)
- Can be updated later via service method

### ✅ Cascading Deletes
- Deleting a session removes all associated messages
- Database relationships properly configured

## Technical Implementation Details

### LLM Integration
- **Dual Provider Support**: Gemini (priority) and OpenAI
- **Auto-detection**: Based on `GEMINI_API_KEY` > `OPENAI_API_KEY` env vars
- **Async Methods**: All LLM calls are async-compatible
- **System Prompt**: Instructs LLM to use only provided kundli data

### Astrology Computation
- **Library**: jyotishyamitra (open-source Vedic astrology)
- **Flexible API**: Supports multiple library version APIs
- **Output**: Structured JSON with planets, houses, ascendant, dashas

### Database
- **ORM**: SQLModel (Pydantic + SQLAlchemy)
- **Async**: Full async database support
- **Relationships**: Proper foreign keys and cascade rules

## Migration from Old Implementation

### Before (Stateless)
```python
# No database persistence
# No session management
# No message history
return {"answer": answer, "kundli": kundli}
```

### After (Stateful)
```python
# Create or get session
session = await chat_service.get_or_create_session(...)

# Save user question
await chat_service.add_message(..., sender=USER)

# Get AI response
answer = await llm_client.ask(...)

# Save AI response
await chat_service.add_message(..., sender=AI)

return {"session_id": session.id, "answer": answer, "kundli": kundli}
```

## Environment Variables Required
```bash
# Choose one or both LLM providers
GEMINI_API_KEY=your_gemini_api_key       # Priority if both set
OPENAI_API_KEY=your_openai_api_key

# Optional: Force specific provider
LLM_PROVIDER=gemini  # or 'openai'
```

## Testing Status
- ✅ All 25 existing tests passing
- ✅ Linters passing (ruff, black, mypy)
- ✅ Type checking clean
- 📝 Integration tests for chat system recommended (future work)

## Future Enhancements
- [ ] Add pagination for session lists and message history
- [ ] Add session search/filter by date or title
- [ ] Add message editing/deletion endpoints
- [ ] Add session export (PDF/JSON download)
- [ ] Add multi-turn conversation context to LLM
- [ ] Add integration tests for chat flow
- [ ] Add rate limiting per session/user
