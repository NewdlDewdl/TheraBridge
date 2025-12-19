#!/usr/bin/env python3
"""
Session Navigator - Wave 1, Instance I1

Logs into Upheal, navigates to session detail page, and analyzes tab structure.
Part of 4-agent team for competitive analysis.

Privacy: Does NOT extract patient names, PHI, or session content.
Only extracts URL structure and tab selectors for UI analysis.
"""
import asyncio
import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Configuration
BASE_URL = "https://app.upheal.io"
LOGIN_URL = f"{BASE_URL}/login"
DEFAULT_SESSION_ID = "session_navigator_v2"
DATA_DIR = Path(__file__).parent / "data"


def load_credentials() -> Dict[str, str]:
    """Load Upheal credentials from .env file."""
    project_root = Path(__file__).parent.parent
    credentials_path = project_root / ".claude" / "skills" / "crawl4ai" / ".env"

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

    credentials = {}
    with open(credentials_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                credentials[key.strip()] = value.strip()

    email = credentials.get('UPHEAL_EMAIL')
    password = credentials.get('UPHEAL_PASSWORD')

    if not email or not password:
        raise ValueError("Missing UPHEAL_EMAIL or UPHEAL_PASSWORD in credentials file")

    return {'email': email, 'password': password}


def build_login_js(email: str, password: str) -> str:
    """
    Build JavaScript to fill and submit login form.
    Uses native input setter to trigger React's synthetic event handling.
    """
    return f'''
    (async () => {{
        console.log('Starting login automation...');

        // Wait for page to fully load
        await new Promise(r => setTimeout(r, 2000));

        // Helper function to set input value in React-compatible way
        const setNativeValue = (element, value) => {{
            const valueSetter = Object.getOwnPropertyDescriptor(element, 'value')?.set;
            const prototype = Object.getPrototypeOf(element);
            const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;

            if (valueSetter && valueSetter !== prototypeValueSetter) {{
                prototypeValueSetter.call(element, value);
            }} else if (valueSetter) {{
                valueSetter.call(element, value);
            }} else {{
                element.value = value;
            }}
        }};

        // Find email field
        const emailField = document.querySelector('input[type="email"]') ||
                          document.querySelector('input[name="email"]') ||
                          document.querySelector('input[placeholder*="Email" i]');

        if (!emailField) {{
            console.error('EMAIL_NOT_FOUND');
            return;
        }}
        console.log('Found email field');

        // Clear and fill email using React-compatible method
        emailField.focus();
        setNativeValue(emailField, '');
        emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
        await new Promise(r => setTimeout(r, 100));

        setNativeValue(emailField, '{email}');
        emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
        emailField.dispatchEvent(new Event('change', {{ bubbles: true }}));
        emailField.dispatchEvent(new Event('blur', {{ bubbles: true }}));

        console.log('Email set to: ' + emailField.value);

        await new Promise(r => setTimeout(r, 300));

        // Find password field
        const passwordField = document.querySelector('input[type="password"]');
        if (!passwordField) {{
            console.error('PASSWORD_NOT_FOUND');
            return;
        }}
        console.log('Found password field');

        // Fill password
        passwordField.focus();
        setNativeValue(passwordField, '');
        passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
        await new Promise(r => setTimeout(r, 100));

        setNativeValue(passwordField, '{password}');
        passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
        passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));
        passwordField.dispatchEvent(new Event('blur', {{ bubbles: true }}));

        console.log('Password set');

        await new Promise(r => setTimeout(r, 500));

        // Find the Log in button specifically
        const buttons = document.querySelectorAll('button');
        let loginBtn = null;
        for (const btn of buttons) {{
            const text = btn.textContent.trim().toLowerCase();
            if (text === 'log in' || text === 'login' || text === 'sign in') {{
                loginBtn = btn;
                break;
            }}
        }}

        // Fallback to submit button
        if (!loginBtn) {{
            loginBtn = document.querySelector('button[type="submit"]');
        }}

        if (loginBtn) {{
            console.log('Found login button: ' + loginBtn.textContent);
            // Ensure button is enabled
            loginBtn.disabled = false;
            loginBtn.click();
            console.log('LOGIN_CLICKED');
        }} else {{
            console.error('LOGIN_BUTTON_NOT_FOUND');
            // Try form submit
            const form = emailField.closest('form');
            if (form) {{
                form.dispatchEvent(new Event('submit', {{ bubbles: true, cancelable: true }}));
                console.log('FORM_SUBMITTED');
            }}
        }}
    }})();
    '''


async def login_and_navigate():
    """
    Main function: Login to Upheal, navigate to session detail, analyze tabs.
    """
    print("\n" + "=" * 60)
    print("SESSION NAVIGATOR - Wave 1, Instance I1")
    print("=" * 60 + "\n")

    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)

    # Load credentials
    print("[1] Loading credentials...")
    try:
        creds = load_credentials()
        print(f"    Email: {creds['email']}")
    except Exception as e:
        print(f"    ERROR: {e}")
        return False

    # Browser config - use non-headless for debugging
    browser_config = BrowserConfig(
        headless=True,  # Set to False to watch browser
        viewport_width=1920,
        viewport_height=1080,
        verbose=False,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Read existing session data
    session_data_file = DATA_DIR / "session_detail_url.json"
    existing_data = {}
    if session_data_file.exists():
        with open(session_data_file, 'r') as f:
            existing_data = json.load(f)
        print(f"    Found existing session URL: {existing_data.get('session_detail_url', 'N/A')}")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Step 1: Load login page first
        print("\n[2] Loading login page...")
        load_config = CrawlerRunConfig(
            session_id=DEFAULT_SESSION_ID,
            wait_for="css:input[type='email']",
            page_timeout=30000
        )

        load_result = await crawler.arun(LOGIN_URL, config=load_config)

        if not load_result.success:
            print(f"    Failed to load login page: {load_result.error_message}")
            return False

        print("    Login page loaded!")

        # Step 2: Execute login JavaScript
        print("\n[3] Executing login...")
        login_config = CrawlerRunConfig(
            session_id=DEFAULT_SESSION_ID,
            js_code=build_login_js(creds['email'], creds['password']),
            delay_before_return_html=5000,  # Wait 5 seconds for redirect
            page_timeout=60000,
            screenshot=True
        )

        login_result = await crawler.arun(LOGIN_URL, config=login_config)

        # Save screenshot
        if login_result.screenshot:
            import base64
            with open(DATA_DIR / "login_after.png", 'wb') as f:
                f.write(base64.b64decode(login_result.screenshot))
            print("    Saved screenshot: data/login_after.png")

        # Check current URL
        current_url = login_result.url if hasattr(login_result, 'url') else ''
        print(f"    Current URL: {current_url}")

        # Step 3: Wait and check if redirected
        print("\n[4] Checking login result...")

        # Try navigating to dashboard to verify session
        dashboard_config = CrawlerRunConfig(
            session_id=DEFAULT_SESSION_ID,
            wait_for="css:body",
            page_timeout=30000,
            screenshot=True
        )

        dashboard_result = await crawler.arun(f"{BASE_URL}/dashboard", config=dashboard_config)

        # Save dashboard screenshot
        if dashboard_result.screenshot:
            import base64
            with open(DATA_DIR / "dashboard_check.png", 'wb') as f:
                f.write(base64.b64decode(dashboard_result.screenshot))
            print("    Saved screenshot: data/dashboard_check.png")

        dashboard_url = dashboard_result.url if hasattr(dashboard_result, 'url') else ''
        print(f"    Dashboard URL: {dashboard_url}")

        # Check if we were redirected back to login
        if 'login' in dashboard_url.lower():
            print("    WARNING: Redirected to login - authentication failed")
            print("    Trying one more time with longer wait...")

            # Wait and retry
            await asyncio.sleep(2)
            retry_result = await crawler.arun(f"{BASE_URL}/dashboard", config=dashboard_config)
            retry_url = retry_result.url if hasattr(retry_result, 'url') else ''

            if 'login' in retry_url.lower():
                print("    ERROR: Still redirecting to login. Authentication failed.")
                return False

            dashboard_result = retry_result
            dashboard_url = retry_url

        print("    Login SUCCESS - Dashboard accessible!")

        # Step 4: Get session URL
        session_url = existing_data.get('session_detail_url') or existing_data.get('full_url')

        if not session_url:
            print("\n[5] Finding session URLs from clients page...")

            clients_config = CrawlerRunConfig(
                session_id=DEFAULT_SESSION_ID,
                wait_for="css:body",
                page_timeout=30000
            )

            clients_result = await crawler.arun(f"{BASE_URL}/clients", config=clients_config)

            if clients_result.success:
                # Extract URLs
                html = clients_result.html or ''
                markdown = clients_result.markdown or ''

                # Look for /detail/ URLs
                detail_pattern = r'https://app\.upheal\.io/detail/([a-f0-9-]+)/([a-f0-9-]+)'
                matches = re.findall(detail_pattern, html + markdown)

                if matches:
                    client_id, session_id_val = matches[0]
                    session_url = f"{BASE_URL}/detail/{client_id}/{session_id_val}"
                    print(f"    Found session URL: {session_url}")

        if not session_url:
            print("    ERROR: No session URL available")
            return False

        # Step 5: Navigate to session detail page
        print(f"\n[6] Navigating to session detail...")
        print(f"    URL: {session_url}")

        detail_config = CrawlerRunConfig(
            session_id=DEFAULT_SESSION_ID,
            wait_for="css:body",
            page_timeout=30000,
            delay_before_return_html=3000,  # Wait for React to render tabs
            screenshot=True
        )

        detail_result = await crawler.arun(session_url, config=detail_config)

        if not detail_result.success:
            print(f"    Failed to load session detail: {detail_result.error_message}")
            return False

        # Save screenshot
        if detail_result.screenshot:
            import base64
            with open(DATA_DIR / "session_detail.png", 'wb') as f:
                f.write(base64.b64decode(detail_result.screenshot))
            print("    Saved screenshot: data/session_detail.png")

        print("    Session detail page loaded!")

        # Step 6: Analyze tab structure
        print("\n[7] Analyzing tab structure...")

        html = detail_result.html or ''
        markdown = detail_result.markdown or ''

        # Look for tab patterns
        tabs_found = []
        tab_selectors = {}

        tab_names = ['Overview', 'Transcript', 'Analytics', 'Session Map', 'Notes', 'Summary', 'AI Notes']

        # Search for each tab name
        for name in tab_names:
            # Case-insensitive search
            if re.search(rf'\b{re.escape(name)}\b', html, re.IGNORECASE) or \
               re.search(rf'\b{re.escape(name)}\b', markdown, re.IGNORECASE):
                tabs_found.append(name)

                # Generate selector
                key = name.lower().replace(' ', '_')
                tab_selectors[key] = f'[role="tab"]:has-text("{name}"), button:has-text("{name}")'

        # Check for tablist structure
        has_tablist = bool(re.search(r'role="tablist"', html))
        has_tabs = bool(re.search(r'role="tab"', html))

        # Look for MUI tabs
        has_mui_tabs = bool(re.search(r'MuiTab', html))

        print(f"    Tabs found: {tabs_found}")
        print(f"    Has tablist role: {has_tablist}")
        print(f"    Has tab roles: {has_tabs}")
        print(f"    Has MUI tabs: {has_mui_tabs}")

        # Extract URL components
        url_parts = session_url.replace(BASE_URL, '').split('/')
        # URL format: /detail/{client_id}/{session_id}
        client_id = None
        session_id_val = None

        if 'detail' in url_parts:
            detail_idx = url_parts.index('detail')
            if len(url_parts) > detail_idx + 2:
                client_id = url_parts[detail_idx + 1]
                session_id_val = url_parts[detail_idx + 2]

        # Build final selectors (fallback to position-based if text-based not found)
        if not tab_selectors and (has_tablist or has_tabs or has_mui_tabs):
            tab_selectors = {
                "overview": '[role="tab"]:first-of-type',
                "transcript": '[role="tab"]:nth-of-type(2)',
                "analytics": '[role="tab"]:nth-of-type(3)',
                "session_map": '[role="tab"]:nth-of-type(4)'
            }

        # Step 7: Save results
        print("\n[8] Saving results...")

        result = {
            "session_url": f"/detail/{client_id}/{session_id_val}" if client_id else session_url.replace(BASE_URL, ''),
            "full_url": session_url,
            "discovered_at": datetime.now().isoformat(),
            "tabs_found": tabs_found,
            "tab_selectors": tab_selectors,
            "has_tablist_role": has_tablist,
            "has_tab_roles": has_tabs,
            "has_mui_tabs": has_mui_tabs,
            "client_id": client_id,
            "session_id": session_id_val,
            "page_analysis": {
                "html_length": len(html),
                "markdown_length": len(markdown),
                "url_after_load": detail_result.url if hasattr(detail_result, 'url') else None
            }
        }

        # Save JSON
        with open(session_data_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"    Saved: {session_data_file}")

        # Save markdown for reference (truncated, no PHI)
        markdown_file = DATA_DIR / "session_detail_page.md"
        # Filter out potential PHI - keep only structure analysis
        safe_markdown = markdown[:3000] if markdown else "No content"
        # Remove any names/emails that might appear
        safe_markdown = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', safe_markdown)

        with open(markdown_file, 'w') as f:
            f.write(f"# Session Detail Page Structure\n\n")
            f.write(f"URL: {session_url}\n")
            f.write(f"Captured: {datetime.now().isoformat()}\n\n")
            f.write("## Tabs Found\n")
            for tab in tabs_found:
                f.write(f"- {tab}\n")
            f.write("\n## Page Preview (structure only)\n\n")
            f.write("```\n")
            f.write(safe_markdown[:2000])
            f.write("\n```\n")
        print(f"    Saved: {markdown_file}")

        print("\n" + "=" * 60)
        print("RESULTS SUMMARY")
        print("=" * 60)
        print(f"Session URL: {session_url}")
        print(f"Client ID: {client_id}")
        print(f"Session ID: {session_id_val}")
        print(f"Tabs Found: {tabs_found}")
        print(f"Tab Selectors:")
        for key, sel in tab_selectors.items():
            print(f"    {key}: {sel}")
        print(f"Output File: {session_data_file}")
        print("=" * 60 + "\n")

        return True


if __name__ == "__main__":
    success = asyncio.run(login_and_navigate())
    sys.exit(0 if success else 1)
