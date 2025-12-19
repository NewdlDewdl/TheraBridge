#!/usr/bin/env python3
"""
Ultra-simple session scraper - directly target the known session URLs.

Since we know the session URLs from previous scrapes, just go directly there
and extract all the content we can see.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Known session detail URLs from previous scrape
SESSION_URLS = [
    "https://app.upheal.io/detail/c9289f16-7f34-4d07-9497-96243334f68f/b88886ba-f023-49d0-9972-9a51fb6e9244",  # Rhonda García
    "https://app.upheal.io/detail/b83dc32e-58c9-4c43-ad16-338a5f331c95/5b4aa0cb-9f10-405a-b7ff-e34ea54e5071"   # Tony Pasano
]

# Output directory
OUTPUT_DIR = Path("data/session_scrape_direct")
OUTPUT_DIR.mkdir(exist_ok=True)

async def scrape_session(url: str, session_name: str):
    """Scrape a single session detail page."""

    print(f"\n{'='*60}")
    print(f"Scraping: {session_name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    browser_config = BrowserConfig(
        headless=False,  # Visible so we can see what's happening
        viewport_width=1920,
        viewport_height=1080,
        verbose=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First attempt - just load the page and wait
        print("\n[1] Loading session page...")

        config = CrawlerRunConfig(
            session_id="upheal_direct_session",  # Consistent session
            wait_for="css:body",
            page_timeout=30000,
            screenshot=True,
            delay_before_return_html=3000  # Wait 3 seconds for content to load
        )

        result = await crawler.arun(url, config=config)

        # Save initial page load
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        md_file = OUTPUT_DIR / f"{session_name}_initial_{timestamp}.md"
        md_file.write_text(result.markdown)
        print(f"✅ Saved markdown: {md_file}")

        html_file = OUTPUT_DIR / f"{session_name}_initial_{timestamp}.html"
        html_file.write_text(result.html)
        print(f"✅ Saved HTML: {html_file}")

        if result.screenshot:
            screenshot_file = OUTPUT_DIR / f"{session_name}_initial_{timestamp}.png"
            screenshot_file.write_bytes(result.screenshot)
            print(f"✅ Saved screenshot: {screenshot_file}")

        # Try clicking through tabs if we can find them
        print("\n[2] Looking for tabs...")

        # JavaScript to find and log tab structure
        tab_discovery_js = """
        const tabs = document.querySelectorAll('[role="tab"], button[class*="tab"], a[class*="tab"]');
        console.log('FOUND_TABS:', tabs.length);

        tabs.forEach((tab, i) => {
            console.log(`TAB_${i}:`, tab.textContent.trim(), '|', tab.getAttribute('data-tab') || tab.className);
        });

        // Return count for detection
        tabs.length;
        """

        config2 = CrawlerRunConfig(
            session_id="upheal_direct_session",
            js_code=tab_discovery_js,
            wait_for="css:body",
            page_timeout=15000,
            screenshot=True
        )

        result2 = await crawler.arun(url, config=config2)

        # Save this too
        md_file2 = OUTPUT_DIR / f"{session_name}_with_tabs_{timestamp}.md"
        md_file2.write_text(result2.markdown)

        if result2.screenshot:
            screenshot_file2 = OUTPUT_DIR / f"{session_name}_with_tabs_{timestamp}.png"
            screenshot_file2.write_bytes(result2.screenshot)

        print(f"✅ Tab discovery complete")

        return {
            "url": url,
            "session_name": session_name,
            "files": {
                "markdown": str(md_file),
                "markdown_tabs": str(md_file2),
                "html": str(html_file),
                "screenshot": str(screenshot_file) if result.screenshot else None,
                "screenshot_tabs": str(screenshot_file2) if result2.screenshot else None
            }
        }

async def main():
    """Scrape all known session URLs."""

    print("="*60)
    print("DIRECT SESSION SCRAPER")
    print("="*60)
    print(f"\nTarget sessions: {len(SESSION_URLS)}")
    print(f"Output directory: {OUTPUT_DIR}")

    results = []

    for i, url in enumerate(SESSION_URLS, 1):
        session_name = f"session_{i}"
        try:
            result = await scrape_session(url, session_name)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error scraping {session_name}: {e}")
            results.append({
                "url": url,
                "session_name": session_name,
                "error": str(e)
            })

    # Save summary
    summary_file = OUTPUT_DIR / "scrape_summary.json"
    summary_file.write_text(json.dumps(results, indent=2))

    print("\n" + "="*60)
    print("SCRAPING COMPLETE")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
