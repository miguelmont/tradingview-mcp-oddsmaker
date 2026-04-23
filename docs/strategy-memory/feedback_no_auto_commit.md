---
name: Never make git commits automatically
description: User always commits manually. Do not run git commit, git push, or git add -A on their behalf even if the task seems to warrant it.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
Never run `git commit`, `git push`, `git add -A`, or any mutating git operation that creates or publishes commits. The user handles all commits manually and wants full control over what goes into their git history.

**Why:** user stated explicitly on 2026-04-22 after I proposed committing completed optimization work. Commit authorship, message wording, and staging hygiene are things they want to do themselves.

**How to apply:** after completing code changes, summarize what was edited/created and hand the session back. Do NOT suggest "let me commit this" or run the commands. It's fine to run read-only git operations (status, log, diff) when the user asks. If the user asks me to commit explicitly, then do it — but default is manual.
