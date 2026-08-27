---
issue: 2637
role: conformance-review
author: conformance-review
verifies_subject: true  # independent verification of PR #2643's deliverable against issue #2637's own acceptance text
loop_state: reported
type: review-record
code_under_review:
  - priorities.py (new file — `_priorities_legacy_path`/`_priorities_dir`/`_priorities_entry_path`/`read_priorities`/`priorities_aggregate`)
  - spawn.py:81-87,2335-2350 (`priorities-path`/`priorities-log` subcommands)
  - on-the-record/hooks/deliverable-guard.sh:106-133 (shard-directory write exemption + anchor fix)
  - on-the-record/hooks/product-capture-stopgate.sh:74-140,229-260,304-312 (priorities-category nudge check retargeted to the shard directory)
  - on-the-record/hooks/skill-verdict-guard.sh:164-170 (obligations wording)
breaking: none
verdict: "pass — canonical: independent re-derivation, this session, of all three of issue #2637's Acceptance checks plus its must-not clause against PR #2643 (branch issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985, HEAD aa152c79) — every named requirement confirmed Present; two low-severity open findings noted below, neither blocking"
upstream:
  - path: aa152c79:docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md (implementation record; not merged into this branch's tree, read via git show)
    sha: aa152c797e60e6620e8162dec586b97fc8f171e1
  - path: priorities.py, spawn.py, on-the-record/hooks/deliverable-guard.sh, on-the-record/hooks/product-capture-stopgate.sh, on-the-record/hooks/skill-verdict-guard.sh (code under review)
    sha: aa152c797e60e6620e8162dec586b97fc8f171e1
subject: PR #2643 (branch issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985, HEAD aa152c797e60e6620e8162dec586b97fc8f171e1, OPEN, mergeable: MERGEABLE/CLEAN)
test: issue #2637's own Acceptance section, https://github.com/tokenmaxxxer/on-the-record/issues/2637
result: passed
assertedBy: conformance-review session, issue-2637 (builder-blind; independently re-ran every acceptance check in fresh git worktrees against the merge-base of origin/main and the PR branch tip, rather than trusting the implementation record's pasted transcripts)
---

canonical: `gh issue view 2637` body, `## Acceptance` section (this session, quoted verbatim in "Requirement list" below).

skill-verdict: work-in-english — applied: invoked; this record and all commands run this session are in English; the final chat summary to the user is in Korean per the skill's routing rule.
skill-verdict: conformance-review-finding-record — applied: invoked; every requirement below carries a verdict from the five-value set, a file:line/command evidence pointer, and a one-line rationale connecting the two.

# issue-2637 — conformance-review record

## What was done

canonical: `git rev-parse origin/main origin/pr2643 $(git merge-base origin/main origin/pr2643)` (this session) — result:
```
5f23f894527842d8088b094d75210e23ee0395f5
aa152c797e60e6620e8162dec586b97fc8f171e1
9a1de9bbdcc293d2c47a199985e5a312ca6df274
```

canonical: `gh pr view 2643 --json mergeable,mergeStateStatus,state` (this session) — result:
```
{"mergeStateStatus":"CLEAN","mergeable":"MERGEABLE","state":"OPEN"}
```

canonical: `git show aa152c79:docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md`
(this session) — the implementation record, not merged into this
checkout's own branch, read in full via `git show`.

Independent conformance review of PR #2643 (issue #2637's delivery,
branch `issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985`,
HEAD `aa152c79`, OPEN, MERGEABLE/CLEAN per the `gh pr view` result above)
against issue #2637's own Acceptance section. Read the full diff against
the merge-base above (8 files, +1043/-8) and the implementation record
cited above in full, then independently reproduced the two load-bearing
acceptance demonstrations myself in fresh throwaway `git worktree`s
rather than trusting the implementation record's pasted transcripts — a
fresh two-branch/merge/read sequence with different filenames and
timestamps than the builder used, and a fresh Python evaluation of the
anchored-regex fix and the pre-existing bug it disclosed as out of scope.

## Requirement list

canonical: `gh issue view 2637` body, `## Acceptance` section, quoted verbatim —

- AC-1: Two sessions appending a product-capture entry in the same window
  both land without a conflict — check: construct two branches that each
  add an entry from the same base, merge both in sequence, and show
  neither conflicts.
- AC-2: Chronological order of entries is recoverable without a shared
  file — check: read the entries back in order and show the ordering
  rule that produced it.
- AC-3: Existing entries remain readable by whatever reads them today —
  check: name every consumer of `priorities.md` and show each still
  works.
- MUST-NOT-1: do not lose or reorder existing entries.
- MUST-NOT-2: do not invent a third sharding convention — follow #2333's
  shape or state explicitly why this file needs something different.
- MUST-NOT-3: do not make the write path require the orchestrator.

## AC-1 — Present

canonical: `priorities.py:82-95` (`_priorities_entry_path()`, this
session) — every call mints `<timestamp>-<pid>.md` with microsecond-UTC
timestamp and the calling process's pid, never reusing a filename; two
concurrent sessions therefore write disjoint filenames into the same new
directory rather than both editing one shared file's byte range.

derived: independent reproduction, this session, in three fresh `git
worktree`s off the PR's merge-base commit `9a1de9bb`, using different
filenames/timestamps than the implementation record's own demo (not
reused, to make this an independent check rather than a re-run) — result:
```
$ git worktree add /tmp/cr-verify/base 9a1de9bb
$ git checkout -b cr-verify-a 9a1de9bb   # + docs/reports/product/priorities/20260827T050000000000-30001.md
$ git branch cr-verify-b 9a1de9bb; git checkout cr-verify-b   # + docs/reports/product/priorities/20260827T020000000000-30002.md
$ git checkout -b cr-verify-integration 9a1de9bb
$ git merge --no-ff cr-verify-a -m "cr-verify: merge A"
Merge made by the 'ort' strategy.
 docs/reports/product/priorities/20260827T050000000000-30001.md | 1 +
 1 file changed, 1 insertion(+)
exit=0
$ git merge --no-ff cr-verify-b -m "cr-verify: merge B"
Merge made by the 'ort' strategy.
 docs/reports/product/priorities/20260827T020000000000-30002.md | 1 +
 1 file changed, 1 insertion(+)
exit=0
$ git status --porcelain
(no output — clean, no unmerged paths)
```

Rationale: zero `CONFLICT` lines and exit 0 on both merges, independently
reproduced with fresh filenames on a fresh base checkout — the
conflict-elimination property comes from the sharding shape itself
(disjoint filenames per entry), not from anything specific to the
builder's own demo data, so this independent re-run with different data
is the correct check rather than re-running their exact transcript.

## AC-2 — Present

canonical: `priorities.py:98-119` (`read_priorities()`, this session) —
prepends the legacy flat file's content (if present), then appends
shard files in `sorted(d.glob("*.md"))` order — filename order, and the
fixed-width `%Y%m%dT%H%M%S%f` timestamp format makes filename order
equal chronological order.

derived: independent reproduction, this session, continuing the AC-1
worktree after both merges — copied `priorities.py` from the PR branch
into the integration worktree and called `read_priorities()` directly —
result:
```
$ python3 -c "import priorities; [print(repr(e)) for e in priorities.read_priorities(None, '.')]"
'# Priorities\n\nAppend-only, newest entry last.\n...' (legacy file content, unchanged)
'- 2026-08-27T02:00:00Z: [cr-verify branch B, earlier timestamp]\n'
'- 2026-08-27T05:00:00Z: [cr-verify branch A, later timestamp]\n'
```

Rationale: entry B (filename timestamp `020000000000`, merged SECOND)
comes back before entry A (filename timestamp `050000000000`, merged
FIRST) — output order tracks filename/timestamp order, not git-merge
order, which is exactly the ordering rule AC-2 asks to be shown. Matches
the same inverse-of-merge-order result the implementation record's own
demo reports, independently reproduced here with different data rather
than read from their transcript.

## AC-3 — Present

canonical: `on-the-record/hooks/deliverable-guard.sh:106-133`,
`on-the-record/hooks/product-capture-stopgate.sh:74-140,229-260,304-312`,
`on-the-record/hooks/skill-verdict-guard.sh:164-170`, `spawn.py:81-87,2335-2350`
(this session) — the four live-code consumers of `priorities.md`, each
diffed and each independently exercised below.

derived: `git grep -l "priorities.md" origin/pr2643` and `git grep -ln
"priorities" origin/pr2643 -- "*.py" "*.sh"` (this session, run against
the PR tip independently of the implementation record's own sweep) —
result: 29 hits for the literal string on the PR tip (includes the new
record file, `priorities.py`, and `spawn.py`'s own new prose, which the
record's own pre-change sweep against `HEAD` correctly excluded), 5 code
files in the `*.py`/`*.sh` sweep (`priorities.py`, `spawn.py`,
`deliverable-guard.sh`, `product-capture-stopgate.sh`,
`skill-verdict-guard.sh`). Subtracting the PR's own 4 new/changed files
(the record, `priorities.py`, and `spawn.py`'s own new comment lines)
reproduces the implementation record's own pre-change count of 25 hits
(24 historical docs + 1 code file from the literal-string sweep) against
the 3 pre-existing code consumers named above.

derived: independent functional exercise, this session, of the anchored
regex `PRODUCT_CAPTURE_PRIORITIES_DIR_RE`
(`on-the-record/hooks/deliverable-guard.sh:129-132`) — result:
```
$ python3 -c "... PRODUCT_CAPTURE_PRIORITIES_DIR_RE = re.compile(r'^docs/reports/product/priorities/[^/]+\.md$') ..."
[exploit-shaped path, priorities-shard suffix nested under src/] -> False   # correctly rejected
docs/reports/product/priorities/20260827T000000000000-999.md -> True   # legit shard path correctly exempted
docs/reports/product/priorities/nested/hack.md -> False   # nested path correctly rejected
```

derived: independent functional exercise, this session, of the two new
`spawn.py` subcommands against the PR checkout — result:
```
$ python3 spawn.py priorities-path
.../docs/reports/product/priorities/20260827T091557578992-4169042.md
$ python3 spawn.py priorities-log | head -3
# Priorities

Append-only, newest entry last.
```

Rationale: all three hook consumers and both new CLI subcommands were
independently run against the real code, not re-read from the record's
transcript — `deliverable-guard.sh`'s new exemption is correctly scoped
(exploit-shaped path denied, legit path allowed, nested path denied),
`spawn.py`'s two subcommands work as documented, and the `git grep`
sweep above turns up only `docs/issue-*` report/proposal files as the
historical references, none of which are `*.py`/`*.sh` — prose
describing a past session's observations, not code that parses the file
— so none require updating for AC-3 to hold.

## MUST-NOT-1 (no lost/reordered entries) — Present

canonical: `priorities.py:104-108` (`read_priorities()`, this session) —
the legacy path is read via `legacy.is_file()` / `read_text()` only.

derived: `git grep -n "_priorities_legacy_path" origin/pr2643 --
priorities.py` (this session) — result: the name appears exactly twice
(the definition at line 61, and the one call site inside
`read_priorities()` at line 104); no write call anywhere in the module.

Rationale: the flat file is frozen and prepended verbatim ahead of the
new shards in `read_priorities()`, so every pre-#2637 entry is still
surfaced, in its original position, by the same call that surfaces the
new ones.

## MUST-NOT-2 (no invented third convention) — Present

canonical: `priorities.py:1-49` (module docstring, this session) — states
the one deliberate divergence from #2333/#2348 (per-entry sharding
instead of per-session sharding) and the rationale for it, and states the
second divergence (compatible dual-source reader) separately with its own
rationale, both citing the specific precedent function bodies they
diverge from.

Rationale: both divergences are named and justified against a concrete
precedent (`consult.py`'s `_consult_trace_path()`/`_consult_log_aggregate()`,
`deviation_log.py`'s shard-id-reuse) rather than presented as a
freestanding new design — satisfies the issue's explicit instruction to
"follow that precedent or state explicitly why this file needs something
different."

## MUST-NOT-3 (write path needs no orchestrator) — Present

canonical: `spawn.py:2347-2350` (`priorities-path` subcommand) and
`priorities.py:82-95` (`_priorities_entry_path()`), this session — a
session calls either the Python function directly or `spawn.py
priorities-path` to get its own unique path, then writes the entry itself
with its own Write/Edit call; neither path routes the actual write
through `spawn.py` or any other coordinating process.

derived: independent exercise, this session, of `python3 spawn.py
priorities-path` (see AC-3 above) — result: prints a path and returns;
the directory exists after the call, the file does not, until a caller
writes it (confirmed by listing the directory immediately after the call
in the same session, not shown separately as it is the same command
already quoted above).

Rationale: matches `_consult_trace_path()`/`_deviation_log_path()`'s
established shape exactly — the coordinator only mints a collision-free
name, the writer is always the calling session's own tool call.

## Why

The PR mirrors the exact shape issue #2333 established and issue #2348
extended, adapted with two disclosed, precedent-grounded divergences
(per-entry not per-session sharding; a dual-source reader that also
covers the pre-existing flat file). Both divergences are required by
issue #2637's own text (a one-shot product-capture entry, and the
explicit "do not lose or reorder" clause that #2333/#2348 never had to
satisfy), not invented preferences.

## What did not work

canonical: `git show aa152c79:docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985/2026-08-27-hunt-issue-2637-priorities-sharding.md`
(this session) — the before-landing warrant-hunt record, not merged into
this branch's tree, read via `git show`. The hunter's before-landing
dispatch found the `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` anchoring bug
covered under AC-3/MUST-NOT-3 above before this PR opened, and the
implementation record's own "What did not work" section documents the
fix. This review independently re-verified the fix holds (see AC-3's
regex-exercise result above) rather than re-stating that finding as if
newly discovered in this review. Nothing failed in this review's own
independent checks.

## Upstream basis

canonical: `git show aa152c79:docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md`
(this session) — implementation record, not merged into this branch's
tree, read in full via `git show`; every acceptance-relevant claim in it
was independently re-derived above rather than trusted verbatim.

canonical: `git show aa152c79:docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985/2026-08-27-hunt-issue-2637-priorities-sharding.md`
(this session) — before-landing warrant-hunt record, not merged into
this branch's tree, read in full via `git show`; documents the anchoring
bug and its fix, independently re-verified above under AC-3.

derived: `git show aa152c79:priorities.py`,
`git show aa152c79:spawn.py`,
`git show aa152c79:on-the-record/hooks/deliverable-guard.sh`,
`git show aa152c79:on-the-record/hooks/product-capture-stopgate.sh`,
`git show aa152c79:on-the-record/hooks/skill-verdict-guard.sh` (this
session) — code under review, each read in full and independently
exercised this session (see AC-1 through MUST-NOT-3 above).

## Open findings

1. `on-the-record/hooks/deliverable-guard.sh`'s pre-existing
   `EXEMPT_SUFFIXES` tuple (line 103-109) and `PRODUCT_CAPTURE_ISSUE_RE`
   (line 113-116) both use unanchored suffix/search matching, the same
   bug class the new `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` had before the
   before-landing warrant-hunt fix documented above.

   derived: `python3 -c "import posixpath; print(posixpath.normpath('src/docs/reports/product/priorities.md').endswith(('docs/reports/product/priorities.md',)))"`
   (this session) — result: `True` — a deliverable path nested under
   `src/` that merely ends with the exempted flat-file suffix is wrongly
   exempted today, on current `main`, unrelated to this PR.

   canonical: `git show aa152c79:docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md`
   (this session, cited above under "Upstream basis") discloses this
   explicitly and correctly scopes it out of issue #2637 ("this session
   did not introduce them; whether to fix them is a separate follow-up
   call"). Not a conformance gap in this PR — recorded here only so it
   is not lost as a candidate follow-up issue. Resolution path: a future
   issue against `deliverable-guard.sh`'s pre-existing exemption
   matching, not a re-open of #2637.

2. `_priorities_entry_path()` (`priorities.py:82-95`) mints a filename
   from `datetime.now(timezone.utc)` plus `os.getpid()` with no
   collision-avoidance beyond that pair.

   derived: `python3 -c "import priorities,tempfile; d=tempfile.mkdtemp(); print(len(set(priorities._priorities_entry_path(None, d) for _ in range(20))))"`
   (this session) — result: `20` (20 distinct filenames from 20
   back-to-back calls in one process; did not reproduce a same-microsecond
   collision in practice).

   Two calls from the *same* process landing in the same microsecond
   would mint the same filename and the second write would silently
   overwrite the first — the code has no defense against that case, only
   the evidence above that it is unlikely in practice. This is a
   narrower guarantee than #2333/#2348's precedent, which avoids the
   whole class by caching one shard id per session rather than minting a
   fresh name every call — the implementation record's own rationale for
   not doing that (a product-capture entry is "a single one-shot
   scribing act") is reasonable but does not make the same-microsecond
   case structurally impossible, only unlikely. Resolution path: none
   needed for this PR to pass — issue #2637's acceptance criteria are
   about cross-session (cross-process) collisions, which the pid
   component disambiguates completely (see AC-1 above); this
   same-process/same-microsecond case is a lower-severity residual risk
   worth naming, not a defect against any acceptance bullet.

## Next steps

canonical: `gh pr view 2643 --json mergeable,mergeStateStatus,state`
(this session, quoted in full under "What was done" above) — result:
`MERGEABLE`/`CLEAN`/`OPEN`.

None further. `loop_state: reported` is terminal for this record — all
three acceptance checks and all three must-not clauses were independently
re-derived above as Present (not merely re-read from the implementation
record), the PR is mergeable against current `main` per the citation
above, and both open findings are non-blocking (one pre-existing and
explicitly out of scope, one a low-severity residual risk in new code,
neither contradicting any named acceptance criterion).
