#!/usr/bin/env python3
"""
Apply demo mode migrations programmatically.
Since Supabase Python client doesn't support raw SQL, we'll execute via PostgREST.
"""

import sys
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

print("=" * 70)
print("🚀 TherapyBridge - Demo Mode Migration Tool")
print("=" * 70)
print(f"📍 URL: {SUPABASE_URL}")
print(f"🔑 Key: {SERVICE_KEY[:30]}...")
print()

def read_sql(filename):
    """Read SQL file from supabase/ directory."""
    path = Path(__file__).parent / "supabase" / filename
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    return path.read_text()

def execute_via_postgrest(sql: str, description: str) -> bool:
    """
    Execute SQL by POSTing directly to PostgREST.
    This is a workaround since Supabase Python client doesn't support raw SQL.
    """
    print(f"\n📝 {description}")
    print("-" * 70)

    # PostgREST doesn't have a direct SQL endpoint
    # We need to use the Supabase Management API or execute via a custom function

    # Let's try creating an RPC function first
    url = f"{SUPABASE_URL}/rest/v1/rpc"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # This won't work because we can't create functions via RPC
    print("   ⚠️  PostgREST doesn't support direct SQL execution")
    return False

def main():
    """
    Main function - displays manual instructions since automated execution isn't possible.
    """

    # Read all migrations
    try:
        migration_1 = read_sql("migrations/007_add_demo_mode_support.sql")
        migration_2 = read_sql("seed_demo_data.sql")
        migration_3 = read_sql("cleanup_demo_data.sql")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    print("📋 AUTOMATED EXECUTION NOT AVAILABLE")
    print("=" * 70)
    print("\nSupabase REST API doesn't support direct SQL execution.")
    print("You need to apply migrations via Supabase SQL Editor.\n")

    print("🔗 Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/sql\n")

    print("─" * 70)
    print("STEP 1: Apply Schema Changes")
    print("─" * 70)
    print("\nClick 'New Query' and paste:\n")
    print(migration_1)
    print("\n✅ Click RUN. Expected: 'Success. No rows returned'\n")

    print("─" * 70)
    print("STEP 2: Create Seed Function")
    print("─" * 70)
    print("\nClick 'New Query' and paste the ENTIRE contents of:")
    print(f"   {Path(__file__).parent}/supabase/seed_demo_data.sql")
    print("\n✅ Click RUN. Expected: 'CREATE FUNCTION'\n")

    print("─" * 70)
    print("STEP 3: Create Cleanup Function")
    print("─" * 70)
    print("\nClick 'New Query' and paste:\n")
    print(migration_3)
    print("\n✅ Click RUN. Expected: 'CREATE FUNCTION'\n")

    print("=" * 70)
    print("🧪 VERIFICATION")
    print("=" * 70)
    print("\nAfter completing the above steps, run this query:\n")
    print("SELECT * FROM seed_demo_user_sessions(gen_random_uuid());")
    print("\n✅ Expected: Table showing patient_id and array of 10 UUIDs\n")

    print("=" * 70)
    print("💡 TIP: Copy migrations from terminal output above")
    print("=" * 70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
