#!/usr/bin/env python3
"""
Upheal Transcript Tab Extractor

Wave 2.2 - Instance I3: Transcript Tab Specialist

This script extracts the Transcript tab content from an Upheal session detail page,
analyzing the conversation display patterns and speaker labeling systems.

What it extracts:
1. Transcript display format (bubbles, list, columns)
2. Speaker labeling (Therapist vs. Client, colors, icons)
3. Timestamp display format and position
4. Message grouping and turn organization
5. UI patterns (highlights, search, export, scroll behavior)
6. Interaction patterns (clickable messages, annotations, playback controls)

Session Detail URL Pattern:
    https://app.upheal.io/detail/{client_uuid}/{session_uuid}

Usage:
    python transcript_tab_extractor.py                    # Use cached session URL
    python transcript_tab_extractor.py --url <url>        # Specify URL directly
    python transcript_tab_extractor.py --visible          # Show browser
    python transcript_tab_extractor.py --verbose          # Debug logging

Output:
    - Screenshot: Scrapping/upheal_crawl_results/tab_transcript_[timestamp].png
    - Data: Scrapping/data/tabs/transcript_tab.json
"""

import asyncio
import json
import os
import re
import sys
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field

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


def find_env_file() -> Path:
    """Find the .env file with Upheal credentials."""
    possible_paths = [
        Path(__file__).parent.parent / ".env",  # Scrapping/.env
        Path(__file__).parent.parent.parent / ".claude" / "skills" / "crawl4ai" / ".env",
        Path(__file__).parent.parent.parent / ".env",  # Root .env
    ]

    for path in possible_paths:
        if path.exists():
            content = path.read_text()
            if "UPHEAL_EMAIL" in content and "UPHEAL_PASSWORD" in content:
                return path

    return possible_paths[0]


# Load environment variables
env_path = find_env_file()
load_dotenv(env_path, override=True)


@dataclass
class SpeakerLabeling:
    """Speaker identification and styling information."""
    therapist_label: str = ""
    client_label: str = ""
    therapist_color: str = ""
    client_color: str = ""
    therapist_position: str = ""  # left, right, centered
    client_position: str = ""
    uses_avatars: bool = False
    uses_icons: bool = False
    icon_details: str = ""


@dataclass
class TimestampFormat:
    """Timestamp display information."""
    format_pattern: str = ""  # e.g., "HH:MM:SS", "MM:SS", "relative"
    position: str = ""  # above, below, inline, tooltip
    visible_by_default: bool = True
    sample_values: List[str] = field(default_factory=list)


@dataclass
class UIPatterns:
    """UI interaction patterns."""
    has_highlighted_moments: bool = False
    highlight_style: str = ""
    has_search_filter: bool = False
    search_location: str = ""
    has_export_copy: bool = False
    export_options: List[str] = field(default_factory=list)
    scroll_behavior: str = ""  # virtual, pagination, infinite
    has_jump_to_timestamp: bool = False


@dataclass
class InteractionPatterns:
    """User interaction capabilities."""
    messages_clickable: bool = False
    click_action: str = ""  # plays audio, shows details, etc.
    has_annotations: bool = False
    annotation_types: List[str] = field(default_factory=list)
    has_playback_controls: bool = False
    playback_features: List[str] = field(default_factory=list)
    can_edit_transcript: bool = False


@dataclass
class SampleTurn:
    """Sample conversation turn for pattern analysis."""
    speaker: str = ""  # therapist, client
    timestamp: str = ""
    text_preview: str = ""  # First 100 chars
    css_classes: List[str] = field(default_factory=list)
    html_structure: str = ""


@dataclass
class TranscriptTabResult:
    """Complete extraction result for the Transcript tab."""
    status: str  # success, error
    tab_name: str = "transcript"

    # Display format
    display_format: str = ""  # bubbles, list, columns
    layout_style: str = ""

    # Speaker labeling
    speaker_labeling: Optional[SpeakerLabeling] = None

    # Timestamp format
    timestamp_format: Optional[TimestampFormat] = None

    # UI patterns
    ui_patterns: Optional[UIPatterns] = None

    # Interaction patterns
    interaction_patterns: Optional[InteractionPatterns] = None

    # Sample turns (for pattern analysis, not content)
    sample_turns: List[SampleTurn] = field(default_factory=list)
    total_turns_visible: int = 0

    # Technical details
    tab_selector_used: str = ""
    content_container_selector: str = ""
    html_structure_summary: str = ""

    # Output files
    screenshot_path: str = ""

    # Metadata
    session_url: str = ""
    timestamp: str = ""
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Handle nested dataclasses
        if self.speaker_labeling:
            result['speaker_labeling'] = asdict(self.speaker_labeling)
        if self.timestamp_format:
            result['timestamp_format'] = asdict(self.timestamp_format)
        if self.ui_patterns:
            result['ui_patterns'] = asdict(self.ui_patterns)
        if self.interaction_patterns:
            result['interaction_patterns'] = asdict(self.interaction_patterns)
        if self.sample_turns:
            result['sample_turns'] = [asdict(t) for t in self.sample_turns]
        return result


class TranscriptTabExtractor:
    """
    Extracts Transcript tab content from Upheal session detail pages.

    Focuses on extracting UI structure and patterns, NOT actual conversation content.
    """

    BASE_URL = "https://app.upheal.io"
    LOGIN_URL = f"{BASE_URL}/login"
    SESSION_ID = "upheal_transcript_extractor"

    # Common tab selectors to try
    TAB_SELECTORS = [
        '[role="tab"]',
        '.tab-button',
        '.tabs-menu > div',
        '[data-tab]',
        'button[class*="tab"]',
        'div[class*="tab"]',
        '.MuiTab-root',
        '.ant-tabs-tab',
    ]

    # Common transcript container selectors
    TRANSCRIPT_SELECTORS = [
        '[class*="transcript"]',
        '[class*="conversation"]',
        '[class*="message"]',
        '[class*="chat"]',
        '[class*="dialog"]',
        '.messages-container',
        '.transcript-container',
    ]

    def __init__(
        self,
        headless: bool = True,
        verbose: bool = False,
        output_dir: Optional[Path] = None
    ):
        """Initialize the transcript tab extractor."""
        self.headless = headless
        self.verbose = verbose

        # Credentials
        self.email = os.getenv("UPHEAL_EMAIL")
        self.password = os.getenv("UPHEAL_PASSWORD")

        if not self.email or not self.password:
            raise ValueError(
                "Missing UPHEAL_EMAIL or UPHEAL_PASSWORD in environment.\n"
                f"Checked .env file at: {env_path}"
            )

        # Output directories
        self.scrapping_dir = Path(__file__).parent.parent
        self.screenshot_dir = self.scrapping_dir / "upheal_crawl_results"
        self.data_dir = self.scrapping_dir / "data" / "tabs"

        # Ensure directories exist
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Browser configuration
        self.browser_config = BrowserConfig(
            headless=self.headless,
            viewport_width=1920,
            viewport_height=1080,
            verbose=self.verbose,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

    def _build_login_js(self) -> str:
        """Build JavaScript to fill and submit the login form."""
        return f'''
        setTimeout(function() {{
            var emailField = document.querySelector('input[type="email"]') ||
                             document.querySelector('input[name="email"]');

            if (!emailField) {{
                console.error('EMAIL_NOT_FOUND');
                return;
            }}

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
                    if (submitBtn) {{
                        submitBtn.click();
                        console.log('LOGIN_CLICKED');
                    }}
                }}, 500);
            }}, 500);
        }}, 1000);
        '''

    def _build_tab_click_js(self) -> str:
        """Build JavaScript to click the Transcript tab."""
        return '''
        (async () => {
            // Try multiple tab selector strategies
            const tabSelectors = [
                '[role="tab"]',
                '.tab-button',
                '.tabs-menu > div',
                '[data-tab]',
                'button[class*="tab"]',
                'div[class*="tab"]',
                '.MuiTab-root',
                '.ant-tabs-tab',
                'nav button',
                'nav a'
            ];

            const transcriptKeywords = ['transcript', 'conversation', 'chat', 'dialog', 'messages'];

            let tabFound = false;
            let tabClicked = null;

            for (const selector of tabSelectors) {
                const tabs = document.querySelectorAll(selector);
                for (const tab of tabs) {
                    const text = (tab.textContent || '').toLowerCase();
                    const ariaLabel = (tab.getAttribute('aria-label') || '').toLowerCase();
                    const dataTab = (tab.getAttribute('data-tab') || '').toLowerCase();

                    for (const keyword of transcriptKeywords) {
                        if (text.includes(keyword) || ariaLabel.includes(keyword) || dataTab.includes(keyword)) {
                            tab.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            await new Promise(r => setTimeout(r, 200));
                            tab.click();
                            tabClicked = {
                                selector: selector,
                                text: tab.textContent.trim().substring(0, 100),
                                keyword: keyword
                            };
                            tabFound = true;
                            break;
                        }
                    }
                    if (tabFound) break;
                }
                if (tabFound) break;
            }

            // Wait for tab content to load
            if (tabFound) {
                await new Promise(r => setTimeout(r, 2000));
            }

            return JSON.stringify({
                success: tabFound,
                tabInfo: tabClicked
            });
        })();
        '''

    def _build_transcript_analysis_js(self) -> str:
        """Build JavaScript to analyze transcript UI structure."""
        return '''
        (() => {
            const result = {
                displayFormat: 'unknown',
                layoutStyle: '',
                speakerLabeling: {
                    therapistLabel: '',
                    clientLabel: '',
                    therapistColor: '',
                    clientColor: '',
                    therapistPosition: '',
                    clientPosition: '',
                    usesAvatars: false,
                    usesIcons: false,
                    iconDetails: ''
                },
                timestampFormat: {
                    formatPattern: '',
                    position: '',
                    visibleByDefault: true,
                    sampleValues: []
                },
                uiPatterns: {
                    hasHighlightedMoments: false,
                    highlightStyle: '',
                    hasSearchFilter: false,
                    searchLocation: '',
                    hasExportCopy: false,
                    exportOptions: [],
                    scrollBehavior: '',
                    hasJumpToTimestamp: false
                },
                interactionPatterns: {
                    messagesClickable: false,
                    clickAction: '',
                    hasAnnotations: false,
                    annotationTypes: [],
                    hasPlaybackControls: false,
                    playbackFeatures: [],
                    canEditTranscript: false
                },
                sampleTurns: [],
                totalTurnsVisible: 0,
                contentContainerSelector: '',
                htmlStructureSummary: ''
            };

            // Find transcript container
            const containerSelectors = [
                '[class*="transcript"]',
                '[class*="conversation"]',
                '[class*="message-list"]',
                '[class*="chat"]',
                '[class*="dialog"]',
                '.messages-container',
                '.transcript-container'
            ];

            let container = null;
            for (const sel of containerSelectors) {
                container = document.querySelector(sel);
                if (container) {
                    result.contentContainerSelector = sel;
                    break;
                }
            }

            if (!container) {
                // Try finding by message elements
                const messageEl = document.querySelector('[class*="message"]');
                if (messageEl) {
                    container = messageEl.closest('div[class*="container"]') || messageEl.parentElement;
                }
            }

            if (!container) {
                return JSON.stringify(result);
            }

            // Analyze display format
            const containerStyle = window.getComputedStyle(container);
            if (containerStyle.display === 'flex') {
                if (containerStyle.flexDirection === 'column') {
                    result.displayFormat = 'list';
                } else {
                    result.displayFormat = 'columns';
                }
            } else if (containerStyle.display === 'grid') {
                result.displayFormat = 'columns';
            } else {
                result.displayFormat = 'list';
            }

            // Check for bubble-style messages
            const messageEls = container.querySelectorAll('[class*="message"], [class*="bubble"], [class*="turn"]');
            if (messageEls.length > 0) {
                const firstMsg = messageEls[0];
                const msgStyle = window.getComputedStyle(firstMsg);
                if (msgStyle.borderRadius && parseInt(msgStyle.borderRadius) > 8) {
                    result.displayFormat = 'bubbles';
                }
                if (firstMsg.className.toLowerCase().includes('bubble')) {
                    result.displayFormat = 'bubbles';
                }
            }

            result.layoutStyle = `${containerStyle.display}, ${containerStyle.flexDirection || 'default'}`;

            // Analyze speaker labeling
            const speakerElements = container.querySelectorAll(
                '[class*="speaker"], [class*="author"], [class*="name"], [class*="therapist"], [class*="client"], [class*="patient"]'
            );

            speakerElements.forEach(el => {
                const text = el.textContent.toLowerCase();
                const computedStyle = window.getComputedStyle(el);

                if (text.includes('therapist') || text.includes('provider') || text.includes('clinician') || text.includes('you')) {
                    result.speakerLabeling.therapistLabel = el.textContent.trim();
                    result.speakerLabeling.therapistColor = computedStyle.color || computedStyle.backgroundColor;
                } else if (text.includes('client') || text.includes('patient')) {
                    result.speakerLabeling.clientLabel = el.textContent.trim();
                    result.speakerLabeling.clientColor = computedStyle.color || computedStyle.backgroundColor;
                }
            });

            // Check for avatars/icons
            const avatars = container.querySelectorAll('img[class*="avatar"], [class*="avatar"], svg[class*="icon"]');
            result.speakerLabeling.usesAvatars = avatars.length > 0;
            if (avatars.length > 0) {
                result.speakerLabeling.iconDetails = Array.from(avatars).slice(0, 3).map(a => a.className).join(', ');
            }

            // Analyze timestamp format
            const timeElements = container.querySelectorAll('time, [class*="time"], [class*="timestamp"], [datetime]');
            timeElements.forEach(el => {
                const text = el.textContent.trim();
                if (text && !result.timestampFormat.sampleValues.includes(text)) {
                    result.timestampFormat.sampleValues.push(text);
                }
            });

            if (result.timestampFormat.sampleValues.length > 0) {
                const sample = result.timestampFormat.sampleValues[0];
                if (sample.match(/\\d{1,2}:\\d{2}:\\d{2}/)) {
                    result.timestampFormat.formatPattern = 'HH:MM:SS';
                } else if (sample.match(/\\d{1,2}:\\d{2}/)) {
                    result.timestampFormat.formatPattern = 'MM:SS';
                } else if (sample.includes('ago')) {
                    result.timestampFormat.formatPattern = 'relative';
                }
            }

            // Check timestamp position
            if (timeElements.length > 0) {
                const timeEl = timeElements[0];
                const parent = timeEl.parentElement;
                const siblings = Array.from(parent?.children || []);
                const timeIndex = siblings.indexOf(timeEl);
                const messageIndex = siblings.findIndex(s => s.className.toLowerCase().includes('message') || s.className.toLowerCase().includes('text'));

                if (timeIndex < messageIndex || timeIndex === 0) {
                    result.timestampFormat.position = 'above';
                } else if (timeIndex > messageIndex) {
                    result.timestampFormat.position = 'below';
                } else {
                    result.timestampFormat.position = 'inline';
                }
            }

            // UI Patterns
            // Check for highlights
            const highlights = container.querySelectorAll('[class*="highlight"], [class*="key-moment"], [class*="important"]');
            result.uiPatterns.hasHighlightedMoments = highlights.length > 0;
            if (highlights.length > 0) {
                result.uiPatterns.highlightStyle = highlights[0].className;
            }

            // Check for search
            const searchInput = document.querySelector('input[type="search"], input[placeholder*="search"], [class*="search"] input');
            result.uiPatterns.hasSearchFilter = searchInput !== null;
            if (searchInput) {
                const searchParent = searchInput.closest('[class*="search"], [class*="filter"]');
                result.uiPatterns.searchLocation = searchParent ? searchParent.className : 'header';
            }

            // Check for export/copy
            const exportButtons = document.querySelectorAll('button[class*="export"], button[class*="download"], button[class*="copy"], [title*="export"], [title*="copy"]');
            result.uiPatterns.hasExportCopy = exportButtons.length > 0;
            if (exportButtons.length > 0) {
                result.uiPatterns.exportOptions = Array.from(exportButtons).map(b => b.textContent.trim() || b.title).filter(Boolean);
            }

            // Check scroll behavior
            if (container.scrollHeight > container.clientHeight) {
                // Has scrollable content
                const virtualItems = container.querySelectorAll('[style*="position: absolute"], [style*="transform: translateY"]');
                if (virtualItems.length > 5) {
                    result.uiPatterns.scrollBehavior = 'virtual';
                } else {
                    result.uiPatterns.scrollBehavior = 'standard';
                }
            }

            // Check for pagination
            const pagination = document.querySelector('[class*="pagination"], [class*="page-"]');
            if (pagination) {
                result.uiPatterns.scrollBehavior = 'pagination';
            }

            // Interaction Patterns
            // Check if messages are clickable
            const clickableMessages = container.querySelectorAll('a[class*="message"], button[class*="message"], [role="button"][class*="message"]');
            result.interactionPatterns.messagesClickable = clickableMessages.length > 0 || messageEls.length > 0;

            // Check for playback controls
            const playbackControls = document.querySelectorAll('[class*="playback"], [class*="audio"], [class*="play"], [class*="player"]');
            result.interactionPatterns.hasPlaybackControls = playbackControls.length > 0;
            if (playbackControls.length > 0) {
                result.interactionPatterns.playbackFeatures = ['play/pause', 'seek'];
            }

            // Check for edit capabilities
            const editButtons = container.querySelectorAll('[class*="edit"], button[title*="edit"], [contenteditable]');
            result.interactionPatterns.canEditTranscript = editButtons.length > 0;

            // Check for annotations
            const annotations = container.querySelectorAll('[class*="annotation"], [class*="note"], [class*="comment"]');
            result.interactionPatterns.hasAnnotations = annotations.length > 0;

            // Extract sample turns (for structure analysis, not content)
            result.totalTurnsVisible = messageEls.length;

            Array.from(messageEls).slice(0, 5).forEach((msg, i) => {
                const turn = {
                    speaker: '',
                    timestamp: '',
                    textPreview: '',
                    cssClasses: msg.className.split(' ').filter(c => c.length > 0),
                    htmlStructure: ''
                };

                // Determine speaker
                if (msg.className.toLowerCase().includes('therapist') ||
                    msg.className.toLowerCase().includes('outgoing') ||
                    msg.className.toLowerCase().includes('sent')) {
                    turn.speaker = 'therapist';
                } else if (msg.className.toLowerCase().includes('client') ||
                           msg.className.toLowerCase().includes('patient') ||
                           msg.className.toLowerCase().includes('incoming') ||
                           msg.className.toLowerCase().includes('received')) {
                    turn.speaker = 'client';
                } else {
                    // Try to determine from position
                    const style = window.getComputedStyle(msg);
                    if (style.marginLeft === 'auto' || style.alignSelf === 'flex-end') {
                        turn.speaker = 'therapist';
                    } else {
                        turn.speaker = 'client';
                    }
                }

                // Get timestamp if present
                const timeInMsg = msg.querySelector('time, [class*="time"]');
                if (timeInMsg) {
                    turn.timestamp = timeInMsg.textContent.trim();
                }

                // Get text preview (first 100 chars, anonymized)
                const textEl = msg.querySelector('[class*="text"], [class*="content"], p');
                if (textEl) {
                    turn.textPreview = textEl.textContent.substring(0, 100).replace(/[a-zA-Z]+/g, '[text]');
                }

                // HTML structure summary
                turn.htmlStructure = msg.tagName + (msg.className ? '.' + msg.className.split(' ')[0] : '');

                result.sampleTurns.push(turn);
            });

            // HTML structure summary
            result.htmlStructureSummary = container.tagName +
                (container.className ? '.' + container.className.split(' ').slice(0, 2).join('.') : '') +
                ' > ' + (messageEls[0]?.tagName || 'div') +
                (messageEls[0]?.className ? '.' + messageEls[0].className.split(' ')[0] : '');

            return JSON.stringify(result);
        })();
        '''

    def _save_screenshot(self, screenshot_data: Any, filename: str) -> str:
        """Save screenshot and return path."""
        filepath = self.screenshot_dir / filename

        if screenshot_data:
            if isinstance(screenshot_data, str):
                screenshot_data = base64.b64decode(screenshot_data)
            with open(filepath, 'wb') as f:
                f.write(screenshot_data)
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)

        return ""

    def load_session_url(self) -> Optional[str]:
        """Load session URL from Wave 1 discovery output."""
        session_file = self.scrapping_dir / "data" / "session_detail_url.json"

        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                if data.get("status") == "success":
                    return data.get("session_detail_url")
            except Exception as e:
                logger.warning(f"Failed to load session URL: {e}")

        return None

    async def extract_transcript_tab(self, session_url: str) -> TranscriptTabResult:
        """
        Extract transcript tab content from session detail page.

        Args:
            session_url: Full URL to the session detail page.

        Returns:
            TranscriptTabResult with extracted UI patterns.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"Extracting transcript tab from: {session_url}")

        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                # Step 1: Authenticate
                logger.info("Step 1: Authenticating...")

                login_config = CrawlerRunConfig(
                    session_id=self.SESSION_ID,
                    js_code=self._build_login_js(),
                    wait_for='''js:() => {
                        if (!window.__loginAttempted) {
                            window.__loginAttempted = Date.now();
                            return false;
                        }
                        if (Date.now() - window.__loginAttempted < 5000) {
                            return false;
                        }
                        if (!window.location.pathname.includes('login')) return true;
                        return false;
                    }''',
                    page_timeout=60000,
                    screenshot=True,
                )

                login_result = await crawler.arun(self.LOGIN_URL, config=login_config)

                if not login_result.success:
                    return TranscriptTabResult(
                        status="error",
                        session_url=session_url,
                        error_message=f"Login failed: {login_result.error_message}"
                    )

                if "login" in login_result.url.lower():
                    screenshot_path = self._save_screenshot(
                        login_result.screenshot,
                        f"transcript_login_failed_{timestamp}.png"
                    )
                    return TranscriptTabResult(
                        status="error",
                        session_url=session_url,
                        screenshot_path=screenshot_path,
                        error_message="Authentication failed - still on login page"
                    )

                logger.info(f"Authenticated successfully, redirected to: {login_result.url}")

                # Step 2: Navigate to session detail page
                logger.info(f"Step 2: Navigating to session detail: {session_url}")

                session_config = CrawlerRunConfig(
                    session_id=self.SESSION_ID,
                    wait_for="css:[class*='tab'], css:[role='tab']",
                    page_timeout=30000,
                    screenshot=True,
                )

                session_result = await crawler.arun(session_url, config=session_config)

                if not session_result.success:
                    return TranscriptTabResult(
                        status="error",
                        session_url=session_url,
                        error_message=f"Failed to load session page: {session_result.error_message}"
                    )

                # Step 3: Click Transcript tab
                logger.info("Step 3: Clicking Transcript tab...")

                tab_click_config = CrawlerRunConfig(
                    session_id=self.SESSION_ID,
                    js_code=self._build_tab_click_js(),
                    page_timeout=30000,
                    screenshot=True,
                )

                tab_result = await crawler.arun(session_url, config=tab_click_config)

                tab_info = {}
                if hasattr(tab_result, 'js_result') and tab_result.js_result:
                    try:
                        tab_info = json.loads(tab_result.js_result)
                        logger.info(f"Tab click result: {tab_info}")
                    except (json.JSONDecodeError, TypeError):
                        pass

                # Step 4: Wait for transcript content to load
                logger.info("Step 4: Waiting for transcript content...")
                await asyncio.sleep(2)  # Give time for content to load

                # Step 5: Analyze transcript UI structure
                logger.info("Step 5: Analyzing transcript UI structure...")

                analysis_config = CrawlerRunConfig(
                    session_id=self.SESSION_ID,
                    js_code=self._build_transcript_analysis_js(),
                    page_timeout=30000,
                    screenshot=True,
                )

                analysis_result = await crawler.arun(session_url, config=analysis_config)

                # Save screenshot
                screenshot_path = self._save_screenshot(
                    analysis_result.screenshot,
                    f"tab_transcript_{timestamp}.png"
                )

                # Parse analysis results
                analysis_data = {}
                if hasattr(analysis_result, 'js_result') and analysis_result.js_result:
                    try:
                        analysis_data = json.loads(analysis_result.js_result)
                        logger.info("Successfully parsed transcript analysis")
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse analysis: {e}")

                # Build result
                result = TranscriptTabResult(
                    status="success",
                    session_url=session_url,
                    screenshot_path=screenshot_path,
                    display_format=analysis_data.get('displayFormat', 'unknown'),
                    layout_style=analysis_data.get('layoutStyle', ''),
                    tab_selector_used=tab_info.get('tabInfo', {}).get('selector', '') if tab_info else '',
                    content_container_selector=analysis_data.get('contentContainerSelector', ''),
                    html_structure_summary=analysis_data.get('htmlStructureSummary', ''),
                    total_turns_visible=analysis_data.get('totalTurnsVisible', 0),
                )

                # Parse speaker labeling
                speaker_data = analysis_data.get('speakerLabeling', {})
                result.speaker_labeling = SpeakerLabeling(
                    therapist_label=speaker_data.get('therapistLabel', ''),
                    client_label=speaker_data.get('clientLabel', ''),
                    therapist_color=speaker_data.get('therapistColor', ''),
                    client_color=speaker_data.get('clientColor', ''),
                    therapist_position=speaker_data.get('therapistPosition', ''),
                    client_position=speaker_data.get('clientPosition', ''),
                    uses_avatars=speaker_data.get('usesAvatars', False),
                    uses_icons=speaker_data.get('usesIcons', False),
                    icon_details=speaker_data.get('iconDetails', ''),
                )

                # Parse timestamp format
                ts_data = analysis_data.get('timestampFormat', {})
                result.timestamp_format = TimestampFormat(
                    format_pattern=ts_data.get('formatPattern', ''),
                    position=ts_data.get('position', ''),
                    visible_by_default=ts_data.get('visibleByDefault', True),
                    sample_values=ts_data.get('sampleValues', []),
                )

                # Parse UI patterns
                ui_data = analysis_data.get('uiPatterns', {})
                result.ui_patterns = UIPatterns(
                    has_highlighted_moments=ui_data.get('hasHighlightedMoments', False),
                    highlight_style=ui_data.get('highlightStyle', ''),
                    has_search_filter=ui_data.get('hasSearchFilter', False),
                    search_location=ui_data.get('searchLocation', ''),
                    has_export_copy=ui_data.get('hasExportCopy', False),
                    export_options=ui_data.get('exportOptions', []),
                    scroll_behavior=ui_data.get('scrollBehavior', ''),
                    has_jump_to_timestamp=ui_data.get('hasJumpToTimestamp', False),
                )

                # Parse interaction patterns
                int_data = analysis_data.get('interactionPatterns', {})
                result.interaction_patterns = InteractionPatterns(
                    messages_clickable=int_data.get('messagesClickable', False),
                    click_action=int_data.get('clickAction', ''),
                    has_annotations=int_data.get('hasAnnotations', False),
                    annotation_types=int_data.get('annotationTypes', []),
                    has_playback_controls=int_data.get('hasPlaybackControls', False),
                    playback_features=int_data.get('playbackFeatures', []),
                    can_edit_transcript=int_data.get('canEditTranscript', False),
                )

                # Parse sample turns
                for turn_data in analysis_data.get('sampleTurns', []):
                    result.sample_turns.append(SampleTurn(
                        speaker=turn_data.get('speaker', ''),
                        timestamp=turn_data.get('timestamp', ''),
                        text_preview=turn_data.get('textPreview', ''),
                        css_classes=turn_data.get('cssClasses', []),
                        html_structure=turn_data.get('htmlStructure', ''),
                    ))

                return result

        except Exception as e:
            logger.exception(f"Error extracting transcript tab: {e}")
            return TranscriptTabResult(
                status="error",
                session_url=session_url,
                error_message=str(e)
            )

    def save_result(self, result: TranscriptTabResult) -> Path:
        """Save extraction result to JSON file."""
        output_file = self.data_dir / "transcript_tab.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved result to: {output_file}")
        return output_file


async def main():
    """Main entry point for transcript tab extraction."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract Transcript tab UI patterns from Upheal session detail page"
    )
    parser.add_argument(
        "--url", "-u",
        help="Session detail URL (default: load from data/session_detail_url.json)"
    )
    parser.add_argument(
        "--visible", "-v",
        action="store_true",
        help="Run browser in visible mode"
    )
    parser.add_argument(
        "--verbose", "-d",
        action="store_true",
        help="Enable verbose/debug logging"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("\n" + "=" * 70)
    print("UPHEAL TRANSCRIPT TAB EXTRACTOR")
    print("Wave 2.2 - Instance I3: Transcript Tab Specialist")
    print("=" * 70 + "\n")

    try:
        # Initialize extractor
        extractor = TranscriptTabExtractor(
            headless=not args.visible,
            verbose=args.verbose
        )

        # Get session URL
        session_url = args.url
        if not session_url:
            session_url = extractor.load_session_url()
            if not session_url:
                print("[ERROR] No session URL provided and none found in data/session_detail_url.json")
                print("Run upheal_session_detail_scraper.py first or provide --url")
                return 1

        print(f"Session URL: {session_url}")
        print(f"Browser:     {'Visible' if args.visible else 'Headless'}")
        print("-" * 70)

        # Extract transcript tab
        print("\n[Extracting] Transcript tab content...")
        result = await extractor.extract_transcript_tab(session_url)

        # Save result
        output_file = extractor.save_result(result)

        # Print summary
        print("\n" + "=" * 70)
        print("EXTRACTION RESULT")
        print("=" * 70)

        if result.status == "success":
            print(f"Status:              SUCCESS")
            print(f"Display Format:      {result.display_format}")
            print(f"Layout Style:        {result.layout_style}")
            print(f"Total Turns Visible: {result.total_turns_visible}")

            if result.speaker_labeling:
                print(f"\nSpeaker Labeling:")
                print(f"  Therapist Label:   {result.speaker_labeling.therapist_label or 'Not found'}")
                print(f"  Client Label:      {result.speaker_labeling.client_label or 'Not found'}")
                print(f"  Therapist Color:   {result.speaker_labeling.therapist_color or 'Not detected'}")
                print(f"  Client Color:      {result.speaker_labeling.client_color or 'Not detected'}")
                print(f"  Uses Avatars:      {result.speaker_labeling.uses_avatars}")

            if result.timestamp_format:
                print(f"\nTimestamp Format:")
                print(f"  Pattern:           {result.timestamp_format.format_pattern or 'Unknown'}")
                print(f"  Position:          {result.timestamp_format.position or 'Unknown'}")
                if result.timestamp_format.sample_values:
                    print(f"  Samples:           {', '.join(result.timestamp_format.sample_values[:3])}")

            if result.ui_patterns:
                print(f"\nUI Patterns:")
                print(f"  Highlighted Moments: {result.ui_patterns.has_highlighted_moments}")
                print(f"  Search/Filter:       {result.ui_patterns.has_search_filter}")
                print(f"  Export/Copy:         {result.ui_patterns.has_export_copy}")
                print(f"  Scroll Behavior:     {result.ui_patterns.scroll_behavior or 'Standard'}")

            if result.interaction_patterns:
                print(f"\nInteraction Patterns:")
                print(f"  Messages Clickable:  {result.interaction_patterns.messages_clickable}")
                print(f"  Has Playback:        {result.interaction_patterns.has_playback_controls}")
                print(f"  Can Edit:            {result.interaction_patterns.can_edit_transcript}")

            print(f"\nOutput Files:")
            print(f"  Screenshot: {result.screenshot_path}")
            print(f"  JSON Data:  {output_file}")

            # Key UI patterns summary
            print("\n" + "-" * 70)
            print("KEY UI PATTERNS FOR THERAPYBRIDGE:")
            print("-" * 70)
            patterns = []
            if result.display_format:
                patterns.append(f"1. Display format: {result.display_format}")
            if result.speaker_labeling and (result.speaker_labeling.therapist_color or result.speaker_labeling.uses_avatars):
                patterns.append(f"2. Speaker differentiation: colors/avatars")
            if result.ui_patterns and result.ui_patterns.has_playback_controls:
                patterns.append("3. Audio playback integration")
            if result.timestamp_format and result.timestamp_format.format_pattern:
                patterns.append(f"4. Timestamp format: {result.timestamp_format.format_pattern}")

            for pattern in patterns[:3]:
                print(f"  {pattern}")

            return 0
        else:
            print(f"Status:  ERROR")
            print(f"Message: {result.error_message}")
            if result.screenshot_path:
                print(f"Debug Screenshot: {result.screenshot_path}")
            return 1

    except ValueError as e:
        print(f"\n[ERROR] Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
