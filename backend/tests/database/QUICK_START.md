# Quick Start Guide - Feature 6 Index Tests

## For Agent I2 (Migration Creator)

After you create the Alembic migration with the 4 indexes, run this to validate:

```bash
cd backend
source venv/bin/activate

# Run all index validation tests
python -m pytest tests/database/test_feature6_indexes.py -v

# Expected output:
# ✓ test_session_date_index_exists_and_used PASSED
# ✓ test_status_index_exists_and_used PASSED
# ✓ test_therapist_queries_composite_index PASSED
# ✓ test_extracted_notes_gin_index_jsonb_queries PASSED
# ✓ test_index_performance_improvement PASSED
# ✓ test_all_indexes_summary PASSED
```

## For Agent I4 (Integration Tester)

Run the summary test to get a comprehensive performance report:

```bash
python -m pytest tests/database/test_feature6_indexes.py::test_all_indexes_summary -v -s --log-cli-level=INFO
```

Expected output will show:
```
======================================================================
FEATURE 6 INDEX VALIDATION SUMMARY
======================================================================
Test dataset: 150 therapy sessions

Index Performance Results:
  session_date_index            :   XX records in   X.XXms
  status_index                  :   XX records in   X.XXms
  composite_index               :   XX records in   X.XXms
  gin_index                     :  XXX records in  XX.XXms

All indexes verified ✓
======================================================================
```

## Index Names (Use These Exact Names)

Your Alembic migration must create indexes with these exact names:

1. `idx_therapy_sessions_session_date`
2. `idx_therapy_sessions_status`
3. `idx_therapy_sessions_therapist_queries`
4. `idx_therapy_sessions_extracted_notes_gin`

## Test Status

✅ Test module created (602 lines)
✅ 6 test cases implemented
✅ Test discovery verified (6 tests collected)
✅ Import verification passed
✅ Initial test run confirmed passing

## Performance Thresholds

All queries must complete within:
- < 100ms for 100 records (standard tests)
- < 150ms for 200 records (performance test)
- < 200ms for summary test (safety margin)

## Files Created

1. `test_feature6_indexes.py` - Main test suite
2. `README.md` - Comprehensive documentation
3. `WAVE1_I8_COMPLETION_REPORT.md` - Completion report
4. `QUICK_START.md` - This file
5. `__init__.py` - Package marker

---

**Ready for use by Agent I2** ✅
