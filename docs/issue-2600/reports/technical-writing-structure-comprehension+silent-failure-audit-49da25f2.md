---
issue: 2600
role: technical-writing-structure-comprehension+silent-failure-audit-49da25f2
author: technical-writing-structure-comprehension+silent-failure-audit-49da25f2
skills: technical-writing-structure-comprehension (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: on-the-record (7 files — see "What was done" for the list; full diff in this PR)
    sha: same-commit
type: audit-and-fix
breaking: false
verdict: prompt/directive-text slice of #2600 delivered for on-the-record (7 files under directive/*.md and commands/*.md; scope-file total 210 -> 139 occurrences of role/역할, derived below). protocol.md and protocol.ko.md deliberately left untouched — their `roles/<name>.json`-based rulebook architecture appears to already be dead code, a pre-existing staleness question out of this slice's remit, detailed under "Open findings".
loop_state: landed
upstream:
  - path: docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab.md (PR #2673/#2675, comment/docstring slice — established the `role session` -> `spawned session`, `role` -> `skill` vocabulary convention this record reuses)
    sha: ee7c8c92b0bcb1fde198dec041ef27003843a59c
---

# issue-2600 — technical-writing-structure-comprehension+silent-failure-audit-49da25f2 record

## Environment check (spawned per task directive)

canonical: `env | grep -E 'CLAUDE_SKILL|CLAUDE_ROLE'` output at session start —
`CLAUDE_SKILL=technical-writing-structure-comprehension+silent-failure-audit-49da25f2`,
no `CLAUDE_ROLE` in the environment. `CORE_BUILD_NOW=1` was also present,
authorizing the build-now bypass this record follows. This session's own
spawn (from user request through this record's PR) is the requested
end-to-end proof that PR #2710's `CLAUDE_ROLE` -> `CLAUDE_SKILL` rename did
not break spawning.

## What was done

Retired teaching-current-model `role`/`역할` wording from on-the-record's
prompt/directive-text slice (protocol.md, protocol.ko.md,
`on-the-record/directive/*.md`, `on-the-record/commands/*.md`) — the slice
the earlier comment/docstring PR (#2673/#2675) deliberately left alone
because these files are read live, as instruction, by every spawned
session.

Edited (7 files):

- `on-the-record/directive/spawn-and-board.md` — fixed #2693 (the
  `--with-judge` preview claimed to match "the same ... refinement spawn
  itself would run"; it doesn't — `rank_skills()` defaults `k=2`, spawn's
  own internal mount uses `k=5` via `_COMPOSED_SKILLS_TOPK`) and #2694
  (documented the `outcome` value list, derived from `rank_skills()`'s own
  docstring/return paths in consult.py, not from #2694's prose); plus 6
  generic `role session`/`role` -> `spawned session`/`session` prose
  rewrites. 9 -> 2 occurrences (the 2 left are the retired
  `role`-positional CLI form, named as history, and the literal
  `APPROVE issue-<n>/<role>` token — see "Why").
- `on-the-record/commands/run.md` — 65 -> 15. Same rewrite pattern applied
  at scale, plus one stale-example fix: consult.md's `--skills`/consult
  examples used `coding` as a sample skill name; `coding` does not exist
  under skill-repository as an exact name or a `coding-`-prefixed family
  (checked below), so the example would have failed if followed literally.
- `on-the-record/commands/consult.md` — 7 -> 1. Renamed the `<역할>`
  placeholder to `<스킬>` throughout (matches line 30's own explanation
  that the value resolves through `resolved_skill_dirs()`, same path as
  `--skills`) and replaced the broken `coding` example with
  `architecture-interface-contract-shape` (a real skill-repository
  directory, thematically matched to the example's "is this schema change
  breaking" question).
- `on-the-record/directive/record-claim-shape.md` — 2 -> 0.
- `on-the-record/directive/relay-and-reporting.md` — 4 -> 0. Includes the
  "DELIVERABLES ARE ROLE WORK" line — the same phrase the issue's comment
  thread flagged in `deliverable-guard.sh:281` (out of this slice's file
  scope) as a live consumer-visible refusal message teaching the retired
  model in the same breath as `--skills`. No gate/regex in this repo
  matches on the literal string "role work" (checked below), so rewording
  it here is safe and consistent with the established convention.
- `on-the-record/directive/requirement-intake.md` — 1 -> 0 (dropped a
  redundant `/role` suffix after an already-correct `skill` reference).
- `on-the-record/commands/report-upstream.md` — 2 -> 1 (one generic
  "issue->role flow" phrase rewritten; the other occurrence names a
  literal, still-real record-schema field, left — see "Why").

Left unchanged: `protocol.md`, `protocol.ko.md`,
`on-the-record/directive/acceptance-format.md`,
`on-the-record/directive/merge-gates.md`,
`on-the-record/directive/delegation-loops.md`,
`on-the-record/directive/monitor-mode.md` (0 occurrences already). Reasons
are per-file, in "Why".

Also updated `docs/specs/reconciled-index.md`'s one tracked row for
`on-the-record/commands/run.md` (mandatory: `gates/spec_index.py` /
`spec-index-preflight` blocks a commit that changes a tracked spec file
without it) — this is the only change under `docs/` in this PR, and it is
not a historical record.

derived: `git archive HEAD | tar -x` into an empty directory, before and
after this commit, then
`grep -rIo -iE '\brole\b|역할' protocol.md protocol.ko.md on-the-record/directive/*.md on-the-record/commands/*.md | wc -l`
— 210 before, 139 after (per-file breakdown in "What was done" above).

## Why

**The behavior test, applied per occurrence.** For every `role`/`역할`
hit in the scope files, the question was "can a session act differently
on the new sentence than on the old one?" — not "does this read better."
Concretely, that split into four buckets:

1. **Safe rename** — generic prose describing "a spawned unit of
   work"/"a session" with no tie to a literal, still-existing identifier.
   Renamed per the convention #2673 already established
   (`role session` -> `spawned session`, `role` -> `skill` where a skill
   name is genuinely meant).
2. **Literal identifier/template, left untouched** — text citing a real
   code symbol, file path, or gate-matched string that has not itself
   been renamed. Examples: `APPROVE issue-<n>/<role>` (matches
   `approval-gate.sh:255`'s literal `needle` construction and
   `gates/forbidden_action_rule.py`'s regex — same carve-out the earlier
   slice already applied to README.md/UNENFORCED-CLAUSES.md, extended
   here to every file in this slice that also carries the token);
   `docs/issue-<n>/reports/<역할>.md` (the frontmatter `role:` field is
   still the live filename convention — this record's own filename is an
   instance of it); `issue-<n>/<role>` branch naming (matches
   `spawn.py:3532`'s literal `f"issue-{issue}/{role}"` and the regex
   symbol names `_BRANCH_SUBJECT_ROLE_RE`/`_ISSUE_ROLE_BRANCH` quoted in
   merge-gates.md); `session-role-bind.sh` (a real, currently-shipped
   filename, still snapshotting `CLAUDE_SKILL` under its old name —
   checked below).
3. **Historical narration** — text explicitly describing the *retired*
   form as retired (e.g. spawn-and-board.md/run.md's "the retired
   role-positional (`spawn.py <role> "<task>"`)", run.md's "이 판단은
   고정된 이름(역할/카테고리)으로 분류하지 않는다"). Rewriting the word
   here would make the sentence describe nothing — left as-is, same
   treatment the earlier slice gave "historical narration."
4. **Pre-existing stale content, out of this slice's remit** — see "Open
   findings" below. Where a `role` occurrence sits inside a claim that is
   already factually wrong (not because of wording, because the file/
   mechanism it names no longer exists), rewriting the word would dress
   up a false claim in current vocabulary rather than fix it. Left
   untouched and flagged instead of silently "fixed" by relabeling.

derived: `grep -n "role work\|ROLE WORK" --include=*.py --include=*.sh -r .`
— 2 hits, both in `on-the-record/hooks/deliverable-guard.sh` (a comment
and an emitted message); no gate parses this exact phrase as a token, so
`relay-and-reporting.md`'s rewrite to "DELIVERABLES ARE DELIVERY WORK" is
a labeling change only.

derived: `ls /home/jwjung/skill-registry/skills | grep -iE "^coding"` —
empty (no exact or prefix match) — confirms the `coding` example in
consult.md/run.md was stale before this PR.

derived (spawn-and-board.md #2693 fix): `grep -n "_COMPOSED_SKILLS_TOPK" spawn.py`
— `_COMPOSED_SKILLS_TOPK = 5` at line 616, used by the real cross-family
mount call (`consult.py:867`); `rank_skills()`'s own signature
(`consult.py:749`) defaults `k: int = 2`, and `spawn.py`'s
`--skill-candidates` call site (~line 2186) does not override it — so the
preview and the real mount ask for different `k` by default.

derived (spawn-and-board.md #2694 outcome list):
```
consult.py:783-798 (rank_skills docstring): "no-candidates" -- ranked is
[] (BM25 found nothing); "bm25-only" -- use_judge=False; "completed" --
judge ran and returned a verdict; "fail-open" -- judge errored or timed
out, ranked (BM25) is still fully populated; "fast-path:<names>
[+completed|+fail-open]" -- declared-phrase auto-pick short-circuited
some/all judge slots.
```

canonical: `grep -n "APPROVE issue" on-the-record/hooks/approval-gate.sh` —
line 255 `needle = "APPROVE issue-%d/%s" % (issue, role)`, confirming the
literal token this repo's live approval path matches on, unrenamed.

canonical: `grep -n "session-role-bind" on-the-record/hooks/approval-gate.sh`
— line 86, `# session-role-bind.sh snapshots CLAUDE_SKILL at SessionStart`
— the script is still named `session-role-bind.sh` even though PR #2710
already moved what it snapshots to `CLAUDE_SKILL`; this is why
protocol.md's "session-role-bind snapshot"/"bound role" wording (§8) was
left untouched rather than renamed to match `CLAUDE_SKILL` — the script
itself has not been renamed, so the doc naming it correctly still matches
reality.

## What did not work

None.

## Open findings

Four pre-existing staleness findings surfaced while checking whether a
`role` occurrence was safe to rename (bucket 4 above). None of these are
wording issues — each is a claim that is false regardless of vocabulary,
and fixing them means redesigning what the text says, not relabeling it,
so they are named here rather than silently patched:

1. **`roles/<name>.json` and `roles/specs/<role>.spec.json` no longer
   exist in this repo**, but protocol.md/protocol.ko.md §3 and run.md's
   "띄우기 전에 확인할 것" step 1 both still instruct reading them.
   derived: `find . -maxdepth 1 -iname "roles" -not -path "./.git*"` —
   empty. derived: `python3 gates/spec_index.py --update` —
   `FileNotFoundError: ... roles/specs/brand-design.spec.json` (the
   generator itself crashes on this dangling reference, independent of
   this PR — confirms the path is gone, not just unread). `roles/specs/`
   is also cited by `merge-gates.md`'s "PER-ROLE QUALITY BAR" bullet and
   `gates/quality_bar.py`'s own docstring already says (line 7) that path
   "was deleted." Resolution path: a follow-up issue scoped to what
   replaced the `decides`/`use_when`/`produces` catalog (skill-repository
   `SKILL.md` files, per consult.py's own #2610 note, is the likely
   candidate) — not #2600.
2. **`_JUDGMENT_AXES` does not exist in the codebase.**
   derived: `grep -rn "JUDGMENT_AXES" --include=*.py .` — no output.
   run.md's step-5 boundary bullet (lines ~145-149) still tells the
   orchestrator to route review judgment through "이미 배선된 축 패널
   (`_JUDGMENT_AXES`, 각 축의 소유 역할, `open_decision_item` 트리아지)".
   Left untouched (the whole mechanism it names is phantom, not just the
   word) and flagged for the same follow-up as finding 1.
3. **`docs/specs/reconciled-index.md`'s ledger citation is already
   wrong.** It cites `on-the-record/commands/run.md:677` for the ledger
   claim; the actual line is 663, and this predates this PR — derived:
   `git show origin/main:on-the-record/commands/run.md | grep -n ledger`
   — line 663, same as after this PR's edits (my edits did not change
   run.md's line count: `wc -l` is 680 before and after). Not fixed here
   (out of scope — this record's edits target `role`/역할 wording only).
4. **`protocol.md`'s recorded hash in `docs/specs/reconciled-index.md`
   already does not match the file on `origin/main`**, predating this
   PR. derived: `git show origin/main:protocol.md | sha256sum` ->
   `d8d58309ed6d66f0ea07b90c995a95a6d3b145c2c7e4e5b337b614ac5cd85eba`;
   the index's recorded value is `84addaa507f829b4b9a061dd1c9b5059b087e4e3bcdb1353860de06398d4717d`.
   `git log --oneline -3 -- protocol.md` shows PR #2632 (issue #2629) as
   the most recent change, which evidently did not run
   `spec_index.py --update`. Not fixed here — updating it requires
   deciding the index is "reconciled" against the current content, which
   is a judgment this slice (wording-only, and explicitly not touching
   protocol.md's content) should not make.

Given findings 1-2, `protocol.md`/`protocol.ko.md`'s `roles/<name>.json`
per-role-marketplace description (§2-3) and run.md's mirrored bullets look
like they may themselves be describing an architecture already replaced
by the current skill-repository/`CLAUDE_SKILL` system — not confirmed
either way here, since confirming it means resolving what (if anything)
replaced the per-role rulebook marketplace, which is out of a
vocabulary-only slice's remit. This is why protocol.md/protocol.ko.md
were left entirely untouched rather than partially reworded: renaming
`role` to `skill` inside a section that may already be describing a dead
mechanism would make a stale claim read as current, which is worse than
leaving it visibly in the old vocabulary.

## Upstream basis

Builds on `docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab.md`
(PR #2673/#2675, comment/docstring slice, `sha: ee7c8c92b0bcb1fde198dec041ef27003843a59c`)
for the `role session` -> `spawned session`, `role` -> `skill` vocabulary
convention this record reuses — spot-checked as still current by
re-deriving this record's own before/after counts rather than trusting
that record's numbers.

Also read, as context only (no commit basis, not listed in frontmatter
`upstream:`): the issue #2600 comment thread's live consumer-encounter
finding on `deliverable-guard.sh:148`/`:102`/`pr-base-guard.sh:3`, its
persisted-data-key finding on `runs/spawn-attempts.jsonl`, and its
partition-by-occurrence-kind consult. The persisted-data-key and
hooks-emitted-string findings are out of this slice's file scope (`.jsonl`
and `.sh`, not `.md`) and not addressed here.

## Next steps

skill-verdict: technical-writing-structure-comprehension — not-applicable:
this slice was single-word/short-phrase vocabulary substitution inside
already-short sentences, not sentence/paragraph restructuring for
comprehension — no sentence exceeded the 15-20 word target as a result of
an edit.
skill-verdict: silent-failure-audit — not-applicable: no code changed in
this diff (prose-only, `.md` files), so there are no catch blocks/error
paths to classify; the skill's own trace-forward reasoning (does a
fallible path fail with no indication?) informed how "Open findings" 1-2
above were surfaced and reported instead of silently patched, but that is
an analogy, not an application of the procedure to code.

This slice (prompt/directive-text, on-the-record only) is done.
canonical: `git diff --stat origin/main -- on-the-record/directive on-the-record/commands docs/specs/reconciled-index.md`
in this working tree shows exactly the 7 edited `.md` files plus the one
index row, matching "What was done" above.

Remaining #2600 work, per the issue's own partition (not started here):
the identifier slice (`role_settings()`, `role.json`,
`roles/*.json`/`roles/specs/*.json` — findings 1-2 above feed that slice),
the persisted-data-key slice (`runs/*.jsonl`), the hooks-emitted-string
slice (`.sh` files, including `deliverable-guard.sh`/`pr-base-guard.sh`),
and tokenmaxxxer-core's own sweep.

`loop_state: landed`.
