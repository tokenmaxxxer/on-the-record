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
| `deviation-log-guard.sh` | n/a | reads/checks only (`git diff`/`git log -p`/`git status --porcelain`, issue #2348 added the last one), no write call — the actual `docs/issue-<n>/reports/<role>/deviation-log/<shard>.md` (or the no-role/no-issue variants) append is made by the session via `spawn.py deviation-log-path`, not this hook |
| `skill-verdict-guard.sh` | n/a | reads/checks only (transcript scan + a direct read of the current branch's role record file), no write call — the actual `skill-verdict:` lines are appended by the session, not this hook |
| `retry-loop-bound.sh` | out-of-tree | safe — `$TMPDIR`-rooted, never inside the target repo |
| `approach-cap-warning.sh` | out-of-tree | safe — `$TMPDIR`-rooted (`${OTR_APPROACH_CAP_STATE_DIR:-$TMPDIR/otr-approach-cap}`), never inside the target repo, same pattern as `retry-loop-bound.sh` |
| `lint-test-on-edit.sh` | n/a | the lint/impacted-test subprocess's own stdout/stderr capture uses `tempfile.TemporaryFile()` (anonymous, unnamed, OS-tempdir-backed, never resolves to a named path inside the target repo); `python3 -m py_compile <edited-file>` may additionally write a standard `__pycache__/<name>.<tag>.pyc` next to the edited file — the same deterministic, 1:1-derived-from-source-path bytecode cache Python produces for any interpreter invocation of that file, not a hook-invented shared/generated path, so it carries none of this survey's cross-role collision risk |
| `plan-order-guard.sh` | issue-scoped | safe — `docs/issue-<n>/decisions/spawn-refusal-<ts>.md`, `<n>` from `--issue` CLI arg |
| `session-role-bind.sh` | out-of-tree | safe — `${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}`-rooted, never inside the target repo (#698) |
| `self-update.sh` | out-of-tree | safe — writes into the shared plugin checkout, not the target repo |
| `directive.sh` | out-of-tree | safe — clones into the shared plugin checkout |
| `poll-rearm.sh` | out-of-tree | safe — shared function library sourced by `directive.sh`/`stop-poll-rearm.sh`; its checkout-clone fallback writes into the shared plugin checkout, same as `directive.sh` |
| `stop-poll-rearm.sh` | n/a | reads/validates only in its own file — no write call greppable in this file itself; the actual write happens via the sourced `poll-rearm.sh`'s `poll_rearm_arm_if_due()`, already recorded out-of-tree on that row, and (issue #2348) the sourced `hook-fires.sh`'s `hook_fires_record()`, recorded below |
| `hook-fires.sh` | n/a | issue #2348: shared library sourced by `directive.sh`/`stop-gate.sh`/`stop-poll-rearm.sh` — its embedded-python write is an append (`open(..., "a")`), which this gate's `open\([^)]*['"]w` pattern does not match (append-mode is not `"w"`-mode), so it lands in the n/a bucket the same way the `.orchestrate-hook-fires.log` `printf >>` write it replaces always has (a raw bash `>>` redirect was never matched by this gate either). The write itself (`.orchestrate-hook-fires/<sha256(session_id)[:24]>.log`, workspace-root-relative) is neither out-of-tree nor issue-scoped in this table's two-bucket sense — it is session-scoped: safe because two sessions never hash to the same shard, not because the path is outside the repo or carries an issue number |
| `impact-guard.sh` | out-of-tree | safe — same shared checkout clone |
| `spawn-allow-gate.sh` | n/a | reads/validates only, no write call |
| `merge-allow-gate.sh` | out-of-tree | safe — same `_checkout_resolve` shared-checkout-clone pattern as `impact-guard.sh`/`decision-queue-stopgate.sh` below, never inside the target repo |
| `gh-write-allow-gate.sh` | n/a | reads/validates only, no write call, no checkout resolution needed |
| `heredoc-command-refusal-gate.sh` | n/a | reads/validates only, no write call |
| `git-push-guard.sh` | n/a | reads/validates only (`git rev-parse`/`git config`/`git ls-remote`), no write call |
| `decision-queue-stopgate.sh` | out-of-tree | safe — same shared checkout clone |
| `accumulation-claim-guard.sh` | n/a | reads/validates only, no write call |
| `pretooluse-dispatcher.sh` | n/a | dispatch shim only (issue #2146) — no write call of its own; every write a dispatched gate body performs is that gate's own row above |
| `design-rationale-guard.sh` | n/a | reads/validates only, no write call |
| `accessibility-guard.sh` | n/a | reads/validates only, no write call |
| `api-version-guard.sh` | n/a | reads/validates only, no write call |
| `perf-measurement-guard.sh` | n/a | reads/validates only, no write call |
| `test-authoring-spawn-check.sh` | n/a | reads/validates only, no write call |
| `issue-retrospective-spawn-check.sh` | n/a | reads/validates only, no write call |
| `interaction-design-spawn-check.sh` | n/a | reads/validates only, no write call |
| `ux-engineering-spawn-check.sh` | n/a | reads/validates only, no write call |
| `approval-gate.sh` | n/a | reads/validates only, no write call |
| `call-shape-guard.sh` | n/a | reads/validates only, no write call |
| `claim-scan-preflight.sh` | n/a | reads/validates only, no write call |
| `absorbed-branch-recut-guard.sh` | n/a | reads/validates only — shells out to `spawn.py recut-if-absorbed`, which git-checkouts inside the target repo's own worktree, not a generated path |
| `contract-guard.sh` | n/a | reads/validates only, no write call |
| `deliverable-guard.sh` | n/a | reads/validates only, no write call |
| `delegation-post-gate.sh` | n/a | reads/validates only, no write call |
| `gate-registration-guard.sh` | n/a | reads/validates only, no write call |
| `gate-registration-post-guard.sh` | out-of-tree | safe — `$TMPDIR`-rooted (`${OTR_GRG_POST_STATE_DIR:-$TMPDIR/otr-grg-post}/<session_id>.json`), never inside the target repo, same pattern as `approach-cap-warning.sh` |
| `pr-preflight.sh` | n/a | reads/validates only, no write call |
| `pr-base-guard.sh` | n/a | reads/validates only, no write call |
| `record-claim-guard.sh` | n/a | reads/validates only, no write call |
| `credential-record-guard.sh` | n/a | reads/validates only, no write call |
| `credential-network-guard.sh` | n/a | reads/validates only, no write call |
| `upstream-defect-scope-guard.sh` | n/a | reads/validates only, no write call |
| `record-claim-shape-directive.sh` | n/a | reads/validates only, no write call |
| `record-tiering-directive.sh` | n/a | reads/validates only, no write call |
| `record-tiering-guard.sh` | n/a | reads/validates only, no write call |
| `report-framing-check.sh` | n/a | reads/validates only, no write call |
| `post-landing-obligation-gate.sh` | n/a | shells out to `gates/landing_obligation.py open` for the actual `.landing-obligations/<issue>-<role>-<pr>.json` write; the hook script itself makes no write call |
| `role-axis-completeness-guard.sh` | n/a | reads/validates only, no write call |
| `role-deviation-directive.sh` | n/a | reads/validates only, no write call |
| `role-spec-reference-guard.sh` | n/a | reads/validates only, no write call |
| `role-test-claim-guard.sh` | n/a | reads/validates only, no write call |
| `spec-index-preflight.sh` | n/a | reads/validates only, no write call |
| `amends-index-preflight.sh` | n/a | reads/validates only (calls `amends_index.check()`), no write call — the hook never calls `write_backlinks()`/`update()` itself, those are CLI-invoked landing-step actions |
| `test-tier-directive.sh` | n/a | reads/validates only, no write call |
| `requirement-digest-preflight.sh` | n/a | reads/validates only, no write call |
| `test-authoring-invariant-guard.sh` | n/a | reads/validates only, no write call |
| `stop-gate.sh` | n/a | reads/validates only, no write call |
| `live-fire-test-guard.sh` | n/a | reads/validates only, no write call |
| `acceptance-command-real-run-guard.sh` | n/a | reads/validates only + re-runs a recorded command via `subprocess.run` (no `write_text`/`open(..., "w")`/`.mkdir(`/`shutil.copy`/`move` call in its own staged text) |
| `live-fire-claim-real-run-guard.sh` | n/a | reads/validates only + re-runs a cited live-fire test via `subprocess.run(["python3", "-m", "pytest", ...])` (no `write_text`/`open(..., "w")`/`.mkdir(`/`shutil.copy`/`move` call in its own staged text) |
| `quality-bar-gate.sh` | n/a | reads/validates only (role record files, `git log`, `gh pr view`) — no `write_text`/`open(..., "w")`/`.mkdir(`/`shutil.copy`/`move` call in its own staged text; the `open_decision_item-*.md` path it names in a denial message is instructive text for the operator/next session to create, not a path this hook writes itself |

Out of scope (per docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md):
the warrant counter / hunt-report naming (core#200); human-authored file
collisions (write-scope territory); the `<seq>` auto-decision/remediation
counter under same-issue concurrent sessions; shared-checkout marker/clone
races in the out-of-tree hooks above.
