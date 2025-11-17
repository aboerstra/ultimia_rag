import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useState, useEffect } from 'react'
import Icon from './Icon'
import './HealthStatus.css'

interface ServiceHealth {
  name: string
  status: 'ready' | 'not_configured' | 'error'
  message: string
}

interface HealthResponse {
  timestamp: string
  services: {
    [key: string]: ServiceHealth
  }
}

interface SalesforceOrg {
  username: string
  alias: string | null
  isSandbox: boolean
  isDefault: boolean
  connectedStatus: string
}

interface SalesforceOrgsResponse {
  available: boolean
  orgs: SalesforceOrg[]
  message?: string
}

interface JiraProject {
  key: string
  name: string
  id: string
}

interface ConfluenceSpace {
  key: string
  name: string
  type: string
}

interface ClockifyClient {
  id: string
  name: string
}

interface ClockifyProject {
  id: string
  name: string
  client: string
  clientId: string
}

function HealthStatus() {
  const queryClient = useQueryClient()
  const [showSfConfig, setShowSfConfig] = useState(false)
  const [showJiraConfig, setShowJiraConfig] = useState(false)
  const [showConfluenceConfig, setShowConfluenceConfig] = useState(false)
  const [showClockifyConfig, setShowClockifyConfig] = useState(false)
  
  // Global client code filter (applies to all services)
  const [clientCode, setClientCode] = useState('')
  
  // Load client code from backend on mount
  useEffect(() => {
    axios.get('/api/config/client-code').then(response => {
      if (response.data.client_code) {
        setClientCode(response.data.client_code)
      }
    }).catch(() => {
      // Ignore errors - config might not be set yet
    })
  }, [])
  
  // Save client code to backend when changed
  const saveClientCode = async (newCode: string) => {
    try {
      await axios.post('/api/config/set-client-code', { client_code: newCode })
      queryClient.invalidateQueries({ queryKey: ['jira-projects'] })
      queryClient.invalidateQueries({ queryKey: ['confluence-spaces'] })
      queryClient.invalidateQueries({ queryKey: ['clockify-clients'] })
      queryClient.invalidateQueries({ queryKey: ['clockify-projects'] })
    } catch (error) {
      console.error('Failed to save client code:', error)
    }
  }
  
  // Salesforce config state
  const [selectedProdOrg, setSelectedProdOrg] = useState('')
  const [selectedSandboxOrg, setSelectedSandboxOrg] = useState('')
  
  // Jira config state
  const [jiraProject, setJiraProject] = useState('')
  const [jiraDateRange, setJiraDateRange] = useState('6')
  
  // Confluence config state
  const [confluenceSpace, setConfluenceSpace] = useState('')
  const [confluenceDateRange, setConfluenceDateRange] = useState('6')
  
  // Clockify config state
  const [clockifyClient, setClockifyClient] = useState('')
  const [clockifyProjects, setClockifyProjects] = useState<string[]>([])
  const [clockifyDateRange, setClockifyDateRange] = useState('6')
  
  // Individual service testing state
  const [testingService, setTestingService] = useState<string | null>(null)
  
  const testIndividualService = async (serviceKey: string) => {
    setTestingService(serviceKey)
    try {
      const result = await axios.get(`/api/health/test/${serviceKey}`)
      // Update the health data with the test result
      if (health) {
        const updatedServices = { ...health.services }
        updatedServices[serviceKey] = {
          name: updatedServices[serviceKey].name,
          status: result.data.status,
          message: result.data.message
        }
        queryClient.setQueryData(['health'], {
          ...health,
          services: updatedServices,
          timestamp: new Date().toISOString()
        })
      }
    } catch (error) {
      console.error('Test failed:', error)
    } finally {
      setTestingService(null)
    }
  }
  
  const { data: health, isLoading, refetch: refetchHealth } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: () => axios.get('/api/health/detailed', {
      params: { t: Date.now() } // Cache buster
    }).then(r => r.data),
    enabled: true,
    staleTime: 30000, // Cache for 30 seconds
    refetchOnWindowFocus: false,
    retry: 1, // Only retry once if it fails
  })

  const { data: sfOrgs } = useQuery<SalesforceOrgsResponse>({
    queryKey: ['salesforce-orgs'],
    queryFn: () => axios.get('/api/salesforce/orgs').then(r => r.data),
    enabled: showSfConfig,
  })

  const { data: jiraProjects } = useQuery<JiraProject[]>({
    queryKey: ['jira-projects'],
    queryFn: () => axios.get('/api/jira/projects').then(r => r.data),
    enabled: showJiraConfig,
  })

  const { data: confluenceSpaces } = useQuery<ConfluenceSpace[]>({
    queryKey: ['confluence-spaces'],
    queryFn: () => axios.get('/api/confluence/spaces').then(r => r.data),
    enabled: showConfluenceConfig,
  })

  const { data: clockifyClients } = useQuery<ClockifyClient[]>({
    queryKey: ['clockify-clients'],
    queryFn: () => axios.get('/api/clockify/clients').then(r => r.data),
    enabled: showClockifyConfig,
  })

  const { data: clockifyProjectsList } = useQuery<ClockifyProject[]>({
    queryKey: ['clockify-projects', clockifyClient],
    queryFn: () => axios.get('/api/clockify/projects', {
      params: clockifyClient ? { client_id: clockifyClient } : {}
    }).then(r => r.data),
    enabled: showClockifyConfig,
  })

  // Filter items by client code (matches items that CONTAIN the code)
  const filterByClientCode = (items: any[], filterCode: string, nameField: string = 'name') => {
    if (!filterCode) return items
    const code = filterCode.toUpperCase()
    return items.filter(item => {
      const name = item[nameField]?.toUpperCase() || ''
      const key = item.key?.toUpperCase() || ''
      return name.includes(code) || key.includes(code)
    })
  }
  
  const filteredJiraProjects = filterByClientCode(jiraProjects || [], clientCode, 'name')
  const filteredConfluenceSpaces = filterByClientCode(confluenceSpaces || [], clientCode, 'name')
  const filteredClockifyClients = filterByClientCode(clockifyClients || [], clientCode, 'name')
  const filteredClockifyProjects = filterByClientCode(clockifyProjectsList || [], clientCode, 'name')

  const setOrgMutation = useMutation({
    mutationFn: (data: { production_org?: string, sandbox_org?: string }) =>
      axios.post('/api/salesforce/set-org', data),
    onSuccess: (_, variables) => {
      // Update the health data immediately in cache
      if (health) {
        const updatedServices = { ...health.services }
        if (variables.production_org) {
          updatedServices.salesforce_prod = {
            ...updatedServices.salesforce_prod,
            message: `Configured - Org: ${variables.production_org}`
          }
        }
        if (variables.sandbox_org) {
          updatedServices.salesforce_sandbox = {
            ...updatedServices.salesforce_sandbox,
            message: `Configured - Org: ${variables.sandbox_org}`
          }
        }
        queryClient.setQueryData(['health'], {
          ...health,
          services: updatedServices,
          timestamp: new Date().toISOString()
        })
      }
      queryClient.invalidateQueries({ queryKey: ['salesforce-orgs'] })
      alert('Org updated!')
    },
  })

  const setJiraConfigMutation = useMutation({
    mutationFn: (data: { project?: string, space?: string, date_range_months?: number }) =>
      axios.post('/api/jira/set-config', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health'] })
      alert('Jira configuration updated! Backend will reload automatically.')
    },
  })

  const setConfluenceConfigMutation = useMutation({
    mutationFn: (data: { space?: string, date_range_months?: number }) =>
      axios.post('/api/confluence/set-config', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health'] })
      alert('Confluence configuration updated! Backend will reload automatically.')
    },
  })

  const setClockifyConfigMutation = useMutation({
    mutationFn: (data: { client?: string, projects?: string, date_range_months?: number }) =>
      axios.post('/api/clockify/set-config', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health'] })
      alert('Clockify configuration updated! Backend will reload automatically.')
    },
  })


  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <Icon name="check-circle" size={16} color="#22c55e" />
      case 'not_configured':
        return <Icon name="alert-circle" size={16} color="#f59e0b" />
      case 'error':
        return <Icon name="x-circle" size={16} color="#ef4444" />
      default:
        return <Icon name="circle" size={16} color="#9ca3af" />
    }
  }

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'ready':
        return 'status-ready'
      case 'not_configured':
        return 'status-not-configured'
      case 'error':
        return 'status-error'
      default:
        return ''
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ready':
        return 'Ready'
      case 'not_configured':
        return 'Not Configured'
      case 'error':
        return 'Error'
      default:
        return 'Unknown'
    }
  }

  const prodOrgs = sfOrgs?.orgs.filter(org => !org.isSandbox) || []
  const sandboxOrgs = sfOrgs?.orgs.filter(org => org.isSandbox) || []

  // Initialize config from .env via health status
  useEffect(() => {
    if (!health) return
    
    // Salesforce orgs
    if (health.services.salesforce_prod) {
      const message = health.services.salesforce_prod.message
      const match = message.match(/Org:\s*(\S+)/)
      if (match && match[1] && match[1] !== 'configured') {
        setSelectedProdOrg(match[1])
      }
    }
    if (health.services.salesforce_sandbox) {
      const message = health.services.salesforce_sandbox.message
      const match = message.match(/Org:\s*(\S+)/)
      if (match && match[1] && match[1] !== 'configured') {
        setSelectedSandboxOrg(match[1])
      }
    }
  }, [health])
  
  // Load all configs from backend on mount
  useEffect(() => {
    // Load Jira/Confluence config
    axios.get('/api/config/jira').then(response => {
      if (response.data.project) {
        setJiraProject(response.data.project)
      }
      if (response.data.space) {
        setConfluenceSpace(response.data.space)
      }
      if (response.data.date_range_months) {
        setJiraDateRange(response.data.date_range_months.toString())
        setConfluenceDateRange(response.data.date_range_months.toString())
        setClockifyDateRange(response.data.date_range_months.toString())
      }
    }).catch(() => {
      // Ignore errors
    })
    
    // Load Clockify config
    axios.get('/api/config/clockify').then(response => {
      if (response.data.client) {
        setClockifyClient(response.data.client)
      }
      if (response.data.projects) {
        // Projects are stored as comma-separated string
        setClockifyProjects(response.data.projects.split(','))
      }
      if (response.data.date_range_months) {
        setClockifyDateRange(response.data.date_range_months.toString())
      }
    }).catch(() => {
      // Ignore errors
    })
    
    // Load Salesforce org config
    axios.get('/api/config/salesforce').then(response => {
      if (response.data.production_org) {
        setSelectedProdOrg(response.data.production_org)
      }
      if (response.data.sandbox_org) {
        setSelectedSandboxOrg(response.data.sandbox_org)
      }
    }).catch(() => {
      // Ignore errors
    })
  }, [])

  const openSfLogin = (isSandbox: boolean) => {
    const url = isSandbox 
      ? 'https://test.salesforce.com'
      : 'https://login.salesforce.com'
    window.open(url, '_blank')
    alert('After logging in, run:\nsf org login web' + (isSandbox ? ' --instance-url https://test.salesforce.com' : ''))
  }

  return (
    <div className="health-status">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0 }}><Icon name="shield" size={20} /> System Health {isLoading && <Icon name="loader" size={16} />}</h3>
        <button
          onClick={() => refetchHealth()}
          disabled={isLoading}
          className="login-btn"
          style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
        >
          {isLoading ? <><Icon name="loader" size={14} /> Testing...</> : <><Icon name="tool" size={14} /> Test All Connections</>}
        </button>
      </div>
      
      <div className="health-services">
        {health ? Object.entries(health.services).map(([key, service]) => {
          const isSalesforce = key.includes('salesforce')
          const isJira = key === 'jira'
          const isConfluence = key === 'confluence'
          const isClockify = key === 'clockify'
          
          return (
            <div key={key} className={`health-service ${getStatusClass(service.status)}`}>
              <div className="service-header">
                <span className="service-icon">{getStatusIcon(service.status)}</span>
                <span className="service-name">{service.name}</span>
                <span className={`service-badge ${service.status}`}>
                  {getStatusLabel(service.status)}
                </span>
                <div style={{ display: 'flex', gap: '0.5rem', marginLeft: 'auto' }}>
                  {(isSalesforce || isJira || isConfluence || isClockify) && (
                    <button 
                      className="config-btn"
                      onClick={() => testIndividualService(key)}
                      disabled={testingService === key}
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                    >
                      {testingService === key ? <Icon name="loader" size={12} /> : <Icon name="tool" size={12} />} Test
                    </button>
                  )}
                  {isSalesforce && (
                    <button 
                      className="config-btn"
                      onClick={() => setShowSfConfig(!showSfConfig)}
                    >
                      {showSfConfig ? '▼' : '▶'} Configure
                    </button>
                  )}
                  {isJira && (
                    <button 
                      className="config-btn"
                      onClick={() => setShowJiraConfig(!showJiraConfig)}
                    >
                      {showJiraConfig ? '▼' : '▶'} Configure
                    </button>
                  )}
                  {isConfluence && (
                    <button 
                      className="config-btn"
                      onClick={() => setShowConfluenceConfig(!showConfluenceConfig)}
                    >
                      {showConfluenceConfig ? '▼' : '▶'} Configure
                    </button>
                  )}
                  {isClockify && (
                    <button 
                      className="config-btn"
                      onClick={() => setShowClockifyConfig(!showClockifyConfig)}
                    >
                      {showClockifyConfig ? '▼' : '▶'} Configure
                    </button>
                  )}
                </div>
              </div>
              <div className="service-message">{service.message}</div>
              
              {/* Salesforce Org Selector */}
              {isSalesforce && showSfConfig && (
                <div className="sf-config">
                  <div className="sf-config-section">
                    <label>
                      {key === 'salesforce_prod' ? 'Production Org:' : 'Sandbox Org:'}
                    </label>
                    <select 
                      value={key === 'salesforce_prod' ? selectedProdOrg : selectedSandboxOrg}
                      onChange={(e) => {
                        const orgIdentifier = e.target.value
                        if (key === 'salesforce_prod') {
                          setSelectedProdOrg(orgIdentifier)
                          if (orgIdentifier) {
                            setOrgMutation.mutate({ production_org: orgIdentifier })
                          }
                        } else {
                          setSelectedSandboxOrg(orgIdentifier)
                          if (orgIdentifier) {
                            setOrgMutation.mutate({ sandbox_org: orgIdentifier })
                          }
                        }
                      }}
                      className="org-selector"
                    >
                      <option value="">Select an org...</option>
                      {(key === 'salesforce_prod' ? prodOrgs : sandboxOrgs).map((org) => (
                        <option key={org.username} value={org.alias || org.username}>
                          {org.alias ? `${org.alias} (${org.username})` : org.username}
                          {org.isDefault ? ' [Default]' : ''}
                        </option>
                      ))}
                    </select>
                    <button 
                      className="login-btn"
                      onClick={() => openSfLogin(key === 'salesforce_sandbox')}
                    >
                      <Icon name="lock" size={14} /> Login to Salesforce
                    </button>
                  </div>
                  {sfOrgs && !sfOrgs.available && (
                    <p className="sf-hint">
                      Install Salesforce CLI and run: <code>sf org login web</code>
                    </p>
                  )}
                  {sfOrgs && sfOrgs.available && (key === 'salesforce_prod' ? prodOrgs : sandboxOrgs).length === 0 && (
                    <p className="sf-hint">
                      No {key === 'salesforce_prod' ? 'production' : 'sandbox'} orgs found. 
                      Click "Login to Salesforce" button above.
                    </p>
                  )}
                </div>
              )}

              {/* Jira Configuration */}
              {isJira && showJiraConfig && (
                <div className="data-source-config">
                  <div className="config-section">
                    <label>Client Code (Global Filter):</label>
                    <input 
                      type="text"
                      placeholder="e.g., MAXCOM"
                      value={clientCode}
                      onChange={(e) => setClientCode(e.target.value.toUpperCase())}
                      onBlur={(e) => saveClientCode(e.target.value.toUpperCase())}
                      className="date-range-input"
                      style={{ textTransform: 'uppercase' }}
                    />
                    <p className="hint-text">Filters all dropdowns across all services</p>
                  </div>

                  <div className="config-section">
                    <label>Jira Project:</label>
                    <select 
                      value={jiraProject}
                      onChange={(e) => setJiraProject(e.target.value)}
                      className="config-selector"
                    >
                      <option value="">All Projects</option>
                      {filteredJiraProjects.map((project) => (
                        <option key={project.key} value={project.key}>
                          {project.key} - {project.name}
                        </option>
                      ))}
                    </select>
                    {clientCode && filteredJiraProjects.length === 0 && jiraProjects && jiraProjects.length > 0 && (
                      <p className="hint-text" style={{ color: '#f59e0b' }}>No projects match "{clientCode}"</p>
                    )}
                  </div>

                  <div className="config-section">
                    <label>Date Range (months):</label>
                    <input 
                      type="number"
                      min="1"
                      max="24"
                      value={jiraDateRange}
                      onChange={(e) => setJiraDateRange(e.target.value)}
                      className="date-range-input"
                    />
                  </div>

                  <button 
                    className="save-config-btn"
                    onClick={() => {
                      setJiraConfigMutation.mutate({
                        project: jiraProject || undefined,
                        date_range_months: parseInt(jiraDateRange)
                      })
                    }}
                  >
                    <Icon name="save" size={14} /> Save Configuration
                  </button>
                </div>
              )}

              {/* Confluence Configuration */}
              {isConfluence && showConfluenceConfig && (
                <div className="data-source-config">
                  <div className="config-section">
                    <label>Client Code (Global Filter):</label>
                    <input 
                      type="text"
                      placeholder="e.g., MAXCOM"
                      value={clientCode}
                      onChange={(e) => setClientCode(e.target.value.toUpperCase())}
                      onBlur={(e) => saveClientCode(e.target.value.toUpperCase())}
                      className="date-range-input"
                      style={{ textTransform: 'uppercase' }}
                    />
                    <p className="hint-text">Filters all dropdowns across all services</p>
                  </div>

                  <div className="config-section">
                    <label>Confluence Space:</label>
                    <select 
                      value={confluenceSpace}
                      onChange={(e) => setConfluenceSpace(e.target.value)}
                      className="config-selector"
                    >
                      <option value="">All Spaces</option>
                      {filteredConfluenceSpaces.map((space) => (
                        <option key={space.key} value={space.key}>
                          {space.key} - {space.name}
                        </option>
                      ))}
                    </select>
                    {clientCode && filteredConfluenceSpaces.length === 0 && confluenceSpaces && confluenceSpaces.length > 0 && (
                      <p className="hint-text" style={{ color: '#f59e0b' }}>No spaces match "{clientCode}"</p>
                    )}
                  </div>

                  <div className="config-section">
                    <label>Date Range (months):</label>
                    <input 
                      type="number"
                      min="1"
                      max="24"
                      value={confluenceDateRange}
                      onChange={(e) => setConfluenceDateRange(e.target.value)}
                      className="date-range-input"
                    />
                  </div>

                  <button 
                    className="save-config-btn"
                    onClick={() => {
                      setConfluenceConfigMutation.mutate({
                        space: confluenceSpace || undefined,
                        date_range_months: parseInt(confluenceDateRange)
                      })
                    }}
                  >
                    <Icon name="save" size={14} /> Save Configuration
                  </button>
                </div>
              )}

              {/* Clockify Configuration */}
              {isClockify && showClockifyConfig && (
                <div className="data-source-config">
                  <div className="config-section">
                    <label>Client Code (Global Filter):</label>
                    <input 
                      type="text"
                      placeholder="e.g., MAXCOM"
                      value={clientCode}
                      onChange={(e) => setClientCode(e.target.value.toUpperCase())}
                      onBlur={(e) => saveClientCode(e.target.value.toUpperCase())}
                      className="date-range-input"
                      style={{ textTransform: 'uppercase' }}
                    />
                    <p className="hint-text">Filters all dropdowns across all services</p>
                  </div>

                  <div className="config-section">
                    <label>Client:</label>
                    <select 
                      value={clockifyClient}
                      onChange={(e) => setClockifyClient(e.target.value)}
                      className="config-selector"
                    >
                      <option value="">All Clients</option>
                      {filteredClockifyClients.map((client) => (
                        <option key={client.id} value={client.id}>
                          {client.name}
                        </option>
                      ))}
                    </select>
                    {clientCode && filteredClockifyClients.length === 0 && clockifyClients && clockifyClients.length > 0 && (
                      <p className="hint-text" style={{ color: '#f59e0b' }}>No clients match "{clientCode}"</p>
                    )}
                  </div>

                  <div className="config-section">
                    <label>Projects (multi-select):</label>
                    <select 
                      multiple
                      value={clockifyProjects}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, option => option.value)
                        setClockifyProjects(selected)
                      }}
                      className="config-selector multi-select"
                      size={5}
                    >
                      {filteredClockifyProjects.map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.name} {project.client ? `(${project.client})` : ''}
                        </option>
                      ))}
                    </select>
                    {clientCode && filteredClockifyProjects.length === 0 && clockifyProjectsList && clockifyProjectsList.length > 0 && (
                      <p className="hint-text" style={{ color: '#f59e0b' }}>No projects match "{clientCode}"</p>
                    )}
                    <p className="hint-text">Hold Ctrl/Cmd to select multiple projects</p>
                  </div>

                  <div className="config-section">
                    <label>Date Range (months):</label>
                    <input 
                      type="number"
                      min="1"
                      max="24"
                      value={clockifyDateRange}
                      onChange={(e) => setClockifyDateRange(e.target.value)}
                      className="date-range-input"
                    />
                  </div>

                  <button 
                    className="save-config-btn"
                    onClick={() => {
                      setClockifyConfigMutation.mutate({
                        client: clockifyClient || undefined,
                        projects: clockifyProjects.length > 0 ? clockifyProjects.join(',') : undefined,
                        date_range_months: parseInt(clockifyDateRange)
                      })
                    }}
                  >
                    <Icon name="save" size={14} /> Save Configuration
                  </button>
                </div>
              )}
            </div>
          )
        }) : (
          <p style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>
            Loading configuration... {isLoading && <Icon name="clock" size={16} />}
          </p>
        )}
      </div>
      {health && (
        <div className="health-footer">
          Last checked: {new Date(health.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}

export default HealthStatus
