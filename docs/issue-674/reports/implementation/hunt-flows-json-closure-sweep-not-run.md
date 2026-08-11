---
proposal: docs/issue-674/proposals/2026-08-11-flows-json-closure-sweep-not-run.md
---

# Hunt record — flows-json-closure-sweep-not-run

Note: the warrant directive specifies a different record path directly
under `docs/issue-674/reports/`, but writing there was refused by this
session's `board-gate.sh` R5 ownership rule (`CLAUDE_ROLE=implementation`
on branch `issue-674/implementation`; error: "belongs to another role.
implementation writes only implementation.md, implementation/** — never
a foreign record"). Every existing `hunt-*.md` record under
`docs/issue-*/reports/` in this repo lives under a role subtree
(`reports/<role>/hunt-*.md`), never directly under `reports/`, which
matches R5 but not the directive's naming rule for issue-scoped
proposals. Filing this record under `reports/implementation/` instead
so it lands somewhere at all.

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — accumulation-claim-guard's "filled" check on `## Accumulation` accepts any non-blank line, so a one-character placeholder body satisfies the gate exactly as well as a real accumulation-cost claim.
Kind: silent-failure
Seed: docs/issue-674/reports/implementation/survey.md, docs/issue-674/proposals/2026-08-11-flows-json-closure-sweep-not-run.md (two new docs-only files; the proposal's own `## Accumulation` section, added to satisfy on-the-record/hooks/accumulation-claim-guard.sh, was the named candidate)
cap_seconds: 60
tier: default (size:docs-only)
diff_stat_lines: 2 files changed (docs-only, no code diff vs main)
started_at: 2026-08-11T02:52:19Z
ended_at: 2026-08-11T02:56:30Z

### Reproduce
```
cd /tmp && rm -rf acg_test && mkdir -p acg_test/docs/issue-674/proposals && cd acg_test && git init -q
PAYLOAD=$(python3 -c '
import json
content = "# Proposal\n\nfiles:\n  - roles/example.json\n\n## Accumulation\nx\n"
print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"docs/issue-674/proposals/2026-08-11-x.md","content":content},"cwd":"/tmp/acg_test"}))
')
export ACG_PAYLOAD="$PAYLOAD"
export ORCHESTRATE_OFF=0
bash /Users/jk/.tokenmaxxxer/work/on-the-record-issue-674-implementation/on-the-record/hooks/accumulation-claim-guard.sh <<< "$PAYLOAD"
echo "exit=$?"
```

### Observed
`exit=0` — the guard allows the write. The `files:` list names
`roles/example.json`, which trips shape 5
(`_touches_shape_5`/`re.match(r"^roles/[^/]+\.json$", ...)`), so the
guard's own logic requires a filled `## Accumulation` section before it
will pass. It passes anyway, because `_has_filled_accumulation` is:
```python
def _has_filled_accumulation(body):
    m = _ACCUMULATION_HEADING.search(body or "")
    if not m:
        return False
    return any(line.strip() for line in m.group(1).splitlines())
```
— `x` is a non-blank line, so the check is satisfied. Nothing about the
body content is checked: it need not mention accumulation, cost, N-more
occurrences, or the touched shape at all. (The guard's own header
comment names this as deliberate: "field-presence strengthening ...
content is never interpreted, contract section 14" — the check is
documented as shallow by design, but the pass/fail outcome an author or
reviewer sees is identical to a real, substantive claim, which is
exactly the "looks like success" shape this hunt is chartered to flag.)
The actual proposal on this branch has a genuine, specific
`## Accumulation` section (not hollow), so this run found the guard's
enforced condition generally bypassable, not a hollow instance already
present in this proposal.

### Expected
A gate whose stated purpose is to force authors to "specify what happens
if this change comes N more times" should not be satisfiable by a
single placeholder character; at minimum a length/word-count floor or a
check for one of a small set of required tokens (e.g. a number, "no
new", "N more") would make a one-character body fail the same way an
empty body already does.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: NO FINDING
Seed: `git diff main -- gates/flows.py test_flows.py test_spawn.py docs/specs/flows-schema.md` (gates/flows.py stops calling `closure_sweep.find_violations()` in `flows_payload`, `hygiene.closure_sweep` now hard-coded `[]`, `hygiene.closure_sweep_skips` built locally as one `{"subject", "reason": "not-run-in-flows"}` per board subject)
cap_seconds: 180
tier: default
diff_stat_lines: >200 (4 files)
started_at: 2026-08-11T03:10:48Z
ended_at: 2026-08-11T03:13:02Z

Searched for any other gate/hook/spec whose behavior implicitly depends on
`hygiene.closure_sweep`/`hygiene.closure_sweep_skips` in `flows --json`
carrying real violation data, or on `find_violations()` running inside the
`flows` path:

- `grep -rln "hygiene" on-the-record/hooks/` — zero matches. No hook (not
  `decision-queue-stopgate.sh`, not `plan-order-guard.sh`, not
  `pr-preflight.sh`) reads the `hygiene` key of the `flows --json` payload at
  all; `decision-queue-stopgate.sh` only reads `decision_queue`.
- `on-the-record/hooks/plan-order-guard.sh` calls
  `gates/flows.py:plan_order_blocked()`, which *is* new relative to `main`,
  but `git diff HEAD -- gates/flows.py` shows it was already committed on
  this branch (commit `b2d913e`, issue #659, landed before the uncommitted
  issue-674 change) — not part of this change, and it doesn't touch
  `closure_sweep` at all. Confirmed via `git diff HEAD` (only the
  `closure_sweep`-removal hunk is uncommitted).
- `spawn.py:_board_wide_sweep()` (called every tick from
  `roster_watchdog()`, spawn.py:1943-1946) does `import closure_sweep;
  violations, skips = closure_sweep.find_violations(root)` directly, with
  its own top-level import inside the function — completely independent of
  `gates/flows.py:flows_payload()`. `test_spawn.py`'s
  `test_board_wide_sweep_*` tests (mock.patch.dict on `sys.modules`) confirm
  this call site is separate and untouched by the diff.
- `gates/closure_sweep.py` itself imports `pr_reference`, `spawn`, `ci`,
  `accumulation` — no import of `gates/flows.py`, no dependency on the
  `flows` path.
- `docs/specs/enforcement-boundary.md`'s `closure_sweep.py` row documents
  board-wide enforcement as running via `spawn.py:roster_watchdog()`
  (`find_violations()` call), not via `flows --json` — consistent with the
  code.
- Ran `on-the-record/hooks/test_decision_queue_stopgate.py` and
  `test_pr_preflight.py` (14 tests) — all pass, confirming no hook-side
  fixture assumed non-empty `hygiene.closure_sweep`.

No consumer of `flows --json`'s `hygiene.closure_sweep`/`closure_sweep_skips`
exists outside `gates/flows.py` itself (its own CLI print at
gates/flows.py:499-503) and the test suite. Every other place that needs
real violation data (`roster_watchdog`/`_board_wide_sweep`,
`gates/closure_sweep.py --post`, `contract-guard.sh`'s single-PR case) calls
`closure_sweep.find_violations()` (or equivalent single-PR logic) directly
and was never routed through `flows_payload()`. No cancelling pair found.
