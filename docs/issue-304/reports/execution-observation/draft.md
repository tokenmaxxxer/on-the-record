kind: execution-observation
loop_state: handed-off

# Issue #304 — execution-observation record (draft, pending phase-2 approval)

## What was done

Ran the current test suite's sandbox/role_settings coverage against HEAD (`bc53410e`, this
branch's parent) and inspected `spawn.py` directly to determine whether the artifact PR #307
landed for #304 (the `PLAYWRIGHT_BROWSERS_PATH` cache mount, merge commit `2feb64ce`) is still
present and exercisable, since no execution-observation record existed yet for that commit sha.

canonical: `pytest tests/test_spawn.py -k "sandbox or Sandbox or role_settings" -q`, run this
session
```
$ python3 -m pytest tests/test_spawn.py -k "sandbox or Sandbox or role_settings" -q
....                                                                     [100%]
4 passed, 499 deselected in 67.45s (0:01:07)
```

canonical: `python3 -c "import spawn; ..."` inline probe of the live module, run this session
```
$ python3 -c "
import spawn
print('PACKAGE_CACHE_DIRS' in dir(spawn))
print('playwright_cache_layer' in dir(spawn))
print('go_proxy_layer' in dir(spawn))
out = spawn.role_settings('implementation')
print('sandbox' in out, out.get('sandbox'))
"
False
False
False
True {'enabled': False, 'network': {'allowedDomains': ['api.anthropic.com', '*.github.com', 'github.com']}}
```

`PACKAGE_CACHE_DIRS`, `playwright_cache_layer()`, and `go_proxy_layer()` — the three symbols PR
#307 added or extended — do not exist on the `spawn` module at HEAD, and `role_settings()`'s
live output shows `sandbox.enabled: False` with no `filesystem.allowRead` key at all, so there is
no cache mount to observe today (canonical: the `python3 -c` probe fenced immediately above, run
this session).

canonical: `git log --oneline --all -S "playwright_cache_layer" -- spawn.py`, run this session
```
$ git log --oneline --all -S "playwright_cache_layer" -- spawn.py
1af5aee1 refactor(issue-695): stop role_settings() from enabling the sandbox
933be5e9 issue-304: phase 2 — Playwright browser-cache mount for sandboxed sessions
```
Exactly two commits touch that symbol: `933be5e9` (this issue's PR #307, which added it) and
`1af5aee1` (the PR closing issue #695, which removed it).

canonical: `git show 1af5aee1 --format=%s%n%n%b`, run this session
```
$ git show 1af5aee1 --format=%s%n%n%b | head -10
refactor(issue-695): stop role_settings() from enabling the sandbox

Central disable in role_settings(): force sandbox.enabled=False
regardless of what roles/*.json declares ...
Removes the sandbox-only plumbing that becomes unreachable once the
sandbox never enables: the registry/web-domain merge, the issue-#72
switch-opening block, the package-cache allowRead mount, the
tlsTerminate shim, and the allowUnsandboxedCommands pin. Also removes
go_proxy_layer()/playwright_cache_layer(), which the before-landing
warrant hunt found silently going dead as a direct consequence of the
cache-mount removal (their gate could never be true again).
```

canonical: `spawn.py:539-545` at HEAD, read this session — inline comment carries the same
account: "이슈 #695: 롤-세션 샌드박스를 role_settings() 가 중앙에서 끈다 ... 패키지 캐시
allowRead 마운트(#38)는 전부 도달 불가능해져 issue-695 에서 함께 제거했다."

canonical: `git merge-base --is-ancestor 2feb64cebb0e01461f3f06d5ae09b1ac5dad5ac4 HEAD; echo $?`,
run this session, exit `0`
```
$ git merge-base --is-ancestor 2feb64cebb0e01461f3f06d5ae09b1ac5dad5ac4 HEAD && echo yes
yes
```
PR #307's merge commit is an ancestor of HEAD, so the removal in `1af5aee1` is a later,
deliberate supersession, not a missing branch or an unmerged PR.

## Why

#304's acceptance criteria (issue body, "## Acceptance") name two executable checks against
`test_spawn.py`: the Playwright cache visible read-only with `PLAYWRIGHT_BROWSERS_PATH` resolved,
and the mount widening no network domain. Both checks target code (`PACKAGE_CACHE_DIRS`,
`playwright_cache_layer()`) that PR #307 added and that issue #695's later, separately-approved
refactor removed as dead code once `sandbox.enabled` was forced `False` for every role
unconditionally — a decision `spawn.py:539-545`'s own comment (canonical: `spawn.py:539-545`,
read this session, quoted above) attributes to a different set of repeated blockage bugs
(#38/#58/#65/#72/#153), not to anything wrong with #304's mount itself.

## Upstream basis

PR #307 (merged 2026-08-07, commit `2feb64cebb0e01461f3f06d5ae09b1ac5dad5ac4`; canonical: `gh pr
view 307 --json mergeCommit,files,body`, read this session); issue #695 / commit
`1af5aee135bec43cae09c1af12b86623b0810405` (canonical: `git show 1af5aee1`, read this session,
quoted above); `spawn.py:485-545` at HEAD (canonical: file read this session).

## Verdicts

### Outcome

Per the role spec's recomputation rule (`roles/specs/execution-observation.spec.json`: worst-case
across cited test entries), the outcome is **inapplicable**. The two acceptance-criteria tests
this record could run against the currently-shipped `spawn.py` at HEAD — `PACKAGE_CACHE_DIRS`
containing the Playwright entry, and `playwright_cache_layer()` resolving it — have no subject
left to execute against.

canonical: `python3 -c "import spawn; ..."` fenced above, run this session — both symbols absent
from the `spawn` module at HEAD, removed by `1af5aee1` (issue #695) as an intended consequence of
its central sandbox disable, not a regression of #304's own work.

canonical: `pytest tests/test_spawn.py -k "sandbox or Sandbox or role_settings" -q` fenced above,
run this session — the sandbox/role_settings suite that does still exist at HEAD passes
(derived: the fenced pytest summary line "4 passed, 499 deselected" above), consistent with that
same disable — it asserts `sandbox.enabled=False` for every role, which is the state that made
the mount unreachable.

- subject: `spawn.py` `PACKAGE_CACHE_DIRS` / `playwright_cache_layer()` (as landed by PR #307,
  commit `2feb64ce`)
  test: `python3 -c "import spawn; 'PACKAGE_CACHE_DIRS' in dir(spawn)"` against HEAD
  result: **inapplicable** — symbol does not exist at HEAD (canonical: fenced `python3 -c` output
  above); removed by `1af5aee1` (issue #695), not by any defect in #304's own landing
- subject: `spawn.py` `role_settings()`'s sandbox output at HEAD
  test: `tests/test_spawn.py -k "sandbox or Sandbox or role_settings"`
  canonical: `pytest tests/test_spawn.py -k "sandbox or Sandbox or role_settings" -q` — result
  "4 passed, 499 deselected" (fenced above)
  result: **passed**, confirming the current, superseding behavior (`sandbox.enabled=False`
  unconditionally) rather than #304's mount

### Trajectory

Sound at landing time, superseded since. canonical: `docs/issue-304/reports/implementation.md`,
read this session — PR #307's own record states it implemented PR #305's approved
keep-with-adjusted-settings recommendation via `APPROVE issue-304/architecture`. canonical: `git
show 1af5aee1` fenced above, read this session — issue #695's PR body states the mount's
dependent functions were found going dead as a consequence of #695's own central-disable change
during its own before-landing warrant hunt, not as a defect this session found. No fresh approval
gate applies to this record — it is an observation of already-landed, already-superseded state,
not a new judgment call requiring one.

### Step

Zero confirmed deficiencies (canonical: the `python3 -c` and `git log -S` fences above, run this
session — nothing in PR #307's landed diff is itself broken; the symbols it added simply do not
exist post-`1af5aee1`). The subject #304 built is no longer reachable code after a later,
separately-scoped, separately-approved decision (#695) removed the sandbox enablement the mount
depended on. This record does not recommend any follow-up to #304 itself — if the mount is needed
again, that is a #695-scope question (whether/how the sandbox comes back), not a #304-scope one.

## What did not work

None.
