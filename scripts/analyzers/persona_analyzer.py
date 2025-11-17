"""
Persona Analyzer - Multi-pass AI analysis to build executive personas from meeting transcripts

Implements expert frameworks from:
- Daniel Kahneman (Decision Psychology)
- Patrick Lencioni (Working Genius)
- Roger Martin (Integrative Thinking)
- Robert Cialdini (Influence Patterns)
- Nancy Duarte (Communication Preferences)
- Adam Grant (Cognitive Flexibility)
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from connectors.llm_client import LLMClient
from connectors.linkedin_scraper import LinkedInScraper
from connectors.linkedin_persistence import LinkedInPersistence


class PersonaAnalyzer:
    """Analyzes meeting transcripts to build comprehensive executive personas"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.linkedin = LinkedInScraper()
        self.persistence = LinkedInPersistence()
        self.data_dir = Path(__file__).parent.parent.parent / 'data-sources'
        self.transcripts_dir = self.data_dir / 'transcripts' / 'extracted'
        self.personas_dir = self.data_dir / 'personas'
        self.personas_dir.mkdir(exist_ok=True)
        
    def extract_all_participants(self) -> Dict[str, Dict[str, Any]]:
        """Extract all unique participants from transcript analyses"""
        participants = {}
        
        # Read all transcript analysis files
        for analysis_file in self.transcripts_dir.glob('*_analysis.json'):
            try:
                with open(analysis_file, 'r') as f:
                    data = json.load(f)
                    
                # Get attendees
                attendees = data.get('attendees', [])
                transcript_date = data.get('date', 'Unknown')
                filename = data.get('filename', analysis_file.stem)
                
                for attendee in attendees:
                    # Normalize name
                    name = attendee.strip()
                    
                    if name not in participants:
                        participants[name] = {
                            'name': name,
                            'transcripts': [],
                            'first_appearance': transcript_date,
                            'last_appearance': transcript_date,
                            'transcript_count': 0
                        }
                    
                    participants[name]['transcripts'].append({
                        'filename': filename,
                        'date': transcript_date,
                        'analysis_file': str(analysis_file)
                    })
                    participants[name]['transcript_count'] += 1
                    participants[name]['last_appearance'] = transcript_date
                    
            except Exception as e:
                print(f"Error reading {analysis_file}: {e}")
                continue
        
        # Merge duplicates (e.g., "Laura" + "Laura Dolphin" → "Laura Dolphin")
        participants = self._merge_duplicate_names(participants)
        
        return participants
    
    def _merge_duplicate_names(self, participants: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Merge duplicate names where first name matches full name's first part"""
        
        # Manual merge rules for known duplicates
        KNOWN_MERGES = {
            'Laura': 'Laura Dolphin',
            'Lyndon': 'Lyndon Elam'
        }
        
        merged = {}
        name_mapping = {}  # Maps short names to full names
        
        # Apply manual merges first
        all_names = list(participants.keys())
        for short_name, full_name in KNOWN_MERGES.items():
            if short_name in all_names and full_name in all_names:
                name_mapping[short_name] = full_name
                name_mapping[full_name] = full_name
        
        # First pass: identify automatic duplicates
        for name in all_names:
            if name in name_mapping:
                continue  # Already handled by manual merges
                
            # Check if this name is a first name that matches someone's full name
            potential_matches = []
            for other_name in all_names:
                if other_name != name and other_name.startswith(name + ' '):
                    potential_matches.append(other_name)
            
            # If we found matches, use the longest (most complete) name
            if potential_matches:
                # Use the longest matching name
                full_name = max([name] + potential_matches, key=len)
                name_mapping[name] = full_name
                for match in potential_matches:
                    name_mapping[match] = full_name
            elif name not in name_mapping:
                # No duplicates, keep as-is
                name_mapping[name] = name
        
        # Second pass: merge data
        for original_name, canonical_name in name_mapping.items():
            if canonical_name not in merged:
                merged[canonical_name] = {
                    'name': canonical_name,
                    'transcripts': [],
                    'first_appearance': participants[original_name]['first_appearance'],
                    'last_appearance': participants[original_name]['last_appearance'],
                    'transcript_count': 0
                }
            
            # Merge transcripts
            merged[canonical_name]['transcripts'].extend(participants[original_name]['transcripts'])
            merged[canonical_name]['transcript_count'] += participants[original_name]['transcript_count']
            
            # Update dates
            if participants[original_name]['first_appearance'] < merged[canonical_name]['first_appearance']:
                merged[canonical_name]['first_appearance'] = participants[original_name]['first_appearance']
            if participants[original_name]['last_appearance'] > merged[canonical_name]['last_appearance']:
                merged[canonical_name]['last_appearance'] = participants[original_name]['last_appearance']
        
        return merged
    
    def get_participant_transcripts(self, person_name: str) -> List[Dict[str, Any]]:
        """Get all transcript analyses for a specific person"""
        transcripts = []
        
        for analysis_file in self.transcripts_dir.glob('*_analysis.json'):
            try:
                with open(analysis_file, 'r') as f:
                    data = json.load(f)
                    
                if person_name in data.get('attendees', []):
                    # Also load the markdown transcript
                    md_file = analysis_file.with_suffix('.md')
                    transcript_text = ""
                    if md_file.exists():
                        with open(md_file, 'r') as mf:
                            transcript_text = mf.read()
                    
                    transcripts.append({
                        'analysis': data,
                        'transcript': transcript_text,
                        'filename': data.get('filename', analysis_file.stem),
                        'date': data.get('date', 'Unknown')
                    })
            except Exception as e:
                print(f"Error reading {analysis_file}: {e}")
                continue
        
        return transcripts
    
    def pass1_behavioral_coding(self, transcripts: List[Dict], profile_context: str = "") -> Dict[str, Any]:
        """Pass 1: Extract behavioral patterns and decision points"""
        
        prompt = f"""You are an organizational psychologist analyzing executive behavior patterns.

{profile_context}
CONTEXT: Analyzing {len(transcripts)} meeting transcripts to identify behavioral patterns.

TASK: For each transcript, identify and code:
1. Decision Points - When the person made or influenced decisions
2. Question Types - Clarifying, challenging, exploring, directing
3. Priority Signals - Words indicating importance ("must-have", "critical", "nice-to-have")
4. Time Orientation - Immediate/tactical vs. strategic/long-term focus
5. Risk Language - "proper solution", "quick fix", risk tolerance indicators
6. Stakeholder Mentions - Who they consider in decisions

TRANSCRIPTS TO ANALYZE:
{json.dumps([{'filename': t['filename'], 'date': t['date'], 'key_topics': t['analysis'].get('key_topics', [])} for t in transcripts[:10]], indent=2)}

OUTPUT: Structured behavioral coding with patterns and frequency counts."""

        response = self.llm.generate_text(prompt, max_tokens=4000)
        
        return {
            'behavioral_patterns': response,
            'transcript_count': len(transcripts),
            'analysis_date': datetime.now().isoformat()
        }
    
    def pass2_framework_mapping(self, behavioral_data: Dict, transcripts: List[Dict], profile_context: str = "") -> Dict[str, Any]:
        """Pass 2: Apply expert frameworks to behavioral data"""
        
        # Prepare context from transcripts
        priorities_context = []
        for t in transcripts[:15]:  # Use up to 15 transcripts for context
            if 'michael_priorities' in t['analysis']:
                priorities_context.extend(t['analysis']['michael_priorities'])
        
        prompt = f"""You are an executive leadership analyst applying expert frameworks.

{profile_context}
BEHAVIORAL DATA:
{behavioral_data.get('behavioral_patterns', '')}

PRIORITY PATTERNS FROM TRANSCRIPTS:
{json.dumps(priorities_context, indent=2)}

Apply these frameworks:

1. KAHNEMAN (Thinking Fast & Slow):
   - System 1 decisions: Quick, intuitive, pattern-based
   - System 2 decisions: Deliberate, analytical, reasoned
   - Score each (0-10) and provide evidence

2. LENCIONI (Working Genius):
   - Wonder (abstract thinking, curiosity)
   - Invention (creative problem-solving)
   - Discernment (judgment, evaluation)
   - Galvanizing (rallying people, momentum)
   - Enablement (supporting, resourcing)
   - Tenacity (completion, persistence)
   - Score each (0-10) with examples

3. MARTIN (Integrative Thinking):
   - Ability to hold opposing ideas
   - Trade-off navigation approach
   - Synthesis patterns
   - Score (0-10) with evidence

4. CIALDINI (Influence Patterns):
   - What persuades this person?
   - Reciprocity, Authority, Social Proof, etc.

OUTPUT: Framework scores with supporting evidence from transcripts."""

        response = self.llm.generate_text(prompt, max_tokens=4000)
        
        return {
            'framework_analysis': response,
            'frameworks_applied': ['kahneman', 'lencioni', 'martin', 'cialdini']
        }
    
    def pass3_longitudinal_analysis(self, transcripts: List[Dict], profile_context: str = "") -> Dict[str, Any]:
        """Pass 3: Track patterns over time"""
        
        # Sort transcripts chronologically if possible
        sorted_transcripts = sorted(transcripts, key=lambda x: x.get('date', ''))
        
        prompt = f"""Analyze how this executive's patterns evolved over {len(transcripts)} conversations.

{profile_context}
TIMELINE:
First conversation: {sorted_transcripts[0]['date'] if sorted_transcripts else 'Unknown'}
Last conversation: {sorted_transcripts[-1]['date'] if sorted_transcripts else 'Unknown'}

EARLY PRIORITIES (First 5 conversations):
{json.dumps([t['analysis'].get('key_topics', []) for t in sorted_transcripts[:5]], indent=2)}

RECENT PRIORITIES (Last 5 conversations):
{json.dumps([t['analysis'].get('key_topics', []) for t in sorted_transcripts[-5:]], indent=2)}

TRACK:
1. Priority shifts over time
2. Language pattern evolution
3. Decision speed changes
4. Recurring concerns vs. one-time issues
5. Commitment follow-through patterns

OUTPUT: Longitudinal pattern analysis with trends."""

        response = self.llm.generate_text(prompt, max_tokens=3000)
        
        return {
            'evolution_patterns': response,
            'timeline_span': f"{sorted_transcripts[0]['date']} to {sorted_transcripts[-1]['date']}" if sorted_transcripts else "Unknown"
        }
    
    def pass4_persona_synthesis(self, all_analyses: Dict, profile_context: str = "") -> Dict[str, Any]:
        """Pass 4: Synthesize into concise, actionable persona profile"""
        
        prompt = f"""Create a CONCISE executive persona profile (max 600 words).

{profile_context}
AVAILABLE DATA:
- Behavioral Patterns: {all_analyses.get('pass1', {}).get('transcript_count', 0)} transcripts analyzed
- Framework Scores: {all_analyses.get('pass2', {}).get('frameworks_applied', [])}
- Evolution: {all_analyses.get('pass3', {}).get('timeline_span', 'Unknown')}

BEHAVIORAL CODING:
{all_analyses.get('pass1', {}).get('behavioral_patterns', '')[:2000]}

FRAMEWORK ANALYSIS:
{all_analyses.get('pass2', {}).get('framework_analysis', '')[:2000]}

EVOLUTION PATTERNS:
{all_analyses.get('pass3', {}).get('evolution_patterns', '')[:1500]}

CREATE ULTRA-CONCISE PROFILE:

1. DECISION STYLE (2-3 sentences max)
   - Core approach, speed, what matters most

2. GREEN LIGHTS (bullets, 3-4 items)
   - What gets approved fast

3. RED FLAGS (bullets, 3-4 items)
   - What causes rejection

4. WORKING PREFERENCES (bullets, 3-4 items)
   - Communication style, energy sources

5. PRIORITY WEIGHTS (ranked list, top 3-5)
   - What matters most in order

CRITICAL: Be SPECIFIC not GENERIC. Use actual patterns from data.
NO REDUNDANCY between sections. Each point unique.
OUTPUT: Concise, scannable markdown."""

        response = self.llm.generate_text(prompt, max_tokens=2500)
        
        return {
            'persona_profile': response
        }
    
    def pass5_predictive_model(self, persona_profile: Dict, transcripts: List[Dict], profile_context: str = "") -> Dict[str, Any]:
        """Pass 5: Create practical working templates"""
        
        # Extract actual decisions made
        decisions_context = []
        for t in transcripts[:10]:
            if 'decisions' in t['analysis']:
                decisions_context.extend(t['analysis']['decisions'])
        
        prompt = f"""Create PRACTICAL TEMPLATES for working with this executive (max 500 words).

{profile_context}
PERSONA PROFILE:
{persona_profile.get('persona_profile', '')[:1500]}

ACTUAL DECISIONS:
{json.dumps(decisions_context[:5], indent=2)}

CREATE 3 ACTIONABLE TEMPLATES:

TEMPLATE 1: Proposing Technical Solutions
- Subject line format
- 4-part structure (Problem/Solution/Resources/Risks)
- Example: ✅ Good vs ❌ Bad

TEMPLATE 2: Requesting Resources
- What data to include
- How to justify
- Example pitch

TEMPLATE 3: Escalating Issues
- When to escalate
- Information to provide
- Expected response

ALSO CREATE:
DECISION IF/THEN RULES (5-7 rules)
- IF [clear conditions] THEN [likely outcome] (confidence %)

CRITICAL: Make templates COPY-PASTE ready. Specific not generic.
OUTPUT: Actionable markdown templates."""

        response = self.llm.generate_text(prompt, max_tokens=2500)
        
        return {
            'working_templates': response
        }
    
    def pass6_qbr_presentation_guide(self, all_analyses: Dict, transcripts: List[Dict], profile_context: str = "") -> Dict[str, Any]:
        """Pass 6: Create QBR presentation template"""
        
        prompt = f"""Create a COMPREHENSIVE QBR SLIDE DECK TEMPLATE for this executive (800-1000 words).

{profile_context}
PERSONA PROFILE:
{all_analyses.get('pass4', {}).get('persona_profile', '')[:1500]}

CREATE DETAILED QBR GUIDE:

## OPTIMAL DECK STRUCTURE (25-30 slides, 45 min)

Break down by sections with specific guidance:

SECTION 1: Executive Dashboard (X slides, Y min)
- What to include (metrics, KPIs, etc.)
- Visual format preferences
- Example slide content

SECTION 2: Deep Dive (X slides, Y min)
- Technical vs business focus
- Level of detail expected
- Supporting data requirements

SECTION 3: Forward Planning (X slides, Y min)
- Resource requests format
- Decision framing approach
- Timeline expectations

SECTION 4: Decisions Needed (X slides, Y min)
- How to present options
- What trade-offs to show
- Action items format

## GOLDEN RULES (based on decision style)
- Lead with [data/narrative/metrics] - be specific
- Time allocation per section
- Pre-meeting preparation requirements
- When to send deck (days before)
- Interactive vs presentation style

## SLIDE DESIGN PREFERENCES
✅ DO (5-6 specific items):
- Visual format they prefer
- Data presentation style
- Technical depth level
- Specific examples

❌ DON'T (5-6 specific items):
- What to avoid
- Format mistakes
- Content gaps
- Specific anti-patterns

## BEFORE THE MEETING
- Preparation checklist
- Pre-socialization needs
- Materials to send ahead

## DURING PRESENTATION
- Pacing and timing
- When to pause for questions
- How to handle pushback
- Discussion vs presentation ratio

## EXAMPLE SLIDE STRUCTURES
Provide 2-3 example slide outlines showing:
- Title format
- Content structure
- Data visualization
- Key takeaways

CRITICAL: Base ALL guidance on THIS person's actual decision style and preferences from the persona profile. Be SPECIFIC not generic. Include concrete examples.

OUTPUT: Comprehensive, actionable QBR template."""

        response = self.llm.generate_text(prompt, max_tokens=3500)
        
        return {
            'qbr_template': response
        }
    
    def generate_persona_document(self, person_name: str, all_analyses: Dict, transcript_count: int, profile_data: Optional[Dict] = None) -> str:
        """Generate final persona document in markdown"""
        
        # Build header with professional data if available
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M:%S %p %Z')
        header_parts = [f"**Generated:** {timestamp}", f"**Based on:** {transcript_count} transcripts"]
        
        # Add professional data if available
        if profile_data and (profile_data.get('title') or profile_data.get('company')):
            if profile_data.get('title'):
                header_parts.insert(0, f"**Role:** {profile_data['title']}")
            if profile_data.get('company'):
                header_parts.insert(1 if profile_data.get('title') else 0, f"**Company:** {profile_data['company']}")
        
        header = " | ".join(header_parts)
        
        doc = f"""# {person_name}: Executive Persona

{header}

---

## Quick Reference

{all_analyses.get('pass4', {}).get('persona_profile', 'Profile generation in progress...')}

---

## How to Work With {person_name.split()[0]}

{all_analyses.get('pass5', {}).get('working_templates', 'Templates generation in progress...')}

---

## QBR Presentation Guide

{all_analyses.get('pass6', {}).get('qbr_template', 'QBR guide generation in progress...')}

---

<details>
<summary><b>📊 Analysis Details</b> (click to expand)</summary>

### Evolution Over Time

{all_analyses.get('pass3', {}).get('evolution_patterns', 'Evolution analysis in progress...')}

### Methodology

6-pass AI analysis using expert frameworks:
- **Kahneman** (Decision Psychology) • **Lencioni** (Working Genius) • **Martin** (Integrative Thinking)
- **Cialdini** (Influence) • **Duarte** (Communication) • **Grant** (Cognitive Flexibility)

**Analysis Passes:**
1. Behavioral Coding → 2. Framework Mapping → 3. Longitudinal Analysis → 4. Persona Synthesis → 5. Working Templates → 6. QBR Guide

**Timeline:** {all_analyses.get('pass3', {}).get('timeline_span', 'Unknown')}

</details>

---

*AI-generated persona profile • Use as decision-support tool, not absolute truth*
"""
        
        return doc
    
    def build_persona(self, person_name: str, linkedin_url: Optional[str] = None) -> Dict[str, Any]:
        """Execute complete 6-pass analysis to build persona"""
        
        print(f"\n🔨 Building persona for {person_name}...")
        
        # Automatically fetch professional background (no URL required)
        profile_data = None
        profile_context = ""
        
        # Check if we have cached profile data
        cached_data = self.persistence.get_cached_profile(person_name)
        if cached_data:
            cache_age = self.persistence.get_cache_age(person_name)
            print(f"  Using cached profile ({cache_age})")
            profile_data = cached_data
        else:
            # Fetch fresh data using person's name only
            print(f"  Fetching professional background...")
            try:
                profile_data = self.linkedin.fetch_profile(person_name)
                print(f"  DEBUG: fetch_profile returned: {profile_data is not None}")
                
                if profile_data:
                    # Cache the fetched data
                    print(f"  DEBUG: Caching profile data...")
                    self.persistence.cache_profile_data(person_name, profile_data)
                    print(f"  DEBUG: Cache successful")
                else:
                    print(f"  DEBUG: profile_data was None")
            except Exception as e:
                print(f"  ❌ ERROR in enrichment: {e}")
                import traceback
                traceback.print_exc()
                profile_data = None
        
        # Format context if we have profile data
        if profile_data:
            profile_context = self.linkedin.format_context_prompt(profile_data)
            print(f"  ✅ Professional context added: {profile_data.get('title', 'Unknown role')}")
        else:
            print(f"  ℹ️  No professional context found, using transcript-only analysis")
        
        # Get all transcripts for this person
        transcripts = self.get_participant_transcripts(person_name)
        
        if len(transcripts) < 3:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least 3 transcripts, found {len(transcripts)}',
                'transcript_count': len(transcripts)
            }
        
        print(f"  Found {len(transcripts)} transcripts")
        
        all_analyses = {}
        
        # Pass 1: Behavioral Coding
        print("  Pass 1/6: Behavioral Coding...")
        all_analyses['pass1'] = self.pass1_behavioral_coding(transcripts, profile_context)
        
        # Pass 2: Framework Mapping
        print("  Pass 2/6: Framework Mapping...")
        all_analyses['pass2'] = self.pass2_framework_mapping(all_analyses['pass1'], transcripts, profile_context)
        
        # Pass 3: Longitudinal Analysis
        print("  Pass 3/6: Pattern Evolution...")
        all_analyses['pass3'] = self.pass3_longitudinal_analysis(transcripts, profile_context)
        
        # Pass 4: Persona Synthesis
        print("  Pass 4/6: Persona Synthesis...")
        all_analyses['pass4'] = self.pass4_persona_synthesis(all_analyses, profile_context)
        
        # Pass 5: Predictive Model
        print("  Pass 5/6: Working Templates...")
        all_analyses['pass5'] = self.pass5_predictive_model(all_analyses['pass4'], transcripts, profile_context)
        
        # Pass 6: QBR Presentation Guide
        print("  Pass 6/6: QBR Guide...")
        all_analyses['pass6'] = self.pass6_qbr_presentation_guide(all_analyses, transcripts, profile_context)
        
        # Generate final document
        print("  Generating document...")
        persona_doc = self.generate_persona_document(person_name, all_analyses, len(transcripts), profile_data)
        
        # Save to file
        filename = person_name.lower().replace(' ', '-')
        output_path = self.personas_dir / f'{filename}_persona.md'
        
        with open(output_path, 'w') as f:
            f.write(persona_doc)
        
        print(f"✅ Persona saved to {output_path}")
        
        return {
            'status': 'completed',
            'person_name': person_name,
            'transcript_count': len(transcripts),
            'output_path': str(output_path),
            'analyses': all_analyses
        }
