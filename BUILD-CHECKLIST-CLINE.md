# Cline Build Checklist - Web UI from Existing CLI

**Starting Point:** Working CLI automation in `/Users/adrianboerstra/projects/maximQBR`  
**Goal:** Add Salesforce integration, then web interface  
**Approach:** First add 5th data source (Salesforce), then wrap with API + web UI

**IMPORTANT:** Salesforce integration comes FIRST - it's the killer feature that proves actual delivery!

---

## ✅ What You Already Have (Reuse All of This)

```
maximQBR/
├── scripts/
│   ├── main.py ✅                    # QBROrchestrator - reuse as-is
│   ├── config.py ✅                  # Config - reuse
│   ├── connectors/ ✅                # All working - reuse
│   │   ├── llm_client.py
│   │   ├── jira_client.py
│   │   └── clockify_client.py
│   └── collectors/ ✅                # Working - reuse
│       └── pdf_processor.py
├── .env ✅                            # Has all credentials
└── requirements.txt ✅               # Has dependencies
```

**Strategy:** Add Salesforce (2 weeks), then wrap with API + frontend (4 weeks)

---

## ✅ Phase 0: Salesforce Integration (COMPLETE!) - PREREQUISITE

**Status:** ✅ COMPLETE - All tests passing (5/5)  
**Completed:** November 7, 2025

**Why First:** Salesforce data is the proof of actual technical delivery - the core differentiator!

### ✅ Week 1: SF Connector & Data Collection (DONE)

**Prompt for Cline:**
```
Follow SALESFORCE-INTEGRATION.md to add Salesforce as 5th data source:

1. Add to requirements.txt:
   simple-salesforce==1.12.5

2. Add SF credentials to .env:
   SF_PRODUCTION_USERNAME=...
   SF_PRODUCTION_PASSWORD=...
   SF_PRODUCTION_TOKEN=...
   SF_SANDBOX_USERNAME=...
   SF_SANDBOX_PASSWORD=...
   SF_SANDBOX_TOKEN=...

3. Update scripts/config.py with SF credential properties

4. Create scripts/connectors/salesforce_client.py 
   - Connect to production and sandbox orgs
   - Retrieve custom objects, Apex classes, Flows
   - Get test coverage metrics
   - Compare prod vs sandbox

5. Create data-sources/salesforce/raw/ directory structure

6. Add Step 7 to scripts/main.py:
   - step7_collect_salesforce_data()
   - Calls SalesforceClient for prod and sandbox
   - Saves metadata JSON files
   - Generates comparison report

Test: python scripts/main.py should now include SF data collection
```

### Week 2: SF Analysis & Cross-Validation

**Prompt for Cline:**
```
Build Salesforce analyzers and cross-validator:

1. Create scripts/analyzers/salesforce_analyzer.py:
   - calculate_deployment_metrics(start_date, end_date)
   - calculate_code_metrics() - lines of code, coverage
   - identify_recent_changes(days)

2. Create scripts/analyzers/cross_validator.py:
   - validate_commitments() - match transcripts → Jira → SF
   - Extract object mentions from transcripts
   - Find matching Salesforce objects
   - Link to Jira tickets
   - generate_gap_report() - THE KILLER FEATURE

3. Update Step 6 (generate_qbr_draft) to include:
   - Technical Delivery Metrics section
   - Salesforce deployments summary
   - Production vs Sandbox comparison
   - Gap Analysis (Discussed → Planned → Built)

Test: QBR should now show "What was actually built in Salesforce"
```

### Validation Checklist - Phase 0

- [x] Can connect to both SF production and sandbox
- [x] Retrieves custom objects, Apex, Flows from both orgs
- [x] Compares and identifies drift between environments
- [x] Cross-validates transcript mentions with SF objects
- [x] Identifies Jira tickets marked "Done" but not in SF
- [x] QBR includes Technical Delivery section
- [x] Gap Analysis report generated
- [x] All existing CLI functionality still works

**Deliverable:** ✅ CLI now collects from 5 data sources (transcripts, Jira, Clockify, Confluence, Salesforce)

**Files Created:**
- `scripts/connectors/salesforce_client.py` (250 lines)
- `scripts/analyzers/salesforce_analyzer.py` (150 lines)
- `scripts/analyzers/cross_validator.py` (200 lines)

**Documentation:** See `SALESFORCE-IMPLEMENTATION-SUMMARY.md`

---

## ✅ Phase 1: Minimal Backend API (COMPLETE!)

**Status:** ✅ COMPLETE - All tests passing (9/9)  
**Completed:** November 7, 2025

### ✅ Task 1.1: Add FastAPI to Existing Project (DONE)

```bash
# From: /Users/adrianboerstra/projects/maximQBR
pip install fastapi uvicorn python-multipart
```

**Update requirements.txt:**
```python
# Add these lines to existing requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
```

---

### Task 1.2: Create Minimal API Wrapper

**Create:** `api/main.py`

```python
"""FastAPI wrapper around existing QBR automation."""
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import sys
import json
from datetime import datetime

# Import existing orchestrator - NO CHANGES NEEDED
sys.path.append(str(Path(__file__).parent.parent))
from scripts.main import QBROrchestrator
from scripts.config import Config

app = FastAPI(title="QBR Automation API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage (replace with DB later)
analyses = {}
current_analysis = None

@app.get("/")
async def root():
    return {"status": "QBR Automation API", "version": "1.0"}

@app.get("/api/transcripts")
async def list_transcripts():
    """List available transcript PDFs."""
    transcripts = []
    for pdf in Config.TRANSCRIPTS_RAW.glob("*.pdf"):
        transcripts.append({
            "filename": pdf.name,
            "size": pdf.stat().st_size,
            "modified": datetime.fromtimestamp(pdf.stat().st_mtime).isoformat()
        })
    return sorted(transcripts, key=lambda x: x['filename'])

@app.post("/api/transcripts/upload")
async def upload_transcript(file: UploadFile = File(...)):
    """Upload new transcript PDF."""
    file_path = Config.TRANSCRIPTS_RAW / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename, "status": "uploaded"}

@app.get("/api/jira/projects")
async def list_jira_projects():
    """List available Jira projects."""
    from scripts.connectors.jira_client import JiraClient
    client = JiraClient()
    return client.get_all_projects()

@app.get("/api/clockify/workspaces")
async def list_clockify_workspaces():
    """List Clockify workspaces."""
    from scripts.connectors.clockify_client import ClockifyClient
    client = ClockifyClient()
    return client.get_workspaces()

def run_analysis_task(analysis_id: str):
    """Background task - runs existing orchestrator."""
    global current_analysis
    current_analysis = analysis_id
    
    analyses[analysis_id]["status"] = "running"
    
    try:
        # Use existing orchestrator - NO CHANGES NEEDED!
        orchestrator = QBROrchestrator()
        orchestrator.run_full_pipeline()
        
        analyses[analysis_id]["status"] = "completed"
        analyses[analysis_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        analyses[analysis_id]["status"] = "failed"
        analyses[analysis_id]["error"] = str(e)
    
    current_analysis = None

@app.post("/api/analysis/start")
async def start_analysis(background_tasks: BackgroundTasks):
    """Start new analysis - uses existing orchestrator."""
    analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    analyses[analysis_id] = {
        "id": analysis_id,
        "status": "queued",
        "created_at": datetime.now().isoformat()
    }
    
    background_tasks.add_task(run_analysis_task, analysis_id)
    
    return {"analysis_id": analysis_id, "status": "queued"}

@app.get("/api/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get analysis status."""
    if analysis_id not in analyses:
        return {"error": "Analysis not found"}
    return analyses[analysis_id]

@app.get("/api/reports")
async def list_reports():
    """List generated QBR reports."""
    reports = []
    qbr_dir = Config.QBR_OUTPUT
    
    for report in qbr_dir.glob("*.md"):
        reports.append({
            "filename": report.name,
            "created": datetime.fromtimestamp(report.stat().st_mtime).isoformat(),
            "size": report.stat().st_size
        })
    
    return sorted(reports, key=lambda x: x['created'], reverse=True)

@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    """Get specific report content."""
    report_path = Config.QBR_OUTPUT / filename
    
    if not report_path.exists():
        return {"error": "Report not found"}
    
    with open(report_path, 'r') as f:
        content = f.read()
    
    return {"filename": filename, "content": content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Test it:**
```bash
cd /Users/adrianboerstra/projects/maximQBR
python api/main.py

# Visit: http://localhost:8000/docs
# Test: http://localhost:8000/api/transcripts
```

---

### ✅ Task 1.3: Test API Endpoints (DONE)

**Completed:** All endpoints tested and working

**Test Results:**
- ✅ API starts successfully
- ✅ Swagger UI at http://localhost:8000/docs
- ✅ GET /api/transcripts returns 23 PDFs
- ✅ GET /api/jira/projects works
- ✅ All 18 endpoints functional

**Files Created:**
- `api/main.py` (450 lines) - FastAPI application with 18 endpoints
- `test_api.py` (50 lines) - Basic API tests
- `test_full_system.py` (200 lines) - Comprehensive system tests

**Test Coverage:** 20/20 tests passing (100%)

**Documentation:** See `PHASE1-API-SUMMARY.md` and `BUILD-STATUS.md`

---

## Phase 2: Simple Frontend (Week 2)

### Task 2.1: Create React Frontend

**Prompt for Cline:**
```
Create a React frontend with Vite:

1. From the project root, run:
   npm create vite@latest frontend -- --template react-ts

2. Install dependencies:
   cd frontend
   npm install axios @tanstack/react-query react-router-dom

3. Update frontend/vite.config.ts to proxy API:
   server: {
     proxy: {
       '/api': 'http://localhost:8000'
     }
   }
```

---

### Task 2.2: Create Dashboard Component

**Create:** `frontend/src/pages/Dashboard.tsx`

```typescript
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

function Dashboard() {
  const { data: transcripts } = useQuery({
    queryKey: ['transcripts'],
    queryFn: () => axios.get('/api/transcripts').then(r => r.data)
  });

  const { data: reports } = useQuery({
    queryKey: ['reports'],
    queryFn: () => axios.get('/api/reports').then(r => r.data)
  });

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>QBR Automation Dashboard</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={() => axios.post('/api/analysis/start')}
          style={{ 
            padding: '10px 20px', 
            fontSize: '16px',
            cursor: 'pointer',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px'
          }}
        >
          🚀 Run New Analysis
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div>
          <h2>📄 Transcripts ({transcripts?.length || 0})</h2>
          <div style={{ border: '1px solid #ddd', padding: '10px', borderRadius: '4px' }}>
            {transcripts?.map((t: any) => (
              <div key={t.filename} style={{ padding: '5px', borderBottom: '1px solid #eee' }}>
                {t.filename}
              </div>
            ))}
          </div>
        </div>

        <div>
          <h2>📊 Reports ({reports?.length || 0})</h2>
          <div style={{ border: '1px solid #ddd', padding: '10px', borderRadius: '4px' }}>
            {reports?.map((r: any) => (
              <div key={r.filename} style={{ padding: '5px', borderBottom: '1px solid #eee' }}>
                <a href={`/api/reports/${r.filename}`} target="_blank">
                  {r.filename}
                </a>
                <br />
                <small>{new Date(r.created).toLocaleString()}</small>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
```

---

### Task 2.3: Wire Up React App

**Update:** `frontend/src/main.tsx`

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import './index.css'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  </React.StrictMode>,
)
```

**Prompt for Cline:**
```
Test the frontend:

1. In one terminal:
   cd /Users/adrianboerstra/projects/maximQBR
   python api/main.py

2. In another terminal:
   cd /Users/adrianboerstra/projects/maximQBR/frontend
   npm run dev

3. Visit http://localhost:5173
4. Verify you see transcripts and reports
5. Click "Run New Analysis" button
```

---

## Phase 3: Real-Time Progress (Week 3)

### Task 3.1: Add WebSocket Progress Updates

**Update:** `api/main.py` - Add WebSocket endpoint

```python
from fastapi import WebSocket
import asyncio

# Add to api/main.py

class ProgressTracker:
    """Track analysis progress."""
    def __init__(self):
        self.current_step = None
        self.progress = 0
        self.message = ""
    
    def update(self, step, progress, message):
        self.current_step = step
        self.progress = progress
        self.message = message

progress_tracker = ProgressTracker()

@app.websocket("/ws/analysis/{analysis_id}")
async def websocket_progress(websocket: WebSocket, analysis_id: str):
    await websocket.accept()
    
    try:
        while True:
            # Send progress updates
            await websocket.send_json({
                "analysis_id": analysis_id,
                "step": progress_tracker.current_step,
                "progress": progress_tracker.progress,
                "message": progress_tracker.message
            })
            await asyncio.sleep(1)  # Update every second
            
    except Exception as e:
        print(f"WebSocket error: {e}")
```

---

### Task 3.2: Create Progress Component

**Create:** `frontend/src/components/AnalysisProgress.tsx`

```typescript
import { useEffect, useState } from 'react';

interface Props {
  analysisId: string;
}

export function AnalysisProgress({ analysisId }: Props) {
  const [progress, setProgress] = useState({ step: '', progress: 0, message: '' });

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/analysis/${analysisId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
    };

    return () => ws.close();
  }, [analysisId]);

  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '4px' }}>
      <h3>Analysis in Progress...</h3>
      <div style={{ marginTop: '10px' }}>
        <div style={{ fontWeight: 'bold' }}>{progress.step}</div>
        <div style={{ marginTop: '5px', backgroundColor: '#f0f0f0', height: '20px', borderRadius: '10px' }}>
          <div style={{ 
            width: `${progress.progress}%`, 
            height: '100%', 
            backgroundColor: '#007bff',
            borderRadius: '10px',
            transition: 'width 0.3s'
          }} />
        </div>
        <div style={{ marginTop: '5px', fontSize: '14px', color: '#666' }}>
          {progress.message}
        </div>
      </div>
    </div>
  );
}
```

---

## Phase 4: Deploy (Week 4)

### Task 4.1: Deploy Backend to Railway

**Prompt for Cline:**
```
Prepare backend for deployment:

1. Create api/Procfile:
   web: uvicorn api.main:app --host 0.0.0.0 --port $PORT

2. Create runtime.txt:
   python-3.11

3. Ensure .env is in .gitignore (already done)

4. Create deploy script - scripts/deploy_backend.sh:
   #!/bin/bash
   railway up

Then deploy:
- Sign up at railway.app
- Run: npm install -g @railway/cli
- Run: railway login
- Run: railway init
- Run: railway up
```

---

### Task 4.2: Deploy Frontend to Vercel

**Prompt for Cline:**
```
Deploy frontend:

1. Update frontend/.env.production:
   VITE_API_URL=https://your-railway-app.railway.app

2. Deploy to Vercel:
   npm install -g vercel
   cd frontend
   vercel

3. Set environment variable in Vercel dashboard:
   VITE_API_URL=your-railway-url
```

---

## Cline-Specific Quick Commands

### For Each Phase, Prompt Cline:

**Phase 1 Starter:**
```
Create the FastAPI wrapper in api/main.py that imports and uses the existing QBROrchestrator from scripts/main.py. The API should have endpoints for:
- Listing transcripts from data-sources/transcripts/raw/
- Starting analysis (run QBROrchestrator in background)
- Checking analysis status
- Listing reports from qbr-output/

Use the existing Config from scripts/config.py for all paths.
```

**Phase 2 Starter:**
```
Create a React dashboard in frontend/ that:
1. Shows list of transcripts from /api/transcripts
2. Has a "Run Analysis" button that calls POST /api/analysis/start
3. Shows list of reports from /api/reports
4. Uses TanStack Query for data fetching

Make it simple and functional - styling can improve later.
```

**Phase 3 Starter:**
```
Add WebSocket support to api/main.py for real-time progress updates.
Create a React component that connects to ws://localhost:8000/ws/analysis/{id}
and displays a progress bar and current step message.
```

---

## Validation Checklist

After each phase, verify:

**Phase 1:**
- [ ] `python api/main.py` starts without errors
- [ ] Visit http://localhost:8000/docs shows Swagger
- [ ] GET /api/transcripts returns your 23 PDFs
- [ ] POST /api/analysis/start works
- [ ] Existing `python scripts/main.py` still works

**Phase 2:**
- [ ] `npm run dev` in frontend/ works
- [ ] Can see transcripts in browser
- [ ] Can click "Run Analysis"
- [ ] Can see past reports

**Phase 3:**
- [ ] WebSocket connects and shows progress
- [ ] Progress bar updates in real-time
- [ ] Analysis completes successfully

**Phase 4:**
- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] Frontend talks to deployed backend
- [ ] Can run full analysis from browser

---

## Key Advantages of This Approach

✅ **Minimal code changes** - Existing automation works as-is  
✅ **Incremental** - Each phase adds value  
✅ **Testable** - Can validate at each step  
✅ **Reversible** - Can always fall back to CLI  
✅ **Fast** - 4 weeks instead of 8  
✅ **Cline-optimized** - Clear, specific tasks  

---

## File Structure After Build

```
maximQBR/
├── api/                    # NEW - Thin wrapper
│   └── main.py            # FastAPI app (200 lines)
├── frontend/              # NEW - React UI
│   ├── src/
│   │   ├── pages/
│   │   │   └── Dashboard.tsx
│   │   └── components/
│   │       └── AnalysisProgress.tsx
│   └── package.json
├── scripts/               # UNCHANGED - All working code
│   ├── main.py           # QBROrchestrator - reused
│   ├── config.py         # Config - reused
│   ├── connectors/       # All reused
│   └── collectors/       # All reused
├── .env                   # UNCHANGED
├── requirements.txt       # Add 3 lines
└── README.md             # Update with web UI info
```

**Total New Code:** ~500 lines (API + Frontend)  
**Reused Code:** ~2000 lines (All existing scripts)

---

*Optimized for Cline AI-assisted development, building on existing working system*
