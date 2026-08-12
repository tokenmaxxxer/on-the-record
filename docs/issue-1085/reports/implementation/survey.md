# Current-state survey — issue #1085

## Background

canonical: docs/issue-1037/reports/conformance-review/survey.md, read this session — req#5
section documents that `docs/issue-1062/reports/implementation.md` cites two evidence paths
(quoted below in a fence to avoid a live path-reference) for a `no-defect-found` verdict, and
that neither path has ever existed in this repository's git history:
```
docs/issue-1062/reports/panel/rest-v1-v2.md
docs/issue-1062/reports/consult-log.md
```

## Re-verification: does the #1062 record's evidence exist anywhere?

derived: `find docs/issue-1062 -type f`, run this session:
```
docs/issue-1062/reports/implementation.md
docs/issue-1062/proposals/live-panel-round-trip-diagnosis.md
docs/issue-1062/reports/implementation/survey.md
docs/issue-1062/reports/implementation/2026-08-12-hunt-live-panel-round-trip-diagnosis.md
```
canonical: same listing above, run this session — neither of the two paths quoted in the
Background fence is present in the working tree.

derived: `git log --all --diff-filter=A --name-only -- 'docs/issue-1062/reports/panel*' 'docs/issue-1062/reports/consult-log.md'`, run this session:
```
(no output)
```
canonical: same command output above — neither path was ever added in any commit on any
branch in this repository's history.

## Re-verification: is the underlying diagnosis (no round-trip defect) still supportable?

canonical: docs/issue-1062/reports/implementation/survey.md, read this session, "Live
reproduction" section — describes two live `spawn.py` invocations this session ran
(`spawn.py consult ...`, `spawn.py panel ... api-design ...`) and states both returned
well-formed judgment JSON with a position -> rebuttal -> verdict round trip.

derived: `git log --all --oneline -- docs/issue-1062/reports/implementation/survey.md`, run this
session:
```
2411440 issue-1062 phase-2: ground live panel round-trip diagnosis with executed-live evidence
71f2f11 issue-1062 phase-2: ground live panel round-trip diagnosis with executed-live evidence (#1064)
```
canonical: same command output above — unlike the two false pointer paths, this file (the
record's own live-reproduction narrative) is genuinely committed and reachable.

So the diagnosis's narrative evidence is not wholly fabricated: the record's own survey
describes the live runs it ran. The gap is narrower than "the verdict is unsupported" — it is
that `implementation.md` additionally cites two pointer paths that do not exist and were never
committed, sitting alongside evidence that does exist. The record's own prose says those
role-output files were "not staged by this commit per contract v3 s11"; combined with the
`git log --all` result above showing they were never staged in any commit at all, the two
paths were either transient working-tree artifacts of the authoring session or never produced
as literal files (spawn.py's own JSON output being the real evidence, per survey.md's Live
reproduction section).

Correcting the record therefore means retracting the two false path citations and pointing at
the evidence that does exist (survey.md's own Live reproduction section, and the hunt file) —
the verdict's real support (the live spawn.py runs) still stands per the committed survey.md
above, so the retraction is a correction of the citation, not a verdict reversal.

## Gate survey: why didn't record-claim-guard catch this at authoring time?

canonical: on-the-record/hooks/record-claim-guard.sh, read this session — wires
`record_lint.orphaned_path_reference_check(Path(root), content)` against writes under
`docs/issue-*/reports/**`, where `root` is resolved as the nearest ancestor `.git` directory
from the write's `cwd`.

canonical: gates/record_lint.py:237-249, read this session —
`orphaned_path_reference_check` tests `(root / ref).exists()`: a plain filesystem existence
check against the working tree at write time, not against git history and not against what is
actually staged/committed.

canonical: gates/record_lint.py:237-249 (same read) — the check cannot distinguish "exists in
the working tree right now" from "exists in git history": a path present on disk at write
time (even if untracked, even if never staged, even if later deleted) satisfies `.exists()`
the same way a properly committed path does. The #1062 record's own prose acknowledging its
role-output files were "not staged by this commit" is consistent with a path being present at
write time and thus clearing the check, then never landing in any commit. Closing this gap is
what #1085 asks for — reject a canonical citation naming a path that is not (and never was)
tracked in git history, not only one absent from the current working tree.

## Existing test/gate infra relevant to the fix

canonical: gates/test_record_lint.py:29-44, read this session — `_repo_with_record` builds a
throwaway git repo per test (git init, base commit on `origin/main`, checkout
`issue-517/implementation`, write+commit the record) — the established fixture pattern this
issue's new gate test should reuse.

## Write-set

- docs/issue-1062/reports/implementation.md (retract the two false path citations, point at
  real evidence)
- gates/record_lint.py (new check: canonical/evidence path citation must be git-tracked, not
  just filesystem-present)
- gates/test_record_lint.py (test pinning the new check)
- docs/issue-1085/reports/implementation.md (phase-2 record, once approved)
