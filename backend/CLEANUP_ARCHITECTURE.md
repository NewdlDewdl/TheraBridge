# Cleanup Service Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      TherapyBridge Backend                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────┐      ┌──────────────────┐              │
│  │   API Endpoints   │      │   Scheduled Job  │              │
│  │  (cleanup.py)     │      │   (cron/cloud)   │              │
│  └─────────┬─────────┘      └────────┬─────────┘              │
│            │                         │                         │
│            └─────────┬───────────────┘                         │
│                      │                                         │
│            ┌─────────▼─────────┐                               │
│            │  Cleanup Service  │                               │
│            │   (cleanup.py)    │                               │
│            └─────────┬─────────┘                               │
│                      │                                         │
│         ┌────────────┼────────────┐                            │
│         │            │            │                            │
│    ┌────▼─────┐ ┌───▼────┐ ┌────▼─────┐                      │
│    │ Orphaned │ │ Failed │ │ Combined │                      │
│    │  Files   │ │Session │ │  Cleanup │                      │
│    │ Cleanup  │ │Cleanup │ │          │                      │
│    └────┬─────┘ └───┬────┘ └────┬─────┘                      │
│         │           │           │                             │
│         └───────────┼───────────┘                             │
│                     │                                         │
│         ┌───────────▼───────────┐                             │
│         │   Storage Operations  │                             │
│         │  - Scan directory     │                             │
│         │  - Query database     │                             │
│         │  - Delete files       │                             │
│         │  - Log operations     │                             │
│         └───────────┬───────────┘                             │
│                     │                                         │
│         ┌───────────▼───────────┐                             │
│         │   External Resources  │                             │
│         │  - PostgreSQL DB      │                             │
│         │  - File system        │                             │
│         │  - Application logs   │                             │
│         └───────────────────────┘                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Component Interactions

### 1. API Endpoints → Cleanup Service

```
User Request
     │
     ├──[Authentication]──▶ JWT Validation
     │                      ↓
     ├──[Authorization]───▶ Role Check (therapist/admin)
     │                      ↓
     └──[Cleanup Request]─▶ AudioCleanupService
                            ↓
                      [Execute Cleanup]
                            ↓
                      [Return Results]
```

### 2. Orphaned File Cleanup Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Scan Upload Directory                                    │
│    ├─ List all files in uploads/audio/                      │
│    └─ Exclude .gitkeep                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. Query Database for Referenced Files                      │
│    ├─ SELECT audio_filename FROM sessions                   │
│    │   WHERE audio_filename IS NOT NULL                     │
│    └─ Include processed file variants                       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 3. Identify Orphaned Files                                  │
│    ├─ files_in_directory - files_in_database                │
│    └─ Filter by retention period (24h default)              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. Delete Files (if not dry_run)                            │
│    ├─ Check file age vs retention period                    │
│    ├─ Delete file from filesystem                           │
│    ├─ Track space freed                                     │
│    └─ Log operation                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 5. Return Results                                           │
│    ├─ Files deleted (list)                                  │
│    ├─ Space freed (MB)                                      │
│    └─ Errors (if any)                                       │
└─────────────────────────────────────────────────────────────┘
```

### 3. Failed Session Cleanup Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Query Failed Sessions                                    │
│    ├─ SELECT * FROM sessions                                │
│    │   WHERE status = 'failed'                              │
│    │   AND created_at < NOW() - retention_period            │
│    │   AND audio_filename IS NOT NULL                       │
│    └─ Default retention: 7 days                             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. Process Each Failed Session                              │
│    ├─ Check for original file (e.g., abc123.m4a)            │
│    └─ Check for processed file (e.g., abc123_processed.mp3) │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 3. Delete Associated Files (if not dry_run)                 │
│    ├─ Verify file exists                                    │
│    ├─ Get file size                                         │
│    ├─ Delete file from filesystem                           │
│    ├─ Track space freed                                     │
│    └─ Log operation                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. Return Results                                           │
│    ├─ Sessions cleaned (list of UUIDs)                      │
│    ├─ Space freed (MB)                                      │
│    └─ Errors (if any)                                       │
└─────────────────────────────────────────────────────────────┘

Note: Session records are PRESERVED for audit trail
```

## Data Flow

### Input Sources

```
┌─────────────────────┐
│  Configuration      │
│  (.env)             │
│  ├─ Retention days  │
│  ├─ Retention hours │
│  └─ Auto cleanup    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  API Request        │
│  ├─ Endpoint        │
│  ├─ Auth token      │
│  └─ dry_run param   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Database State     │
│  ├─ Sessions        │
│  └─ audio_filename  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  File System        │
│  └─ uploads/audio/  │
└─────────────────────┘
```

### Output Results

```
┌─────────────────────┐
│  API Response       │
│  (JSON)             │
│  ├─ Success flag    │
│  ├─ Files deleted   │
│  ├─ Space freed     │
│  └─ Errors          │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Application Logs   │
│  ├─ Operations      │
│  ├─ Timestamps      │
│  └─ File details    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  File System        │
│  (Files deleted)    │
│  └─ uploads/audio/  │
└─────────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────┐
│ Layer 1: Network Security                       │
│  ├─ HTTPS/TLS encryption                        │
│  └─ CORS policies                               │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│ Layer 2: Authentication                         │
│  ├─ JWT token validation                        │
│  └─ Token expiration check                      │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│ Layer 3: Authorization                          │
│  ├─ Role-based access control                   │
│  └─ Only therapists/admins allowed              │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│ Layer 4: Input Validation                       │
│  ├─ Query parameter validation                  │
│  └─ Path traversal prevention                   │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│ Layer 5: Operation Safety                       │
│  ├─ Dry-run mode                                │
│  ├─ Retention period checks                     │
│  └─ Audit logging                               │
└─────────────────────────────────────────────────┘
```

## Deployment Scenarios

### Scenario 1: Manual Cleanup (Ad-hoc)

```
Admin/Therapist ─┐
                 │
          [Login]
                 │
         ┌───────▼────────┐
         │  GET /status   │  ◀─── Check what will be cleaned
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │ POST /all?     │  ◀─── Test with dry_run=true
         │  dry_run=true  │
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │  POST /all     │  ◀─── Actual cleanup
         └───────┬────────┘
                 │
         [View Results]
```

### Scenario 2: Scheduled Cleanup (Automated)

```
Cron Job / Cloud Scheduler
         │
         ├─── 3:00 AM Daily
         │
    ┌────▼─────────────┐
    │ run_scheduled_   │
    │   cleanup()      │
    └────┬─────────────┘
         │
    ┌────▼─────────────┐
    │ AudioCleanup     │
    │   Service        │
    └────┬─────────────┘
         │
    [Execute Cleanup]
         │
    [Log Results]
```

### Scenario 3: Startup Cleanup (Automatic)

```
Server Start (uvicorn)
         │
    ┌────▼─────────────┐
    │ lifespan()       │
    │  startup         │
    └────┬─────────────┘
         │
    [init_db()]
         │
    ┌────▼─────────────┐
    │ run_startup_     │
    │   cleanup()      │  ◀─── If AUTO_CLEANUP_ON_STARTUP=true
    └────┬─────────────┘
         │
    [Server Ready]
```

## Error Handling

```
┌─────────────────────────────────────┐
│  Cleanup Operation Attempted        │
└────────────────┬────────────────────┘
                 │
         ┌───────▼────────┐
         │  Try Delete    │
         │     File       │
         └───┬────────┬───┘
             │        │
        [Success] [Failure]
             │        │
             │   ┌────▼────────┐
             │   │ Log Error   │
             │   │ Continue    │
             │   └────┬────────┘
             │        │
         ┌───▼────────▼───┐
         │  Track Result  │
         │  ├─ Deleted    │
         │  └─ Errors     │
         └────────────────┘
```

**Error Philosophy:**
- Individual file errors don't stop cleanup
- All errors are logged and reported
- Cleanup continues processing remaining files
- Results include both successes and failures

## Performance Optimization

### Database Queries

```sql
-- Optimized query for referenced files
SELECT audio_filename
FROM sessions
WHERE audio_filename IS NOT NULL;

-- Optimized query for failed sessions
SELECT id, audio_filename, created_at
FROM sessions
WHERE status = 'failed'
  AND created_at < NOW() - INTERVAL '7 days'
  AND audio_filename IS NOT NULL;
```

**Optimization techniques:**
- Index on `audio_filename` column
- Index on `status` column
- Composite index on `(status, created_at)`
- Single query to fetch all data needed

### File Operations

```
Sequential Processing (Current)
├─ Read directory: O(n)
├─ Query database: O(1) indexed
├─ Set difference: O(n)
└─ Delete files: O(n) sequential

Future Optimization (Phase 2)
└─ Parallel deletion: O(n/workers)
```

## Monitoring & Observability

### Metrics to Track

```
┌─────────────────────────────────┐
│  Cleanup Metrics                │
├─────────────────────────────────┤
│  • Files deleted per run        │
│  • Space freed per run          │
│  • Cleanup duration             │
│  • Error rate                   │
│  • Orphaned file count          │
│  • Failed session count         │
└─────────────────────────────────┘
```

### Log Structure

```json
{
  "timestamp": "2025-12-17T11:59:00Z",
  "level": "INFO",
  "component": "cleanup_service",
  "operation": "orphaned_file_cleanup",
  "result": {
    "files_deleted": 15,
    "space_freed_mb": 234.5,
    "errors": 0,
    "duration_ms": 1234
  }
}
```

## Integration Points

### With Existing Systems

```
┌─────────────────────────────────────────┐
│  Session Upload Pipeline                │
│  ├─ Upload → Transcribe → Extract       │
│  └─ If fails → status='failed'          │
└────────────────┬────────────────────────┘
                 │
                 │ (7 days later)
                 │
┌────────────────▼────────────────────────┐
│  Cleanup Service                        │
│  └─ Detects failed session              │
│     └─ Deletes audio files              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Authentication System                  │
│  └─ Role-based access control           │
└────────────────┬────────────────────────┘
                 │
                 │ (checks role)
                 │
┌────────────────▼────────────────────────┐
│  Cleanup Endpoints                      │
│  └─ Requires therapist/admin role       │
└─────────────────────────────────────────┘
```

## Conclusion

The cleanup service is designed with:
- **Modularity** - Independent service that integrates cleanly
- **Safety** - Multiple layers of protection against data loss
- **Flexibility** - Configurable for different environments
- **Observability** - Comprehensive logging and reporting
- **Scalability** - Efficient algorithms and optimized queries
- **Security** - Role-based access and authentication required
