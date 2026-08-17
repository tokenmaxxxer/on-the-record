---
status: proposed
files:
  - on-the-record/hooks/stop-gate.sh
  - on-the-record/hooks/deviation-log-guard.sh
  - on-the-record/hooks/role-test-claim-guard.sh
  - on-the-record/hooks/report-framing-check.sh
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_stop_gate.py
  - on-the-record/hooks/test_deviation_log_guard.py
  - on-the-record/hooks/test_role_test_claim_guard.py
  - on-the-record/hooks/test_report_framing_check.py
  - on-the-record/hooks/test_product_capture_stopgate.py
---

files: on-the-record/hooks/stop-gate.sh,
on-the-record/hooks/deviation-log-guard.sh,
on-the-record/hooks/role-test-claim-guard.sh,
on-the-record/hooks/report-framing-check.sh,
on-the-record/hooks/product-capture-stopgate.sh,
on-the-record/hooks/test_stop_gate.py,
on-the-record/hooks/test_deviation_log_guard.py,
on-the-record/hooks/test_role_test_claim_guard.py,
on-the-record/hooks/test_report_framing_check.py,
on-the-record/hooks/test_product_capture_stopgate.py

## Request

#1725: the five Stop hooks `stop-gate.sh`, `deviation-log-guard.sh`,
`role-test-claim-guard.sh`, `report-framing-check.sh`,
`product-capture-stopgate.sh` still write `additionalContext` and/or
`decision:"block"` without ever reading `stop_hook_active` from the Stop
payload. The harness treats any Stop `additionalContext` as
inject-and-resume — the same loop-guard as `decision:"block"` — so any of
these five can hold a turn open across up to 8 consecutive forced
re-entries whenever its trigger condition persists across the reply the
block itself forces. #1718 already fixed this for the sixth Stop hook,
`decision-queue-stopgate.sh`; this closes the same gap on its five
siblings, restoring the full `stop_hook_active` contract across every
Stop hook in `on-the-record/hooks/`.

## Constraints

- Byte-identical behavior when `stop_hook_active` is false or absent —
  no change to any existing branch's output shape or trigger condition.
- Exit 0, empty stdout, on every branch when `stop_hook_active` is true —
  not just the branches that currently write `decision:"block"`.
- `ORCHESTRATE_OFF=1`, role-session/orchestrator-only scoping, and each
  hook's non-Stop code paths stay unchanged (issue's stated empty state).
- Test obligation is per-hook: extend the existing `test_*.py` where one
  exists in `on-the-record/hooks/`; create one where none does.
- Minimal diff — this is a mechanical port of an already-approved,
  already-merged pattern (#1718/PR #1720), not a redesign.

## Rationale

**Placement: inside each Python `CHECK` body, immediately after the
`isinstance(e, dict)` guard — not in the surrounding bash launcher.**
Considered and rejected: parsing `stop_hook_active` at the bash layer
(e.g. via `jq` or a `grep`/regex probe on the raw stdin payload) and
short-circuiting `exit 0` before ever invoking `python3 -c "$CHECK"`.
Rejected because every one of these five hooks already deserializes the
full payload exactly once, in Python, into a dict named `e`
(`decision-queue-stopgate.sh`'s own precedent does the same, into
`stdin_payload`); a second, independent bash-level JSON parse duplicates
that work, risks a bash/python inconsistency on an edge-case payload (a
literal `"stop_hook_active"` substring appearing inside an unrelated
string field, for instance, would defeat a naive grep but not the `dict`
lookup), and there is no existing `jq`-or-equivalent dependency assumed
by any of these hooks today — introducing one for a two-line check is
disproportionate. Doing the check in Python, on the already-parsed dict,
before any other field of `e` is read, matches #1718's own placement and
needs no new tooling.

**Duplicated per-file, not factored into a shared helper.** Considered
and rejected: extracting the `stop_hook_active` short-circuit into one
shared bash or Python library sourced by all six Stop hooks (the five
here plus `decision-queue-stopgate.sh`). Rejected because none of these
hooks currently shares code with any other — each is a fully
self-contained bash script embedding its own standalone Python heredoc,
invoked independently by the harness with no module-loading convention
between them, and `decision-queue-stopgate.sh` itself does not source
anything for this same two-line check. Introducing a shared-library seam
here is a larger structural change than the fix warrants and would be
inconsistent with the file-per-hook house style every other Stop hook in
this directory already follows.

## Accumulation

This is the accumulation-cost-shaped change the Rationale's second
rejected alternative (a shared helper) was weighed against: the same
two-line `if e.get("stop_hook_active"): sys.exit(0)` guard, hand-copied
into a Python heredoc embedded in a standalone bash script, once per
Stop hook. After this proposal lands, six of six current Stop hooks in
`on-the-record/hooks/` (`decision-queue-stopgate.sh` plus these five)
carry the identical two-line check independently. If a 7th Stop hook is
added later, it needs the same two lines copied in by hand again — there
is no single place that enforces "every Stop hook checks
`stop_hook_active` first"; a new hook that omits it is now a silent gap
identical in shape to the one #1725 itself closes. The proposal accepts
this cost now (see Rationale: no existing sourcing convention among
these hooks, and six instances is not yet enough duplication to justify
inventing one), but the threshold is concrete and worth naming rather
than leaving implicit: if a 7th or 8th Stop hook is added carrying this
same copy-pasted guard, that is the point to revisit the shared-helper
alternative rejected here, or add a mechanical gate (a grep-based repo
test asserting every Stop-registered hook contains the guard) instead of
relying on each new hook's author remembering to copy it.

## What will be done

For `stop-gate.sh`, `deviation-log-guard.sh`, `report-framing-check.sh`,
and `product-capture-stopgate.sh` — each already has
`if not isinstance(e, dict): sys.exit(2)` right after `json.loads`: add,
directly below that guard,
```python
if e.get("stop_hook_active"):
    sys.exit(0)
```
before the first field of `e` is otherwise read.

For `role-test-claim-guard.sh` — its dict-guard exits 0 (not 2); add the
same two-line check directly below it, before role-identity resolution
(the `OTR_ROLE_BIND_STATE_DIR` snapshot read) runs — matching #1718's
own before-role-resolution placement rather than the file's own
post-guard read order, per the Rationale's placement discussion.

Test changes:
- `test_deviation_log_guard.py`, `test_role_test_claim_guard.py`,
  `test_product_capture_stopgate.py` — add a `stop_hook_active` parameter
  to each file's `_run()` helper (default `False`, folded into the
  payload dict), and one new `t_stop_hook_active_emits_nothing_for_*`
  test per file, each reusing an existing scenario that currently
  produces `additionalContext` output and asserting `returncode == 0` /
  `stdout == ""` instead.
- `test_stop_gate.py` (new) — a `_run()` helper matching
  `test_role_test_claim_guard.py`'s shape (payload → env → subprocess),
  covering the hook's core structural check (missing-clause flag, all-
  clauses silent, role-session no-op, `ORCHESTRATE_OFF` no-op) plus the
  required `stop_hook_active` case.
- `test_report_framing_check.py` (new) — same shape, covering the
  `decision:"block"` missing-elements case, the all-elements-silent case,
  role/`ORCHESTRATE_OFF` no-ops, and the required `stop_hook_active` case.

## Out of scope

- `decision-queue-stopgate.sh` itself — already fixed by #1718, not part
  of this issue's write set.
- `tests/test_stop_gate.sh` and `gates/test_report_framing_check.py` —
  both exist and cover different concerns (see survey), neither is a
  `test_*.py` in `on-the-record/hooks/`, and the issue's acceptance line
  names that directory specifically; left untouched.
- Any change to what triggers each hook's existing branches (the
  approval-shape check, the framing-element check, the deviation-log
  diff check, the product-capture category regexes, the skip/hand-count
  test-claim checks) — only the new-branch addition is in scope.

## How you'll know it worked

Each of the five hooks' extended-or-new `test_*.py` passes, including a
`t_stop_hook_active_emits_nothing_for_*` case that feeds
`stop_hook_active: true` into a scenario that would otherwise produce
`additionalContext`/`decision:"block"` output, and asserts
`returncode == 0` and `stdout == ""`. All pre-existing tests in the same
five files (and in the untouched `test_decision_queue_stopgate.py`, run
as a control) continue to pass unchanged — confirming the
`stop_hook_active: false` path stayed byte-identical.
