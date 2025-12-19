#!/usr/bin/env python3
"""Quick debug script to see what's happening with Upheal login."""

import asyncio
from upheal_authenticated_scraper import UphealAuthenticatedScraper

async def debug_login():
    # Run with visible browser
    scraper = UphealAuthenticatedScraper(headless=False, verbose=True)

    print("Attempting login with visible browser...")
    print("Watch the browser window to see what's happening")

    result = await scraper.login()

    print(f"\nResult: {result.status}")
    print(f"Error: {result.error_message}")

    # Wait a bit so we can see the final state
    await asyncio.sleep(5)

    return result

if __name__ == "__main__":
    asyncio.run(debug_login())
