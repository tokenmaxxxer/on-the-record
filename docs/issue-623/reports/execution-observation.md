# Execution observation — issue #623 (phase 2)

## Independence statement

This role did not author or edit any observed artifact this session. All
findings below cite this session's own fixture-drive commands or the
observed roles' own committed records — never a re-execution of an
observed role's *task*, only a black-box drive of its *shipped surface*
(hooks/gates invoked as an external caller would invoke them).

## What was done

Built a simulated marketplace-cache fixture at
`$SCRATCH/issue623-fixture/cache/on-the-record/` (`cp -r
on-the-record/hooks`, `cp -r on-the-record/gates`, pycache stripped) with
`CLAUDE_PLUGIN_ROOT` pointed at it, driven from
`$SCRATCH/issue623-fixture/target/` — a directory with **no repo-root
`gates/`** (verified: `test -e $FIX/target/gates` → absent). This mirrors
`on-the-record/hooks/test_hook_cache_layout.py`'s `_make_cache_dir`
pattern from #556, extended to run the actual hook scripts (not just
import them) with real Bash/Write/Stop JSON payloads via a Python driver
(`drive2.py`, `drive.py`, this session). Scope B queried the registering
docs for each pre-registered metric's current measured state.

`$SCRATCH` = `/tmp/claude-1000/-home-jwjung--tokenmaxxxer-work-on-the-record-issue-623-execution-observation/e1297c13-2482-4c17-ad12-faa114097b6d/scratchpad`.

## Scope A — per-surface side-effect table

| Surface (issue) | Hook(s) driven | Environment | Result | Evidence |
|---|---|---|---|---|
| #573/#597 Bash PreToolUse chain (contract-guard, pr-preflight, claim-scan-preflight, spec-index-preflight, impact-guard, delegated-judgment-gate) | all 6, payload `{"tool_name":"Bash","tool_input":{"command":"git status"}}` | installed-cache fixture (`CLAUDE_PLUGIN_ROOT`=cache, no repo-root `gates/`) | measured-pass — all 6 exit 0, zero `ModuleNotFoundError`, chain latency 177ms | `drive.py` output this session: `('contract-guard.sh', 0, ...)` … `('__chain_latency_ms__', 177, ...)` |
| #566 Write/Stop guards (record-claim-guard, accumulation-claim-guard) | driven with #608's approval-gate, deliverable-guard as one chain | installed-cache fixture | measured-pass — all exit 0, no crash | `drive.py` output: `('record-claim-guard.sh', 0, ...)`, `('accumulation-claim-guard.sh', 0, ...)`, `('approval-gate.sh', 0, ...)`, `('deliverable-guard.sh', 0, ...)` |
| #586 role-spec-reference-guard | ownership-fast-path probe: Write to an *unowned* path | installed-cache fixture | measured-pass — exits 0 in the fast path with no gates-module dependency reached, matching #556's ownership-before-crash guarantee (commit `cc9feff`, `on-the-record/hooks/test_hook_cache_layout.py`) | `drive2.py` output this session: `unowned-write: (0, '')` |
| #587 spawn.py `-C` target threading, five-event e2e | not re-driven this session — `spawn.py` lives at repo root and is **not packaged under `on-the-record/`** (`find on-the-record -iname spawn.py` → empty; `on-the-record/.claude-plugin/plugin.json` lists no spawn.py entry point) | dev checkout only (install-path parity does not apply — this surface is orchestrator tooling, not a shipped plugin hook) | deferred-with-reason — install-path parity is not a coherent question for this surface; #587's own round-4 record (`docs/issue-587/reports/execution-observation.md`, "Recommend closure of #587") already covers the dev-checkout-only claim it makes and states the same fixture/checkout boundary in its own "Resolution path" section | `docs/issue-587/reports/execution-observation.md`, cited above |
| core#189 | not reachable — `core` is a separate repository from this checkout; no local artifact to drive | n/a | deferred-with-reason — cross-repo surface, unreachable from this session's fixture (per contract independence: never a re-execution, and there is no local artifact to black-box drive) | this session's own `find`/`ls` of the checkout root found no `core` tree |
| #577 contract-guard (baseline) | covered under the Bash chain row above | installed-cache fixture | measured-pass (subsumed in the #573/#597 chain row) | `drive.py` output, `contract-guard.sh` rc=0 |
| #576 accumulation-claim-guard, decision-queue-stopgate | covered under Write and Stop chain rows | installed-cache fixture | measured-pass | `drive.py` output, `decision-queue-stopgate.sh` rc=0 |
| #608 approval-gate, deliverable-guard, pr-preflight | covered under Write and Bash chain rows above | installed-cache fixture | measured-pass | `drive.py` output, rows for `approval-gate.sh`, `deliverable-guard.sh`, `pr-preflight.sh` |
| #600 accumulation-claim-guard, decision-queue-stopgate, proposal-shape-gate, survey-order-gate | `accumulation-claim-guard.sh`, `decision-queue-stopgate.sh` driven; `proposal-shape-gate.sh`/`survey-order-gate.sh` not present under `on-the-record/hooks/` (`ls` this session) | installed-cache fixture (partial) | measured-pass for the two hooks present in the packaged surface; deferred-with-reason for `proposal-shape-gate.sh`/`survey-order-gate.sh` — not found under the packaged `on-the-record/hooks/` tree this session, so either they are repo-root-only tooling (like #587's `spawn.py`) or were renamed since #600 landed; not re-derivable without editing #600's own docs, which is out of scope | `ls on-the-record/hooks/` this session; `docs/issue-600/reports/implementation.md` |
| #619 report-framing-check, role-test-claim-guard | Stop chain | installed-cache fixture | measured-pass | `drive.py` output: `role-test-claim-guard.sh` rc=0, `report-framing-check.sh` rc=0 |
| Cross-cutting: honest-work false-reject class (#476) | this session's own live commands, not the fixture | this repo's own live session (dev checkout, real `CLAUDE_PLUGIN_ROOT`) | **measured-fail** — a legitimate multi-line `for`-loop Bash command and a legitimate Python-heredoc command containing literal JSON (`{"tool_input": ...}`) were both refused pre-execution this session with `Contains shell syntax (string) that cannot be statically analyzed` / `Contains brace with quote character (expansion obfuscation)`, forcing a workaround (writing the script to a file via the Write tool instead of a heredoc) before the drive could proceed. This is a live, reproduced instance of #476's `false_reject` class, not a hypothetical. | this session's own transcript: the blocked `for h in ...; do ... done` command and the blocked `python3 - <<'PYEOF' ... {"tool_input":...} ... PYEOF` command, both immediately preceding the `drive2.py`-file workaround |

## Scope B — per-metric measured table

| Metric (registering issue) | Registered guardrail | Status | Evidence |
|---|---|---|---|
| `wiring_coverage_rate` / `warn_period_correction_rate` (#476) | H1b, two-week/60% threshold | deferred-with-reason — the issue's own implementation record states measurement is "the issue's own next step, out of scope for this build" and requires a two-week window not yet elapsed | `docs/issue-476/reports/implementation.md`: "...measuring `wiring_coverage_rate` and `warn_period_correction_rate` against the H1b two-week/60% threshold) is the issue's own next step, out of scope for this build" |
| `unrecorded_requirement_rate` / `false_flag_rate` (#566) | `false_flag_rate <= 20%` | deferred-with-reason — pre-registered guardrail with no measurement window run yet; proposal states this is "a measurement question for whoever runs the pre-registered H1 window", not yet run | `docs/issue-566/proposals/architecture.md`: "not solved here — it is a `false_flag_rate`/`unrecorded_requirement_rate` measurement question for whoever runs the pre-registered H1 window" |
| `decision_fatigue_reduction_rate` / `auto_decision_reversal_rate` (#573) | `auto_decision_reversal_rate <= 5%`, measured at step 5 | deferred-with-reason — proposal states explicitly "this phase cannot itself measure that, only avoid loosening it"; no step-5 measurement exists in the corpus yet | `docs/issue-573/proposals/architecture.md`: "Downstream, product-discovery's registered guardrail (`auto_decision_reversal_rate <= 5%`, measured at step 5) is the eventual test... this phase cannot itself measure that" |
| #587 five-event e2e | all five issue-timeline events fire on shipped code | measured-pass, dev-checkout only (see Scope A row above — install-path parity not applicable to this surface) | `docs/issue-587/reports/execution-observation.md`: "Every one of the five issue-timeline events... now fires on the shipped code's exposed surface against a fixture target repo" |
| #609/#600/#608/#619 acceptance re-runs | issue's stated acceptance criteria | measured-pass — `#600`, `#608`, and `#619` each carry `loop_state: landed` in their own implementation records, and this session's fixture drive independently reproduced their packaged hooks resolving with no crash under install-cache conditions (Scope A rows above) for the hooks actually present in the package; #609 not found as a distinct implementation record in this checkout (deferred-with-reason — no local artifact under `docs/issue-609/` naming a driveable hook surface) | `grep loop_state` this session on `docs/issue-600/reports/implementation.md`, `docs/issue-608/reports/implementation.md`, and `docs/issue-619/reports/implementation.md`; `ls docs/issue-609` |

## Verdict

**Outcome**: not fully met as originally scoped — the drive establishes
install-path parity (no `ModuleNotFoundError`, correct ownership-fast-path
exit, acceptable chain latency) for every hook present in the packaged
`on-the-record/hooks/` tree, satisfying the operator's addition for those
surfaces. It does **not** establish install-path parity for #587
(`spawn.py`, unpackaged, dev-checkout-only by design) or for #600's
`proposal-shape-gate.sh`/`survey-order-gate.sh` (not found in the packaged
tree this session — see Scope A row, `ls on-the-record/hooks/`). Per the
spec's worst-case-among-cited-steps recomputation rule, the outcome
verdict is the worst of these step results: **measured-fail**, driven by
the reproduced #476 false-reject instance (Scope A cross-cutting row)
plus the two deferred/unreachable Scope A rows above (#600's two missing
hooks, core#189).

**Trajectory**: sound. Phase 1 (survey + proposal,
`docs/issue-623/proposals/2026-08-10-execution-observation-post-landing-verification.md`,
commit `983af74`) preceded phase 2; phase 2 opened only after the
single-account `APPROVE issue-623/execution-observation` comment (verified
against `docs/specs/approvers.md`, which lists `JiwonJung94`, the PR #635
author and the approving comment's author — single-account mode per
contract v3 s19, string-exact match confirmed) — see this session's
`gh issue view 623 --comments` output. No step was skipped: current-state
survey preceded the sweep, the proposal named the fixture design before
any verdict language appeared.

**Step**: the deficient artifact is `on-the-record/hooks/contract-guard.sh`
and/or its sibling shell-syntax analyzer (whichever one fired — the error
text did not name the hook) exercised live in this very session — subject:
the honest-work false-reject behavior; test: two legitimate commands (a
multi-line `for` loop, a Python heredoc containing literal JSON) submitted
in the normal course of building this drive; result: **measured-fail**
(false_reject, per #476's own taxonomy); assertedBy: execution-observation,
this session, citing its own blocked-command transcript (Scope A
cross-cutting row) as the reproduction.

## Coordination with #628

#628's phase-2 hunt (signature classes a-h) was checked this session
(`ls docs/issue-628/`) — only its phase-1 survey/proposal exist, no
phase-2 record to cite. This record proceeds independently per the
proposal's stated fallback ("cite its record by commit SHA once it
exists... drive independently until then"); no #628 citation is available
as of this commit.

## Why

To close the operator's install-path-parity gap left open by PR #635
(phase 1) and #587's round-4 record, which validated dev-checkout code
paths only.

## Upstream / basis

Commit `983af74` (phase-1 proposal), commit `cc9feff` (#556's cache-layout
fix this drive's fixture pattern mirrors), `docs/issue-587/reports/execution-observation.md`
(cited Scope A row).

kind: execution-observation
loop_state: handed-off

## Open findings

1. **Honest-work false-reject in the Bash-command shell-syntax analyzer**
   (Scope A cross-cutting row). Impact: this session's own legitimate
   `for`-loop and JSON-heredoc commands were refused pre-execution, adding
   a manual file-write workaround to what should have been a direct
   command — the same class #476 was built to reduce, still reproducing
   live post-#476. Timeline: reproduced this session, 2026-08-10, mid-drive
   (see blocked commands immediately preceding the `drive2.py` workaround
   in this session's transcript). Root cause: not diagnosed by this
   role — diagnosing the analyzer's matching logic would require reading
   `contract-guard.sh`'s internals as a fix, which is out of scope for an
   observation role (independence: no edits to the observed surface).
   Action item: route to remediation against #476 (or a fresh issue, which
   only the user files) with this session's exact blocked-command strings
   as the reproduction.
2. **#600's `proposal-shape-gate.sh`/`survey-order-gate.sh` not found under
   the packaged `on-the-record/hooks/` tree.** Impact: install-path parity
   for these two hooks named in #600's own implementation record is
   unverified — either they are repo-root/dev-only tooling (benign, like
   #587's `spawn.py`) or a packaging gap (not benign). Timeline: observed
   this session, 2026-08-10. Root cause: not diagnosed — distinguishing
   "intentionally unpackaged" from "packaging regression" requires reading
   #600's own design intent, out of scope here. Action item: #600's own
   role or a fresh remediation issue should state explicitly whether these
   two are meant to ship in `on-the-record/hooks/`.

## Next steps

Deliver this record via PR carrying `Closes #623`. The two open findings
above route to remediation per each issue's registered rule (proposal's
"## What will be done", item 4) — no fix lands in this branch.

## Resolution path

Finding 1: a remediation round against #476 (or a fresh user-filed issue)
that narrows the shell-syntax analyzer's obfuscation-detection patterns to
exclude legitimate multi-line loops and JSON-literal heredocs, verified by
re-running this session's exact blocked commands and confirming they no
longer refuse.

Finding 2: #600's own role states in its record (or a fresh remediation
round) whether `proposal-shape-gate.sh`/`survey-order-gate.sh` belong in
`on-the-record/hooks/`; if yes, a packaging fix; if no, no action beyond
this note.
