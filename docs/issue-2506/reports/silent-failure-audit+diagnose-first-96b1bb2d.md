---
issue: 2506
role: silent-failure-audit+diagnose-first-96b1bb2d
author: silent-failure-audit+diagnose-first-96b1bb2d
skills: silent-failure-audit (skill-repository(297e350)), diagnose-first (skill-repository(297e350))
loop_state: landed
upstream:
  - path: gh issue 2506 (body + 2 comments) — build-now bypass, no phase-1 proposal doc; branch point this fix was built against
    sha: dc4e9f134fc7fc1421737a4f715b3b50580cd997
code_under_review:
  - consult.py:366-441 (`_CONSULT_TRACE_REF`, rewritten `_commit_consult_trace()`)
  - spawn.py:2566-2632 (`checkout_staleness()`, new)
  - gates/merge_gate.py:283-301 (`evaluate()` checkout-staleness preflight)
type: fix
breaking: internal-only — `consult._commit_consult_trace()`'s git side-effect changed (commits now land on `refs/heads/otr-consult-trace` instead of the checked-out branch); its signature and every call site are unchanged. `merge_gate.evaluate()`'s return dict gained an optional `checkout_staleness` key; existing keys (`allowed`, `reasons`, `staleness`) are unchanged, so `verdict_gate.py` and any other caller keep working unmodified.
verdict: pass
---

# issue-2506 — silent-failure-audit+diagnose-first-96b1bb2d record

canonical: `gh issue view 2506` output, read at session start:

```
## Ask
The orchestrator's own checkout (`~/.claude/plugins/marketplaces/tokenmaxxxer`) had **153 local commits on `main` that were never pushed**...
```

canonical: `gh issue view 2506 --comments` output, read at session start — the 2026-08-27 comment quoted verbatim:

```
$ git status -sb
## main...origin/main [앞에: 18, 뒤에: 9]

$ git log --oneline origin/main..HEAD | grep -cv 'consult-trace'
0
```

skill-verdict: silent-failure-audit — applied: invoked; audited the new error-handling paths in `consult.py::_commit_consult_trace()` and `spawn.py::checkout_staleness()`. Found and fixed two Silently-Absorbed sites — `consult.py:408` now distinguishes a real `rev-parse` error (nonzero exit with stderr despite `--quiet`) from the expected "ref doesn't exist yet" case (nonzero exit, empty stderr), instead of treating both the same way; `spawn.py:2616` and `spawn.py:2626` now return `checked: False` when `merge-base --is-ancestor`/`rev-list --count` themselves fail, instead of the original draft's fallthrough that would have silently reported `behind: 0` (confidently "not stale") on a git error. derived: `python3 -m pytest test/test_consult_trace_commit.py::CommitConsultTraceTest::test_rev_parse_error_is_not_silently_read_as_missing_ref test/test_checkout_staleness.py::CheckoutStalenessTest::test_merge_base_error_is_not_silently_read_as_fresh -q` — result: 2 passed (both tests inject a simulated git error via `mock.patch("subprocess.run", ...)` and assert the function reports failure/uncertainty rather than silently proceeding as if nothing were wrong).
skill-verdict: diagnose-first — not-applicable: invoked to check applicability first (see the two `canonical:` codefences above this line — the issue body and its 2026-08-27 comment already supply a fully-verified root cause, with reproduction commands and their literal output, before any fix was written this session). The skill's own "does this even need the procedure" gate reads: "Is the cause already confirmed and agreed? ... then just do the task" — that is the case here, so the gated diagnose-before-act procedure does not apply.
skill-verdict: work-in-english — not-applicable: no cross-cutting language decision was needed this session. derived: `git log --oneline -5` — result: every one of the 5 most recent commit subjects (e.g. `dc4e9f13 issue-2238: fix spawn-on-pr park guard re-arming...`) is in English, matching this session's own commit message; new code comments in `consult.py`/`spawn.py`/`gates/merge_gate.py` are Korean, matching every pre-existing comment in those same files (checked by reading each file this session) — same repo-convention-override judgment as `docs/issue-2574/reports/implementation.md`'s skill-verdict line.
skill-verdict: merge-gates — applied: invoked; ran the four-property shape test and configuration-holes audit against the new `checkout_staleness()` preflight in `gates/merge_gate.py::evaluate()` — see ## Why for the property-(c) finding and ## Open findings for the scope limit it surfaced.

## What was done

One commit (`85f7b6f6`), three changes:

1. **`consult.py:366-441`** — `_commit_consult_trace()` no longer commits consult traces onto the checked-out branch (`main`, in the orchestrator's own checkout). It now writes each trace commit to a dedicated ref, `_CONSULT_TRACE_REF = "refs/heads/otr-consult-trace"`, built through an isolated temporary index (`GIT_INDEX_FILE`) that never touches `HEAD`, the current branch, or the shared repo index — only the real object database receives the new blob/tree/commit objects. Concurrent writers (e.g. the background-fork consult path, issue #2569) retry on `git update-ref <ref> <new> <old>` compare-and-swap failure, up to `_CONSULT_TRACE_COMMIT_RETRIES = 5` times. Working-tree trace files are untouched — they stay on disk at the exact paths `_consult_log_aggregate()` already globs; nothing about "one trace line per consult" changed.

   Acceptance bullet 1 requirement met — derived: `python3 -m pytest test/test_consult_trace_commit.py -q` — result: 5 passed. `test_main_head_never_moves_across_n_consults` is the bullet's literal demonstration: it runs 3 consults against a scratch origin+clone, then runs `git merge-base --is-ancestor origin/main main` and asserts return code 0. `test_trace_ref_accumulates_every_commit` confirms no trace is dropped (3 consults → 3 commits on the side ref). `test_working_tree_files_survive_and_stay_untracked_on_main` confirms the on-disk trace file content is untouched.

2. **`spawn.py:2566-2632`** — new `checkout_staleness(root=ROOT, fetch=True)`. Fetches `origin` (best-effort — a failed fetch does not block the check; per the issue, blocking gates entirely on a network hiccup is worse than comparing against the last known `origin/HEAD`). Compares local `HEAD` against `origin/HEAD` via `git merge-base --is-ancestor` + `git rev-list --count`. Returns `{"checked": bool, "stale": bool, "behind": int, "fetch_ok": bool, "detail": str}`. Never runs `reset`/`checkout`/`merge` — fetch and compare only, per the issue's must-not.

3. **`gates/merge_gate.py:283-301`** — `evaluate()` calls `checkout_staleness()` first. When `checked and stale`, it returns `{"allowed": False, "reasons": ["checkout-stale (코드 결함 아님...): <behind-count and shas>"], "checkout_staleness": {...}}` immediately — before `check_runner.fetch_all_role_branches()`, `required_verification_missing()`, or any of the other existing checks run. That early return is the fix: the issue's reproduced failure was `_exempt_own_role` (now `_exempt_own_record_kind`) being evaluated from a stale tree and answering confidently; this makes that entire downstream evaluation unreachable once staleness is detected. `verdict_gate.py` inherits the same protection for free, since it calls `merge_gate.evaluate()` rather than duplicating its logic.

   Acceptance bullet 2 requirement met — derived: `python3 -m pytest test/test_checkout_staleness.py -q` — result: 7 passed. `test_deliberately_stale_checkout_is_flagged_with_count` is the bullet's literal demonstration: a checkout deliberately held one commit behind a scratch origin reports `checked: True, stale: True, behind: 1`, with a detail string naming the staleness. `test_current_checkout_is_not_stale` and `MergeGateRefusesOnStaleCheckoutTest.test_legitimately_current_checkout_is_not_blocked` pin the must-not (a legitimately-current checkout is never blocked). `test_staleness_check_never_mutates_the_working_tree` pins the other must-not (HEAD and `git status` are byte-identical before/after the check).

derived: `python3 -m pytest test/ -q` — result: 15 failed, 308 passed. The 15 failures are pre-existing and unrelated to this change — derived: `git stash && python3 -m pytest test/test_convention_equivalence.py test/test_local_dependency_env.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_artifact_skill_pairing.py test/test_spawn_skill_judge_haiku_timeout_overlap.py -q; git stash pop` (run against the pre-session commit `dc4e9f13`) — result: the identical 15 failure names reproduced with zero code from this session present.

## Why

**Why a side ref instead of no commit at all.** The acceptance bullet offers two options: "traces are written without a commit, or committed somewhere that does not block main from fast-forwarding." Issue #1134's original rationale for auto-committing at all was "a record that exists only as local uncommitted state is not a record" (northpole req#2, quoted verbatim in `consult.py`'s pre-existing docstring at the time this session started). Dropping the commit entirely would revert that guarantee for every future trace. A side ref keeps every trace committed (durable, `git log <ref>`-visible, survives a `git clean`) while structurally decoupling it from `main`'s fast-forward eligibility — nothing on this path ever touches `main`'s ref again, so it cannot recur through this code path.

**Why an isolated temp index instead of `git stash` / a branch switch.** Switching the checked-out branch to commit traces elsewhere would disrupt whatever else the orchestrator process is doing concurrently in that same working tree, and would temporarily move the trace directory `_consult_log_aggregate()` reads by path (not `git show`). `GIT_INDEX_FILE` lets `git add` / `write-tree` / `commit-tree` build a commit against the real object database without ever moving `HEAD` or touching the real index — same object store, a disconnected lineage, zero disruption to the checkout's current branch.

**Why the gate check is fetch-then-compare, never mutate.** The issue's must-not is explicit: "must not auto-mutate the operator's working tree (fetch and compare is fine; reset/checkout is not)." `checkout_staleness()` only ever runs `fetch`, `rev-parse`, `merge-base --is-ancestor`, and `rev-list --count` — none of which change the working tree or `HEAD`.

**Why uncertain cases fail open (merge-gates skill finding).** Invoking the `merge-gates` skill's four-property shape test flags property (c) — "fail-closed: absence, error, timeout, or skip yields anything other than 'blocked'" — as failed by design here: a checkout with no `origin` remote, or one where `origin/HEAD` can't be resolved (or where `merge-base`/`rev-list` themselves error rather than answer), returns `checked: False` and is *not* blocked. This is a deliberate, issue-mandated exception to the general gate convention, not an oversight: the issue's own empty-state clause is "a fresh checkout with zero local commits — the staleness check is a no-op," and its must-not forbids blocking a legitimately-current checkout. Failing closed on every ambiguous case would block gates in exactly the synthetic-test-repo and fresh-clone scenarios the issue protects. The one case the bullet actually targets — genuinely, measurably behind origin — still fails closed (`allowed: False`, named reason, computed before any other check runs).

**Why this covers `merge_gate.py`/`verdict_gate.py` and not the other gate scripts.** The issue's concrete reproduction (PR #2493's refusal) and acceptance bullet 2 both center on this one gate. Wiring `checkout_staleness()` into every gate entrypoint in the repo was out of scope for this fix — recorded as a residual gap in ## Open findings rather than silently left uncovered.

## What did not work

None.

## Disclosure: how many 2026-08-26 gate verdicts came from the stale tree

unverifiable: the count cannot be recovered — checked three independent places for a durable, date-keyed record of individual `merge_gate.py` invocations and found none in any of them.

derived: `grep -n "ledger_write\|ledger\." gates/merge_gate.py gates/verdict_gate.py gates/gates.py` (this repo) — result: no matches. Neither gate writes its verdict to any ledger; both only print to stdout, which is only as durable as whatever process captured that stdout.

derived: `wc -l runs/ledger.jsonl && grep -c 2026-08-26 runs/ledger.jsonl`, run read-only from the live orchestrator checkout (env var `ON_THE_RECORD`, no writes made there) — result: 80 lines total, 0 mentioning `2026-08-26`. Not a historical log reaching back to that date.

derived: `wc -l runs/spawn-attempts.jsonl`, same checkout — result: 6 lines total; none mention `merge_gate` or `gate` (checked by reading the full 6-line file directly). Not a log of gate invocations at all.

canonical: `gh pr view 2493 --json comments,state,createdAt,mergedAt` output, read this session — the PR the issue names as the live incident (state: MERGED, created 2026-08-26T02:13:28Z, merged 2026-08-26T03:12:34Z). Its two GitHub comments (2026-08-26T02:53:21Z, 2026-08-26T03:12:28Z) record a *different* refusal as the operator's landing basis — a `no_checks: True` / Acceptance-format finding — not the "필요한 검증 기록이 없다: ['execution-observation']" refusal the issue's own prose quotes. That specific stale verdict was evidently observed directly by the operator (a terminal/session transcript, not a GitHub artifact) and never became a durable, `gh`-queryable comment.

Given no code path in this repository persists a merge-gate verdict keyed by date, and the one PR named as a concrete instance does not carry the specific stale verdict as a comment, the honest answer is: the number of 2026-08-26 gate verdicts produced from the stale tree cannot be recovered from anything durable in this repository or the live orchestrator checkout. That absence is itself part of the case for this fix — a verdict consequential enough to trigger a duplicate spawn against already-completed work left no trace of its own wrongness anywhere queryable. `checkout_staleness()`'s named reason, folded into `evaluate()`'s `reasons` list and printed by every caller (`merge_gate.py`'s own CLI and `verdict_gate.py`), at least makes the failure visible in the one place a human or the orchestrator is already looking: the gate's own output.

## Open findings

- **Scope limit, not a defect**: `checkout_staleness()` is wired into `gates/merge_gate.py::evaluate()` only (and transitively `verdict_gate.py`, which calls it). derived: `grep -rln "checkout_staleness" gates/` — result: only `gates/merge_gate.py` calls it. The other gate scripts under `gates/` each run standalone and do not call through `merge_gate.evaluate()`, so they remain exposed to the same "stale checkout, confident wrong verdict" class this issue targets. Resolution path: lift the `checkout_staleness()` call into a shared preflight used by every gate's `main()` in a follow-up issue — not done here, to keep this change bounded to the issue's concretely-reproduced failure (`merge_gate.py`).
- **`fetch_ok` is returned but not consumed**: canonical: `gates/merge_gate.py:295-301` (this session's own edit, quoted in full above under ## What was done, item 3) never reads `checkout["fetch_ok"]`. `checkout_staleness()`'s return dict carries it for future callers that might want to distinguish "confirmed current" from "current per possibly-stale cached knowledge," but nothing branches on it today. Not a defect — the value is exposed, not hidden — but noted so it isn't mistaken for telemetry that's actually tracked or alerted on anywhere.
- The watchdog's `코드-신선도` message only reports "HEAD changed since startup," never "checkout is behind origin" — the exact asymmetry the issue's second comment names ("noisy about the benign case and silent about the harmful one"). canonical: `watchdog.py:1280-1294` (read this session, unmodified by this fix):

```python
    if not fetched_this_tick:
        subprocess.run(["git", "-C", str(cwd), "fetch", "--quiet", "origin"],
                        capture_output=True, text=True)
        pull = subprocess.run(["git", "-C", str(cwd), "merge", "--ff-only",
                                "--quiet", "origin/HEAD"],
                               capture_output=True, text=True)
        del pull  # 실패해도(로컬 커밋 등) advisory — HEAD 비교로 판정한다
    current = _sp.watchdog_current_head(cwd)
    if current is None:
        return True, ""
    if current == startup_head:
        return True, ""
    msg = (f"[watchdog] 코드-신선도: 체크아웃 HEAD 가 바뀌었다 "
           f"(시작={startup_head[:12]} 현재={current[:12]}) — "
           f"재기동 필요")
```

  This session did not touch `watchdog.py`: the formal acceptance bullets target gate verdicts, not this advisory log line. Mechanically, though, the `git merge --ff-only origin/HEAD` shown above should now succeed on every tick going forward instead of failing silently against a diverged `main` — because `_commit_consult_trace()` no longer advances `main` at all, the thing that was making that `--ff-only` merge fail every time is gone. Left as a residual finding rather than silently dropped, per the silent-failure-audit skill's own gate ("every fallible operation... mapped to at least one error-handling site, or explicitly noted as unguarded").

## Next steps

None — `loop_state: landed`.
