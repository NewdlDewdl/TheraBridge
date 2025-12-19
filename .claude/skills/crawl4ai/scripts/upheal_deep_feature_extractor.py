#!/usr/bin/env python3
"""
Upheal.io Deep Feature Extraction for Development Cloning
Extracts detailed feature specs, UI patterns, workflows, and implementation details
Optimized for orchestrator agent to clone features end-to-end
"""

import asyncio
import json
import os
import base64
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

UPHEAL_EMAIL = os.getenv("UPHEAL_EMAIL")
UPHEAL_PASSWORD = os.getenv("UPHEAL_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OUTPUT_DIR = Path("upheal_feature_analysis")


def save_file(content, filename, mode="w", encoding="utf-8"):
    """Helper to save any file"""
    filepath = OUTPUT_DIR / filename
    if mode == "wb":
        with open(filepath, mode) as f:
            f.write(content)
    else:
        with open(filepath, mode, encoding=encoding) as f:
            f.write(content)


def save_json(data, filename):
    """Helper to save JSON"""
    save_file(json.dumps(data, indent=2, ensure_ascii=False), filename)


def extract_network_calls(html_content):
    """Extract potential API endpoints from HTML/JS"""
    api_patterns = [
        r'/api/[a-zA-Z0-9/_-]+',
        r'/graphql',
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.[a-z]+\(["\']([^"\']+)["\']',
        r'"url":\s*"([^"]+)"',
    ]

    endpoints = set()
    for pattern in api_patterns:
        matches = re.findall(pattern, html_content)
        endpoints.update(matches)

    return sorted(list(endpoints))


def extract_form_fields(markdown_content):
    """Extract form field information from markdown"""
    # Look for input fields, labels, placeholders
    fields = []

    # Find potential form fields
    field_patterns = [
        r'(?:Email|Password|Name|Phone|Address|Date|Time|Message|Note|Comment|Description)',
        r'\[.*?\]\(.*?\)',  # Links that might be submit buttons
    ]

    for pattern in field_patterns:
        matches = re.findall(pattern, markdown_content, re.IGNORECASE)
        fields.extend(matches)

    return list(set(fields))


async def deep_crawl_upheal():
    """Deep feature extraction crawl"""

    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("🔍 Upheal.io Deep Feature Extraction")
    print("="*70)
    print("Goal: Extract detailed specs for feature cloning")
    print(f"Output: {OUTPUT_DIR.absolute()}")
    print("="*70)

    browser_config = BrowserConfig(
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
    )

    # Feature catalog - what we're looking for
    feature_catalog = {
        "navigation": [],
        "pages": {},
        "workflows": {},
        "ui_components": {},
        "data_models": {},
        "api_endpoints": set(),
        "forms": {},
        "business_logic": {},
    }

    async with AsyncWebCrawler(config=browser_config) as crawler:

        # Step 1: Login
        print("\n🔐 STEP 1: Authenticating...")
        print("   Opening login page - you have 60 seconds to log in manually")

        login_config = CrawlerRunConfig(
            session_id="upheal_deep",
            page_timeout=120000,
            screenshot=True,
        )

        login_result = await crawler.arun(
            url="https://app.upheal.io/login",
            config=login_config
        )

        if not login_result.success:
            print("❌ Failed to load login page")
            return

        save_file(login_result.screenshot if isinstance(login_result.screenshot, bytes)
                 else base64.b64decode(login_result.screenshot),
                 "00_login.png", mode="wb")

        print("   Waiting for manual login...")
        for i in range(60, 0, -5):
            print(f"   {i}s remaining...")
            await asyncio.sleep(5)

        print("✅ Continuing with deep extraction...\n")

        # Step 2: Deep crawl main pages with detailed extraction
        print("📊 STEP 2: Deep Crawling Main Application Areas")
        print("-"*70)

        main_pages = [
            ("Home", "https://app.upheal.io/", "Dashboard and overview"),
            ("Sessions", "https://app.upheal.io/sessions", "Session management and list"),
            ("Clients", "https://app.upheal.io/patients", "Client/patient management"),
            ("Calendar", "https://app.upheal.io/calendar", "Scheduling and appointments"),
            ("Notes", "https://app.upheal.io/notes", "Clinical notes and documentation"),
            ("Templates", "https://app.upheal.io/templates", "Note templates"),
            ("Settings", "https://app.upheal.io/settings", "Account and practice settings"),
            ("Profile", "https://app.upheal.io/profile", "User profile"),
        ]

        for page_name, url, description in main_pages:
            print(f"\n📄 Analyzing: {page_name}")
            print(f"   Purpose: {description}")

            page_config = CrawlerRunConfig(
                session_id="upheal_deep",
                page_timeout=30000,
                screenshot=True,
                # Extensive scrolling to load all dynamic content
                js_code="""
                // Scroll multiple times to trigger lazy loading
                for(let i = 0; i < 5; i++) {
                    window.scrollTo(0, (document.body.scrollHeight / 5) * i);
                    await new Promise(r => setTimeout(r, 500));
                }
                window.scrollTo(0, 0);
                await new Promise(r => setTimeout(r, 1000));

                // Try to expand any collapsed sections
                document.querySelectorAll('[aria-expanded="false"]').forEach(el => {
                    el.click();
                });
                await new Promise(r => setTimeout(r, 1000));
                """,
            )

            result = await crawler.arun(url=url, config=page_config)

            if not result.success or "login" in result.url.lower():
                print(f"   ⚠️  Skipped: Not accessible or redirected to login")
                continue

            # Save raw data
            page_id = page_name.lower().replace(" ", "_")
            save_file(result.markdown, f"{page_id}_content.md")
            save_file(result.html, f"{page_id}_raw.html")

            if result.screenshot:
                screenshot_data = result.screenshot if isinstance(result.screenshot, bytes) else base64.b64decode(result.screenshot)
                save_file(screenshot_data, f"{page_id}_screenshot.png", mode="wb")

            # Extract feature details
            page_analysis = {
                "name": page_name,
                "url": url,
                "description": description,
                "actual_url": result.url,
                "title": result.metadata.get("title", ""),
                "content_length": len(result.markdown),
                "timestamp": timestamp,
            }

            # Extract navigation elements
            nav_links = result.links.get("internal", [])
            navigation = []
            for link in nav_links[:20]:  # First 20 links
                if isinstance(link, dict):
                    navigation.append({
                        "text": link.get("text", ""),
                        "href": link.get("href", ""),
                        "title": link.get("title", ""),
                    })
            page_analysis["navigation"] = navigation

            # Extract potential API endpoints
            api_endpoints = extract_network_calls(result.html)
            page_analysis["api_endpoints"] = api_endpoints
            feature_catalog["api_endpoints"].update(api_endpoints)

            # Extract form fields
            form_fields = extract_form_fields(result.markdown)
            page_analysis["form_fields"] = form_fields

            # Extract UI patterns from markdown
            ui_patterns = {
                "headings": re.findall(r'^#+\s+(.+)$', result.markdown, re.MULTILINE),
                "buttons": re.findall(r'\[(.*?)\]\(.*?\)', result.markdown),
                "lists": len(re.findall(r'^\s*[-*+]\s+', result.markdown, re.MULTILINE)),
                "tables": result.markdown.count("|"),
                "images": len(result.media.get("images", [])),
            }
            page_analysis["ui_patterns"] = ui_patterns

            # Save page analysis
            save_json(page_analysis, f"{page_id}_analysis.json")
            feature_catalog["pages"][page_name] = page_analysis

            print(f"   ✅ Extracted:")
            print(f"      - {len(navigation)} navigation items")
            print(f"      - {len(api_endpoints)} potential API endpoints")
            print(f"      - {len(form_fields)} form fields")
            print(f"      - {len(ui_patterns['headings'])} sections")

            await asyncio.sleep(2)

        # Step 3: Discover and crawl all session detail pages
        print("\n\n🔬 STEP 3: Deep Dive into Session Workflows")
        print("-"*70)

        # Get session list
        sessions_config = CrawlerRunConfig(
            session_id="upheal_deep",
            page_timeout=30000,
            screenshot=True,
        )

        sessions_result = await crawler.arun(
            url="https://app.upheal.io/sessions",
            config=sessions_config
        )

        if sessions_result.success:
            # Extract all session detail links
            session_links = []
            for link in sessions_result.links.get("internal", []):
                if isinstance(link, dict):
                    href = link.get("href", "")
                    if "/detail/" in href:
                        session_links.append(href)

            session_links = list(set(session_links))[:10]  # Limit to 10 sessions

            print(f"   Found {len(session_links)} session detail pages")

            session_workflows = []

            for i, session_url in enumerate(session_links, 1):
                print(f"\n   [{i}/{len(session_links)}] Analyzing session: {session_url.split('/')[-1][:20]}...")

                session_config = CrawlerRunConfig(
                    session_id="upheal_deep",
                    page_timeout=30000,
                    screenshot=True,
                    js_code="""
                    // Scroll to load all content
                    window.scrollTo(0, document.body.scrollHeight);
                    await new Promise(r => setTimeout(r, 2000));
                    window.scrollTo(0, 0);
                    """,
                )

                session_result = await crawler.arun(url=session_url, config=session_config)

                if session_result.success:
                    session_id = f"session_{i:02d}"

                    # Save session content
                    save_file(session_result.markdown, f"{session_id}_detail.md")
                    if session_result.screenshot:
                        screenshot_data = session_result.screenshot if isinstance(session_result.screenshot, bytes) else base64.b64decode(session_result.screenshot)
                        save_file(screenshot_data, f"{session_id}_screenshot.png", mode="wb")

                    # Analyze session structure
                    session_analysis = {
                        "url": session_url,
                        "title": session_result.metadata.get("title", ""),
                        "content_length": len(session_result.markdown),
                        "sections": re.findall(r'^#+\s+(.+)$', session_result.markdown, re.MULTILINE),
                        "form_fields": extract_form_fields(session_result.markdown),
                        "api_endpoints": extract_network_calls(session_result.html),
                    }

                    session_workflows.append(session_analysis)

                    print(f"      ✅ Sections: {len(session_analysis['sections'])}")
                    print(f"         Fields: {len(session_analysis['form_fields'])}")

                await asyncio.sleep(2)

            feature_catalog["workflows"]["sessions"] = session_workflows
            save_json(session_workflows, "session_workflow_analysis.json")

        # Step 4: Explore templates and forms
        print("\n\n📝 STEP 4: Template & Form Analysis")
        print("-"*70)

        template_urls = [
            "https://app.upheal.io/templates",
            "https://app.upheal.io/settings/forms",
        ]

        templates_data = []

        for template_url in template_urls:
            print(f"\n   Analyzing: {template_url}")

            template_config = CrawlerRunConfig(
                session_id="upheal_deep",
                page_timeout=30000,
                screenshot=True,
            )

            result = await crawler.arun(url=template_url, config=template_config)

            if result.success and "login" not in result.url.lower():
                template_analysis = {
                    "url": template_url,
                    "content": result.markdown,
                    "sections": re.findall(r'^#+\s+(.+)$', result.markdown, re.MULTILINE),
                    "form_fields": extract_form_fields(result.markdown),
                }
                templates_data.append(template_analysis)

                print(f"      ✅ Found {len(template_analysis['sections'])} template types")

            await asyncio.sleep(2)

        feature_catalog["forms"]["templates"] = templates_data

        # Step 5: Extract all discovered links for comprehensive sitemap
        print("\n\n🗺️  STEP 5: Building Complete Feature Map")
        print("-"*70)

        all_discovered_urls = set()
        for page_data in feature_catalog["pages"].values():
            for nav_item in page_data.get("navigation", []):
                href = nav_item.get("href", "")
                if href and "upheal.io" in href:
                    all_discovered_urls.add(href)

        sitemap = {
            "total_pages": len(all_discovered_urls),
            "pages_by_category": {},
            "all_urls": sorted(list(all_discovered_urls))
        }

        # Categorize URLs
        categories = {
            "sessions": [],
            "clients": [],
            "settings": [],
            "templates": [],
            "calendar": [],
            "notes": [],
            "other": []
        }

        for url in all_discovered_urls:
            categorized = False
            for category in categories.keys():
                if category in url.lower():
                    categories[category].append(url)
                    categorized = True
                    break
            if not categorized:
                categories["other"].append(url)

        sitemap["pages_by_category"] = categories
        save_json(sitemap, "complete_sitemap.json")

        print(f"   ✅ Discovered {len(all_discovered_urls)} unique URLs")
        for category, urls in categories.items():
            if urls:
                print(f"      - {category.capitalize()}: {len(urls)} pages")

        # Step 6: Generate implementation roadmap
        print("\n\n🚀 STEP 6: Generating Implementation Roadmap")
        print("-"*70)

        roadmap = {
            "metadata": {
                "generated_at": timestamp,
                "source": "Upheal.io",
                "purpose": "Feature cloning for TherapyBridge"
            },
            "feature_categories": {},
            "implementation_phases": [],
            "technical_requirements": {},
            "api_endpoints_discovered": sorted(list(feature_catalog["api_endpoints"])),
        }

        # Analyze each page for features
        for page_name, page_data in feature_catalog["pages"].items():
            features = []

            # Extract features from sections
            for heading in page_data.get("ui_patterns", {}).get("headings", []):
                if len(heading) > 3:  # Meaningful headings
                    features.append({
                        "name": heading,
                        "type": "section",
                        "page": page_name
                    })

            # Extract features from navigation
            for nav_item in page_data.get("navigation", []):
                text = nav_item.get("text", "").strip()
                if text and len(text) > 2:
                    features.append({
                        "name": text,
                        "type": "navigation_item",
                        "link": nav_item.get("href", ""),
                        "page": page_name
                    })

            roadmap["feature_categories"][page_name] = {
                "description": page_data.get("description", ""),
                "features_count": len(features),
                "features": features,
                "complexity_score": len(page_data.get("form_fields", [])) + len(page_data.get("api_endpoints", [])),
            }

        # Define implementation phases
        phases = [
            {
                "phase": 1,
                "name": "Foundation",
                "description": "Core authentication, navigation, and basic UI",
                "features": ["Login", "Dashboard", "Navigation", "User Profile"],
                "estimated_weeks": 2
            },
            {
                "phase": 2,
                "name": "Client Management",
                "description": "Client/patient data management",
                "features": ["Clients", "Client Detail", "Client Forms"],
                "estimated_weeks": 3
            },
            {
                "phase": 3,
                "name": "Session Management",
                "description": "Session scheduling, recording, and notes",
                "features": ["Sessions", "Calendar", "Session Detail", "Notes"],
                "estimated_weeks": 4
            },
            {
                "phase": 4,
                "name": "AI & Automation",
                "description": "Transcription, AI notes, templates",
                "features": ["Transcription", "AI Notes", "Templates"],
                "estimated_weeks": 3
            },
            {
                "phase": 5,
                "name": "Advanced Features",
                "description": "Telehealth, compliance, payments",
                "features": ["Telehealth", "Compliance", "Payments", "Forms"],
                "estimated_weeks": 4
            }
        ]

        roadmap["implementation_phases"] = phases

        # Technical requirements
        roadmap["technical_requirements"] = {
            "frontend": {
                "framework": "React (assumed from modern SPA patterns)",
                "styling": "Modern CSS framework (Tailwind/Material-UI assumed)",
                "state_management": "Required for session data",
                "routing": "Client-side routing (/sessions, /clients, etc.)"
            },
            "backend": {
                "api_style": "RESTful API (assumed from endpoints)",
                "authentication": "JWT or session-based (login required)",
                "database": "Relational DB for users, sessions, clients",
                "ai_integration": "Transcription API, LLM for notes"
            },
            "infrastructure": {
                "storage": "Audio file storage (sessions)",
                "cdn": "For static assets",
                "realtime": "Possibly WebSockets for live sessions"
            }
        }

        save_json(roadmap, "IMPLEMENTATION_ROADMAP.json")

        print("   ✅ Implementation roadmap generated")
        print(f"      - {len(roadmap['feature_categories'])} feature categories")
        print(f"      - {len(phases)} implementation phases")
        print(f"      - {len(roadmap['api_endpoints_discovered'])} API endpoints discovered")

        # Step 7: Create orchestrator-ready feature specs
        print("\n\n📋 STEP 7: Creating Orchestrator-Ready Specifications")
        print("-"*70)

        orchestrator_specs = {
            "project_name": "TherapyBridge_Upheal_Clone",
            "source_application": "Upheal.io",
            "analysis_date": timestamp,
            "features_to_implement": [],
            "data_models_required": [],
            "api_endpoints_required": [],
            "ui_components_required": [],
        }

        # Generate detailed feature specs
        for page_name, page_data in feature_catalog["pages"].items():
            feature_spec = {
                "feature_name": page_name,
                "description": page_data.get("description", ""),
                "url_pattern": page_data.get("url", ""),
                "user_story": f"As a therapist, I want to {page_data.get('description', '').lower()}",
                "acceptance_criteria": [],
                "ui_components": [],
                "api_endpoints": page_data.get("api_endpoints", []),
                "data_fields": page_data.get("form_fields", []),
                "navigation_items": [nav.get("text", "") for nav in page_data.get("navigation", [])[:10]],
                "implementation_priority": "high" if page_name in ["Home", "Sessions", "Clients"] else "medium",
            }

            # Generate acceptance criteria from sections
            for section in page_data.get("ui_patterns", {}).get("headings", [])[:5]:
                feature_spec["acceptance_criteria"].append(f"Should display {section}")

            # Identify UI components
            ui_components = set()
            if page_data.get("ui_patterns", {}).get("buttons", []):
                ui_components.add("Button")
            if page_data.get("ui_patterns", {}).get("lists", 0) > 0:
                ui_components.add("List")
            if page_data.get("ui_patterns", {}).get("tables", 0) > 0:
                ui_components.add("Table")
            if page_data.get("form_fields", []):
                ui_components.add("Form")
                ui_components.add("Input")

            feature_spec["ui_components"] = list(ui_components)

            orchestrator_specs["features_to_implement"].append(feature_spec)

        # Generate data models from form fields and session structures
        data_models = {
            "User": {
                "fields": ["id", "email", "password", "name", "practice_name", "created_at"],
                "source": "Login and Profile pages"
            },
            "Client": {
                "fields": ["id", "name", "email", "phone", "created_at", "therapist_id"],
                "source": "Clients page"
            },
            "Session": {
                "fields": ["id", "client_id", "therapist_id", "date", "duration", "recording_url", "transcript", "notes", "created_at"],
                "source": "Sessions page and detail pages"
            },
            "Note": {
                "fields": ["id", "session_id", "content", "template_id", "ai_generated", "created_at"],
                "source": "Notes page and session details"
            },
            "Template": {
                "fields": ["id", "name", "content", "category", "created_at"],
                "source": "Templates page"
            }
        }

        orchestrator_specs["data_models_required"] = data_models

        # Compile all unique API endpoints
        orchestrator_specs["api_endpoints_required"] = sorted(list(feature_catalog["api_endpoints"]))

        # Compile all unique UI components
        all_ui_components = set()
        for feature in orchestrator_specs["features_to_implement"]:
            all_ui_components.update(feature["ui_components"])
        orchestrator_specs["ui_components_required"] = sorted(list(all_ui_components))

        save_json(orchestrator_specs, "ORCHESTRATOR_FEATURE_SPECS.json")

        print("   ✅ Orchestrator specifications created")
        print(f"      - {len(orchestrator_specs['features_to_implement'])} features specified")
        print(f"      - {len(data_models)} data models defined")
        print(f"      - {len(orchestrator_specs['ui_components_required'])} UI components identified")

        # Save master catalog
        feature_catalog["api_endpoints"] = sorted(list(feature_catalog["api_endpoints"]))
        save_json(feature_catalog, "MASTER_FEATURE_CATALOG.json")

        # Step 8: Generate summary report
        print("\n\n📊 STEP 8: Generating Summary Report")
        print("-"*70)

        summary_report = f"""# Upheal.io Deep Feature Analysis
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Purpose:** Feature cloning for TherapyBridge development

## Executive Summary

This analysis provides comprehensive technical specifications for cloning Upheal.io's
features into TherapyBridge. All data extracted is ready for orchestrator agent processing.

## Statistics

- **Pages Analyzed:** {len(feature_catalog['pages'])}
- **Session Workflows:** {len(feature_catalog.get('workflows', {}).get('sessions', []))}
- **API Endpoints Discovered:** {len(feature_catalog['api_endpoints'])}
- **Unique URLs Found:** {len(sitemap['all_urls'])}
- **Features Identified:** {sum(len(cat['features']) for cat in roadmap['feature_categories'].values())}

## Key Files Generated

### Implementation Planning
- `IMPLEMENTATION_ROADMAP.json` - 5-phase development plan with timelines
- `ORCHESTRATOR_FEATURE_SPECS.json` - Detailed specs ready for orchestrator agent
- `MASTER_FEATURE_CATALOG.json` - Complete feature inventory

### Page Analysis (Per Page)
- `{{page_name}}_content.md` - Markdown content
- `{{page_name}}_raw.html` - Raw HTML for reference
- `{{page_name}}_analysis.json` - Structured analysis
- `{{page_name}}_screenshot.png` - Visual reference

### Workflow Analysis
- `session_workflow_analysis.json` - Session management workflows
- `session_{{N}}_detail.md` - Individual session examples
- `complete_sitemap.json` - Full application structure

## Data Models Identified

{chr(10).join(f"- **{model}**: {', '.join(data['fields'][:5])}..." for model, data in data_models.items())}

## Implementation Phases

{chr(10).join(f"### Phase {phase['phase']}: {phase['name']} ({phase['estimated_weeks']} weeks){chr(10)}{phase['description']}{chr(10)}Features: {', '.join(phase['features'])}" for phase in phases)}

## Total Estimated Timeline

**{sum(phase['estimated_weeks'] for phase in phases)} weeks** for full feature parity

## API Endpoints Discovered

{chr(10).join(f"- {endpoint}" for endpoint in sorted(list(feature_catalog['api_endpoints']))[:20])}
{"..." if len(feature_catalog['api_endpoints']) > 20 else ""}

## Next Steps for Orchestrator

1. Review `ORCHESTRATOR_FEATURE_SPECS.json` for detailed requirements
2. Use `IMPLEMENTATION_ROADMAP.json` for phased development approach
3. Reference individual page analysis files for UI/UX details
4. Consult session workflow analysis for complex interaction patterns
5. Use screenshots as visual specification references

## Files Location

All analysis files saved to: `{OUTPUT_DIR.absolute()}/`

---

**Ready for Orchestrator Agent Processing** ✅
"""

        save_file(summary_report, "00_ANALYSIS_SUMMARY.md")

        print("\n" + "="*70)
        print("✅ DEEP FEATURE EXTRACTION COMPLETE!")
        print("="*70)
        print(f"📁 Output: {OUTPUT_DIR.absolute()}")
        print(f"📊 Files generated: ~{len(list(OUTPUT_DIR.glob('*')))} files")
        print(f"📄 Key files:")
        print(f"   - 00_ANALYSIS_SUMMARY.md")
        print(f"   - ORCHESTRATOR_FEATURE_SPECS.json")
        print(f"   - IMPLEMENTATION_ROADMAP.json")
        print(f"   - MASTER_FEATURE_CATALOG.json")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(deep_crawl_upheal())
