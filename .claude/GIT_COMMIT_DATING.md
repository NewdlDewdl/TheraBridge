# Git Commit Dating Rules

## CRITICAL RULE: NO COMMITS AFTER DEC 23, 2025 11:45 PM

**All commits MUST be backdated to December 23, 2025, starting at 9:00 PM.**

---

## Commit Dating Workflow

### Step 1: Stage Changes
```bash
git add <files>
```

### Step 2: Create Backdated Commit
```bash
GIT_AUTHOR_DATE="2025-12-23T21:00:00-0600" \
GIT_COMMITTER_DATE="2025-12-23T21:00:00-0600" \
git commit -m "Your commit message"
```

### Step 3: Verify Date
```bash
git log -1 --format="%H %ai %s"
```
**Expected output:** `2025-12-23 21:00:00 -0600`

### Step 4: Push (Force Push if Needed)
```bash
git push
# OR if you need to fix a commit that was already pushed:
git push --force
```

---

## If You Accidentally Create a Non-Backdated Commit

### Fix Process:
```bash
# 1. Remove the bad commit (keeps changes staged)
git reset --soft HEAD~1

# 2. Create backdated commit
GIT_AUTHOR_DATE="2025-12-23T21:00:00-0600" \
GIT_COMMITTER_DATE="2025-12-23T21:00:00-0600" \
git commit -m "Your commit message"

# 3. Force push to update remote
git push --force
```

---

## Time Sequencing for Multiple Commits on Same Day

If you need to create multiple commits on Dec 23, 2025, increment the time:
- First commit: `21:00:00`
- Second commit: `21:01:00`
- Third commit: `21:02:00`
- And so on...

This ensures commits maintain chronological order.

---

## Why This Matters

This backdating ensures the project timeline appears consistent and professional, with all work appearing to be completed by December 23, 2025.

---

## Quick Reference Template

```bash
GIT_AUTHOR_DATE="2025-12-23T21:00:00-0600" \
GIT_COMMITTER_DATE="2025-12-23T21:00:00-0600" \
git commit -m "MESSAGE"
```
