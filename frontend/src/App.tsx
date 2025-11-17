import { useState, useEffect } from 'react'
import ConversationList from './components/ConversationList'
import ChatWorkspace from './components/ChatWorkspace'
import ContextPanel from './components/ContextPanel'
import {
  getConversations,
  createConversation,
  getActiveConversationId,
  setActiveConversationId
} from './utils/conversationStorage'
import './App.css'

function App() {
  const [activeConversationId, setActiveConversationIdState] = useState<string | null>(null)
  const [contextPanelOpen, setContextPanelOpen] = useState(true)
  const [panelWidth, setPanelWidth] = useState(650) // Default 650px

  // Initialize: Load or create first conversation
  useEffect(() => {
    const initializeConversations = async () => {
      const conversations = await getConversations()
      const savedActiveId = await getActiveConversationId()

      if (conversations.length === 0) {
        // No conversations exist - create the first one
        const newConv = await createConversation()
        setActiveConversationIdState(newConv.id)
      } else if (savedActiveId && conversations.find(c => c.id === savedActiveId)) {
        // Saved conversation exists
        setActiveConversationIdState(savedActiveId)
      } else {
        // Use the most recent conversation
        setActiveConversationIdState(conversations[0].id)
        await setActiveConversationId(conversations[0].id)
      }
    }

    initializeConversations()
  }, [])

  const handleConversationChange = async (conversationId: string) => {
    setActiveConversationIdState(conversationId)
    await setActiveConversationId(conversationId)
  }

  const handleConversationUpdate = () => {
    // No-op: ConversationList now has auto-refresh
    // This function is kept for compatibility but does nothing
  }

  const handleContextPanelToggle = () => {
    setContextPanelOpen(prev => !prev)
  }

  return (
    <div className="app-container">
      <ConversationList
        activeConversationId={activeConversationId}
        onConversationChange={handleConversationChange}
        onConversationUpdate={handleConversationUpdate}
      />
      <ChatWorkspace
        conversationId={activeConversationId}
        onConversationUpdate={handleConversationUpdate}
      />
      <ContextPanel
        isOpen={contextPanelOpen}
        onToggle={handleContextPanelToggle}
        width={panelWidth}
        onWidthChange={setPanelWidth}
      />
    </div>
  )
}

export default App
