# Conversation Persistence Implementation

## Overview

Conversations are now persisted in a SQLite database instead of browser localStorage. This ensures your chat history is safe, accessible across devices/browsers, and won't be lost when clearing browser cache.

## Key Features

✅ **Automatic Migration**: Existing conversations in localStorage are automatically migrated to the database on first load  
✅ **Zero Data Loss**: The migration is safe and preserves all your conversation history  
✅ **Fallback Support**: If the database is unavailable, the system falls back to localStorage  
✅ **Database Backend**: Uses SQLite with SQLAlchemy ORM for reliability  
✅ **RESTful API**: Full CRUD operations via FastAPI endpoints  

## Architecture

### Database Schema

**Conversations Table:**
- `id` (String, Primary Key): Unique conversation identifier
- `title` (String): Conversation title (auto-generated from first message)
- `created_at` (DateTime): When the conversation was created
- `updated_at` (DateTime): Last modification timestamp

**Messages Table:**
- `id` (String, Primary Key): Unique message identifier
- `conversation_id` (String, Foreign Key): Links to conversation
- `role` (String): 'user', 'assistant', or 'system'
- `content` (Text): Message content
- `timestamp` (DateTime): When the message was sent
- `sources` (Text): Optional JSON array of sources

### File Structure

```
api/
├── models.py              # SQLAlchemy database models
└── main.py                # FastAPI endpoints for conversations

frontend/src/utils/
└── conversationStorage.ts # Updated storage utilities (now async)

data-sources/
└── conversations.db       # SQLite database (auto-created)
```

## API Endpoints

### Conversation Management

**GET `/api/conversations`**
- Lists all conversations (without messages)
- Returns: Array of conversation summaries

**GET `/api/conversations/{id}`**
- Gets a single conversation with all messages
- Returns: Full conversation object

**POST `/api/conversations`**
- Creates a new conversation
- Body: Full conversation object
- Returns: Success confirmation

**PUT `/api/conversations/{id}`**
- Updates conversation metadata (title, timestamps)
- Body: Partial conversation update
- Returns: Success confirmation

**DELETE `/api/conversations/{id}`**
- Deletes a conversation and all its messages
- Returns: Success confirmation

### Message Management

**POST `/api/conversations/{id}/messages`**
- Adds a message to a conversation
- Body: Message object
- Returns: Success confirmation

**DELETE `/api/conversations/{id}/messages/{message_id}`**
- Deletes a specific message
- Returns: Success confirmation

### Migration

**POST `/api/conversations/migrate`**
- Migrates conversations from localStorage to database
- Body: Array of conversations from localStorage
- Returns: Migration summary (count migrated, skipped, errors)

## Migration Process

### Automatic Migration

The migration happens automatically when you first load the app after the update:

1. **Detection**: System checks if migration has been completed (via `qbr_conversations_migrated` flag in localStorage)
2. **Data Retrieval**: Reads existing conversations from localStorage (`qbr_conversations` key)
3. **Upload**: Sends all conversations to the `/api/conversations/migrate` endpoint
4. **Validation**: Backend safely handles duplicates (skips conversations that already exist)
5. **Confirmation**: Sets migration flag to prevent re-migration
6. **Fallback**: If migration fails, system continues using localStorage

### Manual Migration

If needed, you can trigger migration manually:

```typescript
import { migrateToDatabase } from './utils/conversationStorage'

const result = await migrateToDatabase()
console.log(result.message)
```

## Installation

### 1. Install SQLAlchemy

```bash
pip install -r requirements.txt
```

The requirements.txt now includes:
```
sqlalchemy==2.0.23
```

### 2. Database Initialization

The database is automatically created when the API starts. No manual setup required!

Location: `/Users/adrianboerstra/projects/maximQBR/data-sources/conversations.db`

### 3. Restart the API

```bash
./restart_api.sh
```

## Usage

### Frontend (TypeScript/React)

All storage functions are now async. Update your code accordingly:

**Before:**
```typescript
const conversations = getConversations()
const conv = getConversation(id)
```

**After:**
```typescript
const conversations = await getConversations()
const conv = await getConversation(id)
```

### Creating a Conversation

```typescript
import { createConversation } from './utils/conversationStorage'

const newConv = await createConversation()
console.log(newConv.id)
```

### Adding a Message

```typescript
import { addMessage } from './utils/conversationStorage'

await addMessage(conversationId, {
  id: '123',
  role: 'user',
  content: 'Hello!',
  timestamp: new Date().toISOString()
})
```

### Deleting a Conversation

```typescript
import { deleteConversation } from './utils/conversationStorage'

await deleteConversation(conversationId)
```

## Data Safety

### Backup

The SQLite database file is stored at:
```
data-sources/conversations.db
```

To backup your conversations:
```bash
cp data-sources/conversations.db data-sources/conversations.backup.db
```

### Recovery

If the database becomes corrupted:

1. Stop the API
2. Delete `data-sources/conversations.db`
3. Restart the API (creates new DB)
4. The system will fall back to localStorage if available
5. Or restore from backup: `cp data-sources/conversations.backup.db data-sources/conversations.db`

### localStorage Preservation

Even after migration, your conversations remain in localStorage as a backup. They will not be used unless the database is unavailable.

To completely clear localStorage after successful migration:
```typescript
import { clearAllConversations } from './utils/conversationStorage'

clearAllConversations() // Only use if you're sure migration was successful!
```

## Troubleshooting

### Migration Failed

**Symptom**: Migration error message on app load

**Solution**:
1. Check that the API is running (`http://localhost:8000`)
2. Verify SQLAlchemy is installed: `pip list | grep SQLAlchemy`
3. Check API logs for errors
4. Manually trigger migration from browser console:
   ```javascript
   // Open browser console (F12)
   // This will attempt migration again
   localStorage.removeItem('qbr_conversations_migrated')
   location.reload()
   ```

### Database Locked

**Symptom**: "Database is locked" errors

**Solution**:
1. Only one API instance should be running
2. Stop all running instances: `pkill -f uvicorn`
3. Restart: `./restart_api.sh`

### Conversations Not Appearing

**Symptom**: Conversations show in database but not in UI

**Solution**:
1. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
2. Clear React state: Close and reopen the tab
3. Check browser console for API errors

## Development

### Viewing Database Contents

```bash
# Install sqlite3 if needed
brew install sqlite3  # Mac
apt-get install sqlite3  # Linux

# Open database
sqlite3 data-sources/conversations.db

# View conversations
SELECT * FROM conversations;

# View messages
SELECT * FROM messages LIMIT 10;

# Exit
.quit
```

### Testing Migration

```bash
# Create a test conversation in localStorage
# (Open browser console)
localStorage.setItem('qbr_conversations', JSON.stringify([{
  id: 'test_123',
  title: 'Test Chat',
  messages: [{
    id: '1',
    role: 'user',
    content: 'Test message',
    timestamp: new Date().toISOString()
  }],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString()
}]))

# Remove migration flag to force re-migration
localStorage.removeItem('qbr_conversations_migrated')

# Reload page - migration should occur
location.reload()
```

## Benefits

1. **Persistence**: Conversations survive browser cache clearing
2. **Portability**: Access your conversations from any browser
3. **Backup**: Easy to backup entire conversation history
4. **Scalability**: Database can handle thousands of conversations
5. **Search**: Future: Full-text search across all conversations
6. **Analytics**: Future: Conversation analytics and insights

## Future Enhancements

- [ ] Full-text search across conversations
- [ ] Conversation export (JSON, Markdown)
- [ ] Conversation sharing/collaboration
- [ ] Conversation tagging and filtering
- [ ] Cloud sync (optional)
- [ ] Conversation analytics dashboard
