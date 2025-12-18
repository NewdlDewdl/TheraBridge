"""
Authorization and access control tests for template and note endpoints.

Tests verify that:
- Therapists can create custom templates, patients cannot
- Only template owners can update/delete their templates
- System templates cannot be updated or deleted
- Shared templates can be viewed but not modified
- Therapists can create notes for assigned patients only
- Active therapist-patient relationships are enforced for note operations
- Inactive relationships don't grant access
- Role-based access control (therapist vs patient)
- Proper 403/401 error responses for unauthorized access
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import datetime, timedelta

from app.models.db_models import User, TherapistPatient, NoteTemplate, TherapySession, SessionNote
from app.models.schemas import UserRole
from app.auth.utils import get_password_hash


# ============================================================================
# Fixtures for Template & Note Authorization Tests
# ============================================================================

@pytest.fixture(scope="function")
def assigned_patient_user(test_db, therapist_user):
    """
    Create a patient user assigned to the therapist via active relationship.

    Args:
        test_db: Test database session
        therapist_user: Therapist user fixture

    Returns:
        User object with patient role assigned to therapist
    """
    patient = User(
        email="assigned_patient@test.com",
        hashed_password=get_password_hash("patientpass123"),
        first_name="Assigned",
        last_name="Patient",
        full_name="Assigned Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient.id,
        is_active=True,
        relationship_type="primary"
    )
    test_db.add(relationship)
    test_db.commit()

    return patient


@pytest.fixture(scope="function")
def assigned_patient_token(assigned_patient_user):
    """
    Generate access token for the assigned patient.

    Args:
        assigned_patient_user: Assigned patient user fixture

    Returns:
        JWT access token string
    """
    from app.auth.utils import create_access_token
    return create_access_token(assigned_patient_user.id, assigned_patient_user.role.value)


@pytest.fixture(scope="function")
def assigned_patient_auth_headers(assigned_patient_token):
    """
    Generate authorization headers for assigned patient.

    Args:
        assigned_patient_token: JWT token for assigned patient

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {assigned_patient_token}"}


@pytest.fixture(scope="function")
def other_therapist_user(test_db):
    """
    Create a different therapist user for testing access isolation.

    Args:
        test_db: Test database session

    Returns:
        User object with therapist role (different from therapist_user)
    """
    therapist = User(
        email="other_therapist@test.com",
        hashed_password=get_password_hash("otherpass123"),
        first_name="Other",
        last_name="Therapist",
        full_name="Other Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    test_db.add(therapist)
    test_db.commit()
    test_db.refresh(therapist)
    return therapist


@pytest.fixture(scope="function")
def other_therapist_token(other_therapist_user):
    """
    Generate access token for the other therapist.

    Args:
        other_therapist_user: Other therapist user fixture

    Returns:
        JWT access token string
    """
    from app.auth.utils import create_access_token
    return create_access_token(other_therapist_user.id, other_therapist_user.role.value)


@pytest.fixture(scope="function")
def other_therapist_auth_headers(other_therapist_token):
    """
    Generate authorization headers for other therapist.

    Args:
        other_therapist_token: JWT token for other therapist

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {other_therapist_token}"}


@pytest.fixture(scope="function")
def other_patient_user(test_db, other_therapist_user):
    """
    Create a patient assigned to other_therapist (not current therapist).

    Args:
        test_db: Test database session
        other_therapist_user: Other therapist user fixture

    Returns:
        User object with patient role assigned to other therapist
    """
    patient = User(
        email="other_patient@test.com",
        hashed_password=get_password_hash("otherpatient123"),
        first_name="Other",
        last_name="Patient",
        full_name="Other Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)

    # Create active relationship with other therapist
    relationship = TherapistPatient(
        therapist_id=other_therapist_user.id,
        patient_id=patient.id,
        is_active=True,
        relationship_type="primary"
    )
    test_db.add(relationship)
    test_db.commit()

    return patient


@pytest.fixture(scope="function")
def inactive_relationship_patient(test_db, therapist_user):
    """
    Create a patient with INACTIVE relationship to therapist.

    Args:
        test_db: Test database session
        therapist_user: Therapist user fixture

    Returns:
        User object with patient role and inactive relationship
    """
    patient = User(
        email="inactive_rel@test.com",
        hashed_password=get_password_hash("inactivepass123"),
        first_name="Inactive",
        last_name="Relationship",
        full_name="Inactive Relationship",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)

    # Create INACTIVE therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient.id,
        is_active=False,  # Relationship exists but is inactive
        relationship_type="primary",
        ended_at=datetime.utcnow() - timedelta(days=30)
    )
    test_db.add(relationship)
    test_db.commit()

    return patient


@pytest.fixture(scope="function")
def therapist_custom_template(test_db, therapist_user):
    """
    Create a custom template owned by therapist_user.

    Args:
        test_db: Test database session
        therapist_user: Therapist user fixture

    Returns:
        NoteTemplate object owned by therapist
    """
    template = NoteTemplate(
        name="Therapist's Custom SOAP",
        description="My personal SOAP template",
        template_type="soap",
        is_system=False,
        created_by=therapist_user.id,
        is_shared=False,
        structure={
            "sections": [
                {
                    "id": "subjective",
                    "name": "Subjective",
                    "description": "Patient's reported experience",
                    "order": 1,
                    "fields": [
                        {
                            "id": "mood",
                            "label": "Mood",
                            "type": "text",
                            "required": True,
                            "order": 1
                        }
                    ]
                }
            ]
        }
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


@pytest.fixture(scope="function")
def other_therapist_template(test_db, other_therapist_user):
    """
    Create a custom template owned by other_therapist_user.

    Args:
        test_db: Test database session
        other_therapist_user: Other therapist user fixture

    Returns:
        NoteTemplate object owned by other therapist
    """
    template = NoteTemplate(
        name="Other Therapist's Custom DAP",
        description="Another therapist's DAP template",
        template_type="dap",
        is_system=False,
        created_by=other_therapist_user.id,
        is_shared=False,
        structure={
            "sections": [
                {
                    "id": "data",
                    "name": "Data",
                    "description": "Observable data",
                    "order": 1,
                    "fields": [
                        {
                            "id": "observations",
                            "label": "Observations",
                            "type": "textarea",
                            "required": True,
                            "order": 1
                        }
                    ]
                }
            ]
        }
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


@pytest.fixture(scope="function")
def shared_template(test_db, other_therapist_user):
    """
    Create a shared template owned by other_therapist_user.

    Args:
        test_db: Test database session
        other_therapist_user: Other therapist user fixture

    Returns:
        NoteTemplate object that is shared
    """
    template = NoteTemplate(
        name="Shared BIRP Template",
        description="Shared template available to all",
        template_type="birp",
        is_system=False,
        created_by=other_therapist_user.id,
        is_shared=True,
        structure={
            "sections": [
                {
                    "id": "behavior",
                    "name": "Behavior",
                    "description": "Client behavior",
                    "order": 1,
                    "fields": [
                        {
                            "id": "observations",
                            "label": "Observations",
                            "type": "textarea",
                            "required": True,
                            "order": 1
                        }
                    ]
                }
            ]
        }
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


@pytest.fixture(scope="function")
def system_template(test_db):
    """
    Create a system template (available to all, unmodifiable).

    Args:
        test_db: Test database session

    Returns:
        NoteTemplate object that is a system template
    """
    template = NoteTemplate(
        name="System SOAP Template",
        description="Default system SOAP template",
        template_type="soap",
        is_system=True,
        created_by=None,
        is_shared=False,
        structure={
            "sections": [
                {
                    "id": "subjective",
                    "name": "Subjective",
                    "description": "Patient's reported experience",
                    "order": 1,
                    "fields": [
                        {
                            "id": "chief_complaint",
                            "label": "Chief Complaint",
                            "type": "textarea",
                            "required": True,
                            "order": 1
                        }
                    ]
                }
            ]
        }
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


@pytest.fixture(scope="function")
def assigned_patient_session(test_db, therapist_user, assigned_patient_user):
    """
    Create a therapy session for assigned patient.

    Args:
        test_db: Test database session
        therapist_user: Therapist user fixture
        assigned_patient_user: Patient assigned to therapist

    Returns:
        TherapySession object for assigned patient
    """
    session = TherapySession(
        patient_id=assigned_patient_user.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        status="completed",
        transcript_text="Patient discussed anxiety management strategies.",
        extracted_notes={
            "chief_complaint": "Anxiety symptoms",
            "session_summary": "Discussed coping strategies",
            "mood_affect": "anxious"
        }
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


@pytest.fixture(scope="function")
def other_patient_session(test_db, other_therapist_user, other_patient_user):
    """
    Create a therapy session for other patient (not assigned to current therapist).

    Args:
        test_db: Test database session
        other_therapist_user: Other therapist user fixture
        other_patient_user: Patient assigned to other therapist

    Returns:
        TherapySession object for other patient
    """
    session = TherapySession(
        patient_id=other_patient_user.id,
        therapist_id=other_therapist_user.id,
        session_date=datetime.utcnow(),
        status="completed",
        transcript_text="Other therapist's session.",
        extracted_notes={
            "chief_complaint": "Depression",
            "session_summary": "Behavioral activation",
            "mood_affect": "flat"
        }
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


# ============================================================================
# Test: POST /api/v1/templates - Create Template
# ============================================================================

@pytest.mark.templates
class TestCreateTemplateAuthorization:
    """Test authorization for template creation"""

    def test_therapist_can_create_custom_template(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers
    ):
        """Test therapist can create custom templates"""
        test_db.commit()

        template_data = {
            "name": "My Custom Template",
            "description": "A custom template for my practice",
            "template_type": "soap",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "subjective",
                        "name": "Subjective",
                        "description": "Patient's report",
                        "order": 1,
                        "fields": [
                            {
                                "id": "mood",
                                "label": "Mood",
                                "type": "text",
                                "required": True,
                                "order": 1
                            }
                        ]
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            headers=therapist_auth_headers,
            json=template_data
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "My Custom Template"
        assert data["is_system"] is False


    def test_patient_cannot_create_template(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers
    ):
        """Test patient role cannot create templates (therapist only)"""
        test_db.commit()

        template_data = {
            "name": "Patient Template (should fail)",
            "description": "Not allowed",
            "template_type": "soap",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "subjective",
                        "name": "Subjective",
                        "description": "Test",
                        "order": 1,
                        "fields": [
                            {
                                "id": "test",
                                "label": "Test",
                                "type": "text",
                                "required": True,
                                "order": 1
                            }
                        ]
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            headers=assigned_patient_auth_headers,
            json=template_data
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: PATCH /api/v1/templates/{template_id} - Update Template
# ============================================================================

@pytest.mark.templates
class TestUpdateTemplateAuthorization:
    """Test authorization for template updates"""

    def test_therapist_can_update_own_template(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_custom_template
    ):
        """Test therapist can update their own template"""
        test_db.commit()

        update_data = {
            "name": "Updated Template Name",
            "is_shared": True
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{therapist_custom_template.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Template Name"
        assert data["is_shared"] is True


    def test_therapist_cannot_update_other_therapist_template(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_therapist_template
    ):
        """Test therapist cannot update another therapist's template"""
        test_db.commit()

        update_data = {
            "name": "Unauthorized Update"
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{other_therapist_template.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        # Should return 403 Forbidden (not the owner)
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_user_cannot_update_system_template(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        system_template
    ):
        """Test users cannot update system templates"""
        test_db.commit()

        update_data = {
            "name": "Modified System Template"
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{system_template.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        # Should return 403 Forbidden (system templates are read-only)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: DELETE /api/v1/templates/{template_id} - Delete Template
# ============================================================================

@pytest.mark.templates
class TestDeleteTemplateAuthorization:
    """Test authorization for template deletion"""

    def test_therapist_can_delete_own_template(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_custom_template
    ):
        """Test therapist can delete their own template"""
        test_db.commit()

        response = async_db_client.delete(
            f"/api/v1/templates/{therapist_custom_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "deleted successfully" in data["message"].lower()


    def test_therapist_cannot_delete_other_therapist_template(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_therapist_template
    ):
        """Test therapist cannot delete another therapist's template"""
        test_db.commit()

        response = async_db_client.delete(
            f"/api/v1/templates/{other_therapist_template.id}",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden (not the owner)
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_user_cannot_delete_system_template(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        system_template
    ):
        """Test users cannot delete system templates"""
        test_db.commit()

        response = async_db_client.delete(
            f"/api/v1/templates/{system_template.id}",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden (system templates cannot be deleted)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: GET /api/v1/templates - List Templates
# ============================================================================

@pytest.mark.templates
class TestListTemplatesAuthorization:
    """Test authorization for template listing"""

    def test_user_can_view_system_templates(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        system_template
    ):
        """Test authenticated users can view system templates"""
        test_db.commit()

        response = async_db_client.get(
            "/api/v1/templates",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert any(t["id"] == str(system_template.id) for t in data)


    def test_user_can_view_own_templates(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_custom_template
    ):
        """Test user can view their own templates"""
        test_db.commit()

        response = async_db_client.get(
            "/api/v1/templates",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(t["id"] == str(therapist_custom_template.id) for t in data)


    def test_user_can_view_shared_templates(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        shared_template
    ):
        """Test user can view shared templates from other users"""
        test_db.commit()

        response = async_db_client.get(
            "/api/v1/templates?include_shared=true",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(t["id"] == str(shared_template.id) for t in data)


    def test_user_cannot_see_unshared_templates_from_others(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_therapist_template
    ):
        """Test user cannot see unshared templates from other users"""
        test_db.commit()

        response = async_db_client.get(
            "/api/v1/templates",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should NOT include other therapist's private template
        assert not any(t["id"] == str(other_therapist_template.id) for t in data)


# ============================================================================
# Test: GET /api/v1/templates/{template_id} - Get Template
# ============================================================================

@pytest.mark.templates
class TestGetTemplateAuthorization:
    """Test authorization for viewing individual templates"""

    def test_user_can_view_system_template(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        system_template
    ):
        """Test authenticated users can view system templates"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/templates/{system_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(system_template.id)


    def test_user_can_view_shared_template(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        shared_template
    ):
        """Test user can view shared templates"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/templates/{shared_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(shared_template.id)


    def test_user_cannot_view_unshared_template_from_other_user(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_therapist_template
    ):
        """Test user cannot view unshared templates from other users"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/templates/{other_therapist_template.id}",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden (template is not shared)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: POST /api/v1/sessions/{session_id}/notes - Create Note
# ============================================================================

@pytest.mark.notes
class TestCreateNoteAuthorization:
    """Test authorization for creating session notes"""

    def test_therapist_can_create_note_for_assigned_patient(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_session,
        therapist_custom_template
    ):
        """Test therapist can create note for assigned patient's session"""
        test_db.commit()

        note_data = {
            "template_id": str(therapist_custom_template.id),
            "content": {
                "subjective": {"mood": "anxious"}
            }
        }

        response = async_db_client.post(
            f"/api/v1/sessions/{assigned_patient_session.id}/notes",
            headers=therapist_auth_headers,
            json=note_data
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["session_id"] == str(assigned_patient_session.id)


    def test_therapist_cannot_create_note_for_unassigned_patient(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_session,
        therapist_custom_template
    ):
        """Test therapist cannot create note for unassigned patient's session"""
        test_db.commit()

        note_data = {
            "template_id": str(therapist_custom_template.id),
            "content": {
                "subjective": {"mood": "anxious"}
            }
        }

        response = async_db_client.post(
            f"/api/v1/sessions/{other_patient_session.id}/notes",
            headers=therapist_auth_headers,
            json=note_data
        )

        # Should return 403 Forbidden (not assigned to this patient)
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_therapist_cannot_create_note_with_inactive_relationship(
        self,
        async_db_client,
        test_db,
        therapist_user,
        therapist_auth_headers,
        inactive_relationship_patient,
        therapist_custom_template
    ):
        """Test inactive relationship blocks note creation"""
        # Create session for patient with inactive relationship
        session = TherapySession(
            patient_id=inactive_relationship_patient.id,
            therapist_id=therapist_user.id,
            session_date=datetime.utcnow(),
            status="completed",
            transcript_text="Old session from inactive relationship"
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)

        note_data = {
            "template_id": str(therapist_custom_template.id),
            "content": {
                "subjective": {"mood": "neutral"}
            }
        }

        response = async_db_client.post(
            f"/api/v1/sessions/{session.id}/notes",
            headers=therapist_auth_headers,
            json=note_data
        )

        # Should return 403 Forbidden (relationship is inactive)
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_patient_cannot_create_notes(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        assigned_patient_session,
        therapist_custom_template
    ):
        """Test patient role cannot create notes (therapist only)"""
        test_db.commit()

        note_data = {
            "template_id": str(therapist_custom_template.id),
            "content": {
                "subjective": {"mood": "good"}
            }
        }

        response = async_db_client.post(
            f"/api/v1/sessions/{assigned_patient_session.id}/notes",
            headers=assigned_patient_auth_headers,
            json=note_data
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: POST /api/v1/sessions/{session_id}/notes/autofill - Autofill Template
# ============================================================================

@pytest.mark.notes
class TestAutofillTemplateAuthorization:
    """Test authorization for template autofill"""

    def test_therapist_can_autofill_for_assigned_patient(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_session
    ):
        """Test therapist can autofill template for assigned patient's session"""
        test_db.commit()

        autofill_request = {
            "template_type": "soap"
        }

        response = async_db_client.post(
            f"/api/v1/sessions/{assigned_patient_session.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=autofill_request
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["template_type"] == "soap"
        assert "auto_filled_content" in data


    def test_therapist_cannot_autofill_for_unassigned_patient(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_session
    ):
        """Test therapist cannot autofill for unassigned patient's session"""
        test_db.commit()

        autofill_request = {
            "template_type": "soap"
        }

        response = async_db_client.post(
            f"/api/v1/sessions/{other_patient_session.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=autofill_request
        )

        # Should return 403 Forbidden (not assigned to this patient)
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_patient_cannot_autofill_templates(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        assigned_patient_session
    ):
        """Test patient role cannot autofill templates (therapist only)"""
        test_db.commit()

        autofill_request = {
            "template_type": "soap"
        }

        response = async_db_client.post(
            f"/api/v1/sessions/{assigned_patient_session.id}/notes/autofill",
            headers=assigned_patient_auth_headers,
            json=autofill_request
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: GET /api/v1/sessions/{session_id}/notes - List Notes
# ============================================================================

@pytest.mark.notes
class TestListNotesAuthorization:
    """Test authorization for listing session notes"""

    def test_therapist_can_list_notes_for_assigned_patient_session(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_session,
        therapist_custom_template
    ):
        """Test therapist can list notes for assigned patient's session"""
        # Create a note first
        note = SessionNote(
            session_id=assigned_patient_session.id,
            template_id=therapist_custom_template.id,
            content={"subjective": {"mood": "anxious"}},
            status="draft"
        )
        test_db.add(note)
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/sessions/{assigned_patient_session.id}/notes",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


    def test_therapist_cannot_list_notes_for_unassigned_patient_session(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_session
    ):
        """Test therapist cannot list notes for unassigned patient's session"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/sessions/{other_patient_session.id}/notes",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden (not assigned to this patient)
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_patient_cannot_list_notes(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        assigned_patient_session
    ):
        """Test patient role cannot list notes (therapist only)"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/sessions/{assigned_patient_session.id}/notes",
            headers=assigned_patient_auth_headers
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: PATCH /api/v1/notes/{note_id} - Update Note
# ============================================================================

@pytest.mark.notes
class TestUpdateNoteAuthorization:
    """Test authorization for updating session notes"""

    def test_therapist_can_update_note_for_assigned_patient_session(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_session,
        therapist_custom_template
    ):
        """Test therapist can update note for assigned patient's session"""
        # Create a note first
        note = SessionNote(
            session_id=assigned_patient_session.id,
            template_id=therapist_custom_template.id,
            content={"subjective": {"mood": "anxious"}},
            status="draft"
        )
        test_db.add(note)
        test_db.commit()
        test_db.refresh(note)

        update_data = {
            "content": {"subjective": {"mood": "calm"}},
            "status": "finalized"
        }

        response = async_db_client.patch(
            f"/api/v1/notes/{note.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "finalized"


    def test_therapist_cannot_update_note_from_different_therapist_session(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_session,
        other_therapist_template
    ):
        """Test therapist cannot update note from another therapist's session"""
        # Create note for other therapist's session
        note = SessionNote(
            session_id=other_patient_session.id,
            template_id=other_therapist_template.id,
            content={"data": {"observations": "test"}},
            status="draft"
        )
        test_db.add(note)
        test_db.commit()
        test_db.refresh(note)

        update_data = {
            "status": "finalized"
        }

        response = async_db_client.patch(
            f"/api/v1/notes/{note.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        # Should return 403 Forbidden (not assigned to this patient)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: Unauthenticated Access
# ============================================================================

@pytest.mark.templates
@pytest.mark.notes
class TestUnauthenticatedAccess:
    """Test that unauthenticated requests are properly rejected"""

    def test_unauthenticated_template_requests_fail(
        self,
        async_db_client,
        test_db,
        system_template
    ):
        """Test template endpoints reject unauthenticated requests"""
        test_db.commit()

        endpoints = [
            ("GET", "/api/v1/templates"),
            ("GET", f"/api/v1/templates/{system_template.id}"),
            ("POST", "/api/v1/templates", {"name": "test", "template_type": "soap", "structure": {"sections": []}}),
        ]

        for method, endpoint, *payload in endpoints:
            if method == "POST":
                response = async_db_client.post(endpoint, json=payload[0] if payload else None)
            else:
                response = async_db_client.get(endpoint)

            # Should return 401 Unauthorized or 403 Forbidden
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ], f"Endpoint {method} {endpoint} should reject unauthenticated request"


    def test_unauthenticated_note_requests_fail(
        self,
        async_db_client,
        test_db,
        assigned_patient_session
    ):
        """Test note endpoints reject unauthenticated requests"""
        test_db.commit()

        endpoints = [
            ("GET", f"/api/v1/sessions/{assigned_patient_session.id}/notes"),
            ("POST", f"/api/v1/sessions/{assigned_patient_session.id}/notes", {"content": {}}),
            ("POST", f"/api/v1/sessions/{assigned_patient_session.id}/notes/autofill", {"template_type": "soap"}),
        ]

        for method, endpoint, *payload in endpoints:
            if method == "POST":
                response = async_db_client.post(endpoint, json=payload[0] if payload else None)
            else:
                response = async_db_client.get(endpoint)

            # Should return 401 Unauthorized or 403 Forbidden
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ], f"Endpoint {method} {endpoint} should reject unauthenticated request"
