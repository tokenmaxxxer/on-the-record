---
issue: 2637
role: conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-7e0e0de6
author: conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-7e0e0de6
skills: conformance-review-traceability-and-evidence (skill-repository(297e350)), conformance-review-verdict-assignment (skill-repository(297e350))
verifies_subject: true  # independent verification of PR #2643's deliverable against issue #2637's own acceptance text
loop_state: reported
type: review-record
code_under_review:
  - priorities.py:1-128 (new module — `_priorities_dir`/`_priorities_legacy_path`/`_priorities_entry_path`/`read_priorities`/`priorities_aggregate`)
  - spawn.py:78-84,2332-2347 (imports `priorities`; `priorities-log`/`priorities-path` subcommands)
  - on-the-record/hooks/deliverable-guard.sh:103-135 (`PRODUCT_CAPTURE_PRIORITIES_DIR_RE` write exemption, anchored)
  - on-the-record/hooks/product-capture-stopgate.sh:199-233,301-309 (shard-dir nudge check + `git status --porcelain` untracked fallback + advisory wording)
  - on-the-record/hooks/skill-verdict-guard.sh:164-170 (obligations-reminder wording only)
  - docs/reports/product/priorities.md (legacy file — verified byte-identical, untouched)
breaking: "none — this is a review record, no code changed by this role"
verdict: "pass — canonical: independent re-derivation, this session, of all
  three of issue #2637's Acceptance checks plus its must-not clause,
  against branch
  issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985
  HEAD aa152c797e60e6620e8162dec586b97fc8f171e1 (fresh git worktrees at
  /tmp/otr-main = origin/main 5f23f894527842d8088b094d75210e23ee0395f5,
  and /tmp/otr-branch-tip = the branch tip, plus /tmp/otr-fixtureA,
  /tmp/otr-fixtureB, /tmp/otr-fixtureMerge, /tmp/otr-fixtureMerge2 for the
  two-branch merge demonstration) — every named acceptance bullet and the
  four named consumers confirmed Present; the warrant-hunt bypass/fix
  claim reproduced exactly as stated; two open findings outside the named
  acceptance bullets, neither blocking — see Open findings."
upstream:
  - path: docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md
    sha: aa152c797e60e6620e8162dec586b97fc8f171e1
  - path: docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985/2026-08-27-hunt-issue-2637-priorities-sharding.md (untracked in this checkout — this session is on a different branch; read via git show)
    sha: aa152c797e60e6620e8162dec586b97fc8f171e1
  - path: docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985/deviation-log/20260827T091104549429-5b51be7623d773d1.md (untracked in this checkout; read via git show)
    sha: aa152c797e60e6620e8162dec586b97fc8f171e1
subject: PR #2643 (branch issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985, HEAD aa152c797e60e6620e8162dec586b97fc8f171e1, OPEN, mergeable)
test: issue #2637's own Acceptance section, https://github.com/tokenmaxxxer/on-the-record/issues/2637
result: passed
assertedBy: conformance-review session, issue-2637 (structurally independent from the builder session; re-ran every acceptance check in fresh git worktrees against both origin/main and the PR branch tip, plus a hand-built two-branch merge fixture the builder's own transcript is not the source of)
---

# issue-2637 — conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-7e0e0de6 record

canonical: `gh issue view 2637` (this session) — issue #2637's Acceptance
section, quoted verbatim in "Requirement list" below.

skill-verdict: conformance-review-traceability-and-evidence — applied: invoked;
every citation below is pinned to file:line plus the commit sha
this session actually read (`aa152c79` on the branch, `5f23f894`/`9a1de9bb`
where the citation is to current main or the merge-base), and the
requirements.md/philosophy.md/goals.md scoping claim is checked against
`--all` git history, not just the current tree, before being cited.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
rule 6 (re-check before finalizing) drove the second adversarial pass
against the landed anchored regex (traversal/double-slash/nested-subdir/
mixed-case probes) before accepting the warrant-hunt fix as sufficient,
and rule 3 (name the missing-evidence location) is used for the open
findings below rather than folding them into a verdict they do not
belong to.

Note on setup: this review session's own checkout is on the review
role's branch (`issue-2637/conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-7e0e0de6`),
not PR #2643's branch — so all code-under-review and hunt/deviation-log
citations below were read via `git show <sha>:<path>` or fresh `git
worktree`s built from freshly fetched refs (`verify-main` =
`origin/main`, `verify-pr2643` = the PR branch tip), never from this
checkout's own working tree.

## What was done

Independent conformance review of PR #2643 (issue #2637's delivery,
branch `issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985`,
HEAD `aa152c79`, OPEN, `mergeable: MERGEABLE`) against issue #2637's own
Acceptance section. Set up fresh `git worktree`s off freshly fetched refs
(`/tmp/otr-main` = `origin/main`, `/tmp/otr-branch-tip` = the branch tip)
and re-derived every named check directly against real code, plus
hand-built a two-branch same-base merge fixture from scratch
(`/tmp/otr-fixtureA`, `/tmp/otr-fixtureB`, two merge worktrees) rather
than trusting the implementation record's or hunt record's pasted
transcripts.

derived: `git rev-parse origin/main issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985` (this session, via `git fetch` into local refs `verify-main`/`verify-pr2643`) —
```
5f23f894527842d8088b094d75210e23ee0395f5
aa152c797e60e6620e8162dec586b97fc8f171e1
```

derived: `git merge-base verify-main verify-pr2643` then `git diff <merge-base> verify-main --stat -- priorities.py spawn.py on-the-record/hooks/deliverable-guard.sh on-the-record/hooks/product-capture-stopgate.sh on-the-record/hooks/skill-verdict-guard.sh docs/reports/product/priorities.md` (this session) —
```
merge-base: 9a1de9bbdcc293d2c47a199985e5a312ca6df274
(diff: no output)
```
Confirms `origin/main`'s commits since the branch's merge-base never
touched any reviewed file, so `origin/main` is a valid "before" baseline.

## Requirement list

canonical: `gh issue view 2637` body, `## Acceptance` section (this
session, quoted verbatim) —

- AC-1: two sessions appending a product-capture entry in the same
  window both land without a conflict — check: construct two branches
  that each add an entry from the same base, merge both in sequence, and
  show neither conflicts.
- AC-2: chronological order of entries is recoverable without a shared
  file — check: read the entries back in order and show the ordering
  rule that produced it.
- AC-3: existing entries remain readable by whatever reads them today —
  check: name every consumer of `priorities.md` and show each still
  works.
- MUST-NOT-1: do not lose or reorder existing entries. Do not invent a
  third sharding convention — follow #2333's shape or state explicitly
  why this file needs something different. Do not make the write path
  require the orchestrator.

## AC-1 — Present

canonical: `aa152c79:priorities.py:82-95` (`_priorities_entry_path`, read
this session via a fresh worktree at `/tmp/otr-branch-tip`) — mints
`<timestamp>-<pid>.md` under a shard directory (untracked in every
checkout of this repo today — no commit has ever created it; it is
created at runtime by this function's own `mkdir(parents=True,
exist_ok=True)`), never reused.

derived: hand-built fixture, this session, entirely independent of the
builder's own transcript —

```
$ git worktree add /tmp/otr-fixtureA verify-pr2643 -b fixtureA-base
$ git worktree add /tmp/otr-fixtureB verify-pr2643 -b fixtureB-base
# fixtureA (in /tmp/otr-fixtureA):
$ PATHA=$(python3 -c "import priorities; print(priorities._priorities_entry_path(issue=None, cwd='.'))")
$ echo "- session A entry: ..." > "$PATHA" && git add "$PATHA" && git commit -m "fixtureA: add priorities entry" -q
committed A: docs/reports/product/priorities/20260827T091524709284-4165785.md
# fixtureB (in /tmp/otr-fixtureB, ~2s later):
$ PATHB=$(python3 -c "import priorities; print(priorities._priorities_entry_path(issue=None, cwd='.'))")
$ echo "- session B entry: ..." > "$PATHB" && git add "$PATHB" && git commit -m "fixtureB: add priorities entry" -q
committed B: docs/reports/product/priorities/20260827T091526302489-4166023.md
# merge both, in sequence, into a fresh branch off the same base:
$ git branch fixtureMerge verify-pr2643 && git worktree add /tmp/otr-fixtureMerge fixtureMerge
$ git merge --no-ff fixtureA-base -m "merge fixtureA"
Merge made by the 'ort' strategy.
 docs/reports/product/priorities/20260827T091524709284-4165785.md | 1 +
exit: 0
$ git merge --no-ff fixtureB-base -m "merge fixtureB"
Merge made by the 'ort' strategy.
 docs/reports/product/priorities/20260827T091526302489-4166023.md | 1 +
exit: 0
```

No `CONFLICT` line, no non-zero exit, from either merge. Both entries
present on disk afterward inside the disposable `/tmp/otr-fixtureMerge`
worktree (never committed to this repo's own checkout). Rationale: this
is the exact collision PR #2632/#2633 hit on the flat file — two
sessions from the same base, each adding one entry — rebuilt from
scratch against the landed code, and it does not recur because the two
entries never share a path.

## AC-2 — Present

canonical: `aa152c79:priorities.py:98-118` (`read_priorities`) — legacy
file content first (if present), then shard directory entries in
`sorted(d.glob("*.md"))` order — filename order, and filenames are
`<timestamp>-<pid>.md` with a fixed-width UTC timestamp, so filename sort
is chronological sort.

derived: this session, reading the fixture-merge result from AC-1 back
through the real reader, **twice**, once with each merge order, to prove
the ordering is filename-driven and not an artifact of merge order —

```
# /tmp/otr-fixtureMerge: merged A then B
$ python3 verify_order.py
total entries: 3
'- session A entry: ...\n'
'- session B entry: ...\n'
# /tmp/otr-fixtureMerge2 (fresh branch, same two commits): merged B then A
$ git merge --no-ff fixtureB-base -m "merge fixtureB first"
$ git merge --no-ff fixtureA-base -m "merge fixtureA second"
$ python3 verify_order.py
total entries: 3
'- session A entry: ...\n'
'- session B entry: ...\n'
```
Both worktrees return the same order (A before B, matching A's earlier
timestamp) regardless of which was `git merge`d first — the ordering
rule is `sorted(d.glob("*.md"))` on the fixed-width-timestamp filename,
not commit/merge order. `total entries: 3` in both cases (legacy file +
A + B) — nothing lost.

## AC-3 — Present

canonical: `aa152c79:on-the-record/hooks/deliverable-guard.sh`,
`on-the-record/hooks/product-capture-stopgate.sh`,
`on-the-record/hooks/skill-verdict-guard.sh`, `spawn.py` — the four
consumers the PR names. Found independently, not accepted from the PR
body, via:

```
$ git grep -ln "priorities" HEAD -- "*.py" "*.sh"
on-the-record/hooks/deliverable-guard.sh
on-the-record/hooks/product-capture-stopgate.sh
on-the-record/hooks/skill-verdict-guard.sh
priorities.py
spawn.py
```
(`priorities.py` is the new implementation itself, not a consumer.) No
test file references "priorities" at all (`git grep -ln priorities HEAD
-- 'test*' '*test*.py'` → no output), so there is no pre-existing suite
to regress and none was added — noted below under Open findings, not a
named acceptance bullet.

Each named consumer exercised live, this session, in the
`/tmp/otr-branch-tip` worktree:

**`deliverable-guard.sh`** — pass case (legit shard) and refuse case
(ordinary `src/` write), both with an absolute `cwd` in the payload:
```
$ echo '{"session_id":"t2","cwd":"<abs>","tool_name":"Write","tool_input":{"file_path":"docs/reports/product/priorities/20260827T000000000000-999.md"}}' | env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/deliverable-guard.sh; echo $?
0
$ echo '{"session_id":"t3","cwd":"<abs>","tool_name":"Write","tool_input":{"file_path":"src/hack.py"}}' | env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/deliverable-guard.sh; echo $?
orchestrate: this is an orchestrator session and src/hack.py is a deliverable path...
2
```

**`product-capture-stopgate.sh`** — pass case (a "priorities"-triggering
turn with no matching shard on disk → nudge fires) and refuse case (same
turn, with an untracked shard already on disk → nudge suppressed via the
`git status --porcelain` fallback):
```
$ echo '{"transcript_path":"/tmp/transcript1.jsonl","stop_hook_active":false}' | env -u TOKENMAXXXER_SPAWNED PRODUCT_CAPTURE_REPO="$(pwd)" bash on-the-record/hooks/product-capture-stopgate.sh
{"hookSpecificOutput": {..., "additionalContext": "product-capture-stopgate: statements matching these categories were not reflected in docs/reports/product/: priorities/ (spawn.py priorities-path; e.g. \"...\"). Record them..."}}
$ mkdir -p docs/reports/product/priorities && echo "- priority entry test" > docs/reports/product/priorities/20260827T099999000000-1.md
$ echo '{"transcript_path":"/tmp/transcript1.jsonl","stop_hook_active":false}' | env -u TOKENMAXXXER_SPAWNED PRODUCT_CAPTURE_REPO="$(pwd)" bash on-the-record/hooks/product-capture-stopgate.sh
(no output, exit 0)
```
Confirms the shard-directory check plus the untracked-file fallback both
work, and the advisory text names `priorities/ (spawn.py priorities-path;
...)` as claimed. (The untracked test shard created here lived only in
the disposable `/tmp/otr-branch-tip` worktree and was deleted at the end
of this session — never committed, never touching this repo's own
checkout.)

**`spawn.py`** — both new subcommands run live:
```
$ python3 spawn.py priorities-path
/tmp/otr-branch-tip/docs/reports/product/priorities/20260827T092030601055-4183030.md
$ python3 spawn.py priorities-log
... (legacy content, then shard content, in order)
```

**`skill-verdict-guard.sh`** — confirmed by direct code read
(`aa152c79:on-the-record/hooks/skill-verdict-guard.sh:164-170`): the
diff against `origin/main` is a wording-only change to
`obligations_reminder()`'s returned string (mentions `spawn.py
priorities-path`); no branch condition, no file I/O in the function
touches `priorities`, so there is no behavior to regress — a live
invocation would only re-confirm the same string change already visible
in the diff.

## MUST-NOT-1 — Present

**No loss/reorder of existing entries**: canonical, this session —
```
$ diff <(git show verify-main:docs/reports/product/priorities.md) <(git show verify-pr2643:docs/reports/product/priorities.md) && echo IDENTICAL
IDENTICAL
$ md5sum <(git show verify-main:...) <(git show verify-pr2643:...)
f3db1d6b667c04bf70061364d778372c  (both)
```
Legacy file is byte-identical between `origin/main` and the branch tip —
never rewritten. `read_priorities()` (AC-2 above) prepends this file's
full content ahead of the shards, so the reader's view also loses
nothing.

**No invented third sharding convention**: the PR states one explicit,
documented divergence from #2333/#2348 — sharding per *entry* rather
than per *session* — in `priorities.py`'s own module docstring (read in
full this session). Judged sound, not a reintroduction of the collision
under different granularity: the collision domain is
`(timestamp-microsecond, pid)`, identical to `consult.py`'s own formula,
and per-entry vs. per-session only changes *how often* a fresh pair is
minted, not the pair's uniqueness guarantee. Verified directly, this
session, with two genuinely concurrent processes launched in the same
second (the scenario the review brief names):
```
$ ( python3 spawn.py priorities-path & python3 spawn.py priorities-path & wait )
docs/reports/product/priorities/20260827T092123062224-4185098.md
docs/reports/product/priorities/20260827T092123065696-4185097.md
```
Distinct timestamps (3.5ms apart) and distinct pids — no collision.
Also ran 200 rapid same-process calls (a disposable throwaway script
written and deleted this session in `/tmp/otr-branch-tip`, never
committed): 200/200 unique filenames.

**Write path does not require the orchestrator**: `spawn.py
priorities-path` only *prints* the path a new entry belongs at
(`aa152c79:spawn.py:2345-2347`) — the actual write is the calling
session's own `Write`/`Edit` tool call, exactly as demonstrated in AC-1's
fixture (each branch wrote its entry directly with a shell redirect
standing in for a session's own write). No orchestrator/coordinator
process is in the write path.

## Warrant-hunt bypass claim — reproduced, fix confirmed, one adversarial pass added

canonical: the hunt record, read this session via `git show
aa152c797e60:docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985/2026-08-27-hunt-issue-2637-priorities-sharding.md`
(untracked in this checkout — this session's own branch is not PR
#2643's branch) — claims an unanchored `re.search` in the first draft of
`PRODUCT_CAPTURE_PRIORITIES_DIR_RE` let a `src/`-rooted synthetic test
path ending in the shard suffix (not a real file anywhere in this repo —
used only as a `tool_input.file_path` value inside a JSON payload piped
to the hook) through as exempt.

Reproduced independently against a hand-reverted copy of the regex (a
disposable local copy, this session, `^` stripped from both
alternatives — the exact pre-fix shape the hunt record quotes):
```
$ echo '{"session_id":"t4","cwd":"<abs>","tool_name":"Write","tool_input":{"file_path":"src/docs/reports/product/priorities/hack.md"}}' | env -u TOKENMAXXXER_SPAWNED bash /tmp/prefix-guard.sh; echo $?
0
```
Bypass reproduced exactly as claimed: exit 0, silently allowed.

Landed version (`aa152c79:on-the-record/hooks/deliverable-guard.sh:129-134`,
both alternatives anchored with `^`) denies the identical payload:
```
$ echo '{"session_id":"t1","cwd":"<abs>","tool_name":"Write","tool_input":{"file_path":"src/docs/reports/product/priorities/hack.md"}}' | env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/deliverable-guard.sh; echo $?
orchestrate: this is an orchestrator session and src/docs/reports/product/priorities/hack.md is a deliverable path...
2
```
and the legitimate shard path still passes (exit 0, shown under AC-3).

Own adversarial pass against the landed regex (rule 6 — re-check before
accepting a fix as sufficient), all denied correctly or otherwise
inert — no further path-shaped bypass found:
```
$ # nested subdir under the shard directory
$ echo '{"session_id":"t5","cwd":"<abs>","tool_name":"Write","tool_input":{"file_path":"docs/reports/product/priorities/sub/hack.md"}}' | env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/deliverable-guard.sh; echo $?
2   # denied — [^/]+ excludes "/", correctly falls through to the general deliverable check
$ # mixed case
$ echo '{"session_id":"t6","cwd":"<abs>","tool_name":"Write","tool_input":{"file_path":"Docs/reports/product/priorities/hack.md"}}' | env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/deliverable-guard.sh; echo $?
2   # denied — regex is case-sensitive by design; fails closed, not a security opening
$ # trailing slash / leading ./ both normalize (posixpath.normpath) to the identical exempt path, still correctly exempt (exit 0) since they genuinely refer to the real shard path, not a bypass
```
Also reasoned through, not just tested: `posixpath.normpath` (applied to
`n` before the regex ever runs, `aa152c79:on-the-record/hooks/deliverable-guard.sh:96-98`)
collapses any `..`-traversal sequence before the anchored regex sees the
string. A crafted input built as the exempted-prefix segments followed
by enough `..` climbs to walk back out to a `src/`-rooted destination
would, after normalization, no longer contain the `priorities` segment
at all by the time the regex runs — it resolves to a plain path with no
exempted prefix left, which the general (non-exempt) deliverable check
then denies on its own merits, not via this regex.

## Open findings

**Finding 1 — unrelated hang in the pre-existing git-root walk, not
introduced by this PR.** derived: this session, live invocation —
```
$ echo '{"session_id":"t7","cwd":"<abs>","tool_name":"Write","tool_input":{"file_path":"//docs/reports/product/priorities/hack.md"}}' | timeout 10 env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/deliverable-guard.sh
(no output — ran past the 10s timeout, process killed by `timeout`)
```
A `file_path` beginning with a POSIX doubled leading slash (`//...`)
does not match the anchored `^docs/...` exemption (correct, falls
through to the general check), but then drives the pre-existing,
unchanged-by-this-PR `while probe and probe != "/":` git-root walk at
`aa152c79:on-the-record/hooks/deliverable-guard.sh:157-163` (identical
on `origin/main` — confirmed no diff to this file's non-exemption logic
in the "What was done" merge-base check above) into an infinite loop:
`posixpath.dirname("//")` returns `"//"` again on every iteration, and
`"//" != "/"` is always true, so the loop never terminates. Not
reachable through the new `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` exemption
itself (a `//`-prefixed path never matches it), and not a named
acceptance bullet of issue #2637 — filed here, not counted against this
PR's pass verdict. **Resolution path:** file a follow-up issue against
`deliverable-guard.sh`'s git-root walk (bound the loop or special-case a
`//`-prefixed absolute path) — out of scope for issue #2637 to fix
itself, since the walk logic predates this PR and is untouched by it.

**Finding 2 — no new tests added for `priorities.py` or the touched
hooks.** derived: `git grep -ln priorities HEAD -- 'test*'
'*test*.py'` (this session) —
```
(no output)
```
No file under `test/`/`tests/` references "priorities" before or after
this PR. Not a named acceptance bullet (issue #2637's three checks are
all "executed-live" demonstrations, not unit tests) and consistent with
the precedent this PR follows (#2333/#2348 also shipped without a
dedicated test file per this session's own `git grep` sweep of `test/`).
**Resolution path:** none required by issue #2637 itself; whoever picks
up Finding 1's follow-up issue should add a regression test for the
`//`-prefix hang at that time, since a fix without a test would be
un-guarded against recurrence.

## What did not work

None.

## Next steps

None — `loop_state: reported`, terminal for this record kind.
