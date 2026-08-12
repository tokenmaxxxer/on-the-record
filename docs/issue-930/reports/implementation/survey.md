# Current-state survey — issue #930 (implementation role, phase 1)

## Scout skip record

Skip condition: "spec literally leaves no design decision open."

canonical: `docs/issue-930/proposals/requirement-digest-drift-guard.md` (read in full this session)

The `product-discovery` role's design proposal for this issue is on
`main` at that path and its frontmatter reads `status: approved`,
naming the full write set and design already. This role's job is to
build that design as specified; the design proposal already made every
product-shaped call implementation would otherwise scout for. No
separate scouting step taken.

## Write set this proposal expects to touch (verified against current tree)

derived: `ls docs/specs/requirements.md gates/spec_index.py gates/test_accumulation.py on-the-record/hooks/spec-index-preflight.sh`
```
docs/specs/requirements.md
gates/spec_index.py
gates/test_accumulation.py
on-the-record/hooks/spec-index-preflight.sh
```

- docs/specs/requirements.md — exists (canonical: file read this
  session, lines 1-24 — `## R001` entry present; field doc states
  `status: stale` is "computed by gates.requirement_registry").
- docs/specs/requirement-digest.md — new file, not yet present
  (derived: `ls docs/specs/requirement-digest.md` — no such file).
- gates/requirement_digest.py — new file, not yet present (derived:
  `ls gates/requirement_digest.py` — no such file). gates/spec_index.py
  (canonical: file read this session, lines 1-90) is the pattern to
  mirror: `parse()` / `render()`/`update()` / `check()` / `main()` with
  a `--update` flag, CLI invoked as the script path plus an optional
  repo arg and optional `--update`, return-code 0 for the success
  case and 1 for the blocking case per its own docstring.
- gates/test_requirement_digest.py — new file, not yet present (derived:
  `ls gates/test_requirement_digest.py` — no such file); gates/test_accumulation.py
  existing (canonical: `ls gates/` output this session) confirms the
  naming convention `gates/test_<module>.py`.
- on-the-record/hooks/requirement-digest-preflight.sh — new file, not
  yet present (derived: `ls on-the-record/hooks/requirement-digest-preflight.sh`
  — no such file). on-the-record/hooks/spec-index-preflight.sh is the
  sibling pattern already wired.
- on-the-record/hooks/hooks.json — exists; canonical: file read this
  session — the `PreToolUse`/`Bash` matcher group lists
  `spec-index-preflight.sh` among its entries; this proposal appends one
  more entry to that same array.
- on-the-record/hooks/directive.sh — exists (canonical: SessionStart/
  UserPromptSubmit hook output visible in this session's own system
  reminders, produced by this exact script); one line naming the
  digest path will be added to its standing-directive text.
- gates/gates.py — exists; canonical: `sed -n '641,660p' gates/gates.py`
  output this session shows `requirement_registry` appends a message
  only when an entry's `check` path does not exist — it contains no
  write to a `status:` field anywhere in the function body inspected.
- gates/ci.py — exists; canonical: `grep -n requirement_registry gates/ci.py`
  output this session shows line 469 already calls
  `gates.requirement_registry(repo, {})`; this proposal adds a sibling
  call next to it for the new digest check function.
- spawn.py — exists; canonical: `sed -n '2313,2345p' spawn.py` output
  this session shows `_board_wide_sweep()` calling
  `closure_sweep.accumulation_trend()` and printing its result via
  `format_accumulation_trend()`, with an inline comment stating the
  call is advisory-only and excluded from `anomaly_count` (이슈 #512
  요구사항 4 comment, same function body). `requirement_drift()` will be
  added as a new function, called from the same site, following the
  same print-only, uncounted contract.
- docs/specs/enforcement-boundary.md — exists; canonical: `grep -n
  accumulation_trend docs/specs/enforcement-boundary.md` output this
  session, line 49 — the `closure_sweep.py`/`accumulation_trend()` row
  is the documented precedent this proposal's new row will match in
  shape (advisory, board-wide, non-blocking).
- harness/fixture-requirement-digest — new directory, not yet present
  (derived: `ls harness/ | grep requirement-digest` — no match).
  Sibling fixture directories exist under harness/ (derived: `ls harness/`
  output this session lists fixture-ambiguous, fixture-feature,
  fixture-infeasible, fixture-multimod, fixture-multirole,
  fixture-redtest, fixture-target, driver.py, signals.py, README.md,
  run_smoke.py) confirming the fixture-per-scenario pattern and the
  shared driver machinery this new scenario will plug into.
- tests/test_hooks_parity.py — existence not yet checked at survey
  time (open unknown below).

## req#7 constraint check (no CI/Actions, hook/plugin-only, default-on)

on-the-record/hooks/hooks.json is a plugin-shipped file under
on-the-record/hooks/, not under .github/workflows/ (derived: `ls
.github/workflows/ 2>&1` this session returns no matching directory in
the working tree read). The gates/ci.py addition is a CI-timing
backstop, mirroring gates/spec_index.py's own pattern: canonical:
gates/ci.py grep above shows spec_index's check already called from
gates/ci.py as a secondary/CI-timing call, and gates/spec_index.py's
own docstring (read this session) labels its no-flag mode "검사 모드
(기본, CI)" — a second timing, not the enforcement's primary path. The
commit-time hook stays the primary enforcement path in this design.

## Open unknowns for phase 2

- tests/test_hooks_parity.py — presence/shape not yet checked this
  survey; to check at build-start time. If it exists and enumerates
  hook filenames, the new hook name is added there in the same commit
  (still inside the frozen write set as a test file covering
  hooks.json).
