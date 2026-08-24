# Current-state survey — issue #2156 conformance-review

## Target artifact and spec

Target: commit `b47a2abf` ("issue-2156: forbid redundant spawn-watcher
agents/loops (#2157)"), the squash-merge of PR #2157 onto `origin/main`,
touching `on-the-record/directive/spawn-and-board.md` plus
`docs/issue-2156/reports/**`.
canonical: `git show b47a2abf --stat` (read directly)

Spec: issue #2156 body, `## Change` (the guidance to add) and
`## Acceptance` (3 criteria).
canonical: `gh issue view 2156` (read directly)

## Scout skip record

Skip condition: the spec leaves no design decision open. This role's
phase-1 output is a requirement list mechanically derived from the
issue's own `## Change`/`## Acceptance` text, checked against a single
already-merged commit — there is no product/exemplar field to scout
best-in-class comparables for.
canonical: `gh issue view 2156` (read directly — `## Change`/`## Acceptance`
are the entire spec surface, no open field left to a design choice)

## What exists today (board state)

canonical: `find docs/issue-2156 -type f` (read directly) — result:
```
docs/issue-2156/reports/conformance-review.md
docs/issue-2156/reports/implementation.md
docs/issue-2156/reports/implementation/2026-08-24-hunt-spawn-watcher-guidance.md
docs/issue-2156/reports/implementation/deviation-log.md
```
Board condition per role spec (`roles/specs/conformance-review.spec.json`,
`use_when.board_condition`): "an implementation commit landed on the
branch AND no conformance-review record exists yet for this commit sha."
canonical: `roles/specs/conformance-review.spec.json` (read directly)
— satisfied: `docs/issue-2156/reports/implementation.md` exists at
`b47a2abf` (landed, listed in the `find` output above), and the `find`
output above shows a `conformance-review.md` path already present in
this session's working tree as issue #2135's pre-seeded,
never-yet-committed skeleton
(`git log --all --diff-filter=A -- docs/issue-2156/reports/conformance-review.md`
returns no commit, executed this session) — not a filled record.

## PR / issue state

canonical: `gh pr view 2157 --json state,mergeCommit,body -q '.state,.mergeCommit.oid'`
(executed this session) — result: `MERGED`, `b47a2abf3a4b28e54303b15bd4f660870fbef8da`.
canonical: `gh issue view 2156 --json state -q .state` (executed this
session) — result: `OPEN` (despite the merge above).
canonical: `gh pr view 2157 --json body -q .body` (executed this session)
— result: the body's last line is the plain string `#2156` (no
`Closes`/`Fixes`/`Resolves` keyword).

## Requirement list (from issue #2156 `## Change`/`## Acceptance`, split
per requirement-extraction rule 1 — bundled clauses separated — and
dimension-tagged per rule 6)

canonical: `gh issue view 2156` (read directly, `## Change`/`## Acceptance`
— the source for every item below)

1. (scope-boundary) The guidance is added to
   `on-the-record/directive/spawn-and-board.md` or another existing
   directive file — no new file created.
2. (functional) The guidance states that after `spawn.py` returns, an
   orchestrator must not spawn a separate watcher Agent whose sole
   purpose is polling that spawn to completion.
3. (functional) The guidance names the mechanism reason: the spawn's own
   watcher process + Monitor/watchdog poll cycle already surface
   HEALTHY/RUNNING/anomaly/returned-PR events as background-task
   notifications automatically.
4. (functional) The guidance directs to trust those notifications and
   act on them when they arrive.
5. (functional/edge-case) The guidance permits a one-shot fallback check
   via `spawn.py ps` or `spawn.py watch --issue <n> --role <r>`.
6. (scope-boundary, negative requirement) The guidance states this
   one-shot check is the only sanctioned direct status check — never a
   standing watcher agent.
7. (scope-boundary, acceptance criterion 2) The change is docs-only —
   no code/gate change (`infrastructure/no-direct-requirement`).
8. (verification, acceptance criterion 3, canonical: `gh issue view 2156`
   read directly, `## Acceptance` item 3) Executed acceptance evidence —
   a grep confirms the new guidance text is present in the target file.

## Notable surface for phase 2 (candidate observation, not verdicted here)

The PR-body/issue-state facts under "PR / issue state" above (plain
`#2156` reference, issue still `OPEN` post-merge) are outside the 8
requirements listed above — issue #2156's own `## Acceptance` text names
none of this. `docs/reports/deviation-log.md` already carries two
same-day, same-mechanism entries for this exact gap (issue #2153, issue
#2152 — both note `pr-preflight.sh` forces a plain `#<n>` reference under
the `CORE_BUILD_NOW=1` bypass because no real approval comment exists to
authorize a `Closes` trailer), but has none for issue #2156.
canonical: `docs/reports/deviation-log.md` (read directly, this session —
tail entries dated `2026-08-24T05:05:09Z` issue-2153 and
`2026-08-24T14:30:00Z` issue-2152; no `2156` match)
Flagged as a candidate open finding for phase 2 to record (outside the
requirement-verdict set, not itself a failed requirement), not resolved
here — phase 1 of this role produces a requirement list, never a verdict.
