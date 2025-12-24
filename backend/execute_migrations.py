#!/usr/bin/env python3
"""
Execute demo mode migrations using direct PostgreSQL connection.
Requires database password.
"""

import sys
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv()

PROJECT_REF = "rfckpldoohyjctrqxmiv"

print("=" * 70)
print("🚀 TherapyBridge - Database Migration Tool")
print("=" * 70)
print(f"📍 Project: {PROJECT_REF}")
print()

# Get database password
print("🔐 Database Connection Required")
print("-" * 70)
print("To find your database password:")
print(f"1. Go to: https://supabase.com/dashboard/project/{PROJECT_REF}/settings/database")
print("2. Look for 'Database Password' or 'Connection String'")
print("3. Copy the password")
print()

db_password = input("Enter database password (or 'skip' to see manual instructions): ").strip()

if db_password.lower() == 'skip' or not db_password:
    print("\n" + "=" * 70)
    print("📋 MANUAL MIGRATION INSTRUCTIONS")
    print("=" * 70)
    print(f"\n1. Go to: https://supabase.com/dashboard/project/{PROJECT_REF}/sql")
    print("\n2. Execute these queries in order:\n")

    files = [
        ("migrations/007_add_demo_mode_support.sql", "Schema Changes"),
        ("seed_demo_data.sql", "Seed Function"),
        ("cleanup_demo_data.sql", "Cleanup Function")
    ]

    for i, (filename, desc) in enumerate(files, 1):
        filepath = Path(__file__).parent / "supabase" / filename
        print(f"   Query {i}: {desc}")
        print(f"   File: {filepath}")
        print()

    print("3. Verify with:")
    print("   SELECT * FROM seed_demo_user_sessions(gen_random_uuid());")
    print()
    sys.exit(0)

# Connect to database
connection_string = f"postgresql://postgres.{PROJECT_REF}:{db_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

print("\n📡 Connecting to database...")
print("-" * 70)

try:
    conn = psycopg2.connect(connection_string)
    conn.set_session(autocommit=True)
    cursor = conn.cursor()
    print("✅ Connected successfully!")

    # Read migration files
    def read_sql(filename):
        path = Path(__file__).parent / "supabase" / filename
        return path.read_text()

    migrations = [
        ("migrations/007_add_demo_mode_support.sql", "Schema Changes - Add demo columns"),
        ("seed_demo_data.sql", "Seed Function - Create demo sessions"),
        ("cleanup_demo_data.sql", "Cleanup Function - Delete expired demos")
    ]

    # Execute each migration
    for filename, description in migrations:
        print(f"\n📝 Executing: {description}")
        print("-" * 70)

        sql = read_sql(filename)

        try:
            cursor.execute(sql)
            print(f"✅ Success: {description}")
        except psycopg2.Error as e:
            if 'already exists' in str(e).lower():
                print(f"⚠️  Already exists (skipping): {description}")
            else:
                print(f"❌ Error: {e}")
                raise

    # Verify migrations
    print("\n🧪 Verifying migrations...")
    print("-" * 70)

    test_uuid = '00000000-0000-0000-0000-000000000001'
    cursor.execute(f"SELECT * FROM seed_demo_user_sessions('{test_uuid}'::uuid);")
    result = cursor.fetchone()

    if result:
        patient_id, session_ids = result
        print(f"✅ Seed function works!")
        print(f"   Patient ID: {patient_id}")
        print(f"   Sessions created: {len(session_ids)}")

        # Cleanup test data
        print("\n🧹 Cleaning up test data...")
        cursor.execute(f"DELETE FROM users WHERE demo_token = '{test_uuid}'::uuid;")
        print("✅ Test data removed")

    cursor.close()
    conn.close()

    print("\n" + "=" * 70)
    print("✅ ALL MIGRATIONS APPLIED SUCCESSFULLY!")
    print("=" * 70)
    print("\n📋 Next Steps:")
    print("   1. Test demo initialization:")
    print("      curl -X POST http://localhost:8000/api/demo/initialize | jq")
    print()
    print("   2. Open frontend:")
    print("      http://localhost:3000/dashboard")
    print()

except psycopg2.OperationalError as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n💡 Troubleshooting:")
    print("   - Verify password is correct")
    print("   - Check if database allows external connections")
    print("   - Try manual migration via Supabase SQL Editor")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
