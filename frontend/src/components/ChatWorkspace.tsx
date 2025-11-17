import { useState, useEffect, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import Icon from './Icon'
import './ChatWorkspace.css'
import {
  getConversation,
  addMessage,
  deleteMessage,
  type Message,
  type Conversation
} from '../utils/conversationStorage'

interface ChatWorkspaceProps {
  conversationId: string | null
  onConversationUpdate: () => void
}

function ChatWorkspace({ conversationId, onConversationUpdate }: ChatWorkspaceProps) {
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [input, setInput] = useState('')
  const [useGeneralKnowledge, setUseGeneralKnowledge] = useState(false)
  const [useWebSearch, setUseWebSearch] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load conversation when ID changes
  useEffect(() => {
    const loadConv = async () => {
      if (conversationId) {
        const conv = await getConversation(conversationId)
        setConversation(conv)
      }
    }
    loadConv()
  }, [conversationId])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation?.messages])

  const chatMutation = useMutation({
    mutationFn: (question: string) => {
      // Build conversation history from messages (exclude system messages)
      const conversation_history = conversation?.messages
        .filter(m => m.role !== 'system')
        .map(m => ({
          role: m.role,
          content: m.content
        })) || []
      
      // Create AbortController for cancellation support
      const controller = new AbortController()
      
      // Store controller for manual cancellation
      ;(chatMutation as any).abortController = controller
      
      return axios.post('/api/chat', { 
        question, 
        conversation_history,
        use_general_knowledge: useGeneralKnowledge,
        use_web_search: useWebSearch
      }, { 
        timeout: 120000,
        signal: controller.signal
      }).then(r => r.data)
    },
    onSuccess: async (data) => {
      if (!conversationId) return

      const assistantMessage: Message = {
        id: `${Date.now()}_assistant`,
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
        sources: data.sources_used
      }

      await addMessage(conversationId, assistantMessage)
      const updatedConv = await getConversation(conversationId)
      setConversation(updatedConv)
      onConversationUpdate()
    },
    onError: async (error: any) => {
      if (!conversationId) return

      const errorMessage: Message = {
        id: `${Date.now()}_error`,
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || error.message || 'Request failed'}`,
        timestamp: new Date().toISOString()
      }

      await addMessage(conversationId, errorMessage)
      const updatedConv = await getConversation(conversationId)
      setConversation(updatedConv)
      onConversationUpdate()
    }
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || chatMutation.isPending || !conversationId) return

    const userMessage: Message = {
      id: `${Date.now()}_user`,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    await addMessage(conversationId, userMessage)
    const updatedConv = await getConversation(conversationId)
    setConversation(updatedConv)
    onConversationUpdate()

    chatMutation.mutate(input)
    setInput('')
  }

  const handleStop = () => {
    // Cancel the ongoing request using AbortController
    const controller = (chatMutation as any).abortController
    if (controller) {
      controller.abort()
    }
    chatMutation.reset()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
    // Shift+Enter creates a line break (default textarea behavior)
  }

  const handleExampleClick = (question: string) => {
    setInput(question)
  }

  const exampleQuestions = [
    "What are our top 5 Jira issues this month?",
    "How many hours were tracked on Salesforce projects?",
    "What were the main topics in recent meetings?",
    "Show me Salesforce deployment metrics",
    "What blockers were mentioned in transcripts?"
  ]

  if (!conversation) {
    return (
      <div className="chat-workspace">
        <div className="chat-workspace-empty">
          <div className="empty-icon"><Icon name="chat" size={48} /></div>
          <h2>No Conversation Selected</h2>
          <p>Select a conversation from the sidebar or create a new one to get started.</p>
        </div>
      </div>
    )
  }

  const showExamples = conversation.messages.length <= 1

  return (
    <div className="chat-workspace">
      <div className="chat-workspace-header">
        <div className="header-content">
          <span className="header-icon"><Icon name="bot" size={24} /></span>
          <div className="header-info">
            <h1>{conversation.title}</h1>
            <p className="header-subtitle">AI Assistant powered by your data</p>
          </div>
        </div>
        <div className="header-badge">Beta</div>
      </div>

      <div className="chat-messages">
        {conversation.messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.role}`}
          >
            <div className="message-avatar">
              <Icon name={message.role === 'user' ? 'user' : 'bot'} size={20} />
            </div>
            <div className="message-content">
              <div className="message-text">
                {message.role === 'user' ? (
                  <div className="user-text">{message.content}</div>
                ) : (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code(props) {
                        const { children, className, node, ...rest } = props
                        const match = /language-(\w+)/.exec(className || '')
                        return match ? (
                          <SyntaxHighlighter
                            style={oneDark}
                            language={match[1]}
                            PreTag="div"
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...rest}>
                            {children}
                          </code>
                        )
                      }
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                )}
              </div>
              <div className="message-actions">
                <button
                  className="action-btn"
                  onClick={() => {
                    navigator.clipboard.writeText(message.content)
                    alert('Copied to clipboard!')
                  }}
                  title="Copy message"
                >
                  <Icon name="copy" size={14} /> Copy
                </button>
                {message.role === 'assistant' && (
                  <button
                    className="action-btn save-btn"
                    onClick={async () => {
                      try {
                        const response = await axios.post('/api/memory/save', {
                          fact_content: message.content,
                          fact_title: `Fact from ${new Date(message.timestamp).toLocaleDateString()}`,
                          source_conversation_id: conversationId
                        })
                        alert(`✅ Saved to memory! Total facts: ${response.data.total_facts}`)
                      } catch (error:any) {
                        alert(`❌ Failed to save: ${error.message}`)
                      }
                    }}
                    title="Save this response to persistent memory"
                  >
                    <Icon name="save" size={14} /> Save to Memory
                  </button>
                )}
                {message.role !== 'system' && (
                  <button
                    onClick={async () => {
                      if (!conversationId) return
                      if (window.confirm('Delete this message?')) {
                        await deleteMessage(conversationId, message.id)
                        const updatedConv = await getConversation(conversationId)
                        setConversation(updatedConv)
                        onConversationUpdate()
                      }
                    }}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '6px 12px',
                      background: 'linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(211, 47, 47, 0.1) 100%)',
                      color: '#f44336',
                      border: '1px solid #f44336',
                      borderRadius: '6px',
                      fontSize: '13px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.background = 'linear-gradient(135deg, rgba(244, 67, 54, 0.2) 0%, rgba(211, 47, 47, 0.2) 100%)'
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.background = 'linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(211, 47, 47, 0.1) 100%)'
                    }}
                    title="Delete message"
                  >
                    <Icon name="trash" size={14} /> Delete
                  </button>
                )}
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <span className="sources-icon"><Icon name="database" size={14} /></span>
                    <span className="sources-text">
                      Sources: {message.sources.join(', ')}
                    </span>
                  </div>
                )}
              </div>
              <div className="message-time">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {chatMutation.isPending && (
          <div className="message assistant typing">
            <div className="message-avatar"><Icon name="bot" size={20} /></div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <button
                onClick={handleStop}
                style={{
                  marginTop: '12px',
                  padding: '8px 16px',
                  background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(244, 67, 54, 0.3)'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                <Icon name="close" size={16} /> Stop Generating
              </button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {showExamples && (
        <div className="example-questions">
          <p className="example-label">Try asking:</p>
          <div className="example-buttons">
            {exampleQuestions.map((question, idx) => (
              <button
                key={idx}
                className="example-btn"
                onClick={() => handleExampleClick(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="chat-input-container">
        <div className="ai-mode-toggles-wrapper">
          <label className="mode-toggle">
            <input
              type="checkbox"
              checked={useGeneralKnowledge}
              onChange={(e) => setUseGeneralKnowledge(e.target.checked)}
            />
            <span className="toggle-box"></span>
            <span className="toggle-text">General Knowledge</span>
          </label>
          <label className="mode-toggle">
            <input
              type="checkbox"
              checked={useWebSearch}
              onChange={(e) => setUseWebSearch(e.target.checked)}
            />
            <span className="toggle-box"></span>
            <span className="toggle-text">Web Search</span>
          </label>
        </div>
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <textarea
            className="chat-input"
            placeholder="Ask about Jira, Clockify, Salesforce, or transcripts... (Shift+Enter for line break)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={chatMutation.isPending}
            rows={1}
          />
          <button
            type="submit"
            className="chat-send"
            disabled={!input.trim() || chatMutation.isPending}
            title="Send message (or press Enter)"
          >
            {chatMutation.isPending ? <Icon name="clock" size={16} /> : '➤'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default ChatWorkspace
