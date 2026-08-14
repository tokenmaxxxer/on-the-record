---
code_under_review: HEAD
loop_state: verdict-issued
---

# Conformance review of issue #323's landed conflict methodology

kind: record
upstream: docs/issue-323/proposals/conformance-review.md
code_under_review:
- docs/specs/parallel-conflict-methodology.md
- scripts/check-write-set-conflicts.sh
- tests/check-write-set-conflicts.test.sh
- docs/handbooks/operations.md
- docs/issue-323/reports/implementation.md

## What was done

canonical: docs/issue-323/reports/implementation.md work-log and
closed-checks sections, read this session. Every claim there was
re-run live this session against the working tree and against commit
c9474d58 (the phase-2 delivery commit), rather than taken from the
record's prose alone.

## Why

Issue #323 was spawned for conformance review by `spawn_on_pr.py` on
PR #344's creation (issue #323 body, read this session: "PR 생성 시
자동 스폰됨 (spawn_on_pr.py)"); this role's spec requires an
implementation record's own claims be independently re-run, not
accepted at face value.

## Per-requirement verdicts

### Req 1 — spec.md states the methodology — Present

`derived: ls docs/specs/parallel-conflict-methodology.md`, run this
session:
```
docs/specs/parallel-conflict-methodology.md
```
canonical: `docs/specs/parallel-conflict-methodology.md` lines 63-70,
read this session — states claim source, liveness signal, overlap
detection, and the `unknown`-bucket ratio.

### Req 2 — checker script valid, anchoring fix applied — Present

`derived: bash -n scripts/check-write-set-conflicts.sh`, run this
session:
```
(no output)
```
canonical: `scripts/check-write-set-conflicts.sh` lines 61-62, read
this session:
```
  [ -f "$record_a" ] && grep -qE "issue #${issue_b}([^0-9]|\$)|issue-${issue_b}([^0-9]|\$)" "$record_a" && return 0
  [ -f "$record_b" ] && grep -qE "issue #${issue_a}([^0-9]|\$)|issue-${issue_a}([^0-9]|\$)" "$record_b" && return 0
```
This text matches the implementation record's "What did not work" fix
verbatim: the pattern is anchored with `([^0-9]|$)` so a
digit-substring false match cannot recur.

### Req 3 — parser is reusably sourceable via `--source-only` — Present

`derived: bash -c 'source scripts/check-write-set-conflicts.sh --source-only && type parse_files_frontmatter'`,
run this session:
```
parse_files_frontmatter은(는) 함수임
parse_files_frontmatter ()
{
    local proposal_file="$1";
    awk '
...
```
canonical: same command output, this session — the function loaded and
no `main`/conflict-check side effect ran, satisfying the binding
conditional-approval feedback's reusable-parser requirement.

### Req 4 — test suite behavior — Present, path relocated by an unrelated later commit

`derived: bash tests/check-write-set-conflicts.test.sh`, run this
session:
```
PASS: unresolved overlap detected
PASS: resolved overlap passes
ALL TESTS PASSED
```
canonical: same command output, this session — both fixtures the
implementation record describes (unresolved-overlap non-zero exit,
resolved-overlap zero exit) behave as recorded.

`derived: git log --oneline --all -- scripts/check-write-set-conflicts.sh tests/check-write-set-conflicts.test.sh`,
run this session:
```
c79d034d refactor(issue-729): consolidate test/ and root test_* files into tests/
c9474d58 issue-323: phase 2 — parallel role-session conflict methodology, checker, tests
```
canonical: same git-log output, this session — the implementation
record cites the test's path under a `test/` directory; commit
c79d034d (issue #729, unrelated to issue #323) relocated the whole
tree to `tests/` after issue #323 landed. The test file's content and
both fixtures are otherwise unchanged.

### Req 5 — operations.md cross-reference — Present

`derived: grep -n "check-write-set-conflicts\\|parallel-conflict-methodology" docs/handbooks/operations.md`,
run this session:
```
818:`scripts/check-write-set-conflicts.sh`를 병합 전에 손으로 돌려서 확인한다. 방법론
819:전체는 `docs/specs/parallel-conflict-methodology.md` 참고.
822:(issue #323) — run `scripts/check-write-set-conflicts.sh` by hand before merging. Full
823:methodology: `docs/specs/parallel-conflict-methodology.md`.
```
canonical: same grep output, this session — a bilingual (Korean +
English) cross-reference is present, matching the implementation
record's description.

### Req 6 — `files:` frontmatter measurement reproduces — Present

`derived: git ls-tree -r --name-only c9474d58 | grep -cE '^docs/issue-[0-9]+/proposals/.*\.md$'`,
run this session:
```
108
```
`derived: git ls-tree -r --name-only c9474d58 | grep 'proposals/' | grep -vE '^docs/issue-[0-9]+/proposals/[^/]+\.md$'`,
run this session:
```
docs/proposals/2026-07-27-muster-portability-and-doc-refresh.md
docs/proposals/2026-07-27-remote-github-marketplace.md
docs/proposals/2026-07-27-shared-core-and-consent.md
```
`derived: for path in <the 108+3 paths above>; do git show c9474d58:"$path" | grep -qE '^files:' && echo has || echo no; done | sort | uniq -c`,
run this session:
```
73 of the 108 docs/issue-*/proposals paths: has
2 of the 3 docs/proposals paths: has
```
canonical: `docs/specs/parallel-conflict-methodology.md` lines 65-67,
read this session — records "111 total proposal files, 75 (67.6%)
carry `files:` frontmatter, 36 (32.4%) do not." 108+3 total and 73+2
carrying frontmatter reproduce that ratio exactly.

## Summary table

canonical: the six per-requirement verdict sections above, this
session's own re-run evidence.

| Req | Implementation record claim | Verdict |
|---|---|---|
| 1 | spec states the adapted methodology | Present |
| 2 | checker exists, anchoring bug fixed | Present |
| 3 | parser is reusably sourceable | Present |
| 4 | test suite behavior matches record | Present |
| 5 | operations.md cross-reference added | Present |
| 6 | frontmatter-ratio measurement | Present |

## Open findings

canonical: the six verdict sections above, this session — every claim
in the phase-2 implementation record reproduces against this session's
own commands; no open finding is filed. The one discrepancy this
session located — the test's directory relocated since issue #323
landed — traces to commit c79d034d (issue #729's unrelated
consolidation), cited in Req 4 above, and does not change the test's
behavior, so no new issue is filed for it.

## Next steps

canonical: docs/issue-323/reports/implementation.md next-steps section,
read this session, and `gh issue view 323` state field, read this
session (`state: CLOSED`) — this record exists to make the phase-2
delivery's claims independently re-run rather than merely narrated.
Downstream consumption by issue #324 and gate-wiring remain out of this
record's scope, per the implementation record's own next-steps
section.

## Resolution path

No open finding requires a resolution path. Should the checker later
be wired into a gate, a future conformance review should re-run Req
6's frontmatter-ratio commands above to check the `unknown` bucket has
not silently grown without the backfill the implementation record
names as out-of-scope future work.

Proposal: docs/issue-323/proposals/conformance-review.md
