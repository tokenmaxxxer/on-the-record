# Deviation log — issue #2073 (implementation role)

Placed under `reports/implementation/` rather than the issue-level
deviation-log path named in the deviation directive: `board-gate.sh`
refuses that path for this role as a foreign record (contract v3 §11).

- 2026-08-23 — filed — the skill-verdict obligation (#2039) requires one
  verdict line per mounted skill in this role's phase-2 record file, but
  contract v3 §19 forbids writing that record before the phase-2
  Approve, so it does not exist yet. This phase-1 session therefore
  stated the six verdict lines in its reply instead, and the Stop-hook
  `skill-verdict-guard` fired. Needs a rule-level resolution (a phase-1
  home for skill verdicts, or scoping the guard to phase-2 sessions) —
  reported, not spawned.
- 2026-08-23 — inline — `acceptance-command-real-run-guard.sh` refuses
  any commit staging `docs/specs/enforcement-boundary.md`, because that
  file's own row for the guard quotes verbatim the citation shape the
  guard scans staged content for; the phase-2 write set has to add a row
  there for the new leaf gate module. Used the guard's documented
  `Acceptance-recheck-N/A:` trailer on the commits that touch that file.
- 2026-08-23 — inline — the issue's Acceptance names
  `gates/test_check_runner.py`, but a file of that basename already
  existed under tests/ (issue-1323 req 2), and two test modules sharing
  a basename with no package boundary break pytest collection —
  `gates/test_duplicate_test_basenames.py` fails on it.
  canonical: `python3 -m pytest -q -m "not slow"` on this tree, which
  reported that failure plus a collection ERROR for the tests/ path
  Moved the older file's tests into `gates/test_check_runner.py` (next
  to the module they exercise, as every other `gates/test_*.py` sits)
  and deleted the tests/ copy. No coverage was dropped and no assertion
  was changed. The deleted path is outside the proposal's frozen write
  set, so it is also reported in this session's reply rather than only
  logged here.


