#!/usr/bin/env python3
"""
Apply all demo mode migrations to Supabase database using direct PostgreSQL connection.
This script applies the three migrations in order:
1. Schema changes (add demo columns)
2. Seed function (create demo user sessions)
3. Cleanup function (delete expired demos)
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")

# Extract database connection details from Supabase URL
# Format: https://[PROJECT_REF].supabase.co
# Database connection: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

def get_db_connection_string():
    """Construct PostgreSQL connection string."""
    # We need the database password - it's not in the .env
    # Let's try using the Supabase connection pooler instead
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL not found in .env")

    project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")

    # Ask user for database password
    print("=" * 60)
    print("🔐 Database Password Required")
    print("=" * 60)
    print(f"Project: {project_ref}")
    print("\nTo find your database password:")
    print("1. Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/settings/database")
    print("2. Look for 'Database Password' section")
    print("3. Copy the password (or reset if forgotten)")
    print()

    db_password = input("Enter database password (or press Enter to skip): ").strip()

    if not db_password:
        print("\n⚠️  No password provided. Trying alternative method...")
        return None

    # Connection string for direct database access
    connection_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    return connection_string

def read_migration_file(filename: str) -> str:
    """Read migration SQL file."""
    migration_path = Path(__file__).parent / "supabase" / filename
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    with open(migration_path, 'r') as f:
        return f.read()

def execute_migration_via_postgres(connection_string: str, sql: str, description: str) -> bool:
    """Execute SQL via direct PostgreSQL connection."""
    try:
        print(f"\n📝 Executing: {description}")
        print("-" * 60)

        # Connect to database
        conn = psycopg2.connect(connection_string)
        conn.set_session(autocommit=True)
        cursor = conn.cursor()

        # Execute SQL
        cursor.execute(sql)

        # Check for results
        if cursor.description:
            results = cursor.fetchall()
            print(f"   Rows affected: {len(results)}")

        cursor.close()
        conn.close()

        print(f"✅ Success: {description}")
        return True

    except psycopg2.Error as e:
        error_msg = str(e)

        # Check if error is due to already existing objects (safe to ignore)
        if any(phrase in error_msg.lower() for phrase in [
            'already exists',
            'duplicate',
        ]):
            print(f"⚠️  Already exists (skipping): {description}")
            return True

        print(f"❌ Error in {description}:")
        print(f"   {error_msg}")
        return False

def main():
    """Main execution function."""
    print("=" * 60)
    print("🚀 TherapyBridge - Demo Mode Migration Tool")
    print("=" * 60)

    # Get connection string
    connection_string = get_db_connection_string()

    if not connection_string:
        print("\n" + "=" * 60)
        print("⚠️  ALTERNATIVE APPROACH NEEDED")
        print("=" * 60)
        print("\nSince direct database access requires the password,")
        print("please use ONE of these methods:\n")
        print("METHOD 1: Apply via Supabase SQL Editor (Manual)")
        print("  → Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/sql")
        print("  → Run the SQL files in order:\n")
        print("     1. backend/supabase/migrations/007_add_demo_mode_support.sql")
        print("     2. backend/supabase/seed_demo_data.sql")
        print("     3. backend/supabase/cleanup_demo_data.sql")
        print("\nMETHOD 2: Provide Service Role Key")
        print("  → Add SUPABASE_SERVICE_KEY to .env file")
        print("  → Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/settings/api")
        print("  → Copy the 'service_role' key (not anon key)")
        print("  → Add to .env: SUPABASE_SERVICE_KEY=eyJhb...")
        print("\nMETHOD 3: Re-run this script with database password")
        print("  → python apply_migrations_direct.py")
        print()
        return 1

    # Read migration files
    try:
        migration_1 = read_migration_file("migrations/007_add_demo_mode_support.sql")
        migration_2 = read_migration_file("seed_demo_data.sql")
        migration_3 = read_migration_file("cleanup_demo_data.sql")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    # Apply migrations
    success = True
    success = execute_migration_via_postgres(connection_string, migration_1, "Migration 1: Schema Changes") and success
    success = execute_migration_via_postgres(connection_string, migration_2, "Migration 2: Seed Function") and success
    success = execute_migration_via_postgres(connection_string, migration_3, "Migration 3: Cleanup Function") and success

    if success:
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
        print("⚠️  SOME MIGRATIONS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
