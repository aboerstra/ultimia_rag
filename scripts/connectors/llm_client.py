"""OpenRouter/Claude API client for intelligent analysis."""
import json
from typing import Dict, List, Optional
from openai import OpenAI
from config import Config


class LLMClient:
    """Client for interacting with Claude via OpenRouter using OpenAI library."""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=Config.OPENROUTER_BASE_URL,
            api_key=Config.OPENROUTER_API_KEY
        )
        self.model = "anthropic/claude-3.5-sonnet"  # Using 3.5 sonnet
        
    def analyze(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """
        Send a prompt to Claude and get analysis back.
        
        Args:
            prompt: The main prompt/question
            system_prompt: Optional system message to set context
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0-1)
            
        Returns:
            Claude's response text
        """
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    'HTTP-Referer': 'https://fayebsg.com',
                    'X-Title': 'Maxim QBR Analysis'
                },
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenRouter API: {e}")
            raise
    
    def analyze_transcript(self, transcript_text: str, filename: str) -> Dict:
        """
        Analyze a single meeting transcript.
        
        Args:
            transcript_text: The full text of the transcript
            filename: Name of the transcript file for context
            
        Returns:
            Dict with structured analysis
        """
        system_prompt = """You are analyzing meeting transcripts for a QBR presentation. 
Focus on extracting actionable insights, decisions, commitments, and concerns."""
        
        prompt = f"""Analyze this meeting transcript: {filename}

Transcript:
{transcript_text[:15000]}

Please provide a structured analysis in JSON format with these keys:
- date: Meeting date (if mentioned, otherwise "Unknown")
- attendees: List of attendees
- summary: 2-3 sentence summary of key discussion
- key_topics: List of main topics discussed
- decisions: List of decisions made
- action_items: List of action items with owners if mentioned
- concerns: List of concerns or blockers raised
- michael_priorities: What Michael Kianmahd specifically cared about or asked for
- commitments: Promises or commitments made

Return only valid JSON, no additional text."""

        response = self.analyze(prompt, system_prompt, max_tokens=2000, temperature=0.3)
        
        try:
            # Extract JSON from response (Claude sometimes adds markdown)
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                'filename': filename,
                'raw_analysis': response,
                'error': 'Failed to parse JSON response'
            }
    
    def synthesize_insights(self, all_analyses: List[Dict]) -> str:
        """
        Synthesize insights from multiple transcript analyses.
        
        Args:
            all_analyses: List of individual transcript analyses
            
        Returns:
            Markdown formatted synthesis document
        """
        system_prompt = """You are creating a comprehensive synthesis of multiple meeting transcripts 
for a QBR presentation to Michael Kianmahd. Focus on patterns, evolution of issues, and strategic insights."""
        
        prompt = f"""Based on these {len(all_analyses)} meeting analyses, create a comprehensive synthesis document.

Analyses:
{json.dumps(all_analyses, indent=2)[:20000]}

Create a markdown document with these sections:
1. Timeline of Key Events
2. Recurring Themes and Patterns
3. Michael's Top Priorities (based on what he repeatedly asked about)
4. Commitments Made vs Delivered
5. Unresolved Issues and Blockers
6. Evolution of Discussion Topics

Focus on insights that would be valuable for a QBR presentation."""

        return self.analyze(prompt, system_prompt, max_tokens=4000, temperature=0.5)
    
    def generate_text(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Generate text from a prompt (wrapper for analyze method).
        Used by AI chat endpoint.
        
        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response
            
        Returns:
            Claude's response text
        """
        return self.analyze(prompt, max_tokens=max_tokens)
    
    def chat_with_tools(
        self, 
        prompt: str, 
        tools: List[Dict],
        max_tokens: int = 4000
    ) -> Dict:
        """
        Chat with function calling support.
        
        Args:
            prompt: User's question
            tools: List of tool definitions
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with 'content' and optional 'tool_calls'
        """
        messages = [{"role": "user", "content": prompt}]
        
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    'HTTP-Referer': 'https://fayebsg.com',
                    'X-Title': 'Maxim QBR Analysis'
                },
                model=self.model,
                messages=messages,
                tools=tools,
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            message = completion.choices[0].message
            
            result = {
                "content": message.content or "",
                "tool_calls": []
            }
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
            
            return result
            
        except Exception as e:
            print(f"Error calling OpenRouter API with tools: {e}")
            raise
