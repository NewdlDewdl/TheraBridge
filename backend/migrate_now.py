#!/usr/bin/env python3
"""
Apply migrations using Supabase connection pooler.
"""
import os
import sys
from pathlib import Path
from supabase import create_client

# Supabase credentials
SUPABASE_URL = "https://rfckpldoohyjctrqxmiv.supabase.co"
SUPABASE_SERVICE_KEY = "sb_secret_HtR41uMvaTUXZvKn0pSE6Q_Uwg8boP_"

# Initialize client with service role
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def read_sql(filename):
    """Read SQL file."""
    path = Path(__file__).parent / "supabase" / filename
    return path.read_text()

# Since Supabase Python client doesn't support raw SQL execution,
# we'll execute the migrations by creating temporary functions
print("=" * 70)
print("🚀 Applying Demo Mode Migrations")
print("=" * 70)

try:
    # Test connection
    print("\n1️⃣ Testing connection...")
    result = supabase.table('users').select("id").limit(1).execute()
    print("   ✅ Connected to Supabase")
    
    # We can't execute raw SQL via the Python client
    # Let's try using the SQL editor programmatically
    print("\n❌ Cannot execute raw SQL via Python client")
    print("\n📋 Please apply migrations manually:")
    print("   Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/sql")
    print("\n   Run these files in order:")
    print("   1. supabase/migrations/007_add_demo_mode_support.sql")
    print("   2. supabase/seed_demo_data.sql")
    print("   3. supabase/cleanup_demo_data.sql")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
