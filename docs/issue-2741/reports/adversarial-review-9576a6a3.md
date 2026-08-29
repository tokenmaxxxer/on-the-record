---
issue: 2741
role: adversarial-review-9576a6a3
author: adversarial-review-9576a6a3
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 76a76c928e290bd2d28ed47850b8ae7cd94aa9f6
loop_state: landed
type: review
breaking: false
verdict: confirmed — PR #2746 (on-the-record) + tokenmaxxxer-core#353 correctly implement the operator's ruling on issue #2741's scope-correction comment (PR-body trailer and GitHub labels are in-scope persisted keys); every claim in both PRs was re-derived directly against the repos rather than trusted from either PR's transcript, and all held. One point of independent disagreement with the orchestrator's own framing (not with the PR): gates/finding_shape.py:23 is correctly left untouched by both PRs, and I judge that correct rather than a miss — it enforces docs/ frontmatter shape, and docs/ frontmatter keeps `role:` forever by this same issue's own non-goal, demonstrated live by this very record's own frontmatter and by the two already-landed adversarial-review records under docs/issue-2741/reports/.
upstream:
  - path: 76a76c92:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-bd0ced79.md
    sha: 76a76c928e290bd2d28ed47850b8ae7cd94aa9f6
  - path: ffaf0d9:tokenmaxxxer-core PR #353, branch issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a
    sha: ffaf0d90628309264ed17991104afeb63cc37bce
---

# issue-2741 — adversarial-review-9576a6a3 record

## What was done

Independently verified `tokenmaxxxer/on-the-record#2746` (head `76a76c92`,
which supersedes the CHANGES-returned #2743) and its cross-repo companion
`tokenmaxxxer/tokenmaxxxer-core#353` (head `ffaf0d9`) — canonical: `gh pr
view 2746 --repo tokenmaxxxer/on-the-record` and `gh pr view 353 --repo
tokenmaxxxer/tokenmaxxxer-core`, both executed live this session. Every
claim below was re-derived from fresh `git worktree`s at `main` and each PR
head in both repos, plus a from-scratch synthetic workspace for the
round-trip/merge-order tests — not read off either PR's own transcript or
record.

### 1 — Write-site enumeration and the reverse direction

canonical: this session's own command,
`git grep -nE '"role"|'"'"'role'"'"'|role\.json|role:' -- '*.py' '*.sh' ':!docs'`,
run against on-the-record `main` (207 hits) and PR head `76a76c92` (66
hits); `diff` of the two hit-lists (cut to `path:content`, dropping line
numbers) shows exactly the ~80 persisted-key sites disappearing, matching
PR #2743's original ~17-site rename plus the two ruled-in-scope sites
below — no unrelated identifier or non-persisted local variable was swept
up in the rename.

Reverse direction — isolating exactly what #2746 changed beyond PR #2743's
own diff: derived: `git diff --stat pr-2743 76a76c92 -- . ':!docs'`
(pr-2743 = PR #2743's own head, fetched this session) returns exactly six
files — `gates/flows.py`, `gates/patrol_board.py`, `gates/patrol_promote.py`,
`relay.py`, `test/test_branch_role_field.py`,
`test/test_convention_equivalence.py` — 16 insertions/15 deletions total.
Nothing outside the ruled-in-scope trailer/label rename and the two
test-literal fixes (section 4 below) was touched; no site that is not a
write-then-parse-back persisted key was renamed.

### 2 — The two orchestrator-flagged sites, adjudicated independently

**`gates/patrol_board.py`/`gates/patrol_promote.py` GitHub labels and
`relay.py`/`gates/flows.py` PR-body trailer — confirmed in scope, confirmed
fixed.** canonical: `git show 76a76c92:gates/patrol_board.py` lines
225-340 and `git show 76a76c92:gates/patrol_promote.py` lines 230-245 —
both now build `f"skill:{skill}"` labels, no `"role:{skill}"` remnant
(confirmed by `git grep -nE 'f"role:\{skill\}"|"role:\{skill\}"'` on
`76a76c92` returning nothing). `git show 76a76c92:relay.py` line 267 now
writes `f"...\n\nskill: {skill}"`, and `git show 76a76c92:gates/flows.py`
line 37 shows `_ROLE_TRAILER_RE = re.compile(r"^skill:\s*([a-z0-9-]+)\s*$")`
— writer and reader moved together in the same commit
(`bd6ed289`, `git show --stat bd6ed289` touches both files).

**`gates/finding_shape.py:23` — I judge out of scope, disagreeing with the
orchestrator's "in scope" framing, not with the PR (which left it
untouched).** canonical: `git show 76a76c92:gates/finding_shape.py` lines
1-40 read this session. `_REQUIRED_FRONTMATTER = ("role", "date",
"domain_rule", "target_repo")` validates the frontmatter shape of files
under `docs/reports/findings/<role>/...md` and
`docs/issue-<n>/reports/findings/<role>/...md` — a `docs/`-tree document,
not a runtime-state dict. Issue #2741's own non-goal states plainly "`docs/`
content in either repo" stays out of scope, and population 1 says record
frontmatter under `docs/` "stays `role:` forever." This is directly
demonstrated live, in this same issue, by two already-landed records:
`git show 00aeaae4:docs/issue-2741/reports/adversarial-review-6a02d514.md`
line 3 reads `role: adversarial-review-6a02d514`, and
`git show c969e44d:docs/issue-2741/reports/adversarial-review-a7c51853.md`
line 3 reads `role: adversarial-review-a7c51853` — both written today,
2026-08-30, after the operator's rename ruling, and both still use `role:`
in `docs/` frontmatter (this record's own frontmatter, above, does the
same). A findings-record shape checker requiring the identical `docs/`
convention key is consistent with that same precedent, not a miss.
`gates/finding_shape.py` also writes nothing itself (it is `check(spec) ->
list[str]`, a pure validator), and no `76a76c92:docs/reports/findings/`
files exist yet to be affected either way — derived:
`find docs/reports/findings -type f 2>/dev/null | wc -l` run in the
`76a76c92` worktree this session returns `0`.

**`gates/findings_due.py:69,82` — confirmed out of scope, print-only.**
canonical: `git show 76a76c92:gates/findings_due.py` lines 60-90 —
`findings_due()` builds `{"role": skill, ...}` dicts, and `format_report()`
immediately consumes them into printed strings
(`f"  - {d['role']} ({d['date']}): ..."`). Traced the only call site,
`git show 76a76c92:spawn.py` lines 2411-2421 (`a.role == "findings-due"`
branch): it calls `findings_due()`, formats, `print()`s each line, and
`return`s — the dict is never written to a file, never re-parsed, never
compared. derived: `git grep -n "findings_due\|format_report"
76a76c92 -- 'test/*' 'tests/*'` returns nothing — no test pins this dict's
key literal either, confirming there is no downstream consumer that would
need the rename.

### 3 — Trailer/label round-trip and no dual read

Confirmed writer and reader moved together (section 2). Confirmed no
compatibility alias in production code: derived:
`git grep -nE '\.get\("role"\)|\["role"\]' -- '*.py' '*.sh' ':!docs'
':!test' ':!tests'` on on-the-record `76a76c92` and on core `ffaf0d9` both
return empty — no site reads the old key as a fallback.

### 4 — The two self-found test-literal misses, confirmed real

PR #2746 claims it found two test-literal misses the CHANGES comment did
not name: `test/test_branch_role_field.py:544` and
`test/test_convention_equivalence.py`'s
`BranchRoleFieldDualReadEquivalenceTest.test_flows_role_from_pr_prefers_trailer_over_branch_group`.
canonical: `git show pr-2743:test/test_branch_role_field.py` — three
trailer-text literals exist at lines 164, 544, and 565, all reading
`"role: implementation"` / `"role: <skill>"` (derived:
`git grep -n '"role: implementation"\|role: implementation' pr-2743 --
test/test_branch_role_field.py` on PR #2743's own head). The CHANGES
comment on PR #2743 named only 164 and 565 ("`test/test_branch_role_field
.py:164,565`'s assertions follow from (1) — update them with it") — line
544 (`test_field_read_prefers_trailer`) was not named, and neither was
`test_convention_equivalence.py`'s
`test_flows_role_from_pr_prefers_trailer_over_branch_group`
(`pr_with_trailer = {"body": "Part of #1792.\n\nrole: product-discovery"}`
at line 438 in the CHANGES-comment state), even though both assert on the
exact trailer text the CHANGES comment's own ruling (1) renames. Both are
therefore genuine, independently-confirmed misses in the CHANGES comment's
own enumeration, not just in PR #2743's original diff. Confirmed fixed in
`76a76c92`: `git grep -n '"role: \|skill: implementation\|skill: {skill}'
76a76c92 -- test/test_branch_role_field.py` shows all three lines now read
`"skill: implementation"`, and
`git show 76a76c92:test/test_convention_equivalence.py` line 438 now reads
`"Part of #1792.\n\nskill: product-discovery"`.

**Would the full-suite-diff method have found more had more existed?**
Judgment: yes — the method (run the full suite, diff the failing-test
*names* against `origin/main`) is exhaustive for this defect class by
construction. A stale trailer-text literal fails loudly as a named
`FAILED` line in pytest's own summary; there is no sampling or partial
coverage in that comparison. This session's own from-scratch full-suite
runs (section 6) reproduce an empty diff against `origin/main` in both
repos, which independently confirms nothing was left over for the method
to have missed a third time.

### 5 — Forward round-trip, driven live against PR-head code

canonical: this session's own executed script and subprocess calls, in a
fresh synthetic git workspace (`/tmp/rt2/work`, isolated via
`MUSTER_STATE_ROOT` so no real roster/state file was touched), against
real `76a76c92` and `ffaf0d9` code (not either PR's transcript):

1. `pipeline._write_skill_sidecar(work, 2741, "adversarial-review-selftest")`
   (real `76a76c92:pipeline.py` function) wrote
   `.on-the-record/role.json` as
   `{"skill": "adversarial-review-selftest", "issue": 2741}` — file content
   printed and inspected this session.
2. `roster.lease_key()` / `roster._roster_save()` / `roster._roster_load()`
   (real `76a76c92:roster.py` functions, `spawn` imported first so
   `roster._sp` is bound) round-tripped a roster entry shaped like
   `spawn.py`'s real early-roster-entry construction
   (`76a76c92:spawn.py:1067`, `"skill": skill` key); the reloaded entry's
   `"skill"` field equalled the written value — printed and asserted this
   session.
3. `board._format_roster_row()` (real `76a76c92:board.py` function)
   rendered `adversarial-review-selftest` correctly into the formatted `ps`
   row from that same roster entry — output
   `RUNNING        adversarial-review-selftest issue-2741  0분  pid 476430`
   captured this session.
4. The real `.on-the-record/role.json` from step 1 was fed to core's real
   `ffaf0d9:core/hooks/board-gate.sh` as an actual `bash` subprocess
   (`CLAUDE_SKILL=adversarial-review-selftest CLAUDE_PROJECT_DIR=/tmp/rt2/work
   bash <path> < <payload>`), against a synthetic workspace on branch
   `issue-2741/adversarial-review-selftest` with `docs/specs/approvers.md`
   and a fake `origin` remote so R1/R2 pass through to the sidecar check:
   exit code `0` (allow), empty stdout/stderr — no shape-mismatch
   diagnostic fired because the branch and sidecar agree.

### 6 — Cross-repo merge-order fail-open claim, constructed in both directions

canonical: `git show main:core/hooks/board-gate.sh` and
`git show ffaf0d9:core/hooks/board-gate.sh` extracted to two files this
session, each run as a real `bash` subprocess against the same synthetic
workspace from section 5, once per row, with the sidecar content written
directly by this session (no interpreter):

| scenario | gate version | sidecar shape | rc | diagnostic |
|---|---|---|---|---|
| on-the-record merged, core not | `main` (`.get("role")`) | new `{"skill":...}` | 0 | none (old gate has no diagnostic branch) |
| core merged, on-the-record not | `ffaf0d9` (`.get("skill")`) | old `{"role":...}` | 0 | `board-gate: .on-the-record/role.json present but not in the expected shape (skill: str, issue: int) -- falling back to branch-name parsing (issue #2741: ...)` |
| control: neither merged | `main` | old `{"role":...}` | 0 | none |
| control: both merged | `ffaf0d9` | new `{"skill":...}` | 0 | none |

derived: all four `rc=` values are this session's own captured `$?`
immediately after each of the four `bash <extracted-gate>` invocations,
run in sequence this session. All four allow (`rc=0`), confirming the
fail-open claim empirically in both merge-order directions plus both
controls. The second row also confirms live that core#353's new
shape-mismatch diagnostic (added on top of PR #2743's CHANGES-comment ask,
which only covered on-the-record's six hooks) actually fires exactly in
the merge-order gap it targets — the identical scenario against `main`'s
old gate (row 1, reversed asymmetry) stays silent because that code
predates the fix, which is expected and not a defect of `ffaf0d9`.

### 7 — `docs/` untouched, both repos

derived: `git diff --name-status main 76a76c92 -- docs/` (on-the-record)
shows three `A` (added) paths only — a record file, a hunt file, and a
deviation-log entry, all new — zero `M` against any pre-existing `docs/`
file. `git diff --name-status main ffaf0d9 -- docs/` (core) returns empty
— zero `docs/` changes at all.

### 8 — Failing-test sets vs `origin/main`, as sets of names, both repos, both suites

Ran `python3 -m pytest test/ tests/ -q -p no:cacheprovider` from scratch,
this session, in four fresh worktrees (on-the-record `main` and `76a76c92`;
core `main` and `ffaf0d9`):

- on-the-record `main`: `15 failed, 425 passed, 6 xfailed`.
- on-the-record `76a76c92`: `15 failed, 425 passed, 6 xfailed`.
- core `main`: `3 failed, 57 passed`.
- core `ffaf0d9`: `3 failed, 57 passed`.

derived: `diff <(grep '^FAILED' otr-main.log | sort) <(grep '^FAILED'
otr-2746.log | sort)` — empty (byte-identical 15-name sets). `diff
<(grep '^FAILED' core-main.log | sort) <(grep '^FAILED' core-353.log |
sort)` — empty (byte-identical 3-name sets). Both comparisons are over the
full `FAILED <test id>` name lines pytest itself printed, not the trailing
count line — behavior on current-format data is unchanged in both repos,
confirmed as sets of names rather than as counts that could coincidentally
match.

## Why

The task was to independently re-verify PR #2746 + core#353 against the
operator's scope-correction ruling on issue #2741, re-deriving each claim
from the repos directly (fresh worktrees, live subprocess runs, real
full-suite pytest runs) rather than trusting either PR's own transcript —
per this session's adversarial-review skill-verdict below, and because the
two prior verifications of PR #2743 had already split on exactly this kind
of claim (dict-key-in-a-`.py`-file vs. write-then-parse-back-key framing),
so re-deriving rather than restating was the only way to catch a repeat of
that failure shape.

skill-verdict: adversarial-review — applied: invoked; used the fresh
structurally-independent-evaluator stance (no shared context with either
PR's builder session) to re-derive every claim — write-site enumeration,
trailer/label round-trip, cross-repo fail-open matrix, test-literal
fixes, failing-test-set diffs — directly against repo/subprocess state
rather than accepting either PR's or the orchestrator's own characterization
of it.
other mounted skills: work-in-english — not invoked (session directive
states enforcement is the core hook only, no Skill-tool action needed).

## What did not work

None — every claim under independent re-derivation held (sections 1-8
above, all executed live this session). One framing disagreement is
recorded above (section 2, `gates/finding_shape.py:23`): I disagree with
the orchestrator's "in scope" characterization of that site, but the PR's
own choice to leave it untouched is, under my own reasoning, the correct
one — not a defect to route back.

## Upstream basis

- `76a76c92:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-bd0ced79.md`
  (sha `76a76c928e290bd2d28ed47850b8ae7cd94aa9f6`) — PR #2746's own record
  (on-the-record repo, PR head only, not present on this session's own
  branch), read for its claims list only — every claim was then
  independently re-derived, not restated, in sections 1-8 above.
- `ffaf0d90628309264ed17991104afeb63cc37bce` — tokenmaxxxer-core PR #353
  head, branch `issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a`.
- Issue #2741's scope-correction comment (2026-08-30) and PR #2743's
  CHANGES comment — both read via `gh issue view 2741 --comments` and
  `gh pr view 2743 --comments`, executed this session — as the ruling PR
  #2746 responds to.

## Open findings

None. canonical: sections 1-8 above are this session's own executed
re-derivation (fresh worktrees, live subprocess round-trips, live
full-suite pytest runs) of every claim in both PRs; all held, so there is
nothing open to route back to either PR.

## Next steps

acceptance: independent re-verification of PR #2746 + core#353 against
issue #2741's acceptance criteria — result: all three checks satisfied —
write-site enumeration re-derived and empty of remaining non-`docs/`
persisted `role` keys (section 1), forward round-trip demonstrated live
end-to-end through core's real hook (section 5), and failing-test sets
identical to `origin/main` as sets of names in both repos/both suites
(section 8). `loop_state: landed` — no further action needed from this
record.
