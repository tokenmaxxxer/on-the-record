# Generated write-path disjointness (issue #684)

Golden reference for `gates/test_generated_paths.py`. One row per
write-producing call (`write_text`, `open(..., "w")`, `.mkdir(`,
`shutil.copy`/`move`) found by grep across `on-the-record/hooks/*.sh`. A
generator is `out-of-tree` when its constructed path never resolves inside
a target repo's worktree, or `issue-scoped` when the constructed path
string contains an issue-number placeholder (`issue-<n>`, `issue-{issue}`,
or an equivalent shell/f-string interpolation of an issue variable).
`collision-risk` names a generator neither of the above — this table must
carry zero such rows; the one #684 survey found is fixed below.

| mechanism | classification | verdict |
|---|---|---|
| `record-scaffold.sh` | issue-scoped | safe — `docs/issue-<n>/reports/<role>.md`, `<n>` from CLI arg |
| `delegated-judgment-gate.sh` | issue-scoped | safe — `docs/issue-<n>/decisions/*`, `<n>` from payload/branch |
| `product-capture-stopgate.sh` | issue-scoped | safe — fixed #684: `docs/issue-<n>/product/<cat>.md`, `<n>` from `issue-<n>/<role>` branch name; no-ops off an issue-scoped branch |
| `deviation-log-guard.sh` | n/a | reads/checks only (`git diff`/`git log -p`), no write call — the actual `docs/issue-<n>/reports/deviation-log.md`/`docs/reports/deviation-log.md` append is made by the session, not this hook |
| `retry-loop-bound.sh` | out-of-tree | safe — `$TMPDIR`-rooted, never inside the target repo |
| `plan-order-guard.sh` | issue-scoped | safe — `docs/issue-<n>/decisions/spawn-refusal-<ts>.md`, `<n>` from `--issue` CLI arg |
| `session-role-bind.sh` | out-of-tree | safe — `${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}`-rooted, never inside the target repo (#698) |
| `self-update.sh` | out-of-tree | safe — writes into the shared plugin checkout, not the target repo |
| `directive.sh` | out-of-tree | safe — clones into the shared plugin checkout |
| `poll-rearm.sh` | out-of-tree | safe — shared function library sourced by `directive.sh`/`stop-poll-rearm.sh`; its checkout-clone fallback writes into the shared plugin checkout, same as `directive.sh` |
| `stop-poll-rearm.sh` | n/a | reads/validates only in its own file — no write call greppable in this file itself; the actual write happens via the sourced `poll-rearm.sh`'s `poll_rearm_arm_if_due()`, already recorded out-of-tree on that row |
| `impact-guard.sh` | out-of-tree | safe — same shared checkout clone |
| `spawn-allow-gate.sh` | n/a | reads/validates only, no write call |
| `merge-allow-gate.sh` | out-of-tree | safe — same `_checkout_resolve` shared-checkout-clone pattern as `impact-guard.sh`/`decision-queue-stopgate.sh` below, never inside the target repo |
| `gh-write-allow-gate.sh` | n/a | reads/validates only, no write call, no checkout resolution needed |
| `decision-queue-stopgate.sh` | out-of-tree | safe — same shared checkout clone |
| `accumulation-claim-guard.sh` | n/a | reads/validates only, no write call |
| `design-rationale-guard.sh` | n/a | reads/validates only, no write call |
| `approval-gate.sh` | n/a | reads/validates only, no write call |
| `call-shape-guard.sh` | n/a | reads/validates only, no write call |
| `claim-scan-preflight.sh` | n/a | reads/validates only, no write call |
| `absorbed-branch-recut-guard.sh` | n/a | reads/validates only — shells out to `spawn.py recut-if-absorbed`, which git-checkouts inside the target repo's own worktree, not a generated path |
| `contract-guard.sh` | n/a | reads/validates only, no write call |
| `deliverable-guard.sh` | n/a | reads/validates only, no write call |
| `delegation-post-gate.sh` | n/a | reads/validates only, no write call |
| `gate-registration-guard.sh` | n/a | reads/validates only, no write call |
| `pr-preflight.sh` | n/a | reads/validates only, no write call |
| `record-claim-guard.sh` | n/a | reads/validates only, no write call |
| `credential-record-guard.sh` | n/a | reads/validates only, no write call |
| `credential-network-guard.sh` | n/a | reads/validates only, no write call |
| `record-claim-shape-directive.sh` | n/a | reads/validates only, no write call |
| `record-tiering-directive.sh` | n/a | reads/validates only, no write call |
| `record-tiering-guard.sh` | n/a | reads/validates only, no write call |
| `report-framing-check.sh` | n/a | reads/validates only, no write call |
| `role-axis-completeness-guard.sh` | n/a | reads/validates only, no write call |
| `role-spec-reference-guard.sh` | n/a | reads/validates only, no write call |
| `role-test-claim-guard.sh` | n/a | reads/validates only, no write call |
| `spec-index-preflight.sh` | n/a | reads/validates only, no write call |
| `requirement-digest-preflight.sh` | n/a | reads/validates only, no write call |
| `test-authoring-invariant-guard.sh` | n/a | reads/validates only, no write call |
| `stop-gate.sh` | n/a | reads/validates only, no write call |
| `live-fire-test-guard.sh` | n/a | reads/validates only, no write call |
| `acceptance-command-real-run-guard.sh` | n/a | reads/validates only + re-runs a recorded command via `subprocess.run` (no `write_text`/`open(..., "w")`/`.mkdir(`/`shutil.copy`/`move` call in its own staged text) |
| `live-fire-claim-real-run-guard.sh` | n/a | reads/validates only + re-runs a cited live-fire test via `subprocess.run(["python3", "-m", "pytest", ...])` (no `write_text`/`open(..., "w")`/`.mkdir(`/`shutil.copy`/`move` call in its own staged text) |

Out of scope (per docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md):
the warrant counter / hunt-report naming (core#200); human-authored file
collisions (write-scope territory); the `<seq>` auto-decision/remediation
counter under same-issue concurrent sessions; shared-checkout marker/clone
races in the out-of-tree hooks above.
