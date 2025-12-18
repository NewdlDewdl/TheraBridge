#!/usr/bin/env python
"""
Debug script to test async database initialization.
Tests if all tables are created and database is writable.
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, event, JSON
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base
import app.models  # Import all models to register with Base.metadata

# Test database URL
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./test_debug.db"

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True,  # Enable SQL logging
    future=True,
)

# Convert JSONB to JSON for SQLite compatibility
@event.listens_for(Base.metadata, "before_create")
def _set_json_columns(target, connection, **kw):
    """
    Convert JSONB columns to JSON for SQLite.
    SQLite doesn't support JSONB (PostgreSQL-specific type),
    so we replace it with JSON for tests.
    """
    # Only convert if using SQLite
    if connection.dialect.name == "sqlite":
        print(f"  Converting JSONB columns to JSON for table: {target}")
        for table in Base.metadata.tables.values():
            for col in table.columns:
                # Check if column type is JSONB or has JSONB as impl
                if isinstance(col.type, JSONB):
                    print(f"    - Converting {table.name}.{col.name}: JSONB -> JSON")
                    col.type = JSON()
                elif hasattr(col.type, 'impl') and isinstance(col.type.impl, JSONB):
                    print(f"    - Converting {table.name}.{col.name}: wrapped JSONB -> JSON")
                    col.type = JSON()

# Enable WAL mode for async SQLite connections
@event.listens_for(async_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable WAL mode for SQLite to support async writes"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

AsyncTestingSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def test_async_db():
    """Test async database initialization"""
    print("=" * 80)
    print("STEP 1: Creating all tables")
    print("=" * 80)

    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("\n" + "=" * 80)
    print("STEP 2: Listing all tables in Base.metadata")
    print("=" * 80)
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

    print("\n" + "=" * 80)
    print("STEP 3: Querying sqlite_master to see created tables")
    print("=" * 80)

    async with AsyncTestingSessionLocal() as session:
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        tables = result.scalars().all()
        print(f"Tables in database: {tables}")

        # Check if users table exists
        if 'users' not in tables:
            print("❌ ERROR: 'users' table NOT found in database!")
            return False
        else:
            print("✅ SUCCESS: 'users' table found in database")

        # Try to insert a user
        print("\n" + "=" * 80)
        print("STEP 4: Testing database writability by inserting a user")
        print("=" * 80)

        try:
            from app.models.db_models import User
            from app.models.schemas import UserRole
            from app.auth.utils import get_password_hash

            test_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("TestPass123!"),
                first_name="Test",
                last_name="User",
                full_name="Test User",
                role=UserRole.therapist,
                is_active=True,
                is_verified=False
            )
            session.add(test_user)
            await session.flush()
            print(f"✅ SUCCESS: User inserted successfully with ID: {test_user.id}")

            # Try to commit
            await session.commit()
            print("✅ SUCCESS: Transaction committed successfully")
            return True

        except Exception as e:
            print(f"❌ ERROR during insert/commit: {e}")
            await session.rollback()
            return False


async def main():
    """Main test function"""
    try:
        success = await test_async_db()

        if success:
            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED - Async database initialization works correctly")
            print("=" * 80)
            return 0
        else:
            print("\n" + "=" * 80)
            print("❌ TESTS FAILED - Async database initialization has issues")
            print("=" * 80)
            return 1

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        print("\n" + "=" * 80)
        print("CLEANUP: Dropping all tables")
        print("=" * 80)
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await async_engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
