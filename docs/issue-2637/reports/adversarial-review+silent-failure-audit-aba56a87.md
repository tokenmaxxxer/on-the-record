---
issue: 2637
role: adversarial-review+silent-failure-audit-aba56a87
author: adversarial-review+silent-failure-audit-aba56a87
skills: adversarial-review (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: true
loop_state: landed
upstream:
  - path: priorities.py (PR #2643, branch issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985, untracked in this branch)
    sha: aa152c797e60e6620e8162dec586b97fc8f171e1
  - path: on-the-record/hooks/deliverable-guard.sh (baseline path exists in this branch too, PR #2643 modifies its content)
    sha: aa152c797e60e6620e8162dec586b97fc8f171e1
---

# issue-2637 — adversarial-review+silent-failure-audit-aba56a87 record

## What was done

Independent verification of PR #2643 (issue #2637, "shard priorities.md into
one-file-per-entry directory") against the issue's own Acceptance section,
re-derived from scratch in a fresh worktree against `origin/main` and the
branch tip — not read from the PR body or the implementation record's pasted
transcripts.

canonical: `gh pr view 2643 --repo tokenmaxxxer/on-the-record` — head
`issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985`,
base `main`, state OPEN, additions 1043 / deletions 8, "Closes #2637".

derived: `git fetch origin issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985 main && git worktree add /tmp/v2637-review origin/issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985 && git -C /tmp/v2637-review rev-parse HEAD origin/main` — result:
```
aa152c797e60e6620e8162dec586b97fc8f171e1
5f23f894527842d8088b094d75210e23ee0395f5
```
`origin/main` has advanced past the PR's own base by three unrelated commits
(issue-2628 AUTO_SPAWN_ROLES work). `git merge-base origin/main HEAD` ==
`9a1de9bbdcc293d2c47a199985e5a312ca6df274`, and
`git diff --stat 9a1de9bb..HEAD` (run in the worktree) shows exactly 8 files
changed / 1043 insertions / 8 deletions — matches the PR view's stated
additions/deletions above, confirming the worktree tip is the PR's real,
uncorrupted diff. All checks below ran against this worktree (plus
disposable fixture repos under `/home/jwjung/dgtest2`, `/home/jwjung/pcstest`,
`/home/jwjung/mergetest` for the hook/merge reproductions — none of these
paths are on this record's own write set and none were committed anywhere).

**Verdict: Present** on acceptance bullets 1 and 2 and the `must not`
clause. **Present with one confirmed regression** on acceptance bullet 3 —
three of four named consumers verified working as claimed; the fourth
(`deliverable-guard.sh`) correctly closes the warrant-hunt's src/-rooted
bypass, but the same anchoring fix introduces a new false-deny for
legitimate absolute-path shard writes, not mentioned anywhere in the PR's
own record or hunt file.

### Acceptance bullet 1 — construct two branches that each add an entry from the same base, merge both in sequence, show neither conflicts

Verdict: **Present.**

derived (fixture built independently, not copied from the record):
```
cd /home/jwjung/mergetest && git clone -q /tmp/v2637-review . && git checkout -q aa152c79
BASE=$(git rev-parse HEAD)
git checkout -q -b branch-A "$BASE"   # mints one shard via _priorities_entry_path, commits it
git checkout -q -b branch-B "$BASE"   # mints a second shard the same way, commits it
git checkout -q -b merged "$BASE"
git merge --no-ff branch-A -m "merge A"   # -> "Merge made by the 'ort' strategy.", no CONFLICT
git merge --no-ff branch-B -m "merge B"   # -> "Merge made by the 'ort' strategy.", no CONFLICT
git status --porcelain                    # -> empty
```
Result: both merges reported `Merge made by the 'ort' strategy.` with zero
`CONFLICT` lines and a clean `git status --porcelain` afterward.
derived: repeated with the merge order reversed
(`git checkout -q -b merged-reverse aa152c79 && git merge --no-ff branch-B ... && git merge --no-ff branch-A ...`)
— same clean result (no `CONFLICT` line, clean `git status --porcelain`),
kept for the ordering check in bullet 2 below.

### Acceptance bullet 2 — read the entries back in order and show the ordering rule that produced it

Verdict: **Present.**

canonical: `aa152c79:priorities.py:98-119` (`read_priorities()`) — the
ordering rule: legacy flat-file content (if present) is appended first,
then shard files under the `priorities` directory in
`sorted(d.glob("*.md"))` order — filename order — and filenames are
`%Y%m%dT%H%M%S%f-<pid>.md` (fixed-width UTC microsecond timestamp + pid,
`aa152c79:priorities.py:82-95`), so filename-sort == chronological-sort by
construction.

derived: in the `merged` worktree from bullet 1,
`python3 -c "from priorities import read_priorities; print(read_priorities(None, cwd='.'))"`
returned legacy content, then `### Entry from session A`, then `### Entry
from session B` — the mint order. Re-ran the identical read against
`merged-reverse` (branch-B merged first, branch-A merged second) — **same
output order** (A before B) — proving the order comes from the filename
timestamp, not from merge order.

### Acceptance bullet 3 — name every consumer of priorities.md, show each still works

Verdict: **Present with one confirmed regression.**

Consumer set independently derived, not accepted from the PR body:
derived: `grep -rl "priorities\.md" --include="*.py" --include="*.sh" /tmp/v2637-review`
(excluding `priorities.py` itself and this session's scratch files) returned
exactly `spawn.py`, `on-the-record/hooks/product-capture-stopgate.sh`,
`on-the-record/hooks/deliverable-guard.sh` — plus
`on-the-record/hooks/skill-verdict-guard.sh` (found via
`grep -n priorities on-the-record/hooks/skill-verdict-guard.sh`, which
references the concept in advisory prose rather than the literal string
`priorities.md`). This is the same four-consumer list the PR names —
confirmed by independent grep, not by trusting the list.

1. **`spawn.py` — Present.** `spawn.py:2335-2348` adds `priorities-log`/
   `priorities-path` subcommands.
   derived: `cd /tmp/v2637-review && python3 spawn.py priorities-path` →
   printed a fresh `docs/reports/product/priorities/<ts>-<pid>.md` path
   (exit 0); `python3 spawn.py priorities-log` → printed the legacy file's
   content leading the output (exit 0).

2. **`on-the-record/hooks/skill-verdict-guard.sh` — Present.**
   `git diff origin/main..HEAD -- on-the-record/hooks/skill-verdict-guard.sh`
   is a one-line wording change inside the advisory reminder string
   (`aa152c79:on-the-record/hooks/skill-verdict-guard.sh:167-168`), no
   control flow touched. canonical: the diff itself, read directly — no
   live exercise needed since nothing functional changed.

3. **`on-the-record/hooks/product-capture-stopgate.sh` — Present.** Built a
   throwaway repo (`/home/jwjung/pcstest`) on a plain (non-`issue-<n>/`)
   branch with a transcript containing one 우선순위-triggering user turn,
   and drove the real hook via stdin with `TOKENMAXXXER_SPAWNED` unset:
   derived:
   ```
   # no shard present, fresh session id
   python3 mkpayload.py sess-fresh-1 | env -u TOKENMAXXXER_SPAWNED \
     OTR_PRODUCT_CAPTURE_STATE_DIR=/home/jwjung/pcstest_state \
     bash on-the-record/hooks/product-capture-stopgate.sh
   # -> {"hookSpecificOutput": {..., "additionalContext": "product-capture-stopgate: ... priorities/ (spawn.py priorities-path; ...) ..."}}

   # untracked shard created at the fixed docs/reports/product/priorities path, fresh session id
   python3 mkpayload.py sess-fresh-2 | env -u TOKENMAXXXER_SPAWNED \
     OTR_PRODUCT_CAPTURE_STATE_DIR=/home/jwjung/pcstest_state \
     bash on-the-record/hooks/product-capture-stopgate.sh
   # -> no output, exit 0
   ```
   This exercises the new `git status --porcelain` fallback
   (`aa152c79:on-the-record/hooks/product-capture-stopgate.sh:240-249`),
   which exists because `git diff`/`git log -p` never see untracked paths —
   reproduced both the "should nudge" and "should stay silent" cases
   against the real script.

4. **`on-the-record/hooks/deliverable-guard.sh` — Present for the claimed
   fix, but a new regression found.**
   Warrant-hunt's claimed bypass, reproduced against the pre-fix regex
   myself (not copied from the hunt file): the pre-fix pattern used
   `.search()` with no `^` anchor. derived: piping a `Write` payload with
   `file_path: "src/docs/reports/product/priorities/hack.md"` into the
   pre-fix content of `deliverable-guard.sh` exits 0 (silently allowed,
   letting a `src/`-rooted deliverable write through).
   derived (against the **landed**, post-fix hook in the worktree, fixture
   repo `/home/jwjung/dgtest2`, `TOKENMAXXXER_SPAWNED` unset):
   ```
   relative shard legit      docs/reports/product/priorities/<ts>.md      -> rc=0 (exempt, correct)
   exploit rel src-rooted    src/docs/reports/product/priorities/hack.md  -> rc=2 (denied, FIXED)
   exploit abs src-rooted    /home/jwjung/dgtest2/src/.../hack.md         -> rc=2 (denied, FIXED)
   real deliverable rel      src/foo.py                                   -> rc=2 (denied, correct)
   legacy priorities.md rel  docs/reports/product/priorities.md           -> rc=0 (exempt, correct)
   ```
   The landed fix holds against both the hunt's own exploit shape and my
   own repeat of that shape with an absolute path. **But** a different
   shape the fix did not consider — a legitimate shard write using an
   **absolute** `file_path`, a form several sibling hooks in this same
   codebase already treat as expected input — produces a false-deny:
   derived:
   ```
   abs shard legit           /home/jwjung/dgtest2/docs/reports/product/priorities/x.md  -> rc=2 (WRONGLY DENIED)
   abs legacy priorities.md  /home/jwjung/dgtest2/docs/reports/product/priorities.md    -> rc=0 (correctly exempt)
   abs approvers.md          /home/jwjung/dgtest2/docs/specs/approvers.md               -> rc=0 (correctly exempt)
   ```
   canonical: `aa152c79:on-the-record/hooks/deliverable-guard.sh:129-134`
   (quoted verbatim):
   ```python
   PRODUCT_CAPTURE_PRIORITIES_DIR_RE = re.compile(
       r"^docs/reports/product/priorities/[^/]+\.md$"
       r"|^docs/issue-\d+/reports/product/priorities/[^/]+\.md$"
   )
   ```
   is anchored with `^` against the raw, un-rooted `n`
   (`posixpath.normpath(p...)`), which only equals `"docs/..."` when
   `file_path` arrived relative. The two pre-existing exemptions three
   lines above it — `EXEMPT_SUFFIXES` via `.endswith(...)` and
   `PRODUCT_CAPTURE_ISSUE_RE` via unanchored `.search(...)` — both
   tolerate an absolute `file_path` (confirmed above: the abs
   legacy/approvers cases both return rc=0). Only the PR's new,
   `^`-anchored regex fails on an absolute path, because closing the
   bypass by anchoring to string-start also excludes any absolute prefix.
   This is not a contrived edge case: `deliverable-guard.sh` itself, three
   lines below the new regex, computes
   `d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))`
   (`aa152c79:on-the-record/hooks/deliverable-guard.sh:157`) — the
   identical `isabs` branch also appears in
   `aa152c79:on-the-record/hooks/call-shape-guard.sh:55`,
   `aa152c79:on-the-record/hooks/accumulation-claim-guard.sh:54`, and
   `aa152c79:on-the-record/hooks/record-claim-guard.sh:134`, confirming the
   codebase's own standing convention treats `file_path` as legitimately
   arriving absolute. derived: `git ls-files | grep -i "test.*deliverable"`
   returns nothing — no test suite exists for this hook, before or after
   this PR — and the PR's own record/hunt file never mentions absolute
   paths. In normal usage where the calling tool supplies an absolute
   `file_path` (the same form the surrounding code already anticipates), a
   real orchestrator-session priorities-shard write is wrongly refused
   post-fix, where the old unanchored suffix rule this case duplicates in
   spirit would have exempted it.

### `must not` clause — no loss/reorder of existing entries; no invented third convention

Verdict: **Present.**

derived: `diff <(git show origin/main:docs/reports/product/priorities.md) <(git show HEAD:docs/reports/product/priorities.md)`
→ no output (byte-identical); `git log --oneline -- docs/reports/product/priorities.md`
on the PR branch shows no new commit touching that path — the legacy file
is frozen exactly as claimed. canonical: `aa152c79:priorities.py:112-119`
(`read_priorities()`) reads it verbatim (`legacy.read_text(...)`, no
rewrite) and prepends it ahead of the shards, so no existing entry is
dropped, reordered, or rewritten — confirmed empirically in bullet 2's
read-back above.

No third sharding convention was invented: canonical:
`aa152c79:priorities.py:11-16` (module docstring) states the shape (a
`priorities` directory paralleling `docs/reports/product/`, timestamp+pid
shard filenames, directory-glob aggregate reader) is structurally identical
to `consult.py`'s `_consult_trace_dir()`/`_consult_trace_path()`, and the
one stated divergence (entry-level vs. session-level sharding, next
section) is documented, not silent.

### Claim: warrant-hunt caught an unanchored-regex bypass in the new deliverable-guard.sh exemption and fixed it

Verdict: **CONFIRMED.**

canonical: this session's own reproduction under acceptance bullet 3 item 4
above — pre-fix `file_path: "src/docs/reports/product/priorities/hack.md"`
exits 0 (bypass reproduced independently, not read from the hunt file's
pasted transcript); post-fix, the same payload exits 2 (denied). My own
second attempt at defeating the *landed* regex — a shape the fix did not
consider, an absolute `file_path` for a legitimate shard — found the
false-deny regression documented in that same section.

### Claim: divergence from #2333 — sharded per entry, not per session

Verdict: judged **sound.**

canonical: `aa152c79:priorities.py:82-95` (`_priorities_entry_path()`) never
caches a filename — every call mints `<timestamp>-<pid>.md` fresh. Cross-
session collision requires identical microsecond *and* identical pid; two
different sessions are two different OS processes and therefore always have
different pids at any given instant. Within a single process, collision
requires two calls landing in the identical microsecond.
derived: `python3 /tmp/v2637-review/scratch_collision_test.py` (calls
`_priorities_entry_path` 5000 times in a tight loop from one process) →
`total 5000 unique 5000`, `dupe count 0`. "Two entries scribed in the same
second by different sessions" therefore produce filenames differing at
minimum in the pid suffix, and in practice also in the microsecond field —
e.g. the real filenames minted by bullet 1's fixture:
`20260827T091814673938-4177198.md` and `20260827T091814914699-4177245.md`
(same second, different microsecond, different pid).

### Claim: requirements.md/philosophy.md/goals.md share the write mechanism but have never been written to

Verdict: **CONFIRMED.**

derived: `git log --all --oneline -- '**/requirements.md'` /
`'**/philosophy.md'` / `'**/goals.md'`, cross-checked against
`docs/reports/product/` and `docs/issue-*/reports/product/` specifically —
zero commits touch `docs/reports/product/requirements.md` (untracked,
never committed at that path in this repo's history),
`docs/reports/product/philosophy.md` (untracked, never committed at that
path), or `docs/reports/product/goals.md` (untracked, never committed at
that path) at any point. The four hits `requirements.md` alone returns are
unrelated files — `docs/specs/requirements.md`,
`docs/issue-54/proposals/requirements.md`, etc. — different paths, not the
product-capture category file. derived: `ls docs/reports/product/` on the
branch tip lists only `priorities.md`, `quality-bar.md`,
`2026-08-14-hiring-market-recon.md` — none of the other three category
files exist on disk either. The PR's scoping decision (converting only
`priorities.md`) rests on a true premise.

### Sanity check: "24 historical doc references confirmed no-op"

derived: `grep -rl "priorities\.md" --include="*.md" docs/ | wc -l` → 25.
`grep -rl "priorities\.md" --include="*.md" docs/ | grep -c "issue-2637"` →
1 (the PR's own new record file, which necessarily mentions
`priorities.md` while describing the PR itself). 25 − 1 = 24, matching the
claimed count exactly.

## Why

The task requires re-deriving every acceptance check from scratch rather
than trusting the PR body or its pasted transcripts, per standard
independent-verification practice (`docs/handbooks/observer-verification.md`)
and this session's own adversarial-review/silent-failure-audit skills:
adversarial review treats the deliverable's own self-report as untrustworthy
by construction, and silent-failure-audit requires tracing each new
try/except to its downstream consequence rather than accepting "handled" on
the implementer's word. Both skills point at the same regression: a
security-shaped fix (the anchored regex) was accepted on the strength of
one passing reproduction without checking whether the fix's own new
condition (`^`-anchoring against a non-rooted string) held for every input
shape the surrounding code already supports.

skill-verdict: adversarial-review — applied: invoked; treated PR #2643's
own record/hunt transcripts as untrustworthy self-report and re-derived
every acceptance check and load-bearing claim independently in a fresh
worktree per the sections above, rather than accepting the pasted
transcripts as evidence.
skill-verdict: silent-failure-audit — applied: invoked; enumerated every
new try/except in the PR's diff
(`aa152c79:on-the-record/hooks/product-capture-stopgate.sh:240-249`'s
`git status --porcelain` fallback — the only new try/except the diff adds
outside `priorities.py`'s deliberately-unwrapped `read_text()` calls) and
traced its failure path forward: `except (OSError, subprocess.SubprocessError): pass`
leaves `added_lines` at 0, which fails open toward still emitting the
advisory nudge (never silently suppresses it) — classified Handled, not
Silently Absorbed.

## What did not work

None.

## Upstream basis

- `priorities.py`, `on-the-record/hooks/deliverable-guard.sh`,
  `on-the-record/hooks/product-capture-stopgate.sh`,
  `on-the-record/hooks/skill-verdict-guard.sh`, `spawn.py` — PR #2643,
  branch `issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985`,
  sha `aa152c797e60e6620e8162dec586b97fc8f171e1` (this record's subject;
  `priorities.py` is a new file added by that PR, untracked on this
  branch — read from the `/tmp/v2637-review` worktree).
- `docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md`
  (untracked in this branch), and its
  `.../2026-08-27-hunt-issue-2637-priorities-sharding.md` (untracked in
  this branch) and
  `.../deviation-log/20260827T091104549429-5b51be7623d773d1.md` (untracked
  in this branch) — same sha, same branch as PR #2643 above — read for the
  claims under test but not trusted as evidence; every claim they make was
  independently re-derived above.

## Open findings

1. **`deliverable-guard.sh`'s new `PRODUCT_CAPTURE_PRIORITIES_DIR_RE`
   wrongly denies a legitimate priorities shard write when `file_path`
   arrives absolute.** canonical:
   `aa152c797e60e6620e8162dec586b97fc8f171e1:on-the-record/hooks/deliverable-guard.sh:129-134`,
   reproduced under acceptance bullet 3 item 4 above (derived: the
   `abs shard legit -> rc=2` line in that section's fenced reproduction).
   Resolution path: anchor the exemption check against the same
   cwd-rooted `d` the git-root walk already computes three lines below it
   (`aa152c79:on-the-record/hooks/deliverable-guard.sh:157`), the way
   `call-shape-guard.sh`/`accumulation-claim-guard.sh`/`record-claim-guard.sh`
   already handle the isabs/relative split, instead of anchoring `^`
   against the raw un-rooted `n`. Out of this record's own write scope —
   this is a verification record, not the implementation — flagged for
   the subject's next round rather than fixed here.

## Next steps

None — `loop_state: landed`. The open finding above is the subject's next
round of work, not this record's.
