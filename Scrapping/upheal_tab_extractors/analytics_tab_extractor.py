#!/usr/bin/env python3
"""
Upheal Analytics Tab Extractor (Wave 2.3 - Instance I4)

Extracts analytics/insights tab content from Upheal session detail pages.
Focuses on:
- Chart types (line, bar, pie, word cloud, etc.)
- Visualization library detection (Recharts, Chart.js, D3, etc.)
- Metrics displayed (mood scores, topics, risks, progress)
- Layout patterns (grid, card-based, dashboard-style)

Session URL format: https://app.upheal.io/detail/{client_id}/{session_id}
"""

import asyncio
import json
import os
import base64
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

# Try to load dotenv for credentials
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


# Default session detail URL (from Wave 1 discovery)
DEFAULT_SESSION_URL = "https://app.upheal.io/detail/b83dc32e-58c9-4c43-ad16-338a5f331c95/5b4aa0cb-9f10-405a-b7ff-e34ea54e5071"

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "tabs"


@dataclass
class ChartInfo:
    """Information about a detected chart."""
    chart_type: str  # line, bar, pie, donut, word_cloud, heatmap, etc.
    element_type: str  # canvas, svg, div
    css_classes: List[str]
    container_id: Optional[str]
    dimensions: Dict[str, int]  # width, height
    data_attributes: Dict[str, str]


@dataclass
class MetricInfo:
    """Information about a displayed metric."""
    name: str
    value: Optional[str]
    unit: Optional[str]
    time_range: Optional[str]  # single session, 30 days, all-time
    category: str  # mood, topic, risk, progress, engagement


@dataclass
class AnalyticsTabResult:
    """Complete extraction result for the Analytics tab."""
    tab_name: str = "analytics"
    extraction_timestamp: str = ""
    session_url: str = ""

    # Tab navigation
    tab_found: bool = False
    tab_selector_used: str = ""
    tab_click_successful: bool = False

    # Chart analysis
    chart_types_found: List[str] = None
    chart_library: str = "unknown"
    chart_library_evidence: List[str] = None
    charts_detailed: List[Dict] = None

    # Metrics analysis
    metrics_found: List[Dict] = None
    time_ranges_available: List[str] = None
    comparative_metrics: bool = False

    # Layout analysis
    layout_pattern: str = ""
    grid_columns: int = 0
    card_based: bool = False
    has_filters: bool = False
    has_date_picker: bool = False
    has_export: bool = False

    # Content
    raw_html_snippet: str = ""
    markdown_content: str = ""

    # Screenshot
    screenshot_path: str = ""

    # UI patterns for TherapyBridge
    ui_patterns: Dict[str, Any] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.chart_types_found is None:
            self.chart_types_found = []
        if self.chart_library_evidence is None:
            self.chart_library_evidence = []
        if self.charts_detailed is None:
            self.charts_detailed = []
        if self.metrics_found is None:
            self.metrics_found = []
        if self.time_ranges_available is None:
            self.time_ranges_available = []
        if self.ui_patterns is None:
            self.ui_patterns = {}
        if self.recommendations is None:
            self.recommendations = []


# JavaScript for clicking on Analytics/Insights tab
JS_CLICK_ANALYTICS_TAB = """
(async () => {
    const result = {
        tabFound: false,
        tabText: '',
        tabSelector: '',
        clicked: false,
        error: null,
        allTabs: []
    };

    try {
        // Collect all potential tab elements
        const tabSelectors = [
            '[role="tab"]',
            '[role="tablist"] > *',
            '.tab-button',
            '.tab',
            '.tabs-menu > div',
            '.tabs-menu > button',
            'button[class*="tab"]',
            'div[class*="tab"]',
            '[data-tab]',
            '.nav-tab',
            '.tab-item',
            '[class*="TabList"] > *',
            '[class*="tablist"] > *'
        ];

        let allTabElements = [];
        for (const selector of tabSelectors) {
            const elements = document.querySelectorAll(selector);
            allTabElements = allTabElements.concat(Array.from(elements));
        }

        // Deduplicate
        allTabElements = [...new Set(allTabElements)];

        // Log all tabs found
        result.allTabs = allTabElements.map(t => ({
            text: t.textContent.trim().substring(0, 50),
            tagName: t.tagName,
            classes: t.className
        }));

        // Look for Analytics/Insights tab (various naming conventions)
        const analyticsKeywords = [
            'analytic', 'insight', 'chart', 'graph', 'stat',
            'metric', 'progress', 'trend', 'overview', 'summary'
        ];

        for (const tab of allTabElements) {
            const text = tab.textContent.toLowerCase();
            const matchedKeyword = analyticsKeywords.find(kw => text.includes(kw));

            if (matchedKeyword) {
                result.tabFound = true;
                result.tabText = tab.textContent.trim();
                result.tabSelector = tab.tagName + (tab.className ? '.' + tab.className.split(' ')[0] : '');

                // Scroll into view and click
                tab.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await new Promise(r => setTimeout(r, 300));

                tab.click();
                result.clicked = true;

                // Wait for charts to potentially render
                await new Promise(r => setTimeout(r, 2500));
                break;
            }
        }

        if (!result.tabFound) {
            // Try clicking on tabs in sequence to find charts
            for (let i = 0; i < Math.min(allTabElements.length, 6); i++) {
                const tab = allTabElements[i];
                tab.click();
                await new Promise(r => setTimeout(r, 1000));

                // Check if charts appeared
                const hasCharts = document.querySelectorAll('canvas, svg[class*="chart"], svg[class*="graph"], [class*="recharts"]').length > 0;
                if (hasCharts) {
                    result.tabFound = true;
                    result.tabText = tab.textContent.trim() + ' (found via chart detection)';
                    result.clicked = true;
                    await new Promise(r => setTimeout(r, 1500));
                    break;
                }
            }
        }

    } catch (e) {
        result.error = e.message;
    }

    // Return result via console for extraction
    console.log('ANALYTICS_TAB_RESULT:' + JSON.stringify(result));
    return result;
})();
"""


# JavaScript for detecting chart library and extracting chart information
JS_DETECT_CHARTS = """
(async () => {
    const result = {
        chartLibrary: 'unknown',
        libraryEvidence: [],
        charts: [],
        metrics: [],
        layout: {},
        hasFilters: false,
        hasDatePicker: false,
        hasExport: false
    };

    try {
        // 1. Detect chart library
        if (window.Chart) {
            result.chartLibrary = 'chart.js';
            result.libraryEvidence.push('window.Chart global detected');
        }
        if (window.Recharts) {
            result.chartLibrary = 'recharts';
            result.libraryEvidence.push('window.Recharts global detected');
        }
        if (window.d3) {
            result.chartLibrary = 'd3';
            result.libraryEvidence.push('window.d3 global detected');
        }
        if (window.Plotly) {
            result.chartLibrary = 'plotly';
            result.libraryEvidence.push('window.Plotly global detected');
        }
        if (window.ApexCharts) {
            result.chartLibrary = 'apexcharts';
            result.libraryEvidence.push('window.ApexCharts global detected');
        }

        // Check DOM for library signatures
        if (document.querySelector('[class*="recharts"]')) {
            result.chartLibrary = 'recharts';
            result.libraryEvidence.push('recharts CSS class found');
        }
        if (document.querySelector('[class*="victory"]')) {
            result.chartLibrary = 'victory';
            result.libraryEvidence.push('victory CSS class found');
        }
        if (document.querySelector('[class*="apexcharts"]')) {
            result.chartLibrary = 'apexcharts';
            result.libraryEvidence.push('apexcharts CSS class found');
        }
        if (document.querySelector('.chartjs-render-monitor, canvas[class*="chart"]')) {
            result.chartLibrary = 'chart.js';
            result.libraryEvidence.push('Chart.js canvas element found');
        }
        if (document.querySelector('[class*="plotly"]')) {
            result.chartLibrary = 'plotly';
            result.libraryEvidence.push('plotly CSS class found');
        }
        if (document.querySelector('[class*="nivo"]')) {
            result.chartLibrary = 'nivo';
            result.libraryEvidence.push('nivo CSS class found');
        }
        if (document.querySelector('[class*="highcharts"]')) {
            result.chartLibrary = 'highcharts';
            result.libraryEvidence.push('highcharts CSS class found');
        }

        // 2. Find all chart elements
        const chartElements = [
            ...document.querySelectorAll('canvas'),
            ...document.querySelectorAll('svg[class*="chart"]'),
            ...document.querySelectorAll('svg[class*="graph"]'),
            ...document.querySelectorAll('[class*="recharts"]'),
            ...document.querySelectorAll('[class*="chart-container"]'),
            ...document.querySelectorAll('[class*="visualization"]'),
            ...document.querySelectorAll('[class*="word-cloud"]'),
            ...document.querySelectorAll('[class*="wordcloud"]'),
            ...document.querySelectorAll('[class*="heatmap"]')
        ];

        for (const el of chartElements) {
            const chartInfo = {
                tagName: el.tagName,
                className: el.className,
                id: el.id,
                width: el.clientWidth || el.getAttribute('width'),
                height: el.clientHeight || el.getAttribute('height'),
                chartType: 'unknown'
            };

            // Infer chart type from classes or structure
            const classes = (el.className || '').toLowerCase();
            if (classes.includes('line')) chartInfo.chartType = 'line';
            else if (classes.includes('bar')) chartInfo.chartType = 'bar';
            else if (classes.includes('pie') || classes.includes('donut')) chartInfo.chartType = 'pie';
            else if (classes.includes('area')) chartInfo.chartType = 'area';
            else if (classes.includes('scatter')) chartInfo.chartType = 'scatter';
            else if (classes.includes('radar')) chartInfo.chartType = 'radar';
            else if (classes.includes('word') || classes.includes('cloud')) chartInfo.chartType = 'word_cloud';
            else if (classes.includes('heatmap')) chartInfo.chartType = 'heatmap';
            else if (el.tagName === 'CANVAS') chartInfo.chartType = 'canvas_chart';
            else if (el.tagName === 'SVG') chartInfo.chartType = 'svg_chart';

            result.charts.push(chartInfo);
        }

        // 3. Extract metrics from the page
        const metricSelectors = [
            '[class*="metric"]',
            '[class*="stat"]',
            '[class*="score"]',
            '[class*="value"]',
            '[class*="kpi"]',
            '[class*="indicator"]',
            '.card h3 + *',  // Card pattern
            '[class*="summary"] *'
        ];

        for (const selector of metricSelectors) {
            const elements = document.querySelectorAll(selector);
            for (const el of elements) {
                const text = el.textContent.trim();
                if (text && text.length < 100) {
                    result.metrics.push({
                        selector: selector,
                        text: text,
                        tag: el.tagName
                    });
                }
            }
        }

        // 4. Analyze layout
        const mainContent = document.querySelector('main, [class*="content"], [class*="detail"]');
        if (mainContent) {
            const computedStyle = window.getComputedStyle(mainContent);
            result.layout = {
                display: computedStyle.display,
                gridTemplateColumns: computedStyle.gridTemplateColumns,
                flexDirection: computedStyle.flexDirection,
                gap: computedStyle.gap
            };
        }

        // Check for grid layouts
        const gridContainers = document.querySelectorAll('[class*="grid"]');
        if (gridContainers.length > 0) {
            result.layout.hasGrid = true;
            result.layout.gridCount = gridContainers.length;
        }

        // Check for cards
        const cards = document.querySelectorAll('[class*="card"]');
        result.layout.cardCount = cards.length;

        // 5. Check for interactive elements
        result.hasFilters = document.querySelectorAll('[class*="filter"], select, [class*="dropdown"]').length > 0;
        result.hasDatePicker = document.querySelectorAll('[class*="date-picker"], [type="date"], [class*="calendar-input"]').length > 0;
        result.hasExport = document.querySelectorAll('[class*="export"], [class*="download"], button[title*="export"]').length > 0;

    } catch (e) {
        result.error = e.message;
    }

    console.log('CHART_DETECTION_RESULT:' + JSON.stringify(result));
    return result;
})();
"""


# JavaScript for extracting more detailed metric information
JS_EXTRACT_METRICS_DETAILED = """
(async () => {
    const result = {
        moodMetrics: [],
        topicMetrics: [],
        riskMetrics: [],
        progressMetrics: [],
        engagementMetrics: [],
        timeRanges: [],
        comparisons: []
    };

    try {
        // Look for mood-related content
        const moodKeywords = ['mood', 'emotion', 'feeling', 'affect', 'sentiment'];
        const topicKeywords = ['topic', 'theme', 'subject', 'concern', 'issue'];
        const riskKeywords = ['risk', 'safety', 'suicide', 'harm', 'crisis', 'alert'];
        const progressKeywords = ['progress', 'goal', 'treatment', 'improvement', 'change'];
        const engagementKeywords = ['engagement', 'attendance', 'participation', 'session', 'duration'];

        function extractMetrics(keywords, category) {
            const found = [];
            const allText = document.body.innerText.toLowerCase();

            for (const kw of keywords) {
                if (allText.includes(kw)) {
                    // Find elements containing this keyword
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.children.length === 0 && el.textContent.toLowerCase().includes(kw)) {
                            found.push({
                                category: category,
                                keyword: kw,
                                text: el.textContent.trim().substring(0, 200),
                                tag: el.tagName,
                                classes: el.className
                            });
                        }
                    }
                }
            }
            return found;
        }

        result.moodMetrics = extractMetrics(moodKeywords, 'mood');
        result.topicMetrics = extractMetrics(topicKeywords, 'topic');
        result.riskMetrics = extractMetrics(riskKeywords, 'risk');
        result.progressMetrics = extractMetrics(progressKeywords, 'progress');
        result.engagementMetrics = extractMetrics(engagementKeywords, 'engagement');

        // Look for time range selectors
        const timeKeywords = ['today', 'week', 'month', '30 days', '90 days', 'all time', 'session', 'year'];
        for (const kw of timeKeywords) {
            if (document.body.innerText.toLowerCase().includes(kw)) {
                result.timeRanges.push(kw);
            }
        }

        // Look for comparison indicators
        const comparisonKeywords = ['vs', 'compared', 'previous', 'last', 'change', 'delta', '%'];
        for (const kw of comparisonKeywords) {
            if (document.body.innerText.toLowerCase().includes(kw)) {
                result.comparisons.push(kw);
            }
        }

    } catch (e) {
        result.error = e.message;
    }

    console.log('METRICS_DETAIL_RESULT:' + JSON.stringify(result));
    return result;
})();
"""


def save_screenshot(screenshot_data: str, filename: str) -> str:
    """Save base64 screenshot to file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename

    if screenshot_data:
        if isinstance(screenshot_data, str):
            screenshot_data = base64.b64decode(screenshot_data)
        with open(filepath, "wb") as f:
            f.write(screenshot_data)
        return str(filepath)
    return ""


def save_json(data: dict, filename: str) -> str:
    """Save dict as JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return str(filepath)


def parse_js_console_output(html: str, marker: str) -> Optional[dict]:
    """Extract JSON data from console log markers in page content."""
    # This is a heuristic - in practice we'd need to capture console output
    # For now, we'll extract from any embedded script results
    pattern = f'{marker}:(.*?)(?:$|\n)'
    match = re.search(pattern, html)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def generate_recommendations(result: AnalyticsTabResult) -> List[str]:
    """Generate recommendations for TherapyBridge based on findings."""
    recommendations = []

    # Chart library recommendation
    if result.chart_library == "recharts":
        recommendations.append("Use Recharts for React-based charting - compatible with Upheal's approach")
    elif result.chart_library == "chart.js":
        recommendations.append("Consider Chart.js for canvas-based charts - matches Upheal's implementation")
    elif result.chart_library == "d3":
        recommendations.append("D3.js detected - consider simpler alternatives unless custom visualizations needed")
    else:
        recommendations.append("Recommend Recharts or Chart.js for consistent charting in React")

    # Chart types
    if "line" in result.chart_types_found:
        recommendations.append("Implement line charts for mood/progress tracking over time")
    if "bar" in result.chart_types_found:
        recommendations.append("Use bar charts for session frequency and duration metrics")
    if "word_cloud" in result.chart_types_found:
        recommendations.append("Consider word cloud for topic/theme visualization")
    if "pie" in result.chart_types_found:
        recommendations.append("Pie/donut charts useful for topic distribution")

    # Layout
    if result.card_based:
        recommendations.append("Use card-based layout for metric grouping (matches Upheal pattern)")
    if result.grid_columns >= 2:
        recommendations.append(f"Implement {result.grid_columns}-column grid for dashboard layout")

    # Features
    if result.has_date_picker:
        recommendations.append("Include date range picker for historical analysis")
    if result.has_filters:
        recommendations.append("Add filtering capabilities for metrics")
    if result.has_export:
        recommendations.append("Implement export functionality for reports")

    return recommendations


async def extract_analytics_tab(
    session_url: str = DEFAULT_SESSION_URL,
    headless: bool = False,
    manual_login_wait: int = 60
) -> AnalyticsTabResult:
    """
    Extract analytics tab content from an Upheal session detail page.

    Args:
        session_url: Full URL to session detail page
        headless: Run browser in headless mode (False for manual login)
        manual_login_wait: Seconds to wait for manual login

    Returns:
        AnalyticsTabResult with extracted data
    """
    result = AnalyticsTabResult(
        extraction_timestamp=datetime.now().isoformat(),
        session_url=session_url
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 70)
    print("Upheal Analytics Tab Extractor (Wave 2.3 - Instance I4)")
    print("=" * 70)
    print(f"Target URL: {session_url}")
    print(f"Timestamp: {timestamp}")
    print("=" * 70)

    # Browser config
    browser_config = BrowserConfig(
        headless=headless,
        viewport_width=1920,
        viewport_height=1080,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:

        # Step 1: Login flow
        print("\n[1/5] Opening login page for authentication...")

        login_config = CrawlerRunConfig(
            session_id="upheal_analytics_session",
            page_timeout=120000,
            screenshot=True,
        )

        login_result = await crawler.arun(
            url="https://app.upheal.io/login",
            config=login_config
        )

        if not login_result.success:
            print(f"ERROR: Failed to open login page: {login_result.error_message}")
            return result

        print(f"Login page loaded: {login_result.url}")

        if not headless:
            print(f"\nManual login required - you have {manual_login_wait} seconds...")
            print("Please log in to Upheal in the browser window.")

            for i in range(manual_login_wait, 0, -10):
                print(f"  {i} seconds remaining...")
                await asyncio.sleep(10)

            print("Continuing with extraction...")

        # Step 2: Navigate to session detail page
        print(f"\n[2/5] Navigating to session detail page...")

        session_config = CrawlerRunConfig(
            session_id="upheal_analytics_session",
            page_timeout=30000,
            screenshot=True,
            js_code="""
            // Wait for page to fully load
            await new Promise(r => setTimeout(r, 2000));
            // Scroll to trigger lazy loading
            window.scrollTo(0, document.body.scrollHeight / 2);
            await new Promise(r => setTimeout(r, 1000));
            window.scrollTo(0, 0);
            """
        )

        session_result = await crawler.arun(
            url=session_url,
            config=session_config
        )

        if not session_result.success:
            print(f"ERROR: Failed to load session page: {session_result.error_message}")
            return result

        if "login" in session_result.url.lower():
            print("WARNING: Redirected to login - authentication may have failed")
            return result

        print(f"Session page loaded: {session_result.url}")
        save_screenshot(session_result.screenshot, f"analytics_01_session_page_{timestamp}.png")

        # Step 3: Click on Analytics/Insights tab
        print("\n[3/5] Searching for and clicking Analytics tab...")

        analytics_tab_config = CrawlerRunConfig(
            session_id="upheal_analytics_session",
            page_timeout=30000,
            screenshot=True,
            js_code=JS_CLICK_ANALYTICS_TAB,
            screenshot_wait_for=3.0  # Wait for charts to render
        )

        tab_result = await crawler.arun(
            url=session_result.url,  # Stay on same page
            config=analytics_tab_config
        )

        if tab_result.success:
            screenshot_path = save_screenshot(
                tab_result.screenshot,
                f"analytics_02_tab_clicked_{timestamp}.png"
            )
            result.screenshot_path = screenshot_path

            # Check console output for tab click result
            # (In practice, we'd need a more robust way to get JS execution results)
            if "analytic" in tab_result.markdown.lower() or "insight" in tab_result.markdown.lower():
                result.tab_found = True
                result.tab_click_successful = True
                print("Analytics tab found and clicked!")
            else:
                print("Tab navigation attempted - checking for chart content...")

        # Step 4: Detect charts and extract chart information
        print("\n[4/5] Detecting charts and visualization library...")

        chart_detect_config = CrawlerRunConfig(
            session_id="upheal_analytics_session",
            page_timeout=30000,
            screenshot=True,
            js_code=JS_DETECT_CHARTS + "\n" + JS_EXTRACT_METRICS_DETAILED,
            screenshot_wait_for=2.0
        )

        chart_result = await crawler.arun(
            url=tab_result.url if tab_result.success else session_url,
            config=chart_detect_config
        )

        if chart_result.success:
            result.markdown_content = chart_result.markdown
            result.raw_html_snippet = chart_result.html[:5000] if chart_result.html else ""

            # Save final screenshot
            final_screenshot_path = save_screenshot(
                chart_result.screenshot,
                f"analytics_03_final_{timestamp}.png"
            )
            if final_screenshot_path:
                result.screenshot_path = final_screenshot_path

            # Analyze the HTML for chart patterns
            html_lower = (chart_result.html or "").lower()
            markdown_lower = result.markdown_content.lower()

            # Detect chart library from HTML
            library_checks = [
                ("recharts", ["recharts", "responsivecontainer", "xaxis", "yaxis"]),
                ("chart.js", ["chartjs", "chart.js", "ctx.bindbindbindbindbindbindbindbindbindbindbindcbindbindbindbindbindbindbindcbindbindbindbindbindbindcbindbindbindcbindcbindbindbindcbindcbindcbindbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbindcbind"]),
                ("d3", ["d3.js", "d3js", "d3.select"]),
                ("plotly", ["plotly", "plotlyjs"]),
                ("apexcharts", ["apexcharts"]),
                ("victory", ["victoryline", "victorychart", "victorybar"]),
                ("nivo", ["@nivo", "nivobar", "nivoline"]),
                ("highcharts", ["highcharts"])
            ]

            for lib_name, patterns in library_checks:
                for pattern in patterns:
                    if pattern in html_lower:
                        result.chart_library = lib_name
                        result.chart_library_evidence.append(f"Pattern '{pattern}' found in HTML")
                        break
                if result.chart_library != "unknown":
                    break

            # Detect chart types
            chart_type_patterns = [
                ("line", ["linechart", "line-chart", "lineplot", "line_chart", "linegraph"]),
                ("bar", ["barchart", "bar-chart", "barplot", "bar_chart", "bargraph"]),
                ("pie", ["piechart", "pie-chart", "pieplot", "pie_chart"]),
                ("donut", ["donutchart", "donut-chart", "donut_chart"]),
                ("area", ["areachart", "area-chart", "areaplot", "area_chart"]),
                ("scatter", ["scatterchart", "scatter-chart", "scatterplot"]),
                ("word_cloud", ["wordcloud", "word-cloud", "word_cloud", "tagcloud"]),
                ("heatmap", ["heatmap", "heat-map", "heat_map"]),
                ("radar", ["radarchart", "radar-chart", "radar_chart"]),
            ]

            for chart_type, patterns in chart_type_patterns:
                for pattern in patterns:
                    if pattern in html_lower:
                        if chart_type not in result.chart_types_found:
                            result.chart_types_found.append(chart_type)
                        break

            # Check for canvas and SVG elements
            if "<canvas" in html_lower:
                if "canvas_chart" not in result.chart_types_found:
                    result.chart_types_found.append("canvas_chart")

            if "<svg" in html_lower:
                if "svg_chart" not in result.chart_types_found:
                    result.chart_types_found.append("svg_chart")

            # Analyze metrics from markdown content
            metric_keywords = {
                "mood": ["mood", "emotion", "feeling", "sentiment", "affect"],
                "topic": ["topic", "theme", "subject", "concern", "issue", "keyword"],
                "risk": ["risk", "safety", "suicide", "harm", "crisis", "alert"],
                "progress": ["progress", "goal", "treatment", "improvement", "outcome"],
                "engagement": ["session", "duration", "attendance", "frequency"]
            }

            for category, keywords in metric_keywords.items():
                for keyword in keywords:
                    if keyword in markdown_lower:
                        result.metrics_found.append({
                            "category": category,
                            "keyword": keyword,
                            "found": True
                        })

            # Check for time ranges
            time_patterns = [
                "today", "this week", "this month", "30 days", "90 days",
                "last session", "all time", "year", "custom"
            ]
            for pattern in time_patterns:
                if pattern in markdown_lower:
                    result.time_ranges_available.append(pattern)

            # Check for comparative metrics
            comparison_patterns = ["vs", "compared", "previous", "change", "delta", "%"]
            result.comparative_metrics = any(p in markdown_lower for p in comparison_patterns)

            # Analyze layout
            if "grid" in html_lower:
                result.layout_pattern = "grid"
            elif "flex" in html_lower:
                result.layout_pattern = "flexbox"
            else:
                result.layout_pattern = "standard"

            # Count grid columns (heuristic)
            grid_col_match = re.search(r'grid-template-columns[:\s]+([^;]+)', html_lower)
            if grid_col_match:
                cols = grid_col_match.group(1).count('fr') + grid_col_match.group(1).count('px') + grid_col_match.group(1).count('%')
                result.grid_columns = max(cols, 1)

            # Check for card-based layout
            result.card_based = "card" in html_lower

            # Check for interactive features
            result.has_filters = any(p in html_lower for p in ["filter", "dropdown", "select"])
            result.has_date_picker = any(p in html_lower for p in ["datepicker", "date-picker", "calendar"])
            result.has_export = any(p in html_lower for p in ["export", "download", "pdf", "csv"])

            print(f"Chart library detected: {result.chart_library}")
            print(f"Chart types found: {result.chart_types_found}")
            print(f"Metrics categories: {[m['category'] for m in result.metrics_found[:5]]}")

        # Step 5: Generate UI patterns and recommendations
        print("\n[5/5] Generating recommendations for TherapyBridge...")

        result.ui_patterns = {
            "chart_library": result.chart_library,
            "visualization_types": result.chart_types_found,
            "layout": {
                "pattern": result.layout_pattern,
                "columns": result.grid_columns,
                "card_based": result.card_based
            },
            "interactivity": {
                "filters": result.has_filters,
                "date_picker": result.has_date_picker,
                "export": result.has_export
            },
            "metrics": {
                "categories": list(set(m['category'] for m in result.metrics_found)),
                "time_ranges": result.time_ranges_available,
                "comparisons": result.comparative_metrics
            }
        }

        result.recommendations = generate_recommendations(result)

    return result


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract Upheal Analytics Tab content")
    parser.add_argument(
        "--url",
        default=DEFAULT_SESSION_URL,
        help="Session detail URL to extract from"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (requires pre-authenticated session)"
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=60,
        help="Seconds to wait for manual login (default: 60)"
    )

    args = parser.parse_args()

    # Run extraction
    result = await extract_analytics_tab(
        session_url=args.url,
        headless=args.headless,
        manual_login_wait=args.wait
    )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = save_json(asdict(result), f"analytics_tab_{timestamp}.json")

    # Also save to standard location
    standard_output = save_json(asdict(result), "analytics_tab.json")

    # Print summary
    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Tab found: {result.tab_found}")
    print(f"Chart library: {result.chart_library}")
    print(f"Chart types: {result.chart_types_found}")
    print(f"Metrics found: {len(result.metrics_found)}")
    print(f"Time ranges: {result.time_ranges_available}")
    print(f"Layout pattern: {result.layout_pattern}")
    print(f"Screenshot: {result.screenshot_path}")
    print(f"Output saved: {output_file}")
    print(f"Standard output: {standard_output}")
    print("\n--- RECOMMENDATIONS FOR THERAPYBRIDGE ---")
    for rec in result.recommendations:
        print(f"  - {rec}")
    print("=" * 70)

    return result


if __name__ == "__main__":
    asyncio.run(main())
