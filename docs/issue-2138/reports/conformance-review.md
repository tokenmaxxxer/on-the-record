---
issue: 2138
role: conformance-review
author: conformance-review
loop_state: complete
upstream:
  - path: d51e4b1ead81ee2cc0b9d4a8307d36158e1459c8:docs/issue-2138/reports/implementation.md
    sha: d51e4b1ead81ee2cc0b9d4a8307d36158e1459c8
subject: PR #2520 (issue-2138/implementation, head d51e4b1e)
test: on-the-record/hooks/test_gate_registry.py plus the 10-file group named in PR #2520's test plan; independent live re-derivation of impact-guard.sh / accumulation-claim-guard.sh check logic, the DEMOTED set, and the unreferenced-scripts enumeration
result: passed
assertedBy: conformance-review (independent re-run, this session)
---

# issue-2138 — conformance-review record

## What was done

Independent re-derivation of PR #2520's three central claims, against
issue #2138's re-scoped acceptance criteria — not against the PR's own
account of itself. derived: `gh pr diff 2520 --name-only` (this turn) —
result:
```
docs/issue-2138/reports/implementation.md
docs/issue-2403/reports/consult-log/20260826T042513540409-3488050.md
docs/issue-2409/reports/consult-log/20260826T042513540409-3488050.md
docs/issue-2468/reports/consult-log/20260826T042513540409-3488050.md
```
Zero code changes, confirming the record's "no code change" framing; the
three consult-log files belong to unrelated issues (#2403/#2409/#2468)
from an automated skill-judge process and are orthogonal to this issue's
scope, not touched by this review. The claim under review is that no gate
registration/deletion was actually required for any of the three
re-scoped items.

**Claim 1 — impact-guard.sh and accumulation-claim-guard.sh are mechanical,
not judgment-shaped; KEEP is correct.**

canonical: read `on-the-record/hooks/impact-guard.sh` and
`on-the-record/hooks/accumulation-claim-guard.sh` in full this turn (both
files exist in this working tree, unmodified by PR #2520 — derived:
`gh pr diff 2520 --name-only` above shows neither in the diff).

- `impact-guard.sh`: canonical: `on-the-record/hooks/impact-guard.sh:82-99`
  (`_count_merge_invocations` — `shlex`-tokenizes the Bash command and
  counts literal `gh pr merge` triples) and
  `on-the-record/hooks/impact-guard.sh:102-127` (only once that count is
  >= 2 does it call `risk_report.scan_open_proposals` /
  `risk_report.batch_blocked`, classifying every currently-open proposal
  in the target repo against `docs/specs/impact-classification.md`'s
  four-axis rule). Every branch is a deterministic function of on-disk
  proposal state and command tokens; no step asks an LLM to interpret
  content.
- `accumulation-claim-guard.sh`: canonical:
  `on-the-record/hooks/accumulation-claim-guard.sh:78-97`
  (`_is_subprocess_call`, an `ast.parse` walk counting
  `subprocess.run/check_output/check_call/Popen` sites, threshold 3) and
  `on-the-record/hooks/accumulation-claim-guard.sh:113-114`
  (`_touches_shape_5`, a bare regex path match,
  `^roles/[^/]+\.json$`). The gate on either shape is
  `_has_filled_accumulation` at
  `on-the-record/hooks/accumulation-claim-guard.sh:72-76` — true iff a
  `## Accumulation` heading exists with at least one non-blank line under
  it, field presence only, no keyword/semantic check on the field's
  content, confirmed by re-reading those four lines directly this turn.
  The script's own comment states this at
  `on-the-record/hooks/accumulation-claim-guard.sh:17-18` — derived:
  `grep -n "content is never\|interpreted, contract" on-the-record/hooks/accumulation-claim-guard.sh`
  (this turn) — result:
```
17:# strengthening, issue #512 requirement 3 — content is never
18:# interpreted, contract §14) in the local working-tree proposal file for
```
  PR #2520's record cites this same comment at "lines 10-16" (canonical:
  `d51e4b1e:docs/issue-2138/reports/implementation.md`, the "Item 1"
  paragraph) — the grep result above places it at 17-18 instead, a
  citation-range miss that does not change the substance of the claim
  (the comment text itself, and the field-presence-only behavior it
  describes, are both confirmed correct by the grep above and by the
  direct read of lines 72-76).

Both checks are mechanical, matching the record's disposition. **Verdict:
Present** — KEEP is the correct disposition for both gates.

**Claim 2 — live-fire-test-guard.sh's absence from `GATES` is an
intentional DEMOTE landed in c93f744f, not a dropped registration.**

derived: `git log --oneline -- on-the-record/hooks/pretooluse_dispatcher.py`
(this turn) — result:
```
5adf3b20 issue-2210: stop 4 git-commit-detection gates from shlex-scanning heredoc body text (#2222)
128f7640 issue-2146: single-dispatcher gate execution — 20 processes -> 1 (#2149)
```
derived: `git show --stat c93f744f` (this turn) — commit message: "issue-2138:
gate retirement — RETIRE 15, DEMOTE 15 with guidance landings, registry
test (#2144)"; DEMOTE scripts are "kept on disk (unregistered) with their
tests; normative content landed in directive/*.md sections". derived:
`grep -n "DEMOTED" on-the-record/hooks/test_gate_registry.py` (this turn)
— `live-fire-test-guard.sh` is a literal entry in the `DEMOTED` set at
`on-the-record/hooks/test_gate_registry.py:113`, a set the same file's
tests assert DEMOTE scripts stay on disk and unregistered against.
**Verdict: Present** — this is the intentional-DEMOTE branch, not the
more-serious silently-dropped-registration class (#2506/#2510/#2511),
confirmed via git history and the registry test's own pinned data rather
than by trusting PR #2520's narrative.

**Claim 3 — quality-bar-gate.sh, plan-order-guard.sh,
report-framing-check.sh, decision-queue-stopgate.sh are unreferenced on
every hook event, not just PreToolUse.**

derived (independent script, not copied from PR #2520's record, written
and run this turn):
```python
import json, sys
from pathlib import Path
HOOKS_DIR = Path('on-the-record/hooks')
data = json.loads((HOOKS_DIR/'hooks.json').read_text())
sys.path.insert(0, str(HOOKS_DIR))
from pretooluse_dispatcher import DISPATCHED_SCRIPTS
registered = set()
for event, groups in data['hooks'].items():
    for group in groups:
        for hook in group['hooks']:
            tokens = hook['command'].split()
            target = tokens[1] if (Path(tokens[0]).name == 'fail-open-wrapper.sh' and len(tokens) > 1) else tokens[0]
            registered.add(Path(target).name)
dispatched = set(DISPATCHED_SCRIPTS)
targets = ['quality-bar-gate.sh','plan-order-guard.sh','report-framing-check.sh','decision-queue-stopgate.sh']
for t in targets:
    print(t, 'registered_directly=', t in registered, 'dispatched=', t in dispatched)
```
result:
```
quality-bar-gate.sh registered_directly= False dispatched= False
plan-order-guard.sh registered_directly= False dispatched= False
report-framing-check.sh registered_directly= False dispatched= False
decision-queue-stopgate.sh registered_directly= False dispatched= False
```
derived: `python3 -c "import json; print(list(json.load(open('on-the-record/hooks/hooks.json'))['hooks'].keys()))"`
(this turn) — result: `['SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop']`,
confirming the loop above iterated all five events, not only PreToolUse.
derived: `grep -rn "quality-bar-gate.sh\|plan-order-guard.sh\|report-framing-check.sh\|decision-queue-stopgate.sh" --include="*.sh" --include="*.py" on-the-record/`
(this turn) — the only hits outside the four scripts' own bodies and
their test files are comment-only cross-references in
`on-the-record/hooks/impact-guard.sh`,
`on-the-record/hooks/product-capture-stopgate.sh`,
`on-the-record/hooks/deviation-log-guard.sh`,
`on-the-record/hooks/stop-gate.sh`; none `source`/`.` these four scripts.
**Verdict: Present** — none of the four is referenced on any of the five
hook events, and none is sourced as a library by another script.

**Guidance-landing spot check.** derived:
`grep -n "demoted from" on-the-record/directive/*.md` (this turn) —
result:
```
on-the-record/directive/spawn-and-board.md:78:- EXECUTION-PLAN ORDER (issue #659, demoted from plan-order-guard.sh):
on-the-record/directive/spawn-and-board.md:84:- DECISION-QUEUE VISIBILITY (issue #466/#374, demoted from
on-the-record/directive/relay-and-reporting.md:44:- REPORT FRAMING (issue #320/#2044, demoted from
on-the-record/directive/merge-gates.md:49:- PER-ROLE QUALITY BAR (issue #1156, demoted from quality-bar-gate.sh):
on-the-record/directive/merge-gates.md:41:- LIVE-FIRE TEST FOR NEW GATES (issue #914, demoted from
```
(plus unrelated demote lines for other issues, omitted). All five
DEMOTE-15 items this issue names appear in that result. derived:
`grep -n "spawn-and-board.md\|relay-and-reporting.md\|merge-gates.md" on-the-record/hooks/directive.sh`
(this turn) — result:
```
339:  D/spawn-and-board.md.
341:  D/relay-and-reporting.md (reply structure, ordering #2043, narration
347:  D/merge-gates.md (requirement-met #1651, scope #1658, verdict #1669,
```
`directive.sh` (the actively-firing UserPromptSubmit index gate) points
sessions at all three files by name in that result. **Verdict: Present**
— the demoted rule text survives somewhere a session actually reads.

**Test-tier spot check.** derived:
`python3 -m pytest on-the-record/hooks/test_gate_registry.py -q` (this
turn) — result: `5 passed in 0.91s`, matching PR #2520's claim exactly.
derived:
`python3 -m pytest on-the-record/hooks/test_gate_registry.py on-the-record/hooks/test_impact_guard.py on-the-record/hooks/test_accumulation_claim_guard.py on-the-record/hooks/test_live_fire_test_guard.py on-the-record/hooks/test_quality_bar_gate.py on-the-record/hooks/test_decision_queue_stopgate.py on-the-record/hooks/test_report_framing_check_live.py gates/test_plan_order_blocked.py gates/test_report_framing_check.py gates/test_quality_bar.py -q`
(this turn) — result: `106 passed in 1.52s`, matching PR #2520's claim
exactly. The full fast/slow tiers were not independently re-run in this
review — canonical: `d51e4b1e:docs/issue-2138/reports/implementation.md`
"Test tiers" section reports `3417 passed`/`1100 passed` with 11 and 6
pre-existing, by-name-explained failures respectively — given the two
exact-match spot checks above; this is a stated sampling choice, not an
unstated gap.

## Why

Issue #2138's acceptance requires that PR #2520's "no code change needed"
conclusion be independently re-derivable, specifically flagging that a
silently-dropped registration (the `live-fire-test-guard.sh` question)
would be a more serious defect class (#2506/#2510/#2511) than a documented
DEMOTE. Re-deriving all three claims from the source scripts, git history,
and a from-scratch enumeration — rather than re-reading
`d51e4b1e:docs/issue-2138/reports/implementation.md`'s own narration — is
the only way to rule out that its classification of "mechanical, not
judgment-shaped" or "intentional DEMOTE, not dropped" is itself the thing
under-verified. All three held up under the independent re-derivation
shown in "What was done" above; the one non-blocking citation-range miss
found there — canonical: `on-the-record/hooks/accumulation-claim-guard.sh:17-18`
(quoted in the "What was done" section above; PR #2520 cites the same
comment as "lines 10-16") — does not change the substance of any claim.

## Upstream basis

- `d51e4b1ead81ee2cc0b9d4a8307d36158e1459c8` (PR #2520,
  `issue-2138/implementation`) — the evidence record under review:
  `d51e4b1ead81ee2cc0b9d4a8307d36158e1459c8:docs/issue-2138/reports/implementation.md`.
- `c93f744fd07aa18708c69f82d24efd23833d2708` (#2144) — the gate-retirement
  execution commit that actually disposed of the KEEP/DEMOTE/RETIRE sets
  this issue re-verifies.
- `128f7640` (#2149) — single-dispatcher collapse, amends
  `pretooluse_dispatcher.py` / the registry test's PreToolUse coverage
  check.
- `on-the-record/hooks/impact-guard.sh`,
  `on-the-record/hooks/accumulation-claim-guard.sh`,
  `on-the-record/hooks/test_gate_registry.py`,
  `on-the-record/hooks/hooks.json`,
  `on-the-record/hooks/pretooluse_dispatcher.py` — read, not modified,
  same-commit (this branch).
- `on-the-record/directive/merge-gates.md`,
  `on-the-record/directive/spawn-and-board.md`,
  `on-the-record/directive/relay-and-reporting.md`,
  `on-the-record/hooks/directive.sh` — read, not modified, same-commit
  (this branch).

## Open findings

None blocking. One non-blocking citation-precision note, canonical: the
grep result quoted under Claim 1 in "What was done" above
(`on-the-record/hooks/accumulation-claim-guard.sh:17-18`): PR #2520's
record (`d51e4b1e:docs/issue-2138/reports/implementation.md`) cites the
"content is never interpreted, contract §14" comment as "lines 10-16";
independent re-reading places that exact text at lines 17-18. The claim
itself (field-presence-only check, content never interpreted) is correct
— only the line-range pointer is off. No correction is owed in this
record since PR #2520 is a separate, already-open PR; noting it here for
whoever next touches that file's citations.

## Next steps

None. `loop_state: complete`. Recommend merging PR #2520 as-is — its
"no code change required" conclusion for all three of issue #2138's
re-scoped items is independently confirmed by the derived:/canonical:
re-derivations recorded above in "What was done" (impact-guard.sh /
accumulation-claim-guard.sh source reads, the `git log`/`git show`
history for `live-fire-test-guard.sh`, the from-scratch unregistered-scripts
enumeration script, the `grep` guidance-landing checks, and the two
exact-match pytest re-runs).

## What did not work

None.

## Skill obligations

skill-verdict: conformance-review-verdict-assignment — applied: invoked;
used to confirm Present (not Surface) was the right verdict for each of
the three claims, since each was independently re-executed/re-read rather
than merely present-on-paper.
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; used to decide the citation-precision granularity (file, line
range, command) for each derived:/canonical: line above.
skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; every one of the three claims was re-derived from the
scripts/git history/a from-scratch enumeration script rather than by
citing or trusting PR #2520's own narration of its evidence.
other mounted skills (conformance-review-requirement-extraction,
conformance-review-sampling-derivation, conformance-review-verification-method-selection,
conformance-review-finding-record, conformance-review-severity-classification):
not triggered — the task handed three pre-decomposed claims to
re-derive rather than a spec to decompose, no sampling was needed since
all three claims and both cited scripts were fully inspected, no severity
banding was requested beyond ordinary Present/Absent verdicts, and the
finding recorded here uses this file's pre-written skeleton rather than a
fresh finding-record decision.
