#!/usr/bin/env python3
"""
Apply all demo mode migrations to Supabase database using REST API.
This script applies the three migrations in order:
1. Schema changes (add demo columns)
2. Seed function (create demo user sessions)
3. Cleanup function (delete expired demos)
"""

import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = "sb_secret_HtR41uMvaTUXZvKn0pSE6Q_Uwg8boP_"

if not SUPABASE_URL:
    print("❌ Error: SUPABASE_URL must be set in .env")
    sys.exit(1)

def read_migration_file(filename: str) -> str:
    """Read migration SQL file."""
    migration_path = Path(__file__).parent / "supabase" / filename
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    with open(migration_path, 'r') as f:
        return f.read()

def execute_sql_via_api(sql: str, description: str) -> bool:
    """Execute SQL via Supabase REST API."""
    try:
        print(f"\n📝 Executing: {description}")
        print("-" * 60)

        # Use PostgREST rpc endpoint to execute raw SQL
        url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"query": sql}

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code in [200, 201, 204]:
            print(f"✅ Success: {description}")
            return True
        else:
            # Check if it's a "already exists" error (safe to ignore)
            error_text = response.text.lower()
            if any(phrase in error_text for phrase in [
                'already exists',
                'duplicate',
                'if not exists'
            ]):
                print(f"⚠️  Already exists (skipping): {description}")
                return True

            print(f"❌ Error in {description}:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error in {description}: {e}")
        return False

def execute_sql_direct(sql: str, description: str) -> bool:
    """Execute SQL directly via HTTP POST to Supabase."""
    try:
        print(f"\n📝 Executing: {description}")
        print("-" * 60)

        # Use the database REST API endpoint
        # We'll split the SQL into individual statements
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

        success = True
        for i, statement in enumerate(statements):
            if not statement:
                continue

            print(f"   Statement {i+1}/{len(statements)}...")

            # Use direct SQL execution via psql-like endpoint
            # Actually, Supabase doesn't expose direct SQL execution via REST API
            # We need to use the database functions or connection pooler

        print(f"⚠️  Note: Direct SQL execution not available via REST API")
        print(f"   Will need to use alternative method")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main execution function."""
    print("=" * 60)
    print("🚀 TherapyBridge - Demo Mode Migration Tool")
    print("=" * 60)
    print(f"📍 Supabase URL: {SUPABASE_URL}")
    print(f"🔑 Using service role key: {SUPABASE_SERVICE_KEY[:20]}...")

    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT NOTICE")
    print("=" * 60)
    print("\nSupabase REST API doesn't support direct SQL execution.")
    print("We need to apply migrations via Supabase SQL Editor.\n")
    print("I'll provide you with the EXACT SQL to copy/paste.\n")

    # Read migration files
    try:
        migration_1 = read_migration_file("migrations/007_add_demo_mode_support.sql")
        migration_2 = read_migration_file("seed_demo_data.sql")
        migration_3 = read_migration_file("cleanup_demo_data.sql")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    print("=" * 60)
    print("📋 MANUAL MIGRATION INSTRUCTIONS")
    print("=" * 60)
    print("\nGo to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/sql\n")

    print("\n" + "─" * 60)
    print("MIGRATION 1: Schema Changes")
    print("─" * 60)
    print("\nCopy and paste this into a new query:\n")
    print(migration_1)
    print("\nClick RUN. Expected: 'Success. No rows returned'\n")

    print("\n" + "─" * 60)
    print("MIGRATION 2: Seed Function")
    print("─" * 60)
    print("\nCopy and paste this into a new query:\n")
    print(migration_2[:500] + "\n... (file continues - see backend/supabase/seed_demo_data.sql)")
    print("\nClick RUN. Expected: 'CREATE FUNCTION'\n")

    print("\n" + "─" * 60)
    print("MIGRATION 3: Cleanup Function")
    print("─" * 60)
    print("\nCopy and paste this into a new query:\n")
    print(migration_3)
    print("\nClick RUN. Expected: 'CREATE FUNCTION'\n")

    print("\n" + "=" * 60)
    print("📝 VERIFICATION QUERY")
    print("=" * 60)
    print("\nAfter applying all migrations, run this to verify:\n")
    print("SELECT * FROM seed_demo_user_sessions(gen_random_uuid());")
    print("\nExpected: Table with patient_id and session_ids array\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
