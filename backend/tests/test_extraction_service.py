"""
Unit tests for note extraction service
"""
import pytest
from app.services.note_extraction import NoteExtractionService
from app.models.schemas import ExtractedNotes
from tests.fixtures.sample_transcripts import SAMPLE_TRANSCRIPT_1


@pytest.mark.asyncio
async def test_extract_notes_basic():
    """Test basic note extraction from sample transcript"""
    service = NoteExtractionService()

    notes = await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)

    # Verify it returns correct type
    assert isinstance(notes, ExtractedNotes)

    # Verify required fields are populated
    assert len(notes.key_topics) >= 3
    assert len(notes.topic_summary) > 50
    assert notes.therapist_notes
    assert notes.patient_summary
    assert notes.session_mood

    # Verify strategies were extracted
    assert len(notes.strategies) > 0
    assert notes.strategies[0].name
    assert notes.strategies[0].category

    # Verify action items
    assert len(notes.action_items) > 0

    # Print for manual review
    print("\n" + "="*60)
    print("EXTRACTED NOTES")
    print("="*60)
    print(f"\nTopics: {', '.join(notes.key_topics)}")
    print(f"\nSummary: {notes.topic_summary}")
    print(f"\nStrategies:")
    for s in notes.strategies:
        print(f"  - {s.name} ({s.category}) - {s.status}")
    print(f"\nAction Items:")
    for a in notes.action_items:
        print(f"  - {a.task}")
    print(f"\nMood: {notes.session_mood} ({notes.mood_trajectory})")
    print("\n" + "="*60)


@pytest.mark.asyncio
async def test_cost_estimation():
    """Test cost estimation for extraction"""
    service = NoteExtractionService()

    cost = service.estimate_cost(SAMPLE_TRANSCRIPT_1)

    assert cost["estimated_input_tokens"] > 0
    assert cost["estimated_output_tokens"] > 0
    assert cost["estimated_cost_usd"] > 0
    assert cost["estimated_cost_usd"] < 0.50  # Should be pennies

    print(f"\nEstimated cost: ${cost['estimated_cost_usd']:.4f}")
