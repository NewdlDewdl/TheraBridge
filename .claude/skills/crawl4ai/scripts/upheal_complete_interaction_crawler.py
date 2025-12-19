#!/usr/bin/env python3
"""
Upheal.io Complete Interaction Crawler
Clicks EVERY button, explores EVERY modal, captures EVERY state change
"""
import asyncio
import json
import os
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Load credentials
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

UPHEAL_EMAIL = os.getenv("UPHEAL_EMAIL")
OUTPUT_DIR = Path("upheal_complete_interaction_results")
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
INTERACTION_LOG = []

def save_screenshot(screenshot_data, filename):
    if screenshot_data:
        if isinstance(screenshot_data, str):
            screenshot_data = base64.b64decode(screenshot_data)
        with open(OUTPUT_DIR / filename, "wb") as f:
            f.write(screenshot_data)
        return True
    return False

def save_content(content, filename):
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        f.write(content)

def save_json(data, filename):
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_interaction(action, element_info, before_url, after_url, notes=""):
    INTERACTION_LOG.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "element": element_info,
        "before_url": before_url,
        "after_url": after_url,
        "notes": notes
    })

async def main():
    print("🚀 Upheal.io COMPLETE Interactive Crawler")
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
        
        # Step 1: Login
        print("\n🔐 STEP 1: Manual Login")
        print("-"*70)
        
        login_config = CrawlerRunConfig(
            session_id="upheal_complete_session",
            page_timeout=120000,
            screenshot=True,
        )

        login_result = await crawler.arun(
            url="https://app.upheal.io/login",
            config=login_config
        )

        save_screenshot(login_result.screenshot, f"00_login_{TIMESTAMP}.png")
        print("\n⏸  You have 60 seconds to log in manually...")
        for i in range(60, 0, -10):
            print(f"   {i} seconds remaining...")
            await asyncio.sleep(10)

        print("\n✅ Starting comprehensive interaction crawl...\n")

        # Step 2: Sessions page - Click ALL buttons
        print("🔘 STEP 2: Sessions Page - Interactive Exploration")
        print("-"*70)

        sessions_config = CrawlerRunConfig(
            session_id="upheal_complete_session",
            page_timeout=30000,
            screenshot=True,
            js_code="""
            // Scroll through page
            window.scrollTo(0, document.body.scrollHeight);
            await new Promise(r => setTimeout(r, 1000));
            window.scrollTo(0, 0);
            """,
        )

        sessions_result = await crawler.arun(
            url="https://app.upheal.io/sessions",
            config=sessions_config
        )

        save_screenshot(sessions_result.screenshot, f"01_sessions_initial_{TIMESTAMP}.png")
        save_content(sessions_result.markdown, f"01_sessions_initial_{TIMESTAMP}.md")

        print(f"✅ Sessions page loaded: {len(sessions_result.markdown)} chars")

        # Get page handle for interaction
        page = crawler.crawler_strategy.context_manager.active_page
        
        if page is None:
            print("❌ Could not get page handle - trying alternative approach")
            # Continue with JS-based interactions
        else:
            print("✅ Got page handle for direct interaction")

            # Discover all buttons on Sessions page
            print("\n🔍 Discovering all interactive elements...")
            
            buttons_js = """
            () => {
                const buttons = [];
                document.querySelectorAll('button').forEach((btn, idx) => {
                    const text = btn.innerText?.trim() || btn.getAttribute('aria-label') || btn.title || '';
                    const classes = btn.className || '';
                    buttons.push({
                        index: idx,
                        text: text,
                        classes: classes,
                        visible: btn.offsetParent !== null,
                        disabled: btn.disabled
                    });
                });
                return buttons;
            }
            """
            
            buttons = await page.evaluate(buttons_js)
            visible_buttons = [b for b in buttons if b['visible'] and not b['disabled']]
            
            print(f"   Found {len(buttons)} buttons ({len(visible_buttons)} visible)")
            
            # Click each visible button and capture state
            interaction_count = 0
            for btn in visible_buttons[:20]:  # Limit to first 20 to avoid endless loops
                try:
                    print(f"\n🔘 Clicking button: '{btn['text'][:50]}...'")
                    
                    before_url = page.url
                    
                    # Click by index
                    click_js = f"""
                    () => {{
                        const buttons = document.querySelectorAll('button');
                        const btn = buttons[{btn['index']}];
                        if (btn) {{
                            btn.click();
                            return true;
                        }}
                        return false;
                    }}
                    """
                    
                    clicked = await page.evaluate(click_js)
                    
                    if not clicked:
                        print(f"   ⚠️  Could not click button {btn['index']}")
                        continue
                    
                    # Wait for any modals/changes
                    await asyncio.sleep(2)
                    
                    after_url = page.url
                    
                    # Capture screenshot after click
                    screenshot = await page.screenshot()
                    safe_name = btn['text'][:30].replace(' ', '_').replace('/', '_')
                    save_screenshot(screenshot, f"interaction_{interaction_count:02d}_{safe_name}_{TIMESTAMP}.png")
                    
                    # Check for modals
                    modal_check = """
                    () => {
                        const modals = document.querySelectorAll('[role="dialog"], .modal, [class*="modal"]');
                        return Array.from(modals).map(m => ({
                            visible: m.offsetParent !== null,
                            text: m.innerText?.substring(0, 200),
                            class: m.className
                        }));
                    }
                    """
                    
                    modals = await page.evaluate(modal_check)
                    visible_modals = [m for m in modals if m['visible']]
                    
                    # Get page content after interaction
                    page_content = await page.content()
                    save_content(page_content, f"interaction_{interaction_count:02d}_{safe_name}_html_{TIMESTAMP}.html")
                    
                    log_interaction(
                        action="button_click",
                        element_info=btn['text'],
                        before_url=before_url,
                        after_url=after_url,
                        notes=f"Modals appeared: {len(visible_modals)}, URL changed: {before_url != after_url}"
                    )
                    
                    print(f"   ✅ Captured state after click")
                    print(f"      Modals: {len(visible_modals)}, URL change: {before_url != after_url}")
                    
                    # Close any modals (press Escape)
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1)
                    
                    # Navigate back if URL changed
                    if before_url != after_url:
                        print(f"   ↩️  Navigating back to {before_url}")
                        await page.goto(before_url)
                        await asyncio.sleep(2)
                    
                    interaction_count += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Error clicking button: {e}")
                    continue

            # Step 3: Explore each session detail page
            print(f"\n\n📄 STEP 3: Session Detail Pages")
            print("-"*70)
            
            # Find all session detail links
            session_links_js = """
            () => {
                const links = [];
                document.querySelectorAll('a[href*="/detail/"]').forEach(link => {
                    links.push({
                        href: link.getAttribute('href'),
                        text: link.innerText?.trim().substring(0, 100)
                    });
                });
                return links;
            }
            """
            
            session_links = await page.evaluate(session_links_js)
            print(f"Found {len(session_links)} session detail links")
            
            for idx, link in enumerate(session_links[:3]):  # Explore first 3 sessions
                print(f"\n📋 Session {idx + 1}: {link['text'][:60]}...")
                
                detail_url = f"https://app.upheal.io{link['href']}" if link['href'].startswith('/') else link['href']
                
                await page.goto(detail_url)
                await asyncio.sleep(3)
                
                # Capture initial state
                screenshot = await page.screenshot()
                save_screenshot(screenshot, f"session_{idx + 1:02d}_initial_{TIMESTAMP}.png")
                
                content = await page.content()
                save_content(content, f"session_{idx + 1:02d}_initial_{TIMESTAMP}.html")
                
                # Find all tabs
                tabs_js = """
                () => {
                    const tabs = [];
                    document.querySelectorAll('[role="tab"], [role="tablist"] button').forEach((tab, idx) => {
                        tabs.push({
                            index: idx,
                            text: tab.innerText?.trim(),
                            selected: tab.getAttribute('aria-selected') === 'true',
                            visible: tab.offsetParent !== null
                        });
                    });
                    return tabs;
                }
                """
                
                tabs = await page.evaluate(tabs_js)
                visible_tabs = [t for t in tabs if t['visible']]
                
                if visible_tabs:
                    print(f"   Found {len(visible_tabs)} tabs: {', '.join([t['text'] for t in visible_tabs])}")
                    
                    # Click each tab
                    for tab in visible_tabs:
                        try:
                            print(f"   🔖 Clicking tab: {tab['text']}")
                            
                            click_tab_js = f"""
                            () => {{
                                const tabs = document.querySelectorAll('[role="tab"], [role="tablist"] button');
                                const tab = tabs[{tab['index']}];
                                if (tab) {{
                                    tab.click();
                                    return true;
                                }}
                                return false;
                            }}
                            """
                            
                            await page.evaluate(click_tab_js)
                            await asyncio.sleep(1.5)
                            
                            # Capture tab content
                            screenshot = await page.screenshot()
                            safe_tab_name = tab['text'][:20].replace(' ', '_')
                            save_screenshot(screenshot, f"session_{idx + 1:02d}_tab_{safe_tab_name}_{TIMESTAMP}.png")
                            
                            print(f"      ✅ Captured tab content")
                            
                        except Exception as e:
                            print(f"      ⚠️  Error clicking tab: {e}")
                
                # Find and click action buttons on this session
                action_buttons_js = """
                () => {
                    const buttons = [];
                    document.querySelectorAll('button').forEach((btn, idx) => {
                        const text = btn.innerText?.trim() || '';
                        if (text && btn.offsetParent !== null && !btn.disabled) {
                            buttons.push({
                                index: idx,
                                text: text
                            });
                        }
                    });
                    return buttons;
                }
                """
                
                action_buttons = await page.evaluate(action_buttons_js)
                print(f"   Found {len(action_buttons)} action buttons")
                
                # Click first 5 action buttons (Edit, Delete, etc.)
                for btn_idx, btn in enumerate(action_buttons[:5]):
                    try:
                        print(f"   🔘 Clicking: {btn['text'][:30]}")
                        
                        click_action_js = f"""
                        () => {{
                            const buttons = document.querySelectorAll('button');
                            buttons[{btn['index']}].click();
                        }}
                        """
                        
                        await page.evaluate(click_action_js)
                        await asyncio.sleep(1.5)
                        
                        # Capture modal/dialog
                        screenshot = await page.screenshot()
                        safe_btn_name = btn['text'][:20].replace(' ', '_')
                        save_screenshot(screenshot, f"session_{idx + 1:02d}_action_{safe_btn_name}_{TIMESTAMP}.png")
                        
                        # Close modal
                        await page.keyboard.press("Escape")
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        print(f"      ⚠️  Error: {e}")

        # Save comprehensive report
        print("\n\n📊 STEP 4: Generating Report")
        print("-"*70)
        
        report = {
            "timestamp": TIMESTAMP,
            "email": UPHEAL_EMAIL,
            "interactions": INTERACTION_LOG,
            "total_interactions": len(INTERACTION_LOG),
            "files_generated": len(list(OUTPUT_DIR.glob("*")))
        }
        
        save_json(report, f"COMPLETE_INTERACTION_REPORT_{TIMESTAMP}.json")
        
        print("\n" + "="*70)
        print("✅ COMPLETE INTERACTION CRAWL FINISHED!")
        print("="*70)
        print(f"📁 Output: {OUTPUT_DIR}")
        print(f"🔘 Interactions: {len(INTERACTION_LOG)}")
        print(f"📄 Files: {len(list(OUTPUT_DIR.glob('*')))}")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
