# Upheal.io Authenticated Crawl Results

**Crawl Date:** December 18, 2025, 18:35 UTC
**Email:** rohinagrawal@gmail.com
**Tool:** Crawl4AI v0.7.8
**Method:** Interactive authenticated scraping (60-second manual login window)

---

## 📊 Summary Statistics

- **Total Pages Crawled:** 12
- **Total Content:** 18,545 characters
- **Average Page Length:** 1,545 characters
- **Screenshots Captured:** 12 PNG files
- **Total Data Size:** ~2 MB

---

## 📁 Files Structure

### Summary & Reports
- `00_SUMMARY_20251218_183523.md` - Human-readable summary report
- `00_SUMMARY_20251218_183523.json` - Machine-readable data
- `03_discovered_links_20251218_183523.json` - All discovered internal links

### Initial Crawl
- `01_login_page_20251218_183523.png` - Login page screenshot
- `02_home_20251218_183523.md` - Home page content
- `02_home_20251218_183523.png` - Home page screenshot

### Main Application Pages

#### Dashboard
- `page_dashboard_20251218_183523.md` (2,923 chars)
- `page_dashboard_20251218_183523.png` (247 KB)
- **Key Features Discovered:**
  - Navigation menu (Home, Calendar, Sessions, Clients, Payments)
  - Templates & forms section
  - Tools (Telehealth, Session capture, Compliance Checker)
  - Recent sessions with demo clients
  - Free trial status (30 days left)
  - UphealOS announcement

#### Sessions
- `page_sessions_20251218_183523.md` (1,511 chars)
- `page_sessions_20251218_183523.png` (100 KB)

#### Clients/Patients
- `page_patients_clients_20251218_183523.md` (2,923 chars)
- `page_patients_clients_20251218_183523.png` (247 KB)

#### Calendar
- `page_calendar_20251218_183523.md` (1,572 chars)
- `page_calendar_20251218_183523.png` (133 KB)

#### Notes
- `page_notes_20251218_183523.md` (2,923 chars)
- `page_notes_20251218_183523.png` (247 KB)

#### Settings
- `page_settings_20251218_183523.md` (843 chars)
- `page_settings_20251218_183523.png` (104 KB)

#### Profile
- `page_profile_20251218_183523.md` (2,923 chars)
- `page_profile_20251218_183523.png` (247 KB)

#### Templates
- `page_templates_20251218_183523.md` (2,923 chars)
- `page_templates_20251218_183523.png` (247 KB)

### Additional Discovered Pages

#### Session Details
- `discovered_detail_b83dc32e-58c9-4c43-ad16-338a5f331c95_5b4aa0_20251218_183523.md`
- `discovered_detail_b83dc32e-58c9-4c43-ad16-338a5f331c95_5b4aa0_20251218_183523.png`
- Session: "Surgeon's perfectionism trauma - progress note demo"
- Client: Tony Pasano (demo)
- Date: Jul 29, 2022

#### Session Details 2
- `discovered_detail_c9289f16-7f34-4d07-9497-96243334f68f_b88886_20251218_183523.md`
- `discovered_detail_c9289f16-7f34-4d07-9497-96243334f68f_b88886_20251218_183523.png`
- Session: "History of violence - intake note demo"
- Client: Rhonda García Sánchez (demo)
- Date: Apr 29, 2023

#### Referral Program
- `discovered_settings_referral-program_20251218_183523.md`
- `discovered_settings_referral-program_20251218_183523.png`

---

## 🔍 Key Insights from Crawled Data

### Application Structure
**Primary Navigation:**
- Home / Dashboard
- Calendar
- Sessions
- Clients
- Payments

**Templates & Forms:**
- Note templates
- Forms

**Tools:**
- Telehealth
- Session capture
- Compliance Checker

**Settings:**
- Practice settings
- Referral program

### Account Information
- **Practice Name:** Carl Jung's Practice
- **User:** Carl Jung (demo account)
- **Trial Status:** 30 days left in free trial
- **Referral Offer:** Give 50% off, get $300

### Features Identified

1. **AI Client Testing**
   - Demo client "Alex" for testing AI notes
   - Voice interaction capability

2. **EHR Migration**
   - SimplePractice integration available
   - Early access program for data migration

3. **Apps & Platforms**
   - Desktop apps (Mac)
   - Mobile apps (iPhone, iPad)
   - Web application

4. **Session Management**
   - Session recording
   - Transcript generation
   - AI-powered note generation
   - Session reassignment
   - Delete recording/transcript/session options

5. **Demo Sessions Available**
   - 2 demo sessions visible
   - Various therapy scenarios (trauma, behavioral issues)
   - Shows note templates and structure

6. **Resources**
   - Free webinars
   - Uphealer Community (Facebook group)
   - Support Center

### UphealOS Features
- Announced as new platform expansion
- "Save time on more than notes"
- Indicates broader practice management functionality

---

## 🛠 Technical Details

### Crawling Configuration
- **Browser:** Chromium (Playwright/Patchright)
- **Headless Mode:** False (visible browser for manual login)
- **Viewport:** 1920x1080
- **Session Management:** Persistent session across all page crawls
- **Scroll Behavior:** Automated scrolling to load dynamic content
- **Rate Limiting:** 2-second delay between requests

### Authentication Method
1. Browser opened to login page
2. 60-second manual login window
3. Session cookies preserved across all subsequent requests
4. All crawled pages used authenticated session

---

## 📋 Competitive Analysis Notes

### Strengths Observed
- Clean, modern UI
- Comprehensive therapy workflow coverage
- AI-powered automation (notes, transcripts)
- Multi-platform support
- Demo/testing capabilities built-in
- Active community and support resources

### Feature Set
- **Clinical Documentation:** AI-generated progress notes, templates
- **Scheduling:** Calendar integration
- **Client Management:** Patient/client profiles
- **Compliance:** Compliance checker tool, consent management
- **Telehealth:** Built-in video capabilities
- **Recording:** Session capture and transcription
- **Payments:** Payment processing integration
- **Forms:** Customizable clinical forms

### Business Model Indicators
- Free trial (30 days)
- Referral program ($300 incentive)
- Premium features (UphealOS)
- SimplePractice migration targeting

---

## 📄 Next Steps for Analysis

1. **Content Analysis:** Parse markdown files for feature details
2. **Screenshot Review:** Examine UI/UX patterns and design
3. **Feature Comparison:** Compare with TherapyBridge feature set
4. **Pricing Research:** Investigate subscription tiers
5. **API Investigation:** Check for public API documentation
6. **Integration Points:** Identify EHR integration capabilities

---

## 🔒 Security & Privacy Notes

- **Credentials stored in:** `.claude/skills/crawl4ai/.env` (gitignored)
- **Data sensitivity:** Contains demo/test session data
- **Account type:** Trial/demo account
- **No PHI:** Demo clients only, no real patient data

---

## 📞 Support & Resources

- **Upheal Support:** https://support.upheal.io
- **Community:** https://www.facebook.com/groups/upheal
- **Webinars:** https://www.upheal.io/webinars

---

**Generated by:** Crawl4AI authenticated scraper
**Script:** `.claude/skills/crawl4ai/scripts/upheal_authenticated_scraper.py`
**Log:** `.claude/skills/crawl4ai/scripts/upheal_crawl.log`
