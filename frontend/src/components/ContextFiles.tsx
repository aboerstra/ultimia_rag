import React, { useState, useEffect } from 'react';
import Icon from './Icon';
import './ContextFiles.css';

interface ContextFile {
  filename: string;
  size: number;
  modified: string;
  type: string;
  snapshot_date?: string;
  is_portfolio?: boolean;
  index_status?: string; // 'indexed' | 'indexing' | 'not_indexed'
}

const ContextFiles: React.FC = () => {
  const [files, setFiles] = useState<ContextFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [snapshotDate, setSnapshotDate] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/custom-context/files');
      const data = await response.json();
      setFiles(data);
    } catch (error) {
      console.error('Error loading files:', error);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Check file extension
    const allowedExtensions = ['.json', '.txt', '.md'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
      setMessage({ type: 'error', text: 'Only JSON, TXT, and MD files are allowed' });
      return;
    }

    setSelectedFile(file);
    
    // Auto-detect date from filename if present
    const dateMatch = file.name.match(/(\d{4}-\d{2}-\d{2}|\d{4}-Q[1-4])/i);
    if (dateMatch) {
      setSnapshotDate(dateMatch[1]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    // Validate snapshot date format if provided
    if (snapshotDate && !/^\d{4}-\d{2}-\d{2}$|^\d{4}-Q[1-4]$/i.test(snapshotDate)) {
      setMessage({ type: 'error', text: 'Invalid date format. Use YYYY-MM-DD or YYYY-QX' });
      return;
    }

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    
    // Add snapshot_date if provided
    if (snapshotDate) {
      formData.append('snapshot_date', snapshotDate);
    }

    try {
      const response = await fetch('http://localhost:8000/api/custom-context/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        
        // Show enhanced message for portfolio snapshots
        let successMessage = data.message || `${data.filename} uploaded successfully! Indexing...`;
        
        if (data.is_portfolio && data.snapshot_date) {
          const dateSource = data.date_source === 'manual' ? ' (manual date)' : '';
          successMessage = `Portfolio snapshot (${data.snapshot_date}${dateSource}) uploaded and indexed!`;
        }
        
        setMessage({ type: 'success', text: successMessage });
        loadFiles();
        
        // Trigger automatic reindex in background
        fetch('http://localhost:8000/api/rag/index', { method: 'POST' })
          .then(() => {
            if (data.is_portfolio && data.snapshot_date) {
              setMessage({ 
                type: 'success', 
                text: `Portfolio snapshot (${data.snapshot_date}) indexed and ready for AI Chat!` 
              });
            } else {
              setMessage({ type: 'success', text: `${data.filename} uploaded and indexed!` });
            }
          })
          .catch(() => {
            setMessage({ type: 'success', text: successMessage });
          });
        
        // Clear the form
        setSelectedFile(null);
        setSnapshotDate('');
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Upload failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Upload failed. Please try again.' });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (filename: string) => {
    if (!confirm(`Delete ${filename}?`)) return;

    try {
      const response = await fetch(`http://localhost:8000/api/custom-context/files/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setMessage({ type: 'success', text: `${filename} deleted successfully! Re-indexing...` });
        loadFiles(); // Refresh the list
        
        // Trigger automatic reindex in background
        fetch('http://localhost:8000/api/rag/index', { method: 'POST' })
          .then(() => {
            setMessage({ type: 'success', text: `${filename} deleted and index updated!` });
          })
          .catch(() => {
            setMessage({ type: 'success', text: `${filename} deleted (re-indexing in progress)` });
          });
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Delete failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Delete failed. Please try again.' });
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    } else if (diffInHours < 168) { // Less than a week
      return date.toLocaleDateString('en-US', { weekday: 'short', hour: 'numeric' });
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const handleReindex = async () => {
    setIndexing(true);
    setMessage({ type: 'success', text: 'Reindexing knowledge base... This may take 30-60 seconds.' });

    // Immediately set all files to "indexing" status
    setFiles(prevFiles => prevFiles.map(file => ({
      ...file,
      index_status: 'indexing'
    })));

    try {
      const response = await fetch('http://localhost:8000/api/rag/index', {
        method: 'POST',
      });

      if (response.ok) {
        // Wait a bit for indexing to complete, then poll for completion
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Poll for completion every 2 seconds
        const pollInterval = setInterval(async () => {
          try {
            const statusResponse = await fetch('http://localhost:8000/api/rag/status');
            const statusData = await statusResponse.json();
            
            if (statusData.status === 'ready') {
              clearInterval(pollInterval);
              
              // Set all files back to indexed
              setFiles(prevFiles => prevFiles.map(file => ({
                ...file,
                index_status: 'indexed'
              })));
              
              setMessage({ type: 'success', text: '✅ Knowledge base reindexed! All files are now searchable in AI Chat.' });
              setIndexing(false);
            }
          } catch (pollError) {
            clearInterval(pollInterval);
            setMessage({ type: 'error', text: 'Error checking index status' });
            setIndexing(false);
          }
        }, 2000);
        
        // Safety timeout after 2 minutes
        setTimeout(() => {
          clearInterval(pollInterval);
          setFiles(prevFiles => prevFiles.map(file => ({
            ...file,
            index_status: 'indexed'
          })));
          setIndexing(false);
        }, 120000);
        
      } else {
        setMessage({ type: 'error', text: 'Reindexing failed. Please try again.' });
        // Reset statuses on error
        loadFiles();
        setIndexing(false);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Reindexing failed. Please try again.' });
      // Reset statuses on error
      loadFiles();
      setIndexing(false);
    }
  };

  return (
    <div className="context-files">
      <div className="context-files-header">
        <h2><Icon name="folder" size={20} /> Custom Context Files</h2>
        <p>Upload JSON, TXT, or MD files to add custom context for AI Chat</p>
      </div>

      {message && (
        <div className={`context-files-message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="context-files-upload">
        <div className="upload-section">
          <h3>Upload New File</h3>
          <p className="upload-hint">Supported formats: JSON, TXT, MD</p>
          
          <div className="upload-form">
            <label className="upload-button">
              <input
                type="file"
                accept=".json,.txt,.md"
                onChange={handleFileSelect}
                disabled={uploading}
              />
              <span>{selectedFile ? selectedFile.name : <><Icon name="upload" size={16} /> Choose File</>}</span>
            </label>

            {selectedFile && selectedFile.name.endsWith('.json') && (
              <div className="snapshot-date-input">
                <label htmlFor="snapshot-date">
                  <Icon name="calendar" size={14} /> Snapshot Date (Optional)
                </label>
                <input
                  id="snapshot-date"
                  type="text"
                  value={snapshotDate}
                  onChange={(e) => setSnapshotDate(e.target.value)}
                  placeholder="2025-11-11 or 2026-Q1"
                  disabled={uploading}
                />
                <p className="input-hint">
                  Format: YYYY-MM-DD or YYYY-QX (e.g., 2025-11-11 or 2026-Q1)
                </p>
              </div>
            )}

            {selectedFile && (
              <button
                className="upload-submit-button"
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading ? <><Icon name="clock" size={16} /> Uploading...</> : <><Icon name="upload" size={16} /> Upload File</>}
              </button>
            )}
          </div>

          <div className="upload-info">
            <h4><Icon name="clipboard" size={16} /> Supported File Types:</h4>
            <ul>
              <li><strong>JSON:</strong> Portfolio files, initiatives, structured data</li>
              <li><strong>TXT:</strong> Plain text notes, documentation</li>
              <li><strong>MD:</strong> Markdown documents, formatted notes</li>
            </ul>
            <p className="upload-note">
              <Icon name="info" size={14} /> Files are automatically indexed and made searchable in AI Chat after upload
            </p>
          </div>
        </div>
      </div>

      <div className="context-files-list">
        <div className="files-list-header">
          <h3>Uploaded Files ({files.length})</h3>
          <div className="header-buttons">
            <button
              className="reindex-button"
              onClick={handleReindex}
              disabled={indexing}
              title="Reindex all files for AI Chat search"
            >
              {indexing ? <><Icon name="clock" size={16} /> Indexing...</> : <><Icon name="search" size={16} /> Reindex</>}
            </button>
            <button
              className="refresh-button"
              onClick={loadFiles}
              title="Refresh file list"
            >
              <Icon name="refresh" size={16} /> Refresh
            </button>
          </div>
        </div>
        
        {files.length === 0 ? (
          <div className="no-files">
            <p>No custom context files uploaded yet.</p>
            <p>Upload a file above to get started!</p>
          </div>
        ) : (
          <table className="files-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Snapshot</th>
                <th>Status</th>
                <th>Size</th>
                <th>Modified</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => {
                // Use API-provided portfolio metadata instead of filename regex
                const isPortfolio = file.is_portfolio || false;
                const snapshotDate = file.snapshot_date || null;
                
                return (
                  <tr key={file.filename} className={isPortfolio ? 'portfolio-file' : ''}>
                    <td className="filename">
                      {isPortfolio && <Icon name="calendar" size={14} className="portfolio-icon" />}
                      {file.filename}
                    </td>
                    <td className="filetype">
                      <span className={`type-badge ${file.type} ${isPortfolio ? 'portfolio' : ''}`}>
                        {isPortfolio ? 'PORTFOLIO' : file.type.toUpperCase()}
                      </span>
                    </td>
                    <td className="snapshot">
                      {snapshotDate ? (
                        <span className="snapshot-date">
                          <Icon name="clock" size={12} /> {snapshotDate}
                        </span>
                      ) : (
                        <span className="no-snapshot">—</span>
                      )}
                    </td>
                    <td className="status">
                      <span 
                        className={`status-indicator ${file.index_status || 'indexed'}`} 
                        title={
                          (file.index_status === 'indexing') ? 'Currently indexing...' :
                          (file.index_status === 'not_indexed') ? 'Not indexed - file not searchable' :
                          'Indexed - searchable in AI Chat'
                        }
                      ></span>
                    </td>
                    <td className="filesize">{formatFileSize(file.size)}</td>
                    <td className="modified">{formatDate(file.modified)}</td>
                    <td className="actions">
                      <button
                        className="delete-button"
                        onClick={() => handleDelete(file.filename)}
                        title="Delete file"
                      >
                        <Icon name="trash" size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="context-files-help">
        <h3><Icon name="lightbulb" size={18} /> How It Works</h3>
        <ol>
          <li><strong>Upload files:</strong> Add JSON portfolio files, text notes, or markdown docs</li>
          <li><strong>Automatic indexing:</strong> Files are immediately indexed and searchable</li>
          <li><strong>Ask questions:</strong> Go to AI Chat and ask about your uploaded content</li>
        </ol>
        
          <div className="example-box">
          <h4><Icon name="calendar" size={16} /> Portfolio Snapshots</h4>
          <p>Two ways to add a snapshot date:</p>
          <ul>
            <li><strong>Option 1:</strong> Include date in filename (e.g., <code>portfolio-2025-11-11.json</code>)</li>
            <li><strong>Option 2:</strong> Use the "Snapshot Date" field when uploading any JSON file</li>
          </ul>
          <p><strong>Supported formats:</strong> <code>YYYY-MM-DD</code> (e.g., 2025-11-11) or <code>YYYY-QX</code> (e.g., 2026-Q1)</p>
          <p><strong>Smart Management:</strong> Same date = replaces old snapshot, different date = both coexist</p>
          <p><strong>AI Queries:</strong> "Compare API Gateway between Nov and Q1" or "Show November roadmap"</p>
        </div>
      </div>
    </div>
  );
};

export default ContextFiles;
