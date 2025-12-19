# Manual Scraping Instructions

Since you're already logged into Upheal, here's the fastest way to get the competitive analysis data:

## What We Need

We want to analyze how Upheal implements session detail pages (to learn UI patterns for TherapyBridge).

## Pages to Scrape

###  1. Session Detail Page - Example Session

**URL:** Click on any session from https://app.upheal.io/sessions

**What to capture:**
- Full page content (all tabs visible)
- Screenshots of each tab if they exist

**Tabs to look for:**
- Overview/Summary tab
- Transcript tab  
- Analytics tab
- Session Map/Timeline tab
- Notes tab

## How to Capture

For each tab:

### Method 1: Browser Save (Easiest)
1. Click on the tab
2. Right-click → "Save Page As" → Save as "Complete Webpage"
3. Save to: `Scrapping/data/manual_scrape/`
4. Name it: `tab_overview.html`, `tab_transcript.html`, etc.

### Method 2: Copy Content (Faster)
1. Click on the tab
2. Press Cmd+A (select all)
3. Press Cmd+C (copy)
4. Create a text file and paste
5. Save to: `Scrapping/data/manual_scrape/tab_NAME.txt`

### Method 3: Screenshots Only
1. Click on each tab
2. Take screenshot (Cmd+Shift+4)
3. Save to: `Scrapping/data/manual_scrape/screenshots/`

## What I'll Do With This Data

Once you provide the files, I'll:
1. Parse the HTML/text to understand UI structure
2. Identify:
   - Note template field structure (SOAP/DAP formats)
   - Transcript display patterns (speaker labels, timestamps)
   - Analytics chart types and metrics
   - Timeline visualization approach
3. Generate competitive analysis report comparing to TherapyBridge
4. Provide specific UI recommendations

## Quick Start

Just save 1-2 session detail pages (all tabs) and I can start the analysis!
