---
proposal: PR #2445 CHANGES round 2 (issue #2381) — untrack .orchestrate-hook-fires.log and .orchestrate-hook-fires/
---

# Hunt record — untrack-orchestrate-hook-fires

## after-proposal — stance 1: untracking .orchestrate-hook-fires{.log,/} breaks a git-facing reader/checker elsewhere

Verdict: NO FINDING
Seed: commit d74a24a9 — `git rm --cached .orchestrate-hook-fires.log` and `-r .orchestrate-hook-fires/`, plus matching `.gitignore` entries; working-tree files left in place.
cap_seconds: n/a (not provided by dispatcher)
tier: n/a (not provided by dispatcher)
diff_stat_lines: 15 files changed, 126 insertions(+), 3359 deletions(-)
started_at: 2026-08-26T12:30:00+09:00
ended_at: 2026-08-26T13:05:00+09:00

Checked and found nothing:
- `hook_fires.py`'s `_hook_fires_dir`/`_hook_fires_aggregate` (only readers besides
  `hook-fires.sh` itself) resolve strictly from `cwd`/live filesystem; grepped the whole
  tree for `_hook_fires_aggregate`/`.orchestrate-hook-fires` — only caller is
  `spawn.py`'s `hook-fires` CLI role, also cwd-based. No `git show`/worktree-of-another-ref
  read exists anywhere.
- `gates/test_generated_paths.py` and `gates/test_boundary.py` (the two gates that cross-check
  `docs/specs/generated-paths.md`/`enforcement-boundary.md`) both already fail on
  `HEAD~1` (before this commit) with the *identical* failure set (`fail-open-wrapper.sh`
  unrecorded, `hook-fires.sh`/`skill-verdict-guard.sh`/`stop-poll-rearm.sh` classified
  `n/a`, several `.py` gates unrecorded in `enforcement-boundary.md`) — this commit
  changes neither doc, so it introduces zero new failures there. Reproduced via
  `python3 gates/test_generated_paths.py` / `python3 gates/test_boundary.py` on both
  HEAD and HEAD~1 (identical stderr).
- `python3 gates/spec_index.py .` passes — `docs/specs/generated-paths.md`/
  `enforcement-boundary.md` content is unchanged by this commit, so the reconciled-index
  hash check has nothing to drift on.
- Neither spec doc's hook-fires row asserts anything about git-tracked-ness of the shard
  directory (checked via grep for "tracked"/"gitignore" in `docs/specs/*.md` — no hits),
  so there is no doc claim this commit contradicts.
- The two removed shard files this branch itself added (`2cfde9a1f735d756b8e80c6b.log`,
  `9f5feb13badaeb330dfcc6e1.log`) are referenced by literal hash only in
  `docs/issue-2381/reports/implementation.md` (a report, not code/config that reads them).
- `deviation-log-guard.sh`'s `git status --porcelain` fallback (needed because sharded
  files start as untracked "??") is scoped to `docs/issue-<n>/reports/<role>/deviation-log/`
  paths, never `.orchestrate-hook-fires/` — confirmed by grep, no shared code path with
  the hook-fires reader.
- `on-the-record/hooks/test_hook_fire_counter.py` (5 passed, per dispatcher) and
  `tests/test_spawn_consult_panel.py`'s hook-fires tests both operate on `tmp_path`/`cwd`
  args, never assert git-tracked state.

No reproduction found; stopping.
