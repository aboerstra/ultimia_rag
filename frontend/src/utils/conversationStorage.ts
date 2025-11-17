// Conversation storage utilities - now using database backend with migration support

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  sources?: string[]
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: string
  updatedAt: string
  messageCount?: number  // From API when loading list
}

const API_BASE = 'http://localhost:8000/api'
const STORAGE_KEY = 'qbr_conversations'
const ACTIVE_CONVERSATION_KEY = 'qbr_active_conversation'
const MIGRATION_KEY = 'qbr_conversations_migrated'

// Check if migration has been completed
const isMigrated = (): boolean => {
  return localStorage.getItem(MIGRATION_KEY) === 'true'
}

// Mark migration as complete
const setMigrated = (): void => {
  localStorage.setItem(MIGRATION_KEY, 'true')
}

// Migrate conversations from localStorage to database
export const migrateToDatabase = async (): Promise<{ success: boolean; message: string }> => {
  try {
    // Get conversations from localStorage
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) {
      setMigrated()
      return { success: true, message: 'No conversations to migrate' }
    }

    const conversations: Conversation[] = JSON.parse(stored)
    
    if (conversations.length === 0) {
      setMigrated()
      return { success: true, message: 'No conversations to migrate' }
    }

    // Send to migration endpoint
    const response = await fetch(`${API_BASE}/conversations/migrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversations })
    })

    if (!response.ok) {
      throw new Error(`Migration failed: ${response.statusText}`)
    }

    const result = await response.json()
    
    // Mark as migrated
    setMigrated()
    
    return {
      success: true,
      message: result.message || `Migrated ${result.migrated_count} conversations`
    }
  } catch (error) {
    console.error('Migration error:', error)
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Migration failed'
    }
  }
}

// Get all conversations (from database only - no localStorage fallback)
export const getConversations = async (): Promise<Conversation[]> => {
  const response = await fetch(`${API_BASE}/conversations`)
  if (!response.ok) {
    throw new Error(`Failed to fetch conversations: ${response.statusText}`)
  }
  
  const data = await response.json()
  
  // Convert API format to internal format
  return data.map((conv: any) => ({
    id: conv.id,
    title: conv.title,
    messages: [], // Messages loaded separately when needed
    createdAt: conv.createdAt,
    updatedAt: conv.updatedAt,
    messageCount: conv.messageCount || 0  // Include message count from API
  }))
}

// Get a single conversation by ID (with messages)
export const getConversation = async (id: string): Promise<Conversation | null> => {
  try {
    const response = await fetch(`${API_BASE}/conversations/${id}`)
    if (!response.ok) {
      if (response.status === 404) return null
      throw new Error('Failed to fetch conversation')
    }
    
    return await response.json()
  } catch (error) {
    console.error('Error loading conversation:', error)
    // Fallback to localStorage
    const conversations = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return conversations.find((c: Conversation) => c.id === id) || null
  }
}

// Create a new conversation
export const createConversation = async (): Promise<Conversation> => {
  const newConversation: Conversation = {
    id: `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    title: 'New Chat',
    messages: [{
      id: '1',
      role: 'system',
      content: '👋 Hi! I can answer questions about your Jira issues, Clockify hours, Salesforce metrics, and meeting transcripts. What would you like to know?',
      timestamp: new Date().toISOString()
    }],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }

  try {
    const response = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newConversation)
    })

    if (!response.ok) throw new Error('Failed to create conversation')
    
    await setActiveConversationId(newConversation.id)
    return newConversation
  } catch (error) {
    console.error('Error creating conversation:', error)
    // Fallback to localStorage
    const conversations = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    conversations.unshift(newConversation)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.slice(0, 50)))
    await setActiveConversationId(newConversation.id)
    return newConversation
  }
}

// Update a conversation
export const updateConversation = async (id: string, updates: Partial<Conversation>): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: updates.title,
        updatedAt: updates.updatedAt || new Date().toISOString()
      })
    })

    if (!response.ok) throw new Error('Failed to update conversation')
  } catch (error) {
    console.error('Error updating conversation:', error)
    // Fallback to localStorage
    const conversations = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    const index = conversations.findIndex((c: Conversation) => c.id === id)
    if (index !== -1) {
      conversations[index] = {
        ...conversations[index],
        ...updates,
        updatedAt: new Date().toISOString()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
    }
  }
}

// Delete a conversation
export const deleteConversation = async (id: string): Promise<void> => {
  const response = await fetch(`${API_BASE}/conversations/${id}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    throw new Error(`Failed to delete conversation: ${response.statusText}`)
  }
  
  // If deleted conversation was active, clear active ID
  if (await getActiveConversationId() === id) {
    localStorage.removeItem(ACTIVE_CONVERSATION_KEY)
  }
}

// Add a message to a conversation
export const addMessage = async (conversationId: string, message: Message): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message)
    })

    if (!response.ok) throw new Error('Failed to add message')
    
    // Auto-generate title from first user message if still "New Chat"
    const conversation = await getConversation(conversationId)
    if (conversation && conversation.title === 'New Chat' && message.role === 'user') {
      await updateConversation(conversationId, {
        title: generateTitle(message.content)
      })
    }
  } catch (error) {
    console.error('Error adding message:', error)
    // Fallback to localStorage
    const conversation = await getConversation(conversationId)
    if (conversation) {
      conversation.messages.push(message)
      await updateConversation(conversationId, {
        messages: conversation.messages,
        title: conversation.title === 'New Chat' && message.role === 'user' 
          ? generateTitle(message.content)
          : conversation.title
      })
    }
  }
}

// Delete a message from a conversation
export const deleteMessage = async (conversationId: string, messageId: string): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages/${messageId}`, {
      method: 'DELETE'
    })

    if (!response.ok) throw new Error('Failed to delete message')
  } catch (error) {
    console.error('Error deleting message:', error)
    // Fallback to localStorage
    const conversation = await getConversation(conversationId)
    if (conversation) {
      conversation.messages = conversation.messages.filter(m => m.id !== messageId)
      await updateConversation(conversationId, {
        messages: conversation.messages
      })
    }
  }
}

// Get active conversation ID
export const getActiveConversationId = async (): Promise<string | null> => {
  return localStorage.getItem(ACTIVE_CONVERSATION_KEY)
}

// Set active conversation ID
export const setActiveConversationId = async (id: string): Promise<void> => {
  localStorage.setItem(ACTIVE_CONVERSATION_KEY, id)
}

// Generate a title from the first user message
export const generateTitle = (content: string): string => {
  // Take first 50 characters and add ellipsis if needed
  const trimmed = content.trim().slice(0, 50)
  return trimmed.length < content.trim().length ? `${trimmed}...` : trimmed
}

// Group conversations by date
export interface GroupedConversations {
  today: Conversation[]
  yesterday: Conversation[]
  last7Days: Conversation[]
  last30Days: Conversation[]
  older: Conversation[]
}

export const groupConversationsByDate = (conversations: Conversation[]): GroupedConversations => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const last7Days = new Date(today)
  last7Days.setDate(last7Days.getDate() - 7)
  const last30Days = new Date(today)
  last30Days.setDate(last30Days.getDate() - 30)

  return conversations.reduce((groups, conv) => {
    const convDate = new Date(conv.updatedAt)
    
    if (convDate >= today) {
      groups.today.push(conv)
    } else if (convDate >= yesterday) {
      groups.yesterday.push(conv)
    } else if (convDate >= last7Days) {
      groups.last7Days.push(conv)
    } else if (convDate >= last30Days) {
      groups.last30Days.push(conv)
    } else {
      groups.older.push(conv)
    }
    
    return groups
  }, {
    today: [],
    yesterday: [],
    last7Days: [],
    last30Days: [],
    older: []
  } as GroupedConversations)
}

// Clear all conversations (use with caution) - only clears localStorage
export const clearAllConversations = (): void => {
  localStorage.removeItem(STORAGE_KEY)
  localStorage.removeItem(ACTIVE_CONVERSATION_KEY)
  localStorage.removeItem(MIGRATION_KEY)
}

// Save conversations (for backward compatibility - no-op now)
export const saveConversations = (conversations: Conversation[]): void => {
  // This is now a no-op since we use the database
  console.warn('saveConversations is deprecated - conversations are automatically saved to database')
}

// BACKUP & RESTORE FUNCTIONS

/**
 * Export all conversations from localStorage to a JSON file
 * This creates a downloadable backup of all your chat history
 */
export const exportConversationsToJSON = (): void => {
  try {
    // Get conversations from localStorage
    const stored = localStorage.getItem(STORAGE_KEY)
    const conversations: Conversation[] = stored ? JSON.parse(stored) : []
    
    if (conversations.length === 0) {
      alert('No conversations to export')
      return
    }
    
    // Create backup object with metadata
    const backup = {
      exportDate: new Date().toISOString(),
      version: '1.0',
      conversationCount: conversations.length,
      conversations: conversations
    }
    
    // Convert to JSON string
    const jsonString = JSON.stringify(backup, null, 2)
    
    // Create blob and download
    const blob = new Blob([jsonString], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `qbr-conversations-backup-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    console.log(`✅ Exported ${conversations.length} conversations to JSON file`)
  } catch (error) {
    console.error('Export error:', error)
    alert('Failed to export conversations. Check console for details.')
  }
}

/**
 * Import conversations from a JSON backup file
 * This will MERGE with existing conversations (won't overwrite)
 */
export const importConversationsFromJSON = (file: File): Promise<{ success: boolean; message: string; imported: number }> => {
  return new Promise((resolve) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        const backup = JSON.parse(content)
        
        // Validate backup format
        if (!backup.conversations || !Array.isArray(backup.conversations)) {
          resolve({
            success: false,
            message: 'Invalid backup file format',
            imported: 0
          })
          return
        }
        
        // Get existing conversations
        const stored = localStorage.getItem(STORAGE_KEY)
        const existing: Conversation[] = stored ? JSON.parse(stored) : []
        const existingIds = new Set(existing.map(c => c.id))
        
        // Filter out conversations that already exist (by ID)
        const newConversations = backup.conversations.filter((c: Conversation) => !existingIds.has(c.id))
        
        if (newConversations.length === 0) {
          resolve({
            success: true,
            message: 'All conversations from backup already exist',
            imported: 0
          })
          return
        }
        
        // Merge new conversations with existing
        const merged = [...existing, ...newConversations]
        
        // Save back to localStorage
        localStorage.setItem(STORAGE_KEY, JSON.stringify(merged))
        
        console.log(`✅ Imported ${newConversations.length} new conversations`)
        console.log(`   Skipped ${backup.conversations.length - newConversations.length} duplicates`)
        
        resolve({
          success: true,
          message: `Imported ${newConversations.length} conversations (${backup.conversations.length - newConversations.length} duplicates skipped)`,
          imported: newConversations.length
        })
      } catch (error) {
        console.error('Import error:', error)
        resolve({
          success: false,
          message: error instanceof Error ? error.message : 'Failed to import',
          imported: 0
        })
      }
    }
    
    reader.onerror = () => {
      resolve({
        success: false,
        message: 'Failed to read file',
        imported: 0
      })
    }
    
    reader.readAsText(file)
  })
}

/**
 * Get conversation count from localStorage
 */
export const getLocalStorageConversationCount = (): number => {
  const stored = localStorage.getItem(STORAGE_KEY)
  const conversations: Conversation[] = stored ? JSON.parse(stored) : []
  return conversations.length
}

/**
 * Load conversations directly from localStorage (bypassing API)
 * Use this to ensure you're always reading from your local backup
 */
export const getLocalStorageConversations = (): Conversation[] => {
  const stored = localStorage.getItem(STORAGE_KEY)
  return stored ? JSON.parse(stored) : []
}
