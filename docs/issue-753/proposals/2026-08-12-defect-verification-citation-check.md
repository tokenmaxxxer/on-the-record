---
status: proposed
files:
  - docs/issue-753/reports/defect-verification.md
---

## Intent

Issue #753 asks for a session-completion-durability audit (northpole
reqs #1, #4), generalizing the 2026-08-11 strand family. Its phase-1
architecture survey (`docs/issue-753/reports/architecture/survey.md`, PR
#764, merged) is the only upstream record — no coding/qa/review records
exist since this is a read-only audit issue. This proposal covers the
defect-verification role's slice: independently attempt to reproduce
specific factual citations inside that architecture survey against the
actual `spawn.py` code and the `#732` proposal it cites, and write a
verified finding record for any citation that does not hold.

## Constraints stated so far

- Read-only reproduction; no fixes proposed (defect-verification role
  never fixes).
- Every reproduced finding carries an evidence pointer (grep/read
  output, command output) — never a paraphrase.
- Severity assigned only by the deterministic band (Critical/High to
  blocking, Medium/Low/Unknown to advisory), never freehand.
- Write set is docs/issue-753/reports/defect-verification.md only.

## What will be done

Phase-1 reproduction is complete:
`docs/issue-753/reports/defect-verification/survey.md` runs 4 attempts
against the architecture survey's own citations — 2 reproduced, 2
not-reproduced (confirmed accurate). Reproduced: (1) §1's claim that
`_release_spawn_claim` fires in a `finally` block after `ensure_pushed()`
returns "with a comment citing #719 explicitly" — false on both counts:
zero occurrences of "719" exist anywhere in `spawn.py`, and
`_release_spawn_claim` (line 2851) actually executes 30 lines *before*
`ensure_pushed` (line 2881), outside any `finally`; (2) §2's claim that
`_watch_all` is one of the watch loop bodies — no such function exists
anywhere in `spawn.py`. Not-reproduced: §1's `#732` proposal
`status: proposed` citation, and §3's `RESPAWN_MAX_ATTEMPTS = 2` citation,
both confirmed accurate.

Phase-2 (this proposal, on approval) writes the final
defect-verification record at
docs/issue-753/reports/defect-verification.md, per role-handoff contract
v3 s19's required shape: one finding block per reproduced attempt, each
addressed to `coding` (since `spawn.py` is on-the-record's own
orchestration code, not architecture's — a citation-accuracy defect in
architecture's survey text is itself out of this role's write scope to
fix, but the underlying #719 race the survey mis-describes as closed is
a real coding-owned defect), with evidence pointer, severity band, and
the northpole requirement it blocks.

## Out of scope

- Fixing spawn.py's release-before-push ordering (the actual #719 race
  this reproduction shows is still open) — role-appropriate follow-up
  for coding, not this role.
- Correcting the architecture survey's prose — that record already
  merged; a correction is a new architecture-role or coding concern, not
  this role's write scope.
- Re-litigating the architecture survey's overall PARTIAL/MET verdicts
  for §1/§2 — both verdicts stay independently plausible on their
  remaining, verified citations; only the specific quoted mechanism
  citations are under test here.

## How you will know it worked

docs/issue-753/reports/defect-verification.md exists, records an outcome
for every attempt in the phase-1 attempt list (no exceptions), a finding
block with evidence and severity for every reproduced attempt, and each
finding names the northpole requirement it blocks.

## What did not work

None.
