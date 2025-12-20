#!/usr/bin/env python3
"""
Playwright script to analyze the Timeline component on dashboard-v3
- Screenshots the timeline in various states
- Tests click interactions
- Reports visual issues
"""

import asyncio
from playwright.async_api import async_playwright

async def analyze_timeline():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1440, 'height': 900})
        page = await context.new_page()

        print("=" * 60)
        print("TIMELINE ANALYSIS REPORT")
        print("=" * 60)

        # Navigate to the dashboard
        print("\n[1] Loading dashboard-v3...")
        await page.goto('http://localhost:3000/patient/dashboard-v3')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)  # Wait for animations

        # Screenshot full page
        await page.screenshot(path='screenshots/timeline_full_page.png', full_page=True)
        print("    Saved: timeline_full_page.png")

        # Find and analyze timeline component
        print("\n[2] Analyzing Timeline component structure...")

        # Check if timeline exists
        timeline = page.locator('[class*="Timeline"]').first
        if not await timeline.count():
            # Try alternative selectors
            timeline = page.locator('text=Timeline').locator('xpath=ancestor::div[contains(@class, "rounded")]').first

        if await timeline.count():
            # Get timeline bounding box
            box = await timeline.bounding_box()
            if box:
                print(f"    Timeline location: x={box['x']:.0f}, y={box['y']:.0f}")
                print(f"    Timeline size: {box['width']:.0f}x{box['height']:.0f}")

                # Screenshot just the timeline
                await timeline.screenshot(path='screenshots/timeline_component.png')
                print("    Saved: timeline_component.png")

        # Find timeline entries
        print("\n[3] Analyzing timeline entries...")
        entries = page.locator('button[aria-haspopup="dialog"]')
        entry_count = await entries.count()
        print(f"    Found {entry_count} timeline entries")

        # Check for visual elements
        print("\n[4] Checking timeline visual elements...")

        # Check for gradient line
        gradient_line = page.locator('[style*="linear-gradient"]')
        if await gradient_line.count():
            print("    [OK] Gradient connector line found")
        else:
            print("    [!] Gradient connector line NOT found")

        # Check for star icons (milestones)
        stars = page.locator('svg.lucide-star')
        star_count = await stars.count()
        print(f"    Found {star_count} milestone stars")

        # Check for timeline dots
        dots = page.locator('[class*="rounded-full"][style*="backgroundColor"]')
        dot_count = await dots.count()
        print(f"    Found {dot_count} mood dots")

        # Test clicking first entry
        print("\n[5] Testing timeline interactions...")
        if entry_count > 0:
            first_entry = entries.first
            await first_entry.click()
            await asyncio.sleep(0.5)

            # Check for popover
            popover = page.locator('[role="dialog"]')
            if await popover.count():
                print("    [OK] Popover appeared after click")
                await page.screenshot(path='screenshots/timeline_popover_open.png')
                print("    Saved: timeline_popover_open.png")

                # Analyze popover structure
                popover_box = await popover.bounding_box()
                if popover_box:
                    print(f"    Popover location: x={popover_box['x']:.0f}, y={popover_box['y']:.0f}")
                    print(f"    Popover size: {popover_box['width']:.0f}x{popover_box['height']:.0f}")

                # Check for arrow
                arrow_div = popover.locator('[class*="border-r-"]')
                if await arrow_div.count():
                    print("    [OK] Popover arrow found")
                else:
                    print("    [!] Popover arrow NOT found")

                # Click "View Full Session" if exists
                view_btn = page.locator('button:has-text("View Full Session")')
                if await view_btn.count():
                    print("    [OK] View Full Session button found")
                else:
                    print("    [!] View Full Session button NOT found")
            else:
                print("    [!] Popover did NOT appear")

        # Check layout alignment
        print("\n[6] Checking layout alignment (80/20 split)...")

        # Get the bottom row container
        bottom_row = page.locator('main > div').last
        if await bottom_row.count():
            children = bottom_row.locator('> div')
            child_count = await children.count()
            print(f"    Bottom row has {child_count} children")

            if child_count >= 2:
                session_grid = children.first
                timeline_sidebar = children.nth(1)

                session_box = await session_grid.bounding_box()
                timeline_box = await timeline_sidebar.bounding_box()

                if session_box and timeline_box:
                    total_width = session_box['width'] + timeline_box['width'] + 24  # gap
                    session_ratio = session_box['width'] / total_width * 100
                    timeline_ratio = timeline_box['width'] / total_width * 100

                    print(f"    Session grid width: {session_box['width']:.0f}px ({session_ratio:.1f}%)")
                    print(f"    Timeline width: {timeline_box['width']:.0f}px ({timeline_ratio:.1f}%)")

                    if abs(timeline_ratio - 20) > 5:
                        print(f"    [!] Timeline width deviates from 20% spec (currently {timeline_ratio:.1f}%)")
                    else:
                        print("    [OK] Layout matches 80/20 spec")

        # Check for scroll behavior
        print("\n[7] Checking timeline scrollability...")
        timeline_container = page.locator('[class*="overflow-y-auto"]').first
        if await timeline_container.count():
            scroll_height = await timeline_container.evaluate('el => el.scrollHeight')
            client_height = await timeline_container.evaluate('el => el.clientHeight')
            print(f"    Scroll height: {scroll_height}px, Client height: {client_height}px")
            if scroll_height > client_height:
                print("    [OK] Timeline is scrollable")
            else:
                print("    Timeline content fits without scrolling")

        # Summary of issues
        print("\n" + "=" * 60)
        print("ISSUES TO INVESTIGATE:")
        print("=" * 60)
        print("""
Based on architecture spec (PAGE_LAYOUT_ARCHITECTURE.md):

1. Timeline should be 20% width (in bottom row 80/20 split)
2. Connector line should be vertical gradient (teal -> lavender -> coral)
3. Dots should be mood-colored (green/blue/rose) - 10px
4. Stars should be 14px with glow effect for milestones
5. Popover should appear to the left with arrow pointing to entry
6. Click on entry should scroll to corresponding session card
7. Timeline should be sticky (stays visible while scrolling)

Please describe specific visual issues you're seeing!
""")

        await browser.close()

if __name__ == '__main__':
    import os
    os.makedirs('screenshots', exist_ok=True)
    asyncio.run(analyze_timeline())
