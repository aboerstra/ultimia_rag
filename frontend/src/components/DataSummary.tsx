import { useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import Icon from './Icon'
import './DataSummary.css'

interface JiraIssue {
  key: string
  summary: string
  status: string
  assignee?: string
  created: string
}

interface ClockifySummary {
  total_hours: number
  projects: Array<{
    name: string
    hours: number
  }>
  users: Array<{
    name: string
    hours: number
  }>
}

interface SalesforceMetrics {
  available: boolean
  custom_objects: number
  apex_classes: number
  apex_lines_of_code: number
  test_coverage_percent: number
  active_flows: number
  validation_rules: number
  coverage_status: string
}

function DataSummary() {
  const queryClient = useQueryClient()

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['jira-issues'] })
    queryClient.invalidateQueries({ queryKey: ['clockify-summary'] })
    queryClient.invalidateQueries({ queryKey: ['salesforce-metrics'] })
  }

  // Fetch Jira issues - refetch every 10 seconds to catch analysis updates
  const { data: jiraData, isLoading: jiraLoading } = useQuery({
    queryKey: ['jira-issues'],
    queryFn: () => axios.get('/api/jira/issues').then(r => r.data),
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 5000,
  })
  
  const jiraIssues = jiraData?.issues || []
  const jiraTotal = jiraData?.total || 0

  // Fetch Clockify summary - refetch every 10 seconds to catch analysis updates
  const { data: clockifySummary, isLoading: clockifyLoading } = useQuery<ClockifySummary>({
    queryKey: ['clockify-summary'],
    queryFn: () => axios.get('/api/clockify/summary').then(r => r.data),
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 5000,
  })

  // Fetch Confluence summary - refetch every 10 seconds to catch analysis updates
  const { data: confluenceSummary, isLoading: confluenceLoading } = useQuery({
    queryKey: ['confluence-summary'],
    queryFn: () => axios.get('/api/confluence/summary').then(r => r.data),
    refetchInterval: 10000,
    staleTime: 5000,
  })

  // Fetch Salesforce metrics - refetch every 10 seconds to catch analysis updates
  const { data: salesforceMetrics, isLoading: salesforceLoading } = useQuery<SalesforceMetrics>({
    queryKey: ['salesforce-metrics'],
    queryFn: () => axios.get('/api/salesforce/metrics').then(r => r.data),
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 5000,
  })

  const getStatusColor = (status: string) => {
    const lowerStatus = status.toLowerCase()
    if (lowerStatus.includes('done') || lowerStatus.includes('closed')) return 'status-done'
    if (lowerStatus.includes('progress') || lowerStatus.includes('active')) return 'status-progress'
    return 'status-todo'
  }

  const hasAnyData = (jiraIssues && jiraIssues.length > 0) || 
                     clockifySummary?.total_hours || 
                     salesforceMetrics;

  return (
    <div className="data-summary">
      <div className="summary-header">
        <div className="header-left">
          <h2><Icon name="trending-up" size={20} /> Collected Data Summary</h2>
          <p className="summary-description">
            Overview of data collected from all configured sources
          </p>
        </div>
        <button 
          className="btn-refresh" 
          onClick={handleRefresh}
          title="Refresh data now"
        >
          <Icon name="refresh" size={16} /> Refresh
        </button>
      </div>

      {!hasAnyData && !jiraLoading && !clockifyLoading && !salesforceLoading && (
        <div className="no-data-message">
          <div className="no-data-icon"><Icon name="bar-chart" size={48} /></div>
          <h3>No Data Available Yet</h3>
          <p>Run an analysis to collect data from your configured sources.</p>
          <p className="hint">Click the "<Icon name="rocket" size={14} /> Start New Analysis" button above to begin.</p>
        </div>
      )}

      <div className="summary-grid">
        {/* Jira Card */}
        <div className="summary-card jira-card">
          <div className="card-header">
            <div className="card-icon"><Icon name="target" size={24} /></div>
            <h3>Jira Issues</h3>
          </div>
          
          {jiraLoading ? (
            <div className="card-loading">
              <div className="loading-spinner"><Icon name="loader" size={20} /></div>
              <p>Loading...</p>
            </div>
          ) : jiraTotal > 0 ? (
            <>
              <div className="card-count">{jiraTotal}</div>
              <div className="card-subtitle">Total Issues</div>
              
              <div className="issue-list">
                {jiraIssues.slice(0, 5).map((issue: JiraIssue) => (
                  <div key={issue.key} className="issue-item">
                    <span className="issue-key">{issue.key}</span>
                    <span className={`issue-status ${getStatusColor(issue.status)}`}>
                      {issue.status}
                    </span>
                  </div>
                ))}
                {jiraTotal > 5 && (
                  <div className="more-items">
                    +{jiraTotal - 5} more issues
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="card-empty">
              <p>No Jira data available</p>
              <small>Configure Jira connection first</small>
            </div>
          )}
        </div>

        {/* Clockify Card */}
        <div className="summary-card clockify-card">
          <div className="card-header">
            <div className="card-icon"><Icon name="clock" size={24} /></div>
            <h3>Clockify Hours</h3>
          </div>
          
          {clockifyLoading ? (
            <div className="card-loading">
              <div className="loading-spinner"><Icon name="loader" size={20} /></div>
              <p>Loading...</p>
            </div>
          ) : clockifySummary && clockifySummary.total_hours !== undefined ? (
            <>
              <div className="card-count">{clockifySummary.total_hours.toFixed(1)}</div>
              <div className="card-subtitle">Total Hours Tracked</div>
              
              {clockifySummary.projects && clockifySummary.projects.length > 0 && (
                <div className="project-breakdown">
                  <h4>By Project:</h4>
                  {clockifySummary.projects.slice(0, 4).map((project, idx) => (
                    <div key={idx} className="breakdown-item">
                      <span className="breakdown-label">{project.name}</span>
                      <span className="breakdown-value">{project.hours.toFixed(1)}h</span>
                    </div>
                  ))}
                  {clockifySummary.projects.length > 4 && (
                    <div className="more-items">
                      +{clockifySummary.projects.length - 4} more projects
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="card-empty">
              <p>No Clockify data available</p>
              <small>Configure Clockify connection first</small>
            </div>
          )}
        </div>

        {/* Salesforce Card */}
        <div className="summary-card salesforce-card">
          <div className="card-header">
            <div className="card-icon"><Icon name="database" size={24} /></div>
            <h3>Salesforce</h3>
          </div>
          
          {salesforceLoading ? (
            <div className="card-loading">
              <div className="loading-spinner"><Icon name="loader" size={20} /></div>
              <p>Loading...</p>
            </div>
          ) : salesforceMetrics ? (
            <>
              <div className="metrics-grid">
                <div className="metric-item">
                  <div className="metric-value">{salesforceMetrics.custom_objects}</div>
                  <div className="metric-label">Custom Objects</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{salesforceMetrics.apex_classes}</div>
                  <div className="metric-label">Apex Classes</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{salesforceMetrics.apex_lines_of_code.toLocaleString()}</div>
                  <div className="metric-label">Lines of Code</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{salesforceMetrics.test_coverage_percent}%</div>
                  <div className="metric-label">Test Coverage</div>
                </div>
              </div>
            </>
          ) : (
            <div className="card-empty">
              <p>No Salesforce data available</p>
              <small>Configure Salesforce connection first</small>
            </div>
          )}
        </div>

        {/* Confluence Card */}
        <div className="summary-card confluence-card">
          <div className="card-header">
            <div className="card-icon"><Icon name="package" size={24} /></div>
            <h3>Confluence</h3>
          </div>
          
          {confluenceLoading ? (
            <div className="card-loading">
              <div className="loading-spinner"><Icon name="loader" size={20} /></div>
              <p>Loading...</p>
            </div>
          ) : confluenceSummary && confluenceSummary.total_pages > 0 ? (
            <>
              <div className="card-count">{confluenceSummary.total_pages}</div>
              <div className="card-subtitle">Pages Collected</div>
              
              {confluenceSummary.spaces && confluenceSummary.spaces.length > 0 && (
                <div className="project-breakdown">
                  <h4>By Space:</h4>
                  {confluenceSummary.spaces.slice(0, 4).map((space: any, idx: number) => (
                    <div key={idx} className="breakdown-item">
                      <span className="breakdown-label">{space.key}</span>
                      <span className="breakdown-value">{space.page_count} pages</span>
                    </div>
                  ))}
                  {confluenceSummary.spaces.length > 4 && (
                    <div className="more-items">
                      +{confluenceSummary.spaces.length - 4} more spaces
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="card-empty">
              <p>No Confluence data available</p>
              <small>Configure Confluence connection first</small>
            </div>
          )}
        </div>
      </div>

      <div className="summary-footer">
        <p className="footer-note">
          <Icon name="lightbulb" size={14} /> Data is refreshed when you run a new analysis
        </p>
      </div>
    </div>
  )
}

export default DataSummary
