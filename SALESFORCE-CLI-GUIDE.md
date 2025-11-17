# Salesforce CLI OAuth Integration Guide

## Overview

The QBR system now supports Salesforce CLI OAuth login, eliminating the need to manage security tokens or store passwords in environment files.

## Quick Start

### 1. Login to Salesforce via CLI

**For Production Org:**
```bash
sf org login web
```

**For Sandbox Org:**
```bash
sf org login web --instance-url https://test.salesforce.com
```

This will:
- Open your browser
- Let you login with normal Salesforce credentials
- Store OAuth tokens securely via SF CLI
- No security token needed!

### 2. Verify Login

Check which orgs you're logged into:
```bash
sf org list
```

### 3. View in Dashboard

Visit http://localhost:5173 and check the Health Status panel. You should see:

```
🟢 Salesforce Production - CLI OAuth - Org: your.email@company.com
```

## Selecting a Specific Org

If you have multiple orgs logged in, you can specify which to use:

### Option 1: Environment Variable

Edit your `.env` file:
```bash
# Use specific org by alias or username
SF_PRODUCTION_ORG=my-prod-alias
SF_SANDBOX_ORG=my-sandbox-alias
```

### Option 2: Set Default Org

Use SF CLI to set a default:
```bash
# Set default production org
sf config set target-org my-prod-alias

# Or for sandbox
sf config set target-org my-sandbox-alias
```

### Option 3: Create an Alias

Make org selection easier with aliases:
```bash
# List current orgs
sf org list

# Create alias for an org
sf alias set my-prod=your.email@company.com
sf alias set my-sandbox=your.email@company.com.sandbox

# Then in .env:
SF_PRODUCTION_ORG=my-prod
SF_SANDBOX_ORG=my-sandbox
```

## How It Works

The system uses this priority order:

1. **Specific org from env var** - `SF_PRODUCTION_ORG` or `SF_SANDBOX_ORG`
2. **First matching CLI org** - First production/sandbox org found in `sf org list`
3. **Username/password fallback** - Traditional credentials from .env (if CLI not available)

## Org Information Display

The Health Status dashboard shows:
- **Connection method**: "CLI OAuth" or "Username/Password"
- **Org name**: The username/email of the connected org
- **Status**: 🟢 Green when connected, 🟡 Yellow when not configured

Example:
```
🟢 Salesforce Production
   CLI OAuth - Org: john.doe@maxim.com
```

## Multiple Production Orgs

If you work with multiple production orgs (e.g., different companies):

1. **Login to both:**
```bash
sf org login web --alias company-a
sf org login web --alias company-b
```

2. **Specify which to use:**
```env
SF_PRODUCTION_ORG=company-a
```

3. **Switch between them:**
```bash
# Edit .env and change SF_PRODUCTION_ORG
# Restart backend
```

## Troubleshooting

### "No Salesforce connection available"

**Check if you're logged in:**
```bash
sf org list
```

**No orgs listed?** Login:
```bash
sf org login web
```

### "Wrong org is being used"

**Set specific org in .env:**
```env
SF_PRODUCTION_ORG=your-desired-org-alias
```

**Restart backend:**
```bash
lsof -ti:8000 | xargs kill -9
cd /Users/adrianboerstra/projects/maximQBR
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### "See which org will be used"

**Check org details:**
```bash
sf org display --target-org your-alias
```

**Or test the connection:**
```bash
cd /Users/adrianboerstra/projects/maximQBR
python -c "
from scripts.connectors.salesforce_client import SalesforceClient
client = SalesforceClient(is_sandbox=False)
print(f'Connected to: {client.org_name}')
print(f'Method: {client.connection_method}')
print(f'Org ID: {client.org_id}')
"
```

## Benefits of CLI OAuth

✅ No security tokens to manage  
✅ No passwords in .env files  
✅ Tokens refresh automatically  
✅ Same login method you use for development  
✅ More secure (OAuth vs password)  
✅ Works with MFA/2FA  
✅ Easy to switch between orgs  

## Fallback to Credentials

The system still supports traditional username/password/token authentication as a fallback.

If you prefer or SF CLI is not available, you can still use:
```env
SF_PRODUCTION_USERNAME=your@email.com
SF_PRODUCTION_PASSWORD=YourPassword
SF_PRODUCTION_TOKEN=YourSecurityToken
```

The system will automatically detect and use whichever method is available.

## Example Workflows

### Workflow 1: Single Production Org

```bash
# One-time setup
sf org login web

# That's it! Dashboard will show connection
```

### Workflow 2: Production + Sandbox

```bash
# Login to both
sf org login web --alias prod
sf org login web --alias sandbox --instance-url https://test.salesforce.com

# Optional: Set in .env for clarity
echo "SF_PRODUCTION_ORG=prod" >> .env
echo "SF_SANDBOX_ORG=sandbox" >> .env

# Restart backend
```

### Workflow 3: Multiple Companies

```bash
# Login to all orgs
sf org login web --alias company-a-prod
sf org login web --alias company-b-prod

# Switch between them via .env
# For Company A:
SF_PRODUCTION_ORG=company-a-prod

# For Company B:
SF_PRODUCTION_ORG=company-b-prod

# Restart backend after changing
```

## Security Notes

- OAuth tokens are stored securely by Salesforce CLI
- Tokens are NOT in your .env file
- Tokens automatically refresh when expired
- You can revoke access anytime from Salesforce Setup → Connected Apps
- Each org login is independent and secure

## Support

For issues with:
- **SF CLI**: See Salesforce CLI documentation
- **System integration**: Check logs in `api.log`
- **Connection errors**: Run health check at http://localhost:8000/api/health/detailed
