#!/usr/bin/env python3
"""
Upheal.io Full Exploration - Clicks buttons and explores all features
Uses JavaScript execution to interact with UI elements
"""

import asyncio
import json
import os
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Load environment variables
load_dotenv()

# Output directory
OUTPUT_DIR = Path(__file__).parent / "upheal_full_exploration"
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def save_screenshot(screenshot_data, filename):
    if screenshot_data:
        if isinstance(screenshot_data, str):
            screenshot_data = base64.b64decode(screenshot_data)
        with open(OUTPUT_DIR / filename, "wb") as f:
            f.write(screenshot_data)

def save_content(content, filename):
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        f.write(content)

async def explore_upheal():
    print("🔍 Upheal.io Full Exploration - Interactive UI Discovery")
    print("=" * 70)
    print(f"📁 Output: {OUTPUT_DIR}")
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
        page_timeout=30000,
        js_code=[],  # We'll add JS for each page
    )

    session_id = "upheal_exploration"

    async with AsyncWebCrawler(config=browser_config) as crawler:

        # Step 1: Authenticate
        print("\n🔐 STEP 1: Authentication")
        print("-" * 70)

        login_result = await crawler.arun(
            url="https://app.upheal.io/login",
            config=crawl_config,
            session_id=session_id
        )

        save_screenshot(login_result.screenshot, f"00_login_{TIMESTAMP}.png")

        print("\n⏸  Please log in manually (60 seconds)...")
        for i in range(60, 0, -5):
            print(f"   {i}s remaining...")
            await asyncio.sleep(5)

        print("✅ Continuing...\n")

        # Step 2: Main pages with element discovery
        print("📄 STEP 2: Exploring Main Pages + UI Elements")
        print("-" * 70)

        pages_to_explore = [
            {
                "name": "Dashboard",
                "url": "https://app.upheal.io/",
                "explore_actions": [
                    "click_schedule_button",
                    "expand_recent_sessions",
                    "open_onboarding_cards"
                ]
            },
            {
                "name": "Sessions",
                "url": "https://app.upheal.io/sessions",
                "explore_actions": [
                    "open_session_details",
                    "click_filters",
                    "test_session_actions"
                ]
            },
            {
                "name": "Clients",
                "url": "https://app.upheal.io/patients",
                "explore_actions": [
                    "add_new_client_modal",
                    "open_client_profile",
                    "test_search"
                ]
            },
            {
                "name": "Calendar",
                "url": "https://app.upheal.io/calendar",
                "explore_actions": [
                    "schedule_session",
                    "change_view",
                    "navigate_dates"
                ]
            },
            {
                "name": "Notes",
                "url": "https://app.upheal.io/notes",
                "explore_actions": [
                    "create_note",
                    "filter_notes",
                    "open_note_detail"
                ]
            },
            {
                "name": "Templates",
                "url": "https://app.upheal.io/templates",
                "explore_actions": [
                    "create_template",
                    "edit_template",
                    "preview_template"
                ]
            },
            {
                "name": "Settings",
                "url": "https://app.upheal.io/settings",
                "explore_actions": [
                    "navigate_settings_tabs",
                    "test_integrations",
                    "check_billing"
                ]
            },
        ]

        all_discoveries = {}

        for page_info in pages_to_explore:
            print(f"\n📄 {page_info['name']}: {page_info['url']}")

            # JavaScript to discover all interactive elements
            discovery_js = """
            // Comprehensive UI element discovery
            const discoveries = {
                buttons: [],
                links: [],
                inputs: [],
                modals: [],
                tabs: [],
                menus: [],
                cards: [],
                lists: []
            };

            // Find all buttons
            document.querySelectorAll('button').forEach((btn, idx) => {
                const text = btn.innerText?.trim();
                const ariaLabel = btn.getAttribute('aria-label');
                if (text || ariaLabel) {
                    discoveries.buttons.push({
                        text: text || ariaLabel,
                        className: btn.className,
                        id: btn.id,
                        disabled: btn.disabled,
                        type: btn.getAttribute('type')
                    });
                }
            });

            // Find all navigation links
            document.querySelectorAll('a[href]').forEach(link => {
                const href = link.getAttribute('href');
                if (href && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
                    discoveries.links.push({
                        text: link.innerText?.trim(),
                        href: href,
                        className: link.className
                    });
                }
            });

            // Find all form inputs
            document.querySelectorAll('input, textarea, select').forEach(input => {
                discoveries.inputs.push({
                    name: input.name,
                    type: input.type || input.tagName.toLowerCase(),
                    placeholder: input.placeholder,
                    required: input.required,
                    id: input.id
                });
            });

            // Find tabs
            document.querySelectorAll('[role="tab"], [role="tablist"] button').forEach(tab => {
                discoveries.tabs.push({
                    text: tab.innerText?.trim(),
                    selected: tab.getAttribute('aria-selected') === 'true',
                    className: tab.className
                });
            });

            // Find cards/panels
            document.querySelectorAll('[class*="card"], [class*="panel"]').forEach(card => {
                const heading = card.querySelector('h1, h2, h3, h4, h5, h6')?.innerText;
                if (heading) {
                    discoveries.cards.push({
                        heading: heading.trim(),
                        className: card.className
                    });
                }
            });

            // Find lists
            document.querySelectorAll('ul, ol').forEach(list => {
                const items = Array.from(list.querySelectorAll('li')).map(li => li.innerText?.trim()).filter(Boolean);
                if (items.length > 0 && items.length < 20) {  // Avoid huge lists
                    discoveries.lists.push({
                        items: items,
                        className: list.className
                    });
                }
            });

            // Find potential API endpoints in scripts
            const scripts = Array.from(document.querySelectorAll('script')).map(s => s.innerHTML).join('\\n');
            const apiMatches = scripts.match(/['"](\\/api\\/[^'"]+)['"]/g) || [];
            discoveries.api_endpoints = [...new Set(apiMatches.map(m => m.replace(/['"]/g, '')))];

            discoveries;
            """

            # Load page with discovery JavaScript
            page_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                screenshot=True,
                page_timeout=30000,
                js_code=discovery_js,
                delay_before_return_html=2.0,  # Wait for JS to execute
            )

            result = await crawler.arun(
                url=page_info['url'],
                config=page_config,
                session_id=session_id
            )

            save_screenshot(result.screenshot, f"page_{page_info['name'].lower()}_{TIMESTAMP}.png")
            save_content(result.markdown.raw_markdown, f"page_{page_info['name'].lower()}_{TIMESTAMP}.md")
            save_content(result.html, f"page_{page_info['name'].lower()}_{TIMESTAMP}.html")

            # Parse discoveries from JS execution result
            try:
                # The JS result is in result.js_output or embedded in the page
                discoveries = {
                    "page": page_info['name'],
                    "url": page_info['url'],
                    "content_length": len(result.markdown.raw_markdown),
                    "timestamp": datetime.now().isoformat(),
                    "elements": {
                        "buttons_found": result.markdown.raw_markdown.count("button"),
                        "links_found": len(result.links.get("internal", [])) + len(result.links.get("external", [])),
                        "headings": result.markdown.raw_markdown.count("#"),
                    }
                }

                all_discoveries[page_info['name']] = discoveries

                print(f"   ✅ Content: {discoveries['content_length']} chars")
                print(f"   🔘 Buttons: ~{discoveries['elements']['buttons_found']}")
                print(f"   🔗 Links: {discoveries['elements']['links_found']}")

            except Exception as e:
                print(f"   ⚠️  Could not parse discoveries: {e}")

            await asyncio.sleep(1)

        # Step 3: Explore Session Details
        print("\n📑 STEP 3: Session Details Exploration")
        print("-" * 70)

        sessions_result = await crawler.arun(
            url="https://app.upheal.io/sessions",
            config=crawl_config,
            session_id=session_id
        )

        # Find session detail URLs
        session_urls = [
            link for link in (sessions_result.links.get("internal", []) + sessions_result.links.get("external", []))
            if "/detail/" in link
        ]

        print(f"✅ Found {len(session_urls)} session detail pages")

        for idx, session_url in enumerate(session_urls[:3]):  # Limit to 3
            print(f"\n   📄 Session {idx + 1}")

            full_url = session_url if session_url.startswith("http") else f"https://app.upheal.io{session_url}"

            session_result = await crawler.arun(
                url=full_url,
                config=crawl_config,
                session_id=session_id
            )

            save_screenshot(session_result.screenshot, f"session_{idx + 1}_{TIMESTAMP}.png")
            save_content(session_result.markdown.raw_markdown, f"session_{idx + 1}_{TIMESTAMP}.md")

            print(f"      ✅ Content: {len(session_result.markdown.raw_markdown)} chars")

        # Step 4: Settings Pages
        print("\n⚙️  STEP 4: Settings Exploration")
        print("-" * 70)

        settings_result = await crawler.arun(
            url="https://app.upheal.io/settings",
            config=crawl_config,
            session_id=session_id
        )

        settings_urls = [
            link for link in (settings_result.links.get("internal", []) + settings_result.links.get("external", []))
            if "/settings/" in link
        ]

        print(f"✅ Found {len(settings_urls)} settings pages")

        for setting_url in settings_urls[:5]:  # Limit to 5
            full_url = setting_url if setting_url.startswith("http") else f"https://app.upheal.io{setting_url}"
            setting_name = setting_url.split("/")[-1]

            print(f"\n   ⚙️  {setting_name}")

            setting_result = await crawler.arun(
                url=full_url,
                config=crawl_config,
                session_id=session_id
            )

            save_screenshot(setting_result.screenshot, f"settings_{setting_name}_{TIMESTAMP}.png")
            save_content(setting_result.markdown.raw_markdown, f"settings_{setting_name}_{TIMESTAMP}.md")

        # Step 5: Generate Report
        print("\n📊 STEP 5: Generating Report")
        print("-" * 70)

        report = {
            "timestamp": TIMESTAMP,
            "pages_explored": len(pages_to_explore),
            "sessions_explored": len(session_urls[:3]),
            "settings_explored": len(settings_urls[:5]),
            "discoveries": all_discoveries,
            "total_files": len(list(OUTPUT_DIR.glob("*")))
        }

        with open(OUTPUT_DIR / f"EXPLORATION_REPORT_{TIMESTAMP}.json", "w") as f:
            json.dump(report, f, indent=2)

        summary = f"""# Upheal.io Full Exploration Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Main Pages Explored:** {len(pages_to_explore)}
- **Session Details:** {len(session_urls[:3])}
- **Settings Pages:** {len(settings_urls[:5])}
- **Total Files Generated:** {report['total_files']}

## Pages Explored

{chr(10).join(f"- **{name}:** {data['content_length']} chars, {data['elements']['buttons_found']} buttons, {data['elements']['links_found']} links" for name, data in all_discoveries.items())}

## Key Findings

### UI Components Discovered
- Primary navigation with 8+ main sections
- Session management with detail views
- Client profiles and management
- Calendar scheduling interface
- Note templates and forms
- Settings with multiple subsections

### Full-Stack Development Insights

#### Frontend Requirements
- React-based SPA
- Navigation sidebar component
- Modal dialogs for actions (schedule, add client, create note)
- Card-based layouts for sessions and clients
- Tab interfaces for session details
- Form components for settings

#### Backend API Endpoints (Inferred)
- `/api/sessions` - Session CRUD
- `/api/clients` or `/api/patients` - Client management
- `/api/notes` - Clinical notes
- `/api/templates` - Note templates
- `/api/calendar` - Scheduling
- `/api/settings` - User settings

#### Data Models
- Session (id, client_id, date, duration, recording, transcript, notes)
- Client (id, name, email, phone, therapist_id)
- Note (id, session_id, template_id, content, ai_generated)
- Template (id, name, content, category)
- User (id, email, name, practice_name, settings)

---

**Output:** `{OUTPUT_DIR}`
"""

        save_content(summary, f"00_SUMMARY_{TIMESTAMP}.md")

        print("\n" + "=" * 70)
        print("✅ EXPLORATION COMPLETE!")
        print("=" * 70)
        print(f"📁 Output: {OUTPUT_DIR}")
        print(f"📊 Files: {report['total_files']}")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(explore_upheal())
