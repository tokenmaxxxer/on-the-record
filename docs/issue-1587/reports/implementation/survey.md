# Survey — issue #1587 judge transport

## Write set under survey
- spawn.py (new verb: `judge <role> --merge <sha> [-C <repo>]`, cmd assembly, trace)
- gates/patrol_queue.py (reuse `enqueue()` with lane="diff"; canonical: gates/patrol_queue.py:65-97 read in full this session)
- docs/handbooks/spawn.md (new verb doc)
- a new trace-always log file at docs/reports/patrol-judge-log.md, not present in the
  tree yet — created by this build, consult-log convention
- test/ coverage for the above (subprocess-mocked, existing spawn test conventions)

## Existing sibling transports (consult/verb family)
- `consult_cmd()` spawn.py:5207 is the closest sibling: read-only-by-contract session
  (no branch/commit/PR), reuses `role_settings()`/`plugin_dirs()` for rulebook loading,
  writes a trace line in a `finally` block regardless of success/failure
  (canonical: spawn.py:5290-5296 read in full this session).
- `_consult_cmd_and_env()` spawn.py:5167 is the argv/env/settings-file builder factored
  out of `consult_cmd()` for reuse by sibling verbs (canonical: docstring spawn.py:5167-5184).
- `_verb_cmd()` spawn.py:5340 generalizes consult into ideate/draft/review by varying
  only prompt instructions + required JSON key (canonical: spawn.py:5299-5321,
  spawn.py:5340-5410 read in full this session). It spawns exactly one `claude -p`
  session and returns one JSON verdict, with no relevance-prefilter stage, no
  diff-compression stage, no second validator stage, and no patrol_queue write.
  Judge's own pipeline (prefilter, then judge, then validator, then enqueue — four
  stages) has no analog in `_verb_cmd`'s single-call loop, so judge needs its own
  `judge_cmd()` reusing `_consult_cmd_and_env()` for session assembly only.

## Read-only session construction (R1 — git plumbing only, no Write/gh)
- `role_settings()` spawn.py:491 and `plugin_dirs()` spawn.py:341 are the existing
  sandbox-boundary and rulebook-loading helpers every verb already goes through
  (canonical: spawn.py:341-364, spawn.py:491 read this session).
- `_consult_cmd_and_env()` spawn.py:5185-5196 always appends `core_plugin_dirs()`
  (spawn.py:4830) to the session's `--plugin-dir` list. The issue's design section
  states judge's isolation must happen "at plugin-dir selection, NOT #1097-style
  prompt suppression" — consult and the verb family instead suppress those hooks via
  an in-prompt override string (canonical: spawn.py:5243-5249, spawn.py:5361-5366 —
  this override text is the prompt-suppression pattern the issue names as
  insufficient for judge). No existing helper filters `core_plugin_dirs()`'s output
  by delivery-vs-read-only purpose (derived: `grep -n "core_plugin_dirs\|delivery" spawn.py`
  shows only the single definition at spawn.py:4830 and its call sites, no filter
  variant) — this filter is new code for judge, operating on the same discovered
  list `core_plugin_dirs()` returns rather than reimplementing plugin discovery.
- `_workspace_bash_allow()` spawn.py:471-488 is the existing precedent for scoping a
  Bash allow-list to specific command prefixes; judge's "git show/diff/log only, no
  gh" restriction follows the same allow-list shape, scoped to git plumbing
  subcommands instead of workspace scripts.

## Diff compression (PR-Agent-style, ~15-20k token cap)
- derived: `grep -rn "PR-Agent\|context_lines\|deletion-only" spawn.py gates/*.py`
  returns no matches — no existing diff-compression helper in this repo to adapt;
  this stage is new code per the issue's own design section (additions-over-deletions
  weighting, deleted-file collapse to name list, deletion-only hunk stripping, ±3-10
  line context window, hard token cap with graceful degradation to name lists).

## Relevance prefilter / validator (Haiku-tier calls)
- `resolved_role_model()` spawn.py:4988 is the existing precedent for resolving which
  model a role session runs under (canonical: spawn.py:4988 read this session);
  prefilter/validator calls need an explicit Haiku-tier `--model` override rather
  than inheriting this role-level resolution.
- derived: `grep -n "prefilter\|validator" spawn.py` returns no matches — no existing
  prefilter/validator helper to reuse in this codebase.
- canonical: issue #1587 body (read via `gh issue view 1587` this session) names a
  security-review-style refute-or-confirm pattern for the validator stage. New code
  guided by that citation, reusing the same `subprocess.run(["claude", "-p", ...])`
  call shape already used at spawn.py:5266-5267 and spawn.py:5380-5381.

## Queue enqueue (lane=diff)
- `enqueue()` gates/patrol_queue.py:65-97 takes a `finding` dict carrying its own
  `lane` field, restricted to `LANES = ("diff", "sweep")` (gates/patrol_queue.py:26),
  fingerprint-deduped, with `promotable=True` allowed only when `lane == "diff"`
  (canonical: gates/patrol_queue.py:65-97 read in full this session). Judge's queue
  write is planned as a direct `enqueue()` call with `lane="diff"`; this reading found
  no interface change needed in gates/patrol_queue.py, subject to re-check at build time.
- `run_scan()` gates/patrol_queue.py:236-308 is the tier-1 mechanical-scanner caller
  (issue #1582/#1584); judge is not a scanner and does not go through `run_scan()` —
  it would call `enqueue()` directly, same underlying primitive, LLM-sourced findings
  instead of `record_lint` output.

## Trace log (trace-always, consult-log convention)
- `_consult_trace_path()` spawn.py:5114, `_append_consult_trace()` spawn.py:5125, and
  `_commit_consult_trace()` spawn.py:5144 are the consult-log convention the issue
  cites (canonical: spawn.py:5114-5166 read in full this session). These target
  `docs/reports/consult-log.md` (or per-issue path); judge's target path is
  explicitly different (patrol-judge-log.md), so judge needs its own
  trace-path/append/commit trio mirroring this shape rather than reusing the consult
  path constants, which are hardcoded to the consult-log filename.

## Budgets (3 roles/merge, 120s/judge)
- `CONSULT_TIMEOUT = 180` spawn.py:64 and `PANEL_TIMEOUT = 240` spawn.py:65 are the
  existing per-verb timeout constants (canonical: spawn.py:60-65 read this session);
  judge would add its own `JUDGE_TIMEOUT = 120` constant alongside them, plus a
  per-merge role-count cap (3) enforced by the CLI/orchestration layer around
  `judge_cmd()`, not inside a single call.

## Test conventions
- derived: `ls test/*.py | grep -i spawn`
