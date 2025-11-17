"""
LinkedIn URL and Profile Data Persistence
Handles saving/loading LinkedIn URLs and caching profile data
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

class LinkedInPersistence:
    def __init__(self):
        self.base_dir = Path("data-sources/personas")
        self.urls_file = self.base_dir / "linkedin_urls.json"
        self.cache_dir = self.base_dir / "linkedin_cache"
        
        # Ensure directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize URLs file if it doesn't exist
        if not self.urls_file.exists():
            self._save_urls({})
    
    def _save_urls(self, urls: Dict[str, str]):
        """Save LinkedIn URLs to file"""
        with open(self.urls_file, 'w') as f:
            json.dump(urls, f, indent=2)
    
    def _load_urls(self) -> Dict[str, str]:
        """Load LinkedIn URLs from file"""
        try:
            with open(self.urls_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_linkedin_url(self, person_name: str, linkedin_url: str):
        """
        Save LinkedIn URL for a person
        
        Args:
            person_name: Name of the person
            linkedin_url: Their LinkedIn profile URL
        """
        urls = self._load_urls()
        urls[person_name] = linkedin_url
        self._save_urls(urls)
        print(f"✓ Saved LinkedIn URL for {person_name}")
    
    def get_linkedin_url(self, person_name: str) -> Optional[str]:
        """
        Get saved LinkedIn URL for a person
        
        Args:
            person_name: Name of the person
            
        Returns:
            LinkedIn URL or None if not saved
        """
        urls = self._load_urls()
        return urls.get(person_name)
    
    def get_all_linkedin_urls(self) -> Dict[str, str]:
        """
        Get all saved LinkedIn URLs
        
        Returns:
            Dictionary mapping person names to LinkedIn URLs
        """
        return self._load_urls()
    
    def remove_linkedin_url(self, person_name: str):
        """Remove LinkedIn URL for a person"""
        urls = self._load_urls()
        if person_name in urls:
            del urls[person_name]
            self._save_urls(urls)
            print(f"✓ Removed LinkedIn URL for {person_name}")
    
    def cache_profile_data(self, person_name: str, profile_data: dict):
        """
        Cache LinkedIn profile data for a person
        
        Args:
            person_name: Name of the person
            profile_data: Profile data from LinkedIn
        """
        # Sanitize filename
        safe_name = person_name.lower().replace(' ', '-').replace('/', '-')
        cache_file = self.cache_dir / f"{safe_name}.json"
        
        # Add metadata
        cached_data = {
            "person_name": person_name,
            "cached_at": datetime.now().isoformat(),
            "profile_data": profile_data
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cached_data, f, indent=2)
        
        print(f"✓ Cached LinkedIn profile for {person_name}")
    
    def get_cached_profile(self, person_name: str) -> Optional[dict]:
        """
        Get cached LinkedIn profile data
        
        Args:
            person_name: Name of the person
            
        Returns:
            Cached profile data or None if not cached
        """
        # Sanitize filename
        safe_name = person_name.lower().replace(' ', '-').replace('/', '-')
        cache_file = self.cache_dir / f"{safe_name}.json"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                # Return just the profile data
                return cached_data.get("profile_data")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️  Error reading cache for {person_name}: {e}")
        
        return None
    
    def clear_cache(self, person_name: str):
        """Clear cached profile data for a person"""
        safe_name = person_name.lower().replace(' ', '-').replace('/', '-')
        cache_file = self.cache_dir / f"{safe_name}.json"
        
        if cache_file.exists():
            cache_file.unlink()
            print(f"✓ Cleared LinkedIn cache for {person_name}")
    
    def get_cache_age(self, person_name: str) -> Optional[str]:
        """Get age of cached data in human-readable format"""
        safe_name = person_name.lower().replace(' ', '-').replace('/', '-')
        cache_file = self.cache_dir / f"{safe_name}.json"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    cached_at = datetime.fromisoformat(cached_data.get("cached_at"))
                    age = datetime.now() - cached_at
                    
                    # Format age
                    if age.days > 0:
                        return f"{age.days} days ago"
                    elif age.seconds > 3600:
                        return f"{age.seconds // 3600} hours ago"
                    else:
                        return f"{age.seconds // 60} minutes ago"
        except Exception:
            pass
        
        return None
