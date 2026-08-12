## Scope

canonical: `gh issue view 753 --json title,state,number,body` (run this session)
Phase-1 reproduction pass for issue #753 (defect-verification role):
independently attempt to reproduce specific factual citations inside
`docs/issue-753/reports/architecture/survey.md`.
canonical: `gh pr list --search "753" --state all` (run this session)
```
$ gh pr list --search "753" --state all
764  docs(issue-753): session completion durability audit  issue-753/architecture  MERGED
```
canonical: the PR-list output immediately above, this session — PR #764
(architecture role) is merged and is the only phase-1 upstream record
for this issue; no coding/qa/review records exist for this read-only
audit issue.

## Scouting

Skipped. Condition: internal read-only reproduction against this repo's
own `spawn.py` citations — no external product/market exemplar exists to
benchmark a citation-accuracy check against.

## Attempt list

1. Source: architecture survey §1 — "`_release_spawn_claim` now fires in
   a `finally` block *after* `ensure_pushed()` returns, with a comment
   citing #719 explicitly ... so the claim always releases even if
   `ensure_pushed()` raises".
2. Source: architecture survey §2 — "`_watch` and `_watch_all` in
   `spawn.py` are the watch loop bodies".
3. Source: architecture survey §1 — `docs/issue-732/proposals/absorbed-branch-untracked-recut.md`
   is `status: proposed`, not landed.
4. Source: architecture survey §3 — `RESPAWN_MAX_ATTEMPTS = 2` caps the
   respawn loop.

code_under_review:
- spawn.py
- docs/issue-732/proposals/absorbed-branch-untracked-recut.md
- docs/issue-753/reports/architecture/survey.md

canonical: this attempt list itself (above), sourced per-item as stated.
closed_checks re-derived, none cited: all four attempts independently
re-read spawn.py and the #732 proposal against the prior architecture
survey's citations — see the `derived:` grep/read commands under each
attempt's outcome below for the actual re-derivation evidence.

## Outcomes

### Attempt 1 — outcome: reproduced

canonical: `grep -n "_release_spawn_claim\|ensure_pushed(cwd" spawn.py`
(run this session, working tree at /home/jwjung/tokenmaxxxer/on-the-record)
```
$ grep -n "_release_spawn_claim\|ensure_pushed(cwd" spawn.py
2585:def _release_spawn_claim(work: str, pid: int) -> None:
2851:            _release_spawn_claim(cwd, os.getpid())
2881:        ensure_pushed(cwd, issue, role)
```
canonical: `grep -n "719" spawn.py` (run this session)
```
$ grep -n "719" spawn.py
```
(no output — zero matches anywhere in spawn.py)

canonical: read of spawn.py lines 2848-2884 (this session)
```python
        rc = proc.wait()
        roster_remove(roster_key)
        if issue is not None:
            _release_spawn_claim(cwd, os.getpid())
    finally:
        if not is_parent_return:
            os.unlink(settings)
    if result.get("result"):
        print(result["result"])                  # 세션의 마지막 답 — 기존 UX
    elif not result:
        print(f"[{role}] 결과 이벤트를 받지 못했다 — 라이브 로그를 봐라: {log_path}",
              file=sys.stderr)

    after = board_snapshot(cwd)
    delta = sorted(p for p in set(before) | set(after)
                   if before.get(p) != after.get(p))
    blocked: list = []

    uncommitted = []
    after_head = None
    if issue is not None:
        after_head = _git_head(cwd)
        st = subprocess.run(["git", "-C", cwd, "status", "--porcelain"],
                            capture_output=True, text=True)
        uncommitted = [l for l in st.stdout.splitlines() if l.strip()]
        if uncommitted:
            print(f"[{role}] 세션이 미커밋 변경 {len(uncommitted)}건을 남기고 "
                  f"끝났다 ...", file=sys.stderr)
        ensure_pushed(cwd, issue, role)
```
canonical: the two command outputs and the code read above, this session.
Two independent facts contradict the survey's §1 claim: (a) zero
occurrences of the string "719" exist anywhere in spawn.py — there is no
comment citing #719 near `_release_spawn_claim` or anywhere else; (b)
`_release_spawn_claim(cwd, os.getpid())` executes at line 2851, inside
the `try` body, and `ensure_pushed(cwd, issue, role)` executes 30 lines
later at line 2881, in a separate `if issue is not None:` block outside
any `finally`. The single `finally:` block present (line 2852) covers
only `os.unlink(settings)` — it does not wrap `ensure_pushed` and runs
*before* `ensure_pushed` is even called, not after. The actual order is
release-claim-then-push, the reverse of what the survey states, and the
reverse of what would close the #719 release-before-push race the
survey claims is fixed.

### Attempt 2 — outcome: reproduced

canonical: `grep -n "_watch_all\|^def _watch\b\|^def watch" spawn.py`
(run this session)
```
$ grep -n "_watch_all\|^def _watch\b\|^def watch" spawn.py
1773:def _watch(issue: int, role: str | None, stall_timeout_min: float,
```
canonical: the grep output immediately above, this session; a separate
unqualified `grep -n "watch_all" spawn.py` (same session) also returned
no match.
No `_watch_all` function exists anywhere in spawn.py. The survey's §2
sentence "`_watch` and `_watch_all` in `spawn.py` are the watch loop
bodies" cites a function that does not exist; `_watch` alone is real
(line 1773).

### Attempt 3 — outcome: not-reproduced

canonical: `head -3 docs/issue-732/proposals/absorbed-branch-untracked-recut.md`
(this session, this workspace's own tree)
```
$ head -3 docs/issue-732/proposals/absorbed-branch-untracked-recut.md
---
status: proposed
files:
```
canonical: the head output immediately above, this session.
Confirms the survey's §1 citation as stated — the proposal frontmatter
reads `status: proposed`, matching the survey's claim it is not landed.
No discrepancy found in this citation.

### Attempt 4 — outcome: not-reproduced

canonical: `grep -n "RESPAWN_MAX_ATTEMPTS = 2" spawn.py` (this session)
```
$ grep -n "RESPAWN_MAX_ATTEMPTS = 2" spawn.py
1578:RESPAWN_MAX_ATTEMPTS = 2
```
canonical: the grep output immediately above, this session.
Confirms the survey's §3 citation as stated. No discrepancy found.

## Cross-reference to prior architecture survey

canonical: attempt 1 and attempt 2 outcomes above (this file, this session)
Both reproduced defects sit inside the *evidence* the survey cites for
its §1 and §2 verdicts, not the verdicts themselves — §1 (PARTIAL) and
§2 (MET) both stay independently plausible on their remaining, verified
citations (attempts 3-4 above).
canonical: `grep -n "^def _watch\b\|^def roster_watchdog\|^def _watchdog_state_load\|^def _watchdog_state_save" spawn.py`
(this session)
```
$ grep -n "^def _watch\b\|^def roster_watchdog\|^def _watchdog_state_load\|^def _watchdog_state_save" spawn.py
1357:def _watchdog_state_load() -> dict:
1364:def _watchdog_state_save(d: dict) -> None:
1439:def roster_watchdog(auto_respawn: bool = False) -> int:
1773:def _watch(issue: int, role: str | None, stall_timeout_min: float,
```
canonical: the grep output immediately above, this session. §2's four
other named functions (excluding the fabricated `_watch_all`) all exist
at the cited lines. What breaks is the survey's own reliability as a
citation source: §1 asserts a specific mechanism (#719 closed via
finally-after-push ordering) that attempt 1 shows is the opposite of
what the code does, and §2 names a function (`_watch_all`) that attempt
2 shows was never grepped for existence before being cited.

## What did not work

None.
