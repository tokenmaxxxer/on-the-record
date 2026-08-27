---
issue: 2574
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: spawn.py
    sha: same-commit
  - path: gates/spawn_on_pr.py
    sha: same-commit
  - path: gates/spawn_on_approve.py
    sha: same-commit
  - path: lifecycle.py
    sha: same-commit
code_under_review:
  - spawn.py:2723 (`_spawn_one()` `single_phase` parameter default)
  - spawn.py:3618 (roster entry now records `single_phase`)
  - spawn.py:3997-4001 (`_self_trigger_respawn()` call threads its own `single_phase`)
  - gates/spawn_on_pr.py:491 (`spawn_missing_for_pr()` call site)
  - gates/spawn_on_pr.py:554 (`backfill_closed()` call site)
  - gates/spawn_on_approve.py:259 (`spawn_phase2()` call site)
  - lifecycle.py:359-362, 480, 515-522, 528-531, 553-557 (`_respawn_or_cap()` / `_auto_respawn_check()` / `_self_trigger_respawn()`)
type: fix
breaking: internal-only — lifecycle._respawn_or_cap() and lifecycle._self_trigger_respawn() gained a new required positional single_phase argument; both are private in-repo-only functions and every call site was updated in this same commit. No external/public interface changed.
verdict: pass
---

# issue-2574 — implementation record

skill-verdict: other mounted skills — not triggered (no Skill tool call this session; solo single-cluster bugfix, no cross-model delegation decision to route, and no repo-language-convention override — this repo's own code comments are Korean throughout, matched for consistency)

## What was done

canonical: `gh issue view 2574` output, read at session start — root cause quoted verbatim from the issue body:

```
spawn.py:2706   def _spawn_one(..., single_phase: bool = False, ...)
                                                  ^^^^^ still False
spawn.py:2183   CLI path:  effective_single_phase = not two_phase and not checkpoint   → True
spawn.py:3397   if single_phase: extra_env["CORE_BUILD_NOW"] = "1"
```

derived: `sed -n '2706,2716p' spawn.py` (pre-edit, same lines the issue cites) confirmed the parameter default was still `False` before this session's edit; `sed -n '2180,2185p' spawn.py` confirmed the CLI's `effective_single_phase = not a.two_phase and not a.checkpoint` at `spawn.py:2183` is unchanged by this fix.

`#2152` flipped the *effective* default to single-phase only at the CLI
entry point (`main()` computing `effective_single_phase` and passing it
explicitly). `_spawn_one()`'s own parameter default stayed `False`, so
every one of the four call sites that invoke `_spawn_one()` directly
(bypassing `main()`) fell back to the pre-`#2152` two-phase behavior —
no `CORE_BUILD_NOW=1`, so `on-the-record/hooks/approval-gate.sh` demands
a human `APPROVE` comment before the observer can write its own record
or touch `src/`/`test(s)/`.

canonical: `on-the-record/hooks/approval-gate.sh:178-191` (read this session):

```
if os.environ.get("CORE_BUILD_NOW") == "1":
    sys.stderr.write(
        "approval-gate: CORE_BUILD_NOW=1 — bypassing phase-2 approval check "
        "for issue-%d/%s write (%s).\n" % (issue, role, n)
    )
    sys.exit(0)
```

THE JUDGMENT the issue asked for (observers as ordinary single-phase
work, or a distinct category): resolved per call site, not uniformly.
Exact call-site locations for the disposition paragraphs below are
listed in this record's own frontmatter `code_under_review:` list and
confirmed again by the check-4 grep further down.

Disposition, `spawn_missing_for_pr()` and `backfill_closed()` (both in
`gates/spawn_on_pr.py`): both write a verification record for code that
is already landed on a PR; there is no `code_under_review` this spawn
opens, so the proposal-first two-phase contract's purpose does not
apply here. Set `single_phase=True`, explicit at the call.

Disposition, `spawn_phase2()` (`gates/spawn_on_approve.py`): this
call's own precondition, per its task text built directly above the
call site, is that an `APPROVE issue-<n>/<role>` comment was already
observed.

canonical: `gates/spawn_on_approve.py`, the `task =` assignment
directly above the `spawn._spawn_one(...)` call (read this session):

```python
task = (f"이슈 #{issue}: {role} — APPROVE issue-{issue}/{role} 코멘트가 "
        f"관측됐다. phase-2 로 계속한다: 기존 phase-1 PR({branch} 브랜치) "
        f"위에서 실제 작업과 기록을 커밋하라. (자동 스폰됨, "
        f"spawn_on_approve.py, issue #2173)")
```

That approval condition is already genuinely satisfied through the
real path shown above (the hook's own live comment scan would find
that same comment even without `CORE_BUILD_NOW`). Passing
`single_phase=True` here does not bypass anything; it makes the
spawned session's own injected instructions agree with what its task
text already says: proceed directly to the delivery work it describes.

Disposition, `_respawn_or_cap()` (`lifecycle.py`, reached from both
`_auto_respawn_check()` and `_self_trigger_respawn()`): not a fixed
disposition. A crashed session being respawned must resume with the
same disposition it was originally spawned with — defaulting it to the
new shared `True` default would silently promote a crashed `--two-phase`
session to build-now on respawn, which acceptance check 3 (below) rules
out. `_self_trigger_respawn()` is called from inside `_spawn_one()`
itself, where `single_phase` is already a known local and is passed
straight through. `_auto_respawn_check()` reads a new `single_phase`
field this session added to the roster entry (written from the real
value at spawn time) via `entry.get("single_phase", False)`; the
`False` fallback covers only the narrow transition case of a roster
entry written before this fix landed, and reproduces today's pre-fix
(safe) two-phase behavior for that case rather than guessing `True`.

derived: `inspect.signature` check (full command and result quoted
under "Acceptance evidence, check 2" below) confirms `_spawn_one()`'s
own `single_phase` default is now `True`, matching the CLI's own
effective default computed at `spawn.py:2183` for the no-flags case —
this closes the shared-default divergence structurally, not just at
the four named call sites.

## Why

canonical: `git diff --stat` (this session's own diff, quoted below)
shows the shape of what changed:

```
gates/spawn_on_approve.py | 13 ++++++++++++-
gates/spawn_on_pr.py      | 16 ++++++++++++++--
lifecycle.py              | 33 ++++++++++++++++++++++++++++-----
spawn.py                  | 26 ++++++++++++++++++++++++--
```

The four call sites are all orchestrator-internal auto-spawn paths that
never route through `main()`'s CLI argument parsing, so none of them
ever saw `#2152`'s default flip — this matches the issue's own
description of the root cause (quoted above under "What was done").
Patching only the four call sites (adding `single_phase=True` at each,
without touching the shared parameter default) would have closed the
instances the issue names but left the underlying mechanism — a
function whose own default disagrees with what its caller-of-record
computes — open for the next direct caller of `_spawn_one()`. This
session did both: moved the shared default (acceptance check 2), and
added an explicit, grep-able `이슈 #2574 disposition:` comment at each
call site (acceptance check 4, grep output quoted below) so each site's
actual reasoning is visible without reading `_spawn_one()`'s docstring.

## What did not work

None — the fix landed as designed, no reverted approach. The live
verification harness (ad hoc script, not committed) needed several
fixture fixes along the way — mocking `bootstrap_fetch_and_record_sha`/
`_fetch_or_halt` since the temp git fixture used for verification has
no `origin` remote, and reading the observer's session-log file instead
of an in-process spy list, because `_spawn_one()` calls `os.fork()`
before its real `Popen()` and the forked child's copy-on-write memory
never propagates back to the parent process. These were properties of
the throwaway verification harness, not deviations in the shipped fix
itself.

## Upstream basis

No separate phase-1 proposal/survey document exists for this issue —
this session ran under the build-now bypass (`CORE_BUILD_NOW=1`, set by
the spawner; contract v3 s19a) with an explicit skip-the-proposal-round
instruction present in this session's own system context at start.
Upstream input was the GitHub issue body (canonical: `gh issue view
2574` output, quoted above) plus the repository state at `same-commit`
for the four edited files. `on-the-record/hooks/approval-gate.sh` was
read (not edited) at commit `6f0c61bad4a43d3ac7cf1435894ac53855b9744a` —
derived: `git rev-parse HEAD` at session start, before any edit.

## Acceptance evidence

### check 1 — an auto-spawned observer runs its git commands without an Approve signal

derived: ad hoc live-harness Python script (not committed —
verify-at-landing convention, no persistent test file), run as
`python3 /tmp/verify_2574.py` and since removed; contents reproduced
below. It calls the real, unmodified `gates.spawn_on_pr.spawn_missing_for_pr()`
against a synthetic issue-648/PR-650/role-conformance-review pair
(mirroring the issue's own real blocked-consumer example). Mocked:
`issue_workspace()`, `checkout_issue_branch()`/`_fetch_or_halt`/
`bootstrap_fetch_and_record_sha` (network-fetch stand-ins, since the
fixture repo has no `origin` remote), `spawn_cmd()` (the actual Claude
Code subprocess swapped for a one-line shell echo — a nested full agent
session cannot run inside this verification), and `gh`-touching
lookups. Not mocked: `_spawn_one()`, `spawn_missing_for_pr()`, and the
real `on-the-record/hooks/approval-gate.sh`.

```python
script = textwrap.dedent(f"""
    echo "[observer session] CORE_BUILD_NOW=$CORE_BUILD_NOW"
    cat > /dev/null
""")

def spy_spawn_cmd(settings, role, unattended, core_plugins, plugins,
                  model, skill_dirs, skill_repo_sha_value, **kwargs):
    return (["bash", "-c", script], {})
```

Result — park state before the tick, then the return value:

```
=== park state before tick (must be empty: first-attach / no observer records yet) ===
{}
=== spawn_missing_for_pr() returned pairs: [('issue-648', 'conformance-review')] ===
```

Result — the observer session's own log output (its `CORE_BUILD_NOW`,
as actually received):

```
[observer session] CORE_BUILD_NOW=1
```

Result — the real hook, given exactly that env, on a `Write` to the
observer's own record file:

```
exit=0
stderr=approval-gate: CORE_BUILD_NOW=1 — bypassing phase-2 approval check for issue-648/conformance-review write (docs/issue-648/reports/conformance-review.md).
```

derived: `python3 /tmp/verify_2574.py` (script contents above) —
result: the observer's own unmodified auto-spawn path produced a
session whose env carried `CORE_BUILD_NOW=1`, and the real hook let its
`Write` proceed with exit 0 — no `APPROVE` comment involved anywhere in
this run. Acceptance requirement met.

### empty-state clause — a PR with no observer records yet is the normal first-attach case and must spawn

Covered by the same run: park state was `{}` immediately before the
tick (quoted above, `load_park_state(work)` — no prior park entry for
this subject/role existed), and `spawn_missing_for_pr()` still returned
`[('issue-648', 'conformance-review')]` (spawned, not parked).

### check 2 — the divergence cannot recur silently

derived: `python3 -c "import inspect, spawn; print(inspect.signature(spawn._spawn_one).parameters['single_phase'].default)"` — result: `True`.

`spawn.py:2183` (unchanged by this fix): `effective_single_phase = not a.two_phase and not a.checkpoint` — with no `--two-phase`/`--checkpoint`, this is `True`. `spawn.py:2723` (this session's edit): `_spawn_one()`'s own parameter default is now also `True` — a caller that omits `single_phase` entirely now receives the same value the CLI computes for its own no-flags default case, by construction of one shared default rather than by each caller remembering to pass a flag. This is the "same behavior as the CLI" branch of the acceptance check.

### check 3 — a genuinely two-phase spawn (--two-phase) still requires its Approve signal

derived: same live-harness run (`python3 /tmp/verify_2574.py`), same hook, same role/branch/session, `CORE_BUILD_NOW` unset this time (what a `--two-phase` spawn's `extra_env` looks like — `spawn.py:3410` only sets `CORE_BUILD_NOW` when `single_phase` is true):

```
exit=2
stderr=approval-gate: docs/specs/approvers.md is absent — this phase-2-shaped write (docs/issue-648/reports/conformance-review.md) cannot be approval-checked, so it is refused rather than silently allowed.
```

derived: `python3 /tmp/verify_2574.py` (same script) — result: without
`CORE_BUILD_NOW`, the same hook denies (exit 2) the same write it
allowed above. The specific denial reason is "approvers.md absent"
rather than "no matching APPROVE comment" only because this harness's
fixture never created `docs/specs/approvers.md` — the hook's
`CORE_BUILD_NOW` check runs before that check
(`on-the-record/hooks/approval-gate.sh:186-191` precedes `:194-204`),
so this denial is reached without ever exercising `CORE_BUILD_NOW`.
Either denial reason demonstrates what this check asks for: the write
is refused, not silently allowed, once `CORE_BUILD_NOW` is absent.
Acceptance requirement met.

### check 4 — all four call sites are named with their disposition

derived: `grep -n "이슈 #2574 disposition" gates/spawn_on_pr.py gates/spawn_on_approve.py lifecycle.py` — result:

```
gates/spawn_on_approve.py:249:        # 이슈 #2574 disposition: single-phase(build-now). 이 스폰의
lifecycle.py:515:    # 이슈 #2574 disposition: 고정값이 아니라 '상속' — 이 크래시한 세션이
lifecycle.py:554:    # 이슈 #2574 disposition: 고정값 아님, 상속 — `single_phase` 는 이
gates/spawn_on_pr.py:484:        # 이슈 #2574 disposition: single-phase(build-now). 이 스폰은 이미
gates/spawn_on_pr.py:551:        # 이슈 #2574 disposition: single-phase(build-now) — 위
```

derived: `grep -n "이슈 #2574 disposition" gates/spawn_on_pr.py
gates/spawn_on_approve.py lifecycle.py` (result above) — every call
site named in the issue carries a disposition comment:
`gates/spawn_on_pr.py` two sites, `gates/spawn_on_approve.py` one site,
and `lifecycle.py`'s respawn path documented at both entry points that
feed the single `_respawn_or_cap()` → `_spawn_one()` call the issue
named. Acceptance requirement met.

### Regression check

derived: `python3 -m pytest test/ -q` — result: `13 failed, 251
passed`.

derived: `git stash && python3 -m pytest test/ -q; git stash pop` —
result: `13 failed, 251 passed`, byte-identical failing test names
(e.g. `test_spawn_artifact_skill_pairing.py`'s artifact-pairing tests),
reproduced against unmodified `HEAD` with this session's diff removed.
All 13 are a pre-existing environment limitation: `git fetch origin`
against a bare local test fixture with no `origin` remote configured
(`SystemExit: 브랜치 체크아웃: fetch 실패 — fatal: 'origin' does not appear to
be a git repository`), not caused by this change. Same pass/fail counts
and same failing-test-name sets before and after this session's diff —
no regression.

## Open findings

None.

## Next steps

None — `loop_state: landed`.
