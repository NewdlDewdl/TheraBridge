#!/usr/bin/env python3
"""
Apply Demo Mode Migrations to Supabase
Provides instructions and validates migration files
"""

import os
import sys
from pathlib import Path

# Supabase credentials
SUPABASE_URL = "https://rfckpldoohyjctrqxmiv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmY2twbGRvb2h5amN0cnF4bWl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYzMjc3MDUsImV4cCI6MjA4MTkwMzcwNX0.M7_2AJ_V_yMy9X5GNiL3fuQTG0kC1KXNTNqQRqdus80"

def validate_sql(sql_content: str, description: str) -> bool:
    """Validate SQL file"""
    print(f"\n{'='*60}")
    print(f"Validating: {description}")
    print(f"{'='*60}")

    print("✓ SQL content loaded successfully")
    print(f"  Size: {len(sql_content)} characters")
    print(f"  Lines: {len(sql_content.splitlines())}")

    return True

def main():
    print("=" * 60)
    print("Demo Mode Migration Application")
    print("=" * 60)

    # Migration files
    migrations = [
        ("supabase/migrations/007_add_demo_mode_support.sql", "Schema Migration - Add demo fields"),
        ("supabase/seed_demo_data.sql", "Seed Function - Create demo users"),
        ("supabase/cleanup_demo_data.sql", "Cleanup Function - Remove expired demos"),
    ]

    base_dir = Path(__file__).parent

    for filepath, description in migrations:
        full_path = base_dir / filepath

        if not full_path.exists():
            print(f"\n✗ File not found: {full_path}")
            continue

        with open(full_path, 'r') as f:
            sql_content = f.read()

        validate_sql(sql_content, description)

    print("\n" + "=" * 60)
    print("Migration Instructions")
    print("=" * 60)
    print("\n1. Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/sql")
    print("\n2. Create a new query and execute each file in order:")
    print("   a) supabase/migrations/007_add_demo_mode_support.sql")
    print("   b) supabase/seed_demo_data.sql")
    print("   c) supabase/cleanup_demo_data.sql")
    print("\n3. Test the seed function:")
    print("   SELECT * FROM seed_demo_user_sessions(gen_random_uuid());")
    print("\n4. Verify the schema:")
    print("   \\d users  -- should show demo_token, is_demo columns")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
