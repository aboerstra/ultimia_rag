import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useState } from 'react'
import Icon from './Icon'
import './Reports.css'

interface Report {
  filename: string
  created: string
  size: number
  path: string
}

function Reports() {
  const [selectedReport, setSelectedReport] = useState<string | null>(null)
  const [reportContent, setReportContent] = useState<string>('')
  const [loading, setLoading] = useState(false)

  // Fetch reports with auto-refresh every 5 seconds
  const { data: reports, isLoading } = useQuery<Report[]>({
    queryKey: ['reports'],
    queryFn: () => axios.get('/api/reports').then(r => r.data),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
    refetchOnWindowFocus: true, // Also refresh when window regains focus
  })

  const viewReport = async (filename: string) => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/reports/${filename}`)
      setSelectedReport(filename)
      setReportContent(response.data.content)
    } catch (error) {
      console.error('Error loading report:', error)
      alert('Failed to load report. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const closeModal = () => {
    setSelectedReport(null)
    setReportContent('')
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getReportType = (filename: string) => {
    if (filename.includes('qbr-draft')) return 'Draft'
    if (filename.includes('final')) return 'Final'
    if (filename.includes('analysis')) return 'Analysis'
    return 'Report'
  }

  return (
    <div className="reports-component">
      <div className="reports-header">
        <h2><Icon name="bar-chart" size={20} /> Generated Reports</h2>
        <p className="reports-description">
          View and download QBR reports generated from analysis runs
        </p>
      </div>

      {isLoading ? (
        <div className="reports-loading">
          <div className="loading-spinner"><Icon name="loader" size={24} /></div>
          <p>Loading reports...</p>
        </div>
      ) : reports && reports.length > 0 ? (
        <div className="reports-grid">
          {reports.map((report) => (
            <div key={report.filename} className="report-card">
              <div className="report-card-header">
                <div className="report-icon"><Icon name="file-text" size={24} /></div>
                <div className="report-type-badge">
                  {getReportType(report.filename)}
                </div>
              </div>
              
              <div className="report-card-body">
                <h3 className="report-filename">{report.filename}</h3>
                <div className="report-meta">
                  <div className="meta-item">
                    <span className="meta-label">Created:</span>
                    <span className="meta-value">
                      {new Date(report.created).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Time:</span>
                    <span className="meta-value">
                      {new Date(report.created).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Size:</span>
                    <span className="meta-value">
                      {formatFileSize(report.size)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="report-card-footer">
                <button
                  className="btn-view"
                  onClick={() => viewReport(report.filename)}
                  disabled={loading}
                >
                  <Icon name="eye" size={14} /> View
                </button>
                <a
                  href={`/api/reports/${report.filename}/download`}
                  download
                  className="btn-download"
                >
                  <Icon name="download" size={14} /> Download
                </a>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="reports-empty">
          <div className="empty-icon"><Icon name="folder" size={48} /></div>
          <h3>No Reports Yet</h3>
          <p>
            Reports will appear here after you run an analysis.
            Use the "Run Analysis" section above to generate your first QBR report.
          </p>
        </div>
      )}

      {/* Report Viewer Modal */}
      {selectedReport && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                <span className="modal-icon"><Icon name="file-text" size={20} /></span>
                <h3>{selectedReport}</h3>
              </div>
              <button className="close-btn" onClick={closeModal}>×</button>
            </div>
            
            <div className="modal-content">
              {loading ? (
                <div className="modal-loading">
                  <div className="loading-spinner"><Icon name="loader" size={24} /></div>
                  <p>Loading report content...</p>
                </div>
              ) : (
                <pre className="report-content">{reportContent}</pre>
              )}
            </div>
            
            <div className="modal-footer">
              <a 
                href={`/api/reports/${selectedReport}/download`} 
                download 
                className="btn-modal-download"
              >
                <Icon name="download" size={16} /> Download
              </a>
              <button className="btn-modal-close" onClick={closeModal}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Reports
