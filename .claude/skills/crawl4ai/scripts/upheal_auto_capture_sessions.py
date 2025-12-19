#!/usr/bin/env python3
"""
Upheal Sessions Auto-Capture
Opens browser, you navigate manually, it auto-captures every 15 seconds
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

OUTPUT_DIR = Path("upheal_sessions_pipeline_analysis")
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
    print("🎯 Upheal Sessions Auto-Capture")
    print("="*70)
    print(f"📁 Output: {OUTPUT_DIR.absolute()}")
    print("="*70)
    print("\n🎮 HOW THIS WORKS:")
    print("   1. Browser will open to Upheal login")
    print("   2. Log in manually")
    print("   3. Navigate and click whatever you want")
    print("   4. Every 15 seconds, I'll auto-capture the current state")
    print("   5. Press Ctrl+C when done (after at least 3-5 minutes)")
    print("="*70)
    print("\n✨ FOCUS AREAS TO EXPLORE:")
    print("   - Sessions page (list view)")
    print("   - Click 'Schedule' or 'Upload' buttons")
    print("   - Open a session detail page")
    print("   - Click through ALL tabs (Transcript, Notes, etc.)")
    print("   - View the transcript with speaker labels")
    print("   - Check session actions menu (Edit, Delete, etc.)")
    print("   - Explore Session Capture tool")
    print("="*70)
    
    browser_config = BrowserConfig(
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
    )

    session_id = "upheal_auto_session"
    capture_count = 0

    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        # Open login page
        print("\n🔐 Opening login page...")
        await crawler.arun(
            url="https://app.upheal.io/login",
            config=CrawlerRunConfig(
                session_id=session_id,
                screenshot=True
            )
        )
        
        print("\n⏸️  You have 60 seconds to log in...")
        for i in range(60, 0, -10):
            print(f"   {i}s...")
            await asyncio.sleep(10)
        
        print("\n✅ Starting auto-capture loop...")
        print("   Navigate manually, I'll capture every 15 seconds")
        print("   Press Ctrl+C to stop\n")
        
        try:
            while True:
                capture_count += 1
                print(f"\n📸 Auto-Capture #{capture_count} at {datetime.now().strftime('%H:%M:%S')}")
                
                # Capture current state
                result = await crawler.arun(
                    url=f"javascript:void(0)",  # Don't navigate, stay on current page
                    config=CrawlerRunConfig(
                        session_id=session_id,
                        screenshot=True,
                        page_timeout=5000,
                        js_code="window.location.href"  # Get current URL
                    )
                )
                
                filename_base = f"capture_{capture_count:03d}_{TIMESTAMP}"
                
                save_screenshot(result.screenshot, f"{filename_base}.png")
                save_content(result.markdown, f"{filename_base}.md")
                
                print(f"   ✅ Saved: {filename_base}.png + .md")
                print(f"   Content: {len(result.markdown)} chars")
                
                # Wait 15 seconds before next capture
                await asyncio.sleep(15)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping auto-capture...")
        
        print("\n" + "="*70)
        print("✅ AUTO-CAPTURE SESSION COMPLETE!")
        print("="*70)
        print(f"📸 Total captures: {capture_count}")
        print(f"📁 Output: {OUTPUT_DIR}")
        print(f"📄 Files: {len(list(OUTPUT_DIR.glob('*')))}")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
