# issue #2241 stage proposals — path corrections (issue #2412)

This doc is the literal patch a session on branch `issue-2241/implementation`
(or a human, directly) needs to apply to
`docs/issue-2241/proposals/`. This session (branch `issue-2412/implementation`)
cannot make these edits itself — see
`docs/issue-2412/reports/implementation.md`'s "Rationale for deviations" for
why, and `gh issue comment 2241` (filed this session) for the same pointer
left where a future `issue-2241/implementation` session or a human will see
it.

## Stage 3 — `2026-08-25-stage-3-board-gate-author-identity.md`

Already spawned and landed under issue #2286 (PR #2387, core PR #319,
`docs/issue-2286/reports/implementation/board-gate-r5-migration.md`).

`files:` frontmatter, replace the untracked, never-created line

```
docs/issue-2241/reports/architecture/board-gate-r5-migration.md
```

with:

```
docs/issue-2286/reports/implementation/board-gate-r5-migration.md
```

"What will be done" bullet, replace the same untracked path's lead-in
(currently reading, in full: "docs/issue-2241/reports/architecture/board-gate-r5-migration.md
states the exact fallback rule above and the date after which every new
record is expected to carry author: (tied to stage 1's landing date, not
a fixed calendar date).") with:

```
- `docs/issue-2286/reports/implementation/board-gate-r5-migration.md`
  states the exact fallback rule above and the date after which every
  new record is expected to carry `author:` (tied to stage 1's landing
  date, not a fixed calendar date). Named under the delivering child
  issue's own tree, not this program issue's tree — `board-gate.sh`
  R4 (branch/tree scope) and R5 (role/report-subtree ownership) both
  forbid a session delivering one child issue from writing into a
  different issue's `docs/issue-2241/` tree or into another role's
  `reports/architecture/` subtree; see issue #2412 for the full
  reasoning. Already landed at this path.
```

## Stage 4 — `2026-08-25-stage-4-branch-record-naming-cutover.md`

Already spawned and landed under issue #2432 (PR #2436,
`docs/issue-2432/reports/implementation/in-flight-branch-migration.md`).

`files:` frontmatter, replace the untracked, never-created line

```
docs/issue-2241/reports/architecture/in-flight-branch-migration.md
```

with:

```
docs/issue-2432/reports/implementation/in-flight-branch-migration.md
```

"What will be done" bullet, replace the same untracked path's lead-in
(currently reading, in full: "docs/issue-2241/reports/architecture/in-flight-branch-migration.md:
states plainly — every branch open at this stage's landing time keeps
...") with:

```
- `docs/issue-2432/reports/implementation/in-flight-branch-migration.md`
  (delivering child issue's own tree, per the same R4/R5 reasoning as
  stage 3 above — see issue #2412): states plainly — every branch open
  at this stage's landing time keeps
```

(the rest of that bullet's text is unchanged).

## Stages 5 and 6 — no change needed

`docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md` and
`docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md` name no
docs/issue-2241/ destination anywhere in their files: list or body —
checked live this session (`grep -n "docs/issue-2241"` against both files,
no match). Stage 5's own doc destination is a standing bucket path
(docs/handbooks/, untracked until stage 5 lands, but unrestricted by
`board-gate.sh` R3/R4/R5 regardless of which branch writes it); whatever
child issue eventually delivers stage 5 or 6 can write its named
destination without any of this issue's problem arising. No amendment
needed for these two proposals.
