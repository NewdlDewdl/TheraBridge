#!/bin/bash
set -e

echo "🧪 Testing TherapyBridge Backend Pipeline"
echo "=========================================="

# 1. Health check
echo -e "\n✓ Testing health endpoint..."
curl -s http://localhost:8000/health | jq -e '.status == "healthy"' > /dev/null
echo "  Health check: PASSED"

# 2. Get patient ID
echo -e "\n✓ Getting patient ID..."
PATIENT_ID=$(curl -s http://localhost:8000/api/patients/ | jq -r '.[0].id')
echo "  Patient ID: $PATIENT_ID"

# 3. Upload audio
echo -e "\n✓ Uploading test audio..."
AUDIO_FILE="${1:-../audio-transcription-pipeline/tests/samples/onemintestvid.mp3}"
if [ ! -f "$AUDIO_FILE" ]; then
  echo "  ERROR: Audio file not found: $AUDIO_FILE"
  exit 1
fi

SESSION_ID=$(curl -s -X POST "http://localhost:8000/api/sessions/upload?patient_id=$PATIENT_ID" \
  -F "file=@$AUDIO_FILE" | jq -r '.id')
echo "  Session ID: $SESSION_ID"

# 4. Wait for processing
echo -e "\n✓ Waiting for processing to complete..."
MAX_WAIT=300  # 5 minutes
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
  STATUS=$(curl -s "http://localhost:8000/api/sessions/$SESSION_ID" | jq -r '.status')
  echo -n "  $(date '+%H:%M:%S') - Status: $STATUS"

  if [ "$STATUS" == "processed" ]; then
    echo " ✅"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo " ❌"
    curl -s "http://localhost:8000/api/sessions/$SESSION_ID" | jq '.error_message'
    exit 1
  else
    echo ""
  fi

  sleep 10
  ELAPSED=$((ELAPSED + 10))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
  echo "  ERROR: Processing timeout"
  exit 1
fi

# 5. Verify extracted notes
echo -e "\n✓ Verifying extracted notes..."
NOTES=$(curl -s "http://localhost:8000/api/sessions/$SESSION_ID/notes")
TOPICS=$(echo "$NOTES" | jq -r '.key_topics | length')
STRATEGIES=$(echo "$NOTES" | jq -r '.strategies | length')
ACTION_ITEMS=$(echo "$NOTES" | jq -r '.action_items | length')
MOOD=$(echo "$NOTES" | jq -r '.session_mood')

echo "  Topics extracted: $TOPICS"
echo "  Strategies extracted: $STRATEGIES"
echo "  Action items: $ACTION_ITEMS"
echo "  Session mood: $MOOD"

# 6. Display summary
echo -e "\n📊 EXTRACTION SUMMARY"
echo "===================="
echo "Topics: $(echo "$NOTES" | jq -r '.key_topics | join(", ")')"
echo ""
echo "Summary:"
echo "$(echo "$NOTES" | jq -r '.topic_summary')"
echo ""
echo "Mood: $MOOD ($(echo "$NOTES" | jq -r '.mood_trajectory'))"

echo -e "\n🎉 All tests PASSED!"
echo ""
echo "Session ID: $SESSION_ID"
echo "View full notes: curl http://localhost:8000/api/sessions/$SESSION_ID/notes | jq"
echo "View therapist summary: curl -s http://localhost:8000/api/sessions/$SESSION_ID/notes | jq -r '.therapist_notes'"
echo "View patient summary: curl -s http://localhost:8000/api/sessions/$SESSION_ID/notes | jq -r '.patient_summary'"
