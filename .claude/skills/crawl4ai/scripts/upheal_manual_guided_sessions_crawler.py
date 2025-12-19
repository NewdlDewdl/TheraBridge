#!/usr/bin/env python3
"""
Upheal Session Capture Pipeline - Manual Guided Crawler
YOU control the browser, I capture every state change.
Focus: Sessions, Audio Upload, Transcription, Diarization
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
OUTPUT_DIR = Path("upheal_sessions_pipeline_analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
capture_count = 0

def save_screenshot(screenshot_data, filename):
    if screenshot_data:
        if isinstance(screenshot_data, str):
            screenshot_data = base64.b64decode(screenshot_data)
        with open(OUTPUT_DIR / filename, "wb") as f:
            f.write(screenshot_data)
        print(f"      💾 Saved: {filename}")

def save_content(content, filename):
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        f.write(content)

def save_json(data, filename):
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

async def capture_current_state(crawler, session_id, step_name, description):
    """Capture current browser state"""
    global capture_count
    capture_count += 1
    
    print(f"\n📸 CAPTURE #{capture_count}: {step_name}")
    print(f"   Description: {description}")
    print(f"   Capturing current page state...")
    
    # Get current page URL from the browser
    current_url_js = "window.location.href"
    
    result = await crawler.arun(
        url="about:blank",  # Don't navigate, just capture current state
        config=CrawlerRunConfig(
            session_id=session_id,
            screenshot=True,
            js_code=current_url_js,
            page_timeout=5000
        )
    )
    
    filename_base = f"{capture_count:03d}_{step_name.replace(' ', '_').replace('/', '_')}"
    
    save_screenshot(result.screenshot, f"{filename_base}_{TIMESTAMP}.png")
    save_content(result.markdown, f"{filename_base}_{TIMESTAMP}.md")
    
    # Extract structured data
    extract_data_js = """
    () => {
        return {
            url: window.location.href,
            title: document.title,
            buttons: Array.from(document.querySelectorAll('button')).map(btn => ({
                text: btn.innerText?.trim().substring(0, 50),
                visible: btn.offsetParent !== null,
                disabled: btn.disabled
            })),
            modals: Array.from(document.querySelectorAll('[role="dialog"], .modal')).map(m => ({
                text: m.innerText?.substring(0, 200),
                visible: m.offsetParent !== null
            })),
            tabs: Array.from(document.querySelectorAll('[role="tab"], [role="tablist"] button')).map(tab => ({
                text: tab.innerText?.trim(),
                selected: tab.getAttribute('aria-selected') === 'true'
            }))
        };
    }
    """
    
    data_result = await crawler.arun(
        url="about:blank",
        config=CrawlerRunConfig(
            session_id=session_id,
            js_code=extract_data_js
        )
    )
    
    if data_result.extracted_content:
        save_json(data_result.extracted_content, f"{filename_base}_data_{TIMESTAMP}.json")
    
    print(f"   ✅ Captured!")

async def main():
    print("🎯 Upheal Sessions Pipeline - Manual Guided Crawler")
    print("="*70)
    print(f"📧 Email: {UPHEAL_EMAIL}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}")
    print("="*70)
    print("\n🎮 HOW THIS WORKS:")
    print("   1. I'll open the browser for you")
    print("   2. You navigate and click buttons manually")
    print("   3. Press ENTER in this terminal after each action")
    print("   4. I'll capture the state after each step")
    print("="*70)

    browser_config = BrowserConfig(
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
    )

    session_id = "upheal_manual_session"

    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        # Step 1: Login
        print("\n\n🔐 STEP 1: Login")
        print("-"*70)
        input("Press ENTER when ready to open login page...")
        
        await crawler.arun(
            url="https://app.upheal.io/login",
            config=CrawlerRunConfig(session_id=session_id, screenshot=True)
        )
        
        input("\n⏸️  Please log in manually, then press ENTER to continue...")
        await capture_current_state(crawler, session_id, "01_logged_in", "After successful login")
        
        # Step 2: Navigate to Sessions
        print("\n\n📋 STEP 2: Sessions Page Exploration")
        print("-"*70)
        input("Navigate to the Sessions page, then press ENTER...")
        await capture_current_state(crawler, session_id, "02_sessions_page", "Sessions list view")
        
        # Step 3: Explore session list buttons
        print("\n📝 Now let's explore ALL buttons on the Sessions page:")
        print("   - Schedule button")
        print("   - Upload recording button")
        print("   - Filter buttons")
        print("   - Session context menus (3-dot menus)")
        print("   - Any other buttons you see")
        
        input("\nClick the 'Schedule' button (or whatever it's called), then press ENTER...")
        await capture_current_state(crawler, session_id, "03_schedule_modal", "Schedule session modal/dialog")
        
        input("Close the modal (press Escape), then press ENTER...")
        await capture_current_state(crawler, session_id, "04_modal_closed", "Back to sessions list")
        
        input("\nClick the 'Upload Recording' or 'Session Capture' button, then press ENTER...")
        await capture_current_state(crawler, session_id, "05_upload_modal", "Audio upload interface")
        
        input("If there's a file picker or instructions, capture it, then press ENTER...")
        await capture_current_state(crawler, session_id, "06_upload_instructions", "Upload workflow details")
        
        input("Close this modal, then press ENTER...")
        
        # Step 4: Explore a session detail page
        print("\n\n📄 STEP 3: Session Detail Page Deep Dive")
        print("-"*70)
        print("Click on one of your existing sessions to open the detail view")
        input("Press ENTER when you're on a session detail page...")
        await capture_current_state(crawler, session_id, "07_session_detail", "Session detail page initial view")
        
        # Step 5: Explore all tabs
        print("\n🔖 STEP 4: Explore ALL Tabs in Session Detail")
        print("-"*70)
        print("Typical tabs might include:")
        print("   - Transcript")
        print("   - Notes / Summary")
        print("   - Recording / Audio")
        print("   - Client Profile")
        print("   - Analysis / Insights")
        
        tab_names = []
        while True:
            tab_name = input("\nEnter the tab name you're about to click (or 'done' if finished): ")
            if tab_name.lower() == 'done':
                break
            tab_names.append(tab_name)
            input(f"Click the '{tab_name}' tab, then press ENTER...")
            await capture_current_state(crawler, session_id, f"08_tab_{tab_name.replace(' ', '_')}", f"{tab_name} tab content")
        
        # Step 6: Transcript view deep dive
        print("\n\n💬 STEP 5: Transcript & Diarization Analysis")
        print("-"*70)
        print("If you're not already on the Transcript tab, navigate there now")
        input("Press ENTER when you're viewing the transcript...")
        await capture_current_state(crawler, session_id, "09_transcript_view", "Full transcript with speaker labels")
        
        print("\n🔍 Look for these features in the transcript:")
        print("   - Speaker labels (Therapist, Client, Speaker 1, etc.)")
        print("   - Timestamps")
        print("   - Confidence scores")
        print("   - Edit/correction capabilities")
        print("   - Search functionality")
        
        input("\nScroll through the transcript to see speaker changes, then press ENTER...")
        await capture_current_state(crawler, session_id, "10_transcript_speakers", "Speaker diarization in action")
        
        # Step 7: Notes/Summary view
        print("\n\n📝 STEP 6: AI-Generated Notes Analysis")
        print("-"*70)
        input("Navigate to the Notes/Summary tab, then press ENTER...")
        await capture_current_state(crawler, session_id, "11_notes_summary", "AI-generated clinical notes")
        
        print("\n📊 Look for:")
        print("   - Note sections (Assessment, Plan, etc.)")
        print("   - How they structure therapeutic insights")
        print("   - Edit capabilities")
        print("   - Export options")
        
        input("\nScroll through the full notes, then press ENTER...")
        await capture_current_state(crawler, session_id, "12_notes_full", "Complete notes view")
        
        # Step 8: Session actions
        print("\n\n⚙️ STEP 7: Session Actions & Settings")
        print("-"*70)
        input("Click the Edit button or context menu (3 dots) on this session, then press ENTER...")
        await capture_current_state(crawler, session_id, "13_session_actions", "Session action menu")
        
        print("\nExplore options like:")
        print("   - Edit session details")
        print("   - Regenerate notes")
        print("   - Download transcript")
        print("   - Delete recording")
        print("   - Share or export")
        
        action_count = 1
        while True:
            action = input(f"\nAction #{action_count} - Describe what you're clicking (or 'done'): ")
            if action.lower() == 'done':
                break
            input("Click it, then press ENTER...")
            await capture_current_state(crawler, session_id, f"14_action_{action_count}_{action.replace(' ', '_')[:20]}", f"After: {action}")
            action_count += 1
        
        # Step 9: Tools menu
        print("\n\n🛠️ STEP 8: Session Capture Tools")
        print("-"*70)
        print("Navigate back to the main sidebar")
        input("Click on 'Session Capture' under Tools menu, then press ENTER...")
        await capture_current_state(crawler, session_id, "15_session_capture_tool", "Session capture tool/settings")
        
        print("\n🔍 Look for:")
        print("   - Recording device settings")
        print("   - Audio quality settings")
        print("   - Automatic upload options")
        print("   - Integrations with calendar/EHR")
        
        input("Explore the settings, then press ENTER...")
        await capture_current_state(crawler, session_id, "16_capture_settings", "Session capture configuration")
        
        # Step 10: Note templates
        print("\n\n📋 STEP 9: Note Templates")
        print("-"*70)
        input("Navigate to Templates (under Templates & Forms), then press ENTER...")
        await capture_current_state(crawler, session_id, "17_note_templates", "Available note templates")
        
        input("Click on a template to view its structure, then press ENTER...")
        await capture_current_state(crawler, session_id, "18_template_detail", "Template structure and fields")
        
        # Final summary
        print("\n\n📊 STEP 10: Generate Analysis Report")
        print("-"*70)
        
        summary = {
            "timestamp": TIMESTAMP,
            "total_captures": capture_count,
            "tabs_explored": tab_names,
            "focus": "Sessions workflow, audio upload, transcript generation, diarization UI",
            "output_directory": str(OUTPUT_DIR.absolute())
        }
        
        save_json(summary, f"00_ANALYSIS_SUMMARY_{TIMESTAMP}.json")
        
        print("\n" + "="*70)
        print("✅ COMPREHENSIVE SESSIONS ANALYSIS COMPLETE!")
        print("="*70)
        print(f"📸 Total captures: {capture_count}")
        print(f"📁 Output: {OUTPUT_DIR}")
        print(f"📄 Files: {len(list(OUTPUT_DIR.glob('*')))}")
        print("="*70)
        print("\n🎯 Focus areas captured:")
        print("   ✅ Sessions list UI")
        print("   ✅ Upload/schedule workflows")
        print("   ✅ Session detail pages")
        print("   ✅ Transcript with diarization")
        print("   ✅ AI-generated notes")
        print("   ✅ Session actions & settings")
        print("   ✅ Capture tools & templates")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
