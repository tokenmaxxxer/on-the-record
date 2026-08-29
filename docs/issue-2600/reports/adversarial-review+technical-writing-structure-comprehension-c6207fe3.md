---
issue: 2600
role: adversarial-review+technical-writing-structure-comprehension-c6207fe3
author: adversarial-review+technical-writing-structure-comprehension-c6207fe3
skills: adversarial-review (skill-repository(297e350)), technical-writing-structure-comprehension (skill-repository(297e350))
verifies_subject: true  # independent verification of PR #2712's deliverable
loop_state: landed
code_under_review: 1642cc963ce5a52a6a25a0b323be6080ad074092
type: verification
breaking: false
verdict: count-and-code-claims-confirmed-two-files-silently-left-out-of-the-slice
upstream:
  - path: PR #2712 (tokenmaxxxer/on-the-record), branch issue-2600/technical-writing-structure-comprehension+silent-failure-audit-49da25f2
    sha: 1642cc963ce5a52a6a25a0b323be6080ad074092
  - path: docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-49da25f2.md (untracked here — lives on PR #2712's branch, not merged to this working tree)
    sha: 1642cc963ce5a52a6a25a0b323be6080ad074092
---

# issue-2600 — adversarial-review+technical-writing-structure-comprehension-c6207fe3 record

## What was done

Independent, hostile re-verification of PR #2712 (issue #2600's
prompt/directive-text slice, also closing #2693/#2694). Two fresh clones
made from scratch (`git clone` into `/tmp/verify-2712/repo`, then
`git fetch origin pull/2712/head:pr2712`) — every claim below is
re-derived from raw command execution against the actual file content,
not inherited from the PR body or its own record.

canonical: `gh pr view 2712 --json title,body,files,commits,state,baseRefName,headRefName`
(executed) — head `1642cc96`, branch
`issue-2600/technical-writing-structure-comprehension+silent-failure-audit-49da25f2`,
base `main`, 7 `.md` files touched under `on-the-record/directive/` and
`on-the-record/commands/`, plus `docs/specs/reconciled-index.md` (1 row)
and the PR's own new record file.

### 1. Behavior-change hunt

derived: `git diff origin/main...pr2712 -- on-the-record/commands/consult.md
on-the-record/commands/report-upstream.md on-the-record/commands/run.md
on-the-record/directive/record-claim-shape.md
on-the-record/directive/relay-and-reporting.md
on-the-record/directive/requirement-intake.md
on-the-record/directive/spawn-and-board.md` — 470-line diff, read in full
(executed, not summarized).

Every rename is either generic-prose "역할"/"role" → "세션"/"스킬", or a
literal identifier the PR left untouched. The literal-identifier claims
were checked against the code that matches them, not against the PR's
own assertion:

```
$ grep -n "APPROVE issue" on-the-record/hooks/approval-gate.sh
255:    needle = "APPROVE issue-%d/%s" % (issue, role)
$ find . -iname "session-role-bind*"
./on-the-record/hooks/session-role-bind.sh
$ grep -n "_BRANCH_SUBJECT_ROLE_RE" gates/spawn_on_approve.py
57:_BRANCH_SUBJECT_ROLE_RE = re.compile(r"(?:^|/)(issue-\d+)/([A-Za-z0-9-]+)$")
$ grep -n "_ISSUE_ROLE_BRANCH" gates/ci.py
75:_ISSUE_ROLE_BRANCH = re.compile(r"^issue-(\d+)/([^/]+)$")
$ grep -n "_BRANCH_RE" gates/flows.py
32:_BRANCH_RE = re.compile(r"^(issue-[0-9]+)/([a-z0-9-]+)$")
```

derived: `grep -rn "directive/spawn-and-board\|commands/run.md\|
directive/relay-and-reporting\|directive/record-claim-shape\|
directive/requirement-intake\|commands/consult.md\|
commands/report-upstream" --include=*.py --include=*.sh .` and
`grep -rln "역할" --include=*.py --include=*.sh .` (both executed) — no
gate/hook greps the prose content of these 7 files for `role`/`역할`;
every `.py`/`.sh` hit is a runtime variable/dict-key literally named
`role`, unrelated to this PR's prose.

Present/Absent verdict: **Absent** — no renamed token in this diff is
matched by a live gate, regex, or branch-naming convention.
`APPROVE issue-<n>/<role>`, `issue-<n>/<role>` branch naming, and
`session-role-bind.sh` are all still real, unrenamed, and correctly left
alone.

### 2. #2693 fix (spawn-and-board.md `--with-judge` claim)

```
$ grep -n "^def rank_skills" consult.py
749:def rank_skills(task_text: str, role: str = "candidates",
   ... k: int = 2) -> dict:
$ sed -n '2172,2189p' spawn.py
    if a.skill_candidates:
        ...
        result = rank_skills(task_text, role="candidates",
                             repo_root=_skill_repo_root(),
                             issue=a.issue, cwd=a.cwd,
                             home=Path.home(), target_repo_root=Path(a.cwd),
                             use_judge=a.with_judge)
$ grep -n "_COMPOSED_SKILLS_TOPK" spawn.py consult.py
spawn.py:616:_COMPOSED_SKILLS_TOPK = 5
spawn.py:3360:            k=_COMPOSED_SKILLS_TOPK,
consult.py:869:        k=_sp._COMPOSED_SKILLS_TOPK, model=model)
```

derived: the `sed`/`grep` output above (executed) shows
`--skill-candidates` never passes `k=`, so it runs `rank_skills()` at its
default `k=2`, while the real internal cross-family mount inside
`_spawn_one()` (`spawn.py:3360`) calls it with `k=_COMPOSED_SKILLS_TOPK`
= `k=5`. spawn-and-board.md's new sentence ("this preview asks for `k=2`
candidates by default while spawn's own internal mount asks for `k=5`")
matches this exactly.

Present/Absent verdict: **Present** — checked against `rank_skills()`'s
and its two call sites' actual code, not against #2693's issue text.

### 3. #2694 fix (spawn-and-board.md `outcome` value list)

Enumerated every return statement myself:

```
$ grep -n 'return {"ranked"\|outcome = \|outcome_prefix = ' consult.py
82:        return {"ranked": [], "outcome": "no-candidates", "picked": []}
84:        return {"ranked": ranked, "outcome": "bm25-only", "picked": []}
... (inside _cross_family_skill_matches_with_consult, lines 607-745)
    outcome_prefix = f"fast-path:{','.join(fast_names)}" if fast_names else ""
    return fast_dirs, outcome_prefix                       # fast-path alone filled every slot
    return fast_dirs, (outcome_prefix or "no-candidates")  # fast-path left 0 BM25 candidates
    outcome = "completed"                                  # judge ran and returned a verdict
    outcome = "fail-open"                                  # judge errored/timed out
    if outcome_prefix:
        outcome = f"{outcome_prefix}+{outcome}"
```

derived: the `grep` output in the fence above (executed) enumerates the
full return-value space as seven concrete strings — `no-candidates`,
`bm25-only`, `completed`, `fail-open`, `fast-path:<names>`,
`fast-path:<names>+completed`, `fast-path:<names>+fail-open`.
spawn-and-board.md's new text ("`outcome` is one of `no-candidates`,
`bm25-only`, `completed`, `fail-open`, or
`fast-path:<names>[+completed|+fail-open]`") accounts for all seven via
the bracketed-optional-suffix notation.

Present/Absent verdict: **Present** — derived directly from the
function's control flow (fence above), nothing missing.

### 4. The count (210 → 139)

```
$ git archive origin/main -- on-the-record/directive on-the-record/commands | tar -x -C before
$ git archive pr2712 -- on-the-record/directive on-the-record/commands | tar -x -C after
$ grep -rIo -iE '\brole\b|역할' before | wc -l
121
$ grep -rIo -iE '\brole\b|역할' after | wc -l
50
```

This is the exact scope the PR body names ("Scope-file total
(`on-the-record/directive/*.md`, `on-the-record/commands/*.md`): 210 ->
139") — 121 -> 50 does not match 210 -> 139.

```
$ git show origin/main:protocol.md > protocol.before.md
$ git show origin/main:protocol.ko.md > protocol.ko.before.md
$ git show pr2712:protocol.md > protocol.after.md
$ git show pr2712:protocol.ko.md > protocol.ko.after.md
$ grep -rIo -iE '\brole\b|역할' protocol.before.md protocol.ko.before.md | wc -l
89
$ grep -rIo -iE '\brole\b|역할' protocol.after.md protocol.ko.after.md | wc -l
89
$ diff protocol.before.md protocol.after.md && echo IDENTICAL
IDENTICAL
$ diff protocol.ko.before.md protocol.ko.after.md && echo IDENTICAL
IDENTICAL
```

derived: the two fences above (both executed) give `121 + 89 = 210` and
`50 + 89 = 139` — the PR's headline 210 -> 139 only reproduces once
`protocol.md` and `protocol.ko.md` (deliberately untouched, unchanged
either side per the `diff` output) are folded into the grep scope. The
PR's own record does this correctly — its `derived:` line lists
`protocol.md protocol.ko.md on-the-record/directive/*.md
on-the-record/commands/*.md` in the grep command — but the **PR body**
text names only the two globs that alone give 121 -> 50, not 210 -> 139.
The number itself is accurate once protocol.md/protocol.ko.md are
included; the PR body's own wording about what it counted is misleading
on its own.

derived: from the same fences above — 89 of the 139 remaining hits sit in
`protocol.md`/`protocol.ko.md`, entirely pre-existing and unchanged
(confirmed by the `diff ... IDENTICAL` lines). The other 50 break down
per file as follows (executed):

```
$ grep -rIo -iE '\brole\b|역할' after | cut -d: -f1 | sort | uniq -c
      1 after/on-the-record/commands/consult.md
      1 after/on-the-record/commands/report-upstream.md
     15 after/on-the-record/commands/run.md
      4 after/on-the-record/directive/acceptance-format.md
     16 after/on-the-record/directive/delegation-loops.md
     11 after/on-the-record/directive/merge-gates.md
      2 after/on-the-record/directive/spawn-and-board.md
```

Reading each hit with context (executed: `grep -n -iE '\brole\b|역할' <file>`
per file): consult.md's 1 is the literal `<역할>.md` record-filename
convention (still-live `role:` frontmatter field); spawn-and-board.md's 2
are historical narration of the retired `spawn.py <role>` form; run.md's
15 mix literal `APPROVE issue-<n>/<role>` (x2), literal
`roles/<역할>.json`/`roles/specs/<role>.spec.json` catalog references
tied to the dead-architecture finding below (x2), the phantom
`_JUDGMENT_AXES` passage tied to that same finding (x2), literal
`issue-<n>/<role>` branch narration, and a handful of generic prose
(e.g. "**역할이 맞는가.**", "역할 분류 줄도 반복하지 않는다") that reads
like the same pattern renamed elsewhere in the same file but wasn't;
report-upstream.md's 1 is the literal `role:` record-schema field name;
merge-gates.md's 11 are mostly the literal `issue-<n>/<role>` branch
pattern plus the `roles/specs/<role>.spec.json` reference, both explained
in the PR's own record's "Why"/"Open findings" sections.
`acceptance-format.md` (4) and `delegation-loops.md` (16) are the
exception — untouched, unexplained, and misdescribed by the PR's own
record. See "Open findings" below.

### 5. protocol.md / protocol.ko.md skip

All four staleness findings the PR's record cites as its reason for
skipping these files were re-derived live, independently:

```
$ find . -maxdepth 1 -iname "roles" -not -path "./.git*"
(empty — roles/<name>.json does not exist)
$ grep -rn "JUDGMENT_AXES" --include=*.py .
(no output — _JUDGMENT_AXES does not exist in code)
$ grep -n "ledger" on-the-record/commands/run.md
663:...사후 회계는 runs/ledger.jsonl 에 있다.
(docs/specs/reconciled-index.md:37 cites run.md:677 — off by 14 lines, predates this PR)
$ sha256sum protocol.md
d8d58309ed6d66f0ea07b90c995a95a6d3b145c2c7e4e5b337b614ac5cd85eba
$ grep -n "protocol.md" docs/specs/reconciled-index.md
18: `protocol.md` | `84addaa507f829b4b9a061dd1c9b5059b087e4e3bcdb1353860de06398d4717d`
(recorded hash does not match the live file — predates this PR)
$ python3 gates/spec_index.py --update
FileNotFoundError: ... roles/specs/brand-design.spec.json
(the generator itself crashes on a dangling roles/specs/ reference, confirming finding 1 independent of this PR)
```

derived: all four executed checks above reproduce exactly as the PR's
record describes them. A sampled read of `protocol.md` (`grep -n -iE
'\brole\b' protocol.md`, executed, first 60 hits) shows the file's
`role`/`역할` content is structurally entangled with the confirmed-dead
`roles/<name>.json` architecture throughout (§2-3's "A role is a plugin
set plus a boundary", `role-handoff-contract.md` references, per-role
quality-bar catalog), not confined to one isolated section — an
all-or-nothing skip is defensible, not an arbitrary shortcut, and it is
disclosed (PR body + record's "Open findings"), not silent.

Present/Absent verdict: **Present/sound** — the skip is justified by
executed evidence, not merely asserted.

### 6. Test-suite delta

derived: `timeout 115 python3 -m pytest test/ -q` on `pr2712` (executed)
produced no completed output before the timeout fired, confirming the
task brief's warning that the full suite exceeds 2 minutes here; switched
to `-m "not slow"` per the task's own guidance, as follows.

```
$ git checkout origin/main && python3 -m pytest test/ -m "not slow" -q 2>&1 | tail -3
15 failed, 387 passed, 6 xfailed in 2.66s
$ git checkout pr2712 && python3 -m pytest test/ -m "not slow" -q 2>&1 | tail -3
15 failed, 387 passed, 6 xfailed in 2.97s
$ diff <(pytest ... origin/main | grep ^FAILED | sort) <(pytest ... pr2712 | grep ^FAILED | sort)
(no output — identical FAILED nodeid sets on both refs)
```

derived: the three executed pytest runs above show zero delta. The 15
pre-existing failures are a sandbox/network limitation (`fetch 실패 —
fatal: 'origin' does not appear to be a git repository`, hit by
`test_convention_equivalence.py`/`test_spawn_cross_family_skill_selection.py`/etc.,
all network-dependent fixtures), unrelated to this PR — present
identically on `origin/main` with zero code changes from this PR. This
matches expectation, since `git diff --name-only origin/main...pr2712`
(executed) shows this PR touches zero `.py`/`.sh`/`test/` files.

## Why

The task's behavior test — "can a session act differently on the new
sentence than on the old one?" — was applied per finding in §1-6 above
and answered no for every renamed token in the diff (§1, executed grep
against every gate/hook in the repo). The count claim reproduces exactly
once the grep scope matches what the underlying record's `derived:` line
actually specifies rather than what the PR body's prose implies (§4,
executed `git archive` both sides). The two code-derived fixes (§2, §3)
were checked against `consult.py`'s real control flow via direct
`grep`/`sed` reads (executed above), not against the issue text or the
PR's own docstring citation.

The one real finding (§4/"Open findings" below) is a completeness/honesty
gap in the PR's record, not a behavior-change bug — no gate reads
`acceptance-format.md`'s or `delegation-loops.md`'s prose (§1, same
executed grep sweep covers these two files: neither appears as a target
of any gate/hook file-read).

## What did not work

None.

## Upstream basis

Builds on PR #2712 (`tokenmaxxxer/on-the-record`, branch
`issue-2600/technical-writing-structure-comprehension+silent-failure-audit-49da25f2`,
head `1642cc96`, per `gh pr view 2712` above) and its own record,
`docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-49da25f2.md`
(untracked in this working tree — lives on PR #2712's branch, read via
`git show pr2712:docs/issue-2600/reports/...md`, executed) — read in
full, but every claim in it was independently re-derived from raw
commands (fresh clone, `git archive`, direct code reads, listed above)
rather than trusted, per this task's instruction not to inherit its
conclusions.

## Open findings

1. **`acceptance-format.md` (4 occurrences) and `delegation-loops.md`
   (16 occurrences) were left completely untouched, and the PR's record
   misrepresents this.**
   canonical: `git show pr2712:docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-49da25f2.md`
   (executed, read in full) — the "Left unchanged" line reads:
   "`protocol.md`, `protocol.ko.md`,
   `on-the-record/directive/acceptance-format.md`,
   `on-the-record/directive/merge-gates.md`,
   `on-the-record/directive/delegation-loops.md`,
   `on-the-record/directive/monitor-mode.md` (0 occurrences already).
   Reasons are per-file, in 'Why'."
   ```
   $ diff before/on-the-record/directive/acceptance-format.md after/on-the-record/directive/acceptance-format.md && echo IDENTICAL
   IDENTICAL
   $ grep -c -iE '\brole\b|역할' before/.../acceptance-format.md after/.../acceptance-format.md
   before: 4   after: 4
   $ diff before/on-the-record/directive/delegation-loops.md after/on-the-record/directive/delegation-loops.md && echo IDENTICAL
   IDENTICAL
   $ grep -c -iE '\brole\b|역할' before/.../delegation-loops.md after/.../delegation-loops.md
   before: 16   after: 16
   $ grep -n "acceptance-format\|delegation-loops" record.md
   79:`on-the-record/directive/acceptance-format.md`,
   81:`on-the-record/directive/delegation-loops.md`,
   (each name appears exactly once, on the "Left unchanged" list line — no other mention anywhere in the record)
   ```
   derived: the four fences above (all executed) show "(0 occurrences
   already)" is false for these two files — 4 and 16 pre-existing hits,
   unchanged on both sides, not 0 — and "Reasons are per-file, in 'Why'"
   is not backed by any explanation for either file anywhere in the
   document (unlike `merge-gates.md`, explained twice — tied to the
   dead-catalog finding and the literal branch-naming carve-out — and
   `protocol.md`/`protocol.ko.md`, explained at length in "Open
   findings"). Content-wise, most hits in both files are generic prose
   ("delegate it to the matching role", "tracing which judgments went to
   which role", "a role-bound session never posts one", "a solo role's
   verdict"; "the delivering role is categorically...", "refuses for
   every role session", "a non-role account") matching the exact "safe
   rename" pattern applied at scale in run.md and spawn-and-board.md,
   with no literal-identifier or dead-mechanism tie found on inspection.
   Not a behavior-change bug (§1: no gate reads this prose) and not
   blocking, but the PR's own accounting of its scope is incomplete.
   Resolution path: fold these 20 occurrences into this same slice, or
   amend the record to explain them the way `merge-gates.md` and
   `protocol.md`/`protocol.ko.md` are explained — not a new issue, since
   it is the same wording-only work this PR already claims finished for
   its sibling files.
2. **PR body's "Scope-file total" line names a scope that does not
   reproduce its own number.** See §4 above (executed `git archive`
   both sides: the named two-glob scope gives 121 -> 50, not 210 -> 139;
   210 -> 139 requires also including `protocol.md`/`protocol.ko.md`,
   which the PR body's sentence does not mention even though the
   record's own `derived:` line does). Cosmetic — the number itself
   holds up — but worth a one-line PR-body correction.

## Next steps

`loop_state: landed` — this verification is finished; no further action
is required from this record. Finding 1 above is a suggested follow-up
for the PR author, not a blocker this record needs to chase further.

skill-verdict: adversarial-review — applied: invoked; used the skill's
blind-evaluator stance as the operating method for this review — every
claim in PR #2712 and its record was re-derived from raw commands in a
fresh clone (§1-6 above) rather than trusted, adapted to a single
hostile-verifier session per this task's explicit instruction to
re-derive from raw commands rather than spawn a literal second session.
skill-verdict: technical-writing-structure-comprehension — not-applicable:
this task is claim verification against code and git history, not
drafting or editing sentence/paragraph structure for reader
comprehension; PR #2712 itself is a vocabulary-substitution slice, not a
structure-comprehension edit, so the skill's checklist (sentence length,
chunk breaks, phase-grouped procedures) has no target in this task.
skill-verdict: work-in-english — applied: invoked; this record, all
intermediate reasoning, and all commands were written in English per the
skill's routing rule; the final chat summary to the user is in Korean.
