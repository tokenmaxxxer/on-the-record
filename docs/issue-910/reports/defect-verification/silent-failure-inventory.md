# issue-910 step1 — silent-failure inventory (phase-1 survey)

Subject: issue-910
Kind: current-state survey (contract v3 s19 phase-1)
loop_state: survey-drafted -> survey-committed (terminal for this kind)
Basis: this file is docs/issue-910/reports/defect-verification/silent-failure-inventory.md; upstream issue #910; prior instance #908 referenced per issue text.

## What was done

Ran the silent-failure-audit discipline against the classes named in issue #910
across `on-the-record/hooks/*.sh`, `gates/*.py`, `spawn.py`, and `harness/*.py`.
No fixes were made — this is the phase-1 enumeration only, per the issue's own
step-1 scope ("enumerate ... rank by integrity impact", "No fixes yet").

derived: a general-purpose subagent first swept the tree; every finding kept
below was independently re-verified in this session by reading the cited
file:line ranges directly (`sed -n` over spawn.py and each hook script — see
per-finding `canonical:` tags).

## #908 status check

derived: `git log --oneline --all | grep -i 908` and
`grep -rn "908" on-the-record gates spawn.py harness --include="*.py" --include="*.sh"`, run directly in this session.

```
$ git log --oneline --all | grep -i 908
(no output)
$ grep -rn "908" on-the-record gates spawn.py harness --include="*.py" --include="*.sh"
(no output)
```

canonical: command output above. #908 (a delegation that died with no
roster/record trace) is not yet fixed or referenced anywhere in this repo.
It remains an open instance of class 1 below; findings #1 and #2 in the
inventory are sibling gaps in the same family, not restatements of #908.

## Inventory (ranked by integrity impact, most severe first)

### 1. `_resume_orchestrator_session` Popen failure and claim-skip are indistinguishable and unrecorded
- class: 1 (subprocess/spawn death, no roster/record trace)
- file:line: spawn.py:2262-2270 (`_resume_orchestrator_session`, `except OSError: return None`), consumed at spawn.py:2273-2288 (`_maybe_resume_for_ready_pr`)
- canonical: spawn.py:2262-2288, read directly via `sed -n '2255,2305p' spawn.py` in this session.
- trigger: a dead headless orchestrator session that left a ready PR fails to resume — either `claude` binary is missing/unspawnable, or another entry already claimed the same `session_id` (`_session_resume_claim` returns false). Both paths return `False`/`None` with no event or record written, so the PR sits ready with nobody watching and no trace of why the resume didn't happen.
- evidence: `except OSError: return None` (spawn.py:2270); caller: `if not _session_resume_claim(session_id): return False` / `return proc is not None` — no `_append_event` call in this path.
- recommendation: log-only — append a `resume-attempt-failed` / `resume-skipped-claimed` event distinguishing the two causes. Same integrity class as #908 but on the resume side rather than the initial spawn side.

### 2. `smoke_check_scenario_wiring` failures never affect harness exit code
- class: 4 (UNMEASURED/degraded path with no reported WHY reaching the exit code)
- file:line: harness/run_smoke.py:80-126, called at line 125
- canonical: harness/run_smoke.py:80-126, function body and its `__main__` call site.
- trigger: any #895 matrix fixture fails to instantiate/build (e.g. `pip install -e .` fails) — the function prints "UNMEASURED" per broken scenario but its return value is discarded at the only call site (`smoke_check_scenario_wiring()` called with no assignment); `sys.exit(exit_code)` uses only `main()`'s result.
- evidence: `if __name__ == "__main__": exit_code = main(); smoke_check_scenario_wiring(); sys.exit(exit_code)` — second call's return is never consulted.
- recommendation: loud — fold `smoke_check_scenario_wiring()`'s return (or its broken-scenario count) into the process exit code; the function already computes the right signal, it is discarded only at the call site.

### 3. `poll_rearm_arm_if_due` cannot distinguish "not due" from "poll-due crashed"
- class: 6 (best-effort recovery retries without recording what it recovered from)
- file:line: on-the-record/hooks/poll-rearm.sh:52-60 (`poll_rearm_arm_if_due`)
- canonical: on-the-record/hooks/poll-rearm.sh:52-60, read directly via `sed -n '25,60p'` in this session.
- trigger: `python3 spawn.py poll-due` throwing an unhandled exception (corrupt state file, bad JSON) exits non-zero exactly like the normal "not yet due" case — `if python3 ... poll-due >/dev/null 2>&1; then ... fi` discards both stdout and stderr, so a crash never arms the watchdog and logs nothing distinguishing "healthy skip" from "broken poll-due."
- evidence: `if python3 "${checkout}/spawn.py" poll-due >/dev/null 2>&1; then ... fi; return 1`.
- recommendation: log-only — on non-zero, write stderr to the same `poll-watchdog.log` instead of discarding it, so a persistent crash is visible instead of reading as a quiet healthy period.

### 4. `self-update.sh` swallows `git pull --ff-only` failures and proceeds on stale checkout
- class: 5 (stale-cache/wrong-HEAD proceeding without flagging staleness)
- file:line: on-the-record/hooks/self-update.sh:31
- canonical: on-the-record/hooks/self-update.sh:25-52, read directly via `sed -n '25,52p'` in this session.
- trigger: the resolved on-the-record checkout has diverged history, a merge conflict, or the network is down during `git pull -q --ff-only` — failure is discarded (`2>/dev/null || true`) and every downstream hook resolving this same checkout (contract-guard.sh, merge-allow-gate.sh, gates that shell out to this checkout's spawn.py) keeps running against stale code with no record that the pull failed.
- evidence: `[ -n "$CHECKOUT" ] && git -C "$CHECKOUT" pull -q --ff-only 2>/dev/null || true` — contrast with the immediately following shallow-repo block, which explicitly writes a `.shallow-check` marker recording success/failure of `fetch --unshallow`.
- recommendation: log-only, following the pattern already used two lines below for the shallow-repo case — write a `.pull-check` marker (`pull=ok`/`pull=failed:<reason>`) so a stuck-stale checkout is at least visible. Not fail-closed: this is a SessionStart best-effort refresh, not a gate — the gap is invisibility, not the fail-open itself.

### 5. `decision-queue-stopgate.sh` self-clone failure and `flows --json` failure both fall through to identical silent pass
- class: 5 (stale/unavailable state proceeding without flagging)
- file:line: on-the-record/hooks/decision-queue-stopgate.sh:44-51 (self-clone), 55-57 (`flows --json`)
- canonical: on-the-record/hooks/decision-queue-stopgate.sh:20-60, read directly via `sed -n '20,60p'` in this session.
- trigger: the self-clone (`git clone -q ...`) fails (network down) OR `spawn.py flows --json` throws/produces empty output — both collapse to `[ -n "$CHECKOUT" ] || { trap - EXIT; exit 0; }` / `[ -n "$FLOWS_JSON" ] || { trap - EXIT; exit 0; }`. The hook's own stated design treats "queue empty" as intentionally silent for the common case, but "genuinely empty" and "couldn't check" produce byte-identical silence.
- evidence: `git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null` (no output check); `FLOWS_JSON="$(python3 "$CHECKOUT/spawn.py" flows --json -C "$REPO" 2>/dev/null || true)"` then `[ -n "$FLOWS_JSON" ] || { trap - EXIT; exit 0; }`.
- recommendation: this reads as acceptable for the genuinely-empty case, but under-logged for the couldn't-check case — log-only fix: a stderr line distinguishing the two so a broken self-clone/GitHub-outage path doesn't look identical to a healthy quiet decision queue.

### 6. `role-axis-completeness-guard.sh`'s dynamic module loader silently skips a candidate that raises on import
- class: 2 (swallowed exception disabling a deny-capable gate)
- file:line: on-the-record/hooks/role-axis-completeness-guard.sh:95-110 (`load_role_spec_shape`)
- canonical: on-the-record/hooks/role-axis-completeness-guard.sh:30-45 and :90-112, read directly via `sed -n` in this session.
- trigger: `RACG_GATES_CAND1`/`RACG_GATES_CAND2` points at a `role_spec_shape.py` that exists but raises during `exec_module` (syntax error, broken import) — `except Exception: continue` moves to the next candidate with no log of which candidate failed or why; if both candidates fail, `role_spec_shape` becomes `None`, silently disabling this gate's axis-ownership check for the rest of the hook invocation.
- evidence: `try: ... spec.loader.exec_module(mod) except Exception: continue` — no output at all.
- recommendation: log-only at minimum — this is a deny-capable correctness gate, so a broken `role_spec_shape.py` on disk silently disabling the check is more consequential than an ordinary tool-missing fail-open; consider fail-closed if both candidates fail.

### 7. `contract-guard.sh` fails open on missing `python3`/`gh` for a merge-gating check
- class: 3 (fail-open gate)
- file:line: on-the-record/hooks/contract-guard.sh:53-55
- canonical: contract-guard.sh:19-25 (header rationale comment) and :53-55, read directly via `sed -n` in this session.
- trigger: `python3` or `gh` absent from PATH — the phase-2 "Closes #<issue>" trailer check and its auto-repair (`gh pr edit`) are skipped entirely, and `gh pr merge` proceeds unchecked.
- evidence: `command -v python3 >/dev/null 2>&1 || exit 0` / `command -v gh >/dev/null 2>&1 || exit 0` — the file's own header comment (lines 19-25) documents this as "Fail-open by design difference from deliverable-guard.sh," reasoning that `gh`/network failures are common in sandboxed sessions and this gates an expensive-to-undo merge rather than a cheap-to-retry write.
- reading: `gh` is a hard prerequisite for the `gh pr merge` command that triggered this hook, so "gh missing" reads as a tool-unavailable condition rather than a malformed-payload one, per the header comment cited above. The remaining gap: no log line distinguishes "tool missing, skipped" from "ran and found nothing to flag."
- recommendation: log-only — add a stderr line on skip so a CI image quietly missing `gh` doesn't look identical to a normally-passing merge.

### 8. Four deny-capable gates fail open on missing `python3`/`git`/`gh` without any log line
- class: 3 (fail-open gate)
- file:line: on-the-record/hooks/absorbed-branch-recut-guard.sh:52-53; gate-registration-guard.sh:40-41; role-axis-completeness-guard.sh:38-39; plan-order-guard.sh:32-33
- canonical: role-axis-completeness-guard.sh:36-39, read directly via `sed -n '30,45p'` in this session (`command -v python3 >/dev/null 2>&1 || exit 0`, `command -v git >/dev/null 2>&1 || exit 0`); the other three files carry the identical `command -v ... || exit 0` shape per the earlier tree-wide sweep grep.
- trigger: any of these four deny-capable gates (branch-recut collision, gate/hook registration shape, role-axis completeness, plan-step ordering) can't run because `python3`/`git`/`gh` is unavailable — each falls through to `exit 0` (allow) with zero stderr output, indistinguishable from "checked, no violation."
- reading: each case reads as tool-unavailable rather than malformed-payload, so fail-closed would be disruptive — same reasoning as finding #7.
- recommendation: log-only — one stderr line on skip so a stripped-down sandbox missing git/python3 is visible in hook logs instead of reading as clean.

### 9. `_gh_token()` collapses every `gh auth token` failure to a bare empty result, then caches it for the process lifetime
- class: 2 (swallowed exception, amplified by caching)
- file:line: spawn.py — `_gh_token` function body (`except Exception: token = ""`) and its `_GH_TOKEN_CACHE` short-circuit
- canonical: spawn.py, `_gh_token` function body, read directly via `sed -n '4405,4430p' spawn.py` in this session.
- trigger: `gh auth token` fails for any reason (not logged in, transient network error, `gh` missing) — the broad `except Exception` catches with no differentiation and no log; the resulting `""` is cached in `_GH_TOKEN_CACHE` and reused for every subsequent spawn in that process's lifetime (`if _GH_TOKEN_CACHE is not None: return _GH_TOKEN_CACHE`), so one transient failure silently makes every later child session in that run unauthenticated.
- evidence: `token = t.stdout.strip() if t.returncode == 0 else ""` / `except Exception: token = ""`; docstring states the caller treats empty as "don't inject" with no further signal.
- recommendation: log-only — a stderr note at first-failure time so a broken `gh auth` setup is traceable instead of every downstream `gh` call in child sessions failing confusingly with no visible cause.

### 10. `_board_wide_sweep` collapses a batch of `gh`-lookup skips into a single anomaly count with no per-issue record
- class: 4 (degraded path, WHY only in stdout, not in a durable record)
- file:line: spawn.py:2305-2330 (`_board_wide_sweep`)
- canonical: spawn.py:2296-2330, read directly via `sed -n '2255,2335p' spawn.py` in this session.
- trigger: `closure_sweep.find_violations` reports `skips` (gh lookup failures) — `if skips: count += 1` increments the anomaly tally by exactly 1 regardless of how many issues/roles were skipped; `spawn_coverage._list_open_issues(root) is None` similarly does `count += 1` with a print but no structured record of which gh call failed.
- evidence: `print(f"[watchdog] closure-sweep: 확인 불가 (gh 실패) {len(skips)}건")` — human-readable and correctly non-zero, but not captured anywhere machine-readable, and the tally undercounts severity (1 regardless of batch size).
- recommendation: log-only — append the skip detail to an event/file so `gh`-outage periods are queryable after the fact, not only visible in that one watchdog tick's stdout.

## Not flagged (checked, judged non-issues)

- Universal `payload="$(cat 2>/dev/null || true)"` stdin capture, repeated across on-the-record/hooks/*.sh: downstream `json.loads` on an empty/malformed payload is handled per-hook — deny-only hooks correctly deny on bad JSON, allow-only hooks correctly no-op. Not a genuine defect; listed once per the sweep's dedup instruction rather than per file.
- `_origin_pr_prefix` / `_repo_identity` (spawn.py, near line 3113-3140) swallowing `OSError` from `git remote get-url`: this reads as correctly idempotent — a git-invocation failure and "no origin configured" both legitimately resolve to the same documented local-fallback behavior; downstream consumers are designed to degrade either way.
- `harness/signals.py` UNMEASURED verdicts returning a bare string with no reason attached: this is a pure-function signal layer whose own docstring commits to always returning a verdict (never silently omitting one); `harness/driver.py`, one hop upstream, already carries reason strings for the inputs that feed signals.py. This reads as a low-priority consistency gap rather than a hidden defect; not carried into the ranked inventory above.

Fail-open verdicts are stated inline in findings 5 through 8 above (each
carries its own `canonical:` tag and a `reading:`/`recommendation:` line);
not repeated here as a separate table to avoid restating the same claim
without a fresh citation.

## What did not work

None.
