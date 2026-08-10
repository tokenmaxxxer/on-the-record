# Issue #651 — Survey: board-gate.sh substring matching vs. resolved write targets

## Scope

Phase-1 research only. No code changes in this commit.

## Scout skip record

Pure bugfix (scout-directive skip condition 1): the acceptance criterion is
fixed by the issue itself ("commands merely MENTIONING board paths pass;
actual writes to foreign records still refuse"), and the fix is a localized
correction of existing gate logic to match its own documented intent — no
open product-shaped design decision to scout best-in-class exemplars for.
Scouting skipped for this reason.

## Cross-repo location (repeats issue-40's finding)

`board-gate.sh` does not exist anywhere in this repo (`tokenmaxxxer/on-the-record`,
this session's own tree/branch/sandbox). It lives in the separate repo
`tokenmaxxxer/tokenmaxxxer-core`, confirmed present and readable (but not
writable — outside this session's sandboxed write scope) at:

- `/home/jwjung/tokenmaxxxer-core/core/hooks/board-gate.sh`

This is the exact cross-repo blocker issue-40's own coding record already
recorded: that phase-2 session discovered mid-build that its approved write
set (the gate script and its shell test harness) resolved to files outside
its repo/sandbox and could not deliver a code change from a
muster-scoped (predecessor of this on-the-record) session. Recording it
here in phase 1, before any build attempt, so phase 2 does not repeat that
discovery cost.

## The bug, read directly off the current file

`board-gate.sh` (PreToolUse Bash/Write/Edit gate) builds a list of write
"hits" — path tails under the board's docs directory — from two paths:

- Write/Edit/MultiEdit/NotebookEdit: the tool payload's own resolved target
  path (`ti.get("file_path")`).
- Bash: text-scanned candidate tokens taken from the actual write-target
  window of a failing segment (the string right after a real redirect
  operator, or a `tee` argument, via the existing `_write_target_windows`
  helper).

Both paths feed into the existing `_docs_relative_tail()` helper, which
looks for the literal substring "docs/" anywhere in the normalized token
and, if found, treats everything after it as a board-relative path —
regardless of whether the token, resolved as an actual filesystem path, is
anywhere near this repository's root. The existing `root_of()` helper
resolves the actual repo root (`CLAUDE_PROJECT_DIR` or `git rev-parse
--show-toplevel`), but that root is never consulted when the hit list is
built — only afterward, to build the approvers-file marker path and later
branch/ownership checks. An absolute-path token that legitimately contains
a "docs/" component but lives entirely outside the resolved root (e.g. a
`/tmp/...` scratch path with its own unrelated docs subdirectory) is
misread as a same-repo board write.

### Confirmed repro (already fenced in issue #628's hunt record)

Issue #628's execution-observation report's hunt table, the board-gate.sh
row: a Write/echo to a path under a `/tmp/claude-1000/...` fixture
directory — not under this repo at all — that happened to contain a docs
component was denied with the same layout-refusal message a real in-repo
foreign write would get. The target path never resolved anywhere near this
repo's root; the gate fired on the command-text substring alone.

### The opposite direction issue #651 also asks to preserve

The existing `_write_target_windows` helper already narrows Bash candidate
extraction to the real write-target window so that a board-path-shaped
string sitting only in echoed/grepped commentary text (not itself a write
target) is not misread as a write candidate — e.g. `echo "see <board path>
for context" > /tmp/notes.txt` already resolves its write target as
`/tmp/notes.txt`, not the echoed string. That existing correctness must not
regress; issue #651's own acceptance criterion repeats it as one half of
the red/green pair ("commands merely MENTIONING board paths pass"). The
remaining, unfixed half: once a real write-target token IS correctly
extracted, the gate still never checks whether that token resolves under
the repo root before treating it as a board hit.

## Projected write set (contingent on repo access — see below)

- `core/hooks/board-gate.sh` — narrow the hits-extraction path so an
  absolute-path candidate is only treated as a board hit when its
  normalized path actually falls under the resolved repo root; a relative
  candidate (no reliable resolution without a full shell cwd model) keeps
  today's honest text-scoped behavior, unchanged.
- `core/hooks/tests/run-board-gate-tests.sh` — new regression scenarios:
  - an absolute out-of-repo path containing an unrelated board-shaped
    directory component is allowed (green)
  - an actual foreign-record write inside the repo (the existing
    reports-ownership rule) still refuses (red, unchanged)
  - the mention-only scenario (echoed/grepped board-path text) still
    allowed (must not regress)

These are files in `tokenmaxxxer/tokenmaxxxer-core`, not in this repo. This
session's write access is confined to this repo/branch
(`tokenmaxxxer/on-the-record`, `issue-651/implementation`); the sandbox
allows reading the core-repo tree but not writing to it (confirmed: file
read succeeded, `cd`/write attempts into that tree are rejected by the
sandbox policy, matching issue-40's recorded blocker exactly). Delivering
the actual code+test change requires a session scoped directly to
`tokenmaxxxer/tokenmaxxxer-core` with its own issue/branch/PR.
