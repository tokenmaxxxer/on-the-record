---
issue: 2749
role: silent-failure-audit-bbfffc81
author: silent-failure-audit-bbfffc81
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/hooks/self-update.sh
    sha: a4e0e6cbe58b2a9dea1ec77312b93f610c962ef2
  - path: spawn.py
    sha: a4e0e6cbe58b2a9dea1ec77312b93f610c962ef2
---

# issue-2749 — silent-failure-audit-bbfffc81 record

## What was done

CORE_BUILD_NOW=1 was set (spawner env — `checked: printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW" — result: CORE_BUILD_NOW=1`), so this delivered directly under contract v3 s19a (build-now bypass) — no phase-1 proposal round.

`on-the-record/hooks/self-update.sh` (commit a4e0e6cb) used to run `git pull --ff-only` unconditionally on every `SessionStart` firing — the working-tree merge that swaps the code every hook in the checkout executes from. Fixed: it now runs only `git fetch` (refs/objects only, never the working tree) and records the checkout's behind-origin state to `.pull-check` (`pull=ok` / `pull=deferred:<n>-behind-origin` / `pull=unknown:<reason>` / `pull=failed:fetch:<reason>`), but never merges.

Added `spawn.py self-update` (`self_update_pull_cli()`, commit a4e0e6cb) as the deliberate replacement for the working-tree advance: it refuses (non-zero exit, no `git pull` invoked) when the roster can't be read, the spawn-claim scan is unreliable, or any session is live (reusing `roster._roster_load_checked`/`_alive`/`_claim_only_live_sessions`, the same primitives `spawn.py ps` already trusts); with zero live sessions it runs `git pull --ff-only` and records the outcome. This is the same "zero sessions running at pull time" discipline issue #2670's final comment describes running by hand, now a named, checkable command.

`docs/specs/enforcement-boundary.md`'s `self-update.sh` row was updated to describe the new fetch-only/deferred-advance shape (commit a4e0e6cb).

Two new test files (commit a4e0e6cb) exercise both sides live:

```
canonical: git show a4e0e6cb --stat -- test/test_self_update_pull_gate.py test/test_self_update_working_tree_untouched.py
 test/test_self_update_pull_gate.py            | 141 ++++++++++++++++++++
 test/test_self_update_working_tree_untouched.py | 123 +++++++++++++++++
```

- `test/test_self_update_pull_gate.py`: `self_update_pull_cli()` pulls and records `pull=ok` with zero live sessions; refuses and leaves the working tree untouched with a live roster session; refuses on an unreadable roster; is a no-op success when already current.
- `test/test_self_update_working_tree_untouched.py`: the real shipped `self-update.sh` never advances the working tree regardless of remote state (up to date / one commit behind / unreachable origin), while `.pull-check` still records the true state in every case.

```
checked: python3 -m pytest test/test_self_update_pull_gate.py test/test_self_update_working_tree_untouched.py -q — result: 7 passed in 0.98s
```
(4 cases in the first file + 3 in the second = 7, `derived: grep -c "def test_" test/test_self_update_pull_gate.py test/test_self_update_working_tree_untouched.py` -> `4` / `3`)

**Full suite, no regression** — same failing-test set before and after, as sets of names:

```
derived (baseline, this issue's diff stashed): python3 -m pytest -q — result: 16 failed, 572 passed, 3 xfailed in 33.18s
derived (with this issue's diff): python3 -m pytest -q — result: 16 failed, 579 passed, 3 xfailed in 33.20s
```
579 - 572 = 7, exactly the 7 new tests added; both runs' 16 `FAILED` lines are the identical set of test IDs (pre-existing environment failures: `git fetch` against a fixture with no real `origin` remote, and one unrelated `test_convention_equivalence.py` assertion already failing on origin/main) — compared by literal diff of the two `short test summary info` blocks in this session, not re-typed by hand.

**No overhead increase** — the new fetch+rev-list sequence is not slower than the old pull it replaces:

```
derived: (10x old self-update.sh, checkout already current) time ( for i in $(seq 1 10); do TOKENMAXXXER_CHECKOUT=... bash old-self-update.sh </dev/null >/dev/null 2>&1; done ) — result: real 0m0.494s
derived: (10x new self-update.sh, same setup) — result: real 0m0.438s
```

**No return of the retired role axis:**

```
derived: git diff a4e0e6cb^..a4e0e6cb -- on-the-record/hooks/self-update.sh spawn.py | grep -inE '\brole\b' — result: only pre-existing context lines (a.role ==, the pre-existing argparse dispatch attribute untouched by this diff, and one pre-existing docstring line); zero added (+) lines match
```

**Monitor/watch machinery unbroken and not quieter** — untouched by this diff and still green:

```
checked: python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py -q -m "not slow" — result: 8 passed in 1.16s
```

## Why

**The question the issue asks: does the orchestrator control when the checkout advances, or does the hook?** Answer: the orchestrator does — `self-update.sh`'s automatic advance had to yield, not the orchestrator's deferred-pull discipline.

**Against #2670's hazard analysis.** #2670's own closing comments (`canonical: gh issue view 2670 --repo tokenmaxxxer/on-the-record --comments`, final two comments) state the rule directly:

```
"the hazard here was the pull, not the merge, because hooks execute from
the marketplace checkout." / "the operative rule is zero sessions running
at pull time... Session count was checked at every step and was 0
throughout; no window was opened."
```

That rule was enforced by hand for #2670's own landing. `self-update.sh`'s unconditional `git pull --ff-only` on every `SessionStart` bypassed it structurally — it advances the shared checkout regardless of how many other sessions are reading from it, on a firing frequency (`startup`, `resume`, `clear`, `compact`, `fork` — `derived: WebFetch https://code.claude.com/docs/en/hooks` — "how the session started" / example matcher values for the `SessionStart` event) far higher than "once per deliberate orchestrator action."

**Against #910 finding #4's staleness argument.** `docs/issue-910/reports/defect-verification/silent-failure-inventory.md` finding #4's own recommendation:

```
"recommendation: log-only, following the pattern already used two lines
below for the shallow-repo case -- write a `.pull-check` marker
(`pull=ok`/`pull=failed:<reason>`) so a stuck-stale checkout is at least
visible. Not fail-closed... the gap is invisibility, not the fail-open
itself."
```

Nothing in that recommendation requires the pull to run on every hook firing — it requires the *outcome* to be recorded, never dropped. `git fetch` (kept unconditional) plus the new `deferred`/`unknown` marker states satisfy that bar without ever touching the working tree; `spawn.py self-update` still writes `pull=ok`/`pull=failed:...` when it actually runs. Live-exercised (own reproduction, not the pytest suite): a checkout deliberately left one commit behind origin, with the pre-#2749 `self-update.sh` run against it as a `SessionStart` firing would, silently advanced and pulled in the new file:

```
derived: TOKENMAXXXER_CHECKOUT=<fixture> bash <pre-#2749 self-update.sh> — result:
  checkout HEAD after OLD hook fired: 63173af... (== origin's new HEAD)
  hooks_changed.txt present in working tree? yes
  .pull-check: pull=ok
```

The same fixture, one commit behind, against the fixed hook:

```
derived: TOKENMAXXXER_CHECKOUT=<fixture2> bash on-the-record/hooks/self-update.sh — result:
  checkout HEAD after FIXED hook fired: 5bec3b3... (unchanged)
  hooks_changed.txt present in working tree? no
  .pull-check: pull=deferred:1-behind-origin
```

And the deliberate advance, same fixture2, zero live sessions:

```
derived: python3 -c "...spawn.ROOT=<fixture2>; spawn.self_update_pull_cli()..." — result:
  self-update: <fixture2> 를 최신으로 당겼다 (살아있는 세션 0)
  checkout2 HEAD now: 63173af... (== origin)
  .pull-check now: pull=ok
```

That is the issue's acceptance bullet 2 ("start a session, merge a hook change, show what the session observes — before and after") and bullet 3 (the stale-checkout case still fails loudly, not silently) exercised end to end.

**Why `git fetch` stays unconditional while the advance does not.** `git fetch` only updates refs/objects; it never touches the working tree, so no session reading from the checkout's files can observe it happening. `git pull`/`git merge --ff-only` rewrites the working tree those same files live in — that is the literal mechanism behind "the pull, not the merge, is the hazard."

**Rejected alternative: restrict `self-update.sh`'s `SessionStart` matcher to `startup`+`resume` only** (excluding the mid-process `clear`/`compact`/`fork` firings, via `hooks.json`'s per-event `matcher` field — `derived: WebFetch https://code.claude.com/docs/en/hooks`, the `SessionStart` matcher-values table). This was the first design considered — it directly targets the "an in-flight session's own hooks change under it mid-turn" framing. Rejected because it only protects the session whose *own* `SessionStart` fired; it does nothing for *other* concurrently-running sessions sharing the same checkout directory, which is exactly the issue's reflog evidence — a fresh session's ordinary `startup` is the common case, not a rare mid-process event, so this alternative leaves the dominant hazard path open.

**Rejected alternative: leave `self-update.sh` fully in charge but gate its own pull on a live-session check inline in the shell hook.** Preferred instead: put the check in `spawn.py`, reusing the liveness-check functions `spawn.py ps` already calls —

```
canonical: spawn.py self_update_pull_cli(), commit a4e0e6cb:
    d, load_error = _roster_load_checked()
    ...
    live_roster = [(key, e.get("pid")) for key, e in d.items()
                   if _alive(e.get("pid", 0))]
    claim_only, claim_warnings = _claim_only_live_sessions(d)
```

A bash `SessionStart` hook has no equally direct path to that same Python machinery; porting it into shell/heredoc would mean a second copy of the same logic to keep in sync. Beyond that reuse consideration, a design preference: keeping the working-tree advance behind an explicit, separately-invoked `spawn.py self-update` command, rather than a gated-but-still-automatic hook, is what makes advancing the checkout "a deliberate act with a visible moment" (the issue's own phrase for the deliverable) — an orchestrator (or a person) has to actually run it.

skill-verdict: silent-failure-audit — applied: invoked; audited `self-update.sh`'s and `self_update_pull_cli()`'s error-handling sites (fetch failure, rev-list failure, roster-load failure, claim-scan failure, subprocess pull failure, `.pull-check` write itself) via the skill's Handled/Silently-Absorbed/Unreachable procedure. One Silently-Absorbed site found and fixed in this delivery:

```
canonical: spawn.py (commit a4e0e6cb), _pull_check_write():
  try:
      marker.write_text(line + "\n")
  except OSError as exc:
      print(f"경고: .pull-check 기록 실패({exc}) — 위 stdout 결과가 유일한 기록이다",
            file=sys.stderr)
```

— originally a bare `except OSError: pass`; changed to a stderr warning since `self_update_pull_cli()` (unlike the fire-and-forget hook) always has a console attached and should not let a marker-write failure be the one silent path left. `self-update.sh`'s own pre-existing `2>/dev/null || true` marker-write pattern was left unchanged: it is out of this issue's diff, and #910 already reviewed and accepted it as intentionally best-effort for a non-blocking `SessionStart` hook.

skill-verdict: work-in-english — applied: invoked; no project-convention conflict found — this delivery's English/Korean split already matches the existing per-file convention (`self-update.sh`'s comments are English like the rest of that file; `spawn.py`'s user-facing CLI `print()` lines are Korean like `roster_ps()`'s and the file's other `_cli` functions).

## What did not work

- Expected `python3 gates/spec_index.py --update` to regenerate `docs/specs/reconciled-index.md` after editing `docs/specs/enforcement-boundary.md` (mandatory per this session's spawn directive). It crashes instead:

```
derived: python3 gates/spec_index.py --update — result:
FileNotFoundError: [Errno 2] No such file or directory: '.../roles/specs/brand-design.spec.json'
```

  That path was deleted by an unrelated prior commit that never updated `gates/spec_index.py`'s own reference to it (`checked: git log --oneline -1 -- roles/specs/brand-design.spec.json — result: 480d1a78 issue-2539: Stage 6C -- consolidate roles/ into spawn_roles.json, delete roles/ + roles/specs/ (#2542)`). Confirmed pre-existing and unrelated to this issue's diff:

```
derived: git stash push -u -- <this issue's changed files> && python3 gates/spec_index.py --update; git stash pop — result: identical FileNotFoundError on the unmodified origin/main tree
```

  Left unfixed here (out of #2749's scope — a `docs/specs/*` edit crashing this generator is its own, unrelated defect); `docs/specs/reconciled-index.md` is therefore not regenerated in this delivery.

## Upstream basis

- `on-the-record/hooks/self-update.sh` — sha a4e0e6cbe58b2a9dea1ec77312b93f610c962ef2 (this delivery's own fix).
- `spawn.py` — sha a4e0e6cbe58b2a9dea1ec77312b93f610c962ef2 (this delivery's own `self_update_pull_cli()` addition).
- `docs/specs/enforcement-boundary.md` — sha a4e0e6cbe58b2a9dea1ec77312b93f610c962ef2 (this delivery's own row update).
- `docs/issue-910/reports/defect-verification/silent-failure-inventory.md` finding #4 — pre-existing, read via `sed -n '63,69p'` in this session; the staleness bar this fix had to keep meeting.
- #2670's final two issue comments (`gh issue view 2670 --repo tokenmaxxxer/on-the-record --comments`) — pre-existing; established "the hazard is the pull, not the merge" and "zero sessions running at pull time" as the operating rule this fix now enforces mechanically instead of by hand.

## Open findings

1. **`watchdog.py`'s `watchdog_freshness_check()` (`watchdog.py:1277-1317`, reached from `spawn.py`'s `watchdog` subcommand, `spawn.py:2295-2328`) also runs an unconditional `git fetch` + `git merge --ff-only` against the same shared checkout on every tick it hasn't already fetched this tick**, independent of `self-update.sh` and of this fix:

```
canonical: watchdog.py:1293-1298
    if not fetched_this_tick:
        subprocess.run(["git", "-C", str(cwd), "fetch", "--quiet", "origin"],
                        capture_output=True, text=True)
        pull = subprocess.run(["git", "-C", str(cwd), "merge", "--ff-only",
                                "--quiet", "origin/HEAD"],
                               capture_output=True, text=True)
```

   It has its own visibility mechanism for the *watchdog process itself* (HEAD-changed detection -> `WATCHDOG_STALE_CODE_SENTINEL` exit 95, presumably a supervised restart), but that visibility is scoped to the watchdog's own process — it gives no signal to any *other* concurrently-running role session sharing the same checkout, whose working tree this merge equally advances out from under it. This is plausibly a second, independent contributor to the reflog shape the issue cites — unconfirmed: the issue's own citation is `self-update.sh:42` only, and this session did not instrument a live watchdog tick to attribute specific reflog entries to it. Left unresolved here: it is a materially different code path (a single-instance, lock-guarded, long-running process with its own self-restart design) than the `SessionStart` hook this issue names, and folding it into this delivery would have widened the diff well past the issue's Ask and Acceptance. Recommend a follow-up issue: route `watchdog_freshness_check()`'s merge step through the same "zero *other* live sessions" gate `self_update_pull_cli()` now uses (its own fetch can stay unconditional for the same refs-vs-working-tree reason), deferring the merge one tick when sessions are live rather than skipping detection.
2. The `python3 gates/spec_index.py --update` breakage documented under "What did not work" above is its own pre-existing defect (unrelated `roles/specs/` path deleted by #2542 without updating this generator) — worth its own issue, separate from #2749.

## Next steps

None — `loop_state: landed`.
