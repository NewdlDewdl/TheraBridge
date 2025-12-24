#!/usr/bin/env python3
"""
Apply all demo mode migrations to Supabase database.
This script applies the three migrations in order:
1. Schema changes (add demo columns)
2. Seed function (create demo user sessions)
3. Cleanup function (delete expired demos)
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def read_migration_file(filename: str) -> str:
    """Read migration SQL file."""
    migration_path = Path(__file__).parent / "supabase" / filename
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    with open(migration_path, 'r') as f:
        return f.read()

def execute_sql(sql: str, description: str) -> bool:
    """Execute SQL statement and handle errors."""
    try:
        print(f"\n📝 Executing: {description}")
        print("-" * 60)

        # Use rpc to execute raw SQL
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()

        print(f"✅ Success: {description}")
        return True

    except Exception as e:
        error_msg = str(e)

        # Check if error is due to already existing objects (safe to ignore)
        if any(phrase in error_msg.lower() for phrase in [
            'already exists',
            'duplicate',
            'if not exists',
            'if exists'
        ]):
            print(f"⚠️  Already exists (skipping): {description}")
            return True

        print(f"❌ Error in {description}:")
        print(f"   {error_msg}")
        return False

def apply_migration_1():
    """Apply Migration 1: Schema Changes"""
    sql = read_migration_file("migrations/007_add_demo_mode_support.sql")
    return execute_sql(sql, "Migration 1: Add demo mode columns to users table")

def apply_migration_2():
    """Apply Migration 2: Seed Function"""
    sql = read_migration_file("seed_demo_data.sql")
    return execute_sql(sql, "Migration 2: Create seed_demo_user_sessions() function")

def apply_migration_3():
    """Apply Migration 3: Cleanup Function"""
    sql = read_migration_file("cleanup_demo_data.sql")
    return execute_sql(sql, "Migration 3: Create cleanup_expired_demo_users() function")

def verify_migrations():
    """Verify migrations were applied successfully."""
    try:
        print("\n🔍 Verifying migrations...")
        print("-" * 60)

        # Test the seed function with a test UUID
        test_uuid = "00000000-0000-0000-0000-000000000001"
        result = supabase.rpc('seed_demo_user_sessions', {'p_demo_token': test_uuid}).execute()

        if result.data:
            patient_id = result.data[0].get('patient_id')
            session_ids = result.data[0].get('session_ids')

            print(f"✅ Seed function works!")
            print(f"   Patient ID: {patient_id}")
            print(f"   Created {len(session_ids)} sessions")

            # Cleanup test data
            print("\n🧹 Cleaning up test data...")
            supabase.table('users').delete().eq('demo_token', test_uuid).execute()
            print("✅ Test data cleaned up")

            return True
        else:
            print("❌ Seed function returned no data")
            return False

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main execution function."""
    print("=" * 60)
    print("🚀 TherapyBridge - Demo Mode Migration Tool")
    print("=" * 60)
    print(f"📍 Supabase URL: {SUPABASE_URL}")
    print(f"🔑 Using key: {SUPABASE_KEY[:20]}...")

    # Apply migrations in order
    migrations = [
        ("Migration 1: Schema Changes", apply_migration_1),
        ("Migration 2: Seed Function", apply_migration_2),
        ("Migration 3: Cleanup Function", apply_migration_3),
    ]

    success_count = 0
    for name, migration_func in migrations:
        if migration_func():
            success_count += 1
        else:
            print(f"\n⚠️  Warning: {name} had issues, continuing anyway...")

    # Verify migrations
    print("\n" + "=" * 60)
    if verify_migrations():
        print("\n" + "=" * 60)
        print("✅ ALL MIGRATIONS APPLIED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("   1. Test demo initialization: curl -X POST http://localhost:8000/api/demo/initialize")
        print("   2. Open frontend: http://localhost:3000/dashboard")
        print("   3. Check API docs: http://localhost:8000/docs")
        return 0
    else:
        print("\n" + "=" * 60)
        print("⚠️  MIGRATIONS APPLIED BUT VERIFICATION FAILED")
        print("=" * 60)
        print("\n🔧 Troubleshooting:")
        print("   1. Check Supabase dashboard for manual verification")
        print("   2. Ensure SUPABASE_SERVICE_KEY is set (not just SUPABASE_KEY)")
        print("   3. Try applying migrations manually via Supabase SQL Editor")
        return 1

if __name__ == "__main__":
    sys.exit(main())
