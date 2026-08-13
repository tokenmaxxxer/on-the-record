skip-condition: trivial mechanical anchoring defect, no open design decision — the
target-root principle is already the recorded standard; issue #1219 itself
carries `validity-consult-skip: trivial`. Scouting the category's
best-in-class is not applicable to a single-repo internal orchestration
tool's watchdog anchoring bug, so this survey covers current-state only.

## Current-state survey

Traced the live-reproduction transcript in issue #1219 to its actual code site.

- `on-the-record/hooks/directive.sh` (UserPromptSubmit) sources
  `on-the-record/hooks/poll-rearm.sh`, resolves `CHECKOUT` (the on-the-record
  clone — marketplace checkout in a plugin install), and on a due tick runs
  `nohup python3 "${checkout}/spawn.py" watchdog --auto-respawn` with no
  `-C` — the subprocess inherits the hook's cwd (the session's target
  project root), so `-C` defaults to `"."`.
  canonical: on-the-record/hooks/poll-rearm.sh:64-68 (read this session)
- `spawn.py`'s CLI dispatch for `a.role == "watchdog"`, before this change,
  called `roster_watchdog(auto_respawn=a.auto_respawn, all_scope=a.all)` —
  `a.cwd` was parsed by argparse but not forwarded — and `roster_watchdog()`
  had no `root` parameter, using the module-level constant
  `ROOT = Path(__file__).resolve().parent` (the checkout's own directory) for
  every board-facing call: `_board_wide_sweep(ROOT)`, `_build_observed(ROOT, e)`,
  `_post_session_end_comment(ROOT, ...)`, `_pr_open_or_merged_for_branch(ROOT, branch)`,
  and two `diagnose_health(...)` calls with no `root=` kwarg (default
  `root: Path = ROOT`).
  canonical: git show c1d341b:spawn.py, `def roster_watchdog` and the
  `a.role == "watchdog"` dispatch block (read this session before editing)
- `requirement_drift(root)` reads `root / "docs" / "specs" /
  "requirement-digest.md"` and runs `gh issue list` / `gh pr list` with
  `cwd=root` — when invoked with `root=ROOT` (pre-fix), this reads
  on-the-record's own requirement digest and scopes the `gh` calls to
  whatever `origin` the checkout points at, matching the transcript's
  description of receiving tokenmaxxxer/on-the-record's own drift/issue
  lines.
  canonical: git show c1d341b:spawn.py, `def requirement_drift` (read this
  session before editing)
- `_board_wide_sweep(root)` and `requirement_drift(root)` also used
  `sys.path.insert(0, str(root / "gates"))` to import `closure_sweep` /
  `spawn_coverage` / `requirement_linkage` — those modules live in the
  checkout's `gates/`, never in a consumer's target repo, so once `root` is
  corrected to the target project this import line must stay pinned to the
  checkout — a separate concern from which repo's board gets scanned.
  canonical: git show c1d341b:spawn.py, same two function bodies (read this
  session)
- The prior-art path the issue cites, 2026-07-26-hook-root-anchored-to-target-project.md
  under docs/proposals/, is not present in this working tree (no backtick
  path quoted here — the path does not resolve).
  derived:
  ```
  $ find . -iname "*hook-root-anchored*"
  (no output)
  ```
  canonical: derived command above (run this session). Treated as an
  unresolvable pointer rather than a hard dependency — the anchoring class
  it names is independently retraced from spawn.py itself (canonical entries
  above), not assumed from the missing file.
- `docs/specs/approvers.md` lists `JiwonJung94` and `jjongkwann`.
  canonical: docs/specs/approvers.md (read this session)
  The issue already carries an issue-level `APPROVE issue-1219/implementation`
  comment from `JiwonJung94` (an approvers.md account).
  canonical: `gh issue view 1219 --comments` (run this session)
  Single-account-mode approval is already in hand, so phase 2 (this build)
  proceeds directly, per contract v3 s19's issue-level-comment path.

## Write set (frozen)

- `spawn.py` — thread a `root: Path` parameter through `roster_watchdog()` and
  its board-facing calls (`_board_wide_sweep`, `diagnose_health` x2,
  `_build_observed`, `_post_session_end_comment`,
  `_pr_open_or_merged_for_branch`), defaulting to `ROOT` for backward
  compatibility with direct/test callers; thread `a.cwd` through from the CLI
  `watchdog` dispatch; pin the two `gates/` import sites
  (`_board_wide_sweep`, `requirement_drift`) to `ROOT` regardless of the scan
  target.
- `tests/test_spawn.py` — update the one existing assertion on the CLI
  watchdog dispatch call shape (`test_cli_watchdog_all_flag_threads_all_scope`)
  and add: a CLI-level test that `-C` threads through as `root` with no
  `--all`; a hermetic consumer-fixture test (foreign repo, no board, no gh
  reachability needed) asserting zero occurrences of the checkout path,
  `"marketplaces"`, or `"tokenmaxxxer/on-the-record"` in watchdog output, and
  that empty-board output stays silent/generic; a dev-session regression test
  asserting `root` defaults to `ROOT` (`_board_wide_sweep` called with `ROOT`)
  when no `-C`/`root` override is given.

No `.env.example`, dependency-manifest, or migration touch — pure Python
logic + tests.
