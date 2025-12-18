# Database Performance Tests

## Feature 6 Index Validation Suite

This directory contains comprehensive database performance tests for validating the Feature 6 database indexes created to optimize query performance in the TherapyBridge backend.

### Test File

**`test_feature6_indexes.py`** (602 lines)
- Comprehensive test suite for validating 4 database indexes on the `therapy_sessions` table
- Tests both index usage (via EXPLAIN plans) and query performance
- Compatible with both SQLite (test environment) and PostgreSQL (production)

### Indexes Being Tested

1. **`idx_therapy_sessions_session_date`**
   - Single-column index on `session_date`
   - Optimizes date range queries (e.g., "show sessions from last 6 months")
   - Expected performance: < 100ms for 100 records

2. **`idx_therapy_sessions_status`**
   - Single-column index on `status`
   - Optimizes status filtering (e.g., "show all completed sessions")
   - Expected performance: < 100ms for 100 records

3. **`idx_therapy_sessions_therapist_queries`**
   - **Composite index** on `(therapist_id, session_date, status)`
   - Most important index for therapist dashboard queries
   - Optimizes multi-column filters (therapist + date + status)
   - Expected performance: < 100ms for complex queries

4. **`idx_therapy_sessions_extracted_notes_gin`**
   - **GIN index** on JSONB column `extracted_notes`
   - Enables fast JSONB queries using `?` (key existence) and `@>` (containment) operators
   - Optimizes queries like "find sessions with risk_level" or "find anxious mood sessions"
   - Expected performance: < 100ms for JSONB operations

### Test Cases

#### 1. `test_session_date_index_exists_and_used`
- Creates 100 therapy sessions spread over 1 year
- Queries sessions after a target date (6 months ago)
- Verifies: Results found, query time < 100ms
- PostgreSQL: Checks EXPLAIN plan for index usage

#### 2. `test_status_index_exists_and_used`
- Creates 100 sessions with varied status distribution
- Filters by status ("completed")
- Verifies: Correct filtering, query time < 100ms
- PostgreSQL: Checks EXPLAIN plan for status index

#### 3. `test_therapist_queries_composite_index`
- Creates sessions for 2 different therapists (100 total)
- Queries with therapist_id + date range + status
- **Tests the most critical composite index**
- Verifies: Correct therapist filtering, query time < 100ms
- PostgreSQL: Checks EXPLAIN plan for composite index usage

#### 4. `test_extracted_notes_gin_index_jsonb_queries`
- Creates 100 sessions with rich JSONB content
- Tests JSONB queries:
  - `?` operator (key existence): "WHERE extracted_notes ? 'risk_level'"
  - `@>` operator (containment): "WHERE extracted_notes @> '{"mood": "anxious"}'"
- Verifies: JSONB queries work correctly, performance < 100-200ms
- PostgreSQL: Checks EXPLAIN plan for GIN index usage
- SQLite: Falls back to Python-side filtering (compatible testing)

#### 5. `test_index_performance_improvement`
- Creates 200 sessions for performance benchmarking
- Runs same query 5 times and averages execution time
- Logs: min, max, average query times
- Verifies: Average query time < 150ms for 200 records

#### 6. `test_all_indexes_summary`
- **Comprehensive summary test**
- Creates 150 realistic test sessions
- Tests all 4 indexes in sequence
- Logs detailed performance report showing:
  - Records returned by each index query
  - Execution time for each query
  - Overall validation status
- Verifies: All queries successful, all under 200ms

### Test Data Generation

The test suite includes sophisticated bulk data generators:

- **`create_test_therapist()`**: Creates authenticated therapist users
- **`create_test_patient()`**: Creates patient records
- **`create_bulk_therapy_sessions()`**: Creates realistic therapy sessions with:
  - Configurable count (50-200 sessions typical)
  - Realistic status distribution (60% completed, 20% processing, etc.)
  - Sessions spaced over 1 year (every 3 days)
  - Rich JSONB content including:
    - Mood tracking (neutral, positive, anxious)
    - Topics (anxiety, depression, relationships, work_stress)
    - Risk levels (low, medium)
    - Interventions (CBT, DBT, mindfulness)
    - Progress notes
    - Session metadata

### Running the Tests

```bash
# Run all Feature 6 index tests
cd backend
source venv/bin/activate
python -m pytest tests/database/test_feature6_indexes.py -v

# Run individual test
python -m pytest tests/database/test_feature6_indexes.py::test_session_date_index_exists_and_used -v

# Run with detailed logging
python -m pytest tests/database/test_feature6_indexes.py -v -s --log-cli-level=INFO

# Run summary test only
python -m pytest tests/database/test_feature6_indexes.py::test_all_indexes_summary -v
```

### Expected Output

Successful test runs should show:

```
✓ session_date index test: 38 sessions found in 4.82ms
✓ status index test: 60 completed sessions found in 3.15ms
✓ therapist composite index test: 25 sessions found in 5.43ms
✓ JSONB ? operator test: 100 sessions in 12.34ms
✓ JSONB @> operator test: 33 anxious sessions in 8.76ms
✓ Performance test (200 sessions, 5 runs):
  - Average query time: 6.23ms
  - Min: 5.12ms, Max: 8.45ms

======================================================================
FEATURE 6 INDEX VALIDATION SUMMARY
======================================================================
Test dataset: 150 therapy sessions

Index Performance Results:
  session_date_index            :   55 records in   4.12ms
  status_index                  :   90 records in   3.89ms
  composite_index               :   30 records in   5.67ms
  gin_index                     :  150 records in  14.23ms

All indexes verified ✓
======================================================================
```

### Performance Benchmarks

| Index Type | Query Type | Expected Time | Records |
|------------|-----------|---------------|---------|
| session_date | Date range | < 100ms | 100 |
| status | Status filter | < 100ms | 100 |
| Composite | Multi-column | < 100ms | 100 |
| GIN (JSONB) | Key existence | < 100ms | 100 |
| GIN (JSONB) | Containment | < 100ms | 100 |
| Performance | Averaged (5x) | < 150ms | 200 |
| Summary | All 4 indexes | < 200ms each | 150 |

### SQLite vs PostgreSQL

The tests are designed to work in both environments:

- **SQLite (Test Environment)**:
  - Indexes are created and used, but EXPLAIN output differs
  - JSONB queries use Python-side filtering for `?` and `@>` operators
  - Performance thresholds slightly relaxed (< 200ms vs < 100ms)

- **PostgreSQL (Production)**:
  - Full EXPLAIN ANALYZE validation
  - Native JSONB operator support (`?`, `@>`)
  - Stricter performance expectations
  - Index Scan verification in query plans

### Integration with CI/CD

These tests should be run:

1. **Before** deploying any database migrations
2. **After** creating or modifying indexes
3. **During** performance regression testing
4. **In** staging environments before production deployment

### Notes for Agent I2 (Migration Creator)

The test suite assumes the following migration structure:

```python
# Migration: Create 4 indexes on therapy_sessions table

def upgrade():
    # 1. Session date index (B-tree)
    op.create_index(
        'idx_therapy_sessions_session_date',
        'therapy_sessions',
        ['session_date'],
        unique=False
    )

    # 2. Status index (B-tree)
    op.create_index(
        'idx_therapy_sessions_status',
        'therapy_sessions',
        ['status'],
        unique=False
    )

    # 3. Composite index for therapist queries (B-tree)
    op.create_index(
        'idx_therapy_sessions_therapist_queries',
        'therapy_sessions',
        ['therapist_id', 'session_date', 'status'],
        unique=False
    )

    # 4. GIN index for JSONB queries (PostgreSQL only)
    op.execute(
        "CREATE INDEX idx_therapy_sessions_extracted_notes_gin "
        "ON therapy_sessions USING GIN (extracted_notes)"
    )

def downgrade():
    op.drop_index('idx_therapy_sessions_extracted_notes_gin')
    op.drop_index('idx_therapy_sessions_therapist_queries')
    op.drop_index('idx_therapy_sessions_status')
    op.drop_index('idx_therapy_sessions_session_date')
```

### Success Criteria

All tests must pass with:
- ✅ 4/4 indexes verified as being used by query planner (PostgreSQL)
- ✅ All query performance within thresholds
- ✅ Correct query results (filtering working properly)
- ✅ No test failures or errors
- ✅ Summary report showing all indexes operational

### Test Maintenance

When modifying these tests:
- Maintain database-agnostic code (SQLite + PostgreSQL)
- Keep performance thresholds realistic
- Update EXPLAIN plan checks when index names change
- Add new test cases for new indexes
- Document expected performance changes

---

**Created by**: Test Engineer #2 (Agent I8)
**Date**: 2025-12-18
**Wave**: Wave 1 (Database Performance Testing)
**Purpose**: Validate Feature 6 database index performance and usage
