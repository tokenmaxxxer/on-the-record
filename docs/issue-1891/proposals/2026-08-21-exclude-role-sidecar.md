---
status: proposed
files:
  - spawn.py
  - test/test_branch_role_field.py
---

## Request

Make `spawn.py` write `.on-the-record/role.json` such that git never
stages it: add `.on-the-record/role.json` to the workspace's
`.git/info/exclude` at sidecar-write time, workspace-local, no repo
`.gitignore` change. Add a regression case to
`test/test_branch_role_field.py` proving `git status --porcelain` in the
workspace omits the sidecar after a write.

## Constraints

- No repo-tracked `.gitignore` change (issue requirement 1: workspace-
  local exclude only).
- Sidecar JSON format and every reader untouched (issue non-goal).
- Fail-open on write failure, matching `_write_role_sidecar`'s existing
  OSError handling — an exclude-write failure must not block the sidecar
  write or halt the spawn.
- The fix must cover all 3 call sites of `_write_role_sidecar`
  (spawn.py:7684, 7708, 7753 per the survey), not only the fresh-clone
  path the existing dotfile-leak exclude block covers.

## Rationale

The survey found a working precedent for exactly this mechanism already
in `issue_workspace()`'s fresh-clone branch (spawn.py:7717-7745,
issue #289 H1): append-only-if-missing lines to
`work / ".git" / "info" / "exclude"`. Two alternatives were considered
and rejected:

1. **Extend the existing `lines` list at spawn.py:7720 to include
   `.on-the-record/role.json` and stop there.** Rejected: that block
   only runs on the fresh-clone path (before `_write_role_sidecar` is
   called at spawn.py:7753). The survey's call-site enumeration shows
   the other two call sites (spawn.py:7684 reused src==work,
   spawn.py:7708 reused separate work dir) call `_write_role_sidecar`
   directly with no exclude step — exactly the PR #1890 shape (an
   already-cloned/reused workspace, sidecar written on a later spawn or
   respawn). Fixing only the fresh-clone list would leave the reuse
   paths, which is where the actual near-miss happened, still exposed.
2. **Add the exclude entry inside `issue_workspace()` at each of the 3
   call sites, right before/after calling `_write_role_sidecar`.**
   Rejected: triplicating the same exclude-write logic at 3 call sites
   is more surface for one site to drift or be missed on a future edit
   (the exact failure mode that produced this issue's gap in the first
   place — the fresh-clone-only block already drifted out of sync with
   the sidecar's own introduction in issue #1814). A single write point
   inside `_write_role_sidecar` itself is structurally guaranteed to run
   on every call site, present and future, without relying on every
   caller remembering to add it.

Chosen instead: move the exclude-write into `_write_role_sidecar` itself,
so it runs unconditionally at the one place the sidecar is actually
written, covering all 3 call sites by construction rather than by each
caller remembering to add it. The existing fresh-clone dotfile-leak
exclude block (spawn.py:7717-7745) is left as-is — it still serves its
original purpose for the other listed paths, and this issue's non-goal
scope keeps the change to the sidecar site only.

## Accumulation

The change adds one more `.git/info/exclude` write inside
`_write_role_sidecar`, alongside the pre-existing separate exclude write
in the fresh-clone branch (spawn.py:7717-7745). This is not a growing
inline list: `_write_role_sidecar` gets exactly one new fixed-length
append (`.on-the-record/role.json`, a single line), not a list that
grows per future sidecar or per future exclude-worthy path. If a future
issue needs another workspace-local file excluded, it would extend the
existing fresh-clone `lines` list (already the established home for
untracked-local exclude entries) or add its own single append at its own
write site — this proposal does not introduce a new per-N-items pattern
that would need consolidating if repeated; two independent
`.git/info/exclude` write points (one per concern: dotfile-leak
prevention vs. sidecar staging) is the same shape the repo already
carries today and does not compound with further additions.

## What will be done

1. In `_write_role_sidecar` (spawn.py:7625-7639), after successfully
   writing `role.json`, append `.on-the-record/role.json` to
   `work / ".git" / "info" / "exclude"` if not already present
   (read-existing-then-append-missing, same idempotent shape as the
   existing dotfile-leak block) — inside the same `try`/`except OSError`
   already wrapping the write, so an exclude-write failure prints the
   existing fail-open warning and does not raise.
2. Add a new regression case to `SidecarWriteShapeTest` in
   `test/test_branch_role_field.py`: `git init` a temp dir, call
   `spawn._write_role_sidecar`, run `git status --porcelain` in that
   dir via `subprocess.run`, and assert the sidecar path does not appear
   in stdout.
3. Run the case live and paste its output in this issue's phase-2
   record (acceptance check requires "executed live and pasted in the
   record").

## Out of scope

- Sidecar JSON format or content.
- Any reader of `.on-the-record/role.json` (the 3 shell hooks or
  `gates/flows.py`).
- The pre-existing dotfile-leak exclude block's own list or logic
  (spawn.py:7717-7745) — left unmodified, still runs on the fresh-clone
  path for its original purpose.
- Retroactively cleaning `.git/info/exclude` in already-existing
  workspaces created before this fix (including this session's own
  workspace) — the fix only guarantees new/future sidecar writes are
  excluded.

## How you'll know it worked

`python3 -m pytest test/test_branch_role_field.py -q` passes including
the new case, executed live; the new case's `git status --porcelain`
assertion directly demonstrates the workspace omits the sidecar after a
write, matching the issue's acceptance check verbatim.
