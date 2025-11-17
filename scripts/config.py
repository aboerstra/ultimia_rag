"""Configuration management for QBR automation."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config:
    """Central configuration for all API connections and settings."""
    
    # OpenRouter/Claude
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
    CLAUDE_MODEL = 'anthropic/claude-3.5-sonnet'
    
    # Google Gemini (Alternative LLM with native function calling)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Jira
    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_EMAIL = os.getenv('JIRA_EMAIL')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
    JIRA_PROJECT = os.getenv('JIRA_PROJECT')  # Specific project key to analyze
    JIRA_SPACE = os.getenv('JIRA_SPACE')  # Confluence space key
    
    # Confluence
    CONFLUENCE_URL = os.getenv('CONFLUENCE_URL')
    CONFLUENCE_EMAIL = os.getenv('CONFLUENCE_EMAIL')
    CONFLUENCE_API_TOKEN = os.getenv('CONFLUENCE_API_TOKEN')
    
    # Clockify
    CLOCKIFY_API_KEY = os.getenv('CLOCKIFY_API_KEY')
    CLOCKIFY_BASE_URL = 'https://api.clockify.me/api/v1'
    CLOCKIFY_CLIENT = os.getenv('CLOCKIFY_CLIENT')  # Specific client to analyze
    CLOCKIFY_PROJECTS = os.getenv('CLOCKIFY_PROJECTS')  # Comma-separated project IDs
    
    # Global client code filter (applies to Jira, Confluence, Clockify)
    CLIENT_CODE = os.getenv('CLIENT_CODE')
    
    # Salesforce
    # Option 1: Specify CLI org alias/username
    SF_PRODUCTION_ORG = os.getenv('SF_PRODUCTION_ORG')  # e.g., "mycompany-prod" or alias
    SF_SANDBOX_ORG = os.getenv('SF_SANDBOX_ORG')  # e.g., "mycompany-sandbox" or alias
    
    # Option 2: Manual credentials (fallback)
    SF_PRODUCTION_USERNAME = os.getenv('SF_PRODUCTION_USERNAME')
    SF_PRODUCTION_PASSWORD = os.getenv('SF_PRODUCTION_PASSWORD')
    SF_PRODUCTION_TOKEN = os.getenv('SF_PRODUCTION_TOKEN')
    
    SF_SANDBOX_USERNAME = os.getenv('SF_SANDBOX_USERNAME')
    SF_SANDBOX_PASSWORD = os.getenv('SF_SANDBOX_PASSWORD')
    SF_SANDBOX_TOKEN = os.getenv('SF_SANDBOX_TOKEN')
    
    # Project settings
    DATE_RANGE_MONTHS = int(os.getenv('DATE_RANGE_MONTHS', 6))
    PROJECT_ROOT = Path(__file__).parent.parent
    
    @classmethod
    def reload(cls):
        """Reload environment variables from .env file."""
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path, override=True)
        
        # Reload all configuration values
        cls.OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
        
        cls.JIRA_URL = os.getenv('JIRA_URL')
        cls.JIRA_EMAIL = os.getenv('JIRA_EMAIL')
        cls.JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
        cls.JIRA_PROJECT = os.getenv('JIRA_PROJECT')
        cls.JIRA_SPACE = os.getenv('JIRA_SPACE')
        
        cls.CONFLUENCE_URL = os.getenv('CONFLUENCE_URL')
        cls.CONFLUENCE_EMAIL = os.getenv('CONFLUENCE_EMAIL')
        cls.CONFLUENCE_API_TOKEN = os.getenv('CONFLUENCE_API_TOKEN')
        
        cls.CLOCKIFY_API_KEY = os.getenv('CLOCKIFY_API_KEY')
        cls.CLOCKIFY_CLIENT = os.getenv('CLOCKIFY_CLIENT')
        cls.CLOCKIFY_PROJECTS = os.getenv('CLOCKIFY_PROJECTS')
        
        cls.CLIENT_CODE = os.getenv('CLIENT_CODE')
        
        cls.SF_PRODUCTION_ORG = os.getenv('SF_PRODUCTION_ORG')
        cls.SF_SANDBOX_ORG = os.getenv('SF_SANDBOX_ORG')
        cls.SF_PRODUCTION_USERNAME = os.getenv('SF_PRODUCTION_USERNAME')
        cls.SF_PRODUCTION_PASSWORD = os.getenv('SF_PRODUCTION_PASSWORD')
        cls.SF_PRODUCTION_TOKEN = os.getenv('SF_PRODUCTION_TOKEN')
        cls.SF_SANDBOX_USERNAME = os.getenv('SF_SANDBOX_USERNAME')
        cls.SF_SANDBOX_PASSWORD = os.getenv('SF_SANDBOX_PASSWORD')
        cls.SF_SANDBOX_TOKEN = os.getenv('SF_SANDBOX_TOKEN')
        
        cls.DATE_RANGE_MONTHS = int(os.getenv('DATE_RANGE_MONTHS', 6))
    
    # Paths
    TRANSCRIPTS_RAW = PROJECT_ROOT / 'data-sources' / 'transcripts' / 'raw'
    TRANSCRIPTS_EXTRACTED = PROJECT_ROOT / 'data-sources' / 'transcripts' / 'extracted'
    JIRA_RAW = PROJECT_ROOT / 'data-sources' / 'jira' / 'raw'
    CONFLUENCE_RAW = PROJECT_ROOT / 'data-sources' / 'confluence' / 'raw'
    CLOCKIFY_RAW = PROJECT_ROOT / 'data-sources' / 'clockify' / 'raw'
    SALESFORCE_RAW = PROJECT_ROOT / 'data-sources' / 'salesforce' / 'raw'
    SYNTHESIS = PROJECT_ROOT / 'data-sources' / 'synthesis'
    QBR_OUTPUT = PROJECT_ROOT / 'qbr-output'
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        missing = []
        
        if not cls.OPENROUTER_API_KEY:
            missing.append('OPENROUTER_API_KEY')
        if not cls.JIRA_URL or not cls.JIRA_API_TOKEN:
            missing.append('JIRA credentials')
        if not cls.CLOCKIFY_API_KEY:
            missing.append('CLOCKIFY_API_KEY')
            
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def _check_sf_cli_auth(cls, is_sandbox=False):
        """Check if Salesforce CLI has an authorized org."""
        import subprocess
        import json
        
        try:
            result = subprocess.run(
                ['sf', 'org', 'list', '--json'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                orgs = data.get('result', {}).get('nonScratchOrgs', [])
                
                for org in orgs:
                    if org.get('isSandbox', False) == is_sandbox:
                        return True
            
            return False
        except:
            return False
    
    @classmethod
    def get_health_status(cls):
        """Get health status of each service without raising errors."""
        # Check SF CLI auth
        sf_prod_cli = cls._check_sf_cli_auth(is_sandbox=False)
        sf_sandbox_cli = cls._check_sf_cli_auth(is_sandbox=True)
        
        return {
            "llm": {
                "configured": bool(cls.OPENROUTER_API_KEY),
                "name": "OpenRouter/Claude"
            },
            "jira": {
                "configured": bool(cls.JIRA_URL and cls.JIRA_API_TOKEN),
                "name": "Jira"
            },
            "confluence": {
                "configured": bool(cls.CONFLUENCE_URL and cls.CONFLUENCE_API_TOKEN),
                "name": "Confluence"
            },
            "clockify": {
                "configured": bool(cls.CLOCKIFY_API_KEY),
                "name": "Clockify"
            },
            "salesforce_prod": {
                "configured": bool(
                    sf_prod_cli or 
                    (cls.SF_PRODUCTION_USERNAME and cls.SF_PRODUCTION_PASSWORD)
                ),
                "name": "Salesforce Production"
            },
            "salesforce_sandbox": {
                "configured": bool(
                    sf_sandbox_cli or
                    (cls.SF_SANDBOX_USERNAME and cls.SF_SANDBOX_PASSWORD)
                ),
                "name": "Salesforce Sandbox"
            }
        }

# Validation is now optional - only validate when running analysis
