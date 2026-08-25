---
kind: decision-record
issue: 2286
role: implementation
---

# board-gate.sh R5 — author-identity migration (issue #2241 stage 3)

Deviation note: the stage-3 proposal
(`docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`)
names this doc's path as `docs/issue-2241/reports/architecture/board-gate-r5-migration.md`
(untracked, never created). This file stands in its place: this
session's write scope under `board-gate.sh` R4 (branch
`issue-2286/implementation`, role `implementation`) does not reach
`docs/issue-2241/...` (untracked from this branch).
canonical: Write tool call to `docs/issue-2241/reports/architecture/board-gate-r5-migration.md`
(untracked) from branch `issue-2286/implementation`, refused live with
"writing docs/issue-2241/ requires branch issue-2241/implementation
(current: issue-2286/implementation)".

## Fallback rule

`board-gate.sh` R5 (reports/ ownership) reads the record file's own
`author:` frontmatter field, not the writing session's role matched
against the record's filename.
canonical: `board-gate.sh` R5 section (the `for parts in issue_hits`
loop reading `_record_author`), as landed by this stage.

- A record that **carries** an `author:` field is owned by whoever that
  field names. The writing session may write it freely when its own
  identity matches; when it doesn't, the session may still append new
  content (a provable `>>`/non-truncating write) but may never alter the
  record's existing lines.
- A record that **carries no** `author:` field — because it predates
  issue #2241 stage 1, or because it does not exist yet and is about to
  be authored for the first time — falls back to the original rule
  unchanged: the writing session may write only its own
  `docs/issue-<n>/reports/<role>.md`, its own `<role>/**` subtree, and
  its one `EXTRA_SUBTREE` entry, if any.

Every record written before stage 1 carries no `author:` field and
keeps working under the same fallback branch the pre-stage-3 gate
already took.

## Cutover date

Stage 1 (issue-scoped lease, `author:` field, `kind:` vocabulary) landed
2026-08-25 (commit `470d5a1a`/`debe31c8`, PR #2317).
canonical: `git log -1 --format=%ci 470d5a1a` → `2026-08-25 13:28:15
+0900`; `directive_assembly.py`'s `_stamp_additive_record_fields` (the
single call site every `author:` stamp goes through) is the code this
date is tied to. Every record `spawn.py` writes from that date forward
is expected to carry an `author:` line.

## EXTRA_SUBTREE correction

In the same PR, `EXTRA_SUBTREE`'s `"feasibility"`/`"ops"` keys — not
present in `spawn.py`'s current `ROLES` tuple — were changed to
`{"technical-feasibility": "spikes", "release-engineering": "postmortems"}`,
matching `board.py`'s existing equivalent ownership check.
canonical: `spawn.py` `ROLES` tuple (grep for `"technical-feasibility"`,
`"release-engineering"`; neither `"feasibility"` nor `"ops"` appears as
an entry); `board.py`'s foreign-write-trace function (the
`rest.startswith("spikes/")` / `rest.startswith("postmortems/")`
branches).
