#!/usr/bin/env python3
"""
Upheal Session Detail URL Discovery Script

Wave 1 of the Upheal Session Detail Deep Dive orchestration.

This script:
1. Authenticates to Upheal.io using crawl4ai browser automation
2. Navigates to the sessions list page
3. Discovers session detail URLs from the page
4. Returns the first available session detail URL for Wave 2 agents

The session detail URL is saved to data/session_detail_url.json for
subsequent Wave 2 agents to extract the 4 tabs (Overview, Transcript,
AI Notes, Audio).

Authentication Engineer (Instance I1) - Wave 1

Usage:
    python upheal_session_detail_scraper.py           # Headless mode
    python upheal_session_detail_scraper.py --visible # Show browser
    python upheal_session_detail_scraper.py --cached  # Use existing crawl data
"""

import asyncio
import json
import re
import sys
import os
import base64
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    # Try the skills directory env
    env_path = Path(__file__).parent.parent / ".claude" / "skills" / "crawl4ai" / ".env"
load_dotenv(env_path)


@dataclass
class SessionDetailDiscoveryResult:
    """Result of session detail URL discovery."""
    status: str  # "success" | "error"
    session_detail_url: Optional[str] = None
    session_id: Optional[str] = None
    client_id: Optional[str] = None
    all_sessions: Optional[list] = None
    error_message: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class SessionDetailDiscovery:
    """
    Discovers session detail URLs from Upheal's authenticated sessions page.

    Handles authentication and session discovery in a single browser context
    to maintain login state across requests.

    Session detail URLs follow the pattern:
        https://app.upheal.io/detail/{client_uuid}/{session_uuid}

    Usage:
        discovery = SessionDetailDiscovery()
        result = await discovery.discover_first_session()

        if result.status == "success":
            print(f"Found session: {result.session_detail_url}")
    """

    # Upheal URL patterns
    BASE_URL = "https://app.upheal.io"
    LOGIN_URL = f"{BASE_URL}/login"
    SESSIONS_URL = f"{BASE_URL}/sessions"

    # Regex patterns for session detail URLs
    # Pattern: /detail/{client_uuid}/{session_uuid}
    SESSION_DETAIL_PATTERN = re.compile(
        r'/detail/([a-f0-9-]{36})/([a-f0-9-]{36})',
        re.IGNORECASE
    )

    # Default session ID for browser persistence
    SESSION_ID = "upheal_session_detail_discovery"

    def __init__(
        self,
        headless: bool = True,
        verbose: bool = False,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize the session detail discovery.

        Args:
            headless: Run browser in headless mode (default True).
            verbose: Enable verbose logging.
            output_dir: Directory to save output files. Defaults to Scrapping/data.
        """
        self.headless = headless
        self.verbose = verbose
        self._is_authenticated = False

        # Load credentials from environment
        self.email = os.getenv("UPHEAL_EMAIL")
        self.password = os.getenv("UPHEAL_PASSWORD")

        if not self.email or not self.password:
            raise ValueError(
                "Missing UPHEAL_EMAIL or UPHEAL_PASSWORD in environment.\n"
                f"Checked .env file at: {env_path}"
            )

        # Output directory
        if output_dir is None:
            self.output_dir = Path(__file__).parent / "data"
        else:
            self.output_dir = Path(output_dir)

        # Existing crawl results directory (for fallback)
        self.crawl_results_dir = Path(__file__).parent / "upheal_crawl_results"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        (async () => {{
            // Wait for React to render
            await new Promise(r => setTimeout(r, 1500));

            // Find email field
            const emailField = document.querySelector('input[type="email"]') ||
                               document.querySelector('input[name="email"]') ||
                               document.querySelector('#email');
            if (!emailField) {{
                console.error('EMAIL_FIELD_NOT_FOUND');
                return;
            }}

            // Fill email with native events for React
            emailField.focus();
            emailField.value = '{self.email}';
            emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
            emailField.dispatchEvent(new Event('change', {{ bubbles: true }}));

            // Find password field
            const passwordField = document.querySelector('input[type="password"]');
            if (!passwordField) {{
                console.error('PASSWORD_FIELD_NOT_FOUND');
                return;
            }}

            // Fill password
            passwordField.focus();
            passwordField.value = '{self.password}';
            passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
            passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));

            // Wait before submit
            await new Promise(r => setTimeout(r, 500));

            // Find and click submit
            const submitBtn = document.querySelector('button[type="submit"]') ||
                              document.querySelector('input[type="submit"]');
            if (submitBtn) {{
                submitBtn.click();
                console.log('LOGIN_SUBMITTED');
            }} else {{
                const form = emailField.closest('form');
                if (form) form.submit();
            }}
        }})();
        '''

    def _build_link_extraction_js(self) -> str:
        """Build JavaScript to extract session detail links."""
        return '''
        (() => {
            const links = [];
            document.querySelectorAll('a[href*="/detail/"]').forEach(a => {
                const match = a.href.match(/\\/detail\\/([a-f0-9-]{36})\\/([a-f0-9-]{36})/i);
                if (match) {
                    links.push({
                        url: a.href,
                        client_id: match[1],
                        session_id: match[2],
                        text: a.textContent.trim().substring(0, 200)
                    });
                }
            });
            return JSON.stringify(links);
        })();
        '''

    def _extract_session_urls(self, content: str) -> list[dict]:
        """
        Extract session detail URLs from page content.

        Looks for URLs matching /detail/{client_uuid}/{session_uuid} pattern.

        Args:
            content: HTML or markdown content to search.

        Returns:
            List of dicts with url, client_id, and session_id.
        """
        sessions = []
        seen_urls = set()

        # Find all session detail URLs
        matches = self.SESSION_DETAIL_PATTERN.findall(content)

        for client_id, session_id in matches:
            url = f"{self.BASE_URL}/detail/{client_id}/{session_id}"

            if url not in seen_urls:
                seen_urls.add(url)
                sessions.append({
                    "url": url,
                    "client_id": client_id,
                    "session_id": session_id
                })
                logger.debug(f"Found session: {url}")

        logger.info(f"Extracted {len(sessions)} unique session URLs")
        return sessions

    def load_from_existing_crawl(self) -> Optional[SessionDetailDiscoveryResult]:
        """
        Load session URLs from existing crawl data (fallback).

        Checks upheal_crawl_results/ for previously discovered links.

        Returns:
            SessionDetailDiscoveryResult if found, None otherwise.
        """
        # Look for discovered links JSON
        links_files = list(self.crawl_results_dir.glob("*_discovered_links_*.json"))

        if not links_files:
            logger.info("No existing crawl data found")
            return None

        # Use most recent file
        links_file = sorted(links_files)[-1]
        logger.info(f"Loading from existing crawl: {links_file}")

        try:
            with open(links_file, 'r') as f:
                data = json.load(f)

            # Extract session detail URLs
            sessions = []
            for url in data.get("discovered_urls", []):
                match = self.SESSION_DETAIL_PATTERN.search(url)
                if match:
                    sessions.append({
                        "url": url,
                        "client_id": match.group(1),
                        "session_id": match.group(2)
                    })

            if sessions:
                first = sessions[0]
                return SessionDetailDiscoveryResult(
                    status="success",
                    session_detail_url=first["url"],
                    session_id=first["session_id"],
                    client_id=first["client_id"],
                    all_sessions=sessions
                )

        except Exception as e:
            logger.warning(f"Failed to load existing crawl: {e}")

        return None

    async def discover_sessions(self, use_cache: bool = False) -> SessionDetailDiscoveryResult:
        """
        Discover all session detail URLs from the sessions page.

        Performs full authentication and crawling in a single browser context
        to maintain session state.

        Args:
            use_cache: If True, try to use existing crawl data first.

        Returns:
            SessionDetailDiscoveryResult with all discovered sessions.
        """
        # Try cache first if requested
        if use_cache:
            cached = self.load_from_existing_crawl()
            if cached:
                logger.info("Using cached session URLs")
                return cached

        logger.info("Starting authenticated session discovery...")

        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                # Step 1: Login
                logger.info(f"Authenticating as: {self.email}")

                login_config = CrawlerRunConfig(
                    session_id=self.SESSION_ID,
                    js_code=self._build_login_js(),
                    wait_for='''js:() => {
                        // Success: redirected away from login
                        if (!window.location.pathname.includes('login')) return true;
                        // Error: check for error messages
                        const error = document.querySelector('[class*="error"]');
                        if (error && error.textContent.trim()) return true;
                        return false;
                    }''',
                    page_timeout=60000,
                    screenshot=True,
                )

                login_result = await crawler.arun(self.LOGIN_URL, config=login_config)

                if not login_result.success:
                    return SessionDetailDiscoveryResult(
                        status="error",
                        error_message=f"Login page failed: {login_result.error_message}"
                    )

                # Check if we're still on login page (auth failed)
                if "login" in login_result.url.lower():
                    # Save screenshot for debugging
                    if login_result.screenshot:
                        debug_path = self.output_dir / "login_failed_debug.png"
                        screenshot_data = login_result.screenshot
                        if isinstance(screenshot_data, str):
                            screenshot_data = base64.b64decode(screenshot_data)
                        with open(debug_path, 'wb') as f:
                            f.write(screenshot_data)
                        logger.error(f"Login failed - screenshot saved to {debug_path}")

                    return SessionDetailDiscoveryResult(
                        status="error",
                        error_message="Authentication failed - still on login page"
                    )

                logger.info(f"Login successful - redirected to: {login_result.url}")
                self._is_authenticated = True

                # Step 2: Fetch sessions page
                logger.info(f"Fetching sessions page: {self.SESSIONS_URL}")

                sessions_config = CrawlerRunConfig(
                    session_id=self.SESSION_ID,
                    js_code=self._build_link_extraction_js(),
                    wait_for="css:a[href*='/detail/']",
                    page_timeout=30000,
                    screenshot=True,
                )

                sessions_result = await crawler.arun(self.SESSIONS_URL, config=sessions_config)

                if not sessions_result.success:
                    return SessionDetailDiscoveryResult(
                        status="error",
                        error_message=f"Sessions page failed: {sessions_result.error_message}"
                    )

                # Extract sessions from JS result or markdown
                sessions = []

                # Try JS result first (more reliable)
                if hasattr(sessions_result, 'js_result') and sessions_result.js_result:
                    try:
                        sessions = json.loads(sessions_result.js_result)
                        logger.info(f"Extracted {len(sessions)} sessions via JavaScript")
                    except (json.JSONDecodeError, TypeError):
                        pass

                # Fallback to markdown/HTML parsing
                if not sessions:
                    content = f"{sessions_result.html or ''}\n{sessions_result.markdown or ''}"
                    sessions = self._extract_session_urls(content)

                if not sessions:
                    # Save screenshot for debugging
                    if sessions_result.screenshot:
                        debug_path = self.output_dir / "sessions_page_debug.png"
                        screenshot_data = sessions_result.screenshot
                        if isinstance(screenshot_data, str):
                            screenshot_data = base64.b64decode(screenshot_data)
                        with open(debug_path, 'wb') as f:
                            f.write(screenshot_data)
                        logger.warning(f"No sessions found - screenshot saved to {debug_path}")

                    return SessionDetailDiscoveryResult(
                        status="error",
                        error_message="No session detail URLs found on sessions page"
                    )

                # Return first session
                first_session = sessions[0]

                return SessionDetailDiscoveryResult(
                    status="success",
                    session_detail_url=first_session["url"],
                    session_id=first_session["session_id"],
                    client_id=first_session["client_id"],
                    all_sessions=sessions
                )

        except Exception as e:
            logger.exception(f"Error discovering sessions: {e}")
            return SessionDetailDiscoveryResult(
                status="error",
                error_message=str(e)
            )

    async def discover_first_session(self, use_cache: bool = False) -> SessionDetailDiscoveryResult:
        """
        Convenience method to discover and return just the first session.

        This is the main entry point for Wave 1 of the orchestration.

        Args:
            use_cache: If True, try to use existing crawl data first.

        Returns:
            SessionDetailDiscoveryResult with the first session URL.
        """
        return await self.discover_sessions(use_cache=use_cache)

    def save_result(self, result: SessionDetailDiscoveryResult) -> Path:
        """
        Save the discovery result to JSON file.

        Args:
            result: The discovery result to save.

        Returns:
            Path to the saved file.
        """
        output_file = self.output_dir / "session_detail_url.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved result to: {output_file}")
        return output_file


async def main():
    """
    Main entry point for session detail URL discovery.

    Usage:
        python upheal_session_detail_scraper.py
        python upheal_session_detail_scraper.py --visible  # Show browser
        python upheal_session_detail_scraper.py --verbose  # Debug logging
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Discover Upheal session detail URLs for Wave 2 extraction"
    )
    parser.add_argument(
        "--visible", "-v",
        action="store_true",
        help="Run browser in visible mode (not headless)"
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
    print("UPHEAL SESSION DETAIL URL DISCOVERY")
    print("Wave 1 - Authentication & URL Discovery")
    print("=" * 70 + "\n")

    # Initialize discovery
    discovery = SessionDetailDiscovery(
        headless=not args.visible,
        verbose=args.verbose
    )

    # Step 1: Authenticate
    print("[Step 1] Authenticating to Upheal...")
    auth_result = await discovery.authenticate()

    if auth_result.status != AuthStatus.SUCCESS:
        print(f"\n[ERROR] Authentication failed: {auth_result.error_message}")
        return 1

    print(f"         Authenticated as: {discovery.scraper.credentials['email']}")

    # Step 2: Discover sessions
    print("\n[Step 2] Discovering session detail URLs...")
    result = await discovery.discover_first_session()

    # Step 3: Save result
    print("\n[Step 3] Saving result...")
    output_file = discovery.save_result(result)

    # Print summary
    print("\n" + "=" * 70)
    print("DISCOVERY RESULT")
    print("=" * 70)

    if result.status == "success":
        print(f"Status:            SUCCESS")
        print(f"Session Detail URL: {result.session_detail_url}")
        print(f"Session ID:        {result.session_id}")
        print(f"Client ID:         {result.client_id}")
        print(f"Total Sessions:    {len(result.all_sessions or [])}")
        print(f"Output File:       {output_file}")

        if result.all_sessions and len(result.all_sessions) > 1:
            print(f"\nAll discovered sessions:")
            for i, session in enumerate(result.all_sessions[:5], 1):
                print(f"  {i}. {session['url']}")
            if len(result.all_sessions) > 5:
                print(f"  ... and {len(result.all_sessions) - 5} more")

        print("\n" + "=" * 70)
        print("Wave 2 agents can now extract from:")
        print(f"  {result.session_detail_url}")
        print("=" * 70 + "\n")
        return 0
    else:
        print(f"Status:  ERROR")
        print(f"Message: {result.error_message}")
        print("=" * 70 + "\n")
        return 1


# Alternative entry point for programmatic use
async def discover_session_url(
    headless: bool = True,
    verbose: bool = False
) -> SessionDetailDiscoveryResult:
    """
    Programmatic entry point for discovering session URLs.

    This function can be imported and called from other scripts
    or orchestration tools.

    Args:
        headless: Run browser in headless mode.
        verbose: Enable verbose logging.

    Returns:
        SessionDetailDiscoveryResult with session URL or error.

    Example:
        from upheal_session_detail_scraper import discover_session_url

        result = await discover_session_url()
        if result.status == "success":
            print(f"Session URL: {result.session_detail_url}")
    """
    discovery = SessionDetailDiscovery(headless=headless, verbose=verbose)
    result = await discovery.discover_first_session()
    discovery.save_result(result)
    return result


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
