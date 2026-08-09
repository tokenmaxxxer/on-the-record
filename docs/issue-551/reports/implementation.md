---
code_under_review:
  - gates/test_env_resolve.py
  - gates/test_test_env_resolve.py
  - docs/specs/test-env-resolution.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #551

## What was done
Delivered the approved proposal (`docs/issue-551/proposals/proposal.md`):
- `gates/test_env_resolve.py` — `resolve_core(env, candidates)` implementing
  the 3-step order (env var / sibling candidate / SKIP) plus a `main(argv)`
  CLI wrapper (`python3 -m gates.test_env_resolve ...`).
- `gates/test_test_env_resolve.py` — pytest coverage of all branches: env-var
  hit, sibling-candidate hit, env-var-set-but-missing-gate-lib fall-through,
  and the SKIP outcome (path + exit code).
- `docs/specs/test-env-resolution.md` — the convention doc: resolution order,
  SKIP contract, no-hardcoded-paths rule, per-consumer-shape adoption notes
  (bash CLI vs. pytest import), the reference module embedded verbatim, and
  the one enumerated empty-state exception (`gates/test_skip_gate.py`, no
  core dependency at all).
- Added a `## Accumulation` section to `docs/issue-551/proposals/proposal.md`
  to satisfy `accumulation-claim-guard.sh`, which fired on the new
  subprocess-adjacent CLI file (see Rationale for deviations).

Doc-placement ladder: the convention doc is the durable spec artifact and
lands at `docs/specs/test-env-resolution.md` per the proposal's frozen
write set — no separate decisions/ or reports/ entry is warranted (no new
dependency, env var, or benchmark number was introduced).

## Why
Basis: `docs/issue-551/proposals/proposal.md`, approved via issue-level
comment `APPROVE issue-551/implementation` by JiwonJung94 (listed in
docs/specs/approvers.md), single-account mode (PR #552's author is the
same account as the approver).

## Upstream
docs/issue-551/proposals/proposal.md

## What did not work
- Wrote the test module importing via
  `from gates.test_env_resolve import ...` first, expecting `gates` to
  behave as a regular package like the CLI's `python3 -m gates.test_env_resolve`
  invocation; pytest collection failed with `ModuleNotFoundError: No module
  named 'gates.test_env_resolve'; 'gates' is not a package` (the `gates`
  directory has no package-init file). Fixed by switching the test import to
  the existing repo convention (`sys.path.insert(0, str(Path(__file__).parent));
  from test_env_resolve import ...`, matching `gates/test_skip_gate.py`).
  `python3 -m gates.test_env_resolve` itself still works via Python's
  implicit namespace-package support, so the proposal's stated CLI
  invocation form did not need to change.
- First attempt at writing the record file (before any of the three
  proposal-listed files existed) was refused by
  `record-claim-guard.sh` (unreachable-path references) — expected: write
  the record after the files exist, not before. Reordered accordingly.
- First attempt at writing `gates/test_env_resolve.py` was refused by
  `accumulation-claim-guard.sh` (new file touches an inline-subprocess/CLI
  shape with no `## Accumulation` field filled in the proposal) — expected
  the file write to just proceed; instead added the `## Accumulation`
  section to `docs/issue-551/proposals/proposal.md` (docs/ paths stay
  writable per the warrant directive) and retried successfully.

## Rationale for deviations
The proposal's frozen write set (`docs/specs/test-env-resolution.md`,
`gates/test_env_resolve.py`, `gates/test_test_env_resolve.py`) was
delivered unchanged. One line was appended outside that write set:
`docs/issue-551/proposals/proposal.md` gained a `## Accumulation` section.
This is not a scope-exceeded stop — the underlying deliverable did not
grow — it is the mandatory response to `accumulation-claim-guard.sh`
refusing the write without it; the proposal doc itself is explicitly a
writable doc-home under the warrant directive, and no other file changed
as a result.

## Open findings
None — one finding was raised and resolved before landing (below).

resolved_findings:
- source: warrant:warrant-hunter, before-landing dispatch, stance 0 (bypass
  hunt), recorded at docs/reports/2026-08-09-hunt-issue-551-implementation.md
  finding: `_has_gate_lib()` checked existence only (`os.path.isfile`), so
  an empty/stale stub `hooks/lib/gate-lib.sh` at `$CLAUDE_PLUGIN_ROOT_CORE`
  or a candidate path made `resolve_core()` report a successful resolution
  (exit 0) even though core was not really reachable — reintroducing the
  ambiguity the convention exists to remove.
  resolution: `_has_gate_lib()` now also requires `os.path.getsize(path) >
  0` (both `gates/test_env_resolve.py` and the embedded copy in
  `docs/specs/test-env-resolution.md`); added
  `test_empty_stub_gate_lib_does_not_resolve` to
  `gates/test_test_env_resolve.py`, confirmed via `derived: python3 -m
  pytest gates/test_test_env_resolve.py -q` — all cases pass, including
  the new one.

## Next steps
None — record is terminal (`loop_state: landed`).

## Resolution path
N/A — no open findings.
