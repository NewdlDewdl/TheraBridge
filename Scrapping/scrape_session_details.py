#!/usr/bin/env python3
"""
Simple Session Detail Scraper for Upheal Competitive Analysis

This script:
1. Logs into Upheal using existing authenticated scraper
2. Navigates to the sessions list
3. Clicks into the first available session
4. Extracts content from all visible tabs
5. Saves screenshots and markdown for analysis

No over-engineering - just get the data we need for competitive analysis.
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from upheal_authenticated_scraper import UphealAuthenticatedScraper, AuthStatus
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Output directories
OUTPUT_DIR = Path("data/session_detail_scrape")
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"
OUTPUT_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

async def scrape_session_details():
    """Main scraping function - straightforward and sequential."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "timestamp": timestamp,
        "tabs_extracted": [],
        "errors": []
    }

    print("=" * 60)
    print("UPHEAL SESSION DETAIL SCRAPER")
    print("=" * 60)

    # Step 1: Login
    print("\n[1/6] Logging into Upheal...")
    scraper = UphealAuthenticatedScraper()
    auth_result = await scraper.login()

    if auth_result.status != AuthStatus.SUCCESS:
        print(f"❌ Login failed: {auth_result.error_message}")
        results["errors"].append(f"Login failed: {auth_result.error_message}")
        return results

    print("✅ Login successful")

    # Step 2: Navigate to sessions list
    print("\n[2/6] Navigating to sessions list...")
    success, sessions_html, error = await scraper.fetch_protected_page(
        "/sessions",
        wait_for="css:body"
    )

    if not success:
        print(f"❌ Failed to load sessions page: {error}")
        results["errors"].append(f"Sessions page failed: {error}")
        return results

    print("✅ Sessions page loaded")

    # Step 3: Find and navigate to first session
    print("\n[3/6] Looking for first session detail page...")

    # Use the crawler with the authenticated session to click into a session
    async with AsyncWebCrawler(config=scraper.browser_config) as crawler:
        # JavaScript to find and click the first session link
        find_session_js = """
        // Look for session links - try multiple selectors
        const selectors = [
            'a[href*="/sessions/"]',
            '[data-testid*="session"]',
            '.session-item a',
            '.sessions-list a',
            'a[class*="session"]'
        ];

        let sessionLink = null;
        for (const selector of selectors) {
            const links = document.querySelectorAll(selector);
            if (links.length > 0) {
                sessionLink = links[0];
                console.log('FOUND_SESSION_LINK:', sessionLink.href);
                break;
            }
        }

        if (sessionLink) {
            sessionLink.click();
            console.log('CLICKED_SESSION');
        } else {
            console.log('NO_SESSION_FOUND');
        }
        """

        config = CrawlerRunConfig(
            session_id=scraper.session_id,
            js_code=find_session_js,
            wait_for="css:body",
            page_timeout=30000,
            screenshot=True
        )

        result = await crawler.arun(scraper.SESSIONS_URL, config=config)

        if "NO_SESSION_FOUND" in result.html:
            print("❌ No sessions found - account might be empty")
            results["errors"].append("No sessions found on sessions page")
            return results

        # Save the session detail page
        session_url = result.url
        print(f"✅ Navigated to session: {session_url}")

        # Step 4: Extract all visible content (all tabs are likely loaded)
        print("\n[4/6] Extracting session detail content...")

        # Get the current page content (this should have all tabs)
        detail_config = CrawlerRunConfig(
            session_id=scraper.session_id,
            wait_for="css:body",
            page_timeout=30000,
            screenshot=True
        )

        detail_result = await crawler.arun(session_url, config=detail_config)

        # Save full page markdown
        full_content_path = OUTPUT_DIR / f"session_full_content_{timestamp}.md"
        full_content_path.write_text(detail_result.markdown)
        print(f"✅ Saved full page content: {full_content_path}")

        # Save screenshot
        if detail_result.screenshot:
            screenshot_path = SCREENSHOTS_DIR / f"session_page_{timestamp}.png"
            screenshot_path.write_bytes(detail_result.screenshot)
            print(f"✅ Saved screenshot: {screenshot_path}")

        # Save raw HTML for detailed analysis
        html_path = OUTPUT_DIR / f"session_raw_html_{timestamp}.html"
        html_path.write_text(detail_result.html)
        print(f"✅ Saved raw HTML: {html_path}")

        results["tabs_extracted"].append({
            "name": "full_page",
            "url": session_url,
            "markdown_file": str(full_content_path),
            "screenshot_file": str(screenshot_path) if detail_result.screenshot else None,
            "html_file": str(html_path)
        })

        # Step 5: Try to click through tabs if they exist
        print("\n[5/6] Attempting to extract individual tabs...")

        # Common tab names to look for
        tab_names = ["overview", "transcript", "analytics", "session-map", "timeline", "notes"]

        for tab_name in tab_names:
            print(f"  Trying tab: {tab_name}...")

            tab_click_js = f"""
            // Try to find and click the tab
            const tabSelectors = [
                '[data-tab="{tab_name}"]',
                '[role="tab"][aria-label*="{tab_name}"]',
                'button[class*="{tab_name}"]',
                'a[class*="{tab_name}"]',
                '[data-testid*="{tab_name}"]'
            ];

            let tabFound = false;
            for (const selector of tabSelectors) {{
                const tabs = document.querySelectorAll(selector);
                if (tabs.length > 0) {{
                    tabs[0].click();
                    console.log('CLICKED_TAB_{tab_name.upper()}');
                    tabFound = true;
                    break;
                }}
            }}

            if (!tabFound) {{
                console.log('TAB_NOT_FOUND_{tab_name.upper()}');
            }}
            """

            tab_config = CrawlerRunConfig(
                session_id=scraper.session_id,
                js_code=tab_click_js,
                wait_for="css:body",
                page_timeout=15000,
                screenshot=True
            )

            tab_result = await crawler.arun(session_url, config=tab_config)

            if f"CLICKED_TAB_{tab_name.upper()}" in tab_result.html:
                # Tab was found and clicked - save its content
                tab_md_path = OUTPUT_DIR / f"tab_{tab_name}_{timestamp}.md"
                tab_md_path.write_text(tab_result.markdown)

                tab_screenshot_path = None
                if tab_result.screenshot:
                    tab_screenshot_path = SCREENSHOTS_DIR / f"tab_{tab_name}_{timestamp}.png"
                    tab_screenshot_path.write_bytes(tab_result.screenshot)

                results["tabs_extracted"].append({
                    "name": tab_name,
                    "url": session_url,
                    "markdown_file": str(tab_md_path),
                    "screenshot_file": str(tab_screenshot_path) if tab_screenshot_path else None
                })

                print(f"    ✅ Extracted {tab_name} tab")
            else:
                print(f"    ⏭️  {tab_name} tab not found (might not exist)")

    # Step 6: Generate summary report
    print("\n[6/6] Generating analysis report...")

    report_path = OUTPUT_DIR / f"EXTRACTION_SUMMARY_{timestamp}.md"

    report = f"""# Upheal Session Detail Extraction Summary

**Extraction Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Session URL:** {session_url if 'session_url' in locals() else 'N/A'}

## Files Generated

### Full Page Content
- Markdown: `{results['tabs_extracted'][0]['markdown_file'] if results['tabs_extracted'] else 'N/A'}`
- Screenshot: `{results['tabs_extracted'][0]['screenshot_file'] if results['tabs_extracted'] else 'N/A'}`
- Raw HTML: `{results['tabs_extracted'][0]['html_file'] if results['tabs_extracted'] else 'N/A'}`

### Individual Tabs Extracted

"""

    for tab in results['tabs_extracted'][1:]:  # Skip first entry (full page)
        report += f"""#### {tab['name'].title()} Tab
- Markdown: `{tab['markdown_file']}`
- Screenshot: `{tab.get('screenshot_file', 'N/A')}`

"""

    if results['errors']:
        report += "\n## Errors Encountered\n\n"
        for error in results['errors']:
            report += f"- {error}\n"

    report += f"""
## Next Steps for Analysis

1. **Review Full Page Content**: Check `session_full_content_{timestamp}.md` to understand overall structure
2. **Examine Screenshots**: Visual reference for UI patterns in `screenshots/` directory
3. **Analyze HTML**: Parse `session_raw_html_{timestamp}.html` for:
   - CSS classes and component structure
   - Chart library indicators (look for: Chart.js, Recharts, D3.js imports)
   - Tab structure and navigation patterns
4. **Extract UI Patterns**: Identify:
   - Note template field structure
   - Transcript display format (speaker labels, timestamps)
   - Analytics chart types
   - Timeline visualization approach

## Competitive Analysis Focus

Compare Upheal's implementation against TherapyBridge:
- **Note Templates**: Do they use SOAP/DAP/BIRP formats? What fields?
- **Transcript UI**: How are long conversations displayed? Speaker colors?
- **Analytics**: What metrics are visualized? Which chart library?
- **Session Timeline**: How do they show progress over time?
"""

    report_path.write_text(report)
    print(f"✅ Summary report: {report_path}")

    # Save JSON results
    json_path = OUTPUT_DIR / f"extraction_results_{timestamp}.json"
    json_path.write_text(json.dumps(results, indent=2))
    print(f"✅ JSON results: {json_path}")

    print("\n" + "=" * 60)
    print(f"EXTRACTION COMPLETE")
    print(f"Total tabs/content extracted: {len(results['tabs_extracted'])}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    results = asyncio.run(scrape_session_details())

    if results['errors']:
        print("\n⚠️  Some errors occurred during extraction")
        exit(1)
    else:
        print("\n✅ Extraction completed successfully")
        exit(0)
