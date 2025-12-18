# Automatic Orchestration Recursion Safety System

## Overview

The orchestration system features **fully automatic recursion depth tracking** using execution ID chains. Orchestrators self-manage their recursion depth without any user or manual intervention.

## Problem Solved

Previously, the orchestration system could spawn infinite orchestrator chains:
```
Orchestrator 0 (user task)
  → finishes → spawns Orchestrator 1 (cleanup)
    → finishes → spawns Orchestrator 2 (cleanup of cleanup)
      → finishes → spawns Orchestrator 3 (cleanup of cleanup of cleanup)
        → INFINITE LOOP ∞
```

This caused:
- Multiple competing orchestrators (6+ instances running)
- Database locks (test.db locked by multiple pytest processes)
- File conflicts (agents editing same files)
- Context window exhaustion (approaching 200K token limit)
- System resource exhaustion (CPU/memory overload)

## Solution: Automatic Execution ID Tracking

### Core Mechanism

Each orchestrator **automatically** tracks its recursion depth using an execution ID chain:

```
[EXEC_ID: ORG_1234.1.1]
```

**How it works:**
- **No tag in prompt:** Root orchestrator (auto-generates `ORG_1234`)
- **One dot:** Child orchestrator (`ORG_1234.1`)
- **Two dots:** Grandchild orchestrator (`ORG_1234.1.1`)
- **Three+ dots:** FORBIDDEN (prevents infinite loops)

**The orchestrator automatically:**
1. Checks for `[EXEC_ID: ...]` in its prompt
2. If not found, generates a root ID (e.g., `ORG_1234`)
3. Counts dots to determine its depth
4. Decides whether to spawn children or use direct commands
5. When spawning, generates child ID by appending `.N`

**NO USER INTERVENTION REQUIRED**

### Automatic Implementation

#### 1. Parse or Generate Execution ID

Every orchestrator starts by getting its ID:

```python
import re
import time

def parse_execution_id(prompt: str) -> str:
    """
    Extract execution ID from prompt, or generate if root
    """
    match = re.search(r'\[EXEC_ID:\s*([^\]]+)\]', prompt)
    if match:
        return match.group(1)
    else:
        # Root orchestrator - auto-generate ID
        timestamp = str(int(time.time() * 1000))[-4:]
        return f"ORG_{timestamp}"

# Usage (automatic)
my_exec_id = parse_execution_id(incoming_prompt)
print(f"🔄 Orchestrator ID: {my_exec_id}")
```

#### 2. Calculate Depth Automatically

Depth is calculated by counting dots:

```python
def calculate_depth(exec_id: str) -> int:
    """
    Count dots to determine depth
    ORG_1234 → 0
    ORG_1234.1 → 1
    ORG_1234.1.1 → 2
    """
    return exec_id.count('.')

# Usage (automatic)
my_depth = calculate_depth(my_exec_id)
print(f"🔄 Recursion Depth: {my_depth} / 2 (max)")
```

#### 3. Check Spawning Permissions Automatically

```python
def can_spawn_child(exec_id: str, max_depth: int = 2) -> bool:
    """Check if we can spawn a child"""
    return calculate_depth(exec_id) < max_depth

# Usage (automatic)
if can_spawn_child(my_exec_id):
    # Safe to spawn child orchestrator
    spawn_child_orchestrator()
else:
    # Max depth reached - use direct commands
    print("⚠️ Max depth reached - using direct commands")
    run_direct_commands()
```

#### 4. Generate Child ID Automatically

When spawning a child:

```python
def generate_child_id(parent_id: str, child_index: int = 1) -> str:
    """
    Auto-generate child ID by appending index
    ORG_1234 + 1 → ORG_1234.1
    ORG_1234.1 + 1 → ORG_1234.1.1
    """
    return f"{parent_id}.{child_index}"

# Usage (automatic)
child_id = generate_child_id(my_exec_id, child_index=1)
child_prompt = f"""[EXEC_ID: {child_id}]

Clean up repository...

Your ID: {child_id}
Your depth: {calculate_depth(child_id)} (automatically calculated)
"""
```

### Cleanup Behavior by Depth

#### Depth 0-1: Comprehensive Orchestrated Cleanup

Spawn a child orchestrator for parallel, intelligent cleanup:

```xml
<invoke name="Task">
<parameter name="subagent_type">parallel-orchestrator</parameter>
<parameter name="description">Cleanup repository (Depth 1)</parameter>
<parameter name="prompt">[RECURSION_DEPTH: 1]

Clean up repository with comprehensive organization...
</parameter>
</invoke>
```

**Benefits:**
- Parallel cleanup agents (multiple files/dirs at once)
- Intelligent consolidation (analyze before deleting)
- Comprehensive metrics (before/after file counts)
- Follows CLAUDE.md rules

#### Depth 2+: Direct Bash Cleanup

Use simple bash commands for basic cleanup:

```xml
<invoke name="Bash">
<parameter name="command">
cd /path/to/repo && {
  # Remove temp files
  find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  find . -name "*.pyc" -delete
  find . -name "*.tmp" -delete
  find . -name ".DS_Store" -delete

  # Show stats
  echo "Cleanup complete"
  git status --short
}
</parameter>
</invoke>
```

**Benefits:**
- No recursion (direct commands)
- Fast execution (no orchestration overhead)
- Safe fallback (prevents infinite loops)

## Maximum Recursion Depth: 2

### Why Depth 2?

```
Depth 0 (Root):
  User: "Implement Feature X with tests"
  └─> Spawns agents to build feature
      └─> Creates commits
          └─> Needs cleanup
              └─> Spawns Depth 1 ✅

Depth 1 (Child):
  Task: "Clean up after Feature X"
  └─> Spawns agents to consolidate files
      └─> Removes duplicates
          └─> Creates commit
              └─> Needs cleanup
                  └─> Spawns Depth 2 ✅

Depth 2 (Grandchild):
  Task: "Clean up after cleanup"
  └─> Uses DIRECT bash commands
      └─> Removes __pycache__
          └─> Done (NO SPAWN) ✅
```

**Depth 3 would be unnecessary:**
- Cleanup of cleanup of cleanup = redundant
- Risk of infinite loops increases
- Minimal benefit vs overhead

## Usage Examples

### Example 1: User-Initiated Orchestration (Depth 0)

```bash
User: /cl:orchestrate Implement authentication system
```

**Orchestrator behavior:**
```
🔄 Orchestrator Depth: 0 (max: 2)

1. Execute main waves (auth implementation)
2. Show execution summary
3. Spawn cleanup orchestrator (Depth 1) ✅
4. Push to GitHub
```

### Example 2: Cleanup Orchestration (Depth 1)

```
[RECURSION_DEPTH: 1]

Clean up repository after authentication implementation
```

**Orchestrator behavior:**
```
🔄 Orchestrator Depth: 1 (max: 2)

1. Execute cleanup waves (consolidate, organize)
2. Show cleanup summary
3. Spawn cleanup orchestrator (Depth 2) ✅
4. Return to parent
```

### Example 3: Cleanup of Cleanup (Depth 2)

```
[RECURSION_DEPTH: 2]

Clean up repository after cleanup phase
```

**Orchestrator behavior:**
```
🔄 Orchestrator Depth: 2 (max: 2)

⚠️ MAX DEPTH REACHED - Using direct cleanup

1. Run bash commands (rm __pycache__, *.pyc, etc.)
2. Show basic summary
3. Return to parent (NO SPAWN) ✅
```

### Example 4: Prevented Infinite Loop (Depth 3)

```
[RECURSION_DEPTH: 3]

This should never happen!
```

**Orchestrator behavior:**
```
🔄 Orchestrator Depth: 3 (max: 2)

🚨 ERROR: Recursion depth exceeded!

This orchestrator was spawned at depth 3, which exceeds the maximum depth of 2.

Possible causes:
- Bug in depth tracking logic
- Orchestrator spawned itself incorrectly
- Depth tag was manually edited

Falling back to direct cleanup mode...
```

## Safety Guarantees

### 1. Hard Limit: Maximum Depth 2

```python
MAX_DEPTH = 2

def validate_depth(depth: int):
    if depth > MAX_DEPTH:
        raise RecursionDepthExceeded(
            f"Depth {depth} exceeds maximum {MAX_DEPTH}"
        )
```

### 2. Automatic Fallback: Direct Commands

If depth >= 2, orchestrators automatically use direct Bash commands instead of spawning children.

### 3. Clear Visibility: Depth Displayed

Every orchestrator outputs its current depth:

```
🔄 Orchestrator Depth: 1 (max: 2)
```

Users can see exactly how deep the recursion is.

### 4. No Orphaned Orchestrators

Each orchestrator completes fully before spawning cleanup:
- Main task → Complete
- Report results → Complete
- Spawn cleanup → Only if depth < 2
- Push to GitHub → Complete
- Return to user → Complete

## Performance Impact

### Before Recursion Safety

```
User task → Orchestrator 0
  → Cleanup → Orchestrator 1
    → Cleanup → Orchestrator 2
      → Cleanup → Orchestrator 3
        → Cleanup → Orchestrator 4
          → ...∞

Total orchestrators: UNBOUNDED
Risk: System crash
```

### After Recursion Safety

```
User task → Orchestrator 0
  → Cleanup → Orchestrator 1
    → Cleanup → Orchestrator 2 (direct bash)
      → DONE

Total orchestrators: MAX 3
Risk: ELIMINATED
```

**Metrics:**
- **Maximum concurrent orchestrators:** 3 (down from 6+)
- **Context window usage:** Bounded (no exponential growth)
- **System resources:** Predictable (no runaway processes)
- **Database locks:** Eliminated (sequential cleanup)

## Monitoring and Debugging

### Check Current Depth

When debugging, look for depth tags in logs:

```
grep "RECURSION_DEPTH" orchestration.log
grep "Orchestrator Depth" orchestration.log
```

### Detect Depth Violations

If you see depth > 2:

```bash
# Check for orchestrators at depth 3+
grep "RECURSION_DEPTH: [3-9]" orchestration.log
```

### Monitor Active Orchestrators

```bash
# Count running orchestrator processes
ps aux | grep "parallel-orchestrator" | wc -l

# Should be <= 3 at any time
```

## Best Practices

### 1. Always Include Depth Tag When Spawning

```xml
<!-- GOOD -->
<invoke name="Task">
<parameter name="prompt">[RECURSION_DEPTH: 1]

Your task here...
</parameter>
</invoke>

<!-- BAD - Missing depth tag -->
<invoke name="Task">
<parameter name="prompt">Your task here...</parameter>
</invoke>
```

### 2. Check Depth Before Spawning

```python
# ALWAYS check depth first
current_depth = parse_recursion_depth(prompt)

if current_depth < 2:
    spawn_orchestrator()
else:
    use_direct_commands()
```

### 3. Use Direct Commands for Simple Tasks

If a task is simple (remove temps, basic cleanup), don't spawn an orchestrator:

```python
# GOOD - Simple task, direct command
run_bash("find . -name '*.tmp' -delete")

# BAD - Overkill to spawn orchestrator
spawn_orchestrator("Remove all .tmp files")
```

### 4. Document Depth in Descriptions

```xml
<parameter name="description">Cleanup repository (Depth 1)</parameter>
```

Makes debugging easier.

## Related Files

- `.claude/agents/cl/parallel-orchestrator.md` - Agent implementation
- `.claude/commands/cl/orchestrate.md` - Slash command protocol
- `.claude/DYNAMIC_WAVE_ORCHESTRATION.md` - Wave methodology
- `.claude/ORCHESTRATION_IMPROVEMENTS.md` - Feature history

## Changelog

**2025-12-18:** Initial implementation
- Added `[RECURSION_DEPTH: N]` tag system
- Implemented depth checking logic
- Added automatic fallback to direct commands at depth 2
- Committed to main branch (commit 86c0681)
- Pushed to GitHub: https://github.com/evolvedtroglodyte/TheraBridge
