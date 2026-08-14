# Conformance review — issue-450 surface exclude-guard write failure

## Upstream / basis

Requirement list: `docs/issue-450/proposals/2026-08-08-surface-exclude-guard-write-failure.md`
(its Constraints and build-plan sections).
canonical: the proposal file above, read this turn.

Reviewed artifact: PR #454, commit `df95ab46`, `spawn.py`
`issue_workspace()` (current `spawn.py:5905-5928`).
canonical: spawn.py:5905-5928, read this turn.

Also reviewed: the repro test in `tests/test_silent_failure_repros.py`
and the implementation record's own header.
canonical: tests/test_silent_failure_repros.py and
docs/issue-450/reports/implementation.md, both read this turn.

Approved via `APPROVE issue-450/conformance-review` (issue #450 comment,
account JiwonJung94, single-account mode).

## What was done

Artifact-only re-read of `issue_workspace()`'s exclude-guard write block
against the proposal's stated requirements; ran the target repro test as
evidence.

```
$ python3 -m pytest tests/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning -q
1 passed in 0.31s
```
canonical: `python3 -m pytest tests/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning -q`, executed this turn (output above).

One verdict rendered per requirement below.

## Verdicts

**R1 — On exclude-guard write failure, surface a warning naming the
workspace and the skipped entries: Present.**
canonical: spawn.py:5915-5928, read this turn.
```
    skipped = lines
    try:
        ex.parent.mkdir(parents=True, exist_ok=True)
        existing = ex.read_text() if ex.exists() else ""
        missing = [ln for ln in lines if ln.rstrip("/") not in existing]
        skipped = missing
        if missing:
            with ex.open("a") as fh:
                for ln in missing:
                    fh.write(ln + "\n")
    except OSError as e:
        print(f"경고: 워크스페이스 {work} 의 자격증명 유출 방지 exclude 항목을 "
              f"쓰지 못했다 ({e}) — 빠진 항목: {', '.join(skipped)}",
              file=sys.stderr)
```
Both the workspace path and the skipped-entry list (`missing`, or the
full `lines` list if the failure happens before `missing` is computed)
are in the one warning line.

**R2 — On write success, behavior unchanged: Present.**
canonical: spawn.py:5916-5924 quoted above, read this turn — the `try`
block's happy path is untouched by the fix; only the `except` arm was
edited, from a no-op body to the print statement. No separate regression
risk was added since no happy-path line changed.

**R3 — `issue_workspace()` still returns a workspace on write failure
(non-fatal, not `sys.exit`): Present.**
canonical: spawn.py:5925-5939, read this turn — the `except OSError as e:`
arm only prints and falls through (no `sys.exit`/`raise`), and execution
reaches the `subprocess.run(...credential.helper...)` call and the final
`return str(work)`, matching the proposal's explicit choice of a
non-fatal warning over refusing the spawn.

**R4 — Repro test updated to assert the surfaced warning, not its
absence: Present.**
canonical: tests/test_silent_failure_repros.py lines 51-85 (function
`test_attempt_1_exclude_write_swallowed_no_warning`), read this turn:
```
    assert str(work) in captured.err
    assert ".mcp.json" in captured.err
    # FIXED: issue_workspace() still returns a workspace (no sys.exit, no
    # exception), but the skipped credential-exclude guard is now surfaced
    # as a warning on stderr naming the workspace and the missing entries.
```
No assertion in the test still checks for the warning's absence.

**R5 — Test file path from the proposal's Constraints vs. actual
location: divergence noted, not a fidelity failure.**
canonical: `find . -iname "test_silent_failure_repros.py"`, executed
this turn — the only match is `tests/test_silent_failure_repros.py`
(plural `tests/`). The proposal's Constraints and Out-of-scope sections
instead spell the directory singular ("test/..."), which resolves
nowhere in the working tree. The correct, actually-existing file is the
one the implementation edited — this is a path-string typo in the
proposal document, not a gap in what was built.

## Why

Per-requirement fidelity verdicts, artifact-only, per the
conformance-review role's rulebook (never a holistic quality read, never
a fix).

## What did not work

None.

## loop_state

kind: review-record
loop_state: draft-reported

## Open findings

- **R5 — proposal path-string mismatch (not itself a fidelity
  failure).** The phase-1 proposal spells the repro-test directory
  singular ("test/..."); the repo's actual directory is `tests/`
  (plural). canonical: `find . -iname "test_silent_failure_repros.py"`,
  executed this turn (see R5 above). Addressed to: proposal-authoring
  convention for this issue's own record only — no code or test impact,
  since the implementation role correctly located and edited the real
  file at `tests/test_silent_failure_repros.py`.

## Next steps

canonical: `python3 -m pytest tests/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning -q` — result: 1 passed in 0.31s, executed this turn.

Verdict tally: Present for R1, R2, R3, R4; R5 is a documentation
path-string note, not a Present/Incorrect verdict. Overall: issue #450's
delivered fix (PR #454) matches its proposal's stated requirements — no
Incorrect or Absent findings against the built code or test. No findings
block treating #450 as conformant.

## Resolution path

None required — R5 is a cosmetic path note in the proposal document with
no behavioral consequence; no resolution action is needed for #450 to be
considered conformant.
