---
issue: 2139
role: silent-failure-audit-212d2fc6
author: silent-failure-audit-212d2fc6
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: same-commit
type: fix
breaking: false
verdict: fixed
upstream:
  - path: docs/issue-2139/reports/adversarial-review-6cda09d1.md
    sha: dfb632ad520efd43e69a7feab038ccb73f3db36f
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/2869
    sha: 0562882dbdfcac518e98866f3ba5ddb0cfc07cdd
---

# issue-2139 — silent-failure-audit-212d2fc6 record

## What was done

Round 2 on PR #2869, responding to the reproduced regression and the
deferred finding raised by `docs/issue-2139/reports/adversarial-review-6cda09d1.md`
(merged as #2873). Merged PR #2869's branch (`issue-2139/overengineering-audit-ecf2ec0d`,
head `0562882d`) into this branch, then made two fixes on top, both
committed at `22fc3f80ea6de4ce8d1c52354aa80f74a43dff94`:

**1. Fixed the reproduced regression.** `harness/fixture-concurrent-judgment/test_panel.py:51-52`
asserted the retired `"role=qa"`/`"role=review"` literal trace-field text;
`_append_panel_turn()` (consult.py:1608) now writes `skill={skill}`. Updated
the two assertions to `"skill=qa"`/`"skill=review"`.

canonical: `python3 -m pytest harness/fixture-concurrent-judgment/test_panel.py -q` — run this session, this turn — result:
```
2 passed in 0.85s
```

**2. Established the unguarded-test-population, without enumerating directories.**
The task asked what else lives outside `test/` and is therefore unguarded
by a check scoped to `pytest test/`. `pytest.ini` at repo root sets no
`testpaths` restriction — it only carries a `norecursedirs` list
(`runs harness/fixture-redtest harness/fixture-target`) — so `python3 -m
pytest .` run from the repo root already collects every real test file
in the tree, not just `test/`, with no enumeration needed.

canonical: `python3 -m pytest --collect-only -q . 2>&1 | grep -E "^(bench|gates|harness|ledger|on-the-record|tests)/" | sed -E 's/::.*//' | sort -u` — run this session, this turn — result:
```
bench/test_ablation.py
gates/test_spawn_on_pr.py
harness/fixture-ambiguous/test_fixture_ambiguous.py
harness/fixture-arcade/test_arcade.py
harness/fixture-concurrent-judgment/test_panel.py
harness/fixture-feature/test_fixture_feature.py
harness/fixture-infeasible/test_fixture_infeasible.py
harness/fixture-multimod/test_fixture_multimod.py
harness/fixture-multirole/test_fixture_multirole.py
harness/fixture-operator-experience/test_flow.py
harness/test_driver.py
harness/test_signals.py
ledger/test_decisions.py
on-the-record/monitors/test_poll_heartbeat.py
tests/test_cross_checkout_prune_liveness.py
tests/test_directive_diet_2135.py
tests/test_tmp_resource_gc.py
```
derived: `python3 -m pytest --collect-only -q . 2>&1 | grep -E "^(bench|gates|harness|ledger|on-the-record|tests)/" | sed -E 's/::.*//' | sort -u | wc -l` → 17.

That is the population this round's "no new bug" check now covers that
`pytest test/` alone never could: 17 test modules across `bench/`,
`gates/`, `harness/` (8 files, including the exact file that hid the
regression), `ledger/`, `on-the-record/monitors/`, and `tests/` — note
`tests/` (plural) is a distinct directory from `test/` (singular), a
second, separate blind spot the singular-directory check also missed.

Two further candidates were checked and excluded, not silently dropped.

derived: `grep -n "^def \|^class " gates/test_tier_contract.py` — result:
```
22:class Contract:
31:def parse_contract(raw):
63:def load_contract(repo_root):
```
Zero functions match pytest's configured `python_functions = test_* t_*`
— confirmed by `python3 -m pytest --collect-only -q gates/test_tier_contract.py`
— result: `no tests collected in 0.01s`. This file matches the `test_*.py`
filename pattern but is a `Contract`-loading helper module, not a test file.

derived: read `harness/fixture-redtest/test_discount.py` and
`harness/fixture-target/test_fixture_target.py` this session — both are
scenario-input fixtures the harness itself drives (test targets *of* the
harness, not tests *of* on-the-record's own code); e.g.
`harness/fixture-target/test_fixture_target.py` tests a toy
`_resolve_version()` helper that ships inside the fixture package. Both
are deliberately excluded via `pytest.ini`'s `norecursedirs`, not
silently missed.

The fix, applied and re-run as this round's own invariant check: run the
"no new bug" comparison as `pytest .` (repo root) instead of `pytest
test/`, since the wider scope requires no enumeration — `pytest.ini`'s
existing `norecursedirs` already draws the correct boundary. Full
results under "Standing invariants" below.

## Why

The verification's diagnosis was that the check "reported clean because
it did not look" — the fix for that shape of failure is to make the check
actually look, not to add a second narrower check that still has to be
told where to look. `pytest.ini` already had no `testpaths` restriction,
so widening the invariant's own command to run from the repo root was
sufficient; no gate/config file needed a directory list added to it,
which is why no enumeration was built.

For `roster_kill()`, the verification traced a real, reproduced silent
failure (a bare skill name — the shape the CLI's own usage text invites —
reports "not in roster" while a live, matching session runs unaffected).

canonical: `docs/issue-2139/reports/adversarial-review-6cda09d1.md`, "What was done" §5 — read this session — its own reproduction transcript shows `exit 1 proc alive: True` for the bare-name call before this round's fix.

The task's framing ("a kill that silently does nothing while reporting a
tidy success is the same shape as the finding above") matches this
session's own mounted `silent-failure-audit` skill's Silently-Absorbed
classification almost exactly (the failure is not absorbed in a catch
block, but the *effect* is identical: an operator reads "no live session
found" and walks away, while one keeps running). Fixing it in this round
rather than deferring again was the explicit instruction, and zero test
coverage meant a fix without a test would just reproduce the same
"structurally can't be seen" shape the round's other half was about.

## Implementation detail: `roster_kill()`

`lifecycle.py:566-590` (`roster_kill(issue, skill)`) matched only the
literal key `issue-<n>/<skill>`. Every live roster key is
`issue-<n>/<skill>-<8-hex-lease>` (`new_lease_disambiguator()`,
roster.py:266-275; assembled at spawn.py:2229 and used to register the
roster entry at spawn.py:4272) — a bare skill name, exactly what
`spawn.py kill`'s own usage text ("사용법: spawn.py kill <역할> --issue
<n>", spawn.py:2532) invites, never matches. Changed `roster_kill()` so
that when the bare key misses, it searches the roster for keys with
prefix `issue-<n>/<skill>-`: exactly one match resolves and kills that
session (loud stdout message names the resolved key); more than one
match fails loudly, listing every candidate key rather than guessing;
zero matches keeps the original "로스터에 없다" behavior unchanged.

canonical: reproduced the exact scenario from `adversarial-review-6cda09d1.md` finding 5, run this session, this turn, after the fix —
```
$ python3 -c "
import spawn, lifecycle, subprocess, time
issue = 99998; skill_slug = 'implementation'
disambiguator = spawn.new_lease_disambiguator()
live_skill = f'{skill_slug}-{disambiguator}'
roster_key = spawn.lease_key(issue, live_skill)
proc = subprocess.Popen(['sleep','60']); time.sleep(0.2)
spawn.roster_register(roster_key, {'pid': proc.pid, 'work': '/tmp/x', 'skill': live_skill, 'issue': issue})
print('Attempt A (bare skill, matches CLI usage text <역할>):')
rc = lifecycle.roster_kill(issue, skill_slug)
print('exit', rc, 'proc alive:', proc.poll() is None)
"
Attempt A (bare skill, matches CLI usage text <역할>):
종료 신호를 보냈다: issue-99998/implementation-af624a3c (pid 2557201). 워크스페이스와 라이브 로그는 남는다 — 재스폰이 이어받는다.
exit 0 proc alive: False
```
Before this round's fix, the identical Attempt A (per
`adversarial-review-6cda09d1.md`'s own pre-fix reproduction cited above)
returned `exit 1 proc alive: True` — "로스터에 없다" while the process
kept running.

Added `test/test_roster_kill_lease_suffix.py` (committed at
`22fc3f80ea6de4ce8d1c52354aa80f74a43dff94`), covering: sole-candidate
resolves, multiple candidates fail loud with names listed, zero
candidates unchanged, exact lease-suffixed key still matches directly.

derived: `grep -c "    def test_" test/test_roster_kill_lease_suffix.py` → 4 (one per case above).

canonical: `python3 -m pytest test/test_roster_kill_lease_suffix.py harness/fixture-concurrent-judgment/test_panel.py -q` — run this session, this turn — result:
```
6 passed in 0.83s
```

Invoked the mounted `silent-failure-audit` skill against this fix's own
code and the surrounding kill path.

canonical: this session's own Skill-tool invocation of `silent-failure-audit`, this turn, applied against `lifecycle.py`'s `roster_kill()` and the kill dispatch path.

derived: read `lifecycle.py:566-590` (the fix's own diff) this session — the sole/multiple/zero-match branches each `print(...)` and `return` explicitly; no empty catch or swallowed exception was introduced.

One pre-existing Silently-Absorbed site one layer down was traced and
left alone.

derived: `roster.py:54-58 _roster_load()` —
```python
def _roster_load() -> dict:
    try:
        return json.loads(_sp.ROSTER.read_text())
    except (OSError, ValueError):
        return {}
```
swallows `(OSError, ValueError)` to `{}`. Its own docstring
(`_roster_load_checked`, roster.py:61-69, read this session) documents
this as a deliberate, issue-#2203 tradeoff that every other roster
reader — not just `roster_kill` — already relies on. Changing it is out
of this round's stated scope (the lease-suffix mismatch, not roster-file
corruption handling), so it is carried forward as an open finding below
rather than fixed here.

## What did not work

None.

## Upstream basis

canonical: `gh issue view 2139` — read this session.
canonical: `docs/issue-2139/reports/adversarial-review-6cda09d1.md` — read this session (finding 1: reproduced `test_panel.py` regression; finding 5: reproduced `roster_kill()` lease-suffix mismatch).
canonical: `git log --oneline origin/issue-2139/overengineering-audit-ecf2ec0d -5` — run this session — head `0562882d` on top of `bf68d49e` (an ancestor of this branch's `origin/main`), merged clean via `git merge --no-edit origin/issue-2139/overengineering-audit-ecf2ec0d`.

## Open findings

1. `on-the-record/hooks/pr-preflight.sh`'s `_MACHINE_BODY_RE` `role=`
   fallback regex.

   canonical: `docs/issue-2139/reports/adversarial-review-6cda09d1.md`, "Open findings" §3 — read this session — already noted there as issue #2138's territory, currently dormant/no live harm.

   None from this round; carried forward unchanged.

2. `roster.py:54-58 _roster_load()`'s `(OSError, ValueError)` → `{}`
   absorption (see "Implementation detail" above) is a genuine
   Silently-Absorbed site by this session's own skill's classification,
   but it is a pre-existing, documented, repo-wide tradeoff
   (`roster.py:61-69`'s own docstring, issue #2203) affecting every
   roster reader, not specific to `roster_kill()` or this round's scope
   — noted for whoever next touches roster-file corruption handling, not
   fixed here.

## Standing invariants (re-run this round, not restated from #2869 or #2873)

Invariant 1 (no return of the retired role axis, in any reshaped form):

derived: `grep -rln '역할\|\brole\b' --include=*.py --include=*.md . | grep -vE '/(test|docs)/' | xargs -I{} grep -c '역할\|\brole\b' {} | awk -F: '{sum+=$1} END {print sum}'` — run this session, this turn, on both trees —
```
origin/main:                                19056
this branch (merged #2869 + both fixes):    19044   (decreased by 12)
```
Direction: decreased, consistent with #2873's own independent
measurement (decreased; different absolute numbers attributable to main
having advanced further and this round's new test file/comments adding
a small amount of `role`-substring text, not a regression).

Invariant 2 (no new bug) — widened scope, stated explicitly per this round's task:

canonical: `python3 -m pytest . -q` (repo root, not `test/` — see "What was done" §2 above for exactly which directories this now covers and which two are legitimately excluded) — run this session, this turn, on both trees —
```
origin/main:    16 failed, 595 passed, 3 xfailed
this branch:    16 failed, 599 passed, 3 xfailed   (+4 = the new roster_kill test file)
```
derived: `diff <(grep '^FAILED' main.log | sort) <(grep '^FAILED' head.log | sort)` — run this session — result: empty diff, SETS IDENTICAL (both listed explicitly, 16 names each, byte-identical).

Invariant 3 (no overhead increase):

canonical: `wc -c on-the-record/directive/delegation-loops.md` — run this session, this turn — result:
```
7983 on-the-record/directive/delegation-loops.md
```
Matches #2869/#2873's own already-verified 7986 → 7983; this round did not touch this file (confirmed via `git diff origin/main -- on-the-record/directive/delegation-loops.md`, unchanged by this round's two commits on top of the merge).

Invariant 4 (monitor and watch machinery unbroken and not quieter):

canonical: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py -q` — run this session, this turn — result:
```
10 passed in 0.83s
```
Unchanged from #2873's own measurement (10 passed, 0 failed); this round did not touch `watchdog.py`.

## Next steps

None from this round.

canonical: this record's own frontmatter, this turn — `loop_state: landed`.

The two fixes are committed (`22fc3f80ea6de4ce8d1c52354aa80f74a43dff94`),
tested, and the four standing invariants are re-run and reported above,
not restated from either prior record.

skill-verdict: silent-failure-audit — applied: invoked; used to audit this round's own `roster_kill()` fix and the surrounding kill path in `lifecycle.py` for any remaining silently-absorbed failure paths — see "Implementation detail" section above (derived tags cite the read code and the pre-existing absorption site found one layer down in `roster.py:_roster_load()`).

canonical: this session's own Skill-tool invocation of `silent-failure-audit`, this turn.
