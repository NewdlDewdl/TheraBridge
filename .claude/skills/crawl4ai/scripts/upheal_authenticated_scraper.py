#!/usr/bin/env python3
"""
Upheal.io Interactive Authenticated Scraper
1. Opens browser for you to log in manually
2. Waits for you to complete login
3. Automatically discovers and crawls all authenticated pages
4. Saves everything to organized output directory
"""

import asyncio
import json
import os
import base64
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Load credentials
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

UPHEAL_EMAIL = os.getenv("UPHEAL_EMAIL")
OUTPUT_DIR = Path("upheal_crawl_results")


def save_screenshot(screenshot_data, filename):
    """Helper to save screenshot"""
    if screenshot_data:
        if isinstance(screenshot_data, str):
            screenshot_data = base64.b64decode(screenshot_data)
        with open(OUTPUT_DIR / filename, "wb") as f:
            f.write(screenshot_data)
        return True
    return False


def save_content(markdown, filename):
    """Helper to save markdown content"""
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        f.write(markdown)


def save_json(data, filename):
    """Helper to save JSON data"""
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def crawl_upheal_interactive():
    """Interactive crawling with manual login"""

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("🚀 Upheal.io Interactive Authenticated Scraper")
    print("="*70)
    print(f"📧 Email hint: {UPHEAL_EMAIL}")
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
    print("="*70)

    # Browser config - VISIBLE for manual login
    browser_config = BrowserConfig(
        headless=False,  # Keep browser visible
        viewport_width=1920,
        viewport_height=1080,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:

        # Step 1: Open login page and wait for manual login
        print("\n🔐 STEP 1: Manual Login")
        print("-"*70)
        print("1. A browser window will open with Upheal login page")
        print("2. Please log in manually")
        print("3. Wait until you see your dashboard/home page")
        print("4. Press ENTER in this terminal when ready to continue...")
        print("-"*70)

        login_config = CrawlerRunConfig(
            session_id="upheal_session",
            page_timeout=120000,  # 2 minutes for manual login
            screenshot=True,
        )

        login_result = await crawler.arun(
            url="https://app.upheal.io/login",
            config=login_config
        )

        if login_result.success:
            save_screenshot(login_result.screenshot, f"01_login_page_{timestamp}.png")
            print(f"\n✅ Login page opened: {login_result.url}")

            # Wait for user to log in manually (60 seconds)
            print("\n⏸  You have 60 seconds to log in manually...")
            print("   The browser window should be open - please log in now!")
            for i in range(60, 0, -5):
                print(f"   {i} seconds remaining...")
                await asyncio.sleep(5)

            print("\n✅ Continuing with authenticated crawl...")
        else:
            print(f"❌ Failed to open login page: {login_result.error_message}")
            return

        # Step 2: Verify we're logged in and discover pages
        print("\n📊 STEP 2: Discovering Authenticated Pages")
        print("-"*70)

        # Try to access the main dashboard/home
        discover_config = CrawlerRunConfig(
            session_id="upheal_session",
            page_timeout=30000,
            screenshot=True,
            js_code="""
            // Scroll to load dynamic content
            window.scrollTo(0, document.body.scrollHeight / 3);
            await new Promise(resolve => setTimeout(resolve, 1000));
            window.scrollTo(0, document.body.scrollHeight * 2/3);
            await new Promise(resolve => setTimeout(resolve, 1000));
            window.scrollTo(0, document.body.scrollHeight);
            await new Promise(resolve => setTimeout(resolve, 1000));
            window.scrollTo(0, 0);
            """,
        )

        home_result = await crawler.arun(
            url="https://app.upheal.io/",
            config=discover_config
        )

        if home_result.success:
            print(f"✅ Loaded: {home_result.url}")
            print(f"   Title: {home_result.metadata.get('title', 'N/A')}")
            print(f"   Content: {len(home_result.markdown)} chars")

            save_content(home_result.markdown, f"02_home_{timestamp}.md")
            save_screenshot(home_result.screenshot, f"02_home_{timestamp}.png")

            # Extract all internal links
            internal_links = home_result.links.get("internal", [])

            # Parse links - they're dicts with 'href' key
            discovered_urls = set()
            for link in internal_links:
                if isinstance(link, dict):
                    href = link.get("href", "")
                else:
                    href = str(link)

                if href and "app.upheal.io" in href:
                    discovered_urls.add(href)

            print(f"\n🔗 Discovered {len(discovered_urls)} unique URLs")

            # Save discovered links
            links_data = {
                "timestamp": timestamp,
                "source_url": home_result.url,
                "discovered_urls": sorted(list(discovered_urls)),
                "raw_links": internal_links
            }
            save_json(links_data, f"03_discovered_links_{timestamp}.json")

        else:
            print(f"❌ Failed to load home page")
            discovered_urls = set()

        # Step 3: Try common Upheal pages
        print("\n📑 STEP 3: Crawling Common Upheal Pages")
        print("-"*70)

        common_pages = [
            ("Dashboard", "https://app.upheal.io/dashboard"),
            ("Sessions", "https://app.upheal.io/sessions"),
            ("Patients/Clients", "https://app.upheal.io/patients"),
            ("Calendar", "https://app.upheal.io/calendar"),
            ("Notes", "https://app.upheal.io/notes"),
            ("Settings", "https://app.upheal.io/settings"),
            ("Profile", "https://app.upheal.io/profile"),
            ("Templates", "https://app.upheal.io/templates"),
        ]

        crawled_data = []

        for name, url in common_pages:
            print(f"\n📄 Crawling: {name}")

            page_config = CrawlerRunConfig(
                session_id="upheal_session",
                page_timeout=30000,
                screenshot=True,
                js_code="""
                // Scroll to load dynamic content
                window.scrollTo(0, document.body.scrollHeight / 2);
                await new Promise(resolve => setTimeout(resolve, 1000));
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(resolve => setTimeout(resolve, 1000));
                """,
            )

            try:
                result = await crawler.arun(url=url, config=page_config)

                if result.success:
                    # Check if we got redirected to login (not authenticated)
                    if "login" in result.url.lower():
                        print(f"   ⚠️  Redirected to login - may need re-authentication")
                        continue

                    # Check if it's a 404 or error page
                    if len(result.markdown) < 100 or "not found" in result.markdown.lower():
                        print(f"   ⚠️  Page not found or empty")
                        continue

                    # Success!
                    filename_base = name.lower().replace("/", "_").replace(" ", "_")
                    md_file = f"page_{filename_base}_{timestamp}.md"
                    png_file = f"page_{filename_base}_{timestamp}.png"

                    save_content(result.markdown, md_file)
                    save_screenshot(result.screenshot, png_file)

                    page_data = {
                        "name": name,
                        "url": url,
                        "actual_url": result.url,
                        "title": result.metadata.get("title", ""),
                        "content_length": len(result.markdown),
                        "links_count": len(result.links.get("internal", [])),
                        "markdown_file": md_file,
                        "screenshot_file": png_file,
                    }
                    crawled_data.append(page_data)

                    print(f"   ✅ {url}")
                    print(f"      Content: {len(result.markdown)} chars → {md_file}")
                    print(f"      Screenshot → {png_file}")
                    print(f"      Links: {len(result.links.get('internal', []))}")
                else:
                    print(f"   ❌ Failed: {result.error_message}")

            except Exception as e:
                print(f"   ❌ Error: {e}")

            # Be polite to the server
            await asyncio.sleep(2)

        # Step 4: Crawl discovered unique pages
        print("\n🌐 STEP 4: Crawling Discovered Pages")
        print("-"*70)

        # Filter out pages we already crawled
        already_crawled = {url for _, url in common_pages}
        new_urls = discovered_urls - already_crawled

        # Limit to reasonable number
        new_urls = sorted(list(new_urls))[:20]  # Max 20 additional pages

        if new_urls:
            print(f"Found {len(new_urls)} additional pages to crawl...")

            for i, url in enumerate(new_urls, 1):
                print(f"\n[{i}/{len(new_urls)}] {url}")

                page_config = CrawlerRunConfig(
                    session_id="upheal_session",
                    page_timeout=30000,
                    screenshot=True,
                )

                try:
                    result = await crawler.arun(url=url, config=page_config)

                    if result.success and "login" not in result.url.lower():
                        # Generate filename from URL
                        path_part = url.split("app.upheal.io/")[-1]
                        filename_base = path_part.replace("/", "_").replace("?", "_")[:50]

                        md_file = f"discovered_{filename_base}_{timestamp}.md"
                        png_file = f"discovered_{filename_base}_{timestamp}.png"

                        save_content(result.markdown, md_file)
                        save_screenshot(result.screenshot, png_file)

                        page_data = {
                            "name": f"Discovered: {path_part}",
                            "url": url,
                            "actual_url": result.url,
                            "title": result.metadata.get("title", ""),
                            "content_length": len(result.markdown),
                            "markdown_file": md_file,
                            "screenshot_file": png_file,
                        }
                        crawled_data.append(page_data)

                        print(f"   ✅ Saved: {md_file}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

                await asyncio.sleep(2)
        else:
            print("No additional unique pages found.")

        # Step 5: Generate summary report
        print("\n📊 STEP 5: Generating Summary Report")
        print("-"*70)

        summary = {
            "timestamp": timestamp,
            "email": UPHEAL_EMAIL,
            "total_pages_crawled": len(crawled_data),
            "pages": crawled_data,
            "statistics": {
                "total_content_chars": sum(p["content_length"] for p in crawled_data),
                "average_content_length": sum(p["content_length"] for p in crawled_data) / len(crawled_data) if crawled_data else 0,
            }
        }

        save_json(summary, f"00_SUMMARY_{timestamp}.json")

        # Create human-readable summary
        summary_text = f"""
# Upheal.io Crawl Summary
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Email: {UPHEAL_EMAIL}

## Statistics
- Total pages crawled: {len(crawled_data)}
- Total content: {summary['statistics']['total_content_chars']:,} characters
- Average page length: {summary['statistics']['average_content_length']:.0f} characters

## Pages Crawled
"""
        for page in crawled_data:
            summary_text += f"\n### {page['name']}\n"
            summary_text += f"- URL: {page['url']}\n"
            summary_text += f"- Title: {page['title']}\n"
            summary_text += f"- Content: {page['content_length']:,} chars\n"
            summary_text += f"- Files: {page['markdown_file']}, {page.get('screenshot_file', 'N/A')}\n"

        save_content(summary_text, f"00_SUMMARY_{timestamp}.md")

        print("\n" + "="*70)
        print("✅ CRAWL COMPLETE!")
        print("="*70)
        print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
        print(f"📊 Pages crawled: {len(crawled_data)}")
        print(f"📄 Summary report: 00_SUMMARY_{timestamp}.md")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(crawl_upheal_interactive())
