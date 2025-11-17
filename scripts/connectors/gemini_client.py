"""Google Gemini API client with native function calling support.

Uses Gemini 2.5 Pro - 1M input tokens, 65K output tokens for long-form content.
"""
import google.generativeai as genai
from google.generativeai.types import content_types
from typing import Dict, List, Optional
import json
import logging
import os

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini 2.5 Pro with native function calling."""
    
    def __init__(self, api_key: str):
        """Initialize Gemini client."""
        genai.configure(api_key=api_key)
        self.model_id = 'gemini-2.5-pro'
        self.model = genai.GenerativeModel(self.model_id)
        logger.info(f"Gemini client initialized with {self.model_id}")
    
    def chat_with_tools(
        self, 
        prompt: str, 
        tools: List[Dict],
        max_tokens: int = 65000
    ) -> Dict:
        """
        Chat with function calling support.
        
        Args:
            prompt: User's question
            tools: List of tool definitions (OpenAI format, will be converted)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with 'content' and optional 'tool_calls'
        """
        try:
            # Convert OpenAI format tools to Gemini format
            gemini_tools = None
            if tools:
                # Gemini expects just the function declarations
                function_declarations = []
                for tool in tools:
                    if tool.get("type") == "function":
                        func = tool["function"]
                        function_declarations.append({
                            "name": func["name"],
                            "description": func["description"],
                            "parameters": func.get("parameters", {})
                        })
                
                if function_declarations:
                    gemini_tools = [{"function_declarations": function_declarations}]
            
            # Make the call
            response = self.model.generate_content(
                contents=prompt,
                tools=gemini_tools,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3
                )
            )
            
            result = {
                "content": "",
                "tool_calls": []
            }
            
            if not response.candidates:
                logger.warning("No candidates in Gemini response")
                return result
            
            candidate = response.candidates[0]
            
            # Check for function calls
            if hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    # Check if this part is a function call
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        logger.info(f"Gemini called function: {fc.name}")
                        
                        # Convert args to dict
                        args_dict = {}
                        if hasattr(fc, 'args') and fc.args:
                            args_dict = dict(fc.args)
                        
                        result["tool_calls"].append({
                            "id": f"call_{fc.name}",
                            "name": fc.name,
                            "arguments": args_dict
                        })
                    # Check if this part is text
                    elif hasattr(part, 'text'):
                        result["content"] += part.text
            
            # Fallback: try to get text directly
            if not result["content"] and not result["tool_calls"]:
                try:
                    result["content"] = candidate.text
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def generate_text(self, prompt: str, max_tokens: int = 65000) -> str:
        """
        Generate text without tools.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text
        """
        try:
            response = self.model.generate_content(
                contents=prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7
                )
            )
            
            # Check if response has candidates
            if not response.candidates:
                raise ValueError("No response candidates returned by Gemini")
            
            candidate = response.candidates[0]
            
            # Check finish reason
            finish_reason = candidate.finish_reason
            if finish_reason == 2:  # MAX_TOKENS
                logger.warning("Response was truncated due to max_tokens limit")
            elif finish_reason == 3:  # SAFETY
                raise ValueError("Response blocked by safety filters")
            elif finish_reason == 4:  # RECITATION
                raise ValueError("Response blocked due to recitation concerns")
            
            # Try to get text
            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                text_parts = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text'):
                        text_parts.append(part.text)
                if text_parts:
                    return ''.join(text_parts)
            
            # Fallback to response.text
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini text generation error: {e}")
            raise
    
    def generate_with_grounding(self, prompt: str, max_tokens: int = 65000) -> Dict:
        """
        Generate text with Google Search grounding.
        
        Uses the new google-genai SDK to enable web search grounding,
        allowing Gemini to search Google and cite sources.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with 'content' and 'sources' (list of web citations)
        """
        try:
            # Import the new SDK
            from google import genai as genai_new
            from google.genai import types
            
            # Initialize client with API key
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            
            client = genai_new.Client(api_key=api_key)
            
            # Create grounding tool for Google Search
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            
            # Configure generation with grounding
            config = types.GenerateContentConfig(
                tools=[grounding_tool],
                temperature=0.7,
                max_output_tokens=max_tokens
            )
            
            # Generate content with grounding
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config=config
            )
            
            result = {
                "content": "",
                "sources": [],
                "search_queries": []
            }
            
            # Extract text content
            if response.text:
                result["content"] = response.text
            
            # Extract grounding metadata
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    gm = candidate.grounding_metadata
                    
                    # Extract search queries used
                    if hasattr(gm, 'web_search_queries') and gm.web_search_queries:
                        result["search_queries"] = list(gm.web_search_queries)
                        logger.info(f"Web search queries: {result['search_queries']}")
                    
                    # Extract grounding chunks (sources)
                    if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                        for chunk in gm.grounding_chunks:
                            if hasattr(chunk, 'web') and chunk.web:
                                source = {
                                    "title": chunk.web.title if hasattr(chunk.web, 'title') else "Unknown",
                                    "uri": chunk.web.uri if hasattr(chunk.web, 'uri') else ""
                                }
                                result["sources"].append(source)
                                logger.info(f"Source: {source['title']} - {source['uri']}")
            
            logger.info(f"Generated with grounding. Found {len(result['sources'])} sources.")
            return result
            
        except ImportError:
            logger.error("google-genai package not installed. Run: pip install google-genai")
            raise
        except Exception as e:
            logger.error(f"Gemini grounding error: {e}")
            raise
