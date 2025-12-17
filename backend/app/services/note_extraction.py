"""
AI-powered note extraction from therapy session transcripts
"""
import json
import time
import logging
from typing import Dict, Optional
from openai import AsyncOpenAI, RateLimitError, APIError, APITimeoutError
from app.models.schemas import ExtractedNotes, TranscriptSegment
import os
from dotenv import load_dotenv
import httpx

# Configure logging
logger = logging.getLogger(__name__)

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

    def __init__(self, api_key: Optional[str] = None, timeout: Optional[float] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        # Configure timeout from environment or use default of 120 seconds
        self.default_timeout = timeout or float(os.getenv("OPENAI_TIMEOUT", "120"))

        # Create HTTP client with timeout configuration
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=30.0,  # Connection timeout
                read=self.default_timeout,  # Read timeout (most important for long API calls)
                write=30.0,  # Write timeout
                pool=10.0   # Pool timeout
            )
        )

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            http_client=http_client
        )
        self.model = "gpt-4o"  # Using GPT-4 for better reasoning

    async def extract_notes_from_transcript(
        self,
        transcript: str,
        segments: Optional[list[TranscriptSegment]] = None,
        timeout: Optional[float] = None
    ) -> ExtractedNotes:
        """
        Extract structured clinical notes from a therapy session transcript.

        Calls OpenAI GPT-4o API to analyze the transcript and produce structured
        clinical data including topics, strategies, risk flags, and summaries for
        both therapist and patient.

        Args:
            transcript: Full text of the therapy session
            segments: Optional list of timestamped segments from transcription
            timeout: Optional timeout in seconds for this specific API call.
                    If not provided, uses the default timeout configured at service initialization.

        Returns:
            ExtractedNotes: Pydantic model containing all structured clinical data

        Processing Details:
            - Temperature set to 0.3 for consistent, factual extraction
            - Uses JSON mode to enforce valid JSON output
            - Includes error handling for JSON parsing
            - Logs extraction metrics (duration, counts)
            - Default timeout: 120 seconds (configurable via OPENAI_TIMEOUT env var)

        Raises:
            ValueError: If OPENAI_API_KEY not in environment
            json.JSONDecodeError: If API response cannot be parsed as JSON
            APITimeoutError: If the API call exceeds the timeout duration
        """
        # Use method-specific timeout or fall back to default
        effective_timeout = timeout if timeout is not None else self.default_timeout

        logger.info(
            "Starting note extraction",
            extra={
                "transcript_length": len(transcript),
                "timeout_seconds": effective_timeout
            }
        )
        start_time = time.time()
        transcript_preview = transcript[:100] + "..." if len(transcript) > 100 else transcript

        # Call OpenAI API with comprehensive error handling
        try:
            response = await self.client.chat.completions.create(
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
                response_format={"type": "json_object"},  # Force JSON output
                timeout=effective_timeout  # Apply timeout to this specific request
            )
        except RateLimitError as e:
            logger.error(
                "Rate limit exceeded during note extraction",
                extra={
                    "transcript_length": len(transcript),
                    "error": str(e)
                }
            )
            raise ValueError(
                f"OpenAI rate limit exceeded. Please try again later. "
                f"(Transcript length: {len(transcript)} chars)"
            ) from e
        except APITimeoutError as e:
            elapsed = time.time() - start_time
            logger.error(
                "API timeout during note extraction",
                extra={
                    "transcript_length": len(transcript),
                    "timeout_seconds": effective_timeout,
                    "elapsed_seconds": round(elapsed, 2),
                    "error": str(e)
                }
            )
            raise ValueError(
                f"OpenAI API request timed out after {effective_timeout}s. "
                f"The transcript may be too long. (Transcript length: {len(transcript)} chars)"
            ) from e
        except APIError as e:
            logger.error(
                "OpenAI API error during note extraction",
                extra={
                    "status_code": getattr(e, 'status_code', 'unknown'),
                    "transcript_length": len(transcript),
                    "error": str(e)
                }
            )
            raise ValueError(
                f"OpenAI API error: {str(e)}. "
                f"Please check API status or try again later."
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error during OpenAI API call",
                extra={
                    "transcript_preview": transcript_preview,
                    "error_type": type(e).__name__,
                    "error": str(e)
                }
            )
            raise ValueError(
                f"Unexpected error during note extraction: {type(e).__name__}: {str(e)}"
            ) from e

        # Parse response with error handling
        response_text = response.choices[0].message.content

        # Handle potential markdown code blocks (shouldn't happen with json_object mode)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        # Parse JSON with error handling
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            response_preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
            logger.error(
                "JSON parsing failed for OpenAI response",
                extra={
                    "response_preview": response_preview,
                    "transcript_length": len(transcript),
                    "error": str(e),
                    "error_position": f"line {e.lineno}, column {e.colno}"
                }
            )
            raise ValueError(
                f"Failed to parse OpenAI response as JSON. "
                f"Response preview: '{response_preview}'. "
                f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
            ) from e

        # Create Pydantic model with validation error handling
        try:
            notes = ExtractedNotes(**extracted_data)
        except Exception as e:
            logger.error(
                "Pydantic validation failed for extracted data",
                extra={
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "data_keys": list(extracted_data.keys()) if isinstance(extracted_data, dict) else "not_a_dict"
                }
            )
            raise ValueError(
                f"Extracted data failed validation: {type(e).__name__}: {str(e)}"
            ) from e

        elapsed = time.time() - start_time
        logger.info(
            "Note extraction completed",
            extra={
                "duration_seconds": round(elapsed, 2),
                "topics_count": len(notes.key_topics),
                "strategies_count": len(notes.strategies),
                "action_items_count": len(notes.action_items),
                "risk_flags_count": len(notes.risk_flags)
            }
        )

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


def get_extraction_service() -> NoteExtractionService:
    """
    FastAPI dependency to provide the note extraction service.

    Creates a new NoteExtractionService instance for each request.
    The AsyncOpenAI client within the service handles connection pooling internally,
    so creating new instances is efficient and thread-safe.

    Returns:
        NoteExtractionService: New instance with OpenAI client initialized

    Raises:
        ValueError: If OPENAI_API_KEY not in environment

    Usage:
        In FastAPI routes, use: service = Depends(get_extraction_service)
    """
    return NoteExtractionService()
