#!/usr/bin/env python3
"""
Upheal Session Detail - Overview Tab Extractor

Wave 2.1 - Instance I2: Overview Tab Specialist

This script extracts the Overview/Summary tab content from an Upheal session detail page.
The Overview tab is typically the default/first tab and contains:
- Session metadata (date, duration, patient name, status)
- Quick stats (mood, topics, highlights)
- Summary card design
- Action buttons (edit, export, share, delete)

Usage:
    python overview_tab_extractor.py                    # Use cached session URL
    python overview_tab_extractor.py --url <url>        # Use specific session URL
    python overview_tab_extractor.py --visible          # Show browser window
    python overview_tab_extractor.py --verbose          # Debug logging

Output:
    - Scrapping/data/tabs/overview_tab.json  (structured data)
    - Scrapping/data/tabs/overview_tab.md    (markdown content)
    - Scrapping/upheal_crawl_results/tab_overview_YYYYMMDD_HHMMSS.png (screenshot)
"""

import asyncio
import json
import re
import sys
import os
import base64
import argparse
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
SCRAPPING_DIR = Path(__file__).parent.parent
env_paths = [
    SCRAPPING_DIR / ".env",
    SCRAPPING_DIR.parent / ".claude" / "skills" / "crawl4ai" / ".env",
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break


@dataclass
class SessionMetadata:
    """Metadata extracted from the session overview."""
    date: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[str] = None
    patient_name: Optional[str] = None
    patient_initials: Optional[str] = None
    therapist_name: Optional[str] = None
    status: Optional[str] = None  # completed, in_progress, pending
    session_type: Optional[str] = None  # intake, progress, termination


@dataclass
class QuickStats:
    """Quick stats/summary information."""
    mood_indicator: Optional[str] = None
    primary_topics: List[str] = field(default_factory=list)
    key_highlights: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    session_notes_preview: Optional[str] = None


@dataclass
class ActionButton:
    """Action button found on the page."""
    name: str
    text: str
    type: str  # primary, secondary, danger, icon
    enabled: bool = True
    icon: Optional[str] = None


@dataclass
class UIPatterns:
    """UI/UX patterns observed on the overview tab."""
    layout_type: str = "unknown"  # card, grid, list, sidebar
    header_style: Optional[str] = None
    has_breadcrumbs: bool = False
    has_back_button: bool = False
    has_sidebar: bool = False
    has_tabs: bool = False
    tab_names: List[str] = field(default_factory=list)
    primary_color: Optional[str] = None
    card_count: int = 0
    expandable_sections: List[str] = field(default_factory=list)
    action_buttons: List[ActionButton] = field(default_factory=list)


@dataclass
class OverviewTabResult:
    """Complete result from overview tab extraction."""
    status: str  # success, error, partial
    tab_name: str = "overview"
    session_url: Optional[str] = None
    metadata: Optional[SessionMetadata] = None
    quick_stats: Optional[QuickStats] = None
    ui_patterns: Optional[UIPatterns] = None
    raw_content: Optional[str] = None
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = ""
    extraction_duration_ms: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Filter out None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}


class OverviewTabExtractor:
    """
    Extracts Overview/Summary tab content from Upheal session detail pages.

    The overview tab typically displays:
    1. Session header with date, duration, patient info
    2. Quick stats cards (mood, topics, highlights)
    3. Summary/overview section
    4. Action buttons (Edit, Export, Share, Delete)
    5. Navigation elements (breadcrumbs, back button, tabs)

    Usage:
        extractor = OverviewTabExtractor()
        result = await extractor.extract(session_url)
    """

    # Browser session ID for persistence
    SESSION_ID = "upheal_overview_tab"

    # Selectors for UI elements
    SELECTORS = {
        "tabs": [
            "[role='tablist']",
            ".tabs",
            "nav[aria-label*='tab']",
            "[data-tabs]",
        ],
        "tab_buttons": [
            "[role='tab']",
            ".tab-button",
            "[data-tab]",
            "button[aria-selected]",
        ],
        "breadcrumbs": [
            "[aria-label='breadcrumb']",
            ".breadcrumb",
            "nav.breadcrumbs",
        ],
        "back_button": [
            "a[href*='sessions']",
            "button[aria-label*='back']",
            ".back-button",
        ],
        "action_buttons": [
            "button:not([role='tab'])",
            "[role='button']",
            ".action-button",
        ],
        "cards": [
            "[class*='card']",
            "[class*='Card']",
            ".panel",
            ".summary-card",
        ],
        "session_header": [
            "header",
            ".session-header",
            "[class*='header']",
            "h1",
            "h2",
        ],
    }

    def __init__(
        self,
        headless: bool = True,
        verbose: bool = False,
        output_dir: Optional[Path] = None,
        screenshot_dir: Optional[Path] = None,
    ):
        """
        Initialize the Overview Tab Extractor.

        Args:
            headless: Run browser in headless mode.
            verbose: Enable verbose logging.
            output_dir: Directory for JSON/MD output. Default: Scrapping/data/tabs
            screenshot_dir: Directory for screenshots. Default: Scrapping/upheal_crawl_results
        """
        self.headless = headless
        self.verbose = verbose

        # Output directories
        self.output_dir = output_dir or (SCRAPPING_DIR / "data" / "tabs")
        self.screenshot_dir = screenshot_dir or (SCRAPPING_DIR / "upheal_crawl_results")

        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Load credentials for authentication
        self.email = os.getenv("UPHEAL_EMAIL")
        self.password = os.getenv("UPHEAL_PASSWORD")

        # Browser configuration
        self.browser_config = BrowserConfig(
            headless=self.headless,
            viewport_width=1920,
            viewport_height=1080,
            verbose=self.verbose,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

    def _build_login_js(self) -> str:
        """Build JavaScript for automated login."""
        return f'''
        setTimeout(function() {{
            var emailField = document.querySelector('input[type="email"]') ||
                             document.querySelector('input[name="email"]');
            if (!emailField) return;

            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;

            nativeInputValueSetter.call(emailField, '{self.email}');
            emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));

            setTimeout(function() {{
                var passwordField = document.querySelector('input[type="password"]');
                if (passwordField) {{
                    nativeInputValueSetter.call(passwordField, '{self.password}');
                    passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}

                setTimeout(function() {{
                    var submitBtn = document.querySelector('button[type="submit"]');
                    if (submitBtn) submitBtn.click();
                }}, 500);
            }}, 500);
        }}, 1000);
        '''

    def _build_ui_analysis_js(self) -> str:
        """Build JavaScript to analyze UI patterns on the page."""
        return '''
        (() => {
            const result = {
                tabs: [],
                buttons: [],
                cards: [],
                layout: {},
                metadata: {},
                content_sections: []
            };

            // Find tabs
            const tabList = document.querySelector('[role="tablist"]') ||
                           document.querySelector('.tabs') ||
                           document.querySelector('[data-tabs]');
            if (tabList) {
                const tabButtons = tabList.querySelectorAll('[role="tab"], .tab-button, button');
                tabButtons.forEach(tab => {
                    result.tabs.push({
                        name: tab.textContent.trim(),
                        selected: tab.getAttribute('aria-selected') === 'true' ||
                                 tab.classList.contains('active') ||
                                 tab.classList.contains('selected'),
                        href: tab.getAttribute('href') || null
                    });
                });
            }

            // Find action buttons (excluding tabs)
            const allButtons = document.querySelectorAll('button:not([role="tab"]), [role="button"]');
            allButtons.forEach(btn => {
                const text = btn.textContent.trim();
                if (text && text.length < 50) {
                    const classes = btn.className || '';
                    let type = 'secondary';
                    if (classes.includes('primary') || classes.includes('main')) type = 'primary';
                    if (classes.includes('danger') || classes.includes('delete') || text.toLowerCase().includes('delete')) type = 'danger';
                    if (btn.querySelector('svg') || classes.includes('icon')) type = 'icon';

                    result.buttons.push({
                        text: text,
                        type: type,
                        disabled: btn.disabled || btn.getAttribute('aria-disabled') === 'true',
                        hasIcon: !!btn.querySelector('svg, img, i')
                    });
                }
            });

            // Find cards/panels
            const cards = document.querySelectorAll('[class*="card"], [class*="Card"], .panel');
            cards.forEach(card => {
                const heading = card.querySelector('h1, h2, h3, h4, h5, h6');
                result.cards.push({
                    title: heading ? heading.textContent.trim() : null,
                    hasContent: card.textContent.trim().length > 50
                });
            });

            // Analyze layout
            result.layout = {
                hasSidebar: !!document.querySelector('[class*="sidebar"], aside, [role="complementary"]'),
                hasBreadcrumbs: !!document.querySelector('[aria-label*="breadcrumb"], .breadcrumb'),
                hasBackButton: !!document.querySelector('a[href*="sessions"], [aria-label*="back"], .back-button'),
                hasHeader: !!document.querySelector('header, [class*="header"]'),
                hasFooter: !!document.querySelector('footer, [class*="footer"]'),
                mainContentWidth: (() => {
                    const main = document.querySelector('main, [role="main"], .main-content');
                    return main ? main.offsetWidth : document.body.offsetWidth;
                })()
            };

            // Extract session metadata from page
            const pageText = document.body.innerText;

            // Look for date patterns
            const dateMatch = pageText.match(/([A-Z][a-z]{2} \\d{1,2}, \\d{4})/);
            if (dateMatch) result.metadata.date = dateMatch[1];

            // Look for time patterns
            const timeMatch = pageText.match(/(\\d{1,2}:\\d{2} [AP]M)/);
            if (timeMatch) result.metadata.time = timeMatch[1];

            // Look for duration patterns
            const durationMatch = pageText.match(/(\\d+ mins?|\\d+ minutes?|\\d+h \\d+m)/i);
            if (durationMatch) result.metadata.duration = durationMatch[1];

            // Look for "Held by" pattern (therapist name)
            const heldByMatch = pageText.match(/Held by ([A-Za-z ]+)/);
            if (heldByMatch) result.metadata.therapistName = heldByMatch[1].trim();

            // Find content sections (expandable areas)
            const expandable = document.querySelectorAll('[aria-expanded], details, [data-expanded], .accordion');
            expandable.forEach(section => {
                const heading = section.querySelector('summary, button, [role="button"]');
                if (heading) {
                    result.content_sections.push({
                        name: heading.textContent.trim(),
                        expanded: section.getAttribute('aria-expanded') === 'true' ||
                                 section.hasAttribute('open')
                    });
                }
            });

            return JSON.stringify(result);
        })();
        '''

    def _build_content_scroll_js(self) -> str:
        """Build JavaScript to scroll and load all dynamic content."""
        return '''
        (async () => {
            // Scroll to load lazy content
            const scrollHeight = document.body.scrollHeight;
            window.scrollTo(0, scrollHeight / 3);
            await new Promise(r => setTimeout(r, 500));
            window.scrollTo(0, scrollHeight * 2/3);
            await new Promise(r => setTimeout(r, 500));
            window.scrollTo(0, scrollHeight);
            await new Promise(r => setTimeout(r, 500));
            window.scrollTo(0, 0);
            await new Promise(r => setTimeout(r, 500));

            // Click to expand any collapsed sections
            const expandButtons = document.querySelectorAll('[aria-expanded="false"]');
            expandButtons.forEach(btn => {
                try { btn.click(); } catch(e) {}
            });
            await new Promise(r => setTimeout(r, 300));
        })();
        '''

    def _parse_ui_patterns(self, js_result: str, markdown: str) -> UIPatterns:
        """Parse the JS analysis result into UIPatterns dataclass."""
        patterns = UIPatterns()

        try:
            data = json.loads(js_result) if js_result else {}
        except json.JSONDecodeError:
            data = {}

        # Parse tabs
        tabs = data.get("tabs", [])
        if tabs:
            patterns.has_tabs = True
            patterns.tab_names = [t["name"] for t in tabs if t.get("name")]

        # Parse layout
        layout = data.get("layout", {})
        patterns.has_sidebar = layout.get("hasSidebar", False)
        patterns.has_breadcrumbs = layout.get("hasBreadcrumbs", False)
        patterns.has_back_button = layout.get("hasBackButton", False)

        # Determine layout type
        if patterns.has_sidebar:
            patterns.layout_type = "sidebar"
        elif len(data.get("cards", [])) > 3:
            patterns.layout_type = "grid"
        elif len(data.get("cards", [])) > 0:
            patterns.layout_type = "card"
        else:
            patterns.layout_type = "list"

        # Parse cards
        patterns.card_count = len(data.get("cards", []))

        # Parse action buttons
        for btn in data.get("buttons", []):
            if btn.get("text"):
                patterns.action_buttons.append(ActionButton(
                    name=btn["text"].lower().replace(" ", "_"),
                    text=btn["text"],
                    type=btn.get("type", "secondary"),
                    enabled=not btn.get("disabled", False),
                    icon="yes" if btn.get("hasIcon") else None
                ))

        # Parse expandable sections
        for section in data.get("content_sections", []):
            if section.get("name"):
                patterns.expandable_sections.append(section["name"])

        return patterns

    def _parse_session_metadata(self, js_result: str, markdown: str) -> SessionMetadata:
        """Parse session metadata from JS result and markdown."""
        metadata = SessionMetadata()

        try:
            data = json.loads(js_result) if js_result else {}
            js_metadata = data.get("metadata", {})
        except json.JSONDecodeError:
            js_metadata = {}

        # From JS extraction
        metadata.date = js_metadata.get("date")
        metadata.time = js_metadata.get("time")
        metadata.duration = js_metadata.get("duration")
        metadata.therapist_name = js_metadata.get("therapistName")

        # Enhanced parsing from markdown
        if markdown:
            # Patient name - look for initials pattern like "RG" or "TP"
            initials_match = re.search(r'\b([A-Z]{2})\b(?![a-z])', markdown)
            if initials_match:
                metadata.patient_initials = initials_match.group(1)

            # Full patient name patterns
            patient_patterns = [
                r'([A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?)\s*\(demo\)',
                r'Client:?\s*([A-Z][a-z]+ [A-Z][a-z]+)',
                r'Patient:?\s*([A-Z][a-z]+ [A-Z][a-z]+)',
            ]
            for pattern in patient_patterns:
                match = re.search(pattern, markdown)
                if match:
                    metadata.patient_name = match.group(1)
                    break

            # Session type from note title
            if "intake" in markdown.lower():
                metadata.session_type = "intake"
            elif "progress" in markdown.lower():
                metadata.session_type = "progress"
            elif "termination" in markdown.lower() or "discharge" in markdown.lower():
                metadata.session_type = "termination"

            # Status - check for keywords
            if "completed" in markdown.lower() or "past" in markdown.lower():
                metadata.status = "completed"
            elif "upcoming" in markdown.lower() or "scheduled" in markdown.lower():
                metadata.status = "scheduled"
            elif "in progress" in markdown.lower():
                metadata.status = "in_progress"

        return metadata

    def _parse_quick_stats(self, markdown: str) -> QuickStats:
        """Parse quick stats from markdown content."""
        stats = QuickStats()

        if not markdown:
            return stats

        # Extract topics - look for common therapy topics
        topic_keywords = [
            "anxiety", "depression", "trauma", "relationship", "stress",
            "grief", "anger", "self-esteem", "behavioral", "violence",
            "perfectionism", "work", "family"
        ]
        found_topics = []
        markdown_lower = markdown.lower()
        for topic in topic_keywords:
            if topic in markdown_lower:
                found_topics.append(topic.title())
        stats.primary_topics = found_topics[:5]  # Top 5

        # Extract session notes preview
        # Look for summary-like sections
        summary_patterns = [
            r'(?:summary|overview|key points?)[:.]?\s*(.{50,300})',
            r'(?:The client|Patient).{20,200}',
        ]
        for pattern in summary_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                stats.session_notes_preview = match.group(0).strip()[:300]
                break

        # Risk flags - look for concerning language
        risk_keywords = ["suicide", "self-harm", "violence", "abuse", "crisis"]
        found_risks = []
        for risk in risk_keywords:
            if risk in markdown_lower:
                found_risks.append(risk.title())
        stats.risk_flags = found_risks

        return stats

    def _save_screenshot(self, screenshot_data: Any, filename: str) -> Optional[str]:
        """Save screenshot and return path."""
        if not screenshot_data:
            return None

        try:
            if isinstance(screenshot_data, str):
                screenshot_data = base64.b64decode(screenshot_data)

            filepath = self.screenshot_dir / filename
            with open(filepath, "wb") as f:
                f.write(screenshot_data)

            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return None

    def get_session_url_from_cache(self) -> Optional[str]:
        """Load session URL from cached discovery data."""
        cache_file = SCRAPPING_DIR / "data" / "session_detail_url.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                return data.get("session_detail_url")
            except Exception as e:
                logger.warning(f"Failed to load cached URL: {e}")

        # Fallback to discovered links
        links_files = list((SCRAPPING_DIR / "upheal_crawl_results").glob("*_discovered_links_*.json"))
        if links_files:
            try:
                with open(sorted(links_files)[-1], 'r') as f:
                    data = json.load(f)
                for url in data.get("discovered_urls", []):
                    if "/detail/" in url:
                        return url
            except Exception as e:
                logger.warning(f"Failed to load discovered links: {e}")

        return None

    async def extract(
        self,
        session_url: Optional[str] = None,
        use_cache: bool = True
    ) -> OverviewTabResult:
        """
        Extract overview tab content from a session detail page.

        Args:
            session_url: URL of the session detail page. If None, uses cached URL.
            use_cache: Whether to use cached session URL if session_url not provided.

        Returns:
            OverviewTabResult with extracted content and UI patterns.
        """
        start_time = datetime.now()
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")

        # Get session URL
        if not session_url and use_cache:
            session_url = self.get_session_url_from_cache()

        if not session_url:
            return OverviewTabResult(
                status="error",
                error_message="No session URL provided and no cached URL found. "
                             "Run upheal_session_detail_scraper.py first."
            )

        logger.info(f"Extracting overview tab from: {session_url}")

        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                # Step 1: Authenticate if needed
                needs_auth = self.email and self.password

                if needs_auth:
                    logger.info("Authenticating...")
                    login_config = CrawlerRunConfig(
                        session_id=self.SESSION_ID,
                        js_code=self._build_login_js(),
                        page_timeout=60000,
                        wait_for='''js:() => {
                            if (!window.__loginAttempted) {
                                window.__loginAttempted = Date.now();
                                return false;
                            }
                            if (Date.now() - window.__loginAttempted < 5000) return false;
                            return !window.location.pathname.includes('login');
                        }''',
                    )

                    login_result = await crawler.arun(
                        "https://app.upheal.io/login",
                        config=login_config
                    )

                    if not login_result.success or "login" in login_result.url.lower():
                        return OverviewTabResult(
                            status="error",
                            session_url=session_url,
                            error_message="Authentication failed"
                        )

                    logger.info("Authentication successful")

                # Step 2: Navigate to session detail page
                logger.info(f"Navigating to session detail: {session_url}")

                detail_config = CrawlerRunConfig(
                    session_id=self.SESSION_ID,
                    page_timeout=45000,
                    screenshot=True,
                    # Wait for content to load - look for common session detail elements
                    wait_for='''js:() => {
                        // Wait for page to have substantial content
                        const content = document.body.innerText || '';
                        if (content.length < 200) return false;

                        // Check for session detail indicators
                        const hasDetailContent =
                            content.includes('Held by') ||
                            content.includes('mins') ||
                            content.includes('transcript') ||
                            content.includes('notes') ||
                            document.querySelector('[class*="detail"]') ||
                            document.querySelector('[class*="session"]');

                        return hasDetailContent;
                    }''',
                    js_code=self._build_content_scroll_js(),
                )

                detail_result = await crawler.arun(session_url, config=detail_config)

                if not detail_result.success:
                    return OverviewTabResult(
                        status="error",
                        session_url=session_url,
                        error_message=f"Failed to load session detail: {detail_result.error_message}"
                    )

                # Check for redirect to login
                if "login" in detail_result.url.lower():
                    return OverviewTabResult(
                        status="error",
                        session_url=session_url,
                        error_message="Session expired - redirected to login"
                    )

                # Step 3: Run UI analysis
                logger.info("Analyzing UI patterns...")

                analysis_config = CrawlerRunConfig(
                    session_id=self.SESSION_ID,
                    page_timeout=15000,
                    screenshot=True,
                    js_code=self._build_ui_analysis_js(),
                )

                analysis_result = await crawler.arun(detail_result.url, config=analysis_config)

                # Get JS result for UI analysis
                js_result = getattr(analysis_result, 'js_result', None) or ""

                # Save screenshot
                screenshot_filename = f"tab_overview_{timestamp}.png"
                screenshot_path = self._save_screenshot(
                    analysis_result.screenshot or detail_result.screenshot,
                    screenshot_filename
                )

                # Parse extracted data
                markdown = analysis_result.markdown or detail_result.markdown or ""
                ui_patterns = self._parse_ui_patterns(js_result, markdown)
                metadata = self._parse_session_metadata(js_result, markdown)
                quick_stats = self._parse_quick_stats(markdown)

                # Calculate extraction duration
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                result = OverviewTabResult(
                    status="success",
                    session_url=session_url,
                    metadata=metadata,
                    quick_stats=quick_stats,
                    ui_patterns=ui_patterns,
                    raw_content=markdown,
                    screenshot_path=screenshot_path,
                    extraction_duration_ms=duration_ms
                )

                logger.info(f"Extraction complete in {duration_ms}ms")
                return result

        except Exception as e:
            logger.exception(f"Extraction error: {e}")
            return OverviewTabResult(
                status="error",
                session_url=session_url,
                error_message=str(e)
            )

    def save_result(self, result: OverviewTabResult) -> tuple[Path, Path]:
        """
        Save extraction result to JSON and MD files.

        Args:
            result: The extraction result to save.

        Returns:
            Tuple of (json_path, md_path)
        """
        # Save JSON
        json_path = self.output_dir / "overview_tab.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON: {json_path}")

        # Save Markdown summary
        md_path = self.output_dir / "overview_tab.md"
        md_content = self._generate_markdown_report(result)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"Saved MD: {md_path}")

        return json_path, md_path

    def _generate_markdown_report(self, result: OverviewTabResult) -> str:
        """Generate a markdown report from the extraction result."""
        lines = [
            "# Upheal Session Detail - Overview Tab Analysis",
            "",
            f"**Extraction Date:** {result.timestamp}",
            f"**Session URL:** {result.session_url}",
            f"**Status:** {result.status}",
            f"**Duration:** {result.extraction_duration_ms}ms",
            "",
        ]

        if result.error_message:
            lines.extend([
                "## Error",
                f"{result.error_message}",
                "",
            ])
            return "\n".join(lines)

        # Session Metadata
        if result.metadata:
            m = result.metadata
            lines.extend([
                "## Session Metadata",
                "",
                f"| Field | Value |",
                f"|-------|-------|",
                f"| Date | {m.date or 'N/A'} |",
                f"| Time | {m.time or 'N/A'} |",
                f"| Duration | {m.duration or 'N/A'} |",
                f"| Patient Name | {m.patient_name or 'N/A'} |",
                f"| Patient Initials | {m.patient_initials or 'N/A'} |",
                f"| Therapist | {m.therapist_name or 'N/A'} |",
                f"| Session Type | {m.session_type or 'N/A'} |",
                f"| Status | {m.status or 'N/A'} |",
                "",
            ])

        # Quick Stats
        if result.quick_stats:
            s = result.quick_stats
            lines.extend([
                "## Quick Stats",
                "",
            ])
            if s.primary_topics:
                lines.append(f"**Topics:** {', '.join(s.primary_topics)}")
            if s.risk_flags:
                lines.append(f"**Risk Flags:** {', '.join(s.risk_flags)}")
            if s.session_notes_preview:
                lines.extend([
                    "",
                    "**Notes Preview:**",
                    f"> {s.session_notes_preview}",
                ])
            lines.append("")

        # UI Patterns
        if result.ui_patterns:
            p = result.ui_patterns
            lines.extend([
                "## UI Patterns",
                "",
                f"**Layout Type:** {p.layout_type}",
                f"**Has Sidebar:** {p.has_sidebar}",
                f"**Has Breadcrumbs:** {p.has_breadcrumbs}",
                f"**Has Back Button:** {p.has_back_button}",
                f"**Has Tabs:** {p.has_tabs}",
                f"**Card Count:** {p.card_count}",
                "",
            ])

            if p.tab_names:
                lines.extend([
                    "### Tabs Found",
                    "",
                ])
                for tab in p.tab_names:
                    lines.append(f"- {tab}")
                lines.append("")

            if p.action_buttons:
                lines.extend([
                    "### Action Buttons",
                    "",
                    "| Button | Type | Enabled |",
                    "|--------|------|---------|",
                ])
                for btn in p.action_buttons:
                    lines.append(f"| {btn.text} | {btn.type} | {btn.enabled} |")
                lines.append("")

            if p.expandable_sections:
                lines.extend([
                    "### Expandable Sections",
                    "",
                ])
                for section in p.expandable_sections:
                    lines.append(f"- {section}")
                lines.append("")

        # Screenshot
        if result.screenshot_path:
            lines.extend([
                "## Screenshot",
                "",
                f"![Overview Tab Screenshot]({result.screenshot_path})",
                "",
            ])

        # Raw Content Preview
        if result.raw_content:
            preview = result.raw_content[:1000]
            if len(result.raw_content) > 1000:
                preview += "..."
            lines.extend([
                "## Raw Content Preview",
                "",
                "```",
                preview,
                "```",
                "",
            ])

        return "\n".join(lines)


async def main():
    """Main entry point for overview tab extraction."""
    parser = argparse.ArgumentParser(
        description="Extract Overview tab from Upheal session detail page"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Session detail URL (uses cached URL if not provided)"
    )
    parser.add_argument(
        "--visible", "-v",
        action="store_true",
        help="Show browser window (not headless)"
    )
    parser.add_argument(
        "--verbose", "-d",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached session URL"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("\n" + "=" * 70)
    print("UPHEAL OVERVIEW TAB EXTRACTOR")
    print("Wave 2.1 - Instance I2")
    print("=" * 70 + "\n")

    try:
        extractor = OverviewTabExtractor(
            headless=not args.visible,
            verbose=args.verbose
        )

        print(f"Output dir:     {extractor.output_dir}")
        print(f"Screenshot dir: {extractor.screenshot_dir}")

        # Run extraction
        print("\n[Step 1] Extracting overview tab...")
        result = await extractor.extract(
            session_url=args.url,
            use_cache=not args.no_cache
        )

        # Save results
        print("\n[Step 2] Saving results...")
        json_path, md_path = extractor.save_result(result)

        # Print summary
        print("\n" + "=" * 70)
        print("EXTRACTION RESULT")
        print("=" * 70)

        if result.status == "success":
            print(f"Status:          SUCCESS")
            print(f"Session URL:     {result.session_url}")
            print(f"Duration:        {result.extraction_duration_ms}ms")

            if result.metadata:
                print(f"\nSession Metadata:")
                print(f"  Date:          {result.metadata.date or 'N/A'}")
                print(f"  Duration:      {result.metadata.duration or 'N/A'}")
                print(f"  Patient:       {result.metadata.patient_name or result.metadata.patient_initials or 'N/A'}")
                print(f"  Type:          {result.metadata.session_type or 'N/A'}")

            if result.ui_patterns:
                print(f"\nUI Patterns:")
                print(f"  Layout:        {result.ui_patterns.layout_type}")
                print(f"  Tabs:          {len(result.ui_patterns.tab_names)} found")
                print(f"  Buttons:       {len(result.ui_patterns.action_buttons)} found")
                print(f"  Cards:         {result.ui_patterns.card_count}")

                if result.ui_patterns.tab_names:
                    print(f"  Tab names:     {', '.join(result.ui_patterns.tab_names)}")

            if result.screenshot_path:
                print(f"\nScreenshot:      {result.screenshot_path}")

            print(f"\nOutput files:")
            print(f"  JSON:          {json_path}")
            print(f"  Markdown:      {md_path}")

            print("\n" + "=" * 70)
            return 0
        else:
            print(f"Status:  ERROR")
            print(f"Message: {result.error_message}")
            print("=" * 70 + "\n")
            return 1

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
