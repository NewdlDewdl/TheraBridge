"""
Tests for cleanup service

Basic tests to verify cleanup functionality works as expected.
"""
import pytest
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cleanup import (
    AudioCleanupService,
    CleanupConfig,
    run_scheduled_cleanup,
)
from app.models.db_models import Session


@pytest.fixture
def mock_upload_dir(tmp_path):
    """Create a temporary upload directory with test files"""
    upload_dir = tmp_path / "uploads" / "audio"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Create some test files
    (upload_dir / "test1.mp3").write_text("test1")
    (upload_dir / "test2.mp3").write_text("test2")
    (upload_dir / "test3_processed.mp3").write_text("test3_processed")

    return upload_dir


@pytest.fixture
def mock_config(mock_upload_dir):
    """Mock cleanup configuration"""
    original_upload_dir = CleanupConfig.UPLOAD_DIR

    CleanupConfig.UPLOAD_DIR = str(mock_upload_dir)

    yield

    CleanupConfig.UPLOAD_DIR = original_upload_dir


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_cleanup_service_initialization(mock_db_session):
    """Test that cleanup service can be initialized"""
    service = AudioCleanupService(db=mock_db_session)
    assert service.db == mock_db_session
    assert service.upload_dir is not None


@pytest.mark.asyncio
async def test_cleanup_service_context_manager():
    """Test that cleanup service can be used as context manager"""
    async with AudioCleanupService() as service:
        assert service.db is not None

    # DB should be closed after context exit
    # (we don't check this explicitly since it's mocked)


@pytest.mark.asyncio
async def test_scan_upload_directory(mock_config, mock_upload_dir, mock_db_session):
    """Test scanning upload directory for files"""
    service = AudioCleanupService(db=mock_db_session)

    files = service._scan_upload_directory()

    assert "test1.mp3" in files
    assert "test2.mp3" in files
    assert "test3_processed.mp3" in files
    assert ".gitkeep" not in files


@pytest.mark.asyncio
async def test_get_referenced_files(mock_db_session):
    """Test getting referenced files from database"""
    # Mock database response
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [
        "file1.mp3",
        "file2.m4a",
        None,  # Test null handling
    ]
    mock_db_session.execute.return_value = mock_result

    service = AudioCleanupService(db=mock_db_session)
    referenced = await service._get_referenced_files()

    # Should include both original and processed variants
    assert "file1.mp3" in referenced
    assert "file1_processed.mp3" in referenced
    assert "file2.m4a" in referenced
    assert "file2_processed.mp3" in referenced


@pytest.mark.asyncio
async def test_cleanup_orphaned_files_dry_run(
    mock_config, mock_upload_dir, mock_db_session
):
    """Test dry-run mode doesn't delete files"""
    # Mock database to return no referenced files
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    # Make files old enough to be cleaned
    for file in mock_upload_dir.iterdir():
        if file.name != ".gitkeep":
            old_time = datetime.now() - timedelta(hours=48)
            os.utime(file, (old_time.timestamp(), old_time.timestamp()))

    service = AudioCleanupService(db=mock_db_session)
    result = await service.cleanup_orphaned_files(dry_run=True)

    # Files should be identified but not deleted
    assert result.dry_run is True
    assert len(result.orphaned_files_deleted) > 0

    # Verify files still exist
    assert (mock_upload_dir / "test1.mp3").exists()
    assert (mock_upload_dir / "test2.mp3").exists()


@pytest.mark.asyncio
async def test_cleanup_orphaned_files_actual_deletion(
    mock_config, mock_upload_dir, mock_db_session
):
    """Test actual file deletion (not dry-run)"""
    # Mock database to return no referenced files
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    # Make files old enough to be cleaned
    for file in mock_upload_dir.iterdir():
        if file.name != ".gitkeep":
            old_time = datetime.now() - timedelta(hours=48)
            os.utime(file, (old_time.timestamp(), old_time.timestamp()))

    service = AudioCleanupService(db=mock_db_session)
    result = await service.cleanup_orphaned_files(dry_run=False)

    # Files should be deleted
    assert result.dry_run is False
    assert len(result.orphaned_files_deleted) > 0
    assert result.total_space_freed_mb > 0

    # Verify files are deleted
    assert not (mock_upload_dir / "test1.mp3").exists()
    assert not (mock_upload_dir / "test2.mp3").exists()


@pytest.mark.asyncio
async def test_cleanup_respects_retention_period(
    mock_config, mock_upload_dir, mock_db_session
):
    """Test that recent files are not deleted"""
    # Mock database to return no referenced files
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    # Files are new (created just now), should not be deleted
    service = AudioCleanupService(db=mock_db_session)
    result = await service.cleanup_orphaned_files(dry_run=False)

    # No files should be deleted (too recent)
    assert len(result.orphaned_files_deleted) == 0

    # Verify files still exist
    assert (mock_upload_dir / "test1.mp3").exists()
    assert (mock_upload_dir / "test2.mp3").exists()


@pytest.mark.asyncio
async def test_cleanup_failed_sessions(mock_config, mock_upload_dir, mock_db_session):
    """Test cleanup of failed sessions"""
    # Create test files
    (mock_upload_dir / "failed_session.m4a").write_text("test")
    (mock_upload_dir / "failed_session_processed.mp3").write_text("test_processed")

    # Mock database to return failed session
    mock_session = Session(
        id="test-uuid",
        status="failed",
        audio_filename="failed_session.m4a",
        created_at=datetime.now() - timedelta(days=10),
    )

    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [mock_session]
    mock_db_session.execute.return_value = mock_result

    service = AudioCleanupService(db=mock_db_session)
    result = await service.cleanup_failed_sessions(dry_run=False)

    # Session files should be deleted
    assert len(result.failed_sessions_cleaned) == 1
    assert "test-uuid" in result.failed_sessions_cleaned
    assert not (mock_upload_dir / "failed_session.m4a").exists()
    assert not (mock_upload_dir / "failed_session_processed.mp3").exists()


@pytest.mark.asyncio
async def test_cleanup_all_combines_results(mock_db_session):
    """Test that cleanup_all combines results from all cleanup operations"""
    service = AudioCleanupService(db=mock_db_session)

    # Mock both cleanup methods
    with patch.object(
        service, "cleanup_orphaned_files", new_callable=AsyncMock
    ) as mock_orphaned:
        with patch.object(
            service, "cleanup_failed_sessions", new_callable=AsyncMock
        ) as mock_failed:
            from app.services.cleanup import CleanupResult

            # Create mock results
            orphaned_result = CleanupResult()
            orphaned_result.orphaned_files_deleted = ["file1.mp3"]
            orphaned_result.total_space_freed_mb = 5.0

            failed_result = CleanupResult()
            failed_result.failed_sessions_cleaned = ["session1"]
            failed_result.total_space_freed_mb = 3.0

            mock_orphaned.return_value = orphaned_result
            mock_failed.return_value = failed_result

            # Run cleanup_all
            result = await service.cleanup_all(dry_run=False)

            # Should combine results
            assert len(result.orphaned_files_deleted) == 1
            assert len(result.failed_sessions_cleaned) == 1
            assert result.total_space_freed_mb == 8.0


def test_cleanup_result_to_dict():
    """Test CleanupResult serialization"""
    from app.services.cleanup import CleanupResult

    result = CleanupResult()
    result.orphaned_files_deleted = ["file1.mp3", "file2.mp3"]
    result.failed_sessions_cleaned = ["session1"]
    result.total_space_freed_mb = 10.5
    result.errors = ["error1"]
    result.dry_run = True

    result_dict = result.to_dict()

    assert result_dict["orphaned_files_count"] == 2
    assert result_dict["failed_sessions_count"] == 1
    assert result_dict["total_space_freed_mb"] == 10.5
    assert result_dict["error_count"] == 1
    assert result_dict["dry_run"] is True
