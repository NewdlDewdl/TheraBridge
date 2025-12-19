#!/usr/bin/env python3
"""
Session Map/Timeline Tab Extractor for Upheal Session Detail Page

This script extracts the Session Map/Timeline tab content from an Upheal session
detail page, focusing on:
- Timeline visualization type (horizontal/vertical/radial)
- Milestone marker design patterns
- Progress tracking indicators
- Interactive timeline features

Part of Wave 2.4 - Upheal Session Detail Deep Dive project.
"""

import asyncio
import json
import os
import base64
import re
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
except ImportError:
    print("ERROR: crawl4ai not installed. Run: pip install crawl4ai")
    exit(1)

# Load environment variables from crawl4ai skill .env
PROJECT_ROOT = Path(__file__).parent.parent.parent
SKILL_ENV = PROJECT_ROOT / ".claude" / "skills" / "crawl4ai" / ".env"
SCRAPPING_ENV = PROJECT_ROOT / "Scrapping" / ".env"

# Try skill env first, then scrapping env
if SKILL_ENV.exists():
    load_dotenv(SKILL_ENV)
elif SCRAPPING_ENV.exists():
    load_dotenv(SCRAPPING_ENV)

# Configuration
UPHEAL_EMAIL = os.getenv("UPHEAL_EMAIL")
UPHEAL_PASSWORD = os.getenv("UPHEAL_PASSWORD")
UPHEAL_LOGIN_URL = os.getenv("UPHEAL_LOGIN_URL", "https://app.upheal.io/login")

# Default session detail URL from Wave 1 discovery
DEFAULT_SESSION_URL = "https://app.upheal.io/detail/b83dc32e-58c9-4c43-ad16-338a5f331c95/5b4aa0cb-9f10-405a-b7ff-e34ea54e5071"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "Scrapping" / "upheal_crawl_results"
DATA_DIR = PROJECT_ROOT / "Scrapping" / "data" / "tabs"


def save_screenshot(screenshot_data: str | bytes, filepath: Path) -> bool:
    """Save screenshot from base64 or bytes."""
    try:
        if isinstance(screenshot_data, str):
            screenshot_data = base64.b64decode(screenshot_data)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(screenshot_data)
        return True
    except Exception as e:
        print(f"Error saving screenshot: {e}")
        return False


def save_json(data: dict, filepath: Path) -> bool:
    """Save data as JSON file."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False


def analyze_timeline_from_html(html: str) -> dict:
    """
    Analyze HTML to detect timeline visualization patterns.
    Returns detected timeline characteristics.
    """
    timeline_analysis = {
        "detected": False,
        "timeline_type": "unknown",
        "orientation": "unknown",
        "container_selectors": [],
        "marker_patterns": [],
        "progress_elements": [],
        "interactive_hints": []
    }

    html_lower = html.lower()

    # Detect timeline containers
    timeline_keywords = [
        "timeline", "session-map", "history", "progress", "journey",
        "chart", "graph", "visualization", "sessions-list"
    ]

    for keyword in timeline_keywords:
        if keyword in html_lower:
            timeline_analysis["container_selectors"].append(keyword)
            timeline_analysis["detected"] = True

    # Detect orientation hints
    if any(x in html_lower for x in ["horizontal", "row", "flex-row"]):
        timeline_analysis["orientation"] = "horizontal"
    elif any(x in html_lower for x in ["vertical", "column", "flex-col"]):
        timeline_analysis["orientation"] = "vertical"

    # Detect SVG/Canvas for visual timeline
    if "<svg" in html_lower:
        timeline_analysis["timeline_type"] = "svg_based"
        timeline_analysis["marker_patterns"].append("svg_elements")
    elif "<canvas" in html_lower:
        timeline_analysis["timeline_type"] = "canvas_based"
        timeline_analysis["marker_patterns"].append("canvas_rendering")

    # Detect marker patterns
    marker_keywords = ["dot", "marker", "node", "point", "milestone", "step"]
    for keyword in marker_keywords:
        if keyword in html_lower:
            timeline_analysis["marker_patterns"].append(keyword)

    # Detect progress indicators
    progress_keywords = ["progress", "percentage", "completion", "goal", "target"]
    for keyword in progress_keywords:
        if keyword in html_lower:
            timeline_analysis["progress_elements"].append(keyword)

    # Detect interactive elements
    interactive_keywords = ["onclick", "click", "hover", "tooltip", "popover", "modal"]
    for keyword in interactive_keywords:
        if keyword in html_lower:
            timeline_analysis["interactive_hints"].append(keyword)

    return timeline_analysis


def analyze_timeline_from_markdown(markdown: str) -> dict:
    """
    Analyze extracted markdown for timeline/session map content.
    """
    content_analysis = {
        "has_session_list": False,
        "session_count": 0,
        "date_patterns": [],
        "topics_mentioned": [],
        "navigation_elements": [],
        "tab_names_found": []
    }

    # Look for session patterns
    date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s*\d{4}'
    dates = re.findall(date_pattern, markdown, re.IGNORECASE)
    content_analysis["date_patterns"] = list(set(dates))
    content_analysis["session_count"] = len(dates)
    content_analysis["has_session_list"] = len(dates) > 0

    # Look for tab navigation
    tab_keywords = ["session map", "timeline", "history", "progress", "journey",
                    "transcript", "notes", "summary", "insights", "analytics"]
    markdown_lower = markdown.lower()
    for tab in tab_keywords:
        if tab in markdown_lower:
            content_analysis["tab_names_found"].append(tab)

    return content_analysis


async def extract_session_map_tab(
    session_url: str = DEFAULT_SESSION_URL,
    manual_login: bool = True,
    login_wait_seconds: int = 60
) -> dict:
    """
    Extract Session Map/Timeline tab from Upheal session detail page.

    Args:
        session_url: URL of the session detail page
        manual_login: If True, waits for manual login. If False, attempts auto-login.
        login_wait_seconds: Seconds to wait for manual login

    Returns:
        Dictionary containing extracted timeline data and UI patterns
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {
        "tab_name": "session_map",
        "extraction_timestamp": timestamp,
        "session_url": session_url,
        "success": False,
        "error": None,
        "timeline_type": "unknown",
        "orientation": "unknown",
        "marker_design": {
            "type": "unknown",
            "color_coding": [],
            "size_variations": False,
            "labels": False,
            "tooltips": False
        },
        "progress_indicators": {
            "found": False,
            "types": [],
            "has_goals": False,
            "has_milestones": False
        },
        "interactive_features": [],
        "screenshot_path": None,
        "ui_patterns": {},
        "raw_html_length": 0,
        "markdown_length": 0,
        "content_analysis": {},
        "html_analysis": {},
        "therapybridge_recommendations": []
    }

    print("=" * 70)
    print("Session Map/Timeline Tab Extractor")
    print("=" * 70)
    print(f"Target URL: {session_url}")
    print(f"Timestamp: {timestamp}")
    print("=" * 70)

    # Browser config - visible for manual login
    browser_config = BrowserConfig(
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:

        # Step 1: Login
        print("\n[1/4] Opening login page...")
        login_config = CrawlerRunConfig(
            session_id="upheal_session_map",
            page_timeout=120000,
            screenshot=True,
        )

        login_result = await crawler.arun(
            url=UPHEAL_LOGIN_URL,
            config=login_config
        )

        if not login_result.success:
            result["error"] = f"Failed to load login page: {login_result.error_message}"
            print(f"ERROR: {result['error']}")
            return result

        print(f"Login page loaded: {login_result.url}")

        if manual_login:
            print(f"\n>>> MANUAL LOGIN REQUIRED <<<")
            print(f">>> You have {login_wait_seconds} seconds to log in...")
            print(f">>> Credentials hint: {UPHEAL_EMAIL}")

            for i in range(login_wait_seconds, 0, -10):
                print(f"    {i} seconds remaining...")
                await asyncio.sleep(10)

        print("\n[2/4] Navigating to session detail page...")

        # Step 2: Navigate to session detail page
        session_config = CrawlerRunConfig(
            session_id="upheal_session_map",
            page_timeout=30000,
            screenshot=True,
            js_code="""
            // Wait for page to fully load
            await new Promise(r => setTimeout(r, 2000));

            // Scroll to load any lazy content
            window.scrollTo(0, document.body.scrollHeight / 2);
            await new Promise(r => setTimeout(r, 1000));
            window.scrollTo(0, 0);
            """,
        )

        session_result = await crawler.arun(
            url=session_url,
            config=session_config
        )

        if not session_result.success:
            result["error"] = f"Failed to load session page: {session_result.error_message}"
            print(f"ERROR: {result['error']}")
            return result

        # Check if redirected to login
        if "login" in session_result.url.lower():
            result["error"] = "Redirected to login - authentication failed"
            print(f"ERROR: {result['error']}")
            return result

        print(f"Session page loaded: {session_result.url}")
        print(f"Content length: {len(session_result.markdown)} chars")

        # Step 3: Click on Session Map/Timeline tab
        print("\n[3/4] Looking for Session Map/Timeline tab...")

        # JavaScript to find and click session map/timeline tab
        js_click_session_map = """
        (async () => {
            // Comprehensive tab selector patterns
            const tabSelectors = [
                '[role="tab"]',
                '.tab-button',
                '.tab',
                '.tabs-menu > div',
                '.tabs-menu > button',
                '[data-tab]',
                '.nav-tab',
                '.tab-item',
                'button[class*="tab"]',
                'div[class*="tab"]',
                'a[class*="tab"]'
            ];

            // Keywords to match for session map/timeline tab
            const keywords = [
                'session map',
                'sessionmap',
                'timeline',
                'history',
                'progress',
                'journey',
                'sessions',
                'all sessions',
                'overview'
            ];

            let clicked = false;
            let tabInfo = { found: false, text: '', selector: '' };

            for (const selector of tabSelectors) {
                if (clicked) break;

                const tabs = document.querySelectorAll(selector);
                for (let tab of tabs) {
                    const text = tab.textContent.toLowerCase().trim();

                    for (const keyword of keywords) {
                        if (text.includes(keyword)) {
                            console.log(`Found tab: "${text}" matching "${keyword}"`);
                            tab.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            await new Promise(r => setTimeout(r, 500));
                            tab.click();
                            clicked = true;
                            tabInfo = { found: true, text: text, selector: selector };
                            await new Promise(r => setTimeout(r, 2000));
                            break;
                        }
                    }
                    if (clicked) break;
                }
            }

            // Store result for extraction
            window.__tabClickResult = tabInfo;

            // If no specific tab found, try clicking any visible tab
            if (!clicked) {
                const allTabs = document.querySelectorAll('[role="tab"], .tab, [class*="tab"]');
                console.log(`No matching tab found. Total tabs on page: ${allTabs.length}`);

                // Log all tab texts for debugging
                const tabTexts = [];
                allTabs.forEach(tab => {
                    const text = tab.textContent.trim();
                    if (text) tabTexts.push(text);
                });
                window.__availableTabs = tabTexts;
            }

            return window.__tabClickResult;
        })();
        """

        tab_click_config = CrawlerRunConfig(
            session_id="upheal_session_map",
            page_timeout=30000,
            screenshot=True,
            js_code=js_click_session_map,
            wait_for="css:body",  # Basic wait
        )

        tab_result = await crawler.arun(
            url=session_url,  # Re-navigate to ensure fresh state
            config=tab_click_config
        )

        if not tab_result.success:
            result["error"] = f"Failed to interact with tabs: {tab_result.error_message}"
            print(f"WARNING: {result['error']}")

        # Step 4: Extract timeline content
        print("\n[4/4] Extracting timeline visualization data...")

        # Wait for timeline elements to render and extract
        js_extract_timeline = """
        (async () => {
            // Wait for any animations/rendering
            await new Promise(r => setTimeout(r, 1500));

            const timelineData = {
                containers: [],
                markers: [],
                progressBars: [],
                interactiveElements: [],
                svgElements: [],
                canvasElements: [],
                tabInfo: window.__tabClickResult || {},
                availableTabs: window.__availableTabs || []
            };

            // Find timeline containers
            const containerSelectors = [
                '.timeline', '.session-map', '.history', '.progress-timeline',
                '.journey', '[class*="timeline"]', '[class*="session-map"]',
                '.sessions-list', '.session-history'
            ];

            containerSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    timelineData.containers.push({
                        selector: selector,
                        className: el.className,
                        tagName: el.tagName,
                        childCount: el.children.length,
                        hasScrollbar: el.scrollHeight > el.clientHeight
                    });
                });
            });

            // Find markers/nodes
            const markerSelectors = [
                '.marker', '.node', '.dot', '.point', '.milestone',
                '.step', '[class*="marker"]', '[class*="node"]'
            ];

            markerSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    timelineData.markers.push({
                        selector: selector,
                        backgroundColor: style.backgroundColor,
                        borderRadius: style.borderRadius,
                        width: style.width,
                        height: style.height
                    });
                });
            });

            // Find progress indicators
            const progressSelectors = [
                'progress', '.progress-bar', '[role="progressbar"]',
                '[class*="progress"]', '.completion'
            ];

            progressSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    timelineData.progressBars.push({
                        selector: selector,
                        value: el.getAttribute('value') || el.style.width,
                        max: el.getAttribute('max')
                    });
                });
            });

            // Check for SVG timeline
            const svgs = document.querySelectorAll('svg');
            svgs.forEach(svg => {
                timelineData.svgElements.push({
                    width: svg.getAttribute('width'),
                    height: svg.getAttribute('height'),
                    hasPath: svg.querySelector('path') !== null,
                    hasCircle: svg.querySelector('circle') !== null,
                    hasLine: svg.querySelector('line') !== null
                });
            });

            // Check for Canvas
            const canvases = document.querySelectorAll('canvas');
            canvases.forEach(canvas => {
                timelineData.canvasElements.push({
                    width: canvas.width,
                    height: canvas.height,
                    className: canvas.className
                });
            });

            // Find interactive elements
            const clickables = document.querySelectorAll('[onclick], [data-tooltip], [title]');
            clickables.forEach(el => {
                if (el.closest('.timeline, .session-map, .history, [class*="timeline"]')) {
                    timelineData.interactiveElements.push({
                        tagName: el.tagName,
                        hasTooltip: el.hasAttribute('data-tooltip') || el.hasAttribute('title'),
                        tooltipText: el.getAttribute('title') || el.getAttribute('data-tooltip')
                    });
                }
            });

            return timelineData;
        })();
        """

        extract_config = CrawlerRunConfig(
            session_id="upheal_session_map",
            page_timeout=30000,
            screenshot=True,
            js_code=js_extract_timeline,
        )

        extract_result = await crawler.arun(
            url=session_result.url,  # Use actual URL we're on
            config=extract_config
        )

        if extract_result.success:
            # Save screenshot
            screenshot_filename = f"tab_session_map_{timestamp}.png"
            screenshot_path = OUTPUT_DIR / screenshot_filename
            if extract_result.screenshot:
                if save_screenshot(extract_result.screenshot, screenshot_path):
                    result["screenshot_path"] = str(screenshot_path)
                    print(f"Screenshot saved: {screenshot_path}")

            # Analyze content
            result["raw_html_length"] = len(extract_result.html)
            result["markdown_length"] = len(extract_result.markdown)
            result["html_analysis"] = analyze_timeline_from_html(extract_result.html)
            result["content_analysis"] = analyze_timeline_from_markdown(extract_result.markdown)

            # Determine timeline type from analysis
            html_analysis = result["html_analysis"]
            if html_analysis["detected"]:
                result["timeline_type"] = html_analysis["timeline_type"]
                result["orientation"] = html_analysis["orientation"]

                if html_analysis["marker_patterns"]:
                    result["marker_design"]["type"] = "visual_markers"
                    result["marker_design"]["labels"] = "label" in str(html_analysis["marker_patterns"])

                if html_analysis["progress_elements"]:
                    result["progress_indicators"]["found"] = True
                    result["progress_indicators"]["types"] = html_analysis["progress_elements"]

                result["interactive_features"] = html_analysis["interactive_hints"]

            # Extract available tabs
            result["ui_patterns"]["available_tabs"] = result["content_analysis"].get("tab_names_found", [])
            result["ui_patterns"]["session_count"] = result["content_analysis"].get("session_count", 0)

            result["success"] = True

            # Generate TherapyBridge recommendations
            result["therapybridge_recommendations"] = generate_recommendations(result)

        else:
            result["error"] = f"Failed to extract timeline: {extract_result.error_message}"

    return result


def generate_recommendations(extraction_result: dict) -> list:
    """
    Generate UI/UX recommendations for TherapyBridge based on Upheal patterns.
    """
    recommendations = []

    html_analysis = extraction_result.get("html_analysis", {})
    content_analysis = extraction_result.get("content_analysis", {})

    # Timeline type recommendations
    if html_analysis.get("timeline_type") == "svg_based":
        recommendations.append({
            "category": "visualization",
            "recommendation": "Use SVG-based timeline for scalability and interactivity",
            "priority": "high",
            "implementation": "Consider D3.js or React-based SVG timeline components"
        })

    # Orientation recommendations
    if html_analysis.get("orientation") == "vertical":
        recommendations.append({
            "category": "layout",
            "recommendation": "Vertical timeline works well for session history",
            "priority": "medium",
            "implementation": "Use flexbox with column direction, newest sessions at top"
        })
    elif html_analysis.get("orientation") == "horizontal":
        recommendations.append({
            "category": "layout",
            "recommendation": "Horizontal timeline good for progress visualization",
            "priority": "medium",
            "implementation": "Use horizontal scroll or responsive breakpoints"
        })

    # Session list recommendations
    if content_analysis.get("session_count", 0) > 0:
        recommendations.append({
            "category": "data_display",
            "recommendation": f"Design for lists of {content_analysis['session_count']}+ sessions",
            "priority": "high",
            "implementation": "Implement virtualization for large lists, lazy loading"
        })

    # Interactive features
    if html_analysis.get("interactive_hints"):
        if "tooltip" in html_analysis["interactive_hints"]:
            recommendations.append({
                "category": "interactivity",
                "recommendation": "Add tooltips for session quick preview",
                "priority": "medium",
                "implementation": "Use Radix UI Tooltip or similar for hover details"
            })
        if "click" in html_analysis["interactive_hints"]:
            recommendations.append({
                "category": "interactivity",
                "recommendation": "Make timeline entries clickable for navigation",
                "priority": "high",
                "implementation": "Each session marker links to session detail page"
            })

    # Default recommendations if analysis yielded limited data
    if not recommendations:
        recommendations.extend([
            {
                "category": "general",
                "recommendation": "Implement session timeline view showing all client sessions",
                "priority": "high",
                "implementation": "List view with dates, duration, key topics"
            },
            {
                "category": "visualization",
                "recommendation": "Add visual progress indicators for treatment goals",
                "priority": "medium",
                "implementation": "Progress bars or milestone markers"
            },
            {
                "category": "interactivity",
                "recommendation": "Enable quick navigation between sessions",
                "priority": "high",
                "implementation": "Click to navigate, keyboard shortcuts"
            }
        ])

    return recommendations


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract Session Map/Timeline tab from Upheal session detail"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_SESSION_URL,
        help="Session detail page URL"
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=60,
        help="Seconds to wait for manual login (default: 60)"
    )
    parser.add_argument(
        "--auto-login",
        action="store_true",
        help="Attempt automatic login (not recommended)"
    )

    args = parser.parse_args()

    # Run extraction
    result = await extract_session_map_tab(
        session_url=args.url,
        manual_login=not args.auto_login,
        login_wait_seconds=args.wait
    )

    # Save results
    timestamp = result.get("extraction_timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
    output_file = DATA_DIR / "session_map_tab.json"

    if save_json(result, output_file):
        print(f"\n{'=' * 70}")
        print("EXTRACTION COMPLETE")
        print(f"{'=' * 70}")
        print(f"Success: {result['success']}")
        print(f"Timeline type: {result['timeline_type']}")
        print(f"Orientation: {result['orientation']}")
        print(f"Marker design: {result['marker_design']['type']}")
        print(f"Progress indicators found: {result['progress_indicators']['found']}")
        print(f"Interactive features: {result['interactive_features']}")
        print(f"Screenshot: {result['screenshot_path']}")
        print(f"Saved to: {output_file}")
        print(f"{'=' * 70}")

        # Print recommendations
        if result.get("therapybridge_recommendations"):
            print("\nTherapyBridge Recommendations:")
            for i, rec in enumerate(result["therapybridge_recommendations"], 1):
                print(f"  {i}. [{rec['priority'].upper()}] {rec['recommendation']}")
                print(f"     Implementation: {rec['implementation']}")
    else:
        print(f"ERROR: Failed to save results")

    return result


if __name__ == "__main__":
    asyncio.run(main())
