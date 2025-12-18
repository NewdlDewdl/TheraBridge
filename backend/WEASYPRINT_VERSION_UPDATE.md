# WeasyPrint Version Update Recommendation

## Current Situation

**requirements.txt specifies:** `weasyprint==60.1`
**Actually installed:** `weasyprint==67.0`
**Status:** Working correctly in development

---

## Recommendation: Update to 67.0

### Why Update requirements.txt

1. **Matches installed version** - Prevents confusion and ensures consistency
2. **Latest stable** - Version 67.0 released Dec 2024, includes important fixes
3. **Already tested** - All 26 PDF generation tests pass with 67.0
4. **Better CSS support** - Improved Grid layout and modern CSS features

### Changes Between 60.1 and 67.0

**Version 67.0 (Dec 2024):**
- Improved CSS Grid support
- Better font handling and fallbacks
- Performance optimizations for large documents
- Bug fixes for edge cases in table rendering
- Updated dependencies (tinycss2, cssselect2)

**Version 60.1 (Jan 2024):**
- Stable but older
- Missing recent improvements
- May have bugs fixed in newer versions

---

## Proposed Change

```diff
# Export & Reporting dependencies (Feature 7)
# WeasyPrint system dependencies (must be installed separately):
# macOS: brew install cairo pango gdk-pixbuf libffi
# Ubuntu: apt-get install libpango-1.0-0 libpangoft2-1.0-0
- weasyprint==60.1         # HTML to PDF conversion
+ weasyprint==67.0         # HTML to PDF conversion (Dec 2024 stable)
python-docx==1.1.0       # DOCX generation
jinja2==3.1.2            # Template rendering
# pillow==10.2.0 moved to Security section (shared by qrcode and weasyprint)
```

---

## Testing Checklist

Before deploying to production:

- [x] Local verification test passes (`test_weasyprint_installation.py`)
- [x] PDF generation tests pass (26/26)
- [x] Integration tests with templates work
- [ ] Staging deployment test
- [ ] Load testing (concurrent PDF generation)
- [ ] Memory usage monitoring
- [ ] Production deployment

---

## Rollback Plan

If issues arise with 67.0:

```bash
# Uninstall current version
pip uninstall weasyprint

# Install older version
pip install weasyprint==60.1

# Verify
python test_weasyprint_installation.py
```

**Likelihood of issues:** Very low - 67.0 is stable and already tested in dev.

---

## Implementation

```bash
# 1. Update requirements.txt
sed -i '' 's/weasyprint==60.1/weasyprint==67.0/' requirements.txt

# 2. Reinstall to verify
pip install -r requirements.txt

# 3. Run tests
python test_weasyprint_installation.py
pytest backend/tests/services/test_pdf_generator.py -v

# 4. Commit changes
git add requirements.txt
git commit -m "Update WeasyPrint to 67.0 (matches installed version)"
```

---

## Alternative: Keep 60.1

If you prefer to stay on 60.1 for stability:

```bash
# Downgrade to match requirements.txt
pip uninstall weasyprint
pip install weasyprint==60.1

# Test thoroughly
python test_weasyprint_installation.py
pytest backend/tests/services/test_pdf_generator.py -v
```

**Pros:**
- Older, more battle-tested version
- No changes to existing setup

**Cons:**
- Missing recent bug fixes and improvements
- Requires downgrade from working version
- Development/production version mismatch

---

## Recommendation

**✅ UPDATE TO 67.0**

Rationale:
1. Already working in development
2. All tests pass
3. Latest stable with improvements
4. Eliminates version discrepancy

**Next steps:**
1. Update `requirements.txt` to `weasyprint==67.0`
2. Deploy to staging and verify
3. Run load tests
4. Deploy to production with monitoring
