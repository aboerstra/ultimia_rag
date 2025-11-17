import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import './ContextPanel.css'
import HealthStatus from './HealthStatus'
import RunAnalysis from './RunAnalysis'
import Reports from './Reports'
import TranscriptUpload from './TranscriptUpload'
import DataSummary from './DataSummary'
import CrossValidation from './CrossValidation'
import CollapsibleSection from './CollapsibleSection'
import PersonaBuilder from './PersonaBuilder'
import ContextFiles from './ContextFiles'

interface Stats {
  transcripts: {
    raw: number
    extracted: number
  }
  reports: number
  analyses: number
  current_analysis: string | null
  salesforce?: {
    custom_objects: number
    apex_classes: number
    test_coverage: number
  }
}

interface ContextPanelProps {
  isOpen: boolean
  onToggle: () => void
  width: number
  onWidthChange: (width: number) => void
}

interface ToolGroup {
  title: string
  icon: string
  defaultExpanded: boolean
}

function ContextPanel({ isOpen, onToggle, width, onWidthChange }: ContextPanelProps) {
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    systemConfiguration: true,
    addContent: false,
    generateReports: false,
    diagnostics: false
  })

  // Fetch stats
  const { data: stats } = useQuery<Stats>({
    queryKey: ['stats'],
    queryFn: () => axios.get('/api/stats').then(r => r.data),
    staleTime: 30000,
    refetchInterval: 10000,
  })

  const toggleGroup = (groupKey: string) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupKey]: !prev[groupKey]
    }))
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = width

    const handleMouseMove = (e: MouseEvent) => {
      const diff = startX - e.clientX
      const newWidth = Math.max(300, Math.min(800, startWidth + diff))
      onWidthChange(newWidth)
    }

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  return (
    <div className={`context-panel ${isOpen ? 'open' : 'collapsed'}`} style={{ width: isOpen ? `${width}px` : '40px' }}>
      {/* Toggle Button */}
      <button 
        className="context-panel-toggle"
        onClick={onToggle}
        title={isOpen ? 'Hide context tools' : 'Show context tools'}
      >
        {isOpen ? '▶' : '◀'}
      </button>

      {/* Resize Handle */}
      {isOpen && (
        <div className="resize-handle" onMouseDown={handleMouseDown} title="Drag to resize" />
      )}

      {/* Panel Content */}
      {isOpen && (
        <div className="context-panel-content">
          <div className="context-panel-header">
            <h2>Workspace Tools</h2>
          </div>

          {/* Compact Stats Row */}
          <div className="context-stats-compact">
            <div className="stat-item">
              <svg className="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              <span className="stat-value">{stats?.transcripts.raw || 0}</span>
            </div>
            <div className="stat-item">
              <svg className="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2"/>
              </svg>
              <span className="stat-value">{stats?.reports || 0}</span>
            </div>
            <div className="stat-item">
              <svg className="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
              <span className="stat-value">{stats?.analyses || 0}</span>
            </div>
            {stats?.salesforce && (
              <div className="stat-item">
                <svg className="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>
                </svg>
                <span className="stat-value">{stats.salesforce.custom_objects}</span>
              </div>
            )}
          </div>

          {/* System Configuration Group */}
          <div className="tool-group">
            <button 
              className="tool-group-header"
              onClick={() => toggleGroup('systemConfiguration')}
            >
              <svg className="group-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 1v6m0 6v6m5.2-12l-4.8 4.8m0 6.4 4.8 4.8M23 12h-6m-6 0H5m12.2 5.2-4.8-4.8m0-6.4-4.8-4.8"/>
              </svg>
              <span className="group-title">System Configuration</span>
              <span className="group-toggle">{expandedGroups.systemConfiguration ? '▼' : '▶'}</span>
            </button>
            {expandedGroups.systemConfiguration && (
              <div className="tool-group-content">
                <CollapsibleSection title="Connector Management" icon="settings" defaultExpanded={false}>
                  <HealthStatus />
                </CollapsibleSection>
              </div>
            )}
          </div>

          {/* Add Content Group */}
          <div className="tool-group">
            <button 
              className="tool-group-header"
              onClick={() => toggleGroup('addContent')}
            >
              <svg className="group-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
              </svg>
              <span className="group-title">Add Content</span>
              <span className="group-badge">{(stats?.transcripts.raw || 0) > 0 ? '●' : '○'}</span>
              <span className="group-toggle">{expandedGroups.addContent ? '▼' : '▶'}</span>
            </button>
            {expandedGroups.addContent && (
              <div className="tool-group-content">
                <CollapsibleSection title="Upload Transcripts" icon="file-text" defaultExpanded={false}>
                  <TranscriptUpload />
                </CollapsibleSection>
                <CollapsibleSection title="Add Custom Knowledge" icon="folder" defaultExpanded={false}>
                  <ContextFiles />
                </CollapsibleSection>
                <CollapsibleSection title="Build Personas" icon="users" defaultExpanded={false}>
                  <PersonaBuilder />
                </CollapsibleSection>
              </div>
            )}
          </div>

          {/* Generate Reports Group */}
          <div className="tool-group">
            <button 
              className="tool-group-header"
              onClick={() => toggleGroup('generateReports')}
            >
              <svg className="group-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              <span className="group-title">Generate Reports</span>
              <span className="group-toggle">{expandedGroups.generateReports ? '▼' : '▶'}</span>
            </button>
            {expandedGroups.generateReports && (
              <div className="tool-group-content">
                <CollapsibleSection title="Generate QBR Report" icon="zap" defaultExpanded={false}>
                  <RunAnalysis />
                </CollapsibleSection>
                <CollapsibleSection title="View Reports" icon="clipboard" defaultExpanded={false}>
                  <Reports />
                </CollapsibleSection>
              </div>
            )}
          </div>

          {/* Diagnostics Group */}
          <div className="tool-group">
            <button 
              className="tool-group-header"
              onClick={() => toggleGroup('diagnostics')}
            >
              <svg className="group-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
              <span className="group-title">Diagnostics</span>
              <span className="group-toggle">{expandedGroups.diagnostics ? '▼' : '▶'}</span>
            </button>
            {expandedGroups.diagnostics && (
              <div className="tool-group-content">
                <CollapsibleSection title="Data Summary" icon="bar-chart" defaultExpanded={false}>
                  <DataSummary />
                </CollapsibleSection>
                <CollapsibleSection title="Verify Data Quality" icon="search" defaultExpanded={false}>
                  <CrossValidation />
                </CollapsibleSection>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ContextPanel
