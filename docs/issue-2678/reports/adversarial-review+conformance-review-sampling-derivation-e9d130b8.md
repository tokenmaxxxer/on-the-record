---
issue: 2678
role: adversarial-review+conformance-review-sampling-derivation-e9d130b8
author: adversarial-review+conformance-review-sampling-derivation-e9d130b8
skills: adversarial-review (skill-repository(297e350)), conformance-review-sampling-derivation (skill-repository(297e350))
verifies_subject: true
loop_state: landed
upstream:
  - path: PR tokenmaxxxer/on-the-record#2690
    sha: 8d980c59b611fc4dff873d30e28713051e37d84a
---

# issue-2678 — adversarial-review+conformance-review-sampling-derivation-e9d130b8 record

## What was done

Independent verification of pull request 2690 ("orchestrator
skill-candidate ranking + zero-invocation signal", covering issues #2678
and #2681). canonical: `gh pr view 2690 --repo tokenmaxxxer/on-the-record
--json title,body,headRefName,baseRefName,files,commits` output, read
this session — head oid `8d980c59b611fc4dff873d30e28713051e37d84a`
(second commit) built on `84d8768707858cb5e3c996a620d6a2c9e2f5629a` (first
commit), base `main`.

Re-derived every claim below from a fresh clone rather than the subject's
own record's conclusions:
```
$ mkdir -p /tmp/verify-2690/repo && cd /tmp/verify-2690/repo
$ git clone --quiet https://github.com/tokenmaxxxer/on-the-record.git .
$ git fetch origin pull/2690/head:pr-2690 && git checkout pr-2690
```
derived: the clone/fetch/checkout commands above, executed this session,
verified via `git log --oneline -3` showing `8d980c59` as HEAD. A second,
independent fresh clone of clean `origin/main` was made at
`/tmp/verify-2690/main-clone/repo` for the before/after test comparison
in Claim 5 below — no state shared with the PR clone or with this role's
own working tree.

None of the six paths below inherited the subject record's conclusions;
each was re-executed against the raw code/tests/hook in the fresh clone.

### Claim 1 — the substituted 12-task corpus may be easy-mode

The subject PR could not recover the consumer session's literal 12-task
corpus in its own environment and substituted this repo's own 12 most
recent issue titles instead — a substitution this verification does not
fault (the spawning instructions for this session state the same: the
consumer's `spawn-attempts.jsonl` schema carries no task-text field, so
recovery was structurally impossible, not merely unattempted). What the
substitution *costs* is the open question.

Constructed three task descriptions in the consumer's actual shape
(field-level mapping between two schemas, no tokenmaxxxer/skill-repo
vocabulary) and ran the real, unmocked `spawn.py --skill-candidates`
against this machine's mounted skill-repository checkout:
```
$ cd /tmp/verify-2690/repo
$ python3 spawn.py --skill-candidates "Map the incoming vendor invoice CSV columns to our internal billing record fields: vendor_id becomes partner_code, invoice_date format changes from MM/DD/YYYY to ISO 8601, and the tax_amount field must be split into state_tax and local_tax using a lookup table" \
  2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['outcome']); print([(r['name'], round(r['score'],2)) for r in d['ranked'][:5]])"
bm25-only
[('localization-locale-convention-formatting', 18.08), ('negotiation-batna-and-zopa-preparation', 14.21), ('api-design-error-design', 12.07), ('conformance-review-severity-classification', 11.95), ('technical-feasibility-verdict-and-timebox-selection', 11.85)]

$ python3 spawn.py --skill-candidates "Given the upstream customer profile schema (name, dob, address_line1, address_line2, phone) and the downstream CRM schema (full_name, birth_date, street, unit, mobile_number), write the field-by-field transformation and flag where one upstream field must fan out into two downstream fields" \
  2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['outcome']); print([(r['name'], round(r['score'],2)) for r in d['ranked'][:5]])"
bm25-only
[('parallel-decomposition', 16.30), ('localization-locale-convention-formatting', 14.60), ('ux-engineering-control-selection', 14.38), ('refactoring-legacy-seam-selection', 12.52), ('finance-unit-economics-evidence-chain', 12.24)]

$ python3 spawn.py --skill-candidates "Reconcile the legacy order schema against the new order schema: legacy order_qty is a string with embedded units, new schema wants a numeric quantity field plus a separate unit enum, and legacy nests shipping address under ship_to while the new schema flattens it into top-level prefixed fields" \
  2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['outcome']); print([(r['name'], round(r['score'],2)) for r in d['ranked'][:5]])"
bm25-only
[('ux-engineering-navigation-depth', 12.65), ('fmea', 11.55), ('api-design-tool-landscape', 11.06), ('product-discovery-hypothesis-preregistration', 10.69), ('localization-locale-convention-formatting', 10.22)]
```
derived: the three `spawn.py --skill-candidates` invocations above,
executed this session against the real mounted skill registry (234
candidate skills). `implementation-blueprint` appears as top-1 in exactly
zero of the three cases — derived from the printed top-5 lists above,
none of which contain that name. Also derived from the same three
outputs: every top-1 result is a generic shared-token match ("format",
generic build/decomposition vocabulary, "field") rather than anything
about schema mapping, so the letter of "not implementation-blueprint" is
met while the ranking is not obviously useful.

Checked where the genuinely relevant skills rank for task 1:
```
$ python3 spawn.py --skill-candidates "Map the incoming vendor invoice CSV columns to our internal billing record fields: vendor_id becomes partner_code, invoice_date format changes from MM/DD/YYYY to ISO 8601, and the tax_amount field must be split into state_tax and local_tax using a lookup table" \
  2>/dev/null > /tmp/t1.json
$ python3 -c "
import json
d = json.load(open('/tmp/t1.json'))
names = [r['name'] for r in d['ranked']]
total = len(names)
for target in ['data-modeling-structure', 'data-engineering-pipeline-design',
               'api-design-resource-modeling', 'architecture-interface-contract-shape']:
    pos = names.index(target) + 1 if target in names else None
    print(target, pos, 'of', total)
"
data-modeling-structure None of 234
data-engineering-pipeline-design None of 234
api-design-resource-modeling 126 of 234
architecture-interface-contract-shape 49 of 234
```
derived: the command above, executed this session against the same JSON
output as the task-1 run above — the two most relevant data-modeling and
data-engineering skills share zero BM25 tokens with the task text and do
not appear anywhere in the 234-entry ranking; `architecture-interface-contract-shape`
(the skill actually mis-mounted in the real #2681 incident) ranks 49th
out of 234, not surfaced near the top. Between this block and the block
immediately above it, the full evidence for this Claim is now on the
table.

Verdict, derived from the two blocks immediately above (the three-probe
top-5 dump and this rank-position check): bullet 3 ("resolves to a skill
other than `implementation-blueprint`") is met, letter-for-letter, on
both the substituted corpus and on all three of my consumer-shaped
probes. That bullet is close to a vacuous win condition against this
corpus, since `implementation-blueprint` rarely tops BM25 for any task
with real content, while the two blocks above show the top-ranked results
are noise and the two most relevant skills are absent or buried far down
the same ranking. The corpus substitution itself is not a defect —
recovering the literal corpus was structurally impossible, confirmed
independently this session by grepping this repo's own retained
`spawn-attempts.jsonl` files for a task-text field:
```
$ find / -xdev -iname "spawn-attempts.jsonl" 2>/dev/null | while read f; do python3 -c "import json; print(list(json.loads(open('$f').readline()).keys()))"; done | sort -u
['event', 'attempt_id', 'issue', 'role', 'pid', 'ts']
```
derived: the command above, executed this session — the schema this
session independently observed carries no task-text field, matching what
the subject record itself reported. What is not established is that
acceptance bullet 3 holds for the consumer's real task shape; it is
plausibly false there, per the ranked-position dump derived two blocks
above.

### Claim 2 — "byte-identical reuse" (SameScoringTest)

Split verdict: true for `ranked` (the BM25 order), false for `picked`
under `--with-judge`.
```
$ grep -n "_bm25_cross_family_scores\|_cross_family_skill_matches_with_consult" consult.py spawn.py
consult.py:15:...
consult.py:607:def _cross_family_skill_matches_with_consult(task_text: str, role: str,
consult.py:634:    scored = _sp._bm25_cross_family_scores(task_text, role, repo_root, home, target_repo_root)
consult.py:826:    scored = _sp._bm25_cross_family_scores(task_text, role, repo_root, home, target_repo_root)
consult.py:834:    picked_dirs, outcome = _sp._cross_family_skill_matches_with_consult(
spawn.py:347:_cross_family_skill_matches_with_consult = consult._cross_family_skill_matches_with_consult
spawn.py:617:_bm25_cross_family_scores = directive_assembly._bm25_cross_family_scores
spawn.py:3358:            _cross_family_skill_matches_with_consult,
```
derived: the grep above, executed this session in the fresh PR clone —
exactly one definition of each shared function, called both from
`rank_skills()` (consult.py:826/834) and from spawn's own real internal
add-only mount (spawn.py:3358). Re-ran the subject's `SameScoringTest`
directly:
```
$ python3 -m pytest test/test_skill_candidates_ranking.py -v 2>&1 | tail -12
...
[gw3] [ 10%] PASSED test/test_skill_candidates_ranking.py::SameScoringTest::test_candidate_path_matches_internal_bm25_scoring
============================== 10 passed in 0.88s ==============================
```
derived: the pytest invocation above, executed this session against the
fresh PR clone (not the subject's own claimed run) — confirms the `ranked`
order really is single-implementation.

The internal call passes `k=_COMPOSED_SKILLS_TOPK` (spawn.py:3360), and
that constant equals 5, raised from a prior default of 2 by issue #2507:
```
$ grep -n "_COMPOSED_SKILLS_TOPK" spawn.py consult.py
consult.py:869:        k=_sp._COMPOSED_SKILLS_TOPK, model=model)
spawn.py:616:_COMPOSED_SKILLS_TOPK = 5
spawn.py:3360:            k=_COMPOSED_SKILLS_TOPK,
```
derived: the grep above, executed this session. `rank_skills()`'s own
default stays `k: int = 2` (consult.py:751), and the `--skill-candidates`
CLI dispatch never overrides it:
```
$ grep -n '"--k"\|"--top-k"\|args.k\b\|a\.k\b' spawn.py
(no output)
```
derived: the grep above, executed this session — no flag exists to
override `k` from the CLI at all.

Live repro isolating `k` as the only variable (real, unmocked production
functions; the judge itself mocked only to remove the network/API
dependency, filling every slot it is offered so the comparison exercises
slot count, not judge quality):
```python
with mock.patch.object(spawn, "_skill_judge_consult", side_effect=fake_judge):
    cli_result = spawn.rank_skills(task, "orchestrator", root, issue=2678,
                                    cwd=td, use_judge=True)   # what --skill-candidates --with-judge calls
    internal_dirs, internal_outcome = spawn._cross_family_skill_matches_with_consult(
        task, "orchestrator", root, 2678, td, k=spawn._COMPOSED_SKILLS_TOPK,
        home=Path("/tmp"), target_repo_root=Path(td))          # what _spawn_one()'s real mount calls
```
```
CLI (--skill-candidates --with-judge) picked: ['data-mapping-skill-0', 'data-mapping-skill-1']
spawn's real internal mount would pick: ['data-mapping-skill-0', 'data-mapping-skill-1', 'data-mapping-skill-2', 'data-mapping-skill-3', 'data-mapping-skill-4']
```
derived: the script above, executed this session in the fresh PR clone —
same `task`/`role`/`repo_root` arguments on both sides, only `k` differs,
and the two entry points return different `picked` lists for the
identical task, per the two lines of output quoted immediately above.
`SameScoringTest` does not exercise this path — it only covers
`use_judge=False`.

This directly contradicts the orchestrator-facing text this PR itself
added to `on-the-record/directive/spawn-and-board.md` (lines 13-29,
re-read this session in the fresh clone): "the ranking you see here
cannot disagree with what spawn would add on top of whatever you name"
(true only of `ranked`, which the sentence does not distinguish from
`picked`) and "`--with-judge` ... the same haiku judge refinement spawn
itself would run" (false for `picked` whenever BM25 top-5 differs from
top-2, i.e. generically whenever more than two candidates are plausible,
per the k-mismatch repro derived above).

### Claim 3 — the fail-open tag

Confirmed end-to-end against the real, unmocked CLI — no defect found
here. Forced a genuine judge timeout through the production path (real
`claude` subprocess launch, real `subprocess.TimeoutExpired`):
```
$ which claude
/home/jwjung/.local/bin/claude
$ SKILL_JUDGE_TIMEOUT=0.001 python3 spawn.py --skill-candidates "Map the incoming vendor invoice CSV columns to our internal billing record fields: vendor_id becomes partner_code" --issue 2678 --with-judge 2>&1 | tail -15
...
  "outcome": "fail-open",
  "picked": [
    "negotiation-batna-and-zopa-preparation",
    "tech-feasibility"
  ]
```
derived: the command above, executed this session end-to-end against the
production CLI and the `SKILL_JUDGE_TIMEOUT` env override (consult.py:181-199)
— `ranked` (234 entries, full BM25 order) survived fully populated in the
same JSON output, `outcome` read `"fail-open"`, never `"no-candidates"`.
This is exactly what the orchestrator would receive from the real
command. Re-ran the subject's own unit test to confirm it exercises the
same contract:
```
$ python3 -m pytest test/test_skill_candidates_ranking.py::FailOpenDistinguishableTest -v
...
2 passed
```
derived: the pytest invocation above, executed this session. This is the
#2679 defect class (a fail-open invisible to its caller) genuinely not
repeated here.

Secondary, minor gap: `spawn-and-board.md`'s new paragraph documents what
`"outcome": "no-candidates"` means (line 27 in the fresh clone) but never
mentions `"fail-open"` anywhere in that file:
```
$ grep -n "fail-open" on-the-record/directive/spawn-and-board.md
(no output)
```
derived: the grep above, executed this session against the fresh PR
clone — the field is present and correct in the JSON, but the
orchestrator-facing directive gives no instruction for interpreting it.
Not a blocking defect; a directive-completeness gap.

### Claim 4 — #2681's advisory-only claim

Confirmed. canonical: `git show 84d8768707858cb5e3c996a620d6a2c9e2f5629a
-- on-the-record/hooks/skill-verdict-guard.sh` output, read this session
— the entire diff for #2681 is the `zero_invocation_notice()` function
plus one call-site edit (`finish(reminder)` becomes
`finish(zero_invocation_notice(mounted), reminder)`); both branches of
`finish()` end in `sys.exit(0)`.

Ran the real, unmocked hook script directly with four adversarial
stdin/env combinations (mounted skills present, zero invoked in every
case):
```
$ cd /tmp/verify-2690/repo
$ echo '{"session_id":"s1"}' | bash on-the-record/hooks/skill-verdict-guard.sh; echo "exit=$?"
exit=0
$ echo '{"session_id":"s2","transcript_path":"/tmp/does-not-exist-xyz.jsonl"}' | bash on-the-record/hooks/skill-verdict-guard.sh; echo "exit=$?"
exit=0
$ printf '\x00\x01\xff\xfe not json at all\n{"type": "assistant"' > /tmp/garbage_transcript.jsonl
$ MUSTER_SKILLS="foo-skill,bar-skill" bash -c 'echo "{\"session_id\":\"s3\",\"transcript_path\":\"/tmp/garbage_transcript.jsonl\"}" | bash on-the-record/hooks/skill-verdict-guard.sh'; echo "exit=$?"
{"hookSpecificOutput": {..."zero-invocation..."}}exit=0
$ : > /tmp/empty_transcript.jsonl
$ MUSTER_SKILLS="foo-skill,bar-skill" bash -c 'echo "{\"session_id\":\"s4\",\"transcript_path\":\"/tmp/empty_transcript.jsonl\"}" | bash on-the-record/hooks/skill-verdict-guard.sh'; echo "exit=$?"
{"hookSpecificOutput": {..."zero-invocation..."}}exit=0
```
derived: the four invocations above, executed this session against the
fresh PR clone's own shipped hook — missing transcript_path key,
nonexistent transcript file, malformed/binary transcript, and empty
transcript, all with skills mounted and none invoked. Every case exits 0
per the `exit=` lines quoted above; none produce `decision:"block"`; the
two cases where the mounted-skills early-return path is actually reached
(malformed and empty transcript) correctly emit the advisory
`zero_invocation_notice()` text via `hookSpecificOutput.additionalContext`.
No input tried made it refuse, block, or non-zero-exit.

Also confirmed #2153's per-mounted-skill obligation is not restored: the
diff quoted above only adds the notice string to the existing
`if not invoked:` early return — it adds no new requirement anywhere else
in the file, and the branch still owes no `skill-verdict:` line for any
uninvoked skill.

### Claim 5 — "15 pre-existing failures, identical before/after"

Confirmed at nodeid level against a genuinely clean `origin/main`
worktree — not the subject's own claim taken on faith.
```
$ cd /tmp/verify-2690/repo && python3 -m pytest test/ -q 2>&1 | grep '^FAILED' | sort > /tmp/pr_failures.txt
$ cd /tmp/verify-2690/main-clone/repo && python3 -m pytest test/ -q 2>&1 | grep '^FAILED' | sort > /tmp/main_failures.txt
$ diff /tmp/pr_failures.txt /tmp/main_failures.txt && echo "IDENTICAL FAILURE SETS"
IDENTICAL FAILURE SETS
$ wc -l /tmp/pr_failures.txt /tmp/main_failures.txt
  15 /tmp/pr_failures.txt
  15 /tmp/main_failures.txt
```
derived: the four commands above, executed this session — a second,
independent fresh clone of `origin/main` with no shared state, `pytest
test/ -q` run on each, sorted FAILED nodeid lists byte-diffed with empty
output, and the line-count check quoted above confirming 15 on each side.
Both runs' full summary lines:
```
$ cd /tmp/verify-2690/repo && python3 -m pytest test/ -q 2>&1 | tail -1
15 failed, 382 passed, 4 xfailed in 2.51s
$ cd /tmp/verify-2690/main-clone/repo && python3 -m pytest test/ -q 2>&1 | tail -1
15 failed, 372 passed, 4 xfailed in 2.95s
```
derived: the two commands above, executed this session — all 15 failures
in both runs error with `fatal: 'origin' does not appear to be a git
repository` (the sandbox clones have no push-capable remote for those
tests' subprocess `git fetch` calls), pre-existing and unrelated to this
PR. The pass-count gap between the two runs is exactly the two new test
files, confirmed directly:
```
$ python3 -m pytest test/test_skill_candidates_ranking.py test/test_skill_verdict_guard_zero_invocation_signal.py -v 2>&1 | tail -3
============================== 10 passed in 0.88s ==============================
```
derived: the pytest invocation above, executed this session — matches
the pass-count delta between the two full-suite runs above.

### Claim 6 — the 0-of-47 zero-invocation measurement

canonical: the subject's own delivery record at
docs/issue-2678/reports/architecture-interface-contract-shape+silent-failure-audit-766c3784.md
(not present in this role's own working tree — part of the PR head
commit `8d980c59b611fc4dff873d30e28713051e37d84a`, read this session from
the fresh PR clone at /tmp/verify-2690/repo), the "#2681 — frequency
measured before deciding severity" section. The subject's own scan: a
flat glob over `$MUSTER_WORKSPACE_ROOT` for whichever workspace
directories still exist on one machine, landed=47, has_verdict=47 — the
subject's own record labels this `unverifiable`/survivorship-biased.

Applying `conformance-review-sampling-derivation` rules 1 and 3
(stratify by risk before sampling; state population size, strata, and
selection method explicitly): this scan has none of those — no stated
total population size, no risk stratification, and a selection method
that is simply "whatever is still on disk," not a designed draw, per the
same canonical section cited above. The sample cannot support a
generalizable frequency conclusion: even taking the subject's own
zero-observed-in-47 count at face value, the one-sided "rule of three"
upper bound on the true rate works out to roughly 3 divided by 47, i.e.
about 6 percent (derived: 3/47 = 0.0638), which is not confidently
"rare," and a single-machine convenience sample cannot generalize to a
wider population, per the same canonical section — the consumer's own
incident that motivated #2681 is, by that scan's own construction (a
scan of this machine's retained workspaces only), not represented in it
at all.

However, the advisory-only severity decision does not actually depend on
this measurement being right. Issue #2681's own "must not" text
(canonical: `gh issue view 2681 --repo tokenmaxxxer/on-the-record` output,
read this session) states that a blocking gate would be worse than
silence even if the zero-invocation case is common — a blocking gate
would strand work at the least recoverable moment and would teach
sessions to invoke a skill perfunctorily just to clear the gate. That
reasoning holds independent of the measured rate, so advisory-only is
justified on the issue's own terms regardless of whether the true rate is
high or low, and the severity decision survives even if the 0-of-47
figure turns out to understate the real rate. The gap is presentational
rather than structural: the subject's own "Why" section cites the
measurement as if it were confirmatory evidence toward "rare," when — per
the sampling-derivation analysis above — it is too weak on its own to
move the conclusion either way; the record would be more defensible
citing the issue's own must-not clause as the primary justification and
the measurement as a secondary, openly-caveated data point, which is
close to but not quite how it is currently framed.

## Why

Followed the six-vector attack order given in the spawning instructions,
re-deriving every claim from a fresh clone rather than reading the
subject record and agreeing with it — per `adversarial-review`'s core
mechanism of structural independence rather than same-session
"be critical" prompting, and per `conformance-review-sampling-derivation`'s
requirement to state a sample's derivation rather than report only a
count. Where the subject's own claim held up under independent
re-execution (Claims 3, 4, and 5 above), this record says so plainly
rather than manufacturing disagreement — the skill's incentive is
finding real problems, not padding a critique for its own sake. Where a
claim was technically true but the underlying acceptance bullet was not
(Claims 1 and 2), this record separates "is the sentence literally true"
from "does it establish what the acceptance bullet requires," since those
came apart in both cases: bullet 3's wording ("a skill other than
implementation-blueprint") is satisfiable by noise, and the "byte-identical"
framing conflates a genuinely single-implementation `ranked` field with a
`picked` field that is not, in practice, wired to the same `k`.

## What did not work

None.

## Upstream basis

PR tokenmaxxxer/on-the-record#2690, head commit
`8d980c59b611fc4dff873d30e28713051e37d84a`. Verified against two fresh
clones outside this role's own working tree (`/tmp/verify-2690/repo` for
the PR branch, `/tmp/verify-2690/main-clone/repo` for clean `origin/main`)
rather than against this role's own checked-out tree, which predates the
PR (`git log --oneline -1` in this working tree shows
`5d0b254d`, an ancestor commit that does not contain the PR's changes).
The subject's own delivery record was read for claim text and for the
Claim 6 sampling scan/quote but not for its conclusions — every verdict
above was re-derived from raw command output executed this session.

## Open findings

1. Claim 2 (picked-field k-mismatch): `spawn.py --skill-candidates` never
   threads a `k` override through to `rank_skills()`, so it silently uses
   the function's own default of 2 while spawn's real internal mount uses
   `_COMPOSED_SKILLS_TOPK` (value 5, per issue #2507). Resolution path: a
   send-back fix adding a `--k`/`--top-k` CLI flag (or hardcoding
   `k=_COMPOSED_SKILLS_TOPK` as the CLI's own default) plus a
   `SameScoringTest` variant that exercises `use_judge=True` against
   spawn's actual `k`, not only the BM25-only `ranked` order — and a
   correction to `spawn-and-board.md`'s "the same ... refinement spawn
   itself would run" wording.
2. Claim 1 (substituted-corpus easy-mode): acceptance bullet 3 is
   unverified — plausibly false — for the consumer's real field-mapping
   task shape; only verified for the substituted corpus and for this
   session's own consumer-shaped probes on the narrower "not
   implementation-blueprint" reading. Resolution path: none available
   within this PR's own environment, since the literal 12-task corpus
   was independently reconfirmed unrecoverable here (see Claim 1) — flagged
   as a known gap for whoever owns ranking-quality follow-up rather than
   a defect to send back on this PR alone.
3. Claim 3 secondary gap: `spawn-and-board.md` never documents the
   `"fail-open"` outcome value to the orchestrator. Resolution path: a
   one-sentence addition to the existing directive paragraph.

## Next steps

None pending from this role. The six attack vectors requested in the
spawning instructions are addressed above with re-derived, executed
evidence for each; the three items above are filed as Open findings for
a possible send-back to the subject PR's author rather than as unresolved
work in this record itself.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; used the
  structural-independence mechanism (fresh clone, re-derive every claim
  from raw command output rather than treating the subject record's
  conclusions as ground truth) across all six claims above. Most
  concretely in Claims 1 and 2: the subject's own tests
  (`TaskShapeRankingTest`, `SameScoringTest`) were re-run this session in
  the fresh clone and observed to succeed on their own inputs (derived:
  `python3 -m pytest test/test_skill_candidates_ranking.py -v`, output
  quoted in Claim 2 above), and this record then constructed inputs those
  tests do not cover — the consumer-shaped probes in Claim 1, the
  k-mismatch repro in Claim 2 — to test what the passing tests do not.
- skill-verdict: conformance-review-sampling-derivation — applied: invoked;
  used rules 1 and 3 (stratification and stated derivation) in
  Claim 6 above to evaluate the subject's 0-of-47 sample as a convenience
  sample with no stated population size, no strata, and no designed
  selection method, and rule 4 (no silent sample expansion on a
  zero-finding result) to accept the subject's own zero-finding count as
  reported (derived: the canonical section quoted in Claim 6 above) rather
  than re-running or enlarging the scan this session to manufacture a
  different finding — the gap identified above is in the derivation's
  defensibility and in how the record leans on it, not in the raw count
  itself.
