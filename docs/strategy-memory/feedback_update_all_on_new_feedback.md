---
name: Every new feedback triggers full artifact update
description: When the user provides new feedback (a new directive, rule change, clarification), ALL strategy artifacts must be updated in the same or immediately-following turn — feedback memo, MEMORY.md index, docs/my-strategy.md, docs/strategy-memory/ copy, .planning/REQUIREMENTS.md, .planning/ROADMAP.md, and any active phase plans. Partial updates lead to scripts/tests built against outdated rules.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
User directive 2026-04-23: "todo el feedback debe ser agregado no quiero scripts que no sirvan por tener feedback actualizado, ademas cada vez que recibas un nuevo feedback de mi, debes actualizar todo".

**Rationale:** In earlier sessions, feedback was captured in memory memos but never propagated to `docs/my-strategy.md`, `REQUIREMENTS.md`, or test fixtures. The result: scripts were written against stale strategy docs and produced incorrect behavior. Any feedback that is real (not noise) must be reflected EVERYWHERE it applies, in the same turn.

**Checklist on receiving new feedback:**
1. **Write the memo** — `.claude/projects/.../memory/feedback_<slug>.md` with frontmatter (name, description, type) + body with rule, Why, How to apply.
2. **Update MEMORY.md index** — add one-line pointer to the new memo.
3. **Copy to repo** — `docs/strategy-memory/feedback_<slug>.md` (same content, tracked in git).
4. **Update `docs/my-strategy.md`** — reflect the rule in the canonical strategy doc. Cross-check existing sections for contradictions and fix them.
5. **Update `.planning/REQUIREMENTS.md`** — if the feedback implies a new testable requirement, add a REQ-ID in the appropriate category. If it modifies an existing REQ, edit it.
6. **Update `.planning/ROADMAP.md`** — add the new REQ to the relevant phase's Requirements column and Success criteria.
7. **Update any in-progress phase PLAN.md** — if the active phase's plan would be affected, edit it.
8. **Update STATE.md** — log the feedback absorption in Accumulated Context.
9. **Commit** — group all these changes in one commit with message like `feedback: <short description> — propagate to requirements/roadmap/strategy`.

**When feedback is ambiguous:** ask for clarification first before propagating. A bad memo is worse than no memo.

**When feedback invalidates prior work:** flag it explicitly in the commit message and update any tests/fixtures that depended on the old behavior.
