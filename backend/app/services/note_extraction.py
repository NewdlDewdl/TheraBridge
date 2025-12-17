"""
AI-powered note extraction from therapy session transcripts
"""
import json
import time
from typing import Dict, Optional
from openai import OpenAI
from app.models.schemas import ExtractedNotes, TranscriptSegment
import os
from dotenv import load_dotenv

load_dotenv("../audio-transcription-pipeline/.env")


EXTRACTION_PROMPT = """You are an AI assistant helping extract structured clinical information from therapy session transcripts. Your role is to identify key therapeutic content while being accurate and not hallucinating information that isn't present.

Analyze the following therapy session transcript and extract:

1. **Key Topics** - Main subjects discussed (list of 3-7 items)
2. **Topic Summary** - 2-3 sentence overview of what the session covered
3. **Strategies/Techniques** - Any coping strategies, therapeutic techniques, or tools mentioned. For each, note:
   - Name of strategy
   - Category (breathing, cognitive, behavioral, mindfulness, interpersonal, etc.)
   - Status (MUST be lowercase: "introduced", "practiced", "assigned", or "reviewed")
   - Brief context
4. **Emotional Themes** - Dominant emotions expressed (anxiety, sadness, anger, hope, frustration, etc.)
5. **Triggers Identified** - Situations, people, or events that cause distress. Include:
   - The trigger
   - Context of how it was discussed
   - Severity if discernible (mild, moderate, severe)
6. **Action Items** - Homework or tasks assigned, things to try before next session
7. **Significant Quotes** - 2-3 direct quotes from the patient that capture important insights or breakthroughs
8. **Session Mood** - Overall emotional tone (MUST be lowercase: "very_low", "low", "neutral", "positive", or "very_positive")
9. **Mood Trajectory** - Did mood improve, decline, stay stable, or fluctuate during session? (MUST be lowercase: "improving", "declining", "stable", or "fluctuating")
10. **Follow-up Topics** - Issues that should be revisited in future sessions
11. **Unresolved Concerns** - Topics brought up but not fully addressed
12. **Risk Flags** - ANY mentions of self-harm, suicidal thoughts, harm to others, or crisis situations. Be vigilant but don't over-flag.

Also generate:
- **Therapist Summary** - A clinical summary (150-200 words) written for the therapist's records
- **Patient Summary** - A warm, supportive summary (100-150 words) written directly to the patient in second person ("You discussed...")

IMPORTANT:
- Only extract information that is actually present in the transcript
- Do not infer or assume information not explicitly stated
- If something is unclear, note the uncertainty
- Be especially careful with risk flags - only flag clear concerns
- Use exact quotes when possible for significant statements

Return your response as valid JSON matching this structure:
{{
  "key_topics": ["topic1", "topic2", ...],
  "topic_summary": "string",
  "strategies": [
    {{"name": "string", "category": "string", "status": "string", "context": "string"}}
  ],
  "emotional_themes": ["emotion1", "emotion2", ...],
  "triggers": [
    {{"trigger": "string", "context": "string", "severity": "string"}}
  ],
  "action_items": [
    {{"task": "string", "category": "string", "details": "string"}}
  ],
  "significant_quotes": [
    {{"quote": "string", "context": "string"}}
  ],
  "session_mood": "string",
  "mood_trajectory": "string",
  "follow_up_topics": ["topic1", ...],
  "unresolved_concerns": ["concern1", ...],
  "risk_flags": [
    {{"type": "string", "evidence": "string", "severity": "string"}}
  ],
  "therapist_notes": "string",
  "patient_summary": "string"
}}

TRANSCRIPT:
{transcript}
"""


class NoteExtractionService:
    """Service for extracting structured notes from transcripts using OpenAI"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Using GPT-4 for better reasoning

    async def extract_notes_from_transcript(
        self,
        transcript: str,
        segments: Optional[list[TranscriptSegment]] = None
    ) -> ExtractedNotes:
        """
        Extract structured clinical notes from a therapy session transcript.

        Calls OpenAI GPT-4o API to analyze the transcript and produce structured
        clinical data including topics, strategies, risk flags, and summaries for
        both therapist and patient.

        Args:
            transcript: Full text of the therapy session
            segments: Optional list of timestamped segments from transcription

        Returns:
            ExtractedNotes: Pydantic model containing all structured clinical data

        Processing Details:
            - Temperature set to 0.3 for consistent, factual extraction
            - Uses JSON mode to enforce valid JSON output
            - Includes error handling for JSON parsing
            - Logs extraction metrics (duration, counts)

        Raises:
            ValueError: If OPENAI_API_KEY not in environment
            json.JSONDecodeError: If API response cannot be parsed as JSON
        """
        print(f"[NoteExtraction] Starting extraction for {len(transcript)} character transcript")
        start_time = time.time()

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical psychology expert who extracts structured data from therapy transcripts. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(transcript=transcript)
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent extraction
            response_format={"type": "json_object"}  # Force JSON output
        )

        # Parse response
        response_text = response.choices[0].message.content

        # Handle potential markdown code blocks (shouldn't happen with json_object mode)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        # Parse JSON
        extracted_data = json.loads(response_text)

        # Create Pydantic model (this validates the structure)
        notes = ExtractedNotes(**extracted_data)

        elapsed = time.time() - start_time
        print(f"[NoteExtraction] Completed in {elapsed:.2f}s")
        print(f"  - Topics: {len(notes.key_topics)}")
        print(f"  - Strategies: {len(notes.strategies)}")
        print(f"  - Action items: {len(notes.action_items)}")
        print(f"  - Risk flags: {len(notes.risk_flags)}")

        return notes

    def estimate_cost(self, transcript: str) -> Dict[str, float]:
        """
        Estimate the API cost for extracting notes from a transcript.

        Uses rough token estimation based on character count (approximately 1 token
        per 4 characters) and GPT-4o pricing as of December 2024.

        Args:
            transcript: The transcript to estimate cost for

        Returns:
            Dict with estimated token counts and cost in USD:
                - estimated_input_tokens: Number of input tokens
                - estimated_output_tokens: Number of output tokens (typically 1500)
                - estimated_cost_usd: Total estimated cost

        Pricing Reference (Dec 2024):
            - Input: $2.50 per 1M tokens
            - Output: $10.00 per 1M tokens

        Note:
            Token estimation is approximate. Actual usage may vary.
        """
        # Rough token estimation
        prompt_tokens = len(EXTRACTION_PROMPT) / 4 + len(transcript) / 4
        output_tokens = 1500  # Estimated output size

        input_cost = (prompt_tokens / 1_000_000) * 2.50
        output_cost = (output_tokens / 1_000_000) * 10.00
        total_cost = input_cost + output_cost

        return {
            "estimated_input_tokens": int(prompt_tokens),
            "estimated_output_tokens": output_tokens,
            "estimated_cost_usd": round(total_cost, 4)
        }


# Singleton instance
_extraction_service: Optional[NoteExtractionService] = None


def get_extraction_service() -> NoteExtractionService:
    """
    Get or create the note extraction service singleton.

    Uses singleton pattern to reuse a single OpenAI client across the application,
    avoiding repeated initialization. The service is lazily instantiated on first use.

    Returns:
        NoteExtractionService: Singleton instance with OpenAI client initialized

    Raises:
        ValueError: If OPENAI_API_KEY not in environment (raised on first call)
    """
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = NoteExtractionService()
    return _extraction_service
