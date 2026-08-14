---
kind: scout-brief
date: 2026-08-14
subject: issue-223
role: execution-observation
phase: 1
---

# Scout brief — what strong audits of this deliverable-class check

canonical: `docs/issue-223/reports/execution-observation/survey.md`, committed this session as `b743aafc`
Deliverable class: an evidence-only post-merge audit of one merged
concurrency fix (PR #249), scoped to the surfaces named in the survey.

## Category must-bes (general audit method, not a per-artifact claim)

- A file-based mutual-exclusion lock is only as good as its create-step
  atomicity. `O_CREAT|O_EXCL` (or an `os.link()`/`os.replace()` onto the
  final path) is the accepted pattern; a read-modify-write on an
  already-created file via `Path.write_text()` (which truncates first)
  is a known variant of the same window. An audit checks every step
  that mutates a claim file, not only the first create.
- A two-thread concurrency test that flips from red to green is
  evidence for the interleaving it constructs, not a proof about every
  interleaving. An audit distinguishes those two claims explicitly.
- A deviation from an approved plan, recorded with its mechanism at the
  time it was taken, is the expected shape of a working change-control
  process — the audit checks the deviation's intent-preservation against
  the original ask, not the bare fact that the shape changed.
- A caller that discards a subordinate call's return code is a known
  false-observation family: the caller's own bookkeeping proceeds
  unaware of an outcome (rejection vs. success) the new code gave new
  meaning to.

## Performance axes

1. Traceability — every claim tied to a named commit or `file:line`.
2. Scope discipline — this audit judges PR #249's account only; it does
   not redesign the fix or re-open issue #132's respawn-claim mechanism.
3. Actionability — a finding names the artifact and line to change.

## Adopt / skip for phase 2

- Adopt: state the inspection ceiling explicitly for the four new
  tests' construction-level check — this role does not re-run
  `test_spawn.py`.
- Adopt: verify the rc-discard item at `spawn.py:3523` by an
  independent read rather than re-deriving it from nothing.
  canonical: `docs/issue-223/reports/execution-observation/survey.md`, "Call-site check" section, committed this session as `b743aafc`
- Skip: evaluating whether `os.link()`+tempfile is the best possible
  design versus alternatives such as `flock()` — the proposal made that
  call and it was approved.
