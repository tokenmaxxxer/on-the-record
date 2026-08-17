---
status: proposed
files:
  - gates/requirement_met.py
  - gates/test_requirement_met.py
  - on-the-record/hooks/directive.sh
  - gates/acceptance_gate.py
---

## Request

#1696: executed-live checks must prove the EXACT installed/documented
command, not a merely equivalent one. Observed live (pilot-devdigest PR
#6): a builder proved `python3 -m devdigest.cli` (PYTHONPATH-dependent)
while the installed crontab line was `python3 -m devdigest`, which could
not run at all — the record looked honest, the digest file existed, and
only a builder-blind reviewer re-running the literal installed line
caught it. Name the command-identity rule in the orchestrate/role
directive and the acceptance-format documentation, and make
`requirement_met`'s deterministic layer flag a recorded command that
differs from the check's named command surface.

## Constraints

- Deterministic only — this is a mechanical string-identity check, not
  an LLM judgment call; it must live in `grade()`'s existing
  deterministic sub-check tier (blocks), never the semantic/advisory
  tier (per the module's own documented separation, issue #1660/#1661).
- No new citation format — reuse the `acceptance: <command> — result:
  ...` shape `gates/record_lint.py` already canonicalizes as
  executed-live proof (issue #870/#892/#914).
- Must not regress the existing artifact-presence sub-check or its
  tests.

## Rationale

Considered making command-identity a semantic/LLM-graded criterion
(have the builder-blind session judge "does this look like the same
command") instead of a deterministic string comparison. Rejected: the
whole point of the issue is that an equivalent-LOOKING command already
fooled an honest-looking record — a semantic judge is exactly the
mechanism that already failed once (LLM judges are documented elsewhere
in this grader as gameable/biased). A deterministic, normalized
string-identity comparison against the diff's own recorded citation is
falsifiable and cannot be talked past.

Considered piggybacking on
`acceptance-command-real-run-guard.sh`'s registered-command re-run
(issue #914) instead of adding a grader-side check. Rejected: that guard
answers "did the claimed PASS/FAIL actually happen," a different axis
from "is the recorded command the one the check named" — folding this
into it would conflate re-execution with identity-checking and the
guard has no notion of a check's Acceptance-section command surface to
compare against in the first place.

## What will be done

- `gates/requirement_met.py`: add `_provenance_map()` (pairs a
  `check:`/`gate:` bullet with its indented `provenance:` line),
  `_recorded_commands_in_diff()` (pulls `acceptance: <command> —
  result: ...` citations from added diff lines), and
  `_command_identity_mismatch()` (env-prefix-normalized comparison).
  Wire into `grade()`: for a `provenance: executed-live` check whose
  artifact is a command, flag `command_identity_mismatch` and add a
  blocking reason — independent of the semantic verdict, since this is
  a structural fact, not a graded judgment. Surface the new fields
  (`provenance`, `command_identity_mismatch`) in `check()`'s advisory
  output too.
- `gates/test_requirement_met.py`: mismatched-command fixture (mirrors
  the pilot-devdigest shape) plus matching-command and
  no-recorded-command / executed-unit-provenance negative cases.
- `on-the-record/hooks/directive.sh`: extend the ACCEPTANCE FORMAT block
  with a COMMAND-IDENTITY paragraph stating the rule.
- `gates/acceptance_gate.py`: extend the module docstring with the same
  rule, cross-referencing `requirement_met.py` as the enforcement point.

## Out of scope

- Re-running the recorded command against the real target (that's
  `acceptance-command-real-run-guard.sh`'s job, issue #914 — unchanged
  here).
- Any change to `check_runner.py`'s own execution path.
- Environment-independence enforcement beyond the env-prefix
  normalization needed to avoid false-positive mismatches — the
  directive/docstring state the rule; a stricter env-crutch detector is
  a possible follow-up, not this issue's acceptance.

## How you'll know it worked

`python3 -m pytest gates/test_requirement_met.py -q` passes, including
the new mismatched-command fixture; `grep -n "COMMAND-IDENTITY"
on-the-record/hooks/directive.sh gates/acceptance_gate.py` shows both
files carry the rule.
