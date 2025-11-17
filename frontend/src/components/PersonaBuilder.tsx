import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Icon from './Icon'
import './PersonaBuilder.css'

interface Participant {
  name: string
  transcript_count: number
  first_appearance: string
  last_appearance: string
  has_persona: boolean
  status: 'ready' | 'building' | 'built' | 'insufficient_data'
}

interface PersonaBuildStatus {
  task_id: string
  person_name: string
  status: 'queued' | 'building' | 'completed' | 'failed'
  progress: number
  current_step?: string
  error?: string
  result?: any
}

interface Persona {
  name: string
  built_date: string
  transcript_count: number
  content: string
  download_url: string
}

function PersonaBuilder() {
  const queryClient = useQueryClient()
  const [selectedPerson, setSelectedPerson] = useState<string | null>(null)
  const [viewingPersona, setViewingPersona] = useState<Persona | null>(null)
  const [buildingTasks, setBuildingTasks] = useState<Set<string>>(new Set())
  const [taskPolling, setTaskPolling] = useState<Map<string, string>>(new Map())
  const [linkedinUrls, setLinkedinUrls] = useState<Map<string, string>>(new Map())

  // Fetch participants
  const { data: participants, isLoading } = useQuery<Participant[]>({
    queryKey: ['personas-participants'],
    queryFn: () => axios.get('/api/personas/participants').then(r => r.data),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  })

  // Fetch saved LinkedIn URLs
  const { data: savedLinkedinUrls } = useQuery<Record<string, string>>({
    queryKey: ['linkedin-urls'],
    queryFn: () => axios.get('/api/personas/linkedin-urls').then(r => r.data),
  })

  // Update linkedinUrls state when saved URLs are loaded
  useEffect(() => {
    if (savedLinkedinUrls) {
      setLinkedinUrls(new Map(Object.entries(savedLinkedinUrls)))
    }
  }, [savedLinkedinUrls])

  // Build persona mutation
  const buildPersonaMutation = useMutation({
    mutationFn: ({ person_name, linkedin_url }: { person_name: string; linkedin_url?: string }) => 
      axios.post('/api/personas/build', { person_name, linkedin_url }).then(r => r.data),
    onSuccess: (data, { person_name }) => {
      // Start polling for this task
      const newPolling = new Map(taskPolling)
      newPolling.set(person_name, data.task_id)
      setTaskPolling(newPolling)
      setBuildingTasks(prev => new Set([...prev, person_name]))
    }
  })

  // Poll build status for active tasks
  useEffect(() => {
    if (taskPolling.size === 0) return

    const interval = setInterval(async () => {
      for (const [person_name, task_id] of taskPolling.entries()) {
        try {
          const response = await axios.get(`/api/personas/build-status/${task_id}`)
          const status: PersonaBuildStatus = response.data

          if (status.status === 'completed' || status.status === 'failed') {
            // Remove from polling
            const newPolling = new Map(taskPolling)
            newPolling.delete(person_name)
            setTaskPolling(newPolling)
            setBuildingTasks(prev => {
              const newSet = new Set(prev)
              newSet.delete(person_name)
              return newSet
            })

            // Refresh participants list
            queryClient.invalidateQueries({ queryKey: ['personas-participants'] })

            if (status.status === 'completed') {
              // Show success notification
              console.log(`✅ Persona built for ${person_name}`)
            }
          }
        } catch (error) {
          console.error(`Error polling status for ${person_name}:`, error)
        }
      }
    }, 3000) // Poll every 3 seconds

    return () => clearInterval(interval)
  }, [taskPolling, queryClient])

  const handleBuildPersona = (person_name: string) => {
    const linkedin_url = linkedinUrls.get(person_name) || undefined
    buildPersonaMutation.mutate({ person_name, linkedin_url })
  }

  const handleLinkedinUrlChange = (person_name: string, url: string) => {
    const newUrls = new Map(linkedinUrls)
    if (url.trim()) {
      newUrls.set(person_name, url.trim())
    } else {
      newUrls.delete(person_name)
    }
    setLinkedinUrls(newUrls)
  }

  const handleViewPersona = async (person_name: string) => {
    try {
      const response = await axios.get(`/api/personas/${encodeURIComponent(person_name)}`)
      setViewingPersona(response.data)
    } catch (error) {
      console.error('Error loading persona:', error)
      alert('Failed to load persona. Please try again.')
    }
  }

  const closePersonaViewer = () => {
    setViewingPersona(null)
  }

  const getStatusBadge = (participant: Participant) => {
    const isBuilding = buildingTasks.has(participant.name)
    
    if (isBuilding) {
      return <span className="status-badge building"><Icon name="loader" size={14} /> Building</span>
    }
    
    switch (participant.status) {
      case 'built':
        return <span className="status-badge built"><Icon name="check" size={14} /> Built</span>
      case 'ready':
        return <span className="status-badge ready">Ready</span>
      case 'insufficient_data':
        return <span className="status-badge insufficient"><Icon name="alert-circle" size={14} /> Need More Data</span>
      default:
        return <span className="status-badge">{participant.status}</span>
    }
  }

  const getActionButton = (participant: Participant) => {
    const isBuilding = buildingTasks.has(participant.name)
    
    if (isBuilding) {
      return (
        <button className="btn-building" disabled>
          <span className="spinner"><Icon name="loader" size={16} /></span> Building...
        </button>
      )
    }
    
    if (participant.status === 'built') {
      return (
        <div className="action-buttons">
          <button 
            className="btn-view"
            onClick={() => handleViewPersona(participant.name)}
          >
            <Icon name="eye" size={14} /> View
          </button>
          <button 
            className="btn-rebuild"
            onClick={() => handleBuildPersona(participant.name)}
            disabled={buildPersonaMutation.isPending}
            title="Rebuild persona with latest analysis"
          >
            <Icon name="refresh" size={14} /> Rebuild
          </button>
        </div>
      )
    }
    
    if (participant.status === 'ready') {
      return (
        <button 
          className="btn-build"
          onClick={() => handleBuildPersona(participant.name)}
          disabled={buildPersonaMutation.isPending}
        >
          <Icon name="build" size={14} /> Build Persona
        </button>
      )
    }
    
    return (
      <button className="btn-disabled" disabled>
        Need 3+ Transcripts
      </button>
    )
  }

  return (
    <div className="persona-builder-component">
      <div className="persona-builder-header">
        <h2><Icon name="users" size={20} /> Persona Builder</h2>
        <p className="description">
          Build AI-powered executive personas from meeting transcripts. 
          Analyzes decision-making patterns, communication styles, and priorities using 6 expert frameworks.
        </p>
      </div>

      {isLoading ? (
        <div className="loading-state">
          <div className="loading-spinner"><Icon name="loader" size={24} /></div>
          <p>Loading participants...</p>
        </div>
      ) : participants && participants.length > 0 ? (
        <div className="participants-section">
          <div className="section-header">
            <h3>Meeting Participants</h3>
            <span className="participant-count">{participants.length} people found</span>
          </div>

          <div className="participants-table">
            <div className="table-header">
              <div className="col-name">Name</div>
              <div className="col-meetings">Meetings</div>
              <div className="col-status">Status</div>
              <div className="col-actions">Actions</div>
            </div>

            {participants.map(participant => (
              <div key={participant.name} className="participant-row">
                <div className="col-name">
                  <div className="participant-info">
                    <div className="participant-name">{participant.name}</div>
                    <div className="participant-dates">
                      {participant.first_appearance !== 'Unknown' && (
                        <small>
                          {participant.first_appearance} - {participant.last_appearance}
                        </small>
                      )}
                    </div>
                  </div>
                </div>

                <div className="col-meetings">
                  <span className="meeting-count">{participant.transcript_count}</span>
                </div>

                <div className="col-status">
                  {getStatusBadge(participant)}
                </div>

                <div className="col-actions">
                  {getActionButton(participant)}
                  {participant.status === 'built' && (
                    <a
                      href={`/api/personas/${encodeURIComponent(participant.name)}/download`}
                      download
                      className="btn-download"
                      title="Download persona"
                    >
                      <Icon name="download" size={14} />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="info-box">
            <h4><Icon name="lightbulb" size={16} /> How It Works</h4>
            <ul>
              <li><strong>Minimum 3 transcripts</strong> needed for viable persona</li>
              <li><strong>4-6 minutes</strong> to build comprehensive profile</li>
              <li><strong>6 expert frameworks</strong> applied (Kahneman, Lencioni, Martin, Cialdini, Duarte, Grant)</li>
              <li><strong>Predictive model</strong> included for decision-making insights</li>
            </ul>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-icon"><Icon name="users" size={48} /></div>
          <h3>No Participants Yet</h3>
          <p>
            Participants will appear here after you run an analysis with transcripts.
            Upload meeting transcripts and run the analysis to get started.
          </p>
        </div>
      )}

      {/* Persona Viewer Modal */}
      {viewingPersona && (
        <div className="modal-overlay" onClick={closePersonaViewer}>
          <div className="modal persona-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                <span className="modal-icon"><Icon name="bar-chart" size={20} /></span>
                <div>
                  <h3>{viewingPersona.name}</h3>
                  <small>
                    Generated from {viewingPersona.transcript_count} transcripts
                  </small>
                </div>
              </div>
              <button className="close-btn" onClick={closePersonaViewer}>×</button>
            </div>

            <div className="modal-content persona-content">
              <div className="persona-markdown">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({node, ...props}) => <h1 className="persona-h1" {...props} />,
                    h2: ({node, ...props}) => <h2 className="persona-h2" {...props} />,
                    h3: ({node, ...props}) => <h3 className="persona-h3" {...props} />,
                    code: ({node, inline, ...props}: any) => 
                      inline ? 
                        <code className="inline-code" {...props} /> : 
                        <code className="code-block" {...props} />,
                    pre: ({node, ...props}) => <pre className="pre-block" {...props} />,
                    table: ({node, ...props}) => <table className="markdown-table" {...props} />,
                    blockquote: ({node, ...props}) => <blockquote className="markdown-quote" {...props} />,
                  }}
                >
                  {viewingPersona.content}
                </ReactMarkdown>
              </div>
            </div>

            <div className="modal-footer">
              <a
                href={viewingPersona.download_url}
                download
                className="btn-modal-download"
              >
                <Icon name="download" size={16} /> Download Markdown
              </a>
              <button className="btn-modal-close" onClick={closePersonaViewer}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PersonaBuilder
