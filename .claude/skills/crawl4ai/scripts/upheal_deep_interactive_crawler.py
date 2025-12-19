#!/usr/bin/env python3
"""
Upheal.io Deep Interactive Crawler
Clicks every button, link, and UI element to capture full application behavior.
Discovers API endpoints, state changes, and workflows for full-stack development.
"""

import asyncio
import json
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Load environment variables
load_dotenv()
UPHEAL_EMAIL = os.getenv("UPHEAL_EMAIL")
UPHEAL_PASSWORD = os.getenv("UPHEAL_PASSWORD")

# Output directory
OUTPUT_DIR = Path(__file__).parent / "upheal_interactive_results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Timestamp for this run
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Track all interactions
INTERACTION_LOG = []
DISCOVERED_APIS = []
STATE_CHANGES = []
WORKFLOWS = []

def save_screenshot(screenshot_data, filename):
    """Save base64 screenshot to file"""
    if screenshot_data:
        if isinstance(screenshot_data, str):
            screenshot_data = base64.b64decode(screenshot_data)
        filepath = OUTPUT_DIR / filename
        with open(filepath, "wb") as f:
            f.write(screenshot_data)
        return filepath
    return None

def save_content(content, filename):
    """Save content to file"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath

def log_interaction(interaction_type: str, element: str, url: str, result: Dict[str, Any]):
    """Log UI interactions"""
    INTERACTION_LOG.append({
        "timestamp": datetime.now().isoformat(),
        "type": interaction_type,
        "element": element,
        "url": url,
        "result": result
    })

def detect_api_call(html: str, url: str):
    """Detect potential API calls from page content and network activity"""
    # Look for common API patterns in HTML/JS
    api_patterns = [
        "/api/", "/v1/", "/v2/", "/graphql",
        "fetch(", "axios.", "XMLHttpRequest",
        ".json()", "/sessions", "/clients", "/notes"
    ]

    for pattern in api_patterns:
        if pattern in html:
            DISCOVERED_APIS.append({
                "pattern": pattern,
                "found_in": url,
                "timestamp": datetime.now().isoformat()
            })

async def wait_for_page_load(page, timeout=3000):
    """Wait for page to load completely"""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except:
        await asyncio.sleep(2)  # Fallback wait

async def interactive_crawl():
    """Main interactive crawling function"""

    print("🔍 Upheal.io Deep Interactive Crawler")
    print("=" * 70)
    print("📧 Email:", UPHEAL_EMAIL)
    print("📁 Output:", OUTPUT_DIR)
    print("=" * 70)

    browser_config = BrowserConfig(
        headless=False,
        verbose=True,
        viewport_width=1920,
        viewport_height=1080,
    )

    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        screenshot=True,
        page_timeout=30000,  # 30 second timeout
    )

    session_id = "upheal_interactive_session"

    async with AsyncWebCrawler(config=browser_config) as crawler:

        # Step 1: Authenticate
        print("\n🔐 STEP 1: Manual Authentication")
        print("-" * 70)
        print("Please log in and complete any questionnaires...")

        login_result = await crawler.arun(
            url="https://app.upheal.io/login",
            config=crawl_config,
            session_id=session_id
        )

        save_screenshot(login_result.screenshot, f"00_login_{TIMESTAMP}.png")

        # Wait for manual login
        print("\n⏸  You have 60 seconds to log in manually...")
        for i in range(60, 0, -5):
            print(f"   {i} seconds remaining...")
            await asyncio.sleep(5)

        print("✅ Continuing with interactive crawl...\n")

        # Step 2: Load dashboard and get page handle
        print("📊 STEP 2: Loading Dashboard")
        print("-" * 70)

        dashboard_result = await crawler.arun(
            url="https://app.upheal.io/",
            config=crawl_config,
            session_id=session_id
        )

        save_screenshot(dashboard_result.screenshot, f"01_dashboard_{TIMESTAMP}.png")
        save_content(dashboard_result.markdown.raw_markdown, f"01_dashboard_{TIMESTAMP}.md")

        # Get Playwright page handle
        page = crawler.crawler_strategy.page

        print(f"✅ Dashboard loaded: {len(dashboard_result.markdown.raw_markdown)} chars\n")

        # Step 3: Discover all interactive elements
        print("🔍 STEP 3: Discovering Interactive Elements")
        print("-" * 70)

        # JavaScript to find all interactive elements
        discover_js = """
        () => {
            const elements = [];

            // Find all buttons
            document.querySelectorAll('button').forEach((btn, idx) => {
                const text = btn.innerText?.trim() || btn.getAttribute('aria-label') || '';
                if (text && !btn.disabled) {
                    elements.push({
                        type: 'button',
                        selector: `button:nth-of-type(${idx + 1})`,
                        text: text,
                        id: btn.id || null,
                        class: btn.className || null
                    });
                }
            });

            // Find all links
            document.querySelectorAll('a[href]').forEach((link, idx) => {
                const text = link.innerText?.trim() || '';
                const href = link.getAttribute('href');
                if (text && href && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
                    elements.push({
                        type: 'link',
                        selector: `a[href="${href}"]`,
                        text: text,
                        href: href,
                        id: link.id || null,
                        class: link.className || null
                    });
                }
            });

            // Find all input fields
            document.querySelectorAll('input, textarea, select').forEach((input, idx) => {
                const label = input.labels?.[0]?.innerText || input.placeholder || input.name || '';
                if (label) {
                    elements.push({
                        type: 'input',
                        selector: `${input.tagName.toLowerCase()}[name="${input.name}"]`,
                        text: label,
                        name: input.name || null,
                        inputType: input.type || input.tagName.toLowerCase(),
                        id: input.id || null
                    });
                }
            });

            // Find all tabs/accordions
            document.querySelectorAll('[role="tab"], [role="button"]').forEach((elem, idx) => {
                const text = elem.innerText?.trim() || elem.getAttribute('aria-label') || '';
                if (text) {
                    elements.push({
                        type: 'tab',
                        selector: `[role="${elem.getAttribute('role')}"][aria-label="${elem.getAttribute('aria-label')}"]`,
                        text: text,
                        id: elem.id || null,
                        class: elem.className || null
                    });
                }
            });

            return elements;
        }
        """

        interactive_elements = await page.evaluate(discover_js)

        print(f"✅ Found {len(interactive_elements)} interactive elements:")
        print(f"   - Buttons: {len([e for e in interactive_elements if e['type'] == 'button'])}")
        print(f"   - Links: {len([e for e in interactive_elements if e['type'] == 'link'])}")
        print(f"   - Inputs: {len([e for e in interactive_elements if e['type'] == 'input'])}")
        print(f"   - Tabs: {len([e for e in interactive_elements if e['type'] == 'tab'])}")

        # Save element inventory
        with open(OUTPUT_DIR / f"interactive_elements_{TIMESTAMP}.json", "w") as f:
            json.dump(interactive_elements, f, indent=2)

        # Step 4: Navigate through all main pages
        print("\n📄 STEP 4: Navigating Main Pages")
        print("-" * 70)

        main_pages = [
            ("Dashboard", "https://app.upheal.io/"),
            ("Sessions", "https://app.upheal.io/sessions"),
            ("Clients", "https://app.upheal.io/patients"),
            ("Calendar", "https://app.upheal.io/calendar"),
            ("Notes", "https://app.upheal.io/notes"),
            ("Templates", "https://app.upheal.io/templates"),
            ("Settings", "https://app.upheal.io/settings"),
            ("Profile", "https://app.upheal.io/profile"),
        ]

        page_interactions = {}

        for page_name, page_url in main_pages:
            print(f"\n📄 Exploring: {page_name}")

            result = await crawler.arun(
                url=page_url,
                config=crawl_config,
                session_id=session_id
            )

            save_screenshot(result.screenshot, f"page_{page_name.lower()}_{TIMESTAMP}.png")
            save_content(result.markdown.raw_markdown, f"page_{page_name.lower()}_{TIMESTAMP}.md")

            # Detect API calls
            detect_api_call(result.html, page_url)

            # Wait for page to settle
            await wait_for_page_load(page)

            # Discover elements on this page
            elements = await page.evaluate(discover_js)
            page_interactions[page_name] = {
                "url": page_url,
                "elements_count": len(elements),
                "elements": elements,
                "content_length": len(result.markdown.raw_markdown)
            }

            print(f"   ✅ {len(elements)} interactive elements found")

            # Step 5: Click on key buttons to discover modals/dialogs
            print(f"   🖱️  Testing key interactions...")

            # Try to find and click common action buttons
            action_keywords = ["new", "add", "create", "schedule", "edit", "settings", "upload"]

            for elem in elements[:10]:  # Limit to first 10 to avoid endless clicking
                if elem['type'] == 'button':
                    text_lower = elem['text'].lower()
                    if any(keyword in text_lower for keyword in action_keywords):
                        try:
                            print(f"      🔘 Clicking: {elem['text']}")

                            # Get page state before click
                            before_url = page.url

                            # Try to click the element
                            if elem.get('id'):
                                await page.click(f"#{elem['id']}", timeout=2000)
                            else:
                                await page.click(f"button:has-text('{elem['text']}')", timeout=2000)

                            # Wait for any modals/changes
                            await asyncio.sleep(1)

                            # Capture after state
                            after_screenshot = await page.screenshot()
                            save_screenshot(after_screenshot, f"interaction_{page_name.lower()}_{elem['text'].replace(' ', '_')}_{TIMESTAMP}.png")

                            after_url = page.url

                            # Check if modal appeared
                            modal_check_js = """
                            () => {
                                const modals = document.querySelectorAll('[role="dialog"], .modal, .popup, [class*="modal"]');
                                return Array.from(modals).map(m => ({
                                    text: m.innerText?.substring(0, 200),
                                    class: m.className,
                                    visible: m.offsetParent !== null
                                }));
                            }
                            """
                            modals = await page.evaluate(modal_check_js)

                            log_interaction(
                                "button_click",
                                elem['text'],
                                page_url,
                                {
                                    "before_url": before_url,
                                    "after_url": after_url,
                                    "modals_appeared": len([m for m in modals if m['visible']]),
                                    "navigation_occurred": before_url != after_url
                                }
                            )

                            # Close modal if appeared (press Escape)
                            await page.keyboard.press("Escape")
                            await asyncio.sleep(0.5)

                            # Return to original page if navigated away
                            if before_url != after_url:
                                await page.goto(before_url)
                                await wait_for_page_load(page)

                        except Exception as e:
                            print(f"         ⚠️  Could not click: {e}")

            # Small delay between pages
            await asyncio.sleep(1)

        # Step 6: Explore session details (if available)
        print("\n📑 STEP 5: Exploring Session Details")
        print("-" * 70)

        sessions_result = await crawler.arun(
            url="https://app.upheal.io/sessions",
            config=crawl_config,
            session_id=session_id
        )

        await wait_for_page_load(page)

        # Find session detail links
        session_links_js = """
        () => {
            const links = [];
            document.querySelectorAll('a[href*="/detail/"]').forEach(link => {
                links.push({
                    text: link.innerText?.trim().substring(0, 100),
                    href: link.getAttribute('href')
                });
            });
            return links;
        }
        """

        session_links = await page.evaluate(session_links_js)

        print(f"✅ Found {len(session_links)} session detail pages")

        for idx, link in enumerate(session_links[:3]):  # Limit to 3 sessions
            print(f"\n   📄 Session {idx + 1}: {link['text'][:50]}...")

            full_url = f"https://app.upheal.io{link['href']}" if link['href'].startswith('/') else link['href']

            session_result = await crawler.arun(
                url=full_url,
                config=crawl_config,
                session_id=session_id
            )

            save_screenshot(session_result.screenshot, f"session_detail_{idx + 1}_{TIMESTAMP}.png")
            save_content(session_result.markdown.raw_markdown, f"session_detail_{idx + 1}_{TIMESTAMP}.md")

            await wait_for_page_load(page)

            # Find tabs/sections in session detail
            tabs_js = """
            () => {
                const tabs = [];
                document.querySelectorAll('[role="tab"], [role="tablist"] button').forEach(tab => {
                    tabs.push({
                        text: tab.innerText?.trim(),
                        selected: tab.getAttribute('aria-selected') === 'true'
                    });
                });
                return tabs;
            }
            """

            tabs = await page.evaluate(tabs_js)

            if tabs:
                print(f"      📑 Found {len(tabs)} tabs: {', '.join([t['text'] for t in tabs])}")

                # Click each tab to see content
                for tab in tabs:
                    try:
                        await page.click(f"button:has-text('{tab['text']}')", timeout=2000)
                        await asyncio.sleep(1)

                        tab_screenshot = await page.screenshot()
                        save_screenshot(tab_screenshot, f"session_{idx + 1}_tab_{tab['text'].replace(' ', '_')}_{TIMESTAMP}.png")

                        print(f"         ✅ Captured tab: {tab['text']}")
                    except Exception as e:
                        print(f"         ⚠️  Could not click tab: {e}")

            detect_api_call(session_result.html, full_url)

        # Step 7: Explore Settings subpages
        print("\n⚙️  STEP 6: Exploring Settings")
        print("-" * 70)

        settings_result = await crawler.arun(
            url="https://app.upheal.io/settings",
            config=crawl_config,
            session_id=session_id
        )

        await wait_for_page_load(page)

        # Find settings navigation
        settings_nav_js = """
        () => {
            const navItems = [];
            document.querySelectorAll('nav a, [role="navigation"] a, aside a').forEach(link => {
                const href = link.getAttribute('href');
                if (href && href.startsWith('/settings/')) {
                    navItems.push({
                        text: link.innerText?.trim(),
                        href: href
                    });
                }
            });
            return navItems;
        }
        """

        settings_pages = await page.evaluate(settings_nav_js)

        print(f"✅ Found {len(settings_pages)} settings pages")

        for setting in settings_pages[:5]:  # Limit to 5 settings pages
            print(f"\n   ⚙️  {setting['text']}")

            full_url = f"https://app.upheal.io{setting['href']}"

            setting_result = await crawler.arun(
                url=full_url,
                config=crawl_config,
                session_id=session_id
            )

            safe_name = setting['text'].replace(' ', '_').replace('/', '_')
            save_screenshot(setting_result.screenshot, f"settings_{safe_name}_{TIMESTAMP}.png")
            save_content(setting_result.markdown.raw_markdown, f"settings_{safe_name}_{TIMESTAMP}.md")

            detect_api_call(setting_result.html, full_url)

        # Step 8: Generate comprehensive report
        print("\n📊 STEP 7: Generating Comprehensive Report")
        print("-" * 70)

        report = {
            "crawl_timestamp": TIMESTAMP,
            "email": UPHEAL_EMAIL,
            "statistics": {
                "pages_visited": len(main_pages) + len(session_links[:3]) + len(settings_pages[:5]),
                "interactive_elements_found": len(interactive_elements),
                "interactions_performed": len(INTERACTION_LOG),
                "api_patterns_discovered": len(set([a['pattern'] for a in DISCOVERED_APIS])),
            },
            "page_interactions": page_interactions,
            "session_details_explored": len(session_links[:3]),
            "settings_pages_explored": len(settings_pages[:5]),
            "interaction_log": INTERACTION_LOG,
            "discovered_api_patterns": DISCOVERED_APIS,
            "all_interactive_elements": interactive_elements
        }

        # Save comprehensive report
        with open(OUTPUT_DIR / f"COMPREHENSIVE_REPORT_{TIMESTAMP}.json", "w") as f:
            json.dump(report, f, indent=2)

        # Generate markdown summary
        summary = f"""# Upheal.io Deep Interactive Crawl Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistics

- **Pages Visited:** {report['statistics']['pages_visited']}
- **Interactive Elements Found:** {report['statistics']['interactive_elements_found']}
- **Interactions Performed:** {report['statistics']['interactions_performed']}
- **API Patterns Discovered:** {report['statistics']['api_patterns_discovered']}

## Pages Explored

### Main Application Pages
{chr(10).join(f'- {name}: {data["elements_count"]} interactive elements, {data["content_length"]} chars' for name, data in page_interactions.items())}

### Session Details Explored
- {len(session_links[:3])} session detail pages with tabs

### Settings Pages Explored
- {len(settings_pages[:5])} settings subpages

## Interactive Elements Breakdown

- **Buttons:** {len([e for e in interactive_elements if e['type'] == 'button'])}
- **Links:** {len([e for e in interactive_elements if e['type'] == 'link'])}
- **Input Fields:** {len([e for e in interactive_elements if e['type'] == 'input'])}
- **Tabs:** {len([e for e in interactive_elements if e['type'] == 'tab'])}

## API Patterns Discovered

{chr(10).join(f'- `{pattern}`' for pattern in set([a['pattern'] for a in DISCOVERED_APIS]))}

## Key Interactions Performed

{chr(10).join(f'- {i["type"]}: {i["element"]} on {i["url"]}' for i in INTERACTION_LOG[:20])}

## Files Generated

- Screenshots: {len(list(OUTPUT_DIR.glob('*.png')))} files
- Content files: {len(list(OUTPUT_DIR.glob('*.md')))} files
- JSON reports: {len(list(OUTPUT_DIR.glob('*.json')))} files

## Next Steps for Full-Stack Development

1. **Review interaction log** to understand user workflows
2. **Analyze API patterns** to design backend endpoints
3. **Study modal interactions** to implement dynamic UI components
4. **Examine session detail tabs** to understand data structure
5. **Review settings pages** for configuration requirements

---

**Output Directory:** `{OUTPUT_DIR}`
"""

        save_content(summary, f"00_SUMMARY_{TIMESTAMP}.md")

        print("\n" + "=" * 70)
        print("✅ DEEP INTERACTIVE CRAWL COMPLETE!")
        print("=" * 70)
        print(f"📁 Output: {OUTPUT_DIR}")
        print(f"📊 Pages visited: {report['statistics']['pages_visited']}")
        print(f"🔘 Interactions: {report['statistics']['interactions_performed']}")
        print(f"📄 Files generated: {len(list(OUTPUT_DIR.glob('*')))}")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(interactive_crawl())
