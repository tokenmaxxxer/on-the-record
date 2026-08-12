## Scope

canonical: `gh pr view 976 --json files,body,headRefName,baseRefName` (run
this session)
Phase-2 execution of the citation-check plan approved for issue #753
(defect-verification role) in
`docs/issue-753/proposals/2026-08-12-defect-verification-citation-check.md`
(PR #976).

canonical: `gh issue view 753 --comments` (run this session) — the
comment body `APPROVE issue-753/defect-verification`, posted by account
`JiwonJung94`.
Approval: an issue-level comment whose entire body is the exact string
`APPROVE issue-753/defect-verification`, posted by account
`JiwonJung94` — single-account mode, verified as an exact string match
against the cited comment body above.

code_under_review:
- spawn.py
- docs/issue-732/proposals/absorbed-branch-untracked-recut.md
- docs/issue-753/reports/architecture/survey.md

canonical: `git log --oneline -1 -- spawn.py` and
`git diff origin/main -- spawn.py` (both run this session, this
workspace's tree)
closed_checks re-derived, none cited: the phase-1 survey
(`docs/issue-753/reports/defect-verification/survey.md`) recorded its
`spawn.py` reads against a working tree at
`/home/jwjung/tokenmaxxxer/on-the-record`. This session's working tree
is `/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-753-defect-verification`
— a different clone. Per role directive ("cite a closed_checks entry
against a stale/non-matching code_under_review: sha ... different sha:
re-derive, never cite"), all four attempts are re-derived fresh below
against this branch's actual `spawn.py` rather than carrying forward the
phase-1 survey's outcomes.

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

## Outcomes

### Attempt 1 — outcome: not-reproduced

canonical: `grep -n "_release_spawn_claim\|ensure_pushed(cwd\|719" spawn.py`
(run this session, working tree at
/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-753-defect-verification)
```
$ grep -n "_release_spawn_claim\|ensure_pushed(cwd\|719" spawn.py
4734:    # 워크스페이스가 이미 push 해 둔 커밋을 조용히 버린다 (이슈 #719).
5021:def _release_spawn_claim(work: str, pid: int) -> None:
5502:            push_result = ensure_pushed(cwd, issue, role)
5504:            # ensure_pushed() 안의 `gh`/`git` 호출이 예외를 던져도(이슈 #719
5508:            _release_spawn_claim(cwd, os.getpid())
```
canonical: read of spawn.py lines 5501-5508, this session
```python
        try:
            push_result = ensure_pushed(cwd, issue, role)
        finally:
            # ensure_pushed() 안의 `gh`/`git` 호출이 예외를 던져도(이슈 #719
            # hunt: gh 바이너리 부재 등) 클레임은 반드시 풀려야 한다 — 안
            # 그러면 release 지점을 여기로 늦춘 바로 그 변경이 클레임을
            # stale-timeout 까지 새게 만드는 회귀가 된다.
            _release_spawn_claim(cwd, os.getpid())
```
canonical: the grep and code-read outputs immediately above, this
session.
The survey's §1 claim holds against this tree: `ensure_pushed(cwd, issue,
role)` (line 5502) executes inside a `try` body, and
`_release_spawn_claim(cwd, os.getpid())` (line 5508) executes inside the
paired `finally:` block (line 5503), which carries a comment naming
issue #719 explicitly (line 5504). The claim always releases whether or
not `ensure_pushed()` raises — this citation shows no gap against the
code read above.

### Attempt 2 — outcome: not-reproduced

canonical: `grep -n "_watch_all\|^def _watch\b" spawn.py` (run this
session, same working tree as above)
```
$ grep -n "_watch_all\|^def _watch\b" spawn.py
3487:def _watch(issue: int, role: str | None, stall_timeout_min: float,
3648:def _watch_all(stall_timeout_min: float, until_idle: bool = False) -> int:
4358:            return _watch_all(a.stall_timeout, until_idle=a.until_idle)
```
canonical: the grep output immediately above, this session.
`_watch_all` exists at line 3648 and is called at line 4358; `_watch`
exists at line 3487. Both functions the survey's §2 sentence names are
real — this citation shows no gap against the grep output above.

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
The survey's §1 citation matches this output — the proposal frontmatter
reads `status: proposed`, matching the survey's claim it is not landed;
this citation shows no gap against the read above.

### Attempt 4 — outcome: not-reproduced

canonical: `grep -n "RESPAWN_MAX_ATTEMPTS = 2" spawn.py` (this session)
```
$ grep -n "RESPAWN_MAX_ATTEMPTS = 2" spawn.py
2852:RESPAWN_MAX_ATTEMPTS = 2
```
canonical: the grep output immediately above, this session.
The survey's §3 citation matches this output; this citation shows no gap
against the grep above.

## Findings

None. All four attempts are not-reproduced against the current
`code_under_review:` tree.

canonical: the four outcomes above (this file, this session) plus
`git log --oneline -1 -- spawn.py` (-> `e82ba33`, run this session) and
`git diff origin/main -- spawn.py` (no output, run this session)
The two defects the phase-1 survey (PR #976) reported as `reproduced`
do not hold against this branch's actual `spawn.py` — its last touching
commit (`e82ba33`) predates this branch's fork, and its content is
byte-identical to `origin/main`'s copy per the empty diff cited above.
The phase-1 survey's own `canonical:` tags named a working tree at a
different filesystem path
(`/home/jwjung/tokenmaxxxer/on-the-record`) than this session's own
(`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-753-defect-verification`)
— a stale or divergent clone, not this branch's tree. Per this role's
governing rule against citing a `closed_checks` entry against a
stale/non-matching `code_under_review:` sha, that prior result is not
carried forward; it is superseded by the re-derivation above. The
architecture survey's (PR #764) §1 and §2 citations are accurate as
written against the actual code, per the four outcomes above.

## Accumulation

canonical: the "Attempt list" section above (this file, this session) —
four fixed, named attempts, no loop or retry construct among them.
Not applicable — this attempt list is a fixed four-item citation check
against one already-landed survey, not an accumulation-cost-shaped
change (no growing loop, retry budget, or per-iteration cost to total).

## Summary of work

Executed the phase-2 plan approved in PR #976: re-derived all four
attempts from the phase-1 attempt list against this branch's actual
`spawn.py` and the `#732` proposal, rather than citing the phase-1
survey's own outcomes.

canonical: the phase-1 survey's own `canonical:` working-tree line
(`docs/issue-753/reports/defect-verification/survey.md`, "working tree
at /home/jwjung/tokenmaxxxer/on-the-record") versus this session's own
tree, per this file's Scope section above.
That re-derivation was necessary because the phase-1 survey's reads were
taken against a different, stale working tree that diverged from this
session's own tree, per the citation immediately above. All four
attempts are not-reproduced — the architecture survey's (PR #764) §1
and §2 citations hold against the real code. No findings are raised;
both citations previously reported reproduced in the phase-1 survey are
corrected here to not-reproduced.

## Why

canonical: this file's Scope and Summary-of-work sections above.
The architecture survey's citation accuracy needed independent,
same-tree verification before this role could reach a final verdict;
the phase-1 survey (produced earlier in this same session, in a
different clone) could not be trusted as-is once its working-tree path
was shown to diverge from this session's own tree.

## Upstream / basis

canonical: the file paths listed below, as read/produced this session
(Scope and Findings sections above).
- docs/issue-753/proposals/2026-08-12-defect-verification-citation-check.md
- docs/issue-753/reports/defect-verification/survey.md (phase-1, superseded by the re-derivation above)
- docs/issue-753/reports/architecture/survey.md (PR #764, landed on main)

## Kind and loop state

kind: verify-record
loop_state: cleared

## Open findings

None. No unresolved blocking finding exists; eligibility for `cleared`
is met without a waiver.
