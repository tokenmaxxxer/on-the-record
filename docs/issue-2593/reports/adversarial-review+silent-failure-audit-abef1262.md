---
issue: 2593
role: adversarial-review+silent-failure-audit-abef1262
author: adversarial-review+silent-failure-audit-abef1262
skills: adversarial-review (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: true  # independent re-derivation of PR #2664's acceptance-bullet claims and its self-verification-guard fix; author differs from PR #2664 (JiwonJung94 / silent-failure-audit+architecture-interface-contract-shape-79606e42)
loop_state: landed
upstream:
  - path: PR #2664 (issue-2593/silent-failure-audit+architecture-interface-contract-shape-79606e42)
    sha: 55b58c12a17d3c2f519abfb504ecd8dfb2db8146
---

# issue-2593 — adversarial-review+silent-failure-audit-abef1262 record

## What was done

canonical: two disposable git worktrees this session, both removed after use —
`/tmp/verify-2664` on PR #2664's branch (`git worktree add /tmp/verify-2664
origin/issue-2593/silent-failure-audit+architecture-interface-contract-shape-79606e42`,
detached HEAD `55b58c12`) and `/tmp/verify-main-2664` on `origin/main`
(detached HEAD `de8b7ffe`). No code, test, or record from PR #2664 was trusted
as evidence — every command below was executed live this session in one of
these two worktrees.

### Bullet 1 — `PR_TRIGGERED_RECORD_KINDS` gone

acceptance: `grep -rn 'PR_TRIGGERED_RECORD_KINDS' --include=*.py .` (run in
`/tmp/verify-2664`) — result: 0 matches, exit code 1 (grep's no-match code).
**Present.**

### Bullet 4 — no live hard-coded `"implementation"`/`"coding"` branch

acceptance: `grep -rnE '"(implementation|coding)"' --include=*.py gates/ *.py`
(run in `/tmp/verify-2664`) — result:
```
gates/skip_eligibility.py:85:# deleted here, not just their two dead `"implementation"` fallback
gates/spawn_on_pr.py:180:    match `kind_field == "implementation" or (kind_field is None and name
gates/spawn_on_pr.py:181:    == "implementation")`, a hard-coded historical role name the #2593
gates/spawn_on_pr.py:184:    matched the equally-historical `"coding"` deliverable name, so a
gates/gates.py:695:    ("implementation")에서만 실제로 발동했다(나머지 43개는 버킷 dict라
```
canonical: read each hit directly this session — `gates/spawn_on_pr.py:177-217`
(the new `subject_deliverable_record()`'s own docstring, describing the
*retired* match, not a live branch), `gates/gates.py:685-700` (a prose comment
about historical catalog behavior), `gates/skip_eligibility.py:70-90` (a
comment recording that `classify_for_subject()` and its two dead
`"implementation"` fallback strings were deleted entirely, with zero remaining
callers). All 5 hits are inside docstrings/comments. **Present.**

### Bullet 2 — merge refusal demonstrated live, mechanism named (load-bearing)

Reproduced in both directions with a synthetic subject `issue-99999`: a
skill-slug-named deliverable (`arch-review-decomp-ab12cd34`) plus two
`verifies_subject: true` records authored by that same slug (a self-authored
double verification):

```
# pre-fix, /tmp/verify-main-2664 (origin/main, de8b7ffe):
PRE-FIX subject_deliverable_record -> None {}
PRE-FIX required_verification_missing -> 0 (0 == merge ALLOWED despite same-author self-verification)

# post-fix, /tmp/verify-2664 (PR #2664 branch, 55b58c12):
POST-FIX subject_deliverable_record -> arch-review-decomp-ab12cd34 {'author': 'arch-review-decomp-ab12cd34'}
POST-FIX required_verification_missing -> 2 (>0 == merge REFUSED, self-authored records correctly excluded)
```
derived: constructed by monkeypatching `spawn.board` to return the synthetic
`subject_board` above and calling `gates.spawn_on_pr.subject_deliverable_record()`
/ `gates.merge_gate.required_verification_missing()` directly (Python one-off,
this session, in each worktree in turn).

Live, non-synthetic confirmation on the PR branch, against this issue's own
open subject:

```
$ python3 gates/merge_gate.py 999999 issue-2593 --repo .
거절: PR #999999 (issue-2593)
  - check-runner 코멘트를 찾을 수 없다
  - required_verification_missing(): 독립 검증 기록이 부족하다 -- 0/2개 확인됨 (2개 더 필요)
```
canonical: exit code 1, run in `/tmp/verify-2664`.

Mechanism named: `gates/merge_gate.py::evaluate()` (:356-364, read directly
this session) calls `required_verification_missing()` (:178-213), which reads
`subject_deliverable_record()`'s `author:` as `subject_author` and calls
`spawn_on_pr.verifying_record_count()` (:67-89) against
`spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS = 2` (:43); `main()` (:384-415)
prints the refusal line and returns exit code 1, exactly as observed above.
**Present**, and the load-bearing self-authored-bypass claim is **confirmed
true in both directions**, not merely asserted.

### 550/83/62/21 breakdown

derived (run in `/tmp/verify-2664`, real `docs/issue-*/reports/` data via
`board.board(Path('.'))`, `import spawn` first so `board.py`'s `_sp` binds):
```
total subjects: 633
old resolved (matched hardcoded 'implementation'): 550
old unresolved: 83
unmatched total: 83
coding bucket: 21
skill-slug bucket: 62
```
Partition criterion used (the PR's own, not a criterion of my own invention):
of the 83 unmatched, does any record in the subject have `kind=='coding'` or
filename `'coding'`? 21 yes, 62 no.
canonical: the code fence immediately above this paragraph — the PR's claimed
550/83/62/21 breakdown reproduced exactly, in a script written from scratch
this session, not copied from PR #2664's own record.

### New-rule attack scenarios (issue #2593's own #2548 test)

```
A1 all-self-declare -> slug: None fm: {}
A2 empty -> slug: None fm: {}
A3 single-self-declaring -> slug: None fm: {}
A4a deliverable -> slug: deliverable-slug fm: {'author': 'deliverable-slug'}
A4a required_verification_missing -> 1 (verify-1 excluded as same-author, verify-2 counts -> 1 missing of 2, refuses)
```
derived: `gates.spawn_on_pr.subject_deliverable_record()` / `gates.merge_gate.required_verification_missing()`
called directly this session (`/tmp/verify-2664`) against four constructed
`subject_board` dicts: (A1) every record self-declares `verifies_subject:
true`; (A2) no records at all; (A3) exactly one record, and it self-declares;
(A4) a verifying record's `author:` spoofed to match the deliverable's own
author (impersonation attempt to dodge exclusion), alongside a second,
honestly-different-author verifying record. A1/A2/A3 all land on `(None, {})`
— refuses to guess, per design. A4 still refuses (`required_verification_missing`
→ 1, not 0) — spoofing an author field to *match* the deliverable can only
make the guard *more* conservative (wrongly excludes a possibly-real verifier
from the count), never less; no exploit found in this direction.

### 7 currently-open subjects (behavior-change tradeoff)

derived: `gh issue list --repo tokenmaxxxer/on-the-record --state open --limit
300 --json number` → 47 open issue numbers, cross-referenced (Python, this
session, `/tmp/verify-2664`) against the 550-subject old-matched bucket for
subjects where `old_match()`'s result differs from `new_match()`'s result:
```
issue-1725 records: ['implementation'] old-> implementation new-> implementation
issue-2079 records: ['implementation'] old-> implementation new-> implementation
issue-2092 records: ['implementation'] old-> implementation new-> implementation
issue-2152 records: ['implementation'] old-> implementation new-> implementation
issue-2153 records: ['implementation'] old-> implementation new-> implementation
issue-2159 records: ['implementation'] old-> implementation new-> implementation
issue-2193 records: ['implementation'] old-> implementation new-> implementation
```
All 7 named by the PR (1725, 2079, 2092, 2152, 2153, 2159, 2193) resolve
identically under old and new logic *today* — zero open subjects differ right
now. The PR's "loses precision" claim is prospective, confirmed by simulation:
```
today: implementation implementation
+legacy observer, no field: implementation None
```
derived: adding a synthetic second record (`execution-observation`, no
`verifies_subject` field — the pre-#2609 shape) to `issue-1725`'s board dict
flips `new_match` to ambiguous while `old_match` still resolves by name. The
PR's future-tense framing ("lose... precision") is accurate, not overstated.

Went further than the PR's own disclosure — the same structural change also
produces additional subjects whose resolution differs between old and new
logic (precisely resolved pre-fix, ambiguous post-fix):
```
newly-ambiguous (was precisely resolved pre-fix, now None post-fix): 99
...of which currently OPEN: []
```
derived: same script, `/tmp/verify-2664`, cross-referenced against the same
47-open-issue list. Zero overlap — the wider regression is real but entirely
confined to closed/historical subjects with no live merge-gating consequence
today. The PR's narrower "7 open subjects" framing is accurate for what
currently has any operational effect.

### Bullet 3 — board rendering

acceptance: `python3 spawn.py -C .` (the real board-status invocation, no
args), run in `/tmp/verify-2664` — result:
```
subject: issue-1005
  [record: implementation] loop_state: landed   verdict: pass
subject: issue-103
  [record: coding] loop_state: landed
```
canonical: the exact incident strings quoted in issue #2593's own Ask section
(`[implementation]`, `[coding]`), now rendered with the `record:` prefix.
**Present.**

Where a session finds the real spawnable vocabulary — checked directly, not
inferred:
```
$ python3 spawn.py --help | grep -A5 -- '--skills SKILLS'
  --skills SKILLS       이슈 #2572: 유일한 스폰 형태 — spawn.py --skills <스킬>[,<스킬>...]
                        "<맡길 일>" --issue <n>. 쉼표로 구분한 스킬 이름 목록을 네 소스 — skill-
                        repository 체크아웃(MUSTER_SKILL_REPO 또는 형제-클론), 설치된 플러그인의
                        skills/, ~/.claude/skills, 타깃 저장소 .claude/skills — 에
                        걸쳐 해석해 마운트한다(이슈 #1742/#1774/#2488).
```
canonical: `on-the-record/commands/consult.md:31-33` (`55b58c12` worktree,
read directly) states "큐레이션된 목록은 없다: 실제 이름은 skill-repository
체크아웃의 디렉터리 목록이다" with the literal `ls
"${MUSTER_SKILL_REPO:-$TOKENMAXXXER_RULEBOOKS/skill-repository}"` command. A
session reading `[record: implementation]` has an explicit "record:" signal
that this is a historical filename, not a `--skills` value, and a stated,
executable path to the real vocabulary.

### #2548-test applied to the PR's own "no reshape found" claim

Ran `scripts/audit_removal_claim.py` myself (not the PR's hand-classification)
against `PR_TRIGGERED_RECORD_KINDS` / member samples `["execution-observation",
"conformance-review"]`, `min_coloc=2`, in `/tmp/verify-2664`:
```
=== PR_TRIGGERED_RECORD_KINDS closed tuple ===
verdict: RESHAPE_DETECTED
detail: closed set reconstructed in: [('./.claude-plugin/marketplace.json', 2), ('./__pycache__/directive_assembly.cpython-310.pyc', 2), ('./directive_assembly.py', 2), ('./gates/__pycache__/spawn_on_approve.cpython-310.pyc', 2), ('./gates/merge_gate.py', 2), ('./gates/spawn_on_approve.py', 2), ('./on-the-record/commands/run.md', 2), ('./on-the-record/directive/spawn-and-board.md', 2), ('./on-the-record/hooks/pr-base-guard.sh', 2), ('./runs/rulebooks/tokenmaxxxer-core/.git/FETCH_HEAD', 2), ('./runs/rulebooks/tokenmaxxxer-core/.git/index', 2), ('./runs/rulebooks/tokenmaxxxer-core/.git/packed-refs', 2), ('./runs/rulebooks/tokenmaxxxer-core/core/hooks/approval-gate.sh', 2), ('./spawn.py', 2)]
```
canonical: hand-read every one of the 14 co-located files this session
(`grep -n "execution-observation\|conformance-review"` on each, then the
surrounding lines). 13 are false positives — prose/comments/directive
docs/`.pyc`/`.git` internals/an unrelated plugin's `marketplace.json` — this
confirms the PR's own claim, for the on-the-record repo itself.

One is not a false positive:
```
$ sed -n '319p' runs/rulebooks/tokenmaxxxer-core/core/hooks/approval-gate.sh
OBSERVER_ROLES = ("execution-observation", "conformance-review")
$ sed -n '311,313p' runs/rulebooks/tokenmaxxxer-core/core/hooks/approval-gate.sh
if issue_state != "OPEN" and role in OBSERVER_ROLES:
    impl_branch = "issue-%s/implementation" % issue_num
```
canonical: read directly this session — a live closed 2-tuple, branched on to
decide whether a phase-gate execution-surface write is exempted, plus a
hard-coded `"issue-%s/implementation"` branch name a line below it. This is a
genuine, live instance of the exact #2548 anti-pattern issue #2593 is about.

It does not invalidate any of the four Present verdicts above:
```
$ git check-ignore -v runs/rulebooks/tokenmaxxxer-core
.gitignore:1:runs/	runs/rulebooks/tokenmaxxxer-core
```
canonical: `runs/` is gitignored in the on-the-record repo — this is a
separate git checkout of the `tokenmaxxxer-core` harness plugin present on
local disk (the very plugin whose hooks drive this session), not a tracked
file PR #2664 touches, and not one of the six surfaces issue #2593's own
Scope section names. Out of scope for this issue and this PR; recorded below
as a finding for a separate issue against that plugin.

### Test suite

```
$ python3 -m pytest test/ -q     # /tmp/verify-2664, PR #2664 branch
15 failed, 358 passed, 3 xfailed in 3.13s

$ python3 -m pytest test/ -q     # /tmp/verify-main-2664, origin/main
15 failed, 353 passed, 3 xfailed in 2.86s
```
derived: same 15 failing test names on both (network/environment-dependent —
`gh` calls to a nonexistent remote, checked directly in the failure output).
358 - 353 = 5, matching exactly the 5 tests contributed by the PR's two new
test files (untracked on this session's own branch — they exist only on PR
#2664's branch, `/tmp/verify-2664`), separately confirmed passing there:
```
$ python3 -m pytest test/test_subject_deliverable_record_name_free.py test/test_board_bracket_provenance.py -q
5 passed in 0.86s
```

## Why

adversarial-review and silent-failure-audit both apply directly: the task is
an independent re-derivation of another session's already-"Present"-labeled
claims (do not trust the maker's self-report), with particular attention to
whether an error/ambiguity path (the self-verification guard's
`subject_author=None` fail-open) is silently absorbed rather than surfaced.
Two disposable worktrees, rather than reading the diff and reasoning about it,
kept the comparison honest — pre-fix and post-fix code were both actually
executed against constructed and real board data, not read and inferred.

## Upstream basis

PR #2664, branch `issue-2593/silent-failure-audit+architecture-interface-contract-shape-79606e42`,
commit `55b58c12a17d3c2f519abfb504ecd8dfb2db8146`, diffed against `origin/main`
@ `de8b7ffe`:
```
$ git diff origin/main...HEAD --stat
 board.py                                           |  14 +-
 ...chitecture-interface-contract-shape-79606e42.md | 171 +++++++++++++++++++++
 gates/spawn_on_pr.py                               |  54 ++++---
 test/test_board_bracket_provenance.py              |  48 ++++++
 test/test_subject_deliverable_record_name_free.py  | 120 +++++++++++++++
 5 files changed, 387 insertions(+), 20 deletions(-)
```
canonical: matches the PR's own stated diffstat exactly. Issue #2593 itself
(`gh issue view 2593 --repo tokenmaxxxer/on-the-record`) supplied the
Acceptance section verbatim and the Scope section's six named surfaces, both
read directly this session.

## Open findings

1. `runs/rulebooks/tokenmaxxxer-core/core/hooks/approval-gate.sh:319`'s
   `OBSERVER_ROLES = ("execution-observation", "conformance-review")` is the
   same #2548-pattern defect, in a different, gitignored plugin checkout, out
   of issue #2593's scope (see "#2548-test applied..." above for the
   canonical read). Resolution path: file a new issue against the
   `tokenmaxxxer-core` rulebook — not actionable from inside this repo or PR.
2. The self-verification guard's fail-open-with-no-log behavior survives the
   fix, on a larger subject pool than pre-fix:
   ```
   total subjects: 633
   post-fix: subjects where guard is skipped (ambiguous/no deliverable) -> 124
   pre-fix : subjects where guard was skipped (unmatched) -> 83
   ```
   derived: `new_none`/`old_none` counts over `board.board(Path('.'))`, same
   script as the 550/83/62/21 section, this session, `/tmp/verify-2664`. This
   is the same gap PR #2664's own upstream record already discloses as its
   own "Open Finding 1," not a new, undisclosed one — no action needed from
   this record.
3. Neither of the above changes the Present verdict on any of issue #2593's
   four acceptance bullets (see each bullet's own section above for the
   canonical/derived evidence).

## Next steps

None. `loop_state: landed`. Every claim in "What was done" above carries its
own `acceptance:`/`derived:`/`canonical:` evidence inline — nothing further to
re-derive.

skill-verdict: adversarial-review — applied: invoked; ran the entire
verification in two disposable worktrees seeded only from PR #2664's branch
and `origin/main`, never trusting PR #2664's own record or hand-classification
as evidence for any section above — every grep, every synthetic pre/post-fix
repro, both count derivations, and the `audit_removal_claim.py` run were
re-executed independently this session.
skill-verdict: silent-failure-audit — applied: invoked; traced
`subject_deliverable_record()`'s ambiguous/`(None, {})` return path end to end
through both call sites into `verifying_record_count()`'s self-verification
guard, classified the `subject_author=None` fail-open as Silently Absorbed (no
log/reason string surfaces "guard skipped"), confirmed it is the same gap PR
#2664 already discloses (not new — see Open Finding 2), and quantified its
post-fix blast radius there.
