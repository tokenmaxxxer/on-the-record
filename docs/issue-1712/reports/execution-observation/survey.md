---
type: docs
breaking: false
loop_state: collecting-evidence
---

Subject: issue-1712

## Scope statement

Observing: role `implementation`, session on branch `issue-1712/implementation`, issue #1712, PR #1715 (`feat(issue-1712): scope-option consult ordering, Korean neutrality, banner wording`), landed on `main` at commit `04a77592963c94770d04f61e4ebe4caee6129bfa` (canonical: acceptance: gh pr view 1715 --json number,title,body,mergeCommit,commits,files,reviews — result: pass).

```
$ gh pr view 1715 --json number,title,body,mergeCommit,commits,files,reviews
number: 1715
mergeCommit.oid: 04a77592963c94770d04f61e4ebe4caee6129bfa
commits[0].oid: 8f91d5a683b21abca33f50c8dcfbced3083501a1
files: docs/issue-1712/reports/implementation.md (ADDED, +144),
       gates/test_scope_option_directive.py (MODIFIED, +36/-3),
       on-the-record/hooks/directive.sh (MODIFIED, +24/-13)
```

## What was read, in order (fresh-eyes ordering)

1. `gh issue view 1712` — issue body and Acceptance criteria, read first.
2. `gh issue view 1712 --comments` — 4 comments (canonical: acceptance: gh issue view 1712 --comments — result: pass): a
   `[watch] issue-1712/implementation: session-end: PR ... opened` note,
   a `Judgment opened` / `Verdict: escalate` pair, and an
   `APPROVE issue-1712/implementation` approval string from `JiwonJung94`
   (4 comments returned, author `JiwonJung94` on all four; one comment
   body is the exact string `APPROVE issue-1712/implementation`).
3. `gh pr view 1715 --json ...` — title, body, single commit, 3 files
   changed, merge commit oid — see the fenced `gh pr view` output above.
4. `gh pr diff 1715` (canonical: acceptance: gh pr diff 1715 — result: pass) — full diff read BEFORE reading the observed role's
   own record narrative (fresh-eyes ordering), covering:
   - `docs/issue-1712/reports/implementation.md` (new file, 144 lines —
     the observed role's own record, read as part of the diff, not
     summarized secondhand)
   - `gates/test_scope_option_directive.py` (+36/-3, three new
     assertions plus a whitespace-normalization fix to an existing one)
   - `on-the-record/hooks/directive.sh` (+24/-13, the SCOPE-OPTION
     PROPOSAL paragraph and the first-contact banner)
5. Local branch was stale against `origin/main`; fetched and fast-forwarded, then reran the acceptance command against the merged tree this session (canonical: acceptance: python3 gates/test_scope_option_directive.py — result: pass):

```
$ git fetch origin main && git merge origin/main --ff-only
Fast-forward 932b5309..04a77592
$ python3 gates/test_scope_option_directive.py
ok - t_states_banner_mentions_option_path
ok - t_states_consult_runs_on_vague_ask_before_options
ok - t_states_consult_trace_per_option
ok - t_states_neutrality_rule_forbids_korean_synonyms
ok - t_states_neutrality_rule_forbids_recommended_token
ok - t_states_non_overlap_with_1006_req4
ok - t_states_option_block_count_and_order
ok - t_states_option_fields
ok - t_states_trigger_subclass
9/9 passed
```

That run above is this session's own reproduction against the merged tree (canonical: acceptance: python3 gates/test_scope_option_directive.py — result: pass, fenced directly above).

## Diff hunks read (diff-scope rule)

Three hunks in `on-the-record/hooks/directive.sh` are in scope for
step-level claims:
- lines ~241-247: first-contact banner sentence.
- lines ~272-296: SCOPE-OPTION PROPOSAL paragraph (consult-ordering +
  neutrality-rule text).
No other region of that file, and no region of any other file besides the two named above, appears in the diff (canonical: acceptance: gh pr diff 1715 — result: pass; full diff read this session confirms no hunk exists outside these two regions in `directive.sh`, plus the one hunk in `gates/test_scope_option_directive.py`).

## What this scopes to check in phase 2

Named per the three verdict levels this role renders (contract v3 /
execution-observation spec):

- **outcome**: recompute across the record's cited step-level checks —
  does PR #1715 satisfy issue #1712's two Acceptance checks (consult
  ordering + derivation from consult output; Korean neutrality synonyms
  + banner wording), each checked against the actual diff hunks named
  above and the independently-reran test output, not the observed
  role's summary of either.
- **trajectory**: three named checks — scouted-when-required (the
  observed role's record claims a scout-directive mechanical-edit skip;
  needs checking that a skip record is actually present, not just
  claimed), surveyed-before-proposing (was there a phase-1 proposal
  commit preceding phase-2, or a single-commit build — PR #1715's commit
  history has exactly one commit per the fenced `gh pr view` output
  above, so this needs judging against that fact), approved-by-human
  (the `APPROVE issue-1712/implementation` comment from `JiwonJung94`, a
  `docs/specs/approvers.md`-listed account, in single-account mode since
  the commit's author is also `JiwonJung94` — needs exact-string
  verification, not paraphrase).
- **step**: whether any specific artifact among the three changed files
  is deficient — checked by rereading the two `directive.sh` hunks
  against the issue's Acceptance wording and the test assertions added
  in the same diff.

No verdict-shaped language appears above; this is scope only.
