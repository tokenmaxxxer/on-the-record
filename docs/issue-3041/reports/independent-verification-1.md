---
issue: 3041
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # third independent verification of PR #3052's own deliverable, re-derived against the current merged main tip
loop_state: landed
code_under_review: PR #3052 (merged as origin/main 4822045d), also re-checked
  at origin/main fb0c6f90 (current tip, one unrelated commit later)
type: verification
breaking: false
verdict: 4 of 5 acceptance criteria Present, independently re-derived on the
  post-merge main tip rather than a pre-merge worktree. Criterion 1 (harness
  executable) reconfirmed Incorrect -- `scripts/issue-3041/run_pair.sh` is
  still git mode 100644 on origin/main today, so the defect the second
  verification pass (PR #3065) found was never fixed before or after merge.
  Finding A (marketplace skill corpus never mounted, all 4 skills-on runs
  show `plugins: []` and 0 Skill tool_use events) independently re-derived
  from the raw jsonl a third time, same result. Must-not clause (no
  call-success/mount-count/open-timing as scoring input; evaluator generates
  neither arm) holds on independent re-check of `evaluate_pair.py` and the
  `evaluator_prompt` field.
upstream:
  - path: docs/issue-3041/reports/experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600.md
    sha: 4822045d04ba68d6763ec8293e62eaca756c98ee
  - path: docs/issue-3041/reports/conformance-review-verdict-assignment+adversarial-review+experiment-trust+hypothesis-testing-e296b769.md
    sha: 5362e75a7d2035fa6f93e3fde734b7142fce7942
  - path: docs/issue-3041/reports/experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-dd58c18a.md
    sha: 5362e75a7d2035fa6f93e3fde734b7142fce7942
  - path: PR 3052, branch issue-3041/experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600
    sha: bb966ce64714cdf17d550b46e14d8e4af332baaa
---

# issue-3041 — independent-verification-1 record

## What was done

A third independent verification of PR #3052 (issue #3041's paired
skills-on/skills-off harness + 4-pair baseline), spawned per the standing
`REQUIRED_INDEPENDENT_VERIFICATIONS = 2` mechanism
(`docs/handbooks/observer-verification.md`). By the time this session
started, two qualifying `verifies_subject: true` records had already landed
on `main` (PR #3056 and PR #3065), and the requirement was already
satisfied before this session ran.

derived: `python3 gates/merge_gate.py 3052 issue-3041`, run this session:
```
허용: PR #3052 (issue-3041) 머지 자격 있음
```
This is `required_verification_missing() == 0` for subject `issue-3041`,
i.e. 2 of 2 qualifying records already present -- confirmed live, not typed
from memory.

canonical: `gh issue view 3041`, run this session -- read the issue body's
five literal `check:` commands and the "must not" clause.

canonical: both prior verification records (paths in `upstream:` above),
read this session for context. Every finding below was independently
re-derived against a live checkout, not inherited from their prose.

derived: `git pull --ff-only` run twice this session as `origin/main`
advanced from 8d4a819e to 4822045d (PR #3052's own squash-merge) to
fb0c6f90 (one unrelated PR, #3066, landing after) -- both PR #3052 and both
prior verification records were confirmed present on `main` before running
any check.

### Re-derivation of the five acceptance criteria (post-merge, on `origin/main`)

1. Harness exists, invocation documented: `test -x
   scripts/issue-3041/run_pair.sh && test -f scripts/issue-3041/README.md`.
   derived: ran both `test` clauses directly this session against the
   working tree at `origin/main` -- `run_pair.sh` is NOT executable (first
   clause fails). derived: `git ls-tree origin/main
   scripts/issue-3041/run_pair.sh` this session:
   ```
   100644 blob 03bbf01552e744b9f5598a29ecdfa5b208682bd7	scripts/issue-3041/run_pair.sh
   ```
   the git-tracked mode read directly from the tree object, not a checkout
   artifact. **Verdict: Incorrect**, matching PR #3065's finding exactly,
   and confirming the one-line `chmod +x` fix PR #3065 identified as an
   open finding was never applied -- the defect is present in the merge
   commit itself, not just the pre-merge PR diff. `README.md` exists and
   its documented invocation (`bash scripts/issue-3041/run_pair.sh ...`,
   confirmed via `grep -n "run_pair.sh" scripts/issue-3041/README.md` this
   session) does not need the `+x` bit, so the harness is usable in
   practice even though the issue's literal check fails as committed.
2. >=3 paired runs, >=2 disciplines, both arms retained: `test $(ls -d
   docs/issue-3041/_assets/*/ | wc -l) -ge 3`. derived: ran this session --
   `4`. Substantively re-checked beyond the directory count: derived: read
   the four task texts (`scripts/issue-3041/tasks/*.txt`) this session --
   distinct disciplines (build-vs-buy product brief, A/B pre-registration
   design, backend/data-model architecture write-up, post-hoc experiment
   trust/statistics review), 4 disciplines not 2. **Verdict: Present.**
3. Blind scoring, blinding mechanism named: `python3 -c "import json,glob;
   [json.load(open(f)) for f in
   glob.glob('docs/issue-3041/_assets/*/verdict.json')] and print('ok')"`.
   derived: ran this session -- `ok`, 4 files parsed. derived: `jq -r
   '.evaluator_prompt' docs/issue-3041/_assets/01-study-groups/verdict.json
   | grep -iE "skill|arm|document_1_actual|mounted"` run this session --
   zero matches (grep exit code 1), independently reconfirming no arm-label
   leak into the evaluator's input. **Verdict: Present.**
4. Top-line verdict, per-pair scores: `test $(grep -l document_1_score
   docs/issue-3041/_assets/*/verdict.json | wc -l) -ge 3`. derived: ran this
   session -- `4`. derived: `jq -c '{document_1_score, evaluator_verdict}'`
   on `01-study-groups/verdict.json` this session:
   ```
   {"document_1_score":null,"evaluator_verdict":{"document_1_score":8,"document_2_score":8,"verdict":"indistinguishable", ...}}
   ```
   top-level `document_1_score` is a `null` placeholder, the real scores
   live nested under `evaluator_verdict`; the literal `grep -l` check
   matches the field-name substring in the placeholder key either way, so
   the check passes regardless. **Verdict: Present** (on the literal check
   as written).
5. Secondary instrumentation script exists: `test -f
   scripts/issue-3041/instrument.py`. derived: ran this session -- passes.
   **Verdict: Present.**

Must-not clause: derived: `grep -n
"instrument\|skill_opens\|mount\|open"
scripts/issue-3041/evaluate_pair.py` this session -- zero references to the
instrumentation module or its metrics inside the scoring script; the
evaluator prompt is built only from task text, rubric, and the two
deliverables (confirmed in criterion 3 above). derived: `grep -n "tools"
scripts/issue-3041/evaluate_pair.py` this session -- `--tools ""`, a
fresh `claude -p` process with no tool access, distinct from either
generation session. Holds.

### Independent re-derivation of Finding A (marketplace corpus never mounted)

derived: `jq -c 'select(.type=="assistant") | .message.content[]? |
select(.type=="tool_use" and .name=="Skill")'` against all 4
`docs/issue-3041/_assets/*/skills-on.session.jsonl` files, run individually
this session -- 0 matches in every file. derived: `head -1 ... | jq -c
'.plugins'` on all 4 of the same files, run this session -- `[]` in every
file. Both independently reconfirm the finding both prior passes reported,
from the raw transcripts rather than from either prior record's narrative.

## Why

canonical: `docs/handbooks/observer-verification.md`, read this session --
`verifies_subject: true` is self-declared per record, not capped at 2; a
qualifying subject may accumulate more than the required count, and
`_own_pr_supplies_verification()` only ever helps a subject meet the
requirement, never blocks additional verification. Given this session was
already spawned with the `independent-verification-1` role before the first
two verifications landed, re-deriving the criteria independently against
the current `main` tip (rather than deferring to the two already-merged
records) is the concrete, non-redundant contribution available: it confirms
the criterion-1 defect and Finding A both persist in what is actually
merged, not only in what was reviewed pre-merge.

## What did not work

None.

## Upstream basis

- `docs/issue-3041/reports/experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600.md`
  (PR #3052's own deliverable record) -- read this session, `sha:` is the
  squash-merge commit that landed it on `main`.
- canonical: `gh pr view 3056 --json state,mergedAt`, run this session:
  ```
  {"mergedAt":"2026-09-02T04:38:32Z","state":"MERGED"}
  ```
  `docs/issue-3041/reports/conformance-review-verdict-assignment+adversarial-review+experiment-trust+hypothesis-testing-e296b769.md`
  (PR #3056, first verification pass) -- read this session for context;
  every claim re-derived independently above, not inherited.
- canonical: `gh pr view 3065 --json state,mergedAt`, run this session:
  ```
  {"mergedAt":"2026-09-02T05:02:12Z","state":"MERGED"}
  ```
  `docs/issue-3041/reports/experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-dd58c18a.md`
  (PR #3065, second verification pass) -- read this session for context.
  Its criterion-1 finding was independently reconfirmed this session
  against the current `main` tip (see the `git ls-tree origin/main` fence
  under criterion 1 above) -- still `100644`, so the fix it identified as
  open was not applied after that pass landed either.
- canonical: `gh pr view 3052 --json state,mergedAt`, run this session:
  ```
  {"mergedAt":"2026-09-02T05:02:35Z","state":"MERGED"}
  ```
  PR 3052, branch
  issue-3041/experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600,
  sha bb966ce64714cdf17d550b46e14d8e4af332baaa -- `scripts/issue-3041/*` and
  `docs/issue-3041/_assets/*` as merged onto `main`, read/run directly from
  the working tree this session (all checks above ran against this
  checkout).
- Issue #3041 body -- `gh issue view 3041`, run this session.
- derived: `python3 gates/merge_gate.py 3052 issue-3041`, run this session
  (fenced under "What was done" above) -- confirms the requirement was
  already satisfied before this session's own record.
- `python3 gates/requirement_met.py 3041 3052`, run this session --
  advisory-only, all 17 lines UNKNOWN (same as PR #3056 reported; no
  automated verdict exists for this issue's criteria).

## Open findings

- Criterion 1's Incorrect verdict (non-executable `run_pair.sh`) is still
  unfixed on `main` as of this session -- the one-line `chmod +x` fix PR
  #3065 identified remains open. Not applied here: this session's charge was
  to verify PR #3052 as landed, not to patch it.
- Finding A's corrected invocation (`--plugin-dir` alongside
  `--setting-sources project,local`, identified and live-tested by PR #3065)
  is still not applied to `run_pair.sh`, and the 4 pairs have not been
  re-run with it. Re-running with the target skill corpus actually mounted
  remains open, unstarted work.
- Finding B (target-repo emptiness confound at the `study-companion` pin)
  was re-examined by PR #3065 and re-confirmed unresolved by re-pinning
  alone; not independently re-derived a third time in this session given
  the first two derivations already agree and no new evidence would change
  the conclusion.
- none other.

## Next steps

canonical: this record's own re-derivation above -- loop_state is terminal
(landed). The five acceptance criteria and the must-not clause were
independently re-checked against the current merged `main` tip, Finding A
was independently reconfirmed a third time from raw session logs, and
criterion 1's Incorrect verdict was reconfirmed to still hold post-merge (a
new observation neither prior pass could make, since both ran pre-merge).
derived: this session made no `git push`, `gh pr merge`, or `gh pr edit`
call against #3052 or any other PR. No further action from this session;
the Open findings above name the follow-up work without starting it.

## Skill verdicts

- skill-verdict: work-in-english -- applied: invoked; used to route this
  record's exhaust (commit message, branch content, this record's body,
  citations) to English while keeping the end-of-turn summary to the user
  in Korean, per the spawning prompt's Korean task text.
- other mounted skills: not triggered.
