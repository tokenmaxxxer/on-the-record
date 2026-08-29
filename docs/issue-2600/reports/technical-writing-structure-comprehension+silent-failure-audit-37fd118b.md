---
issue: 2600
role: technical-writing-structure-comprehension+silent-failure-audit-37fd118b
author: technical-writing-structure-comprehension+silent-failure-audit-37fd118b
skills: technical-writing-structure-comprehension (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: on-the-record/directive/acceptance-format.md
    sha: same-commit
  - path: on-the-record/directive/delegation-loops.md
    sha: same-commit
  - path: docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-49da25f2.md
    sha: same-commit
type: audit-and-fix
breaking: false
verdict: send-back on PR #2712 fixed — the 2 files it falsely marked "0 occurrences already" (acceptance-format.md 4, delegation-loops.md 16) are now renamed under the same behavior-test/bucket framework that record already established; scope-file total for on-the-record/directive/*.md + on-the-record/commands/*.md is 121 -> 32 (was 121 -> 50 after PR #2712 alone).
loop_state: landed
upstream:
  - path: docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-49da25f2.md
    sha: same-commit
  - path: docs/issue-2600/reports/adversarial-review+technical-writing-structure-comprehension-c6207fe3.md
    sha: d6bd4ec3b9a55ef3d0a80c85da557e39372dc6f7
---

# issue-2600 — technical-writing-structure-comprehension+silent-failure-audit-37fd118b record

## What was done

Fixed the two problems raised in the send-back on PR #2712 (the
prompt/directive-text slice of #2600). Both were confirmed live before
fixing:

1. **Completed the slice.** `on-the-record/directive/acceptance-format.md`
   and `on-the-record/directive/delegation-loops.md` were byte-identical
   to `origin/main` at PR #2712's head — the earlier record listed both
   under "Left unchanged ... (0 occurrences already)", which was false
   (4 and 16 occurrences respectively). derived: `grep -oiE '\brole\b|역할'
   on-the-record/directive/acceptance-format.md on-the-record/directive/delegation-loops.md
   | wc -l` on `origin/issue-2600/technical-writing-structure-comprehension+silent-failure-audit-49da25f2`
   (PR #2712's head) — 20. Applying the same behavior test PR #2712's
   record already defined ("can a session act differently on the new
   sentence?"): `delegation-loops.md` — every one of its 16 occurrences
   was generic prose (bucket 1, safe rename), now 0. `acceptance-format.md`
   — 3 of its 4 occurrences were generic prose (renamed), 1 occurrence
   (appearing twice in the added clarifying sentence, so 2 hits in the
   `grep -o` count) is a literal identifier still matched by
   `gates/forbidden_action_rule.py`'s `_ROLE_REASSIGNED` regex
   (`non-role`) and was left untouched — see "Why" for the full
   per-occurrence classification.
2. **Corrected the PR body's count claim.** PR #2712's body stated
   "210 -> 139" for the scope
   "`on-the-record/directive/*.md` and `on-the-record/commands/*.md`" —
   that 210->139 figure only holds once `protocol.md`/`protocol.ko.md`
   are included; those two globs alone reproduced 121 -> 50 (checked
   independently in PR #2713). This record's own PR body (opened by this
   session) states the two figures separately and names which files each
   one covers, so the number and the scope it was taken over agree — see
   "Upstream basis".

Files touched: `on-the-record/directive/acceptance-format.md` (4 -> 2
occurrences), `on-the-record/directive/delegation-loops.md` (16 -> 0),
and an append-only correction section added to
`docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-49da25f2.md`
(board-gate, contract v3 s11, forbids editing another author's existing
lines — the false "Left unchanged"/count lines in that record are left
in place, unedited, and corrected by the new section instead).

derived: `grep -rIo -iE '\brole\b|역할' protocol.md protocol.ko.md
on-the-record/directive/*.md on-the-record/commands/*.md | wc -l` — 210
before this record's PR chain (unchanged, `protocol.md`/`protocol.ko.md`
still deliberately untouched, per PR #2712's "Open findings"), 121 after
this fix (was 139 after PR #2712 alone). Restricted to just
`on-the-record/directive/*.md` + `on-the-record/commands/*.md` (no
protocol files, the scope PR #2712's body actually described): 121
before -> 32 after this fix (was 121 -> 50 after PR #2712 alone).

canonical: `git diff --stat origin/main -- docs/` in this working tree —
3 files, all under `docs/issue-2600/reports/` (this record, PR #2712's
record plus its correction, both newly created/appended by this issue's
own work) and one already-tracked row in `docs/specs/reconciled-index.md`
(PR #2712's mandatory spec-index sync for `run.md`, unrelated to this
fix) — no file under any other `docs/` path is touched, so the
"historical records are untouched" acceptance criterion holds for this
PR chain.

## Why

Same behavior-test/bucket framework PR #2712's record already
established, reapplied to the 2 files it skipped:

- **Bucket 1 (safe rename), all 16 of `delegation-loops.md`'s hits and 3
  of `acceptance-format.md`'s 4**: generic prose naming "the thing a
  judgment/artifact is delegated to." Two distinct referents needed two
  different replacement words, both already established by earlier #2600
  work: `role` -> `skill` where the referent is the consult/panel target
  (matches `spawn.py --skills`/`resolved_skill_dirs()`, same as
  `commands/consult.md`'s already-renamed `<스킬>` placeholder), `role`
  -> `session` where the referent is a spawned delivery unit (matches
  the `role session` -> `spawned session` convention from PR
  #2673/#2675, reused by PR #2712 in `spawn-and-board.md`). Two
  occurrences were additionally stale independent of wording and fixed
  as part of the same pass since the fix was the word itself: "role-scoped
  under $CLAUDE_SKILL" was self-contradictory after PR #2710's
  `CLAUDE_ROLE` -> `CLAUDE_SKILL` rename (fixed to `skill-scoped`);
  "role-bound session ... for any role" sits next to a "no CLAUDE_SKILL
  binding" reference in the same sentence, same contradiction (fixed to
  `skill-bound`/"for any skill").
- **Bucket 2 (literal identifier, left untouched)**: `acceptance-format.md`'s
  "orchestrator/operator/a non-role account" describes the sanctioned
  wording `gates/forbidden_action_rule.py` accepts to reassign a
  forbidden Acceptance-bullet action away from the delivering session.
  canonical: `gates/forbidden_action_rule.py:48`,
  `_ROLE_REASSIGNED = re.compile(r"orchestrator|\boperator\b|\bhuman\b|non-role|..."` —
  the regex matches the literal substring `non-role`. `gates/*.py` is
  out of this slice's file scope (`.md` only, per PR #2712's own scope
  statement), so renaming this doc phrase to `non-session` would desync
  the directive's sanctioned wording from what the gate actually accepts
  — a session following the renamed doc text would write text the gate
  does not recognize, which is exactly the "can a session act
  differently" failure the behavior test exists to catch. Left
  unchanged, with an inline note explaining why (not just left silent,
  which is the shape that produced this send-back in the first place).
- **Bucket 4 (pre-existing stale content, out of a wording-only slice's
  remit)**: `delegation-loops.md`'s File-case example command,
  `spawn.py spawn <role> "<task>" --issue <n> --background`, names a
  `spawn` subcommand and a `--background` flag that do not exist.
  derived: `grep -n '"spawn"' spawn.py` and `grep -n -- "--background"
  spawn.py` — neither returns a subcommand/flag registration (the only
  spawn form is `spawn.py --skills <skill>[,...] "<task>" --issue <n>`,
  per `spawn.py`'s own `--issue` help text and issue #2572). This
  predates the role/역할 sweep and is a design/redesign question (what
  the File-case example should actually say), not a wording fix — named
  here rather than silently renamed into a still-broken example, same
  treatment PR #2712 gave `protocol.md`'s dead `roles/<name>.json`
  references. Only the word (`<role>` -> `<skill>`, "role" -> "skill" in
  the trailing description) was touched inside that broken example; the
  command shape itself is untouched and still wrong.

## Upstream basis

Builds directly on
`docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-49da25f2.md`
(PR #2712, `sha: same-commit` — merged into this branch, then corrected
by this session's append-only addendum in the same file) for the
scope-file set, the bucket framework, and the established
`role`/`role session` -> `skill`/`session` conventions this record
reuses without re-deriving them. Also reads, as the source of the two
problems this record fixes,
`docs/issue-2600/reports/adversarial-review+technical-writing-structure-comprehension-c6207fe3.md`
(PR #2713, sha in frontmatter `upstream:` above — the independent
verification that found the false "0 occurrences" claim and the
scope-mismatch in PR #2712's body) — both problems it raised are fixed
above.
canonical: `gh pr view 2712 --json body` — the send-back this record
answers is a review comment on that PR quoting the exact "0 occurrences
already" false line and the "210 -> 139" scope mismatch this record's
"What was done" section fixes.

## What did not work

None.

## Open findings

None new. The one bucket-4 finding surfaced while fixing
`delegation-loops.md` (the fictional `spawn.py spawn <role> ... --background`
command) is documented above in "Why" and is the same class of
pre-existing, wording-independent staleness PR #2712's record already
opened findings for against `protocol.md`/`protocol.ko.md`/run.md — not
a new resolution path, same remit boundary ("a vocabulary-only slice
should not redesign what a broken example says").

## Next steps

None for this send-back — it closes both problems the review raised.
The rest of #2600 (the identifier slice, the persisted-data-key slice,
the hooks-emitted-string slice, and tokenmaxxxer-core's own sweep)
remains open, per PR #2712's own record, and is not started here.

skill-verdict: technical-writing-structure-comprehension — applied:
invoked; applied the sentence-length target, clause-splitting, and
filler-deletion rules from SKILL.md while drafting this record's own
"What was done"/"Why" prose above; not applied to the
`on-the-record/directive/*.md` edits themselves — those are single-word/
short-phrase vocabulary substitutions inside already-existing sentences
(same judgment PR #2712's record already made for its own edits), not
sentence restructuring.
skill-verdict: silent-failure-audit — not-applicable: no code changed in
this diff (`.md` prose plus one append-only record section) — there are
no catch blocks or error-handling paths to enumerate or classify.

`loop_state: landed`.
