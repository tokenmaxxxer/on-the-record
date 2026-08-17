# Current-state survey — issue #1725

## Scope

The issue's write set (verbatim from its acceptance check): `stop-gate.sh`,
`deviation-log-guard.sh`, `role-test-claim-guard.sh`,
`report-framing-check.sh`, `product-capture-stopgate.sh`, all in
`on-the-record/hooks/`, plus each hook's existing `test_*.py` (or a new
one where none exists) in the same directory.

## Reference implementation (#1718)

`on-the-record/hooks/decision-queue-stopgate.sh` already carries the
fix this issue ports.

canonical: `on-the-record/hooks/decision-queue-stopgate.sh:69-78` (read
in full this session)

Its Python `CHECK` heredoc parses the raw Stop payload into
`stdin_payload`, then — before role resolution, before `decision_queue`
is even read, before any branch that could write output — does:

```python
stop_hook_active = bool(stdin_payload.get("stop_hook_active"))
if stop_hook_active:
    sys.exit(0)
```

(with a comment explaining why: the harness treats *any* Stop
`additionalContext` as inject-and-resume, not passive, so a
`stop_hook_active` turn must emit nothing at all — not just suppress
`decision:"block"` while still writing an advisory `additionalContext`.)
This placement — first substantive check, before every other branch —
is the thing #1725 asks the five sibling hooks to mirror.

canonical: `on-the-record/hooks/test_decision_queue_stopgate.py:246-321`
(read in full this session)

`test_decision_queue_stopgate.py` covers it with four tests prefixed
`t_stop_hook_active_emits_nothing_for_*` (tier1, tier2,
waiting-declaration, primed-tier2-latch), each asserting
`returncode == 0` and `stdout == ""`.

## The five target hooks, current shape

canonical: `on-the-record/hooks/stop-gate.sh`,
`on-the-record/hooks/deviation-log-guard.sh`,
`on-the-record/hooks/role-test-claim-guard.sh`,
`on-the-record/hooks/report-framing-check.sh`,
`on-the-record/hooks/product-capture-stopgate.sh` (all five read in full
this session)

All five share one structural trait relevant to this port: each parses
the Stop payload once into a Python dict named `e`, immediately after
`json.loads`, with an `isinstance(e, dict)` guard directly below the
parse:

| hook | payload env var | dict-guard exit | first field read after the guard |
|---|---|---|---|
| `stop-gate.sh` | `STOP_PAYLOAD` | `sys.exit(2)` | `e.get("last_assistant_message")` |
| `deviation-log-guard.sh` | `STOP_PAYLOAD` | `sys.exit(2)` | `e.get("transcript_path")` |
| `role-test-claim-guard.sh` | `RTCG_PAYLOAD` | `sys.exit(0)` | role-identity resolution (reads a session-bind snapshot file) |
| `report-framing-check.sh` | `REPORT_FRAMING_PAYLOAD` | `sys.exit(2)` | `e.get("last_assistant_message")` |
| `product-capture-stopgate.sh` | `STOP_PAYLOAD` | `sys.exit(2)` | `e.get("transcript_path")` |

canonical: same five files as above (read in full this session, table
directly above cites each one's payload var and post-guard read)

None of the five currently reads `stop_hook_active` anywhere. Each has
at least one branch that writes `hookSpecificOutput.additionalContext`
(all five) and `report-framing-check.sh` additionally has a
`decision: "block"` branch — both are the exact shapes #1725 and #1718
identify as loop-triggering under `stop_hook_active: true`.

Every one of the five is fail-closed the same way:
`trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT`
at the top, `ORCHESTRATE_OFF` kill switch, then the payload is read from
stdin in bash and handed to Python via an env var, matching
`decision-queue-stopgate.sh`'s own skeleton.

`role-test-claim-guard.sh` is the one structural outlier: its
`isinstance(e, dict)` guard exits 0 (not 2) on a non-dict payload, and
role-identity resolution (reading `OTR_ROLE_BIND_STATE_DIR`'s snapshot
file, an actual file read) happens immediately after the dict guard,
before `last_assistant_message` is read. A `stop_hook_active` check
placed after that resolution would still work today (role resolution
has no side effects), but is inconsistent with #1718's own placement
(before role resolution) and would leave a live inconsistency the next
edit to this hook could accidentally trip over.

## Existing tests

Four of the five hooks already have a `test_*.py` in
`on-the-record/hooks/`:

canonical: `on-the-record/hooks/test_deviation_log_guard.py:39-51`,
`on-the-record/hooks/test_role_test_claim_guard.py:11-22`,
`on-the-record/hooks/test_product_capture_stopgate.py:45-57` (all three
read in full this session)

- `test_deviation_log_guard.py` — `_run(repo, transcript, role=None,
  orchestrate_off="")` builds the payload as
  `json.dumps({"transcript_path": str(transcript)})`; no
  `stop_hook_active` key today.
- `test_role_test_claim_guard.py` — `_run(message,
  role="implementation")` builds `json.dumps({"last_assistant_message":
  message})`; no `stop_hook_active` key today.
- `test_product_capture_stopgate.py` — same shape as
  `test_deviation_log_guard.py`'s `_run`.
- `test_decision_queue_stopgate.py` — already has a `stop_hook_active`
  parameter on its `_run` (from #1718); not part of this issue's write
  set, cited here only as the parameter-naming precedent.

One of the five, `stop-gate.sh`, has no `test_*.py` in
`on-the-record/hooks/`, but does have a differently-shaped existing test
elsewhere in the repo.

canonical: `tests/test_stop_gate.sh:1-31` (read in full this session,
after an initial mis-scan wrongly assumed it was unrelated — corrected
by reading the file directly)

`tests/test_stop_gate.sh` is a standalone bash test runner (not pytest,
not `test_*.py`, not under `on-the-record/hooks/`) that already exercises
`on-the-record/hooks/stop-gate.sh` directly: it pipes a synthesized
`last_assistant_message` payload into the hook via `bash "$H/stop-gate.sh"`
and asserts on stdout for the missing-risk-clause, all-clauses-present,
non-approval-passthrough, and role-session-passthrough cases. It has no
`stop_hook_active` case today and is not itself a `test_*.py`, so it does
not satisfy the issue's acceptance line ("Asserted by each hook's
existing `test_*.py` ... in `on-the-record/hooks/`") even though the
hook is not, strictly, untested.

`report-framing-check.sh` also has no `test_*.py` in
`on-the-record/hooks/`.

canonical: `gates/test_report_framing_check.py:1-41`,
`on-the-record/hooks/report-framing-check.sh:9-11` (both read in full
this session)

`gates/test_report_framing_check.py` has one test,
`t_run_md_has_framing_instruction`, which asserts the four framing terms
appear in `on-the-record/commands/run.md`'s text; it never invokes
`report-framing-check.sh`. Per `report-framing-check.sh`'s own header
comment, this is by design — that file "checks the live reply directly,
complementing the grep-based instruction-text check in
`gates/test_report_framing_check.py` (which only verifies `run.md`
still carries the instruction, not that a given reply complied with
it)". A different gate on a different concern, not this hook's
behavioral test.

Repo test config (`pytest.ini`): `python_functions = test_* t_*`, so the
existing `t_*`-prefixed functions in these files are pytest-collected
without a custom runner; `test_product_capture_stopgate.py` additionally
carries a `__main__` block for standalone execution, which is incidental
to collection.

## Confirmed by running the reference suite

canonical: `python3 -m pytest -q -o addopts="" on-the-record/hooks/test_decision_queue_stopgate.py` — result: 23 passed
```
.......................                                                   [100%]
23 passed in 2.10s
```
canonical: same pytest run directly above — no `SKIPPED` line appears in
its output. This is the working, merged precedent the new tests will be
modeled on.

## What the proposal must decide

1. Where inside each of the five Python `CHECK` bodies the
   `stop_hook_active` short-circuit goes (placement, given the table
   above).
2. Whether the check is duplicated per-file (matching every existing
   hook's self-contained-heredoc style, `decision-queue-stopgate.sh`
   included) or factored into a shared bash/python helper.
3. For `stop-gate.sh` and `report-framing-check.sh`, which have no
   existing `test_*.py` in `on-the-record/hooks/`, what scope a new
   test file should cover beyond the one case the issue requires.
