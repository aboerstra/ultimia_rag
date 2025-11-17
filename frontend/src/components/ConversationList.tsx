import { useState, useEffect, useRef } from 'react'
import Icon from './Icon'
import './ConversationList.css'
import { 
  getConversations, 
  groupConversationsByDate, 
  createConversation,
  deleteConversation,
  setActiveConversationId,
  type Conversation,
  type GroupedConversations
} from '../utils/conversationStorage'

interface ConversationListProps {
  onConversationChange: (conversationId: string) => void
  activeConversationId: string | null
  onConversationUpdate?: () => void
}

function ConversationList({ onConversationChange, activeConversationId, onConversationUpdate }: ConversationListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [groupedConversations, setGroupedConversations] = useState<GroupedConversations>({
    today: [],
    yesterday: [],
    last7Days: [],
    last30Days: [],
    older: []
  })
  const refreshIntervalRef = useRef<number | null>(null)

  // Start the auto-refresh interval
  const startRefreshInterval = () => {
    // Clear any existing interval first
    if (refreshIntervalRef.current !== null) {
      clearInterval(refreshIntervalRef.current)
    }
    // Start new interval
    refreshIntervalRef.current = window.setInterval(loadConversations, 5000)
  }

  // Stop the auto-refresh interval
  const stopRefreshInterval = () => {
    if (refreshIntervalRef.current !== null) {
      clearInterval(refreshIntervalRef.current)
      refreshIntervalRef.current = null
    }
  }

  // Load conversations on mount and set up refresh
  useEffect(() => {
    loadConversations()
    startRefreshInterval()
    
    return () => stopRefreshInterval()
  }, [])

  const loadConversations = async () => {
    try {
      const allConversations = await getConversations()
      setConversations(allConversations)
      setGroupedConversations(groupConversationsByDate(allConversations))
    } catch (error) {
      console.error('Error loading conversations:', error)
      // On error, just keep current state
    }
  }

  const handleNewChat = async () => {
    const newConv = await createConversation()
    await loadConversations()
    onConversationChange(newConv.id)
  }

  const handleSelectConversation = async (id: string) => {
    await setActiveConversationId(id)
    onConversationChange(id)
  }

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    // Stop the auto-refresh interval during delete to prevent race condition
    stopRefreshInterval()
    
    try {
      // Immediately remove from UI for instant feedback
      setConversations(prev => prev.filter(c => c.id !== id))
      setGroupedConversations(prev => ({
        today: prev.today.filter(c => c.id !== id),
        yesterday: prev.yesterday.filter(c => c.id !== id),
        last7Days: prev.last7Days.filter(c => c.id !== id),
        last30Days: prev.last30Days.filter(c => c.id !== id),
        older: prev.older.filter(c => c.id !== id)
      }))
      
      // Delete from storage
      console.log('🗑️ Deleting conversation:', id)
      await deleteConversation(id)
      console.log('✅ Delete API call completed successfully')
      
      // If deleted conversation was active, create a new one
      if (activeConversationId === id) {
        const newConv = await createConversation()
        onConversationChange(newConv.id)
      }
      
      // DON'T reload - the conversation is already removed from UI
      // The auto-refresh will sync with backend in 5 seconds if needed
      
      // Restart the auto-refresh interval after delete completes
      startRefreshInterval()
    } catch (error) {
      console.error('Delete failed:', error)
      // Reload to get accurate state from server
      await loadConversations()
      // Restart interval even if delete failed
      startRefreshInterval()
    }
  }

  const renderConversationGroup = (title: string, convs: Conversation[]) => {
    if (convs.length === 0) return null

    return (
      <div className="conversation-group">
        <div className="group-title">{title}</div>
        {convs.map((conv) => (
          <div
            key={conv.id}
            className={`conversation-item ${activeConversationId === conv.id ? 'active' : ''}`}
            onClick={() => handleSelectConversation(conv.id)}
            title={conv.title}
          >
            <div className="conversation-info">
              <div className="conversation-icon"><Icon name="chat" size={18} /></div>
              <div className="conversation-text">
                <div className="conversation-title">{conv.title}</div>
                <div className="conversation-preview">
                  {conv.messageCount || 0} messages
                </div>
              </div>
            </div>
            <button
              className="delete-btn"
              onClick={(e) => handleDeleteConversation(conv.id, e)}
              title="Delete conversation"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="conversation-list">
      <div className="conversation-list-header">
        <h2><Icon name="chat" size={20} /> Conversations</h2>
        <button 
          className="new-chat-btn"
          onClick={handleNewChat}
          title="Start new conversation"
        >
          <span className="btn-icon">+</span>
          <span className="btn-text">New Chat</span>
        </button>
      </div>

      <div className="conversation-list-content">
        {conversations.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon"><Icon name="chat" size={48} /></div>
            <p>No conversations yet</p>
            <button className="empty-action-btn" onClick={handleNewChat}>
              Start Your First Chat
            </button>
          </div>
        ) : (
          <>
            {renderConversationGroup('Today', groupedConversations.today)}
            {renderConversationGroup('Yesterday', groupedConversations.yesterday)}
            {renderConversationGroup('Last 7 Days', groupedConversations.last7Days)}
            {renderConversationGroup('Last 30 Days', groupedConversations.last30Days)}
            {renderConversationGroup('Older', groupedConversations.older)}
          </>
        )}
      </div>

      <div className="conversation-list-footer">
        <div className="footer-info">
          {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  )
}

export default ConversationList
