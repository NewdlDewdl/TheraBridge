#!/usr/bin/env python3
"""
Database Backup Script for TherapyBridge

Exports all database tables to JSON format for safe migration and recovery.
Connects using DATABASE_URL from environment.

Usage:
    python scripts/backup_database.py
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables from .env
load_dotenv()

def backup_database():
    """
    Backup all database tables to JSON format.

    Tables backed up:
    - users: User authentication and roles
    - patients: Patient profiles and metadata
    - sessions: Therapy session data
    - patient_strategies: Tracked coping strategies
    - patient_triggers: Identified patient triggers
    - action_items: Homework and action items

    Returns:
        str: Path to created backup file
    """

    # Verify environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        print("   Please ensure .env file is configured")
        sys.exit(1)

    print("\n" + "="*60)
    print("TherapyBridge Database Backup")
    print("="*60)

    try:
        # Connect to database
        print(f"\nConnecting to database...")
        conn = psycopg2.connect(database_url)
        print("Connection established")

    except psycopg2.OperationalError as e:
        print(f"DATABASE CONNECTION FAILED: {e}")
        print("   Check DATABASE_URL and network connectivity")
        sys.exit(1)

    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

    # Initialize backup structure
    backup = {
        'timestamp': datetime.utcnow().isoformat(),
        'tables': {},
        'summary': {}
    }

    # Tables to backup (in dependency order)
    tables = [
        'users',
        'patients',
        'sessions',
        'patient_strategies',
        'patient_triggers',
        'action_items'
    ]

    total_rows = 0
    backed_up_tables = 0

    # Backup each table
    print(f"\nBacking up {len(tables)} tables...")
    print("-" * 60)

    for table in tables:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get row count
                cur.execute(f'SELECT COUNT(*) as count FROM {table};')
                count_result = cur.fetchone()
                row_count = count_result['count'] if count_result else 0

                # Fetch all data
                cur.execute(f'SELECT * FROM {table};')
                rows = cur.fetchall()

                # Convert to list of dicts
                backup['tables'][table] = [dict(row) for row in rows]

                total_rows += row_count
                backed_up_tables += 1

                print(f"  [OK] {table:<25} {row_count:>5} rows")
                backup['summary'][table] = row_count

        except psycopg2.ProgrammingError:
            print(f"  [SKIP] {table:<25} TABLE NOT FOUND (not yet created)")
        except Exception as e:
            print(f"  [ERROR] {table:<25} {str(e)[:40]}")

    conn.close()

    # Save backup file
    print("-" * 60)
    print(f"\nSaving backup file...")

    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path('migrations/backups')
    backup_dir.mkdir(parents=True, exist_ok=True)

    filename = backup_dir / f'backup_{timestamp}.json'

    try:
        with open(filename, 'w') as f:
            json.dump(backup, f, indent=2, default=str)

        file_size = filename.stat().st_size
        print(f"[OK] Backup saved: {filename}")
        print(f"     File size: {file_size:,} bytes")

    except IOError as e:
        print(f"FAILED TO SAVE BACKUP: {e}")
        sys.exit(1)

    # Verification
    print(f"\n[COMPLETE] Database Backup Successful")
    print(f"   Tables backed up: {backed_up_tables}/{len(tables)}")
    print(f"   Total rows: {total_rows}")
    print(f"   Timestamp: {backup['timestamp']}")
    print("="*60 + "\n")

    return str(filename)

if __name__ == '__main__':
    backup_file = backup_database()
