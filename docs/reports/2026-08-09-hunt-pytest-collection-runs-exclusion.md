---
proposal: docs/issue-540/proposals/2026-08-09-pytest-collection-runs-exclusion.md
---

# Hunt record — pytest-collection-runs-exclusion

## after-proposal — stance 0: assume the gate/fix just proposed is bypassable — find the bypass

Verdict: NO FINDING
Seed: docs/issue-540/proposals/2026-08-09-pytest-collection-runs-exclusion.md (norecursedirs = runs)
cap_seconds: 60
tier: default
diff_stat_lines: 0 (proposal not yet applied to pytest.ini; tested the proposed change manually)
started_at: 2026-08-09T04:59:25+09:00
ended_at: 2026-08-09T05:01:30+09:00

Reproduced by creating pytest.ini with `norecursedirs = runs`, adding
runs/clone/tests/test_collide.py (a basename-colliding test file nested two
levels deep), and running plain `python3 -m pytest -q` from repo root: 819
passed, 2 pre-existing unrelated failures, no collision/duplicate-basename
error — the runs/ clone was correctly skipped. norecursedirs matches
directory basename at any depth (not just top-level), confirmed by the
nested placement. Explicit invocation `pytest runs/clone/tests/test_collide.py`
does collect the file directly, but that is standard pytest behavior
unaffected by norecursedirs and not a new bypass introduced by this fix — it
requires an operator to deliberately path into the ignored directory, which
is outside the threat model of "plain `pytest` walks into runs/ and errors".
No reproducible bypass of the stated goal (stopping ordinary recursive
collection from entering runs/) was found.
