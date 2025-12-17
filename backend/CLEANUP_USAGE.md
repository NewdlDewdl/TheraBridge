# Audio File Cleanup Service - Usage Guide

## Overview

The cleanup service manages orphaned audio files and prevents storage bloat by automatically cleaning up:
1. **Orphaned files** - Audio files not referenced in the database
2. **Failed sessions** - Audio files from sessions that failed processing

## Quick Start

### 1. Check Current Status (No Deletion)

See what files would be cleaned up without actually deleting:

```bash
curl "http://localhost:8000/api/admin/cleanup/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq
```

**Response Example:**
```json
{
  "success": true,
  "message": "Cleanup status retrieved",
  "potential_cleanup": {
    "orphaned_files_deleted": ["abc123.mp3", "xyz789_processed.mp3"],
    "orphaned_files_count": 2,
    "failed_sessions_cleaned": ["550e8400-e29b-41d4-a716-446655440000"],
    "failed_sessions_count": 1,
    "total_space_freed_mb": 25.4,
    "errors": [],
    "error_count": 0,
    "dry_run": true
  }
}
```

### 2. Test with Dry-Run

Run cleanup in dry-run mode to see logs without deletion:

```bash
curl -X POST "http://localhost:8000/api/admin/cleanup/all?dry_run=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq
```

### 3. Run Actual Cleanup

When satisfied with dry-run results, run actual cleanup:

```bash
curl -X POST "http://localhost:8000/api/admin/cleanup/all" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq
```

## Endpoint Reference

### GET /api/admin/cleanup/config

Get current cleanup configuration.

**Authentication:** Required (therapist or admin role)

**Response:**
```json
{
  "failed_session_retention_days": 7,
  "orphaned_file_retention_hours": 24,
  "upload_dir": "uploads/audio",
  "auto_cleanup_on_startup": false,
  "cleanup_schedule_hour": 3
}
```

### GET /api/admin/cleanup/status

Get cleanup statistics without performing deletions.

**Authentication:** Required (therapist or admin role)

**Response:** Same as dry-run cleanup result

### POST /api/admin/cleanup/orphaned-files

Clean up orphaned audio files only.

**Authentication:** Required (therapist or admin role)

**Query Parameters:**
- `dry_run` (boolean, default: false) - If true, report without deleting

**Response:**
```json
{
  "success": true,
  "message": "Orphaned file cleanup completed",
  "result": {
    "orphaned_files_deleted": ["file1.mp3", "file2_processed.mp3"],
    "orphaned_files_count": 2,
    "failed_sessions_cleaned": [],
    "failed_sessions_count": 0,
    "total_space_freed_mb": 15.2,
    "errors": [],
    "error_count": 0,
    "dry_run": false
  }
}
```

### POST /api/admin/cleanup/failed-sessions

Clean up audio files from old failed sessions.

**Authentication:** Required (therapist or admin role)

**Query Parameters:**
- `dry_run` (boolean, default: false) - If true, report without deleting

**Response:** Similar to orphaned-files endpoint

### POST /api/admin/cleanup/all

Run both orphaned file and failed session cleanup.

**Authentication:** Required (therapist or admin role)

**Query Parameters:**
- `dry_run` (boolean, default: false) - If true, report without deleting

**Response:** Combined results from both cleanup operations

## Configuration

Configure cleanup behavior via environment variables in `.env`:

```bash
# How long to keep failed sessions (default: 7 days)
FAILED_SESSION_RETENTION_DAYS=7

# How long to keep orphaned files (default: 24 hours)
ORPHANED_FILE_RETENTION_HOURS=24

# Run cleanup automatically on server startup (default: false)
AUTO_CLEANUP_ON_STARTUP=false

# Reserved for future scheduled cleanup (default: 3 AM)
CLEANUP_SCHEDULE_HOUR=3
```

### Recommended Settings

**Development:**
```bash
FAILED_SESSION_RETENTION_DAYS=1
ORPHANED_FILE_RETENTION_HOURS=12
AUTO_CLEANUP_ON_STARTUP=false
```

**Production:**
```bash
FAILED_SESSION_RETENTION_DAYS=7
ORPHANED_FILE_RETENTION_HOURS=24
AUTO_CLEANUP_ON_STARTUP=true
```

## Scheduled Cleanup (Production)

### Option 1: Cron Job

Add to crontab:

```bash
# Run cleanup daily at 3 AM
0 3 * * * cd /path/to/backend && source venv/bin/activate && python -c "import asyncio; from app.services.cleanup import run_scheduled_cleanup; asyncio.run(run_scheduled_cleanup())"
```

### Option 2: Cloud Scheduler

**AWS EventBridge:**
1. Create Lambda function that calls cleanup endpoint
2. Set EventBridge rule to trigger daily

**GCP Cloud Scheduler:**
1. Create HTTP target pointing to cleanup endpoint
2. Add service account token for authentication
3. Schedule daily execution

### Option 3: Celery Beat (if using Celery)

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('tasks')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run cleanup daily at 3 AM
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        cleanup_task.s(),
    )

@app.task
def cleanup_task():
    import asyncio
    from app.services.cleanup import run_scheduled_cleanup
    asyncio.run(run_scheduled_cleanup())
```

## Common Scenarios

### Scenario 1: Storage is running low

Check how much space can be freed:

```bash
curl "http://localhost:8000/api/admin/cleanup/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq '.potential_cleanup.total_space_freed_mb'
```

If significant space can be freed, run cleanup:

```bash
curl -X POST "http://localhost:8000/api/admin/cleanup/all" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Scenario 2: Testing new retention policies

1. Update `.env` with new retention periods
2. Restart server
3. Check what would be cleaned:
   ```bash
   curl "http://localhost:8000/api/admin/cleanup/status" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```
4. If satisfied, run cleanup

### Scenario 3: Failed upload left orphaned file

The cleanup service will automatically identify and remove orphaned files after the retention period (default: 24 hours).

To clean immediately:

```bash
# Check if file is detected
curl "http://localhost:8000/api/admin/cleanup/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Clean if retention period has passed
curl -X POST "http://localhost:8000/api/admin/cleanup/orphaned-files" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Scenario 4: Bulk cleanup after testing

After running many test uploads, clean up all orphaned files:

```bash
# See what will be deleted
curl -X POST "http://localhost:8000/api/admin/cleanup/all?dry_run=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Delete if looks correct
curl -X POST "http://localhost:8000/api/admin/cleanup/all" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Safety Features

### Dry-Run Mode

Always test with dry-run before actual deletion:

```bash
curl -X POST "http://localhost:8000/api/admin/cleanup/all?dry_run=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Retention Periods

Files are only deleted if they're older than configured retention periods:
- Orphaned files: 24 hours (configurable)
- Failed sessions: 7 days (configurable)

### Audit Trail

All cleanup operations are logged:
- Files deleted
- Timestamps
- Space freed
- Any errors encountered

Check server logs for detailed audit trail:

```bash
# If using systemd
journalctl -u therapybridge-api -f

# If running directly
# Check terminal where uvicorn is running
```

### Role-Based Access

Only therapists and admins can perform cleanup operations. Patient accounts cannot access cleanup endpoints.

## Troubleshooting

### "403 Forbidden" Error

You need therapist or admin role to perform cleanup operations.

**Solution:** Login with therapist/admin account:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "therapist@example.com", "password": "password"}'
```

### "Upload directory does not exist"

The `uploads/audio/` directory hasn't been created yet.

**Solution:** Create it:

```bash
mkdir -p uploads/audio
```

### No files being cleaned

Files might not be old enough to exceed retention period.

**Solution:** Check configuration and file ages:

```bash
# View config
curl "http://localhost:8000/api/admin/cleanup/config" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Check file ages
ls -lh uploads/audio/
```

### Cleanup deleting wrong files

**Prevention:** Always use dry-run first:

```bash
curl -X POST "http://localhost:8000/api/admin/cleanup/all?dry_run=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Recovery:** Files cannot be recovered after deletion. Use git to restore if needed (if files were committed).

## Best Practices

1. **Always dry-run first** - Test before actual deletion
2. **Monitor storage** - Set up alerts for low disk space
3. **Schedule regular cleanup** - Automate with cron or cloud scheduler
4. **Review cleanup logs** - Check for unexpected deletions
5. **Adjust retention periods** - Balance storage vs. data retention needs
6. **Test retention policies** - Use dry-run when changing config
7. **Backup before cleanup** - For critical environments

## Performance Considerations

- Cleanup is async and won't block API requests
- Large cleanups (1000+ files) may take several seconds
- Database queries are optimized with proper indexes
- File I/O is performed sequentially to avoid overwhelming disk

## Future Enhancements

Planned features (not yet implemented):

- ⏳ Automatic scheduled cleanup (cron-like)
- ⏳ Cleanup metrics and dashboards
- ⏳ Email notifications for cleanup results
- ⏳ Backup before cleanup option
- ⏳ Cleanup history tracking
