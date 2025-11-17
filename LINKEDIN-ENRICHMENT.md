# LinkedIn Profile Enrichment for Persona Builder

## Overview

The Persona Builder now supports optional LinkedIn profile enrichment to improve persona accuracy by providing additional context about executives' actual roles, backgrounds, and expertise.

## Problem Solved

**Before:** The AI analyzer only had access to meeting transcripts, which could lead to misidentification of roles. For example:
- A CEO discussing technical projects might be incorrectly labeled as a "technology-oriented leader"
- Business executives might be characterized using technical examples rather than business frameworks
- The AI would infer roles solely from conversation topics, missing broader context

**After:** With LinkedIn profile data, the AI receives structured context about:
- Current role and title
- Company and industry
- Professional background and experience
- Education
- Areas of expertise

This allows the AI to correctly interpret transcript behavior through the appropriate lens (business executive vs. technical leader, etc.).

## How It Works

### 1. User Interface

In the Persona Builder, each participant row now includes an optional "LinkedIn (Optional)" input field where users can paste a LinkedIn profile URL.

**Example URLs:**
- `https://www.linkedin.com/in/username`
- `linkedin.com/in/username`

### 2. Profile Fetching

When a LinkedIn URL is provided and the user clicks "Build Persona" or "Rebuild", the system:

1. Fetches the public LinkedIn profile data using `scripts/connectors/linkedin_scraper.py`
2. Extracts structured information:
   - `title`: Current job title
   - `company`: Current company name
   - `about`: Profile summary/about section
   - `experience`: Work history
   - `education`: Educational background

### 3. Context Enhancement

The LinkedIn data is formatted into a "PUBLIC PROFILE CONTEXT" section and included in all 6 analysis passes:

```python
PUBLIC PROFILE CONTEXT:
- Current Role: President & CEO at [Company Name]
- Industry: Financial Services Technology
- Background: 15 years in private equity, MBA from Wharton
- Focus: Business transformation, ROI optimization, scaling

CRITICAL: This is a BUSINESS EXECUTIVE, not technical engineer.
Interpret "technical" discussions as business outcomes, not code.
```

### 4. AI Analysis Adjustment

With this context, the AI:
- Interprets discussions about "systems" as business process optimization, not technical infrastructure
- Uses business-focused examples (ROI, stakeholder management) instead of technical ones (API integration, system uptime)
- Applies appropriate frameworks based on actual role (executive decision-making vs. technical problem-solving)
- Generates more accurate working templates and communication strategies

## Implementation Details

### Backend Components

**1. LinkedIn Scraper** (`scripts/connectors/linkedin_scraper.py`)
```python
def fetch_linkedin_profile(url: str) -> dict:
    """
    Fetches public LinkedIn profile data
    Returns: {
        'title': str,
        'company': str,
        'about': str,
        'experience': str,
        'education': str
    }
    """
```

**2. Persona Analyzer** (`scripts/analyzers/persona_analyzer.py`)
- Updated `__init__` to import LinkedIn scraper
- Modified `build_persona()` to accept optional `linkedin_url` parameter
- Enhanced all 6 pass methods to include `profile_context` parameter
- Formatted profile data into analysis prompts

**3. API Endpoint** (`api/main.py`)
```python
@app.post("/api/personas/build")
async def build_persona(request: dict):
    person_name = request.get("person_name")
    linkedin_url = request.get("linkedin_url")  # NEW: Optional parameter
    # ... rest of implementation
```

### Frontend Components

**1. PersonaBuilder Component** (`frontend/src/components/PersonaBuilder.tsx`)
- Added `linkedinUrls` state to track URL inputs per participant
- Created `handleLinkedinUrlChange()` to manage URL updates
- Modified `buildPersonaMutation` to include `linkedin_url` in POST request
- Added LinkedIn input field to each participant row

**2. Styling** (`frontend/src/components/PersonaBuilder.css`)
- Added `.col-linkedin` column styling
- Styled `.linkedin-input` field with focus states
- Updated grid layout to accommodate new column: `2fr 0.8fr 1.5fr 0.8fr 2fr`

## Usage Instructions

### For Users

1. **Navigate to Persona Builder** in the dashboard
2. **Locate the participant** you want to build/rebuild a persona for
3. **(Optional) Add LinkedIn URL:**
   - Enter the person's LinkedIn profile URL in the "LinkedIn (Optional)" field
   - Format: `linkedin.com/in/username` or full URL
4. **Click "Build Persona"** or "Rebuild" (if already built)
5. The system will fetch LinkedIn data and generate an enhanced persona

### Best Practices

- **Add LinkedIn URLs for executives** to ensure business-focused analysis
- **URL format is flexible** - both full URLs and shortened versions work
- **Leave blank if unavailable** - the system still works without LinkedIn data
- **Use Rebuild** to regenerate existing personas with new LinkedIn context

## Technical Considerations

### Privacy & Data Usage

- Only fetches **publicly available** LinkedIn profile data
- No authentication or private data access
- Data is used **only for persona generation**, not stored permanently
- Users control which profiles to enhance

### Error Handling

The system gracefully handles:
- Invalid LinkedIn URLs
- Profiles that don't exist
- Network errors during fetching
- Missing profile sections

If LinkedIn fetching fails, the persona generation continues without the enrichment data.

### Performance

- LinkedIn fetch adds ~2-3 seconds to persona build time
- Fetching happens asynchronously before AI analysis
- No impact on personas built without LinkedIn URLs

## Example: Before vs. After

### Before (Transcript Only)

**Michael Kianmahd** - Discussed Salesforce transformation in 19 meetings

**Generated Profile:**
- "Technology-oriented leader focused on system optimization"
- Examples: "system uptime", "API integration", "infrastructure management"
- Frameworks: Technical problem-solving, DevOps methodologies

### After (With LinkedIn: President & CEO)

**Generated Profile:**
- "Business executive with PE background who applies disciplined financial analysis to technology decisions"
- Examples: "ROI tracking", "stakeholder alignment", "vendor selection criteria"
- Frameworks: Executive decision-making, business transformation, financial analysis

## Future Enhancements

Potential improvements for v2:
- Automatic LinkedIn URL lookup via name matching
- Caching of profile data to reduce API calls
- Support for other professional networks (Twitter, GitHub for technical roles)
- Profile data validation and confidence scoring

## Dependencies

**New Requirement:**
```
beautifulsoup4==4.12.2
```

Added to `requirements.txt` for HTML parsing of LinkedIn profiles.

## Files Modified

1. `scripts/connectors/linkedin_scraper.py` (NEW)
2. `scripts/analyzers/persona_analyzer.py`
3. `api/main.py`
4. `frontend/src/components/PersonaBuilder.tsx`
5. `frontend/src/components/PersonaBuilder.css`
6. `requirements.txt`

## Testing

To test the feature:

1. Navigate to Persona Builder
2. Enter a valid LinkedIn URL for a participant
3. Click "Build Persona" or "Rebuild"
4. Compare generated persona with/without LinkedIn context
5. Verify persona uses appropriate business vs. technical language

---

**Status:** ✅ Implemented and Ready for Use

**Date:** November 10, 2025

**Version:** 1.0
