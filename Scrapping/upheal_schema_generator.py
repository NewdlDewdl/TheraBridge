#!/usr/bin/env python3
"""
Upheal CSS Extraction Schema Generator

Generates reusable CSS extraction schemas for Upheal feature pages using one-time LLM analysis.
This allows subsequent extractions to be 10-100x faster without repeated LLM calls.

Workflow:
1. Read filtered high-priority pages from sitemap
2. For each category, fetch ONE representative page
3. Use LLM (gpt-4o-mini) to analyze HTML and generate CSS selectors
4. Save schema to data/schemas/{category}_schema.json
5. Validate schema by testing on 2-3 additional pages

Usage:
    python upheal_schema_generator.py                    # Generate all schemas
    python upheal_schema_generator.py --category notes   # Generate single category
    python upheal_schema_generator.py --validate         # Validate existing schemas
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Version check for crawl4ai
MIN_CRAWL4AI_VERSION = "0.7.4"
try:
    from crawl4ai.__version__ import __version__ as crawl4ai_version
    from packaging import version
    if version.parse(crawl4ai_version) < version.parse(MIN_CRAWL4AI_VERSION):
        print(f"Warning: Crawl4AI {MIN_CRAWL4AI_VERSION}+ recommended (you have {crawl4ai_version})")
except ImportError:
    print(f"Crawl4AI {MIN_CRAWL4AI_VERSION}+ required. Install with: pip install crawl4ai")
    sys.exit(1)

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy

# Configuration
DATA_DIR = Path(__file__).parent / "data"
SCHEMAS_DIR = DATA_DIR / "schemas"
SITEMAP_FILE = DATA_DIR / "upheal_sitemap.json"  # Will also check for filtered version
FILTERED_SITEMAP_FILE = DATA_DIR / "upheal_filtered_sitemap.json"

# High-priority categories for competitive analysis
HIGH_PRIORITY_CATEGORIES = ["features", "notes", "sessions", "analytics", "compliance", "patients"]

# Category-specific extraction instructions for LLM
CATEGORY_INSTRUCTIONS = {
    "features": """
        Analyze this Upheal features page and generate CSS selectors to extract:
        - Feature name/title (main heading for each feature)
        - Feature description (detailed explanation)
        - Feature benefits or key capabilities
        - Screenshots or example images (if present)
        - Availability indicator (free/paid tier if visible)
        - Sub-features or bullet points

        The page likely has feature cards, sections, or grids. Find the container
        element and the child elements for each field.
    """,

    "notes": """
        Analyze this Upheal notes page (SOAP notes, DAP notes, templates) and extract:
        - Note type/format name (e.g., "SOAP Notes", "DAP Notes")
        - Description of the note format
        - Template fields or sections
        - Use cases or when to use
        - AI-powered features related to notes
        - Example outputs or previews

        Look for structured content blocks, cards, or sections describing note types.
    """,

    "sessions": """
        Analyze this Upheal sessions page and extract:
        - Session feature name
        - Feature description
        - Recording capabilities
        - Transcription features
        - Integration options
        - Privacy/security mentions

        Focus on session management features like recording, transcription, storage.
    """,

    "analytics": """
        Analyze this Upheal analytics/insights page and extract:
        - Analytics feature name
        - Metric or insight type
        - Description of what it measures
        - Visualization types (charts, graphs)
        - Data export options
        - Reporting capabilities

        Look for dashboard features, metrics, and reporting tools.
    """,

    "compliance": """
        Analyze this Upheal compliance/security page and extract:
        - Compliance standard name (HIPAA, SOC2, etc.)
        - Security feature or certification
        - Description of compliance measures
        - Data protection details
        - Privacy policy highlights
        - Certification badges or logos

        Focus on regulatory compliance, data security, and privacy measures.
    """,

    "patients": """
        Analyze this Upheal patients/client management page and extract:
        - Patient management feature name
        - Feature description
        - Client portal capabilities
        - Client notes features
        - Patient communication tools
        - Privacy/consent management

        Focus on patient relationship management, client portals, and notes.
    """
}


def load_sitemap() -> Optional[Dict]:
    """Load sitemap from file, preferring filtered version if available."""
    # Try filtered sitemap first
    if FILTERED_SITEMAP_FILE.exists():
        with open(FILTERED_SITEMAP_FILE, "r") as f:
            data = json.load(f)
            # Convert filtered sitemap format to standard format if needed
            if "pages_by_priority" in data:
                return convert_filtered_sitemap(data)
            return data

    # Fall back to regular sitemap
    if SITEMAP_FILE.exists():
        with open(SITEMAP_FILE, "r") as f:
            return json.load(f)

    print(f"Error: No sitemap found at {SITEMAP_FILE} or {FILTERED_SITEMAP_FILE}")
    return None


def convert_filtered_sitemap(filtered: Dict) -> Dict:
    """Convert filtered sitemap format to standard format with pages_by_category."""
    pages_by_category = {}

    # Process all priorities: high, medium, low
    for priority in ["high", "medium", "low"]:
        pages = filtered.get("pages_by_priority", {}).get(priority, [])
        for page in pages:
            category = page.get("category", "other")
            if category not in pages_by_category:
                pages_by_category[category] = []
            pages_by_category[category].append(page)

    return {
        "base_url": filtered.get("base_url", "https://www.upheal.io"),
        "pages_by_category": pages_by_category,
        "filter_stats": filtered.get("filter_stats", {})
    }


def get_representative_urls(sitemap: Dict, category: str, limit: int = 3) -> List[str]:
    """
    Get representative URLs for a category.
    Returns first URL for schema generation and additional URLs for validation.
    Prioritizes public pages (upheal.io) over app pages (app.upheal.io).
    """
    pages = sitemap.get("pages_by_category", {}).get(category, [])

    # Separate public and app pages
    public_pages = [
        p["url"] for p in pages
        if "app.upheal.io" not in p["url"]
    ]

    app_pages = [
        p["url"] for p in pages
        if "app.upheal.io" in p["url"]
    ]

    # Prioritize public pages, then add app pages if needed
    result = public_pages[:limit]
    if len(result) < limit:
        result.extend(app_pages[:limit - len(result)])

    return result[:limit]


async def generate_schema_for_category(
    url: str,
    category: str,
    instruction: str
) -> Optional[Dict]:
    """
    Generate CSS extraction schema for a category using LLM analysis.

    Args:
        url: Representative page URL
        category: Category name (features, notes, etc.)
        instruction: LLM instruction for what to extract

    Returns:
        Generated schema dict or None on failure
    """
    print(f"\n{'='*60}")
    print(f"Generating schema for: {category}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )

    # Use LLM to analyze page structure and generate CSS selectors
    extraction_strategy = LLMExtractionStrategy(
        provider="openai/gpt-4o-mini",
        instruction=f"""
        {instruction}

        Return a JSON schema with CSS selectors that can extract the required data.
        The schema MUST follow this exact format:
        {{
            "name": "{category}_items",
            "baseSelector": "CSS selector for the repeating container element",
            "fields": [
                {{"name": "title", "selector": "CSS selector for title within container", "type": "text"}},
                {{"name": "description", "selector": "CSS selector for description", "type": "text"}},
                {{"name": "image_url", "selector": "CSS selector for image", "type": "attribute", "attribute": "src"}},
                ... more fields as needed
            ]
        }}

        Field types:
        - "text": Extract text content
        - "attribute": Extract HTML attribute (specify "attribute" name)
        - "html": Extract inner HTML

        Make selectors specific to avoid false matches. Use:
        - Class selectors (.class-name)
        - Attribute selectors ([data-*], [class*="keyword"])
        - Descendant selectors (parent > child)
        - Multiple selectors if needed (selector1, selector2)

        IMPORTANT: Return ONLY valid JSON, no markdown formatting or explanation.
        """
    )

    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for="css:body",
        page_timeout=60000,
        remove_overlay_elements=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawler_config)

        if result.success and result.extracted_content:
            try:
                # Try to parse the extracted content as JSON
                content = result.extracted_content.strip()

                # Handle case where LLM returns markdown-wrapped JSON
                if content.startswith("```"):
                    # Remove markdown code blocks
                    lines = content.split("\n")
                    content = "\n".join(
                        line for line in lines
                        if not line.startswith("```")
                    )

                schema = json.loads(content)

                # Validate schema structure
                if "fields" not in schema:
                    print(f"Warning: Generated schema missing 'fields', using fallback")
                    schema = create_fallback_schema(category)

                # Ensure required fields exist
                if "name" not in schema:
                    schema["name"] = f"{category}_items"
                if "baseSelector" not in schema and "selector" in schema:
                    schema["baseSelector"] = schema.pop("selector")

                print(f"Successfully generated schema with {len(schema.get('fields', []))} fields")
                return schema

            except json.JSONDecodeError as e:
                print(f"Error: Failed to parse LLM response as JSON: {e}")
                print(f"Raw output (first 500 chars): {result.extracted_content[:500]}")
                return create_fallback_schema(category)
        else:
            error_msg = result.error_message if hasattr(result, 'error_message') else "Unknown error"
            print(f"Error: Failed to fetch/analyze page: {error_msg}")
            return None


def create_fallback_schema(category: str) -> Dict:
    """Create a fallback schema when LLM generation fails."""

    fallback_schemas = {
        "features": {
            "name": "features_items",
            "baseSelector": "section, .feature-card, .feature-section, [class*='feature'], article",
            "fields": [
                {"name": "title", "selector": "h1, h2, h3, .title, [class*='heading']", "type": "text"},
                {"name": "description", "selector": "p, .description, [class*='desc'], .content", "type": "text"},
                {"name": "image_url", "selector": "img", "type": "attribute", "attribute": "src"},
                {"name": "benefits", "selector": "li, .benefit, [class*='benefit']", "type": "text"}
            ]
        },
        "notes": {
            "name": "notes_items",
            "baseSelector": "section, .note-type, .card, [class*='note'], article",
            "fields": [
                {"name": "title", "selector": "h1, h2, h3, .title", "type": "text"},
                {"name": "description", "selector": "p, .description", "type": "text"},
                {"name": "fields", "selector": "li, .field", "type": "text"},
                {"name": "template_example", "selector": "pre, code, .example", "type": "text"}
            ]
        },
        "sessions": {
            "name": "sessions_items",
            "baseSelector": "section, .session-feature, [class*='session'], article",
            "fields": [
                {"name": "title", "selector": "h1, h2, h3, .title", "type": "text"},
                {"name": "description", "selector": "p, .description", "type": "text"},
                {"name": "capabilities", "selector": "li, .capability", "type": "text"}
            ]
        },
        "analytics": {
            "name": "analytics_items",
            "baseSelector": "section, .analytics-feature, [class*='analytic'], article",
            "fields": [
                {"name": "title", "selector": "h1, h2, h3, .title", "type": "text"},
                {"name": "description", "selector": "p, .description", "type": "text"},
                {"name": "metrics", "selector": "li, .metric", "type": "text"}
            ]
        },
        "compliance": {
            "name": "compliance_items",
            "baseSelector": "section, .compliance-item, [class*='security'], [class*='hipaa'], article",
            "fields": [
                {"name": "title", "selector": "h1, h2, h3, .title", "type": "text"},
                {"name": "description", "selector": "p, .description", "type": "text"},
                {"name": "certification", "selector": ".certification, .badge, [class*='cert']", "type": "text"},
                {"name": "details", "selector": "li, .detail", "type": "text"}
            ]
        },
        "patients": {
            "name": "patients_items",
            "baseSelector": "section, .patient-feature, [class*='client'], [class*='patient'], article",
            "fields": [
                {"name": "title", "selector": "h1, h2, h3, .title", "type": "text"},
                {"name": "description", "selector": "p, .description", "type": "text"},
                {"name": "features", "selector": "li, .feature", "type": "text"}
            ]
        }
    }

    return fallback_schemas.get(category, fallback_schemas["features"])


async def validate_schema(
    schema: Dict,
    urls: List[str],
    category: str
) -> Dict[str, Any]:
    """
    Validate a generated schema by testing it on multiple pages.

    Returns:
        Validation results with success rate and extracted counts
    """
    print(f"\nValidating schema on {len(urls)} pages...")

    validation_results = {
        "pages_tested": 0,
        "pages_successful": 0,
        "items_extracted_per_page": [],
        "errors": []
    }

    extraction_strategy = JsonCssExtractionStrategy(
        schema=schema,
        verbose=False
    )

    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for="css:body",
        page_timeout=30000
    )

    async with AsyncWebCrawler() as crawler:
        for url in urls:
            try:
                result = await crawler.arun(url=url, config=crawler_config)
                validation_results["pages_tested"] += 1

                if result.success and result.extracted_content:
                    data = json.loads(result.extracted_content)

                    # Handle both list and dict formats
                    if isinstance(data, list):
                        items = data
                    else:
                        items = data.get(schema.get("name", f"{category}_items"), [])

                    item_count = len(items) if isinstance(items, list) else 1
                    validation_results["items_extracted_per_page"].append({
                        "url": url,
                        "count": item_count
                    })

                    if item_count > 0:
                        validation_results["pages_successful"] += 1
                        print(f"  {url}: {item_count} items extracted")
                    else:
                        print(f"  {url}: No items extracted")
                else:
                    validation_results["errors"].append({
                        "url": url,
                        "error": "Extraction failed"
                    })
                    print(f"  {url}: Extraction failed")

            except Exception as e:
                validation_results["errors"].append({
                    "url": url,
                    "error": str(e)
                })
                print(f"  {url}: Error - {e}")

    return validation_results


def save_schema(schema: Dict, category: str, validation_results: Optional[Dict] = None) -> Path:
    """Save schema to JSON file with metadata."""

    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "schema": schema,
        "metadata": {
            "category": category,
            "generated_at": datetime.utcnow().isoformat(),
            "generator": "upheal_schema_generator.py",
            "version": "1.0"
        }
    }

    if validation_results:
        output["validation"] = validation_results

    output_path = SCHEMAS_DIR / f"{category}_schema.json"

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved schema to: {output_path}")
    return output_path


async def generate_all_schemas(categories: Optional[List[str]] = None, use_fallback: bool = False):
    """Generate schemas for all high-priority categories.

    Args:
        categories: List of categories to generate (None = all high-priority)
        use_fallback: If True, use fallback schemas without LLM (no API cost)
    """

    sitemap = load_sitemap()
    if not sitemap:
        return

    categories = categories or HIGH_PRIORITY_CATEGORIES

    results_summary = {
        "generated": [],
        "failed": [],
        "total_cost_estimate": 0.0,
        "mode": "fallback" if use_fallback else "llm"
    }

    # Check if OpenAI API key is available
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_key or openai_key.startswith("sk-your"):
        if not use_fallback:
            print("\nWARNING: No valid OPENAI_API_KEY found.")
            print("Using fallback schemas (no LLM cost, but less accurate).")
            print("Set OPENAI_API_KEY environment variable for LLM-generated schemas.\n")
        use_fallback = True

    for category in categories:
        if category not in CATEGORY_INSTRUCTIONS:
            print(f"Skipping {category}: No extraction instruction defined")
            continue

        # Get representative URLs
        urls = get_representative_urls(sitemap, category)

        if not urls:
            print(f"Skipping {category}: No URLs found in sitemap")
            results_summary["failed"].append({
                "category": category,
                "reason": "No URLs in sitemap"
            })
            continue

        print(f"\n{'='*60}")
        print(f"Processing category: {category}")
        print(f"URLs available: {len(urls)}")
        print(f"{'='*60}")

        if use_fallback:
            # Use fallback schema without LLM
            schema = create_fallback_schema(category)
            print(f"Using fallback schema with {len(schema.get('fields', []))} fields")
        else:
            # Generate schema using LLM
            schema = await generate_schema_for_category(
                url=urls[0],
                category=category,
                instruction=CATEGORY_INSTRUCTIONS[category]
            )
            # Estimate cost: ~$0.003 per schema generation with gpt-4o-mini
            results_summary["total_cost_estimate"] += 0.003

        if schema:
            # Validate on available URLs (skip for app.upheal.io pages that need auth)
            validation_results = None
            public_urls = [u for u in urls if "app.upheal.io" not in u]

            if public_urls:
                validation_results = await validate_schema(schema, public_urls[:3], category)

            # Save schema
            output_path = save_schema(schema, category, validation_results)

            results_summary["generated"].append({
                "category": category,
                "path": str(output_path),
                "fields_count": len(schema.get("fields", [])),
                "validation": validation_results,
                "urls_available": len(urls),
                "public_urls": len(public_urls)
            })
        else:
            results_summary["failed"].append({
                "category": category,
                "reason": "Schema generation failed"
            })

        # Small delay between categories
        await asyncio.sleep(0.5)

    # Print summary
    print("\n" + "="*60)
    print("SCHEMA GENERATION SUMMARY")
    print("="*60)
    print(f"\nSchemas generated: {len(results_summary['generated'])}")
    print(f"Failed: {len(results_summary['failed'])}")
    print(f"Estimated total LLM cost: ${results_summary['total_cost_estimate']:.4f}")

    if results_summary["generated"]:
        print("\nGenerated schemas:")
        for item in results_summary["generated"]:
            print(f"  - {item['category']}: {item['fields_count']} fields")
            if item.get('validation'):
                v = item['validation']
                print(f"    Validated on {v['pages_tested']} pages, {v['pages_successful']} successful")

    if results_summary["failed"]:
        print("\nFailed categories:")
        for item in results_summary["failed"]:
            print(f"  - {item['category']}: {item['reason']}")

    # Speedup estimate
    print("\n" + "-"*60)
    print("SPEEDUP ESTIMATE")
    print("-"*60)
    print("After schema generation (one-time LLM cost):")
    print("  - LLM extraction: ~2-3 seconds per page, ~$0.01-0.05 per page")
    print("  - CSS extraction:  ~0.1-0.3 seconds per page, $0.00 per page")
    print("  - Estimated speedup: 10-100x faster, 100% cost reduction")

    return results_summary


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate CSS extraction schemas for Upheal")
    parser.add_argument(
        "--category", "-c",
        help="Generate schema for specific category only"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate existing schemas"
    )
    parser.add_argument(
        "--list-categories", "-l",
        action="store_true",
        help="List available categories from sitemap"
    )
    parser.add_argument(
        "--fallback", "-f",
        action="store_true",
        help="Use fallback schemas without LLM (no API cost)"
    )

    args = parser.parse_args()

    if args.list_categories:
        sitemap = load_sitemap()
        if sitemap:
            print("Available categories:")
            for cat, pages in sitemap.get("pages_by_category", {}).items():
                public_count = len([p for p in pages if "app.upheal.io" not in p.get("url", "")])
                app_count = len(pages) - public_count
                print(f"  - {cat}: {len(pages)} pages ({public_count} public, {app_count} app)")
        return

    if args.validate:
        print("Validating existing schemas...")
        for schema_file in SCHEMAS_DIR.glob("*_schema.json"):
            with open(schema_file) as f:
                data = json.load(f)
            category = data.get("metadata", {}).get("category", schema_file.stem.replace("_schema", ""))
            schema = data.get("schema", {})

            sitemap = load_sitemap()
            if sitemap:
                urls = get_representative_urls(sitemap, category)
                # Only validate on public URLs
                public_urls = [u for u in urls if "app.upheal.io" not in u]
                if public_urls:
                    results = await validate_schema(schema, public_urls[:3], category)
                    print(f"\n{category}: {results['pages_successful']}/{results['pages_tested']} pages successful")
                else:
                    print(f"\n{category}: No public URLs available for validation")
        return

    # Generate schemas
    categories = [args.category] if args.category else None
    await generate_all_schemas(categories, use_fallback=args.fallback)


if __name__ == "__main__":
    asyncio.run(main())
