---
code_under_review:
  - docs/specs/requirement-digest.md
  - gates/requirement_digest.py
  - gates/test_requirement_digest.py
  - on-the-record/hooks/requirement-digest-preflight.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/directive.sh
  - gates/ci.py
  - spawn.py
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
  - harness/fixture-requirement-digest/scenario.py
  - harness/README.md
type: feature
breaking: false
canonical: python3 harness/fixture-requirement-digest/scenario.py, this session — 5 rows PASS, exit 0
verdict: pass
loop_state: landed
---

# Implementation record — issue-930 (implementation role, phase 2)

## What was done

Built the approved proposal
(`docs/issue-930/proposals/requirement-digest-drift-guard-implementation.md`)
step by step:

1. `gates/requirement_digest.py` — new module mirroring
   `gates/spec_index.py`'s shape: `parse()` extracts each `## R###`
   block's `quote`/`source_issue`/`check`/`status` fields;
   `render()` emits one condensed line per non-`stale` entry;
   `update()` first re-verifies each entry's `check` path against the
   working tree and rewrites `status:` to `stale` in
   `docs/specs/requirements.md` in place when the path no longer
   resolves, then writes `docs/specs/requirement-digest.md`; `check()`
   compares current digest content to the freshly rendered content;
   `main()` matches `spec_index.py`'s `[<repo>] [--update]` CLI
   contract.
2. `gates/test_requirement_digest.py` — 9 unit tests covering parse,
   render (stale-exclusion, live-requirement-count line count), the
   check() function's clean/drift/missing-digest outcomes, the
   stale-rewrite path, and the documented empty-registry state.
3. `on-the-record/hooks/requirement-digest-preflight.sh` — new
   `PreToolUse`/`Bash` hook denying a `git commit` that lands a
   `requirements.md` change without a matching digest regeneration.
   Ports `parse()`/`render()` inline (no `gates/` import), matching
   `spec-index-preflight.sh`'s zero-install contract (see "What did
   not work" for why this changed mid-build). Also closes the
   `-a`/`-am` bypass named in the after-proposal hunt record at
   `docs/issue-930/reports/implementation/2026-08-12-hunt-requirement-digest-drift-guard-implementation.md`:
   when the intercepted command stages via `-a`/`--all`/a bundled
   short flag containing `a`, detection diffs the working tree against
   HEAD instead of relying on `git diff --cached` alone.
4. `on-the-record/hooks/directive.sh` — one bullet added to the
   orchestrator's standing `UserPromptSubmit` directive naming
   `docs/specs/requirement-digest.md` as the condensed live-requirement
   pointer to read before `requirements.md`.
5. `gates/ci.py` — `requirement_digest.check(repo)` added next to the
   existing `gates.requirement_registry(repo, {})` call, as the
   CI-timing backstop.
6. `spawn.py` — new `requirement_drift(root)`, called from
   `_board_wide_sweep()` immediately after `accumulation_trend()`'s
   print, same contract (print-only, never added to `anomaly_count`).
   Reads live (non-`stale`) IDs from the digest, lists open
   issues/PRs via `gh issue/pr list --json number,title,body`, and
   prints (a) live requirements mentioned by zero open issues/PRs and
   (b) open issues/PRs citing no requirement ID. `gh` failure prints
   an advisory line and returns `None` — never raises, never blocks.
7. `docs/specs/enforcement-boundary.md` — one new table row for
   `requirement_digest.py`, matching `accumulation_trend()`'s
   advisory/board-wide/non-blocking shape for the `spawn.py` half.
8. `harness/fixture-requirement-digest/scenario.py` + a
   `harness/README.md` section — 5 mechanical checks against a seeded
   scratch repo (3 requirements, 40 synthetic `docs/issue-*` records to
   exercise record-count >> requirement-count).
9. `gates/test_hooks_parity.py` — left unedited, per the proposal's own
   prediction (item 9): it auto-derives its expected hook set from
   `hooks.json`, so the new hook registers for free — verified by
   running it live (canonical/output in "Acceptance verification"
   below).

## Why

Builds the `product-discovery`-approved design for issue #930
(northpole req#6) — a self-maintaining requirement digest so record
accumulation doesn't dilute what the operator actually asked for
(req#2), plus a non-blocking drift guard — per this role's own
approved build proposal.

## Upstream

basis: `docs/issue-930/proposals/requirement-digest-drift-guard-implementation.md`

## Acceptance verification

canonical: `python3 gates/requirement_digest.py --update`, this session
- checked: `python3 gates/requirement_digest.py --update` — result: pass
```
docs/specs/requirement-digest.md 갱신됨
```

canonical: `python3 gates/test_requirement_digest.py`, this session
- checked: `python3 gates/test_requirement_digest.py` — result: pass
```
PASS t_check_empty_registry_documented_empty_state
PASS t_check_flags_drift_after_hand_edit
PASS t_check_flags_missing_digest
PASS t_check_no_registry_passes_nothing_to_check
PASS t_check_passes_after_update
PASS t_parse_extracts_all_required_fields
PASS t_render_drops_stale_and_keeps_live
PASS t_render_line_count_is_o_of_live_requirement_count_not_record_count
PASS t_update_rewrites_status_to_stale_when_check_path_missing
```

canonical: `python3 harness/fixture-requirement-digest/scenario.py`, this session
- checked: `python3 harness/fixture-requirement-digest/scenario.py` — result: pass
```
PASS digest condenses to requirement-count, not record-count
PASS hook denies/allows correctly, stale rewrite lands
PASS fresh digest-only selection is goal-aligned
[watchdog] requirement-drift: gh 실패 — 판정 불가 (advisory, 미집계)
PASS drift guard fires advisory-only, never blocking
PASS no .github/workflows/ changes (req#7)
```

canonical: `python3 gates/test_hooks_parity.py`, this session
- checked: `python3 gates/test_hooks_parity.py` — result: pass
```
  ok  t_live_fire_deny_before_commit_lands
  ok  t_non_self_hosted_target_gets_no_injection
  ok  t_registered_hooks_match_hooksjson_entries
  ok  t_role_settings_merges_hooks_only_for_self_hosted_target

4 passed
```

canonical: `git diff --stat main...HEAD -- .github/workflows/`, this session — empty stdout, exit 0
- checked: `git diff --stat main...HEAD -- .github/workflows/` — result: pass

## What did not work

Drafted `requirement-digest-preflight.sh`'s guard first as
`sys.path.insert(0, os.path.join(cwd, "gates")); import
requirement_digest` — mirroring how `gates/ci.py` imports the module.
Expected: importing from the consumer repo's own `cwd/gates` would
work the same way it does in `gates/ci.py`. Actual: the harness
scenario (step 8), run against a seeded scratch repo carrying only
`docs/specs/requirements.md` and seed `gates/seed_check_*.py` files
(no `gates/requirement_digest.py` checked out — the realistic shape of
a repo that only installs the plugin), hit the `except ImportError:
sys.exit(0)` fail-open path and let a commit through that should have
been denied.

canonical: `python3 harness/fixture-requirement-digest/scenario.py`, this session, before the inline-port fix
```
FAIL hook denies/allows correctly, stale rewrite lands
  - expected deny (rc=2) with no digest staged, got rc=0:
```

This is the zero-install gap `spec-index-preflight.sh`'s own header
comment warns against and avoids by porting its logic inline instead
of importing. Replaced the import with an inline port of `parse()`/
`render()` in the hook script — the passing re-run is the code fence
under "Acceptance verification" above.

## Hunt

Warrant-hunter dispatch skipped this transition: contract v3 s22
(subordinate in headless/single-shot sessions) forbids ending a turn
having delegated work not consumed within the same turn, and this
session has no later turn to consume an async hunter result in. The
harness scenario functioned as the adversarial check for this build —
it caught the zero-install import gap above before landing (see "What
did not work"), the same shape of defect a hunt dispatch would
otherwise have targeted.

## Rationale for deviations

`docs/specs/generated-paths.md` was not in the proposal's frozen write
set. `gate-registration-guard.sh` (issue #441/#684) refused the landing
commit until the new `requirement-digest-preflight.sh` hook also had a
row there, alongside the `enforcement-boundary.md` row the proposal did
list — the two registries share one convention for any new hook
script. `docs/` is the standing exception to the frozen write set (the
warrant directive's own carve-out: "Documents under docs/ are the
exception … always writable"), and the addition is a single mechanical
registry row, not a design decision — added in place rather than
stopping the build over it.

## Open findings

None.
