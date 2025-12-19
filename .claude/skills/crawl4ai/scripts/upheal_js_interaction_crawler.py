#!/usr/bin/env python3
"""
Upheal.io JS-Based Interaction Crawler
Uses JavaScript injection to click all buttons and explore modals
"""
import asyncio
import json
import os
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

UPHEAL_EMAIL = os.getenv("UPHEAL_EMAIL")
OUTPUT_DIR = Path("upheal_js_interaction_results")
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

async def main():
    print("🚀 Upheal.io JS-Based Interactive Crawler")
    print("="*70)
    print(f"📧 Email: {UPHEAL_EMAIL}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}")
    print("="*70)

    browser_config = BrowserConfig(
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        # Login
        print("\n🔐 STEP 1: Manual Login (60 seconds)")
        print("-"*70)
        
        login_result = await crawler.arun(
            url="https://app.upheal.io/login",
            config=CrawlerRunConfig(
                session_id="upheal_js_session",
                screenshot=True
            )
        )
        
        save_screenshot(login_result.screenshot, f"00_login_{TIMESTAMP}.png")
        
        for i in range(60, 0, -10):
            print(f"   {i}s...")
            await asyncio.sleep(10)
        
        print("\n✅ Starting crawl...\n")
        
        # Sessions page - Get ALL session detail links FIRST
        print("📄 STEP 2: Discovering All Session Detail Pages")
        print("-"*70)
        
        sessions_discover_js = """
        () => {
            const links = [];
            document.querySelectorAll('a[href*="/detail/"]').forEach(link => {
                const href = link.getAttribute('href');
                if (href) {
                    links.push({
                        href: href.startsWith('http') ? href : 'https://app.upheal.io' + href,
                        text: link.innerText?.trim().substring(0, 100) || 'No text'
                    });
                }
            });
            return links;
        }
        """
        
        sessions_result = await crawler.arun(
            url="https://app.upheal.io/sessions",
            config=CrawlerRunConfig(
                session_id="upheal_js_session",
                screenshot=True,
                js_code=sessions_discover_js
            )
        )
        
        save_screenshot(sessions_result.screenshot, f"01_sessions_{TIMESTAMP}.png")
        save_content(sessions_result.markdown, f"01_sessions_{TIMESTAMP}.md")
        
        # Parse JS execution result to get session links
        session_links = sessions_result.extracted_content if sessions_result.extracted_content else []
        
        print(f"✅ Found {len(session_links)} session detail links\n")
        
        # Crawl each session detail page with ALL tabs
        print("📋 STEP 3: Exploring Session Detail Pages + Tabs")
        print("-"*70)
        
        for idx, link_info in enumerate(session_links[:5]):  # First 5 sessions
            session_url = link_info['href'] if isinstance(link_info, dict) else link_info
            print(f"\n[{idx+1}/{min(len(session_links), 5)}] {session_url}")
            
            # Initial load
            detail_result = await crawler.arun(
                url=session_url,
                config=CrawlerRunConfig(
                    session_id="upheal_js_session",
                    screenshot=True,
                    page_timeout=30000
                )
            )
            
            save_screenshot(detail_result.screenshot, f"session_{idx+1:02d}_initial_{TIMESTAMP}.png")
            save_content(detail_result.markdown, f"session_{idx+1:02d}_initial_{TIMESTAMP}.md")
            print(f"   ✅ Loaded ({len(detail_result.markdown)} chars)")
            
            # Find and click all tabs
            tabs_discover_js = """
            () => {
                const tabs = [];
                document.querySelectorAll('[role="tab"], [role="tablist"] button, button[class*="tab"]').forEach((tab, idx) => {
                    const text = tab.innerText?.trim() || tab.getAttribute('aria-label') || '';
                    if (text && tab.offsetParent !== null) {
                        tabs.push({
                            index: idx,
                            text: text
                        });
                    }
                });
                return tabs;
            }
            """
            
            tabs_result = await crawler.arun(
                url=session_url,
                config=CrawlerRunConfig(
                    session_id="upheal_js_session",
                    js_code=tabs_discover_js
                )
            )
            
            tabs = tabs_result.extracted_content if tabs_result.extracted_content else []
            
            if tabs:
                print(f"   Found {len(tabs)} tabs: {', '.join([t['text'] for t in tabs if isinstance(t, dict)])}")
                
                # Click each tab and capture
                for tab in tabs:
                    if not isinstance(tab, dict):
                        continue
                        
                    tab_text = tab.get('text', 'unknown')
                    tab_index = tab.get('index', 0)
                    
                    click_tab_js = f"""
                    async () => {{
                        await new Promise(r => setTimeout(r, 500));
                        const tabs = document.querySelectorAll('[role="tab"], [role="tablist"] button, button[class*="tab"]');
                        const tab = tabs[{tab_index}];
                        if (tab) {{
                            tab.click();
                            await new Promise(r => setTimeout(r, 1500));
                            return true;
                        }}
                        return false;
                    }}
                    """
                    
                    tab_result = await crawler.arun(
                        url=session_url,
                        config=CrawlerRunConfig(
                            session_id="upheal_js_session",
                            screenshot=True,
                            js_code=click_tab_js
                        )
                    )
                    
                    safe_tab_name = tab_text[:20].replace(' ', '_').replace('/', '_')
                    save_screenshot(tab_result.screenshot, f"session_{idx+1:02d}_tab_{safe_tab_name}_{TIMESTAMP}.png")
                    save_content(tab_result.markdown, f"session_{idx+1:02d}_tab_{safe_tab_name}_{TIMESTAMP}.md")
                    
                    print(f"      ✅ Tab '{tab_text}' captured")
        
        # Explore main pages with button clicking
        print("\n\n🔘 STEP 4: Main Pages + Button Interactions")
        print("-"*70)
        
        main_pages = [
            ("Dashboard", "https://app.upheal.io/"),
            ("Calendar", "https://app.upheal.io/calendar"),
            ("Patients", "https://app.upheal.io/patients"),
            ("Notes", "https://app.upheal.io/notes"),
            ("Templates", "https://app.upheal.io/templates"),
            ("Settings", "https://app.upheal.io/settings"),
        ]
        
        for page_name, page_url in main_pages:
            print(f"\n📄 {page_name}")
            
            # Initial capture
            page_result = await crawler.arun(
                url=page_url,
                config=CrawlerRunConfig(
                    session_id="upheal_js_session",
                    screenshot=True
                )
            )
            
            safe_name = page_name.lower().replace(' ', '_')
            save_screenshot(page_result.screenshot, f"page_{safe_name}_initial_{TIMESTAMP}.png")
            save_content(page_result.markdown, f"page_{safe_name}_initial_{TIMESTAMP}.md")
            
            print(f"   ✅ Initial capture ({len(page_result.markdown)} chars)")
            
            # Discover clickable buttons
            buttons_js = """
            () => {
                const buttons = [];
                document.querySelectorAll('button').forEach((btn, idx) => {
                    const text = btn.innerText?.trim() || btn.getAttribute('aria-label') || '';
                    if (text && btn.offsetParent !== null && !btn.disabled) {
                        buttons.push({
                            index: idx,
                            text: text
                        });
                    }
                });
                return buttons.slice(0, 10);  // First 10 buttons
            }
            """
            
            buttons_result = await crawler.arun(
                url=page_url,
                config=CrawlerRunConfig(
                    session_id="upheal_js_session",
                    js_code=buttons_js
                )
            )
            
            buttons = buttons_result.extracted_content if buttons_result.extracted_content else []
            
            if buttons:
                print(f"   Found {len(buttons)} buttons")
                
                # Click each button
                for btn in buttons[:5]:  # First 5 buttons
                    if not isinstance(btn, dict):
                        continue
                    
                    btn_text = btn.get('text', 'unknown')
                    btn_index = btn.get('index', 0)
                    
                    click_btn_js = f"""
                    async () => {{
                        const buttons = document.querySelectorAll('button');
                        const btn = buttons[{btn_index}];
                        if (btn) {{
                            btn.click();
                            await new Promise(r => setTimeout(r, 1500));
                            return true;
                        }}
                        return false;
                    }}
                    """
                    
                    click_result = await crawler.arun(
                        url=page_url,
                        config=CrawlerRunConfig(
                            session_id="upheal_js_session",
                            screenshot=True,
                            js_code=click_btn_js
                        )
                    )
                    
                    safe_btn_name = btn_text[:20].replace(' ', '_').replace('/', '_')
                    save_screenshot(click_result.screenshot, f"page_{safe_name}_btn_{safe_btn_name}_{TIMESTAMP}.png")
                    
                    print(f"      ✅ Clicked '{btn_text[:30]}'")
                    
                    # Press Escape to close any modals
                    await asyncio.sleep(0.5)
        
        print("\n\n" + "="*70)
        print("✅ JS-BASED INTERACTION CRAWL COMPLETE!")
        print("="*70)
        print(f"📁 Output: {OUTPUT_DIR}")
        print(f"📄 Files: {len(list(OUTPUT_DIR.glob('*')))}")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
