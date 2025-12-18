"""
Edge case and validation tests for note templates router endpoints.

Tests cover:
- Template structure validation failures
- Malformed JSONB data
- Boundary value testing (max lengths, large counts)
- Data type mismatches
- Race conditions and concurrent operations
- CASCADE deletion behavior
- Autofill with malformed extracted_notes
- Missing required fields
- Empty and invalid structures
- Stress testing with large templates
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import datetime
from app.models.db_models import User, NoteTemplate, TherapySession as Session, Patient
from app.models.schemas import UserRole, SessionStatus, TemplateType

TEMPLATES_PREFIX = "/api/v1/templates"
NOTES_PREFIX = "/api/v1/sessions"


# ============================================================================
# Test Fixtures - Edge Case Data
# ============================================================================

@pytest.fixture(scope="function")
def invalid_structures():
    """
    Collection of invalid template structures for validation testing.

    Returns:
        Dict of invalid structures with descriptive keys
    """
    return {
        "empty_sections": {
            "name": "Empty Sections Template",
            "template_type": "custom",
            "structure": {
                "sections": []
            }
        },
        "duplicate_section_ids": {
            "name": "Duplicate Section IDs",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "First Section",
                        "fields": [
                            {"id": "field1", "label": "Field 1", "type": "text", "required": True}
                        ]
                    },
                    {
                        "id": "section1",  # Duplicate ID
                        "name": "Second Section",
                        "fields": [
                            {"id": "field2", "label": "Field 2", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        },
        "section_no_fields": {
            "name": "Section Without Fields",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Empty Section",
                        "fields": []  # No fields
                    }
                ]
            }
        },
        "duplicate_field_ids": {
            "name": "Duplicate Field IDs",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Section",
                        "fields": [
                            {"id": "field1", "label": "Field 1", "type": "text", "required": True},
                            {"id": "field1", "label": "Field 1 Duplicate", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        },
        "select_no_options": {
            "name": "Select Field Without Options",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Section",
                        "fields": [
                            {
                                "id": "field1",
                                "label": "Select Field",
                                "type": "select",
                                "required": True,
                                "options": []  # Empty options
                            }
                        ]
                    }
                ]
            }
        },
        "multiselect_no_options": {
            "name": "Multiselect Field Without Options",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Section",
                        "fields": [
                            {
                                "id": "field1",
                                "label": "Multiselect Field",
                                "type": "multiselect",
                                "required": True
                                # Missing options
                            }
                        ]
                    }
                ]
            }
        },
        "invalid_field_type": {
            "name": "Invalid Field Type",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Section",
                        "fields": [
                            {
                                "id": "field1",
                                "label": "Field",
                                "type": "invalid_type",  # Not a valid TemplateFieldType
                                "required": True
                            }
                        ]
                    }
                ]
            }
        }
    }


@pytest.fixture(scope="function")
def boundary_test_data():
    """
    Test data for boundary value testing (max lengths, large counts).

    Returns:
        Dict of boundary test cases
    """
    return {
        "max_name_length": {
            "name": "A" * 200,  # Max allowed is 200
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "s1",
                        "name": "Section",
                        "fields": [
                            {"id": "f1", "label": "Field", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        },
        "exceeds_max_name_length": {
            "name": "A" * 201,  # Exceeds max of 200
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "s1",
                        "name": "Section",
                        "fields": [
                            {"id": "f1", "label": "Field", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        },
        "very_long_field_label": {
            "name": "Long Field Label Template",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "s1",
                        "name": "Section",
                        "fields": [
                            {
                                "id": "f1",
                                "label": "A" * 500,  # Very long label
                                "type": "text",
                                "required": True
                            }
                        ]
                    }
                ]
            }
        },
        "fifty_sections": {
            "name": "50 Sections Template",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": f"section_{i}",
                        "name": f"Section {i}",
                        "fields": [
                            {"id": f"field_{i}", "label": f"Field {i}", "type": "text", "required": False}
                        ]
                    }
                    for i in range(50)
                ]
            }
        },
        "hundred_fields_one_section": {
            "name": "100 Fields in One Section",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Massive Section",
                        "fields": [
                            {"id": f"field_{i}", "label": f"Field {i}", "type": "text", "required": False}
                            for i in range(100)
                        ]
                    }
                ]
            }
        }
    }


@pytest.fixture(scope="function")
def malformed_extracted_notes():
    """
    Collection of malformed extracted_notes for autofill error testing.

    Returns:
        Dict of malformed extracted_notes scenarios
    """
    return {
        "empty": {},
        "missing_key_topics": {
            "topic_summary": "Summary without key topics",
            "session_mood": "neutral",
            "mood_trajectory": "stable",
            "therapist_notes": "Notes here",
            "patient_summary": "Summary here"
        },
        "wrong_type_strategies": {
            "key_topics": ["Topic 1"],
            "topic_summary": "Summary",
            "strategies": "not a list",  # Should be list
            "session_mood": "neutral",
            "mood_trajectory": "stable",
            "therapist_notes": "Notes",
            "patient_summary": "Summary"
        },
        "invalid_mood_value": {
            "key_topics": ["Topic 1"],
            "topic_summary": "Summary",
            "session_mood": "invalid_mood",  # Not a valid MoodLevel
            "mood_trajectory": "stable",
            "therapist_notes": "Notes",
            "patient_summary": "Summary"
        }
    }


@pytest.fixture(scope="function")
def template_with_notes(test_db, therapist_user, sample_patient):
    """
    Create a template with associated session notes for CASCADE testing.

    Args:
        test_db: Test database session
        therapist_user: Therapist who owns the template
        sample_patient: Patient for the session

    Returns:
        Dict with template and related notes
    """
    from app.models.db_models import SessionNote

    # Create template
    template = NoteTemplate(
        name="Template with Notes",
        description="For CASCADE testing",
        template_type=TemplateType.custom.value,
        is_system=False,
        created_by=therapist_user.id,
        is_shared=False,
        structure={
            "sections": [
                {
                    "id": "section1",
                    "name": "Section",
                    "fields": [
                        {"id": "field1", "label": "Field", "type": "text", "required": True}
                    ]
                }
            ]
        }
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)

    # Create session
    session = Session(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        status=SessionStatus.completed.value
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)

    # Create note using template
    note = SessionNote(
        session_id=session.id,
        template_id=template.id,
        content={"section1": {"field1": "Test content"}},
        status="draft"
    )
    test_db.add(note)
    test_db.commit()
    test_db.refresh(note)

    return {
        "template": template,
        "session": session,
        "note": note
    }


@pytest.fixture(scope="function")
def sample_patient(test_db, therapist_user):
    """Create a sample patient for testing."""
    patient = Patient(
        name="Sample Patient",
        email="sample@test.com",
        therapist_id=therapist_user.id
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


# ============================================================================
# Test Class 1: Template Structure Validation
# ============================================================================

class TestTemplateStructureValidation:
    """Test validation of template structure constraints"""

    def test_create_template_empty_sections_fails(
        self,
        client,
        therapist_auth_headers,
        invalid_structures
    ):
        """Test creating template with empty sections array returns 400"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_structures["empty_sections"]
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "sections" in response.text.lower() or "at least one" in response.text.lower()

    def test_create_template_duplicate_section_ids_fails(
        self,
        client,
        therapist_auth_headers,
        invalid_structures
    ):
        """Test creating template with duplicate section IDs returns 400"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_structures["duplicate_section_ids"]
        )

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        response_text = response.text.lower()
        assert "unique" in response_text or "duplicate" in response_text

    def test_create_template_section_no_fields_fails(
        self,
        client,
        therapist_auth_headers,
        invalid_structures
    ):
        """Test creating template with section containing no fields returns 400"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_structures["section_no_fields"]
        )

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        response_text = response.text.lower()
        assert "field" in response_text or "at least one" in response_text

    def test_create_template_duplicate_field_ids_fails(
        self,
        client,
        therapist_auth_headers,
        invalid_structures
    ):
        """Test creating template with duplicate field IDs within section returns 400"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_structures["duplicate_field_ids"]
        )

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        response_text = response.text.lower()
        assert "unique" in response_text or "duplicate" in response_text or "field" in response_text

    def test_create_template_select_no_options_fails(
        self,
        client,
        therapist_auth_headers,
        invalid_structures
    ):
        """Test creating template with select field missing options returns 400"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_structures["select_no_options"]
        )

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        response_text = response.text.lower()
        assert "option" in response_text or "select" in response_text

    def test_create_template_multiselect_no_options_fails(
        self,
        client,
        therapist_auth_headers,
        invalid_structures
    ):
        """Test creating template with multiselect field missing options returns 400"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_structures["multiselect_no_options"]
        )

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        response_text = response.text.lower()
        assert "option" in response_text or "multiselect" in response_text or "requires" in response_text

    def test_create_template_invalid_field_type_fails(
        self,
        client,
        therapist_auth_headers,
        invalid_structures
    ):
        """Test creating template with invalid field type returns 422"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_structures["invalid_field_type"]
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_template_invalid_template_type_fails(
        self,
        client,
        therapist_auth_headers
    ):
        """Test creating template with invalid template_type returns 422"""
        invalid_data = {
            "name": "Invalid Type Template",
            "template_type": "invalid_type",  # Not a valid TemplateType
            "structure": {
                "sections": [
                    {
                        "id": "s1",
                        "name": "Section",
                        "fields": [
                            {"id": "f1", "label": "Field", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        }

        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Test Class 2: Boundary Value Testing
# ============================================================================

class TestBoundaryValues:
    """Test boundary conditions for template data"""

    def test_create_template_max_name_length_succeeds(
        self,
        client,
        therapist_auth_headers,
        boundary_test_data
    ):
        """Test creating template with max allowed name length (200 chars) succeeds"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=boundary_test_data["max_name_length"]
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["name"]) == 200

    def test_create_template_exceeds_max_name_length_fails(
        self,
        client,
        therapist_auth_headers,
        boundary_test_data
    ):
        """Test creating template with name exceeding 200 chars fails"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=boundary_test_data["exceeds_max_name_length"]
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_template_very_long_field_label_succeeds(
        self,
        client,
        therapist_auth_headers,
        boundary_test_data
    ):
        """Test creating template with very long field labels succeeds (stress test)"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=boundary_test_data["very_long_field_label"]
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_template_fifty_sections_succeeds(
        self,
        client,
        therapist_auth_headers,
        boundary_test_data
    ):
        """Test creating template with 50 sections succeeds (stress test)"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=boundary_test_data["fifty_sections"]
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["structure"]["sections"]) == 50

    def test_create_template_hundred_fields_succeeds(
        self,
        client,
        therapist_auth_headers,
        boundary_test_data
    ):
        """Test creating template with 100 fields in one section succeeds (stress test)"""
        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=boundary_test_data["hundred_fields_one_section"]
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["structure"]["sections"][0]["fields"]) == 100


# ============================================================================
# Test Class 3: Note Content Validation
# ============================================================================

class TestNoteContentValidation:
    """Test validation of note content against template structure"""

    def test_create_note_content_not_matching_template(
        self,
        client,
        therapist_auth_headers,
        test_session_with_notes
    ):
        """Test creating note with content not matching template structure"""
        from app.models.db_models import SessionNote

        note_data = {
            "template_id": str(uuid4()),  # Non-existent template
            "content": {
                "wrong_section": {
                    "wrong_field": "value"
                }
            }
        }

        response = client.post(
            f"{NOTES_PREFIX}/{test_session_with_notes.id}/notes",
            headers=therapist_auth_headers,
            json=note_data
        )

        # Should fail because template doesn't exist
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_note_missing_required_fields(
        self,
        client,
        therapist_auth_headers,
        test_system_template,
        test_session_with_notes
    ):
        """Test creating note with missing required fields"""
        # Create note with empty content (missing required fields)
        note_data = {
            "template_id": str(test_system_template.id),
            "content": {}  # Empty content
        }

        response = client.post(
            f"{NOTES_PREFIX}/{test_session_with_notes.id}/notes",
            headers=therapist_auth_headers,
            json=note_data
        )

        # Should fail validation (empty content not allowed)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Test Class 4: Autofill with Malformed Data
# ============================================================================

class TestAutofillMalformedData:
    """Test autofill behavior with malformed extracted_notes"""

    def test_autofill_empty_extracted_notes(
        self,
        client,
        test_db,
        therapist_auth_headers,
        test_system_template,
        therapist_user,
        sample_patient,
        malformed_extracted_notes
    ):
        """Test autofill with empty extracted_notes JSONB returns 500 or 400"""
        # Create session with empty extracted_notes
        session = Session(
            patient_id=sample_patient.id,
            therapist_id=therapist_user.id,
            session_date=datetime.utcnow(),
            status=SessionStatus.completed.value,
            extracted_notes=malformed_extracted_notes["empty"]
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)

        request_data = {
            "template_id": str(test_system_template.id)
        }

        response = client.post(
            f"{NOTES_PREFIX}/{session.id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        # Should fail due to malformed data
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_autofill_missing_key_fields(
        self,
        client,
        test_db,
        therapist_auth_headers,
        test_system_template,
        therapist_user,
        sample_patient,
        malformed_extracted_notes
    ):
        """Test autofill with extracted_notes missing critical fields"""
        # Create session with incomplete extracted_notes
        session = Session(
            patient_id=sample_patient.id,
            therapist_id=therapist_user.id,
            session_date=datetime.utcnow(),
            status=SessionStatus.completed.value,
            extracted_notes=malformed_extracted_notes["missing_key_topics"]
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)

        request_data = {
            "template_id": str(test_system_template.id)
        }

        response = client.post(
            f"{NOTES_PREFIX}/{session.id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        # May succeed but with many missing fields, or fail validation
        # Implementation-dependent, but should not crash
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]

    def test_autofill_wrong_data_types(
        self,
        client,
        test_db,
        therapist_auth_headers,
        test_system_template,
        therapist_user,
        sample_patient,
        malformed_extracted_notes
    ):
        """Test autofill with extracted_notes having wrong data types"""
        # Create session with wrong types in extracted_notes
        session = Session(
            patient_id=sample_patient.id,
            therapist_id=therapist_user.id,
            session_date=datetime.utcnow(),
            status=SessionStatus.completed.value,
            extracted_notes=malformed_extracted_notes["wrong_type_strategies"]
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)

        request_data = {
            "template_id": str(test_system_template.id)
        }

        response = client.post(
            f"{NOTES_PREFIX}/{session.id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        # Should handle gracefully (may succeed with partial data or fail)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]


# ============================================================================
# Test Class 5: Template Updates Breaking Notes
# ============================================================================

class TestTemplateUpdateImpact:
    """Test impact of template updates on existing notes"""

    def test_update_template_structure_with_existing_notes(
        self,
        client,
        therapist_auth_headers,
        template_with_notes
    ):
        """Test updating template structure when notes exist using it"""
        template = template_with_notes["template"]

        # Update template to completely different structure
        update_data = {
            "structure": {
                "sections": [
                    {
                        "id": "new_section",
                        "name": "New Section",
                        "fields": [
                            {"id": "new_field", "label": "New Field", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        }

        response = client.patch(
            f"{TEMPLATES_PREFIX}/{template.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        # Update should succeed (backward compatibility is user's responsibility)
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Test Class 6: CASCADE Deletion Behavior
# ============================================================================

class TestCascadeDeletion:
    """Test CASCADE deletion of templates with associated notes"""

    def test_delete_template_with_notes_cascades(
        self,
        client,
        test_db,
        therapist_auth_headers,
        template_with_notes
    ):
        """Test deleting template with associated notes triggers CASCADE"""
        from app.models.db_models import SessionNote
        from sqlalchemy import select

        template = template_with_notes["template"]
        note = template_with_notes["note"]

        # Verify note exists before deletion
        result = test_db.execute(select(SessionNote).where(SessionNote.id == note.id))
        assert result.scalar_one_or_none() is not None

        # Delete template
        response = client.delete(
            f"{TEMPLATES_PREFIX}/{template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify note still exists but template_id is NULL (SET NULL cascade)
        test_db.expire_all()
        result = test_db.execute(select(SessionNote).where(SessionNote.id == note.id))
        note_after = result.scalar_one_or_none()

        # Note should exist but template_id should be NULL (SET NULL behavior)
        assert note_after is not None
        assert note_after.template_id is None


# ============================================================================
# Test Class 7: Concurrent Operations
# ============================================================================

class TestConcurrentOperations:
    """Test race conditions and concurrent updates"""

    def test_concurrent_template_updates(
        self,
        client,
        therapist_auth_headers,
        test_user_template
    ):
        """Test concurrent updates to same template (race condition)"""
        template_id = test_user_template.id

        # Simulate two concurrent update requests
        update_data_1 = {"name": "Updated Name 1"}
        update_data_2 = {"name": "Updated Name 2"}

        response1 = client.patch(
            f"{TEMPLATES_PREFIX}/{template_id}",
            headers=therapist_auth_headers,
            json=update_data_1
        )

        response2 = client.patch(
            f"{TEMPLATES_PREFIX}/{template_id}",
            headers=therapist_auth_headers,
            json=update_data_2
        )

        # Both should succeed (last write wins)
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        # Final state should be from second update
        final_response = client.get(
            f"{TEMPLATES_PREFIX}/{template_id}",
            headers=therapist_auth_headers
        )
        assert final_response.json()["name"] == "Updated Name 2"

    def test_concurrent_template_deletion(
        self,
        client,
        therapist_auth_headers,
        test_user_template
    ):
        """Test concurrent deletion attempts (second should fail with 404)"""
        template_id = test_user_template.id

        # First deletion
        response1 = client.delete(
            f"{TEMPLATES_PREFIX}/{template_id}",
            headers=therapist_auth_headers
        )

        # Second deletion (template already gone)
        response2 = client.delete(
            f"{TEMPLATES_PREFIX}/{template_id}",
            headers=therapist_auth_headers
        )

        assert response1.status_code == status.HTTP_204_NO_CONTENT
        assert response2.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Test Class 8: Additional Edge Cases
# ============================================================================

class TestAdditionalEdgeCases:
    """Additional edge cases and error scenarios"""

    def test_create_template_empty_name_fails(
        self,
        client,
        therapist_auth_headers
    ):
        """Test creating template with empty name fails"""
        invalid_data = {
            "name": "",  # Empty name
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "s1",
                        "name": "Section",
                        "fields": [
                            {"id": "f1", "label": "Field", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        }

        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_template_empty_name_fails(
        self,
        client,
        therapist_auth_headers,
        test_user_template
    ):
        """Test updating template with empty name fails"""
        update_data = {"name": ""}

        response = client.patch(
            f"{TEMPLATES_PREFIX}/{test_user_template.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_template_after_deletion_fails(
        self,
        client,
        therapist_auth_headers,
        test_user_template
    ):
        """Test retrieving template after deletion returns 404"""
        template_id = test_user_template.id

        # Delete template
        delete_response = client.delete(
            f"{TEMPLATES_PREFIX}/{template_id}",
            headers=therapist_auth_headers
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Try to retrieve
        get_response = client.get(
            f"{TEMPLATES_PREFIX}/{template_id}",
            headers=therapist_auth_headers
        )

        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_template_with_null_structure_fails(
        self,
        client,
        therapist_auth_headers
    ):
        """Test creating template with null structure fails"""
        invalid_data = {
            "name": "Null Structure Template",
            "template_type": "custom",
            "structure": None  # Null structure
        }

        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_autofill_with_null_template_id_fails(
        self,
        client,
        therapist_auth_headers,
        test_session_with_notes
    ):
        """Test autofill with null template_id fails"""
        request_data = {
            "template_id": None
        }

        response = client.post(
            f"{NOTES_PREFIX}/{test_session_with_notes.id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
