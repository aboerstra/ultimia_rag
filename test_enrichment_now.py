#!/usr/bin/env python3
"""Test enrichment for Michael now"""

import sys
sys.path.insert(0, 'scripts')

from connectors.linkedin_scraper import LinkedInScraper

scraper = LinkedInScraper()

print("=" * 60)
print("Testing enrichment for Michael Kianmahd...")
print("=" * 60)

result = scraper.fetch_profile("Michael Kianmahd")

print("\nResult:")
print(result)

if result:
    print("\n✅ SUCCESS!")
    print(f"Title: {result.get('title')}")
    print(f"Company: {result.get('company')}")
else:
    print("\n❌ FAILED - returned None")
