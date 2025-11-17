import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useState } from 'react'
import Icon from './Icon'
import './TranscriptUpload.css'

interface Transcript {
  filename: string
  size: number
  modified: string
  path: string
}

function TranscriptUpload() {
  const queryClient = useQueryClient()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragActive, setDragActive] = useState(false)

  // Fetch transcripts
  const { data: transcripts, isLoading } = useQuery<Transcript[]>({
    queryKey: ['transcripts'],
    queryFn: () => axios.get('/api/transcripts').then(r => r.data),
    staleTime: 300000, // 5 minutes
    refetchOnWindowFocus: false,
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)

      return axios.post('/api/transcripts/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0
          setUploadProgress(percentCompleted)
        },
      })
    },
    onSuccess: () => {
      setSelectedFile(null)
      setUploadProgress(0)
      queryClient.invalidateQueries({ queryKey: ['transcripts'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
    onError: () => {
      setUploadProgress(0)
    },
  })

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.type === 'application/pdf') {
        setSelectedFile(file)
      } else {
        alert('Please select a PDF file')
      }
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const file = e.dataTransfer.files?.[0]
    if (file) {
      if (file.type === 'application/pdf') {
        setSelectedFile(file)
      } else {
        alert('Please select a PDF file')
      }
    }
  }

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="transcript-upload">
      <div className="upload-header">
        <h2><Icon name="upload" size={20} /> Upload Transcripts</h2>
        <p className="upload-description">
          Upload PDF transcripts from meetings to be included in the analysis
        </p>
      </div>

      {/* Upload Area */}
      <div
        className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="upload-icon"><Icon name="folder" size={48} /></div>
        <h3>Drag & Drop PDF Files</h3>
        <p>or</p>
        <label className="file-input-label">
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileSelect}
            className="file-input"
          />
          <span className="btn-browse">Browse Files</span>
        </label>
        <p className="upload-hint">Only PDF files are supported</p>
      </div>

      {/* Selected File Preview */}
      {selectedFile && (
        <div className="file-preview">
          <div className="file-info">
            <div className="file-icon"><Icon name="file-text" size={24} /></div>
            <div className="file-details">
              <div className="file-name">{selectedFile.name}</div>
              <div className="file-size">{formatFileSize(selectedFile.size)}</div>
            </div>
            <button
              className="btn-remove"
              onClick={() => setSelectedFile(null)}
              disabled={uploadMutation.isPending}
            >
              ×
            </button>
          </div>

          {uploadMutation.isPending && (
            <div className="upload-progress">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <div className="progress-text">{uploadProgress}%</div>
            </div>
          )}

          {!uploadMutation.isPending && (
            <button
              className="btn-upload"
              onClick={handleUpload}
            >
              <Icon name="upload" size={16} /> Upload File
            </button>
          )}

          {uploadMutation.isError && (
            <div className="upload-error">
              Upload failed. Please try again.
            </div>
          )}

          {uploadMutation.isSuccess && (
            <div className="upload-success">
              <Icon name="check-circle" size={16} /> File uploaded successfully!
            </div>
          )}
        </div>
      )}

      {/* Transcript List */}
      <div className="transcripts-section">
        <h3><Icon name="clipboard" size={18} /> Uploaded Transcripts ({transcripts?.length || 0})</h3>
        
        {isLoading ? (
          <div className="transcripts-loading">
            <div className="loading-spinner"><Icon name="loader" size={20} /></div>
            <p>Loading transcripts...</p>
          </div>
        ) : transcripts && transcripts.length > 0 ? (
          <div className="transcripts-list">
            {transcripts.map((transcript) => (
              <div key={transcript.filename} className="transcript-item">
                <div className="transcript-icon"><Icon name="file-text" size={20} /></div>
                <div className="transcript-details">
                  <div className="transcript-name">{transcript.filename}</div>
                  <div className="transcript-meta">
                    {formatFileSize(transcript.size)} • 
                    Modified: {new Date(transcript.modified).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="transcripts-empty">
            <div className="empty-icon"><Icon name="folder" size={48} /></div>
            <p>No transcripts uploaded yet. Upload your first transcript above!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default TranscriptUpload
