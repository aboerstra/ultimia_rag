import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import axios from 'axios'
import Icon from './Icon'
import './RunAnalysis.css'

interface Analysis {
  id: string
  status: string
  created_at: string
  completed_at?: string
  error?: string
  steps?: Array<{
    step: number
    name: string
    status: string
    error?: string
  }>
  activity_log?: Array<{
    timestamp: string
    message: string
  }>
}

interface AnalysesResponse {
  current: string | null
  analyses: Analysis[]
}

const STEP_NAMES = [
  'Extract Transcripts',
  'Analyze Transcripts',
  'Synthesize Insights',
  'Collect Jira Data',
  'Collect Confluence Data',
  'Collect Clockify Data',
  'Salesforce Production',
  'Salesforce Sandbox',
  'Environment Comparison',
  '', // Step 10 is hidden (metrics generation)
  'Generate QBR Report'
]

function RunAnalysis() {
  const queryClient = useQueryClient()
  const [quickMode, setQuickMode] = useState(true)
  const [skipSteps, setSkipSteps] = useState<{[key: number]: boolean}>({})

  // Fetch analyses - poll only when analysis is running
  const { data: analysesData } = useQuery<AnalysesResponse>({
    queryKey: ['analyses'],
    queryFn: () => axios.get('/api/analysis').then(r => r.data),
    staleTime: 5000,
    refetchInterval: (query) => {
      return query.state.data?.current ? 3000 : false
    },
  })

  // Start analysis mutation
  const startAnalysis = useMutation({
    mutationFn: () => axios.post('/api/analysis/start', { 
      quick_mode: quickMode,
      skip_steps: Object.keys(skipSteps).filter(k => skipSteps[parseInt(k)]).map(k => parseInt(k))
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
  })

  const toggleSkipStep = (stepNumber: number) => {
    setSkipSteps(prev => ({
      ...prev,
      [stepNumber]: !prev[stepNumber]
    }))
  }

  // Cancel analysis mutation
  const cancelAnalysis = useMutation({
    mutationFn: (analysisId: string) => axios.post(`/api/analysis/${analysisId}/cancel`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] })
    },
  })

  const currentAnalysis = analysesData?.analyses.find(a => a.id === analysesData.current)
  const isRunning = !!analysesData?.current
  const recentAnalyses = analysesData?.analyses.slice(0, 5) || []

  const getStepStatus = (stepNumber: number): 'completed' | 'running' | 'pending' | 'error' => {
    if (!currentAnalysis?.steps) return 'pending'
    
    const step = currentAnalysis.steps.find(s => s.step === stepNumber)
    if (!step) return 'pending'
    
    if (step.error) return 'error'
    if (step.status === 'completed') return 'completed'
    if (step.status === 'running') return 'running'
    return 'pending'
  }

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed': return <Icon name="check-circle" size={16} color="#22c55e" />
      case 'running': return <Icon name="loader" size={16} color="#3b82f6" />
      case 'error': return <Icon name="alert-circle" size={16} color="#ef4444" />
      default: return <Icon name="circle" size={16} color="#9ca3af" />
    }
  }

  const handleStartAnalysis = () => {
    const message = 'Start full QBR analysis?\n\n' +
      '• Duration: 10-15 minutes\n' +
      '• Collects data from all configured sources\n' +
      '• Runs cross-validation\n' +
      '• Generates comprehensive QBR report\n\n' +
      'Continue?';
    
    if (confirm(message)) {
      startAnalysis.mutate();
    }
  };

  // Calculate progress percentage
  const completedSteps = currentAnalysis?.steps?.filter(s => s.status === 'completed').length || 0;
  const totalSteps = 11;
  const progressPercent = currentAnalysis ? Math.round((completedSteps / totalSteps) * 100) : 0;

  return (
    <div className="run-analysis">
      <div className="analysis-header">
        <h2><Icon name="rocket" size={20} /> Run Analysis</h2>
        <p className="analysis-description">
          Start a new QBR analysis to collect data from all configured sources, 
          run cross-validation, and generate a comprehensive report.
          <strong> Usually takes 10-15 minutes.</strong>
        </p>
      </div>

      {/* Main Action Button */}
      <div className="analysis-action">
        {/* Quick Mode Toggle */}
        <div className="quick-mode-toggle">
          <label className="checkbox-label">
            <input 
              type="checkbox" 
              checked={quickMode}
              onChange={(e) => setQuickMode(e.target.checked)}
              disabled={isRunning}
            />
            <span className="checkbox-text">
              <Icon name="zap" size={16} /> Quick Mode (reuse cached data from all previous steps)
            </span>
          </label>
          <p className="quick-mode-help">
            <strong>Intelligent caching:</strong> Automatically detects which data needs to be collected fresh vs. reused from cache. Uncheck to force fresh collection from all sources.
          </p>
        </div>

        <button 
          className={`btn-run-analysis ${isRunning ? 'running' : ''}`}
          onClick={handleStartAnalysis}
          disabled={startAnalysis.isPending || isRunning}
        >
          {startAnalysis.isPending ? (
            <><Icon name="clock" size={16} /> Starting Analysis...</>
          ) : isRunning ? (
            <><Icon name="loader" size={16} /> Analysis Running...</>
          ) : (
            <><Icon name="rocket" size={16} /> Start New Analysis</>
          )}
        </button>
        
        {/* Cancel Button - Only show when running */}
        {isRunning && currentAnalysis && currentAnalysis.status === 'running' && (
          <button 
            className="btn-cancel-analysis"
            onClick={() => {
              if (confirm('Cancel this analysis? Progress will be lost.')) {
                cancelAnalysis.mutate(currentAnalysis.id)
              }
            }}
            disabled={cancelAnalysis.isPending}
          >
            {cancelAnalysis.isPending ? (
              <><Icon name="clock" size={16} /> Canceling...</>
            ) : (
              <><Icon name="x" size={16} /> Cancel Analysis</>
            )}
          </button>
        )}
        
        {startAnalysis.isError && (
          <p className="analysis-error">
            Failed to start analysis. Please check that all services are configured and try again.
          </p>
        )}
      </div>

      {/* Step Configuration - Always show */}
      <div className="current-analysis">
        {currentAnalysis && (
          <>
            <div className="analysis-info-bar">
              <div className="analysis-info">
                <span className="info-label">Analysis ID:</span>
                <span className="info-value">{currentAnalysis.id.slice(0, 8)}</span>
              </div>
              <div className="analysis-info">
                <span className="info-label">Status:</span>
                <span className={`analysis-status ${currentAnalysis.status}`}>
                  {currentAnalysis.status}
                </span>
              </div>
              <div className="analysis-info">
                <span className="info-label">Started:</span>
                <span className="info-value">
                  {new Date(currentAnalysis.created_at).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Live Activity Log */}
            {currentAnalysis.activity_log && currentAnalysis.activity_log.length > 0 && (
              <div className="activity-log-section">
                <h4><Icon name="activity" size={16} /> Live Activity</h4>
                <div className="activity-log">
                  {currentAnalysis.activity_log.slice(-20).map((log: any, idx: number) => (
                    <div key={idx} className="activity-item">
                      <span className="activity-time">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span className="activity-message">{log.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* 7-Step Progress Tracker - ALWAYS SHOW */}
        <div className="steps-container">
            <div className="progress-header">
              <h3>Progress Tracker</h3>
              {progressPercent > 0 && (
                <span className="progress-percent" aria-live="polite">
                  {progressPercent}% Complete ({completedSteps} of {totalSteps})
                </span>
              )}
            </div>
            <div className="steps-grid">
              {STEP_NAMES.map((name, index) => {
                const stepNumber = index + 1
                // Skip rendering step 10 (empty name - it's a hidden step)
                if (name === '') return null
                
                const status = getStepStatus(stepNumber)
                const stepData = currentAnalysis?.steps?.find(s => s.step === stepNumber)
                const isSkipped = skipSteps[stepNumber]
                
                return (
                  <div key={stepNumber} className={`step-card ${status} ${isSkipped ? 'skipped' : ''}`}>
                    <div className="step-header">
                      <div className="step-number-badge">{stepNumber}</div>
                      <div className="step-icon">{getStepIcon(status)}</div>
                      <label className="skip-checkbox" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isSkipped || false}
                          onChange={() => toggleSkipStep(stepNumber)}
                          disabled={isRunning}
                          title="Skip this step"
                        />
                      </label>
                    </div>
                    <div className="step-content">
                      <div className="step-name">
                        {name}
                        {isSkipped && <span className="skip-badge">SKIP</span>}
                      </div>
                      {stepData?.error && (
                        <div className="step-error">{stepData.error}</div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

        {currentAnalysis && currentAnalysis.error && (
          <div className="analysis-error-box">
            <strong>Error:</strong> {currentAnalysis.error}
          </div>
        )}
      </div>

      {/* Recent Analyses History */}
      {!currentAnalysis && recentAnalyses.length > 0 && (
        <div className="analysis-history">
          <h3>Recent Analyses</h3>
          <div className="history-list">
            {recentAnalyses.map((analysis) => (
              <div key={analysis.id} className="history-item">
                <div className="history-id">{analysis.id.slice(0, 8)}</div>
                <div className="history-status">
                  <span className={`analysis-status ${analysis.status}`}>
                    {analysis.status}
                  </span>
                </div>
                <div className="history-time">
                  {new Date(analysis.created_at).toLocaleString()}
                </div>
                {analysis.completed_at && (
                  <div className="history-duration">
                    Duration: {Math.round(
                      (new Date(analysis.completed_at).getTime() - 
                       new Date(analysis.created_at).getTime()) / 1000
                    )}s
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default RunAnalysis
