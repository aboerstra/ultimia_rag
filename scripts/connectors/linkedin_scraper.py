"""
LinkedIn Profile Enrichment - Gets professional context using LLM knowledge + Google search

Strategy:
1. First: Ask LLM if it knows the person (might be in training data)
2. Fallback: Use Serper (Google Search API) to find current role/background
3. Last resort: Return empty (graceful degradation)
"""

import os
import re
import requests
from typing import Dict, Optional


class LinkedInScraper:
    """Enriches persona with professional context using LLM knowledge"""
    
    def __init__(self):
        self.llm = None  # Will be lazy-loaded
    
    def _get_llm(self):
        """Lazy load LLM client to avoid circular imports"""
        if self.llm is None:
            from connectors.llm_client import LLMClient
            self.llm = LLMClient()
        return self.llm
    
    def fetch_profile(self, person_name: str) -> Optional[Dict[str, str]]:
        """
        Fetch professional background using LLM knowledge + Google search
        
        Args:
            person_name: Person's full name (from transcripts)
            
        Returns:
            Dict with profile data or None if fetch fails
        """
        try:
            print(f"  Checking LLM knowledge for: {person_name}")
            
            # Ask LLM if it knows this person
            profile_data = self._ask_llm_about_person(person_name)
            
            if profile_data and profile_data.get('title'):
                print(f"  ✅ Found in LLM knowledge: {profile_data['title']}")
                return profile_data
            
            # Fallback: Try Serper (Google Search)
            print(f"  Trying Google Search via Serper...")
            profile_data = self._search_with_serper(person_name)
            
            if profile_data and profile_data.get('title'):
                print(f"  ✅ Found via Google Search: {profile_data['title']}")
                return profile_data
            else:
                print(f"  ℹ️  No context found, continuing without enrichment")
                return None
                
        except Exception as e:
            print(f"⚠️  Error fetching profile data: {e}")
            return None
    
    def _extract_name_from_url(self, url: str) -> Optional[str]:
        """Extract name from LinkedIn URL"""
        try:
            # Format: linkedin.com/in/first-last-12345
            match = re.search(r'/in/([\w-]+)', url)
            if match:
                slug = match.group(1)
                # Remove trailing numbers
                slug = re.sub(r'-\d+$', '', slug)
                # Convert to proper case
                name = slug.replace('-', ' ').title()
                return name
            return None
        except:
            return None
    
    def _search_with_serper(self, name: str) -> Optional[Dict[str, str]]:
        """
        Use Serper (Google Search API) to find professional background
        
        Args:
            name: Person's name
            
        Returns:
            Professional background info or None
        """
        try:
            serper_key = os.getenv('SERPER_API_KEY')
            if not serper_key:
                return None
            
            # Get company name from environment
            company_name = os.getenv('CLIENT_NAME', '')
            
            # Search for the person with company context
            search_query = f"{name} {company_name} CEO president executive professional background"
            
            response = requests.post(
                'https://google.serper.dev/search',
                headers={
                    'X-API-KEY': serper_key,
                    'Content-Type': 'application/json'
                },
                json={'q': search_query},
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            results = response.json()
            
            # Extract information from search results
            profile_text = ""
            
            # Get organic results
            if 'organic' in results:
                for result in results['organic'][:3]:  # Top 3 results
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    profile_text += f"{title}. {snippet} "
            
            # Get knowledge graph if available
            if 'knowledgeGraph' in results:
                kg = results['knowledgeGraph']
                profile_text += f"{kg.get('title', '')}. {kg.get('description', '')} "
            
            if not profile_text:
                return None
            
            # Ask LLM to extract structured data from search results
            llm = self._get_llm()
            
            prompt = f"""Extract professional information from these search results about {name}.

SEARCH RESULTS:
{profile_text[:1000]}

Extract and return ONLY a JSON object with these fields:
{{
  "name": "Michael Kianmahd",
  "title": "CEO",
  "company": "Maxim Commercial Capital, LLC",
  "about": "Brief background from results"
}}

Rules:
- Extract the most recent/current title
- Use full company name if available
- Combine info from multiple results
- Return valid JSON only, no markdown
- If truly no info found, return: {{"title": "", "company": ""}}"""

            response_text = llm.generate_text(prompt, max_tokens=400)
            
            # Parse JSON response - be more lenient
            import json
            
            # Clean response aggressively
            response_clean = response_text.strip()
            
            # Remove markdown code blocks
            if '```' in response_clean:
                # Extract everything between ``` markers
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_clean, re.DOTALL)
                if json_match:
                    response_clean = json_match.group(1)
                else:
                    # Try to find JSON object
                    json_match = re.search(r'\{.*\}', response_clean, re.DOTALL)
                    if json_match:
                        response_clean = json_match.group(0)
            
            try:
                data = json.loads(response_clean)
                
                # Check if we got useful data
                if data.get('title') or data.get('company'):
                    # Fill in missing fields
                    data['url'] = ''
                    for field in ['name', 'title', 'company', 'about', 'location', 'experience_summary', 'education_summary']:
                        if field not in data:
                            data[field] = ''
                    
                    # Debug log
                    print(f"    Extracted: {data.get('title', 'N/A')} at {data.get('company', 'N/A')}")
                    return data
                else:
                    print(f"    LLM returned empty title/company")
                    return None
                    
            except json.JSONDecodeError as e:
                print(f"    JSON parse error: {e}")
                print(f"    Response was: {response_clean[:200]}")
                pass
            
            return None
            
        except Exception as e:
            print(f"    Error with Serper search: {e}")
            return None
    
    def _ask_llm_about_person(self, name: str) -> Optional[Dict[str, str]]:
        """
        Ask LLM if it knows about this person's professional background
        
        Args:
            name: Person's name
            
        Returns:
            Professional background info or None
        """
        try:
            llm = self._get_llm()
            
            # Get company name for context
            company_name = os.getenv('CLIENT_NAME', '')
            
            prompt = f"""Do you have information about {name} in your training data? Context: They work at or with {company_name}.

If yes, provide their current professional information in this EXACT JSON format:
{{
  "name": "Full Name",
  "title": "Current Job Title",
  "company": "Current Company",
  "about": "Brief professional background (1-2 sentences)",
  "experience_summary": "Career highlights",
  "education_summary": "Education background"
}}

If you don't have reliable information about this specific person, respond with:
{{"known": false}}

IMPORTANT: 
- Only include information you're confident about from your training data
- If you're not sure, say you don't know
- Do not make up or infer information"""
            
            response = llm.generate_text(prompt, max_tokens=500)
            
            # Try to parse JSON response
            import json
            
            # Clean response (remove markdown code blocks if present)
            response_clean = response.strip()
            if response_clean.startswith('```'):
                # Extract JSON from code block
                lines = response_clean.split('\n')
                response_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_clean
            
            try:
                data = json.loads(response_clean)
                
                # Check if LLM knows the person
                if data.get('known') == False:
                    return None
                
                # Validate we got useful data
                if data.get('title') or data.get('company'):
                    # Add empty URL field
                    data['url'] = ''
                    # Ensure all expected fields exist
                    for field in ['name', 'title', 'company', 'about', 'location', 'experience_summary', 'education_summary']:
                        if field not in data:
                            data[field] = ''
                    return data
                    
            except json.JSONDecodeError:
                # LLM response wasn't valid JSON
                pass
            
            return None
            
        except Exception as e:
            print(f"    Error asking LLM: {e}")
            return None
    
    def format_context_prompt(self, profile_data: Optional[Dict[str, str]]) -> str:
        """
        Format profile data into context for AI prompts
        
        Args:
            profile_data: Profile data dict or None
            
        Returns:
            Formatted context string for inclusion in prompts
        """
        if not profile_data or not (profile_data.get('title') or profile_data.get('company')):
            return ""
        
        # Build context block
        context_parts = []
        
        context_parts.append("═══════════════════════════════════════════════════════════")
        context_parts.append("PUBLIC PROFILE CONTEXT")
        context_parts.append("═══════════════════════════════════════════════════════════")
        
        if profile_data.get('name'):
            context_parts.append(f"Name: {profile_data['name']}")
        
        if profile_data.get('title'):
            context_parts.append(f"Current Role: {profile_data['title']}")
        
        if profile_data.get('company'):
            context_parts.append(f"Company: {profile_data['company']}")
        
        if profile_data.get('about'):
            context_parts.append(f"\nProfessional Background: {profile_data['about']}")
        
        if profile_data.get('experience_summary'):
            context_parts.append(f"Experience: {profile_data['experience_summary']}")
        
        if profile_data.get('education_summary'):
            context_parts.append(f"Education: {profile_data['education_summary']}")
        
        context_parts.append("")
        
        # Add interpretation guidance
        context_parts.append("⚠️  CRITICAL INTERPRETATION GUIDANCE:")
        
        # Determine if this is a business or technical role
        title_lower = profile_data.get('title', '').lower()
        is_business_role = any(term in title_lower for term in [
            'president', 'ceo', 'chief executive', 'founder', 'managing director',
            'vice president', 'vp', 'director', 'head of', 'general manager', 'owner'
        ])
        
        is_technical_role = any(term in title_lower for term in [
            'engineer', 'developer', 'architect', 'technical', 'devops', 'sre',
            'infrastructure', 'platform', 'software', 'cto', 'chief technology'
        ])
        
        if is_business_role and not is_technical_role:
            context_parts.append("• This is a BUSINESS EXECUTIVE, not a technical engineer")
            context_parts.append("• Interpret transcript discussions through a BUSINESS LENS:")
            context_parts.append("  - 'System uptime' = business continuity, customer satisfaction")
            context_parts.append("  - 'API integration' = vendor relationships, business workflow efficiency")
            context_parts.append("  - 'Infrastructure' = operational risk management, cost optimization")
            context_parts.append("  - 'Technical debt' = ROI analysis on maintenance vs new features")
            context_parts.append("  - 'Salesforce' = CRM strategy, customer relationship management")
            context_parts.append("• Use BUSINESS examples in persona (NOT technical jargon):")
            context_parts.append("  - Good: 'ROI tracking', 'stakeholder alignment', 'vendor selection'")
            context_parts.append("  - Bad: 'system uptime', 'API endpoints', 'deployment pipelines'")
            context_parts.append("• Focus on: Business outcomes, ROI, strategic decisions, stakeholder management")
        elif is_technical_role:
            context_parts.append("• This is a TECHNICAL LEADER")
            context_parts.append("• Balance technical depth with business impact in examples")
            context_parts.append("• Focus on: Architecture decisions, technical trade-offs, team enablement")
        else:
            context_parts.append("• Interpret discussions in context of their actual role")
            context_parts.append("• Avoid assuming technical or business focus without evidence")
        
        context_parts.append("═══════════════════════════════════════════════════════════")
        context_parts.append("")
        
        return "\n".join(context_parts)
