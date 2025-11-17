import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useState } from 'react'
import Icon from './Icon'
import './CrossValidation.css'

interface ValidationResult {
  source_a: string
  source_b: string
  metric: string
  value_a: number | string
  value_b: number | string
  difference: number
  status: 'match' | 'warning' | 'mismatch'
  details: string
}

interface DataQualityMetrics {
  overall_score: number
  completeness: number
  consistency: number
  accuracy: number
  timeliness: number
}

interface CrossValidationData {
  validation_results: ValidationResult[]
  data_quality: DataQualityMetrics
  timestamp: string
  summary: {
    total_checks: number
    passed: number
    warnings: number
    failed: number
  }
}

function CrossValidation() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // Fetch cross-validation data
  const { data: validationData, isLoading, refetch } = useQuery<CrossValidationData>({
    queryKey: ['cross-validation'],
    queryFn: () => axios.get('/api/analysis/cross-validation').then(r => r.data),
    staleTime: 300000, // 5 minutes
    refetchOnWindowFocus: false,
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'match': return <Icon name="check-circle" size={16} color="#22c55e" />
      case 'warning': return <Icon name="alert-circle" size={16} color="#f59e0b" />
      case 'mismatch': return <Icon name="x-circle" size={16} color="#ef4444" />
      default: return <Icon name="help-circle" size={16} color="#9ca3af" />
    }
  }

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'match': return 'status-match'
      case 'warning': return 'status-warning'
      case 'mismatch': return 'status-mismatch'
      default: return ''
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'score-excellent'
    if (score >= 75) return 'score-good'
    if (score >= 60) return 'score-fair'
    return 'score-poor'
  }

  const filteredResults = validationData?.validation_results.filter(result => {
    if (selectedCategory === 'all') return true
    return result.status === selectedCategory
  }) || []

  const categories = [
    { id: 'all', label: 'All Checks', icon: 'bar-chart' },
    { id: 'match', label: 'Passed', icon: 'check-circle' },
    { id: 'warning', label: 'Warnings', icon: 'alert-circle' },
    { id: 'mismatch', label: 'Failed', icon: 'x-circle' },
  ]

  return (
    <div className="cross-validation">
      <div className="validation-header">
        <div className="header-content">
          <h2><Icon name="search" size={20} /> Cross-Validation Dashboard</h2>
          <p className="validation-description">
            Data quality metrics and consistency checks across all sources
          </p>
        </div>
        <button 
          className="btn-refresh"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          {isLoading ? <><Icon name="loader" size={16} /> Loading...</> : <><Icon name="refresh" size={16} /> Refresh</>}
        </button>
      </div>

      {isLoading ? (
        <div className="validation-loading">
          <div className="loading-spinner"><Icon name="loader" size={24} /></div>
          <p>Running cross-validation checks...</p>
        </div>
      ) : validationData ? (
        <>
          {/* Data Quality Score */}
          <div className="quality-score-section">
            <div className="score-card main-score">
              <div className="score-label">Overall Data Quality</div>
              <div className={`score-value ${getScoreColor(validationData.data_quality.overall_score)}`}>
                {validationData.data_quality.overall_score}%
              </div>
              <div className="score-bar">
                <div 
                  className={`score-fill ${getScoreColor(validationData.data_quality.overall_score)}`}
                  style={{ width: `${validationData.data_quality.overall_score}%` }}
                />
              </div>
            </div>

            <div className="score-breakdown">
              <div className="score-card">
                <div className="score-label">Completeness</div>
                <div className={`score-value ${getScoreColor(validationData.data_quality.completeness)}`}>
                  {validationData.data_quality.completeness}%
                </div>
              </div>
              <div className="score-card">
                <div className="score-label">Consistency</div>
                <div className={`score-value ${getScoreColor(validationData.data_quality.consistency)}`}>
                  {validationData.data_quality.consistency}%
                </div>
              </div>
              <div className="score-card">
                <div className="score-label">Accuracy</div>
                <div className={`score-value ${getScoreColor(validationData.data_quality.accuracy)}`}>
                  {validationData.data_quality.accuracy}%
                </div>
              </div>
              <div className="score-card">
                <div className="score-label">Timeliness</div>
                <div className={`score-value ${getScoreColor(validationData.data_quality.timeliness)}`}>
                  {validationData.data_quality.timeliness}%
                </div>
              </div>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="summary-stats">
            <div className="stat-item">
              <span className="stat-icon"><Icon name="clipboard" size={20} /></span>
              <span className="stat-value">{validationData.summary.total_checks}</span>
              <span className="stat-label">Total Checks</span>
            </div>
            <div className="stat-item passed">
              <span className="stat-icon"><Icon name="check-circle" size={20} color="#22c55e" /></span>
              <span className="stat-value">{validationData.summary.passed}</span>
              <span className="stat-label">Passed</span>
            </div>
            <div className="stat-item warning">
              <span className="stat-icon"><Icon name="alert-circle" size={20} color="#f59e0b" /></span>
              <span className="stat-value">{validationData.summary.warnings}</span>
              <span className="stat-label">Warnings</span>
            </div>
            <div className="stat-item failed">
              <span className="stat-icon"><Icon name="x-circle" size={20} color="#ef4444" /></span>
              <span className="stat-value">{validationData.summary.failed}</span>
              <span className="stat-label">Failed</span>
            </div>
          </div>

          {/* Category Filter */}
          <div className="category-filter">
            {categories.map(cat => (
              <button
                key={cat.id}
                className={`filter-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat.id)}
              >
                <span className="filter-icon"><Icon name={cat.icon} size={16} /></span>
                <span className="filter-label">{cat.label}</span>
                {cat.id !== 'all' && (
                  <span className="filter-count">
                    {validationData.validation_results.filter(r => r.status === cat.id).length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Validation Results */}
          <div className="validation-results">
            {filteredResults.length > 0 ? (
              <div className="results-list">
                {filteredResults.map((result, idx) => (
                  <div key={idx} className={`result-card ${getStatusClass(result.status)}`}>
                    <div className="result-header">
                      <div className="result-sources">
                        <span className="source-badge">{result.source_a}</span>
                        <span className="vs-separator">vs</span>
                        <span className="source-badge">{result.source_b}</span>
                      </div>
                      <div className="result-status">
                        {getStatusIcon(result.status)}
                      </div>
                    </div>
                    
                    <div className="result-body">
                      <div className="result-metric">{result.metric}</div>
                      <div className="result-comparison">
                        <div className="comparison-value">
                          <span className="comparison-label">{result.source_a}:</span>
                          <span className="comparison-number">{result.value_a}</span>
                        </div>
                        <div className="comparison-value">
                          <span className="comparison-label">{result.source_b}:</span>
                          <span className="comparison-number">{result.value_b}</span>
                        </div>
                        {typeof result.difference === 'number' && (
                          <div className="comparison-diff">
                            <span className="diff-label">Difference:</span>
                            <span className={`diff-value ${result.difference > 0 ? 'positive' : 'negative'}`}>
                              {result.difference > 0 ? '+' : ''}{result.difference}%
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="result-details">{result.details}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-results">
                <div className="no-results-icon"><Icon name="search" size={48} /></div>
                <p>No validation results in this category</p>
              </div>
            )}
          </div>

          {/* Timestamp */}
          <div className="validation-footer">
            <p className="footer-timestamp">
              Last validated: {new Date(validationData.timestamp).toLocaleString()}
            </p>
          </div>
        </>
      ) : (
        <div className="validation-empty">
          <div className="empty-icon"><Icon name="bar-chart" size={48} /></div>
          <h3>No Validation Data Available</h3>
          <p>
            Run an analysis to generate cross-validation results.
            The system will compare data from Jira, Clockify, Salesforce, and transcripts
            to identify discrepancies and ensure data quality.
          </p>
        </div>
      )}
    </div>
  )
}

export default CrossValidation
