# Persona Builder Feature - Implementation Plan

## Overview
AI-powered executive persona generator that analyzes meeting transcripts to build comprehensive behavioral and decision-making profiles.

## Architecture

### Backend Components
1. **Persona Analyzer** (`scripts/analyzers/persona_analyzer.py`)
   - Multi-pass AI analysis framework
   - Implements 6 expert frameworks (Kahneman, Lencioni, Martin, etc.)
   - Generates comprehensive persona documents

2. **API Endpoints** (`api/main.py`)
   - `GET /api/personas/participants` - List all participants from transcripts
   - `POST /api/personas/build` - Trigger persona generation
   - `GET /api/personas/build-status/{task_id}` - Check build status
   - `GET /api/personas/{person_name}` - Get persona data
   - `GET /api/personas/{person_name}/download` - Download persona document

3. **Data Storage**
   - `data-sources/personas/` - Generated persona documents
   - `data-sources/personas/participants.json` - Cached participant list
   - `data-sources/personas/build-queue.json` - Track in-progress builds

### Frontend Components
1. **PersonaBuilder Component** (`frontend/src/components/PersonaBuilder.tsx`)
   - Display participant list with build status
   - Trigger persona generation
   - View/download generated personas
   - Real-time build progress tracking

2. **PersonaViewer Component** - Modal to display persona details

### Expert Frameworks Applied
1. **Daniel Kahneman** - Decision Psychology (System 1 vs System 2)
2. **Patrick Lencioni** - Working Genius Model
3. **Roger Martin** - Integrative Thinking
4. **Robert Cialdini** - Influence Patterns
5. **Nancy Duarte** - Communication Preferences
6. **Adam Grant** - Cognitive Flexibility

## Implementation Phases

### Phase 1: Backend Foundation ✓ (Ready to start)
- [ ] Create persona analyzer module
- [ ] Add participant extraction logic
- [ ] Implement 6-pass analysis framework
- [ ] Add persona generation API endpoints
- [ ] Create persona document templates

### Phase 2: Frontend UI (2-3 hours)
- [ ] Create PersonaBuilder component
- [ ] Add routing/navigation
- [ ] Build participant table UI
- [ ] Implement build trigger functionality
- [ ] Add persona viewer modal

### Phase 3: Integration & Testing (1 hour)
- [ ] Connect frontend to backend
- [ ] Add real-time status updates
- [ ] Test end-to-end workflow
- [ ] Generate sample persona (Michael Kianmahd)

## Data Requirements
- **Minimum Transcripts**: 3 conversations for viable persona
- **Optimal**: 10+ conversations for high-confidence profile
- **Build Time**: 4-6 minutes per persona

## Output Format
Generated personas include:
- Executive Summary (2 pages)
- Decision DNA Analysis
- Working Genius Profile
- Influence Response Matrix
- Communication Optimization Guide
- Predictive Decision Model
- Scenario Playbooks

## Next Steps
1. Start with Phase 1: Backend implementation
2. Build core analyzer with multi-pass framework
3. Add API endpoints
4. Test with Michael Kianmahd's 23 transcripts
