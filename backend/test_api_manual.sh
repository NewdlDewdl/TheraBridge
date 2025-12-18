#!/bin/bash

# Manual API Testing Script for Feature 3 Templates & Notes
# Instance I5 - Wave 2 API Validation

set -e

BASE_URL="http://localhost:8000"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDlkZjEwNi01OWQ3LTQ3NDUtOWZiOS00NzYzM2YyMDNlMzYiLCJyb2xlIjoidGhlcmFwaXN0IiwiZXhwIjoxNzY2MDU4MzQ0LCJ0eXBlIjoiYWNjZXNzIn0.2jUTVHnf8h66dKLkzbptADlQuv8Ey-GsHVBMo8EaZXA"

RESULTS_DIR="/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/tests/results"
mkdir -p "$RESULTS_DIR"

echo "=========================================="
echo "Feature 3 Manual API Testing"
echo "=========================================="
echo ""

# Test 1: GET /api/v1/templates/ - List all templates
echo "TEST 1: GET /api/v1/templates/ - List all templates"
echo "Expected: 200 OK, 4 system templates"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  "$BASE_URL/api/v1/templates/" \
  -H "Authorization: Bearer $TOKEN" \
  > "$RESULTS_DIR/test1_list_templates.txt"
echo "Result saved to: $RESULTS_DIR/test1_list_templates.txt"
echo ""

# Test 2: GET /api/v1/templates/{id} - Get single template (use SOAP)
echo "TEST 2: GET /api/v1/templates/{id} - Get single template"
SOAP_ID="f7e8a1b2-c3d4-4e5f-9a8b-1c2d3e4f5a6b"
echo "Expected: 200 OK, complete SOAP template structure"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  "$BASE_URL/api/v1/templates/$SOAP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  > "$RESULTS_DIR/test2_get_template.txt"
echo "Result saved to: $RESULTS_DIR/test2_get_template.txt"
echo ""

# Test 3: GET /api/v1/templates/{id} - Invalid UUID
echo "TEST 3: GET /api/v1/templates/{id} - Invalid UUID"
echo "Expected: 422 Validation Error"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  "$BASE_URL/api/v1/templates/not-a-uuid" \
  -H "Authorization: Bearer $TOKEN" \
  > "$RESULTS_DIR/test3_invalid_uuid.txt"
echo "Result saved to: $RESULTS_DIR/test3_invalid_uuid.txt"
echo ""

# Test 4: GET /api/v1/templates/{id} - Non-existent UUID
echo "TEST 4: GET /api/v1/templates/{id} - Non-existent UUID"
echo "Expected: 404 Not Found"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  "$BASE_URL/api/v1/templates/00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer $TOKEN" \
  > "$RESULTS_DIR/test4_nonexistent_uuid.txt"
echo "Result saved to: $RESULTS_DIR/test4_nonexistent_uuid.txt"
echo ""

# Test 5: POST /api/v1/templates/ - Create custom template
echo "TEST 5: POST /api/v1/templates/ - Create custom template"
echo "Expected: 201 Created"
cat > /tmp/custom_template.json << 'EOF'
{
  "name": "Custom SOAP Template",
  "description": "My personalized SOAP template",
  "template_type": "soap",
  "is_shared": false,
  "sections": [
    {
      "section_id": "subjective",
      "title": "Subjective",
      "order_index": 0,
      "fields": [
        {
          "field_id": "chief_complaint",
          "label": "Chief Complaint",
          "field_type": "textarea",
          "is_required": true,
          "order_index": 0
        }
      ]
    },
    {
      "section_id": "objective",
      "title": "Objective",
      "order_index": 1,
      "fields": [
        {
          "field_id": "observations",
          "label": "Clinical Observations",
          "field_type": "textarea",
          "is_required": true,
          "order_index": 0
        }
      ]
    },
    {
      "section_id": "assessment",
      "title": "Assessment",
      "order_index": 2,
      "fields": [
        {
          "field_id": "diagnosis",
          "label": "Clinical Assessment",
          "field_type": "textarea",
          "is_required": true,
          "order_index": 0
        }
      ]
    },
    {
      "section_id": "plan",
      "title": "Plan",
      "order_index": 3,
      "fields": [
        {
          "field_id": "treatment_plan",
          "label": "Treatment Plan",
          "field_type": "textarea",
          "is_required": true,
          "order_index": 0
        }
      ]
    }
  ]
}
EOF

curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  -X POST "$BASE_URL/api/v1/templates/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/custom_template.json \
  > "$RESULTS_DIR/test5_create_template.txt"
echo "Result saved to: $RESULTS_DIR/test5_create_template.txt"

# Extract created template ID for later tests
CUSTOM_TEMPLATE_ID=$(grep -o '"id":"[^"]*"' "$RESULTS_DIR/test5_create_template.txt" | head -1 | cut -d'"' -f4)
echo "Created template ID: $CUSTOM_TEMPLATE_ID"
echo ""

# Test 6: POST /api/v1/templates/ - Create with empty sections (validation test)
echo "TEST 6: POST /api/v1/templates/ - Empty sections validation"
echo "Expected: 400 Bad Request"
cat > /tmp/invalid_template.json << 'EOF'
{
  "name": "Invalid Template",
  "description": "Template with no sections",
  "template_type": "soap",
  "is_shared": false,
  "sections": []
}
EOF

curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  -X POST "$BASE_URL/api/v1/templates/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/invalid_template.json \
  > "$RESULTS_DIR/test6_invalid_empty_sections.txt"
echo "Result saved to: $RESULTS_DIR/test6_invalid_empty_sections.txt"
echo ""

# Test 7: PATCH /api/v1/templates/{id} - Update custom template
echo "TEST 7: PATCH /api/v1/templates/{id} - Update custom template"
echo "Expected: 200 OK"
cat > /tmp/update_template.json << 'EOF'
{
  "name": "Updated Custom SOAP Template",
  "is_shared": true
}
EOF

curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  -X PATCH "$BASE_URL/api/v1/templates/$CUSTOM_TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/update_template.json \
  > "$RESULTS_DIR/test7_update_template.txt"
echo "Result saved to: $RESULTS_DIR/test7_update_template.txt"
echo ""

# Test 8: PATCH /api/v1/templates/{id} - Try to update system template
echo "TEST 8: PATCH /api/v1/templates/{id} - Update system template (should fail)"
echo "Expected: 403 Forbidden"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  -X PATCH "$BASE_URL/api/v1/templates/$SOAP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Modified SOAP"}' \
  > "$RESULTS_DIR/test8_update_system_template.txt"
echo "Result saved to: $RESULTS_DIR/test8_update_system_template.txt"
echo ""

# Test 9: GET /api/v1/templates/?template_type=soap - Filter by type
echo "TEST 9: GET /api/v1/templates/?template_type=soap - Filter by type"
echo "Expected: 200 OK, only SOAP templates"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  "$BASE_URL/api/v1/templates/?template_type=soap" \
  -H "Authorization: Bearer $TOKEN" \
  > "$RESULTS_DIR/test9_filter_by_type.txt"
echo "Result saved to: $RESULTS_DIR/test9_filter_by_type.txt"
echo ""

# Test 10: DELETE /api/v1/templates/{id} - Try to delete system template
echo "TEST 10: DELETE /api/v1/templates/{id} - Delete system template (should fail)"
echo "Expected: 403 Forbidden"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  -X DELETE "$BASE_URL/api/v1/templates/$SOAP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  > "$RESULTS_DIR/test10_delete_system_template.txt"
echo "Result saved to: $RESULTS_DIR/test10_delete_system_template.txt"
echo ""

# Test 11: DELETE /api/v1/templates/{id} - Delete custom template
echo "TEST 11: DELETE /api/v1/templates/{id} - Delete custom template"
echo "Expected: 200 OK"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  -X DELETE "$BASE_URL/api/v1/templates/$CUSTOM_TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  > "$RESULTS_DIR/test11_delete_custom_template.txt"
echo "Result saved to: $RESULTS_DIR/test11_delete_custom_template.txt"
echo ""

# Test 12: DELETE /api/v1/templates/{id} - Delete already deleted template
echo "TEST 12: DELETE /api/v1/templates/{id} - Delete non-existent template"
echo "Expected: 404 Not Found"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  -X DELETE "$BASE_URL/api/v1/templates/$CUSTOM_TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  > "$RESULTS_DIR/test12_delete_nonexistent.txt"
echo "Result saved to: $RESULTS_DIR/test12_delete_nonexistent.txt"
echo ""

echo "=========================================="
echo "Template Endpoint Tests Complete!"
echo "Now testing Notes Endpoints..."
echo "=========================================="
echo ""

# Check if there are any processed sessions
echo "Checking for processed sessions..."
curl -s "$BASE_URL/api/sessions/?status=processed" \
  -H "Authorization: Bearer $TOKEN" \
  > "$RESULTS_DIR/sessions_check.txt"

SESSION_COUNT=$(grep -o '"id":"[^"]*"' "$RESULTS_DIR/sessions_check.txt" | wc -l)
echo "Found $SESSION_COUNT processed sessions"
echo ""

if [ "$SESSION_COUNT" -gt 0 ]; then
  # Extract first session ID
  SESSION_ID=$(grep -o '"id":"[^"]*"' "$RESULTS_DIR/sessions_check.txt" | head -1 | cut -d'"' -f4)
  echo "Using session ID: $SESSION_ID"

  # Test 13: POST /api/v1/sessions/{id}/notes - Create note
  echo "TEST 13: POST /api/v1/sessions/{id}/notes - Create session note"
  echo "Expected: 201 Created"
  cat > /tmp/create_note.json << EOF
{
  "template_id": "$SOAP_ID",
  "content": {
    "subjective": "Patient reports feeling anxious about upcoming exam",
    "objective": "Patient appeared tense, fidgeting during session",
    "assessment": "Generalized anxiety disorder symptoms present",
    "plan": "Continue weekly CBT sessions, practice relaxation techniques"
  },
  "status": "draft"
}
EOF

  curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -X POST "$BASE_URL/api/v1/sessions/$SESSION_ID/notes" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @/tmp/create_note.json \
    > "$RESULTS_DIR/test13_create_note.txt"
  echo "Result saved to: $RESULTS_DIR/test13_create_note.txt"

  # Extract note ID
  NOTE_ID=$(grep -o '"id":"[^"]*"' "$RESULTS_DIR/test13_create_note.txt" | head -1 | cut -d'"' -f4)
  echo "Created note ID: $NOTE_ID"
  echo ""

  # Test 14: GET /api/v1/sessions/{id}/notes - List notes
  echo "TEST 14: GET /api/v1/sessions/{id}/notes - List session notes"
  echo "Expected: 200 OK"
  curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    "$BASE_URL/api/v1/sessions/$SESSION_ID/notes" \
    -H "Authorization: Bearer $TOKEN" \
    > "$RESULTS_DIR/test14_list_notes.txt"
  echo "Result saved to: $RESULTS_DIR/test14_list_notes.txt"
  echo ""

  # Test 15: PATCH /api/v1/notes/{id} - Update note
  echo "TEST 15: PATCH /api/v1/notes/{id} - Update note"
  echo "Expected: 200 OK"
  cat > /tmp/update_note.json << 'EOF'
{
  "content": {
    "subjective": "Patient reports significant improvement in anxiety levels",
    "objective": "Patient appeared relaxed and engaged",
    "assessment": "Positive response to CBT interventions",
    "plan": "Continue current treatment plan, reduce frequency to bi-weekly"
  },
  "status": "completed"
}
EOF

  curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -X PATCH "$BASE_URL/api/v1/notes/$NOTE_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @/tmp/update_note.json \
    > "$RESULTS_DIR/test15_update_note.txt"
  echo "Result saved to: $RESULTS_DIR/test15_update_note.txt"
  echo ""

  # Test 16: POST /api/v1/sessions/{id}/notes/autofill - Auto-fill template
  echo "TEST 16: POST /api/v1/sessions/{id}/notes/autofill - Auto-fill SOAP"
  echo "Expected: 200 OK (or 400 if no extracted_notes)"
  cat > /tmp/autofill_request.json << 'EOF'
{
  "template_type": "soap"
}
EOF

  curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -X POST "$BASE_URL/api/v1/sessions/$SESSION_ID/notes/autofill" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @/tmp/autofill_request.json \
    > "$RESULTS_DIR/test16_autofill_soap.txt"
  echo "Result saved to: $RESULTS_DIR/test16_autofill_soap.txt"
  echo ""

  # Test 17: POST /api/v1/sessions/{id}/notes/autofill - Auto-fill DAP
  echo "TEST 17: POST /api/v1/sessions/{id}/notes/autofill - Auto-fill DAP"
  echo "Expected: 200 OK (or 400 if no extracted_notes)"
  curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -X POST "$BASE_URL/api/v1/sessions/$SESSION_ID/notes/autofill" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"template_type":"dap"}' \
    > "$RESULTS_DIR/test17_autofill_dap.txt"
  echo "Result saved to: $RESULTS_DIR/test17_autofill_dap.txt"
  echo ""

  # Test 18: POST /api/v1/sessions/{id}/notes - Create with invalid template_id
  echo "TEST 18: POST /api/v1/sessions/{id}/notes - Invalid template_id"
  echo "Expected: 404 Not Found"
  curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -X POST "$BASE_URL/api/v1/sessions/$SESSION_ID/notes" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"template_id":"00000000-0000-0000-0000-000000000000","content":{},"status":"draft"}' \
    > "$RESULTS_DIR/test18_invalid_template_id.txt"
  echo "Result saved to: $RESULTS_DIR/test18_invalid_template_id.txt"
  echo ""
else
  echo "⚠️  No processed sessions found. Skipping notes tests."
  echo "Note: Full session processing requires audio upload + AI extraction"
  echo ""
fi

echo "=========================================="
echo "All Tests Complete!"
echo "=========================================="
echo ""
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Summary:"
echo "- Template endpoints: 12 tests"
if [ "$SESSION_COUNT" -gt 0 ]; then
  echo "- Notes endpoints: 6 tests"
  echo "Total: 18 API requests"
else
  echo "- Notes endpoints: SKIPPED (no processed sessions)"
  echo "Total: 12 API requests"
fi
echo ""
