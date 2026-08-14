# Current-state survey: execution-observation of the implementation role on issue #1118

Scope: the `implementation` role's phase-1→phase-2 execution on issue
#1118 (hook-pair contradiction: deliverable-guard vs
product-capture-stopgate), branch `issue-1118/implementation`.

canonical: `gh pr list --search "head:issue-1118/implementation" --state all --json number,title,state,url,mergeCommit,commits`, read this session.
Delivered through two merged PRs: #1125 (code, commit `41e5623b`, merge
commit `12c7cbb1`) and #1128 (phase-2 board record, commit `f526e42b`,
merge commit `930d4153`), against `origin/main` at `2e51bd92` (`git
rev-parse origin/main`, run this session).

## What was read this session, in order

1. `gh issue view 1118` and `gh issue view 1118 --comments` — issue body
   (three named defects, four acceptance scenarios) and full comment
   thread, including the `APPROVE issue-1118/architecture` and
   `APPROVE issue-1118/implementation` exact-string comments, both
   authored by `JiwonJung94`.
   canonical: `gh issue view 1118 --comments`, read this session.
2. `gh pr list --search "head:issue-1118/implementation"` — resolved the
   two merged PRs listed above.
   canonical: same `gh pr list` command, read this session.
3. `gh pr diff 1125` — the diff itself, read before any record
   narrative (fresh-eyes ordering): `on-the-record/hooks/product-capture-stopgate.sh`
   (Fix 2's `INJECTED_WRAPPER_RE`/`flat_text` change, Fix 3's
   session-keyed dedup block), `gates/test_product_capture_vs_deliverable_guard.py`
   (new, 164 lines, four `t_*` scenarios), and
   `docs/issue-1118/decisions/generator-choice.md` (new ADR).
   canonical: `gh pr diff 1125`, read this session.
4. `gh pr view 1128 --json body` and `git show origin/main:docs/issue-1118/reports/implementation.md`
   — the observed role's own phase-2 record, read only after the diff.
   canonical: `git show origin/main:docs/issue-1118/reports/implementation.md`, read this session.
5. `cat docs/specs/approvers.md` — `JiwonJung94` and `jjongkwann` are the
   only listed approver accounts.
   canonical: `cat docs/specs/approvers.md`, read this session.
6. `ls docs/issue-1118/proposals/ docs/issue-1118/reports/architecture/`
   and `git log --oneline --all -- docs/issue-1118/reports/architecture/ docs/issue-1118/proposals/`
   — confirms `2026-08-13-stopgate-scan-and-dedup.md` (proposal) and
   `survey.md` (architecture role's current-state survey) exist, both
   landed in one commit, `407800ca`.
   canonical: the `ls` and `git log` commands above, read this session.
7. `find docs/issue-1118 -iname "*scout*"` and `grep -n -i "scout\|skip"
   docs/issue-1118/proposals/2026-08-13-stopgate-scan-and-dedup.md
   docs/issue-1118/reports/architecture/survey.md`.
   canonical: the `find` and `grep` commands above, run this session —
   no scout-brief file exists anywhere under `docs/issue-1118/`, and no
   skip-record line was found in either file.

## Independent re-execution of the cited evidence

`rm -rf /tmp/otr-product-capture` (clearing the dedup state directory,
matching the observed role's own note about cross-run pollution) then,
on the current working tree (`origin/main` at `2e51bd92`):

canonical: `python3 gates/test_product_capture_vs_deliverable_guard.py`, run this session.
```
PASS t_capture_write_path_permitted_end_to_end
PASS t_empty_state_bootstrap_still_works
PASS t_injected_directive_only_transcript_does_not_flag
PASS t_undischargeable_flag_does_not_repeat_on_consecutive_stops
4/4 passed
```

canonical: `python3 on-the-record/hooks/test_product_capture_stopgate.py`, run this session.
```
9/9 passed
```

canonical: `python3 -m pytest on-the-record/hooks/test_deliverable_guard.py -q`, run this session.
```
19 passed in 0.68s
```

canonical: the three `derived:`-shaped commands and their pasted output
immediately above, run this session — all three counts match the
observed role's own record exactly. This is a live re-run this session
of the already-committed test suite against the already-merged code,
run strictly to check the outcome claim, not a re-execution of the
observed role's task (building/fixing the hooks) — per role-directive
this session never touched `src/`, never re-implemented, and never
edited the observed artifact.

## What the record covers vs. what remains open

- Outcome: PR #1125's diff delivers Fix 2 and Fix 3 as described; PR
  #1128 adds the phase-2 record.
  canonical: the three `derived:`-shaped commands and pasted output in
  the section immediately above, run this session — all three re-run
  clean on current main.
- Trajectory: `docs/issue-1118/reports/architecture/survey.md` and
  `docs/issue-1118/proposals/2026-08-13-stopgate-scan-and-dedup.md` exist
  and were committed together (`407800ca`) before PR #1125's code
  commit (`41e5623`, 2026-08-13T00:39:06Z per its own `gh pr list
  ...commits` metadata, canonical: item 1-2 above) — survey-before-
  proposal and research-before-proposal both look satisfiable, pending
  phase-2's closer read of the full file contents.
  canonical: `gh pr view 1125 --json author` / `gh pr view 1128 --json
  author`, read this session — the `APPROVE issue-1118/implementation`
  comment is a real, listed-account, exact-string match (single-account
  mode: PR author and approver are both `JiwonJung94`).
- Open question flagged for phase 2, canonical: item 7 above (the
  `find`/`grep` commands, run this session) — no scout-brief file
  exists under `docs/issue-1118/` and no skip-record line was found in
  the proposal or survey text. The change involved a named design
  decision (generator-level fix vs. instance patch, per
  `docs/issue-1118/decisions/generator-choice.md`) rather than a pure
  syntactic bugfix, so whether scouting should have applied — and, if
  so, whether its absence is a step-level deficiency — is a phase-2
  judgment call, not resolved here.

## Verdict-level scope for phase 2

Phase 2 will check, against the evidence gathered above (all citations
this session's own reads/re-runs, none of it a verdict yet): **outcome**
(did PR #1125 + #1128 land what issue #1118's Requirements/Acceptance
asked, recomputed from step-level results, not summarized), **trajectory**
(scouted-when-required, surveyed-before-proposing, approved-by-human —
each marked satisfied/unsatisfied/not-applicable on its own line), and
**step** (any specific artifact-level deficiency, including the
scout-brief gap noted above, each with subject/test/result/assertedBy
and an evidence mode tag).
