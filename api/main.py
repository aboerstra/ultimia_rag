"""FastAPI wrapper around existing QBR automation."""
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Body, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import existing orchestrator - NO CHANGES NEEDED
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'scripts'))

from scripts.main import QBROrchestrator
from scripts.config import Config

# Import database models for conversation persistence
from api.models import Conversation as DBConversation, Message as DBMessage, get_db, init_db

app = FastAPI(
    title="QBR Automation API",
    description="API for automated Quarterly Business Review generation",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    init_db()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class SalesforceOrgConfig(BaseModel):
    production_org: Optional[str] = None
    sandbox_org: Optional[str] = None

class JiraConfig(BaseModel):
    project: Optional[str] = None
    space: Optional[str] = None
    date_range_months: Optional[int] = None

class ClockifyConfig(BaseModel):
    client: Optional[str] = None
    projects: Optional[str] = None
    date_range_months: Optional[int] = None

# Conversation Models
class MessageCreate(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    sources: Optional[List[str]] = None

class ConversationCreate(BaseModel):
    id: str
    title: str
    messages: List[MessageCreate]
    createdAt: str
    updatedAt: str

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    updatedAt: Optional[str] = None

class MigrateConversationsRequest(BaseModel):
    conversations: List[ConversationCreate]

# Simple in-memory storage (replace with DB later)
analyses = {}
current_analysis = None


@app.get("/")
async def root():
    """Root endpoint - API status."""
    return {
        "status": "QBR Automation API",
        "version": "1.0.0",
        "endpoints": {
            "transcripts": "/api/transcripts",
            "jira": "/api/jira/projects",
            "clockify": "/api/clockify/workspaces",
            "salesforce": "/api/salesforce/metrics",
            "analysis": "/api/analysis",
            "reports": "/api/reports"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_sources": {
            "transcripts": Config.TRANSCRIPTS_RAW.exists(),
            "jira": bool(Config.JIRA_URL),
            "clockify": bool(Config.CLOCKIFY_API_KEY),
            "salesforce": bool(Config.SF_PRODUCTION_USERNAME)
        }
    }


@app.get("/api/health/test/{service}")
async def test_service(service: str):
    """Test a specific service connection."""
    try:
        if service == "jira":
            from scripts.connectors.jira_client import JiraClient
            client = JiraClient()
            projects = client.get_all_projects()
            return {
                "service": "jira",
                "status": "ready",
                "message": f"Connected - {len(projects)} projects accessible"
            }
        elif service == "clockify":
            from scripts.connectors.clockify_client import ClockifyClient
            client = ClockifyClient()
            workspaces = client.get_workspaces()
            return {
                "service": "clockify",
                "status": "ready",
                "message": f"Connected - {len(workspaces)} workspaces found"
            }
        elif service == "salesforce_prod":
            from scripts.connectors.salesforce_client import SalesforceClient
            client = SalesforceClient(is_sandbox=False)
            return {
                "service": "salesforce_prod",
                "status": "ready",
                "message": f"Connected - Org: {client.org_name}"
            }
        elif service == "confluence":
            from atlassian import Confluence
            confluence = Confluence(
                url=Config.CONFLUENCE_URL,
                username=Config.CONFLUENCE_EMAIL,
                password=Config.CONFLUENCE_API_TOKEN,
                cloud=True
            )
            spaces = confluence.get_all_spaces(start=0, limit=10)
            space_count = len(spaces.get('results', []))
            return {
                "service": "confluence",
                "status": "ready",
                "message": f"Connected - {space_count} spaces accessible"
            }
        elif service == "salesforce_sandbox":
            from scripts.connectors.salesforce_client import SalesforceClient
            client = SalesforceClient(is_sandbox=True)
            return {
                "service": "salesforce_sandbox",
                "status": "ready",
                "message": f"Connected - Org: {client.org_name}"
            }
        else:
            raise HTTPException(status_code=404, detail="Service not found")
    except Exception as e:
        return {
            "service": service,
            "status": "error",
            "message": f"Connection failed: {str(e)}"
        }

@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check - tests each service."""
    health_status = Config.get_health_status()
    
    # Add transcript count
    transcript_count = len(list(Config.TRANSCRIPTS_RAW.glob("*.pdf"))) if Config.TRANSCRIPTS_RAW.exists() else 0
    
    services = {}
    
    # LLM Service
    services["llm"] = {
        "name": health_status["llm"]["name"],
        "status": "ready" if health_status["llm"]["configured"] else "not_configured",
        "message": "API key configured" if health_status["llm"]["configured"] else "Missing OPENROUTER_API_KEY"
    }
    
    # Jira Service - Just check configuration, don't connect
    if health_status["jira"]["configured"]:
        services["jira"] = {
            "name": health_status["jira"]["name"],
            "status": "ready",
            "message": "Configured - API credentials found"
        }
    else:
        services["jira"] = {
            "name": health_status["jira"]["name"],
            "status": "not_configured",
            "message": "Missing JIRA_URL or JIRA_API_TOKEN"
        }
    
    # Confluence Service - Separate from Jira
    if health_status["confluence"]["configured"]:
        services["confluence"] = {
            "name": health_status["confluence"]["name"],
            "status": "ready",
            "message": "Configured - API credentials found"
        }
    else:
        services["confluence"] = {
            "name": health_status["confluence"]["name"],
            "status": "not_configured",
            "message": "Missing CONFLUENCE_URL or CONFLUENCE_API_TOKEN"
        }
    
    # Clockify Service - Just check configuration, don't connect
    if health_status["clockify"]["configured"]:
        services["clockify"] = {
            "name": health_status["clockify"]["name"],
            "status": "ready",
            "message": "Configured - API key found"
        }
    else:
        services["clockify"] = {
            "name": health_status["clockify"]["name"],
            "status": "not_configured",
            "message": "Missing CLOCKIFY_API_KEY"
        }
    
    # Salesforce Production - Just show configured org without connecting
    if health_status["salesforce_prod"]["configured"]:
        org_name = Config.SF_PRODUCTION_ORG or "configured"
        services["salesforce_prod"] = {
            "name": health_status["salesforce_prod"]["name"],
            "status": "ready",
            "message": f"Configured - Org: {org_name}"
        }
    else:
        services["salesforce_prod"] = {
            "name": health_status["salesforce_prod"]["name"],
            "status": "not_configured",
            "message": "Run 'sf org login web' or add credentials to .env"
        }
    
    # Salesforce Sandbox - Just show configured org without connecting
    if health_status["salesforce_sandbox"]["configured"]:
        org_name = Config.SF_SANDBOX_ORG or "configured"
        services["salesforce_sandbox"] = {
            "name": health_status["salesforce_sandbox"]["name"],
            "status": "ready",
            "message": f"Configured - Org: {org_name}"
        }
    else:
        services["salesforce_sandbox"] = {
            "name": health_status["salesforce_sandbox"]["name"],
            "status": "not_configured",
            "message": "Run 'sf org login web --instance-url https://test.salesforce.com'"
        }
    
    # Transcripts
    services["transcripts"] = {
        "name": "Transcripts",
        "status": "ready" if transcript_count > 0 else "not_configured",
        "message": f"{transcript_count} PDF files available" if transcript_count > 0 else "No transcripts found in data-sources/transcripts/raw"
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "services": services
    }


# ==================== TRANSCRIPTS ====================

@app.get("/api/transcripts")
async def list_transcripts():
    """List available transcript PDFs."""
    transcripts = []
    
    if not Config.TRANSCRIPTS_RAW.exists():
        return []
    
    for pdf in Config.TRANSCRIPTS_RAW.glob("*.pdf"):
        transcripts.append({
            "filename": pdf.name,
            "size": pdf.stat().st_size,
            "modified": datetime.fromtimestamp(pdf.stat().st_mtime).isoformat(),
            "path": str(pdf.relative_to(Config.PROJECT_ROOT))
        })
    
    return sorted(transcripts, key=lambda x: x['modified'], reverse=True)


@app.post("/api/transcripts/upload")
async def upload_transcript(file: UploadFile = File(...)):
    """Upload new transcript PDF."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_path = Config.TRANSCRIPTS_RAW / file.filename
    
    # Ensure directory exists
    Config.TRANSCRIPTS_RAW.mkdir(parents=True, exist_ok=True)
    
    # Save file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "filename": file.filename,
        "status": "uploaded",
        "size": len(content),
        "path": str(file_path.relative_to(Config.PROJECT_ROOT))
    }


@app.get("/api/transcripts/extracted")
async def list_extracted_transcripts():
    """List extracted/analyzed transcripts."""
    extracted = []
    
    if not Config.TRANSCRIPTS_EXTRACTED.exists():
        return []
    
    for json_file in Config.TRANSCRIPTS_EXTRACTED.glob("*_analysis.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                extracted.append({
                    "filename": json_file.name,
                    "original": data.get('filename', 'Unknown'),
                    "analyzed": True,
                    "size": json_file.stat().st_size
                })
        except:
            pass
    
    return extracted


# ==================== JIRA ====================

@app.get("/api/jira/projects")
async def list_jira_projects():
    """List available Jira projects, filtered by client code if set."""
    try:
        from scripts.connectors.jira_client import JiraClient
        client = JiraClient()
        projects = client.get_all_projects()
        
        # Filter by client code if set
        if Config.CLIENT_CODE:
            code = Config.CLIENT_CODE.upper()
            projects = [
                p for p in projects
                if code in p.get('name', '').upper() or code in p.get('key', '').upper()
            ]
        
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Jira API error: {str(e)}")


@app.get("/api/jira/spaces")
async def list_confluence_spaces():
    """List available Confluence spaces."""
    try:
        from atlassian import Confluence
        
        # Use Jira credentials for Confluence (same Atlassian instance)
        confluence = Confluence(
            url=Config.CONFLUENCE_URL or Config.JIRA_URL,
            username=Config.CONFLUENCE_EMAIL or Config.JIRA_EMAIL,
            password=Config.CONFLUENCE_API_TOKEN or Config.JIRA_API_TOKEN,
            cloud=True
        )
        
        spaces = confluence.get_all_spaces(start=0, limit=500)
        return [
            {
                'key': space['key'],
                'name': space['name'],
                'type': space.get('type', 'unknown')
            }
            for space in spaces.get('results', [])
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confluence API error: {str(e)}")


@app.get("/api/config/jira")
async def get_jira_config():
    """Get current Jira configuration from environment."""
    return {
        "project": Config.JIRA_PROJECT,
        "space": Config.JIRA_SPACE,
        "date_range_months": Config.DATE_RANGE_MONTHS
    }

@app.get("/api/config/client-code")
async def get_client_code():
    """Get current client code from environment."""
    return {
        "client_code": Config.CLIENT_CODE or ""
    }

@app.post("/api/config/set-client-code")
async def set_client_code(client_code: str = Body(..., embed=True)):
    """Set client code (updates environment)."""
    from pathlib import Path
    
    env_file = Path(__file__).parent.parent / '.env'
    
    try:
        # Read current .env
        env_lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add CLIENT_CODE
        updated = False
        new_lines = []
        
        for line in env_lines:
            if line.startswith('CLIENT_CODE='):
                new_lines.append(f'CLIENT_CODE={client_code}\n')
                updated = True
            else:
                new_lines.append(line)
        
        # Add if not found
        if not updated:
            new_lines.append(f'CLIENT_CODE={client_code}\n')
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        # Reload configuration to pick up new value
        Config.reload()
        
        return {
            "success": True,
            "message": "Client code updated. Configuration reloaded.",
            "client_code": client_code
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update .env: {str(e)}")

@app.post("/api/jira/set-config")
async def set_jira_config(config: JiraConfig):
    """Set Jira/Confluence configuration (updates environment)."""
    project = config.project
    space = config.space
    date_range_months = config.date_range_months
    from pathlib import Path
    
    env_file = Path(__file__).parent.parent / '.env'
    
    try:
        # Read current .env
        env_lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add settings
        updated_project = False
        updated_space = False
        updated_date_range = False
        new_lines = []
        
        for line in env_lines:
            if project and line.startswith('JIRA_PROJECT='):
                new_lines.append(f'JIRA_PROJECT={project}\n')
                updated_project = True
            elif space and line.startswith('JIRA_SPACE='):
                new_lines.append(f'JIRA_SPACE={space}\n')
                updated_space = True
            elif date_range_months is not None and line.startswith('DATE_RANGE_MONTHS='):
                new_lines.append(f'DATE_RANGE_MONTHS={date_range_months}\n')
                updated_date_range = True
            else:
                new_lines.append(line)
        
        # Add if not found
        if project and not updated_project:
            new_lines.append(f'JIRA_PROJECT={project}\n')
        if space and not updated_space:
            new_lines.append(f'JIRA_SPACE={space}\n')
        if date_range_months is not None and not updated_date_range:
            new_lines.append(f'DATE_RANGE_MONTHS={date_range_months}\n')
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        # Reload configuration to pick up new values
        Config.reload()
        
        return {
            "success": True,
            "message": "Jira configuration updated. Configuration reloaded.",
            "project": project,
            "space": space,
            "date_range_months": date_range_months
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update .env: {str(e)}")


@app.get("/api/jira/issues")
async def list_jira_issues():
    """Get Jira issues from last 6 months."""
    issues_file = Config.JIRA_RAW / 'issues.json'
    
    if not issues_file.exists():
        return {"message": "No issues data available. Run analysis first.", "issues": []}
    
    with open(issues_file, 'r') as f:
        issues = json.load(f)
    
    # Return summary
    status_counts = {}
    for issue in issues:
        status = issue.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total": len(issues),
        "status_breakdown": status_counts,
        "issues": issues[:50]  # Return first 50 for preview
    }


# ==================== CONFLUENCE ====================

class ConfluenceConfig(BaseModel):
    space: Optional[str] = None
    date_range_months: Optional[int] = None

@app.get("/api/confluence/spaces")
async def list_confluence_spaces_dedicated():
    """List available Confluence spaces (dedicated endpoint) - with pagination and client code filtering."""
    try:
        from atlassian import Confluence
        
        # Remove /wiki from URL if present - Confluence Cloud API uses base URL
        confluence_url = Config.CONFLUENCE_URL.replace('/wiki', '') if Config.CONFLUENCE_URL else Config.JIRA_URL
        
        confluence = Confluence(
            url=confluence_url,
            username=Config.CONFLUENCE_EMAIL,
            password=Config.CONFLUENCE_API_TOKEN,
            cloud=True
        )
        
        # Determine client code filter
        client_code_filter = Config.CLIENT_CODE.upper() if Config.CLIENT_CODE else None
        
        # Fetch spaces with pagination, filtering by client code during pagination
        all_spaces = []
        start = 0
        limit = 100  # Use consistent batch size
        max_iterations = 100  # Safety limit to prevent infinite loops
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            response = confluence.get_all_spaces(start=start, limit=limit)
            spaces = response.get('results', [])
            
            if not spaces:
                # No more spaces returned
                break
            
            # Filter this batch by client code if set
            if client_code_filter:
                filtered_batch = [
                    space for space in spaces
                    if client_code_filter in space.get('name', '').upper() or 
                       client_code_filter in space.get('key', '').upper()
                ]
                all_spaces.extend(filtered_batch)
            else:
                all_spaces.extend(spaces)
            
            # If we got fewer results than the limit, we've reached the end
            if len(spaces) < limit:
                break
                
            # Otherwise, fetch the next batch
            start += len(spaces)
        
        return [
            {
                'key': space['key'],
                'name': space['name'],
                'type': space.get('type', 'unknown')
            }
            for space in all_spaces
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confluence API error: {str(e)}")


@app.get("/api/confluence/summary")
async def get_confluence_summary():
    """Get Confluence pages summary."""
    # Look for any *_pages.json file in confluence/raw
    confluence_raw = Config.PROJECT_ROOT / 'data-sources' / 'confluence' / 'raw'
    
    if not confluence_raw.exists():
        return {"total_pages": 0, "spaces": []}
    
    # Find pages file
    pages_files = list(confluence_raw.glob('*_pages.json'))
    if not pages_files:
        return {"total_pages": 0, "spaces": []}
    
    # Read the first pages file
    with open(pages_files[0], 'r') as f:
        pages = json.load(f)
    
    # Count pages by space and calculate content size
    space_counts = {}
    total_content_chars = 0
    
    for page in pages:
        space_key = page.get('space', {}).get('key', 'Unknown')
        space_counts[space_key] = space_counts.get(space_key, 0) + 1
        total_content_chars += page.get('body_length', 0)
    
    return {
        "total_pages": len(pages),
        "total_content_chars": total_content_chars,
        "spaces": [
            {"key": key, "page_count": count}
            for key, count in space_counts.items()
        ]
    }


@app.post("/api/confluence/set-config")
async def set_confluence_config(config: ConfluenceConfig):
    """Set Confluence configuration (updates environment)."""
    space = config.space
    date_range_months = config.date_range_months
    from pathlib import Path
    
    env_file = Path(__file__).parent.parent / '.env'
    
    try:
        # Read current .env
        env_lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add settings
        updated_space = False
        updated_date_range = False
        new_lines = []
        
        for line in env_lines:
            if space and line.startswith('JIRA_SPACE='):
                new_lines.append(f'JIRA_SPACE={space}\n')
                updated_space = True
            elif date_range_months is not None and line.startswith('DATE_RANGE_MONTHS='):
                new_lines.append(f'DATE_RANGE_MONTHS={date_range_months}\n')
                updated_date_range = True
            else:
                new_lines.append(line)
        
        # Add if not found
        if space and not updated_space:
            new_lines.append(f'JIRA_SPACE={space}\n')
        if date_range_months is not None and not updated_date_range:
            new_lines.append(f'DATE_RANGE_MONTHS={date_range_months}\n')
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        # Reload configuration to pick up new values
        Config.reload()
        
        return {
            "success": True,
            "message": "Confluence configuration updated. Configuration reloaded.",
            "space": space,
            "date_range_months": date_range_months
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update .env: {str(e)}")


# ==================== CLOCKIFY ====================

@app.get("/api/clockify/workspaces")
async def list_clockify_workspaces():
    """List Clockify workspaces, filtered by client code if set."""
    try:
        from scripts.connectors.clockify_client import ClockifyClient
        client = ClockifyClient()
        workspaces = client.get_workspaces()
        
        # Filter by client code if set
        if Config.CLIENT_CODE:
            code = Config.CLIENT_CODE.upper()
            workspaces = [
                w for w in workspaces
                if code in w.get('name', '').upper()
            ]
        
        return workspaces
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clockify API error: {str(e)}")


@app.get("/api/clockify/clients")
async def list_clockify_clients():
    """List Clockify clients, filtered by client code if set."""
    try:
        from scripts.connectors.clockify_client import ClockifyClient
        client = ClockifyClient()
        clients = client.get_clients()
        
        # Filter by client code if set
        if Config.CLIENT_CODE:
            code = Config.CLIENT_CODE.upper()
            clients = [
                c for c in clients
                if code in c.get('name', '').upper()
            ]
        
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clockify API error: {str(e)}")


@app.get("/api/clockify/projects")
async def list_clockify_projects(client_id: Optional[str] = None):
    """List Clockify projects, optionally filtered by client."""
    try:
        from scripts.connectors.clockify_client import ClockifyClient
        client = ClockifyClient()
        return client.get_projects(client_id=client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clockify API error: {str(e)}")


@app.get("/api/config/clockify")
async def get_clockify_config():
    """Get current Clockify configuration from environment."""
    return {
        "client": Config.CLOCKIFY_CLIENT,
        "projects": Config.CLOCKIFY_PROJECTS,
        "date_range_months": Config.DATE_RANGE_MONTHS
    }


@app.post("/api/clockify/set-config")
async def set_clockify_config(config: ClockifyConfig):
    """Set Clockify configuration (updates environment)."""
    client = config.client
    projects = config.projects
    date_range_months = config.date_range_months
    from pathlib import Path
    
    env_file = Path(__file__).parent.parent / '.env'
    
    try:
        # Read current .env
        env_lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add settings
        updated_client = False
        updated_projects = False
        updated_date_range = False
        new_lines = []
        
        for line in env_lines:
            if client and line.startswith('CLOCKIFY_CLIENT='):
                new_lines.append(f'CLOCKIFY_CLIENT={client}\n')
                updated_client = True
            elif projects and line.startswith('CLOCKIFY_PROJECTS='):
                new_lines.append(f'CLOCKIFY_PROJECTS={projects}\n')
                updated_projects = True
            elif date_range_months is not None and line.startswith('DATE_RANGE_MONTHS='):
                new_lines.append(f'DATE_RANGE_MONTHS={date_range_months}\n')
                updated_date_range = True
            else:
                new_lines.append(line)
        
        # Add if not found
        if client and not updated_client:
            new_lines.append(f'CLOCKIFY_CLIENT={client}\n')
        if projects and not updated_projects:
            new_lines.append(f'CLOCKIFY_PROJECTS={projects}\n')
        if date_range_months is not None and not updated_date_range:
            new_lines.append(f'DATE_RANGE_MONTHS={date_range_months}\n')
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        # Reload configuration to pick up new values
        Config.reload()
        
        return {
            "success": True,
            "message": "Clockify configuration updated. Configuration reloaded.",
            "client": client,
            "projects": projects,
            "date_range_months": date_range_months
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update .env: {str(e)}")


@app.get("/api/clockify/summary")
async def get_clockify_summary():
    """Get Clockify project summary."""
    summary_file = Config.CLOCKIFY_RAW / 'project_summary.json'
    
    if not summary_file.exists():
        return {"message": "No summary data available. Run analysis first.", "projects": {}}
    
    with open(summary_file, 'r') as f:
        projects_dict = json.load(f)
    
    # Calculate total hours and format for frontend
    total_hours = sum(proj.get('total_hours', 0) for proj in projects_dict.values())
    
    # Convert to list of projects with names
    projects_list = [
        {
            'name': proj_name,
            'hours': proj_data.get('total_hours', 0)
        }
        for proj_name, proj_data in projects_dict.items()
    ]
    
    return {
        'total_hours': total_hours,
        'projects': projects_list,
        'users': []  # Could be populated if needed
    }


# ==================== SALESFORCE ====================

@app.get("/api/salesforce/orgs")
async def list_salesforce_orgs():
    """List all available Salesforce orgs from CLI."""
    import subprocess
    import json
    
    try:
        result = subprocess.run(
            ['sf', 'org', 'list', '--json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            orgs = data.get('result', {}).get('nonScratchOrgs', [])
            
            return {
                "available": True,
                "orgs": [{
                    "username": org.get('username'),
                    "alias": org.get('alias'),
                    "isSandbox": org.get('isSandbox', False),
                    "isDefault": org.get('isDefaultUsername', False),
                    "connectedStatus": org.get('connectedStatus')
                } for org in orgs]
            }
        
        return {
            "available": False,
            "message": "SF CLI not available or no orgs logged in",
            "orgs": []
        }
        
    except Exception as e:
        return {
            "available": False,
            "message": str(e),
            "orgs": []
        }


@app.get("/api/config/salesforce")
async def get_salesforce_config():
    """Get current Salesforce configuration from environment."""
    return {
        "production_org": Config.SF_PRODUCTION_ORG,
        "sandbox_org": Config.SF_SANDBOX_ORG
    }


@app.post("/api/salesforce/set-org")
async def set_salesforce_org(config: SalesforceOrgConfig):
    """Set which Salesforce org to use (updates environment)."""
    production_org = config.production_org
    sandbox_org = config.sandbox_org
    import os
    from pathlib import Path
    
    env_file = Path(__file__).parent.parent / '.env'
    
    try:
        # Read current .env
        env_lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add SF org settings
        updated_prod = False
        updated_sandbox = False
        new_lines = []
        
        for line in env_lines:
            if production_org and line.startswith('SF_PRODUCTION_ORG='):
                new_lines.append(f'SF_PRODUCTION_ORG={production_org}\n')
                updated_prod = True
            elif sandbox_org and line.startswith('SF_SANDBOX_ORG='):
                new_lines.append(f'SF_SANDBOX_ORG={sandbox_org}\n')
                updated_sandbox = True
            else:
                new_lines.append(line)
        
        # Add if not found
        if production_org and not updated_prod:
            new_lines.append(f'SF_PRODUCTION_ORG={production_org}\n')
        if sandbox_org and not updated_sandbox:
            new_lines.append(f'SF_SANDBOX_ORG={sandbox_org}\n')
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        # Reload configuration to pick up new values
        Config.reload()
        
        return {
            "success": True,
            "message": "Org selection updated. Configuration reloaded.",
            "production_org": production_org,
            "sandbox_org": sandbox_org
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update .env: {str(e)}")


@app.get("/api/salesforce/metrics")
async def get_salesforce_metrics():
    """Get Salesforce metrics summary."""
    metrics_file = Config.SALESFORCE_RAW / 'metrics.json'
    
    if not metrics_file.exists():
        return {
            "available": False,
            "message": "Salesforce data not available. Configure credentials and run analysis."
        }
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    return {
        "available": True,
        **metrics
    }


@app.get("/api/salesforce/comparison")
async def get_salesforce_comparison():
    """Get Production vs Sandbox comparison."""
    comparison_file = Config.SALESFORCE_RAW / 'comparison.json'
    
    if not comparison_file.exists():
        return {
            "available": False,
            "message": "Environment comparison not available."
        }
    
    with open(comparison_file, 'r') as f:
        comparison = json.load(f)
    
    return {
        "available": True,
        **comparison
    }


# ==================== ANALYSIS ====================

def run_analysis_task(analysis_id: str):
    """Background task - runs existing orchestrator."""
    from datetime import datetime as dt, timedelta
    
    global current_analysis
    current_analysis = analysis_id
    
    analyses[analysis_id]["status"] = "running"
    analyses[analysis_id]["steps"] = []
    analyses[analysis_id]["activity_log"] = []
    
    def log_activity(message: str):
        """Log real-time activity."""
        analyses[analysis_id]["activity_log"].append({
            "timestamp": dt.now().isoformat(),
            "message": message
        })
    
    def check_cancelled():
        """Check if analysis was cancelled."""
        return analyses[analysis_id]["status"] == "cancelled"
    
    try:
        quick_mode = analyses[analysis_id].get("quick_mode", True)
        skip_steps = analyses[analysis_id].get("skip_steps", [])
        log_activity(f"🚀 Analysis started ({'Quick Mode' if quick_mode else 'Full Mode'})")
        
        # Use existing orchestrator
        orchestrator = QBROrchestrator()
        
        # Step 1: Extract transcripts (SKIP if manually skipped OR cached in quick_mode)
        if 1 in skip_steps:
            log_activity("⏭️ Step 1: Skipped transcript extraction (as requested)")
            analyses[analysis_id]["steps"].append({"step": 1, "name": "Extracting transcripts", "status": "skipped"})
            transcripts = []
        elif quick_mode and Config.TRANSCRIPTS_EXTRACTED.exists():
            existing_md = list(Config.TRANSCRIPTS_EXTRACTED.glob("*.md"))
            if existing_md:
                log_activity(f"⚡ Step 1: Using {len(existing_md)} cached text extractions")
                analyses[analysis_id]["steps"].append({"step": 1, "name": "Extracting transcripts", "status": "completed"})
                # Load existing transcripts
                transcripts = []
                for md_file in existing_md:
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            text = f.read()
                            transcripts.append({
                                'filename': md_file.stem + '.pdf',
                                'text': text,
                                'metadata': {'cached': True}
                            })
                    except:
                        pass
            else:
                log_activity("📄 Step 1: Extracting transcripts...")
                analyses[analysis_id]["steps"].append({"step": 1, "name": "Extracting transcripts", "status": "running"})
                transcripts = orchestrator.step1_extract_transcripts()
                if check_cancelled(): return
                log_activity(f"✅ Extracted {len(transcripts)} transcripts")
                analyses[analysis_id]["steps"][-1]["status"] = "completed"
        else:
            log_activity("📄 Step 1: Extracting transcripts...")
            analyses[analysis_id]["steps"].append({"step": 1, "name": "Extracting transcripts", "status": "running"})
            transcripts = orchestrator.step1_extract_transcripts()
            if check_cancelled(): return
            log_activity(f"✅ Extracted {len(transcripts)} transcripts")
            analyses[analysis_id]["steps"][-1]["status"] = "completed"
        
        # Step 2: Analyze transcripts (SKIP if manually skipped OR cached in quick_mode)
        if 2 in skip_steps:
            log_activity("⏭️ Step 2: Skipped transcript analysis (as requested)")
            analyses[analysis_id]["steps"].append({"step": 2, "name": "Analyzing transcripts", "status": "skipped"})
            transcript_analyses = []
        elif quick_mode and Config.TRANSCRIPTS_EXTRACTED.exists():
            existing_analyses = list(Config.TRANSCRIPTS_EXTRACTED.glob("*_analysis.json"))
            if existing_analyses:
                log_activity(f"⚡ Step 2: Using {len(existing_analyses)} cached AI analyses")
                analyses[analysis_id]["steps"].append({"step": 2, "name": "Analyzing transcripts", "status": "completed"})
                # Load existing analyses
                transcript_analyses = []
                for analysis_file in existing_analyses:
                    try:
                        with open(analysis_file, 'r', encoding='utf-8') as f:
                            analysis = json.load(f)
                            transcript_analyses.append(analysis)
                    except:
                        pass
                log_activity(f"   💡 Uncheck 'Quick Mode' to force re-analysis")
            else:
                log_activity(f"🤖 Step 2: Analyzing {len(transcripts)} transcripts with AI...")
                analyses[analysis_id]["steps"].append({"step": 2, "name": "Analyzing transcripts", "status": "running"})
                transcript_analyses = []
                for i, transcript in enumerate(transcripts, 1):
                    log_activity(f"   📄 [{i}/{len(transcripts)}] Analyzing: {transcript['filename']}")
                    try:
                        from scripts.connectors.llm_client import LLMClient
                        llm = LLMClient()
                        analysis = llm.analyze_transcript(
                            transcript['text'],
                            transcript['filename']
                        )
                        analysis['filename'] = transcript['filename']
                        analysis['metadata'] = transcript['metadata']
                        transcript_analyses.append(analysis)
                        log_activity(f"   ✅ [{i}/{len(transcripts)}] Completed: {transcript['filename']}")
                        
                        # Save individual analysis
                        output_path = Config.TRANSCRIPTS_EXTRACTED / f"{transcript['filename'].replace('.pdf', '_analysis.json')}"
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(analysis, f, indent=2, default=str)
                            
                    except Exception as e:
                        log_activity(f"   ❌ [{i}/{len(transcripts)}] Failed: {transcript['filename']} - {str(e)}")
                        transcript_analyses.append({
                            'filename': transcript['filename'],
                            'error': str(e)
                        })
                    
                    if check_cancelled(): return
                
                log_activity(f"✅ Completed all {len(transcript_analyses)} transcript analyses")
                analyses[analysis_id]["steps"][-1]["status"] = "completed"
        else:
            log_activity(f"🤖 Step 2: Analyzing {len(transcripts)} transcripts with AI...")
            analyses[analysis_id]["steps"].append({"step": 2, "name": "Analyzing transcripts", "status": "running"})
            transcript_analyses = []
            for i, transcript in enumerate(transcripts, 1):
                log_activity(f"   📄 [{i}/{len(transcripts)}] Analyzing: {transcript['filename']}")
                try:
                    from scripts.connectors.llm_client import LLMClient
                    llm = LLMClient()
                    analysis = llm.analyze_transcript(
                        transcript['text'],
                        transcript['filename']
                    )
                    analysis['filename'] = transcript['filename']
                    analysis['metadata'] = transcript['metadata']
                    transcript_analyses.append(analysis)
                    log_activity(f"   ✅ [{i}/{len(transcripts)}] Completed: {transcript['filename']}")
                    
                    # Save individual analysis
                    output_path = Config.TRANSCRIPTS_EXTRACTED / f"{transcript['filename'].replace('.pdf', '_analysis.json')}"
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(analysis, f, indent=2, default=str)
                        
                except Exception as e:
                    log_activity(f"   ❌ [{i}/{len(transcripts)}] Failed: {transcript['filename']} - {str(e)}")
                    transcript_analyses.append({
                        'filename': transcript['filename'],
                        'error': str(e)
                    })
                
                if check_cancelled(): return
            
            log_activity(f"✅ Completed all {len(transcript_analyses)} transcript analyses")
            analyses[analysis_id]["steps"][-1]["status"] = "completed"
        
        # Step 3: Synthesize insights (SKIP if manually skipped OR cached in quick_mode)
        skip_steps = analyses[analysis_id].get("skip_steps", [])
        synthesis_file = Config.SYNTHESIS / 'transcript-synthesis.md'
        
        if 3 in skip_steps:
            log_activity("⏭️ Step 3: Skipped synthesis (as requested)")
            analyses[analysis_id]["steps"].append({"step": 3, "name": "Synthesizing insights", "status": "skipped"})
        elif quick_mode and synthesis_file.exists():
            log_activity(f"⚡ Step 3: Using cached synthesis (last updated: {dt.fromtimestamp(synthesis_file.stat().st_mtime).strftime('%b %d')})")
            analyses[analysis_id]["steps"].append({"step": 3, "name": "Synthesizing insights", "status": "completed"})
        else:
            log_activity("📝 Step 3: Synthesizing insights...")
            analyses[analysis_id]["steps"].append({"step": 3, "name": "Synthesizing insights", "status": "running"})
            orchestrator.step3_synthesize_insights(transcript_analyses)
            if check_cancelled(): return
            log_activity("✅ Synthesis complete")
            analyses[analysis_id]["steps"][-1]["status"] = "completed"
        
        # Step 4: Collect Jira data (SKIP if manually skipped OR cached in quick_mode)
        if 4 in skip_steps:
            log_activity("⏭️ Step 4: Skipped Jira collection (as requested)")
            analyses[analysis_id]["steps"].append({"step": 4, "name": "Collecting Jira data", "status": "skipped"})
        else:
            jira_file = Config.JIRA_RAW / 'issues.json'
            has_jira_data = False
            if jira_file.exists():
                try:
                    with open(jira_file, 'r') as f:
                        jira_data = json.load(f)
                        has_jira_data = isinstance(jira_data, list) and len(jira_data) > 0
                except:
                    pass
            
            if quick_mode and has_jira_data:
                log_activity(f"⚡ Step 4: Using cached Jira data ({len(jira_data)} issues)")
                analyses[analysis_id]["steps"].append({"step": 4, "name": "Collecting Jira data", "status": "completed"})
            else:
                if quick_mode and not has_jira_data:
                    log_activity(f"🎫 Step 4: No cached data, collecting from Jira (Project: {Config.JIRA_PROJECT}, Range: {Config.DATE_RANGE_MONTHS} months)...")
                else:
                    log_activity(f"🎫 Step 4: Collecting Jira issues (Project: {Config.JIRA_PROJECT}, Range: {Config.DATE_RANGE_MONTHS} months)...")
                analyses[analysis_id]["steps"].append({"step": 4, "name": "Collecting Jira data", "status": "running"})
            
            try:
                orchestrator.step4_collect_jira_data()
                if check_cancelled(): return
                
                # Check how many issues were collected
                jira_file_check = Config.JIRA_RAW / 'issues.json'
                if jira_file_check.exists():
                    with open(jira_file_check, 'r') as f:
                        collected_issues = json.load(f)
                        issue_count = len(collected_issues) if isinstance(collected_issues, list) else 0
                        
                        if issue_count > 0:
                            log_activity(f"✅ Jira data collected: {issue_count} issues found")
                        else:
                            log_activity(f"⚠️ Jira returned 0 issues - Check if project '{Config.JIRA_PROJECT}' exists and has issues in last {Config.DATE_RANGE_MONTHS} months")
                else:
                    log_activity("⚠️ Jira collection completed but no file created")
                    
                analyses[analysis_id]["steps"][-1]["status"] = "completed"
            except Exception as e:
                log_activity(f"❌ Jira collection failed: {str(e)}")
                analyses[analysis_id]["steps"][-1]["status"] = "failed"
                analyses[analysis_id]["steps"][-1]["error"] = str(e)
        
        # Step 5: Collect Confluence data (SKIP if any *_pages.json exists and quick_mode)
        confluence_files = list(Config.CONFLUENCE_RAW.glob('*_pages.json')) if Config.CONFLUENCE_RAW.exists() else []
        if quick_mode and confluence_files:
            confluence_file = confluence_files[0]
            log_activity(f"⚡ Step 5: Using cached Confluence data (last updated: {dt.fromtimestamp(confluence_file.stat().st_mtime).strftime('%b %d')})")
            analyses[analysis_id]["steps"].append({"step": 5, "name": "Collecting Confluence data", "status": "completed"})
        else:
            log_activity("📚 Step 5: Collecting Confluence pages...")
            analyses[analysis_id]["steps"].append({"step": 5, "name": "Collecting Confluence data", "status": "running"})
            orchestrator.step4b_collect_confluence_data()
            if check_cancelled(): return
            log_activity("✅ Confluence data collected")
            analyses[analysis_id]["steps"][-1]["status"] = "completed"
        
        # Step 6: Collect Clockify data (intelligent caching)
        clockify_file = Config.CLOCKIFY_RAW / 'project_summary.json'
        has_clockify_data = False
        if clockify_file.exists():
            try:
                with open(clockify_file, 'r') as f:
                    clockify_data = json.load(f)
                    # Check if it's a non-empty dict with actual project data
                    has_clockify_data = isinstance(clockify_data, dict) and len(clockify_data) > 0
            except:
                pass
        
        if quick_mode and has_clockify_data:
            project_count = len(clockify_data)
            log_activity(f"⚡ Step 6: Using cached Clockify data ({project_count} projects)")
            analyses[analysis_id]["steps"].append({"step": 6, "name": "Collecting Clockify data", "status": "completed"})
        else:
            if quick_mode and not has_clockify_data:
                log_activity(f"⏱️ Step 6: No cached data, collecting from Clockify (Client: {Config.CLOCKIFY_CLIENT}, Range: {Config.DATE_RANGE_MONTHS} months)...")
            else:
                log_activity(f"⏱️ Step 6: Collecting Clockify time entries (Client: {Config.CLOCKIFY_CLIENT}, Range: {Config.DATE_RANGE_MONTHS} months)...")
            analyses[analysis_id]["steps"].append({"step": 6, "name": "Collecting Clockify data", "status": "running"})
            
            try:
                orchestrator.step5_collect_clockify_data()
                if check_cancelled(): return
                
                # Check how much data was collected
                clockify_file_check = Config.CLOCKIFY_RAW / 'project_summary.json'
                if clockify_file_check.exists():
                    with open(clockify_file_check, 'r') as f:
                        collected_data = json.load(f)
                        if isinstance(collected_data, dict) and len(collected_data) > 0:
                            project_count = len(collected_data)
                            total_hours = sum(p.get('total_hours', 0) for p in collected_data.values())
                            log_activity(f"✅ Clockify data collected: {project_count} projects, {total_hours:.1f} total hours")
                        else:
                            log_activity(f"⚠️ Clockify returned no data - Check if client ID '{Config.CLOCKIFY_CLIENT}' is correct")
                else:
                    log_activity("⚠️ Clockify collection completed but no file created")
                    
                analyses[analysis_id]["steps"][-1]["status"] = "completed"
            except Exception as e:
                log_activity(f"❌ Clockify collection failed: {str(e)}")
                analyses[analysis_id]["steps"][-1]["status"] = "failed"
                analyses[analysis_id]["steps"][-1]["error"] = str(e)
        
        # Step 7: Collect Salesforce Production data
        skip_steps = analyses[analysis_id].get("skip_steps", [])
        
        if 7 not in skip_steps:
            prod_file = Config.SALESFORCE_RAW / 'production' / 'metadata.json'
            if quick_mode and prod_file.exists():
                log_activity(f"⚡ Step 7: Using cached Salesforce Production data (last updated: {dt.fromtimestamp(prod_file.stat().st_mtime).strftime('%b %d')})")
                analyses[analysis_id]["steps"].append({"step": 7, "name": "Salesforce Production", "status": "completed"})
            else:
                log_activity(f"☁️ Step 7: Collecting Salesforce Production data (Org: {Config.SF_PRODUCTION_ORG or 'default'})...")
                analyses[analysis_id]["steps"].append({"step": 7, "name": "Salesforce Production", "status": "running"})
                
                try:
                    from scripts.connectors.salesforce_client import SalesforceClient
                    prod_client = SalesforceClient(is_sandbox=False)
                    
                    prod_data = {
                        'environment': 'production',
                        'custom_objects': prod_client.get_custom_objects(),
                        'apex_classes': prod_client.get_apex_classes(),
                        'flows': prod_client.get_flows(),
                        'coverage': prod_client.get_apex_coverage(),
                        'validation_rules': prod_client.get_validation_rules(),
                        'deployments': prod_client.get_deployment_history()
                    }
                    
                    # Save production data
                    prod_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(prod_file, 'w') as f:
                        json.dump(prod_data, f, indent=2, default=str)
                    
                    if check_cancelled(): return
                    log_activity(f"✅ Production data collected: {len(prod_data['custom_objects'])} objects, {len(prod_data['apex_classes'])} Apex classes")
                    analyses[analysis_id]["steps"][-1]["status"] = "completed"
                except Exception as e:
                    log_activity(f"❌ Salesforce Production collection failed: {str(e)}")
                    analyses[analysis_id]["steps"][-1]["status"] = "failed"
                    analyses[analysis_id]["steps"][-1]["error"] = str(e)
        else:
            log_activity("⏭️ Step 7: Skipped Salesforce Production (as requested)")
            analyses[analysis_id]["steps"].append({"step": 7, "name": "Salesforce Production", "status": "skipped"})
        
        # Step 8: Collect Salesforce Sandbox data
        if 8 not in skip_steps:
            sandbox_file = Config.SALESFORCE_RAW / 'sandbox' / 'metadata.json'
            if quick_mode and sandbox_file.exists():
                log_activity(f"⚡ Step 8: Using cached Salesforce Sandbox data (last updated: {dt.fromtimestamp(sandbox_file.stat().st_mtime).strftime('%b %d')})")
                analyses[analysis_id]["steps"].append({"step": 8, "name": "Salesforce Sandbox", "status": "completed"})
            else:
                log_activity(f"☁️ Step 8: Collecting Salesforce Sandbox data (Org: {Config.SF_SANDBOX_ORG or 'default'})...")
                analyses[analysis_id]["steps"].append({"step": 8, "name": "Salesforce Sandbox", "status": "running"})
                
                try:
                    from scripts.connectors.salesforce_client import SalesforceClient
                    sandbox_client = SalesforceClient(is_sandbox=True)
                    
                    sandbox_data = {
                        'environment': 'sandbox',
                        'custom_objects': sandbox_client.get_custom_objects(),
                        'apex_classes': sandbox_client.get_apex_classes(),
                        'flows': sandbox_client.get_flows(),
                        'coverage': sandbox_client.get_apex_coverage(),
                        'validation_rules': sandbox_client.get_validation_rules(),
                        'deployments': sandbox_client.get_deployment_history()
                    }
                    
                    # Save sandbox data
                    sandbox_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(sandbox_file, 'w') as f:
                        json.dump(sandbox_data, f, indent=2, default=str)
                    
                    if check_cancelled(): return
                    log_activity(f"✅ Sandbox data collected: {len(sandbox_data['custom_objects'])} objects, {len(sandbox_data['apex_classes'])} Apex classes")
                    analyses[analysis_id]["steps"][-1]["status"] = "completed"
                except ValueError as e:
                    log_activity(f"ℹ️ Sandbox org not available: {str(e)}")
                    analyses[analysis_id]["steps"][-1]["status"] = "completed"
                except Exception as e:
                    log_activity(f"❌ Salesforce Sandbox collection failed: {str(e)}")
                    analyses[analysis_id]["steps"][-1]["status"] = "failed"
                    analyses[analysis_id]["steps"][-1]["error"] = str(e)
        else:
            log_activity("⏭️ Step 8: Skipped Salesforce Sandbox (as requested)")
            analyses[analysis_id]["steps"].append({"step": 8, "name": "Salesforce Sandbox", "status": "skipped"})
        
        # Step 9: Compare Salesforce environments
        if 9 not in skip_steps:
            comparison_file = Config.SALESFORCE_RAW / 'comparison.json'
            prod_file = Config.SALESFORCE_RAW / 'production' / 'metadata.json'
            sandbox_file = Config.SALESFORCE_RAW / 'sandbox' / 'metadata.json'
            
            if quick_mode and comparison_file.exists():
                log_activity(f"⚡ Step 9: Using cached environment comparison (last updated: {dt.fromtimestamp(comparison_file.stat().st_mtime).strftime('%b %d')})")
                analyses[analysis_id]["steps"].append({"step": 9, "name": "Environment Comparison", "status": "completed"})
            elif prod_file.exists() and sandbox_file.exists():
                log_activity("🔍 Step 9: Comparing Production vs Sandbox environments...")
                analyses[analysis_id]["steps"].append({"step": 9, "name": "Environment Comparison", "status": "running"})
                
                try:
                    from scripts.connectors.salesforce_client import SalesforceClient
                    
                    # Recreate clients to use comparison method
                    prod_client = SalesforceClient(is_sandbox=False)
                    sandbox_client = SalesforceClient(is_sandbox=True)
                    
                    # Calculate date range
                    end_date = dt.now()
                    start_date = end_date - timedelta(days=Config.DATE_RANGE_MONTHS * 30)
                    
                    comparison = prod_client.compare_with_environment(
                        sandbox_client,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d')
                    )
                    
                    # Save comparison
                    with open(comparison_file, 'w') as f:
                        json.dump(comparison, f, indent=2, default=str)
                    
                    if check_cancelled(): return
                    
                    # Log comparison results
                    drift_count = len(comparison.get('only_in_production', [])) + len(comparison.get('only_in_sandbox', []))
                    log_activity(f"✅ Comparison complete: {drift_count} drift items found")
                    
                    if 'deployment_comparison' in comparison:
                        sync_status = comparison['deployment_comparison']['analysis']['sync_status']
                        log_activity(f"   Sync status: {sync_status}")
                    
                    analyses[analysis_id]["steps"][-1]["status"] = "completed"
                except Exception as e:
                    log_activity(f"❌ Environment comparison failed: {str(e)}")
                    analyses[analysis_id]["steps"][-1]["status"] = "failed"
                    analyses[analysis_id]["steps"][-1]["error"] = str(e)
            else:
                log_activity("ℹ️ Step 9: Skipping comparison (need both Production and Sandbox data)")
                analyses[analysis_id]["steps"].append({"step": 9, "name": "Environment Comparison", "status": "skipped"})
        else:
            log_activity("⏭️ Step 9: Skipped environment comparison (as requested)")
            analyses[analysis_id]["steps"].append({"step": 9, "name": "Environment Comparison", "status": "skipped"})
        
        # Step 10: Generate metrics summary
        prod_file = Config.SALESFORCE_RAW / 'production' / 'metadata.json'
        if prod_file.exists():
            try:
                with open(prod_file, 'r') as f:
                    prod_data = json.load(f)
                
                apex_lines = sum(cls.get('LengthWithoutComments', 0) for cls in prod_data.get('apex_classes', []))
                coverage = prod_data.get('coverage', {}).get('overall_coverage', 0)
                
                metrics = {
                    'custom_objects': len(prod_data.get('custom_objects', [])),
                    'apex_classes': len(prod_data.get('apex_classes', [])),
                    'apex_lines_of_code': apex_lines,
                    'test_coverage_percent': coverage,
                    'active_flows': len(prod_data.get('flows', [])),
                    'validation_rules': len(prod_data.get('validation_rules', [])),
                    'coverage_status': 'Good' if coverage >= 75 else 'Needs Improvement'
                }
                
                metrics_file = Config.SALESFORCE_RAW / 'metrics.json'
                with open(metrics_file, 'w') as f:
                    json.dump(metrics, f, indent=2)
                
                log_activity(f"   📊 Metrics: {metrics['custom_objects']} objects, {metrics['apex_classes']} classes, {metrics['test_coverage_percent']}% coverage")
            except Exception as e:
                log_activity(f"⚠️ Could not generate metrics summary: {str(e)}")
        
        # Step 11: Generate QBR
        log_activity("📊 Step 11: Generating QBR report...")
        analyses[analysis_id]["steps"].append({"step": 11, "name": "Generating QBR", "status": "running"})
        orchestrator.step7_generate_qbr_draft()
        if check_cancelled(): return
        log_activity("✅ QBR report generated")
        analyses[analysis_id]["steps"][-1]["status"] = "completed"
        
        analyses[analysis_id]["status"] = "completed"
        analyses[analysis_id]["completed_at"] = dt.now().isoformat()
        log_activity("🎉 Analysis completed successfully!")
        
    except Exception as e:
        log_activity(f"❌ Error: {str(e)}")
        analyses[analysis_id]["status"] = "failed"
        analyses[analysis_id]["error"] = str(e)
        if analyses[analysis_id]["steps"]:
            analyses[analysis_id]["steps"][-1]["status"] = "failed"
            analyses[analysis_id]["steps"][-1]["error"] = str(e)
    
    current_analysis = None


class AnalysisStartRequest(BaseModel):
    quick_mode: bool = True  # Default to quick mode (skip cached)
    skip_steps: List[int] = []  # List of step numbers to skip (1-8)

@app.post("/api/analysis/start")
async def start_analysis(request: AnalysisStartRequest, background_tasks: BackgroundTasks):
    """Start new analysis - uses existing orchestrator."""
    analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    analyses[analysis_id] = {
        "id": analysis_id,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "steps": [],
        "quick_mode": request.quick_mode,
        "skip_steps": request.skip_steps  # Store which steps to skip
    }
    
    background_tasks.add_task(run_analysis_task, analysis_id)
    
    return {
        "analysis_id": analysis_id,
        "status": "queued",
        "message": "Analysis started in background",
        "quick_mode": request.quick_mode
    }


@app.get("/api/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get analysis status and progress."""
    if analysis_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analyses[analysis_id]


@app.post("/api/analysis/{analysis_id}/cancel")
async def cancel_analysis(analysis_id: str):
    """Cancel a running analysis."""
    global current_analysis
    
    if analysis_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses[analysis_id]
    
    if analysis["status"] != "running":
        raise HTTPException(status_code=400, detail="Analysis is not running")
    
    # Mark as cancelled
    analysis["status"] = "cancelled"
    analysis["completed_at"] = datetime.now().isoformat()
    
    # Clear current analysis if this was it
    if current_analysis == analysis_id:
        current_analysis = None
    
    return {
        "message": "Analysis cancelled successfully",
        "analysis_id": analysis_id
    }


@app.get("/api/analysis")
async def list_analyses():
    """List all analyses."""
    global current_analysis
    
    # Clean up stuck analyses (running for more than 30 minutes)
    from datetime import datetime, timedelta
    now = datetime.now()
    
    for analysis_id, analysis in list(analyses.items()):
        if analysis["status"] == "running":
            created = datetime.fromisoformat(analysis["created_at"])
            if now - created > timedelta(minutes=30):
                # Mark as failed due to timeout
                analysis["status"] = "failed"
                analysis["error"] = "Analysis timed out (exceeded 30 minutes)"
                analysis["completed_at"] = now.isoformat()
                if current_analysis == analysis_id:
                    current_analysis = None
    
    return {
        "current": current_analysis,
        "analyses": list(analyses.values())
    }


@app.post("/api/analysis/reset")
async def reset_analyses():
    """Reset all analysis state - useful for clearing stuck analyses."""
    global current_analysis, analyses
    
    # Mark all running analyses as cancelled
    from datetime import datetime
    for analysis_id, analysis in analyses.items():
        if analysis["status"] == "running":
            analysis["status"] = "cancelled"
            analysis["error"] = "Manually reset"
            analysis["completed_at"] = datetime.now().isoformat()
    
    current_analysis = None
    
    return {
        "message": "All analysis state cleared",
        "analyses_reset": len([a for a in analyses.values() if a["status"] == "cancelled"])
    }


# ==================== REPORTS ====================

@app.get("/api/reports")
async def list_reports():
    """List generated QBR reports."""
    reports = []
    qbr_dir = Config.QBR_OUTPUT
    
    if not qbr_dir.exists():
        return []
    
    for report in qbr_dir.glob("*.md"):
        reports.append({
            "filename": report.name,
            "created": datetime.fromtimestamp(report.stat().st_mtime).isoformat(),
            "size": report.stat().st_size,
            "path": str(report.relative_to(Config.PROJECT_ROOT))
        })
    
    return sorted(reports, key=lambda x: x['created'], reverse=True)


@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    """Get specific report content."""
    report_path = Config.QBR_OUTPUT / filename
    
    # Security: ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {
        "filename": filename,
        "content": content,
        "created": datetime.fromtimestamp(report_path.stat().st_mtime).isoformat()
    }


@app.get("/api/reports/{filename}/download")
async def download_report(filename: str):
    """Download report as file."""
    report_path = Config.QBR_OUTPUT / filename
    
    # Security: ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=report_path,
        filename=filename,
        media_type="text/markdown"
    )


# ==================== SYNTHESIS ====================

@app.get("/api/synthesis")
async def get_synthesis():
    """Get transcript synthesis."""
    synthesis_path = Config.SYNTHESIS / 'transcript-synthesis.md'
    
    if not synthesis_path.exists():
        return {
            "available": False,
            "message": "Synthesis not available. Run analysis first."
        }
    
    with open(synthesis_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {
        "available": True,
        "content": content,
        "created": datetime.fromtimestamp(synthesis_path.stat().st_mtime).isoformat()
    }


# ==================== STATS ====================

@app.get("/api/stats")
async def get_stats():
    """Get overall statistics."""
    stats = {
        "transcripts": {
            "raw": len(list(Config.TRANSCRIPTS_RAW.glob("*.pdf"))) if Config.TRANSCRIPTS_RAW.exists() else 0,
            "extracted": len(list(Config.TRANSCRIPTS_EXTRACTED.glob("*.json"))) if Config.TRANSCRIPTS_EXTRACTED.exists() else 0
        },
        "reports": len(list(Config.QBR_OUTPUT.glob("*.md"))) if Config.QBR_OUTPUT.exists() else 0,
        "analyses": len(analyses),
        "current_analysis": current_analysis
    }
    
    # Add Salesforce stats if available
    metrics_file = Config.SALESFORCE_RAW / 'metrics.json'
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            sf_metrics = json.load(f)
            stats["salesforce"] = {
                "custom_objects": sf_metrics.get('custom_objects', 0),
                "apex_classes": sf_metrics.get('apex_classes', 0),
                "test_coverage": sf_metrics.get('test_coverage_percent', 0)
            }
    
    return stats


# ==================== RAG / KNOWLEDGE BASE ====================

@app.post("/api/rag/index")
async def index_knowledge_base(background_tasks: BackgroundTasks):
    """Index all QBR data into vector database for semantic search."""
    from scripts.connectors.rag_manager import RAGManager
    
    def index_task():
        try:
            rag = RAGManager()
            rag.index_all_data(Config.PROJECT_ROOT)
        except Exception as e:
            print(f"Indexing error: {e}")
    
    background_tasks.add_task(index_task)
    
    return {
        "status": "started",
        "message": "Knowledge base indexing started in background. This may take 30-60 seconds."
    }


@app.get("/api/rag/status")
async def get_rag_status():
    """Get RAG system status."""
    from scripts.connectors.rag_manager import RAGManager
    
    try:
        rag = RAGManager()
        doc_count = rag.collection.count()
        
        return {
            "indexed": doc_count > 0,
            "document_count": doc_count,
            "status": "ready" if doc_count > 0 else "needs_indexing"
        }
    except Exception as e:
        return {
            "indexed": False,
            "document_count": 0,
            "status": "error",
            "error": str(e)
        }


# ==================== MEMORY / SAVED FACTS ====================

class SaveFactRequest(BaseModel):
    fact_content: str
    fact_title: Optional[str] = None  # Optional title/summary
    source_conversation_id: Optional[str] = None

@app.post("/api/memory/save")
async def save_fact(request: SaveFactRequest):
    """Save an AI response or fact to persistent memory."""
    from pathlib import Path
    import json
    from datetime import datetime
    
    # Ensure directory exists
    facts_dir = Config.PROJECT_ROOT / 'data-sources' / 'custom-context'
    facts_dir.mkdir(parents=True, exist_ok=True)
    
    facts_file = facts_dir / 'saved-facts.json'
    
    # Load existing facts
    facts = []
    if facts_file.exists():
        try:
            with open(facts_file, 'r', encoding='utf-8') as f:
                facts = json.load(f)
        except:
            facts = []
    
    # Create new fact entry
    new_fact = {
        "id": f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "title": request.fact_title or f"Fact saved on {datetime.now().strftime('%Y-%m-%d')}",
        "content": request.fact_content,
        "saved_at": datetime.now().isoformat(),
        "source_conversation_id": request.source_conversation_id
    }
    
    facts.append(new_fact)
    
    # Save to file
    with open(facts_file, 'w', encoding='utf-8') as f:
        json.dump(facts, f, indent=2, ensure_ascii=False)
    
    return {
        "success": True,
        "message": "Fact saved to memory",
        "fact_id": new_fact["id"],
        "total_facts": len(facts)
    }


@app.get("/api/memory/facts")
async def get_saved_facts():
    """Get all saved facts from persistent memory."""
    facts_file = Config.PROJECT_ROOT / 'data-sources' / 'custom-context' / 'saved-facts.json'
    
    if not facts_file.exists():
        return []
    
    try:
        with open(facts_file, 'r', encoding='utf-8') as f:
            facts = json.load(f)
        return facts
    except:
        return []


@app.delete("/api/memory/facts/{fact_id}")
async def delete_fact(fact_id: str):
    """Delete a saved fact from memory."""
    facts_file = Config.PROJECT_ROOT / 'data-sources' / 'custom-context' / 'saved-facts.json'
    
    if not facts_file.exists():
        raise HTTPException(status_code=404, detail="No facts found")
    
    try:
        with open(facts_file, 'r', encoding='utf-8') as f:
            facts = json.load(f)
        
        # Remove the fact
        original_length = len(facts)
        facts = [f for f in facts if f.get('id') != fact_id]
        
        if len(facts) == original_length:
            raise HTTPException(status_code=404, detail="Fact not found")
        
        # Save updated list
        with open(facts_file, 'w', encoding='utf-8') as f:
            json.dump(facts, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "message": "Fact deleted",
            "remaining_facts": len(facts)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AI CHAT ====================

class ChatRequest(BaseModel):
    question: str
    conversation_history: Optional[List[Dict[str, str]]] = []  # Optional conversation history
    use_general_knowledge: bool = False  # Allow AI to use training data if RAG returns nothing
    use_web_search: bool = False  # Enable Google Search grounding

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """AI chat with intelligent function calling - routes queries to appropriate tools."""
    from scripts.connectors.gemini_client import GeminiClient
    from scripts.connectors.rag_manager import RAGManager
    
    try:
        # Initialize
        rag = RAGManager()
        gemini = GeminiClient(Config.GEMINI_API_KEY)
        
        # Load system context (always available for every conversation)
        system_context = ""
        system_context_file = Config.PROJECT_ROOT / 'data-sources' / 'custom-context' / 'system-context.md'
        if system_context_file.exists():
            with open(system_context_file, 'r', encoding='utf-8') as f:
                system_context = f.read()
                system_context = f"""SYSTEM CONTEXT (Always available):
{system_context}

---

"""
        
        # DEBUG: Log what we're receiving
        print(f"\n=== CHAT REQUEST DEBUG ===")
        print(f"Question: {request.question}")
        print(f"History length: {len(request.conversation_history) if request.conversation_history else 0}")
        print(f"Use General Knowledge: {request.use_general_knowledge}")
        print(f"Use Web Search: {request.use_web_search}")
        if request.conversation_history:
            print(f"History: {json.dumps(request.conversation_history, indent=2)}")
        print(f"========================\n")
        
        # MODE 3: Web Search - Bypass RAG, use Google Search grounding
        if request.use_web_search:
            conversation_context = ""
            if request.conversation_history:
                conversation_context = "\n\nPrevious conversation:\n"
                for msg in request.conversation_history[-5:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    conversation_context += f"{role.upper()}: {content}\n"
            
            query_with_context = f"{system_context}{conversation_context}\n\nCurrent question: {request.question}" if conversation_context else f"{system_context}{request.question}"
            
            grounded_response = gemini.generate_with_grounding(query_with_context, max_tokens=65000)
            
            return {
                "answer": grounded_response["content"],
                "sources_used": ["Web Search"],
                "tools_used": ["web_search"],
                "web_sources": grounded_response.get("sources", []),
                "search_queries": grounded_response.get("search_queries", [])
            }
        
        # Build conversation context if history exists (used by both MODE 1 and MODE 2)
        conversation_context = ""
        if request.conversation_history:
            conversation_context = "\n\nPrevious conversation:\n"
            for msg in request.conversation_history[-5:]:  # Last 5 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_context += f"{role.upper()}: {content}\n"
            conversation_context += f"\nCurrent question: {request.question}\n"
        
        # MODE 2: General Knowledge - Try RAG search first, then fallback if nothing found
        if request.use_general_knowledge:
            # Force RAG search first
            context, sources = rag.get_context_for_query(request.question, max_tokens=100000)
            
            # If RAG found relevant data, use it
            if context and len(context.strip()) >= 50:
                query_to_use = request.question
                if conversation_context:
                    query_to_use = f"""{system_context}{conversation_context}

Use the conversation history above to resolve any pronouns or references.

Relevant context from internal data:
{context}

Current question: {request.question}"""
                else:
                    query_to_use = f"""{system_context}Based on the following context from our internal documents, answer the question.

Context:
{context}

Question: {request.question}"""
                
                answer = gemini.generate_text(query_to_use, max_tokens=65000)
                return {
                    "answer": answer,
                    "sources_used": sources,
                    "tools_used": ["search_rag"]
                }
            else:
                # No RAG results - fall back to general knowledge
                if conversation_context:
                    fallback_prompt = f"""{system_context}{conversation_context}

Answer the current question using your general knowledge.

Current question: {request.question}"""
                else:
                    fallback_prompt = f"{system_context}{request.question}"
                
                answer = gemini.generate_text(fallback_prompt, max_tokens=65000)
                return {
                    "answer": answer,
                    "sources_used": ["General Knowledge"],
                    "tools_used": []
                }
        
        # MODE 1 (default): RAG only - use function calling with RAG tools
        
        # Define available tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_stats",
                    "description": "Get statistics and counts about the indexed data (Jira issues, Confluence pages, Clockify hours, transcripts). Use this for questions like 'how many', 'total count', 'statistics'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_epic_list",
                    "description": "Get a complete list of all Jira epics with their value streams, status, and assignees. Use this for questions about epics or 'list all epics'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_rag",
                    "description": "Perform semantic search to find relevant context about a topic. Use this for questions requiring specific details, discussions, or context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        # Always include conversation context in the query if it exists
        query_to_use = request.question
        if conversation_context:
            # Include conversation context to help Gemini understand references
            query_to_use = f"""{system_context}{conversation_context}

When answering the current question, use the conversation history above to resolve any pronouns (he, she, they, it, that person, etc.) or references to previously mentioned topics.

Current question: {request.question}"""
        
        # Add explicit tool-calling instruction to the prompt
        tool_instruction = """
IMPORTANT: You MUST use the provided tools to answer this question. Do NOT answer based on general knowledge.
- For questions about Jira, Clockify, Confluence, Salesforce, or transcripts: Call the 'search_rag' tool
- For questions about counts or statistics: Call the 'get_stats' tool  
- For questions about epics: Call the 'get_epic_list' tool

Only after calling tools and reviewing the results should you formulate your answer.
"""
        
        query_with_instruction = f"{tool_instruction}\n\n{query_to_use}"
        
        # Use Gemini with native function calling support
        response = gemini.chat_with_tools(query_with_instruction, tools, max_tokens=65000)
        
        # Execute tool calls if any
        tool_results = []
        
        # If tools were called by Gemini
        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["name"]
                
                if tool_name == "get_stats":
                    stats = rag.get_stats(Config.PROJECT_ROOT)
                    tool_results.append(f"STATISTICS:\n{json.dumps(stats, indent=2)}")
                
                elif tool_name == "get_epic_list":
                    epics = rag.get_epic_list(Config.PROJECT_ROOT)
                    tool_results.append(f"EPIC LIST:\n{json.dumps(epics, indent=2)}")
                
                elif tool_name == "search_rag":
                    query = tool_call["arguments"].get("query", request.question)
                    context, sources = rag.get_context_for_query(query, max_tokens=100000)
                    tool_results.append(f"SEARCH RESULTS:\n{context}")
            
            # Now ask Gemini to synthesize final answer using tool results
            # Include conversation context if it exists
            context_prefix = ""
            if conversation_context:
                context_prefix = f"""{conversation_context}

Use the conversation history above to resolve any pronouns or references.

"""
            
            final_prompt = f"""{system_context}{context_prefix}Based on the tool results below, answer the user's question.

USER QUESTION: {request.question}

TOOL RESULTS:
{chr(10).join(tool_results)}

Provide a clear, accurate answer. For counts, state the exact numbers. For lists, be comprehensive but organized."""
            
            final_answer = gemini.generate_text(final_prompt, max_tokens=65000)
            
            return {
                "answer": final_answer,
                "sources_used": ["Direct Query"] if "get_stats" in [tc["name"] for tc in response["tool_calls"]] else ["Semantic Search"],
                "tools_used": [tc["name"] for tc in response["tool_calls"]]
            }
        
        # No tools called - check if General Knowledge mode is enabled or use default response
        if request.use_general_knowledge:
            # MODE 2: General Knowledge fallback - AI can use its training data
            if conversation_context:
                fallback_prompt = f"""{system_context}{conversation_context}

Answer the current question using your general knowledge. You do not have access to the specific internal documents mentioned, but you can provide helpful general information.

Current question: {request.question}"""
            else:
                fallback_prompt = f"{system_context}{request.question}"
            
            direct_answer = gemini.generate_text(fallback_prompt, max_tokens=65000)
            return {
                "answer": direct_answer,
                "sources_used": ["General Knowledge"],
                "tools_used": []
            }
        else:
            # MODE 1: No tools called and no general knowledge - limited response
            if conversation_context:
                # If we have conversation history, make sure the answer considers it
                context_aware_prompt = f"""{system_context}{conversation_context}

Answer the current question with full awareness of the conversation history. If the question refers to something mentioned earlier (like 'he', 'she', 'that', 'they'), resolve the reference using the conversation history.

Current question: {request.question}"""
                
                direct_answer = gemini.generate_text(context_aware_prompt, max_tokens=65000)
                return {
                    "answer": direct_answer,
                    "sources_used": [],
                    "tools_used": []
                }
            
            # No history and no tools - just return the response
            return {
                "answer": response.get("content", "I couldn't process that request."),
                "sources_used": [],
                "tools_used": []
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# ==================== PERSONA BUILDER ====================

# Background task storage for persona builds
persona_builds = {}

def run_persona_build_task(task_id: str, person_name: str, linkedin_url: Optional[str] = None):
    """Background task to build a persona"""
    from scripts.analyzers.persona_analyzer import PersonaAnalyzer
    from scripts.connectors.rag_manager import RAGManager
    
    persona_builds[task_id]["status"] = "building"
    persona_builds[task_id]["progress"] = 10
    
    try:
        analyzer = PersonaAnalyzer()
        result = analyzer.build_persona(person_name, linkedin_url=linkedin_url)
        
        persona_builds[task_id]["progress"] = 90
        persona_builds[task_id]["current_step"] = "🔄 Indexing persona for search..."
        
        # Automatically index the new persona into RAG
        try:
            rag = RAGManager()
            rag.index_all_data(Config.PROJECT_ROOT)
            persona_builds[task_id]["current_step"] = "✅ Complete & Indexed"
            persona_builds[task_id]["indexed"] = True
        except Exception as index_error:
            # Don't fail the whole task if indexing fails
            persona_builds[task_id]["current_step"] = "✅ Complete (indexing failed)"
            persona_builds[task_id]["indexed"] = False
            persona_builds[task_id]["index_error"] = str(index_error)
        
        persona_builds[task_id]["progress"] = 100
        persona_builds[task_id]["status"] = result["status"]
        persona_builds[task_id]["result"] = result
        persona_builds[task_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        persona_builds[task_id]["status"] = "failed"
        persona_builds[task_id]["error"] = str(e)
        persona_builds[task_id]["completed_at"] = datetime.now().isoformat()


@app.get("/api/personas/linkedin-urls")
async def get_linkedin_urls():
    """Get all saved LinkedIn URLs"""
    try:
        from scripts.connectors.linkedin_persistence import LinkedInPersistence
        persistence = LinkedInPersistence()
        return persistence.get_all_linkedin_urls()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting LinkedIn URLs: {str(e)}")


@app.get("/api/personas/participants")
async def list_persona_participants():
    """List all participants found in transcript analyses"""
    try:
        # Use subprocess to guarantee fresh Python execution with no caching
        import subprocess
        result = subprocess.run(
            [
                'python3', '-c',
                '''
import sys
sys.path.insert(0, "/Users/adrianboerstra/projects/maximQBR/scripts")
from analyzers.persona_analyzer import PersonaAnalyzer
import json
analyzer = PersonaAnalyzer()
participants = analyzer.extract_all_participants()
print(json.dumps(participants))
'''
            ],
            capture_output=True,
            text=True,
            cwd='/Users/adrianboerstra/projects/maximQBR'
        )
        
        if result.returncode != 0:
            raise Exception(f"Subprocess failed: {result.stderr}")
        
        import json
        participants = json.loads(result.stdout)
        
        # Check which participants already have personas
        personas_dir = Config.PROJECT_ROOT / 'data-sources' / 'personas'
        existing_personas = set()
        if personas_dir.exists():
            for persona_file in personas_dir.glob('*_persona.md'):
                # Extract name from filename
                name = persona_file.stem.replace('_persona', '').replace('-', ' ').title()
                existing_personas.add(name)
        
        # Format for frontend
        participant_list = []
        for name, data in participants.items():
            status = "ready"
            if data['transcript_count'] < 3:
                status = "insufficient_data"
            elif name in existing_personas:
                status = "built"
            
            participant_list.append({
                "name": name,
                "transcript_count": data['transcript_count'],
                "first_appearance": data['first_appearance'],
                "last_appearance": data['last_appearance'],
                "has_persona": name in existing_personas,
                "status": status
            })
        
        # Sort by transcript count (descending)
        participant_list.sort(key=lambda x: x['transcript_count'], reverse=True)
        
        return participant_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting participants: {str(e)}")


class PersonaBuildRequest(BaseModel):
    person_name: str
    linkedin_url: Optional[str] = None  # Optional LinkedIn profile URL for enrichment
    framework_selection: List[str] = ["kahneman", "lencioni", "martin"]  # Optional framework selection


@app.post("/api/personas/build")
async def build_persona(request: PersonaBuildRequest, background_tasks: BackgroundTasks):
    """Trigger persona generation (background task)"""
    person_name = request.person_name
    linkedin_url = request.linkedin_url
    task_id = f"persona_{person_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize task
    persona_builds[task_id] = {
        "task_id": task_id,
        "person_name": person_name,
        "linkedin_url": linkedin_url,
        "status": "queued",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "frameworks": request.framework_selection
    }
    
    # Start background task
    background_tasks.add_task(run_persona_build_task, task_id, person_name, linkedin_url)
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Persona build started for {person_name}",
        "estimated_time": "4-6 minutes"
    }


@app.get("/api/personas/build-status/{task_id}")
async def get_persona_build_status(task_id: str):
    """Check persona build status"""
    if task_id not in persona_builds:
        raise HTTPException(status_code=404, detail="Build task not found")
    
    return persona_builds[task_id]


@app.get("/api/personas/{person_name}")
async def get_persona(person_name: str):
    """Get built persona data"""
    # Find persona file
    personas_dir = Config.PROJECT_ROOT / 'data-sources' / 'personas'
    filename = person_name.lower().replace(' ', '-')
    persona_file = personas_dir / f'{filename}_persona.md'
    
    if not persona_file.exists():
        raise HTTPException(status_code=404, detail="Persona not found")
    
    with open(persona_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get metadata
    from scripts.analyzers.persona_analyzer import PersonaAnalyzer
    analyzer = PersonaAnalyzer()
    participants = analyzer.extract_all_participants()
    
    person_data = participants.get(person_name, {})
    
    return {
        "name": person_name,
        "built_date": datetime.fromtimestamp(persona_file.stat().st_mtime).isoformat(),
        "transcript_count": person_data.get('transcript_count', 0),
        "content": content,
        "download_url": f"/api/personas/{person_name}/download"
    }


@app.get("/api/personas/{person_name}/download")
async def download_persona(person_name: str):
    """Download persona document"""
    personas_dir = Config.PROJECT_ROOT / 'data-sources' / 'personas'
    filename = person_name.lower().replace(' ', '-')
    persona_file = personas_dir / f'{filename}_persona.md'
    
    if not persona_file.exists():
        raise HTTPException(status_code=404, detail="Persona not found")
    
    return FileResponse(
        path=persona_file,
        filename=f"{filename}_persona.md",
        media_type="text/markdown"
    )


# ==================== CUSTOM CONTEXT FILE UPLOAD ====================

@app.post("/api/custom-context/upload")
async def upload_custom_context(
    file: UploadFile = File(...),
    snapshot_date: Optional[str] = Form(None)
):
    """Upload custom context file (JSON, TXT, or MD) for RAG indexing.
    
    Args:
        file: The file to upload
        snapshot_date: Optional snapshot date (YYYY-MM-DD or YYYY-QX format) for portfolio files
    """
    # Check file extension
    allowed_extensions = ['.json', '.txt', '.md']
    file_ext = '.' + file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Only {', '.join(allowed_extensions)} files are allowed"
        )
    
    custom_dir = Config.PROJECT_ROOT / 'data-sources' / 'custom-context'
    custom_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = custom_dir / file.filename
    metadata_file = custom_dir / '.file_metadata.json'
    
    # Read and save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Load existing metadata
    file_metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                file_metadata = json.load(f)
        except:
            file_metadata = {}
    
    # Check if this is a portfolio file and handle snapshot cleanup
    if file_ext == '.json':
        try:
            from scripts.connectors.rag_manager import RAGManager
            
            # Parse the JSON to check if it's a portfolio
            file_data = json.loads(content.decode('utf-8'))
            rag = RAGManager()
            
            if rag.is_portfolio_file(file_data):
                # Use manual snapshot_date if provided, otherwise extract from filename
                detected_date = snapshot_date or rag.extract_snapshot_date(file.filename)
                
                if detected_date:
                    # Save metadata
                    file_metadata[file.filename] = {
                        "is_portfolio": True,
                        "snapshot_date": detected_date,
                        "date_source": "manual" if snapshot_date else "filename",
                        "uploaded_at": datetime.now().isoformat()
                    }
                    
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(file_metadata, f, indent=2)
                    
                    # Delete existing snapshot with same date before re-indexing
                    rag.delete_portfolio_snapshot(detected_date)
                    
                    return {
                        "filename": file.filename,
                        "status": "uploaded",
                        "size": len(content),
                        "path": str(file_path.relative_to(Config.PROJECT_ROOT)),
                        "message": f"Portfolio snapshot ({detected_date}) uploaded. Old snapshot replaced. Indexing...",
                        "snapshot_date": detected_date,
                        "is_portfolio": True,
                        "date_source": "manual" if snapshot_date else "filename"
                    }
        except Exception as e:
            # If snapshot detection/cleanup fails, continue with normal upload
            print(f"Error handling portfolio snapshot: {e}")
    
    return {
        "filename": file.filename,
        "status": "uploaded",
        "size": len(content),
        "path": str(file_path.relative_to(Config.PROJECT_ROOT)),
        "message": "File uploaded. Click 'Index Knowledge Base' to make it searchable."
    }


@app.get("/api/custom-context/files")
async def list_custom_context_files():
    """List uploaded custom context files with portfolio metadata and index status."""
    from scripts.connectors.rag_manager import RAGManager
    
    custom_dir = Config.PROJECT_ROOT / 'data-sources' / 'custom-context'
    
    if not custom_dir.exists():
        return []
    
    # Load metadata file
    metadata_file = custom_dir / '.file_metadata.json'
    file_metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                file_metadata = json.load(f)
        except:
            file_metadata = {}
    
    rag = RAGManager()
    files = []
    
    for file_path in custom_dir.glob('*'):
        # Skip the metadata file itself
        if file_path.name == '.file_metadata.json' or not file_path.is_file():
            continue
            
        file_info = {
            "filename": file_path.name,
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "type": file_path.suffix[1:] if file_path.suffix else "unknown",
            "index_status": "indexed"  # Default to indexed (optimistic)
        }
        
        # Check metadata file first
        if file_path.name in file_metadata:
            meta = file_metadata[file_path.name]
            if meta.get("is_portfolio"):
                file_info["is_portfolio"] = True
                file_info["snapshot_date"] = meta.get("snapshot_date")
            # Get index status from metadata
            if "index_status" in meta:
                file_info["index_status"] = meta["index_status"]
        # Fallback to detection for old files
        elif file_path.suffix.lower() == '.json':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                if rag.is_portfolio_file(file_data):
                    file_info["is_portfolio"] = True
                    # Try to extract snapshot date from filename
                    snapshot_date = rag.extract_snapshot_date(file_path.name)
                    if snapshot_date:
                        file_info["snapshot_date"] = snapshot_date
            except:
                pass
        
        files.append(file_info)
    
    return sorted(files, key=lambda x: x['modified'], reverse=True)


@app.delete("/api/custom-context/files/{filename}")
async def delete_custom_context_file(filename: str):
    """Delete a custom context file and its metadata"""
    from pathlib import Path
    import os
    
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    custom_dir = Config.PROJECT_ROOT / 'data-sources' / 'custom-context'
    file_path = custom_dir / filename
    metadata_file = custom_dir / '.file_metadata.json'
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    
    try:
        # Delete the file
        os.remove(file_path)
        
        # Clean up metadata
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    file_metadata = json.load(f)
                
                # Remove this file's metadata
                if filename in file_metadata:
                    del file_metadata[filename]
                    
                    # Save updated metadata
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(file_metadata, f, indent=2)
            except:
                pass  # Non-critical if metadata cleanup fails
        
        return {
            "success": True,
            "message": f"{filename} deleted successfully",
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


# ==================== CONVERSATIONS (Database-backed) ====================

@app.get("/api/conversations")
async def list_conversations(db: Session = Depends(get_db)):
    """List all conversations from database."""
    try:
        conversations = db.query(DBConversation).order_by(DBConversation.updated_at.desc()).all()
        
        return [{
            "id": conv.id,
            "title": conv.title,
            "createdAt": conv.created_at.isoformat(),
            "updatedAt": conv.updated_at.isoformat(),
            "messageCount": len(conv.messages)
        } for conv in conversations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get a single conversation with all messages."""
    try:
        from sqlalchemy import text
        from datetime import datetime, timezone
        
        # Use raw SQL to bypass ORM completely
        conv_result = db.execute(
            text("SELECT id, title, created_at, updated_at FROM conversations WHERE id = :cid"),
            {"cid": conversation_id}
        ).fetchone()
        
        if not conv_result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Fetch messages via raw SQL
        msg_rows = db.execute(
            text("SELECT id, role, content, timestamp, sources FROM messages WHERE conversation_id = :cid"),
            {"cid": conversation_id}
        ).fetchall()
        
        # Process messages manually
        messages_list = []
        for row in msg_rows:
            # row is a tuple: (id, role, content, timestamp, sources)
            ts_raw = row[3]
            
            # Parse timestamp string to datetime with robust error handling
            try:
                if isinstance(ts_raw, str):
                    # Handle various formats
                    ts_str = ts_raw.replace("Z", "+00:00")
                    try:
                        ts = datetime.fromisoformat(ts_str)
                    except:
                        # Fallback: try without timezone
                        ts = datetime.fromisoformat(ts_raw.replace("Z", ""))
                        ts = ts.replace(tzinfo=timezone.utc)
                else:
                    # Already datetime
                    ts = ts_raw
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
            except Exception as e:
                # If timestamp is completely invalid, use current time
                print(f"Warning: Invalid timestamp for message {row[0]}: {ts_raw}. Using current time. Error: {e}")
                ts = datetime.now(timezone.utc)
            
            messages_list.append({
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "timestamp": ts.isoformat(),
                "timestamp_sort": ts.timestamp(),
                "sources": json.loads(row[4]) if row[4] else None
            })
        
        # Sort by Unix timestamp
        messages_list.sort(key=lambda m: m["timestamp_sort"])
        
        # Remove sorting key
        for msg in messages_list:
            del msg["timestamp_sort"]
        
        # Parse conversation timestamps
        created = conv_result[2]
        updated = conv_result[3]
        
        if isinstance(created, str):
            created = datetime.fromisoformat(created.replace("Z", "+00:00"))
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        
        return {
            "id": conv_result[0],
            "title": conv_result[1],
            "createdAt": created if isinstance(created, str) else created.isoformat(),
            "updatedAt": updated if isinstance(updated, str) else updated.isoformat(),
            "messages": messages_list
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/conversations")
async def create_conversation(conversation: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation."""
    try:
        # Check if conversation already exists
        existing = db.query(DBConversation).filter(DBConversation.id == conversation.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Conversation already exists")
        
        # Create conversation
        db_conversation = DBConversation(
            id=conversation.id,
            title=conversation.title,
            created_at=datetime.fromisoformat(conversation.createdAt),
            updated_at=datetime.fromisoformat(conversation.updatedAt)
        )
        
        # Add messages
        for msg in conversation.messages:
            db_message = DBMessage(
                id=msg.id,
                conversation_id=conversation.id,
                role=msg.role,
                content=msg.content,
                timestamp=datetime.fromisoformat(msg.timestamp),
                sources=json.dumps(msg.sources) if msg.sources else None
            )
            db_conversation.messages.append(db_message)
        
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        
        return {
            "success": True,
            "message": "Conversation created",
            "conversation_id": db_conversation.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.put("/api/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str, 
    update_data: ConversationUpdate, 
    db: Session = Depends(get_db)
):
    """Update conversation title or other metadata."""
    try:
        conversation = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if update_data.title is not None:
            conversation.title = update_data.title
        
        if update_data.updatedAt is not None:
            conversation.updated_at = datetime.fromisoformat(update_data.updatedAt)
        else:
            conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(conversation)
        
        return {
            "success": True,
            "message": "Conversation updated",
            "conversation_id": conversation.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and all its messages."""
    try:
        conversation = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        db.delete(conversation)
        db.commit()
        
        return {
            "success": True,
            "message": "Conversation deleted",
            "conversation_id": conversation_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/conversations/{conversation_id}/messages")
async def add_message(conversation_id: str, message: MessageCreate, db: Session = Depends(get_db)):
    """Add a message to a conversation."""
    try:
        from sqlalchemy import text
        from datetime import timezone
        
        conversation = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Parse and validate timestamp, fall back to current time if invalid
        try:
            msg_timestamp = datetime.fromisoformat(message.timestamp.replace("Z", "+00:00"))
            # Ensure it has timezone info
            if msg_timestamp.tzinfo is None:
                msg_timestamp = msg_timestamp.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            # Invalid timestamp - use current time
            msg_timestamp = datetime.now(timezone.utc)
        
        db_message = DBMessage(
            id=message.id,
            conversation_id=conversation_id,
            role=message.role,
            content=message.content,
            timestamp=msg_timestamp,
            sources=json.dumps(message.sources) if message.sources else None
        )
        
        db.add(db_message)
        
        # Update conversation timestamp using ORM (not raw SQL) to ensure proper type conversion
        conversation.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Message added",
            "message_id": db_message.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.delete("/api/conversations/{conversation_id}/messages/{message_id}")
async def delete_message(conversation_id: str, message_id: str, db: Session = Depends(get_db)):
    """Delete a message from a conversation."""
    try:
        message = db.query(DBMessage).filter(
            DBMessage.id == message_id,
            DBMessage.conversation_id == conversation_id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        db.delete(message)
        
        # Update conversation timestamp
        conversation = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Message deleted",
            "message_id": message_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/conversations/migrate")
async def migrate_conversations(request: MigrateConversationsRequest, db: Session = Depends(get_db)):
    """Migrate conversations from localStorage to database. Safely handles duplicates."""
    try:
        migrated_count = 0
        skipped_count = 0
        errors = []
        
        for conv_data in request.conversations:
            try:
                # Check if conversation already exists
                existing = db.query(DBConversation).filter(DBConversation.id == conv_data.id).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new conversation
                db_conversation = DBConversation(
                    id=conv_data.id,
                    title=conv_data.title,
                    created_at=datetime.fromisoformat(conv_data.createdAt),
                    updated_at=datetime.fromisoformat(conv_data.updatedAt)
                )
                
                # Add messages with globally unique IDs
                for msg in conv_data.messages:
                    # Generate globally unique message ID by prefixing with conversation ID
                    # This prevents collisions when different conversations have messages with same ID
                    global_message_id = f"{conv_data.id}_{msg.id}"
                    
                    db_message = DBMessage(
                        id=global_message_id,
                        conversation_id=conv_data.id,
                        role=msg.role,
                        content=msg.content,
                        timestamp=datetime.fromisoformat(msg.timestamp),
                        sources=json.dumps(msg.sources) if msg.sources else None
                    )
                    db_conversation.messages.append(db_message)
                
                db.add(db_conversation)
                migrated_count += 1
                
            except Exception as e:
                errors.append({
                    "conversation_id": conv_data.id,
                    "error": str(e)
                })
        
        # Commit all migrations
        db.commit()
        
        return {
            "success": True,
            "message": f"Migration complete: {migrated_count} migrated, {skipped_count} skipped (already exist)",
            "migrated_count": migrated_count,
            "skipped_count": skipped_count,
            "error_count": len(errors),
            "errors": errors if errors else None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")


# ==================== CROSS-VALIDATION ====================

@app.get("/api/analysis/cross-validation")
async def get_cross_validation():
    """Get cross-validation results and data quality metrics (mock data for now)."""
    # TODO: Replace with actual cross-validation from scripts/analyzers/cross_validator.py
    return {
        "timestamp": datetime.now().isoformat(),
        "data_quality": {
            "overall_score": 87,
            "completeness": 92,
            "consistency": 85,
            "accuracy": 88,
            "timeliness": 83
        },
        "summary": {
            "total_checks": 12,
            "passed": 8,
            "warnings": 3,
            "failed": 1
        },
        "validation_results": [
            {
                "source_a": "Jira",
                "source_b": "Clockify",
                "metric": "Project Hours Alignment",
                "value_a": 240,
                "value_b": 238,
                "difference": -0.8,
                "status": "match",
                "details": "Jira estimates and Clockify tracked hours are within acceptable variance (<5%)"
            },
            {
                "source_a": "Transcripts",
                "source_b": "Jira",
                "metric": "Mentioned Issues Coverage",
                "value_a": 15,
                "value_b": 12,
                "difference": 20,
                "status": "warning",
                "details": "3 issues discussed in meetings were not found in Jira. May indicate tracking gaps."
            },
            {
                "source_a": "Salesforce",
                "source_b": "Clockify",
                "metric": "Deployment Count vs Hours",
                "value_a": 8,
                "value_b": 320,
                "difference": 0,
                "status": "match",
                "details": "8 deployments with 320 hours tracked aligns with expected deployment effort"
            },
            {
                "source_a": "Jira",
                "source_b": "Transcripts",
                "metric": "Blocker Issues Mentioned",
                "value_a": 5,
                "value_b": 3,
                "difference": 40,
                "status": "warning",
                "details": "2 blocker issues in Jira were not discussed in recent meetings"
            },
            {
                "source_a": "Clockify",
                "source_b": "Jira",
                "metric": "Sprint Capacity Utilization",
                "value_a": "95%",
                "value_b": "92%",
                "difference": 3,
                "status": "match",
                "details": "Team capacity utilization is consistent across both systems"
            },
            {
                "source_a": "Salesforce",
                "source_b": "Jira",
                "metric": "Test Coverage vs Quality Issues",
                "value_a": 78,
                "value_b": 12,
                "difference": 0,
                "status": "match",
                "details": "78% test coverage with 12 quality-related Jira issues is within normal range"
            },
            {
                "source_a": "Transcripts",
                "source_b": "Clockify",
                "metric": "Meeting Time vs Client Billable Hours",
                "value_a": 24,
                "value_b": 240,
                "difference": 10,
                "status": "match",
                "details": "24 hours of meetings represents 10% of total tracked time - healthy ratio"
            },
            {
                "source_a": "Jira",
                "source_b": "Salesforce",
                "metric": "Integration Issues vs Deployment Frequency",
                "value_a": 7,
                "value_b": 8,
                "difference": -12.5,
                "status": "warning",
                "details": "7 integration issues with 8 deployments suggests opportunity for better pre-deployment testing"
            },
            {
                "source_a": "Transcripts",
                "source_b": "Salesforce",
                "metric": "Technical Debt Mentions vs Code Quality",
                "value_a": 18,
                "value_b": 78,
                "difference": 0,
                "status": "match",
                "details": "Technical debt discussions align with current test coverage of 78%"
            },
            {
                "source_a": "Clockify",
                "source_b": "Salesforce",
                "metric": "Development Hours vs Apex Classes",
                "value_a": 180,
                "value_b": 45,
                "difference": 0,
                "status": "match",
                "details": "4 hours per Apex class is reasonable for enterprise-grade development"
            },
            {
                "source_a": "Jira",
                "source_b": "Transcripts",
                "metric": "Priority Alignment",
                "value_a": "High",
                "value_b": "Medium",
                "difference": 100,
                "status": "mismatch",
                "details": "Top priority items in Jira don't match discussion focus in meetings. Alignment needed."
            },
            {
                "source_a": "Clockify",
                "source_b": "Transcripts",
                "metric": "Support Hours vs Customer Concerns",
                "value_a": 48,
                "value_b": 6,
                "difference": 0,
                "status": "match",
                "details": "48 support hours with 6 customer concerns mentioned shows proactive support approach"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
