"""
Run database migrations using psycopg2
"""
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv("../audio-transcription-pipeline/.env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment")
    sys.exit(1)

print(f"Connecting to database...")

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2...")
    os.system("pip install psycopg2-binary")
    import psycopg2

# Read migration file
with open("migrations/001_initial_schema.sql", "r") as f:
    migration_sql = f.read()

# Connect and run migration
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("Running migration...")
    cursor.execute(migration_sql)
    conn.commit()

    print("✅ Migration completed successfully!")

    # Verify tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    print(f"\n📊 Created {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # Verify seed data
    cursor.execute("SELECT * FROM users;")
    users = cursor.fetchall()
    print(f"\n👤 Seeded {len(users)} user(s)")

    cursor.execute("SELECT * FROM patients;")
    patients = cursor.fetchall()
    print(f"👥 Seeded {len(patients)} patient(s)")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
