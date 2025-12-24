# Fix Wave 2 Deep Analysis with Cumulative Context - Implementation Plan

## Overview

Fix the Wave 2 (Deep Analysis) async/await bug and implement cumulative context chaining so each session's deep analysis uses progressively richer context from previous sessions' Wave 1 and Wave 2 results.

## Current State Analysis

**What Works:**
- ✅ Wave 1 algorithms (Mood, Topics, Breakthrough) execute successfully on all sessions
- ✅ Model assignments are optimal: gpt-5-nano (mood), gpt-5-mini (topics), gpt-5 (breakthrough), gpt-5.2 (deep)
- ✅ System prompts are generally appropriate for their model tiers
- ✅ Test script successfully loads sessions and runs Wave 1

**What's Broken:**
- ❌ Wave 2 fails with `'coroutine' object is not an iterator` error
- ❌ Deep analysis doesn't receive cumulative context from previous sessions
- ❌ No context blob structure for progressive enrichment
- ❌ System prompt doesn't explain cumulative context structure

**Root Causes:**
1. `deep_analyzer.py:135` - `self.db = db` can be None, but async helper functions expect it
2. `test_full_pipeline_demo.py` - Mocks previous sessions but doesn't create cumulative context
3. No mechanism to pass Wave 2 results as context to next session

## Desired End State

**Session 10**: Runs with NO cumulative context (first session)
- Wave 1: Mood, Topics, Breakthrough
- Wave 2: Deep analysis using only current session data
- Output: Wave 1 + Wave 2 results

**Session 11**: Runs with Session 10 as cumulative context
- Cumulative context blob contains:
  - `session_10_wave1`: All Wave 1 fields
  - `session_10_wave2`: All Wave 2 fields (complete `DeepAnalysis` object)
- Wave 2: Deep analysis using cumulative context + current Wave 1
- Output: Wave 1 + Wave 2 results

**Session 12**: Runs with Sessions 10-11 as nested cumulative context
- Cumulative context blob contains:
  - `previous_context`: The context blob Session 11 used (contains Session 10)
  - `session_11_wave1`: All Wave 1 fields
  - `session_11_wave2`: All Wave 2 fields
- Wave 2: Deep analysis using nested cumulative context + current Wave 1
- Output: Wave 1 + Wave 2 results

**Verification:**
- Run `python tests/test_full_pipeline_demo.py` successfully
- JSON output shows all 3 sessions with complete Wave 2 results
- Deep analysis for Session 11 references Session 10 data
- Deep analysis for Session 12 references both 10 and 11

## What We're NOT Doing

- Not modifying Wave 1 algorithms (they work perfectly)
- Not changing the production orchestrator (`analysis_orchestrator.py`)
- Not persisting cumulative context to database (demo only)
- Not rewriting the entire deep analyzer (surgical fixes only)
- Not changing model assignments (they're optimal)

## Implementation Approach

1. **Fix async/await bug** in `deep_analyzer.py` helper functions
2. **Add cumulative context parameter** to `analyze_session()` method
3. **Update system prompt** to explain cumulative context structure
4. **Modify test script** to build and pass cumulative context between sessions
5. **Verify model system prompts** match their model capabilities

---

## Phase 1: Fix Async/Await Bug in Deep Analyzer

### Overview
Fix the production `deep_analyzer.py` to properly handle None database and async context queries.

### Changes Required:

#### 1.1 Fix Database Helper Functions

**File**: `backend/app/services/deep_analyzer.py`
**Changes**: Make helper functions handle None database gracefully

```python
# Lines 508-524 - _get_previous_sessions
async def _get_previous_sessions(
    self,
    patient_id: str,
    current_session_id: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Get previous sessions for the patient."""
    if self.db is None:
        return []  # No DB available (testing/mocking)

    response = (
        self.db.table("therapy_sessions")
        .select("id, session_date, mood_score, topics, technique, summary")
        .eq("patient_id", patient_id)
        .neq("id", current_session_id)
        .order("session_date", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data if response.data else []
```

Apply same pattern to:
- `_get_mood_trend()` (lines 526-539)
- `_get_recurring_topics()` (lines 541-555)
- `_get_technique_history()` (lines 557-571)
- `_get_breakthrough_history()` (lines 573-601)

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile app/services/deep_analyzer.py`
- [x] No import errors: `python -c "from app.services.deep_analyzer import DeepAnalyzer"`
- [x] Can instantiate with None DB: `python -c "from app.services.deep_analyzer import DeepAnalyzer; DeepAnalyzer(db=None)"` (requires API key but import works)

#### Manual Verification:
- [x] Review each helper function has None check
- [x] Verify return types match (empty list/dict when DB is None)

**Implementation Note**: Complete this phase before proceeding to Phase 2.

---

## Phase 2: Add Cumulative Context Support

### Overview
Modify `deep_analyzer.py` to accept and use cumulative context from previous sessions.

### Changes Required:

#### 2.1 Update analyze_session Signature

**File**: `backend/app/services/deep_analyzer.py`
**Changes**: Add optional cumulative_context parameter

```python
# Lines 137-141
async def analyze_session(
    self,
    session_id: str,
    session: Dict[str, Any],
    cumulative_context: Optional[Dict[str, Any]] = None  # NEW
) -> DeepAnalysis:
    """
    Perform deep clinical analysis on a therapy session.

    Args:
        session_id: Unique identifier for the session
        session: Session data with transcript and Wave 1 analysis results
        cumulative_context: Nested context from previous sessions (Wave 1 + Wave 2)
                           Structure:
                           {
                               "previous_context": {...},  # Context from N-2, N-3, etc.
                               "session_N_wave1": {...},   # Previous session Wave 1
                               "session_N_wave2": {...}    # Previous session Wave 2
                           }

    Returns:
        DeepAnalysis with comprehensive insights
    """
```

#### 2.2 Pass Cumulative Context to Prompt Builder

**File**: `backend/app/services/deep_analyzer.py`
**Changes**: Modify `_build_analysis_context` to include cumulative context

```python
# Lines 308-365 - _build_analysis_context
async def _build_analysis_context(
    self,
    session_id: str,
    session: Dict[str, Any],
    cumulative_context: Optional[Dict[str, Any]] = None  # NEW
) -> Dict[str, Any]:
    """
    Build comprehensive context for deep analysis.

    Args:
        session_id: Session UUID
        session: Current session data
        cumulative_context: Nested context from previous sessions

    Returns:
        Dictionary with all necessary context
    """
    patient_id = session["patient_id"]

    # Get patient history (last 5 sessions) - only if DB available
    previous_sessions = await self._get_previous_sessions(patient_id, current_session_id=session_id, limit=5)

    # ... (existing code for mood_trend, recurring_topics, etc.)

    return {
        "current_session": {
            # ... (existing current session data)
        },
        "patient_history": {
            # ... (existing patient history)
        },
        "cumulative_context": cumulative_context  # NEW: Add cumulative context
    }
```

Pass cumulative context down:

```python
# Lines 152-155
# Gather all context
context = await self._build_analysis_context(session_id, session, cumulative_context)
```

#### 2.3 Update System Prompt to Explain Cumulative Context

**File**: `backend/app/services/deep_analyzer.py`
**Changes**: Add cumulative context explanation to system prompt

```python
# Lines 191-306 - _get_system_prompt
def _get_system_prompt(self) -> str:
    """System prompt defining the AI's role and instructions."""
    return """You are an expert clinical psychologist running on GPT-5.2, analyzing therapy sessions to provide
patient-facing insights. Your goal is to help the patient understand their progress, strengths,
and areas for growth in a compassionate, empowering way.

**YOUR CAPABILITIES (GPT-5.2):**
- You have advanced synthesis and reasoning capabilities
- You excel at integrating complex longitudinal data across multiple sessions
- You can identify subtle patterns and generate deep therapeutic insights
- You have a 400K token context window for comprehensive analysis

You have access to:
1. Full session transcript with speaker roles (Therapist/Client)
2. AI-extracted mood score, topics, action items, and therapeutic technique
3. Breakthrough moments detected during the session
4. Patient's therapy history (previous sessions, mood trends, recurring themes)
5. **CUMULATIVE CONTEXT** from previous sessions (see below)

**CUMULATIVE CONTEXT STRUCTURE:**

The cumulative context contains nested data from previous sessions. It grows progressively:

**Session 1 (First Session):**
- No cumulative context (this is the patient's first analyzed session)

**Session 2:**
```json
{
  "session_1_wave1": {
    "mood_score": 5.5,
    "topics": ["Depression", "Medication"],
    "technique": "Cognitive Restructuring",
    "summary": "...",
    "has_breakthrough": false
  },
  "session_1_wave2": {
    "progress_indicators": {...},
    "therapeutic_insights": {...},
    "coping_skills": {...},
    "therapeutic_relationship": {...},
    "recommendations": {...}
  }
}
```

**Session 3:**
```json
{
  "previous_context": {
    // The cumulative context from Session 2 (which contains Session 1)
    "session_1_wave1": {...},
    "session_1_wave2": {...}
  },
  "session_2_wave1": {...},
  "session_2_wave2": {...}
}
```

**Session 4+:**
- Follows the same nesting pattern
- `previous_context` contains the cumulative context from the prior session
- Direct fields contain the immediate prior session's Wave 1 and Wave 2

**HOW TO USE CUMULATIVE CONTEXT:**

1. **Most Recent Session**: Check `session_N_wave1` and `session_N_wave2` for the immediately prior session
2. **Earlier Sessions**: Navigate `previous_context` recursively to access older sessions
3. **Longitudinal Patterns**: Compare current session to trends across multiple sessions
4. **Progress Tracking**: Compare current progress_indicators to previous sessions
5. **Skill Development**: Track proficiency changes across sessions (beginner → developing → proficient)
6. **Therapeutic Alliance**: Monitor engagement, openness, and alliance strength over time

**CRITICAL**: If cumulative_context is null/missing, this is the patient's first analyzed session. Frame insights accordingly.

[... rest of existing system prompt ...]
```

#### 2.4 Update Prompt Creation to Include Cumulative Context

**File**: `backend/app/services/deep_analyzer.py`
**Changes**: Format cumulative context in user prompt

```python
# Lines 367-440 - _create_analysis_prompt
def _create_analysis_prompt(self, context: Dict[str, Any]) -> str:
    """Create the analysis prompt from context."""
    current = context["current_session"]
    history = context["patient_history"]
    cumulative = context.get("cumulative_context")  # NEW

    # ... (existing previous sessions formatting)

    # NEW: Format cumulative context
    cumulative_context_str = "No cumulative context (this is the first analyzed session)."
    if cumulative:
        cumulative_context_str = json.dumps(cumulative, indent=2)

    return f"""Analyze this therapy session and provide comprehensive patient-facing insights.

**CURRENT SESSION DATA:**

[... existing current session data ...]

---

**PATIENT HISTORY:**

[... existing patient history ...]

---

**CUMULATIVE CONTEXT (Previous Sessions' Full Analysis):**

{cumulative_context_str}

---

**INSTRUCTIONS:**

1. Read the entire current session transcript carefully
2. Review the cumulative context to understand the patient's journey
3. Analyze in context of both patient history AND cumulative context
4. Extract progress indicators (compare to previous sessions if available)
5. Identify key insights (look for patterns across sessions)
6. Assess coping skill development (track proficiency changes)
7. Evaluate therapeutic relationship quality (monitor alliance over time)
8. Provide actionable recommendations (build on previous homework)
9. Assign confidence score based on data quality and clarity

Return your analysis as JSON following the specified format. Be compassionate, specific, and empowering."""
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile app/services/deep_analyzer.py`
- [x] Type hints are correct: `mypy app/services/deep_analyzer.py` (if type checking enabled)
- [x] No import errors after changes

#### Manual Verification:
- [x] `analyze_session()` signature includes `cumulative_context` parameter
- [x] System prompt clearly explains cumulative context structure
- [x] User prompt includes cumulative context when available
- [x] Cumulative context is properly JSON-serialized in prompt

**Implementation Note**: Test with and without cumulative context to ensure backward compatibility.

---

## Phase 3: Update Test Script for Cumulative Context

### Overview
Modify `test_full_pipeline_demo.py` to build cumulative context and pass it between sessions.

### Changes Required:

#### 3.1 Add Cumulative Context Builder Function

**File**: `backend/tests/test_full_pipeline_demo.py`
**Changes**: Add function to create cumulative context blob

```python
# Add after MockSessionDatabase class definition
def build_cumulative_context(
    previous_context: Optional[Dict[str, Any]],
    previous_session_num: int,
    wave1_results: Dict[str, Any],
    wave2_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build cumulative context blob for the next session.

    Args:
        previous_context: The cumulative context from the previous session (or None)
        previous_session_num: Session number of the previous session
        wave1_results: Wave 1 results from previous session
        wave2_results: Wave 2 results from previous session

    Returns:
        New cumulative context blob with nested structure

    Example:
        For Session 11 (using Session 10 results):
        {
            "session_10_wave1": {...},
            "session_10_wave2": {...}
        }

        For Session 12 (using Session 11 results + its context):
        {
            "previous_context": {
                "session_10_wave1": {...},
                "session_10_wave2": {...}
            },
            "session_11_wave1": {...},
            "session_11_wave2": {...}
        }
    """
    context = {}

    # If there was a previous context, nest it
    if previous_context:
        context["previous_context"] = previous_context

    # Add previous session's Wave 1 and Wave 2 results
    context[f"session_{previous_session_num}_wave1"] = wave1_results
    context[f"session_{previous_session_num}_wave2"] = wave2_results

    return context
```

#### 3.2 Update Wave 2 Analysis to Use Cumulative Context

**File**: `backend/tests/test_full_pipeline_demo.py`
**Changes**: Pass cumulative_context to deep analyzer

```python
# Lines 333-395 - run_wave2_analysis
async def run_wave2_analysis(
    session_num: int,
    session_data: Dict[str, Any],
    wave1_results: Dict[str, Any],
    mock_db: MockSessionDatabase,
    cumulative_context: Optional[Dict[str, Any]] = None  # NEW
) -> Dict[str, Any]:
    """
    Run Wave 2 deep analysis with session history context

    Args:
        session_num: Current session number
        session_data: Raw session JSON
        wave1_results: Wave 1 analysis results
        mock_db: Mock database with previous sessions
        cumulative_context: Cumulative context from previous sessions (NEW)

    Returns:
        Deep analysis results
    """
    print(f"\n{'=' * 80}")
    print(f"WAVE 2 ANALYSIS - SESSION {session_num}")
    print(f"{'=' * 80}")

    session_id = f"session_{session_num:02d}"

    # Display cumulative context info
    if cumulative_context:
        print(f"\n🧠 Running Deep Clinical Analysis with Cumulative Context")
        # Count how many sessions are in the cumulative context
        context_depth = 1  # At least one session
        temp_context = cumulative_context
        while "previous_context" in temp_context:
            context_depth += 1
            temp_context = temp_context["previous_context"]
        print(f"   Cumulative context depth: {context_depth} previous session(s)")
    else:
        print(f"\n🧠 Running Deep Clinical Analysis (No cumulative context - first session)")

    # ... (existing session_context building)

    try:
        # ... (existing deep analyzer setup and mocking)

        # Run analysis WITH cumulative context
        analysis = await deep_analyzer.analyze_session(
            session_id,
            session_context,
            cumulative_context=cumulative_context  # NEW: Pass cumulative context
        )

        # ... (existing result display)

        return {
            "session_id": session_id,
            "deep_analysis": analysis.to_dict(),
            "confidence_score": analysis.confidence_score,
        }

    except Exception as e:
        print(f"   ❌ Deep Analysis Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "session_id": session_id,
            "deep_error": str(e)
        }
```

#### 3.3 Update Main Loop to Build and Pass Cumulative Context

**File**: `backend/tests/test_full_pipeline_demo.py`
**Changes**: Modify main() to chain cumulative context

```python
# Lines 514-548 - main() session processing loop
# Process Sessions 10, 11, 12 (full analysis with output)
target_sessions = [10, 11, 12]

cumulative_context = None  # Start with no context for Session 10

for session_num in target_sessions:
    print(f"\n{'#' * 80}")
    print(f"SESSION {session_num} - FULL PIPELINE")
    print(f"{'#' * 80}")

    # Load session
    session_data = load_session(session_num)
    print(f"\n📄 Loaded: {session_data.get('id', 'Unknown')}")
    print(f"   Segments: {len(session_data.get('segments', []))}")

    # Wave 1
    wave1_results = run_wave1_analysis(session_num, session_data)

    # Add to mock database
    mock_db.add_session(session_num, session_data, wave1_results)

    # Wave 2 (with cumulative context)
    wave2_results = await run_wave2_analysis(
        session_num,
        session_data,
        wave1_results,
        mock_db,
        cumulative_context=cumulative_context  # Pass cumulative context
    )

    # Combine results
    session_result = {
        "session_num": session_num,
        "session_id": session_data.get("id"),
        "wave1": wave1_results,
        "wave2": wave2_results,
        "cumulative_context_used": cumulative_context is not None,  # Track if context was used
    }

    all_results["sessions"].append(session_result)

    # Build cumulative context for NEXT session
    # (Session 10 results become context for Session 11, etc.)
    cumulative_context = build_cumulative_context(
        previous_context=cumulative_context,
        previous_session_num=session_num,
        wave1_results=wave1_results,
        wave2_results=wave2_results
    )
```

### Success Criteria:

#### Automated Verification:
- [x] Script runs without errors: `cd backend && source venv/bin/activate && python tests/test_full_pipeline_demo.py`
- [x] JSON output file is created in `mock-therapy-data/`
- [x] JSON file contains all 3 sessions with Wave 2 results (no "deep_error")

#### Manual Verification:
- [x] Terminal output shows "No cumulative context" for Session 10
- [x] Terminal output shows "Cumulative context depth: 1" for Session 11
- [x] Terminal output shows "Cumulative context depth: 2" for Session 12
- [x] JSON output file shows Session 11 references Session 10 patterns
- [x] JSON output file shows Session 12 references Sessions 10 and 11

**Implementation Note**: Review JSON output to verify deep analysis quality improves with cumulative context.

---

## Phase 4: Verify and Optimize System Prompts for Model Tiers

### Overview
Audit all algorithm system prompts to ensure they're optimized for their assigned model tier.

### Changes Required:

#### 4.1 Verify Mood Analyzer (gpt-5-nano)

**File**: `backend/app/services/mood_analyzer.py`
**Current Model**: `gpt-5-nano` (VERY_LOW complexity, $0.05/$0.40 per 1M tokens)
**Prompt Assessment**: ✅ **APPROPRIATE**

**Rationale:**
- Simple 0-10 scoring task with 0.5 increments
- Clear structured output (mood_score, confidence, rationale, indicators, tone)
- Minimal reasoning required (classification + brief explanation)
- Well-defined categories (0-2: severe, 2.5-4: significant, etc.)
- No complex synthesis or multi-step reasoning

**Recommendation**: No changes needed. Prompt is well-suited for gpt-5-nano.

#### 4.2 Verify Topic Extractor (gpt-5-mini)

**File**: `backend/app/services/topic_extractor.py`
**Current Model**: `gpt-5-mini` (MEDIUM complexity, $0.25/$2.00 per 1M tokens)
**Prompt Assessment**: ✅ **APPROPRIATE**

**Rationale:**
- Structured extraction task (1-2 topics, 2 action items, 1 technique, summary)
- Moderate reasoning required (identify main themes, extract concrete tasks)
- Technique library validation (match against predefined list)
- 150-character summary constraint requires conciseness
- No longitudinal analysis or complex synthesis

**Recommendation**: No changes needed. Prompt is well-suited for gpt-5-mini.

#### 4.3 Verify Breakthrough Detector (gpt-5)

**File**: `backend/app/services/breakthrough_detector.py`
**Current Model**: `gpt-5` (HIGH complexity, $1.25/$10.00 per 1M tokens)
**Prompt Assessment**: ✅ **APPROPRIATE**

**Rationale:**
- Complex clinical reasoning required (distinguish genuine breakthroughs from progress)
- Ultra-strict criteria (7 categories of what IS a breakthrough, 6 categories of what ISN'T)
- Nuanced judgment calls (is this self-discovery or just empowerment?)
- Pattern recognition across conversation
- High stakes (false positives dilute therapeutic value)

**Recommendation**: No changes needed. Prompt is well-suited for gpt-5.

#### 4.4 Verify Deep Analyzer (gpt-5.2) - NEEDS UPDATE

**File**: `backend/app/services/deep_analyzer.py`
**Current Model**: `gpt-5.2` (VERY_HIGH complexity, $1.75/$14.00 per 1M tokens)
**Prompt Assessment**: ⚠️ **NEEDS MODEL CAPABILITY CONTEXT**

**Rationale:**
- Most complex task (synthesis of Wave 1 + patient history + cumulative context)
- Requires tracking patterns across multiple sessions
- Generates 5 complex output dimensions (progress, insights, skills, relationship, recommendations)
- Longitudinal reasoning (compare current to previous sessions)
- **BUT**: Prompt doesn't mention the model's advanced capabilities

**Recommendation**: Update system prompt to reference GPT-5.2 capabilities (already done in Phase 2.3).

### Success Criteria:

#### Automated Verification:
- [x] All system prompts are valid Python strings
- [x] No syntax errors in any service file

#### Manual Verification:
- [x] Mood analyzer prompt is concise and task-focused (suited for gpt-5-nano)
- [x] Topic extractor prompt is structured and clear (suited for gpt-5-mini)
- [x] Breakthrough detector prompt is nuanced and strict (suited for gpt-5)
- [x] Deep analyzer prompt references GPT-5.2 capabilities (suited for gpt-5.2)
- [x] No prompts ask for capabilities beyond the model's tier

**Implementation Note**: These are verification-only changes. No code modifications needed for Phases 4.1-4.3.

---

## Testing Strategy

### Unit Tests:
- Deep analyzer handles None cumulative context
- Deep analyzer handles nested cumulative context
- Cumulative context builder creates correct structure
- Helper functions return empty data when db=None

### Integration Tests:
- Full pipeline runs on Sessions 10, 11, 12
- Wave 2 completes successfully for all sessions
- Cumulative context is properly chained
- JSON output contains complete Wave 1 + Wave 2 for all sessions

### Manual Testing Steps:
1. Run: `cd backend && source venv/bin/activate && python tests/test_full_pipeline_demo.py`
2. Verify terminal output shows:
   - Session 10: "No cumulative context (first session)"
   - Session 11: "Cumulative context depth: 1 previous session(s)"
   - Session 12: "Cumulative context depth: 2 previous session(s)"
3. Check JSON output file opens automatically
4. Review JSON structure:
   - All 3 sessions have `wave2` with no `deep_error`
   - Session 11 deep analysis mentions Session 10 patterns
   - Session 12 deep analysis references both 10 and 11
5. Verify deep analysis quality improves with more context

## Performance Considerations

**Expected Runtime:**
- Wave 1 (3 sessions × 3 algorithms): ~60-90 seconds
- Wave 2 (3 sessions × 1 algorithm with cumulative context): ~90-120 seconds
- **Total: ~2.5-3.5 minutes**

**API Costs:**
- Session 10: Wave 1 (~$0.01) + Wave 2 (~$0.02) = ~$0.03
- Session 11: Wave 1 (~$0.01) + Wave 2 with context (~$0.025) = ~$0.035
- Session 12: Wave 1 (~$0.01) + Wave 2 with richer context (~$0.03) = ~$0.04
- **Total per run: ~$0.11**

**Context Window Usage:**
- Session 10: ~5K tokens (current session only)
- Session 11: ~10K tokens (current + Session 10 context)
- Session 12: ~15K tokens (current + Sessions 10-11 context)
- Well within GPT-5.2's 400K context window

## Migration Notes

N/A - This is a fix to existing functionality, not a migration.

## References

- Deep analyzer: `backend/app/services/deep_analyzer.py`
- Model config: `backend/app/config/model_config.py:85-90` (task-model assignments)
- Test script: `backend/tests/test_full_pipeline_demo.py`
- Existing Wave 1 results: `mock-therapy-data/full_pipeline_demo_20251223_174717.json`
- Mood analyzer prompt: `backend/app/services/mood_analyzer.py:127-167`
- Topic extractor prompt: `backend/app/services/topic_extractor.py:164-239`
- Breakthrough detector prompt: `backend/app/services/breakthrough_detector.py:191-306`
