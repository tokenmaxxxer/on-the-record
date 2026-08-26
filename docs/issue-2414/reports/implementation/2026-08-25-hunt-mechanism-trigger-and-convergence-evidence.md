---
proposal: docs/issue-2414/reports/implementation.md
---

# Hunt record — mechanism-trigger-and-convergence-evidence

## before-landing — stance 1: bypass or false-block bug in the two new acceptance_gate.py/requirement_met.py checks

Verdict: FINDING — `_MECHANISM_TRIGGER` in `gates/acceptance_gate.py` only matches present-tense/base/-ing verb forms; it silently fails to match the past-tense/passive forms ("pruned", "purged", "retired", "rotated", "refused", "rejected", "denied") that are the ordinary way an Ask/Acceptance section describes an already-specified mechanism, so a mechanism-adding issue written in passive voice passes with zero `must not:` requirement while the identical issue in present tense is correctly blocked.
Kind: silent-failure
Seed: gates/acceptance_gate.py (uncommitted working-tree diff vs HEAD, `_MECHANISM_TRIGGER` regex + its wiring into `check_issue_body`)
cap_seconds: n/a (not provided by dispatcher)
tier: n/a (not provided by dispatcher)
diff_stat_lines: n/a (not provided by dispatcher; `gates/acceptance_gate.py` diff alone is ~34 added lines)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:20:00Z

### Reproduce
```
python3 -c "
import sys
sys.path.insert(0, 'gates')
import acceptance_gate as ag

body = '''## Ask

Expired session tokens are pruned from the sessions table on every login
attempt, so the table does not grow without bound.

## Acceptance

- \`check: gates/test_session_prune.py\`
- empty state: sessions.jsonl absent -> gate skips
- provenance: executed-live
'''

print('violations:', ag.check_issue_body(2999, body))
"
```

### Observed
```
violations: []
```
The gate passes cleanly (no `must not:` field required), even though the
Ask section plainly describes a prune mechanism with no stated boundary.
Changing only the verb's tense/voice — "pruned" -> "prunes" — in the same
sentence flips the verdict:
```
python3 -c "
import sys
sys.path.insert(0, 'gates')
import acceptance_gate as ag

body = '''## Ask

The mechanism prunes expired session tokens from the sessions table on every
login attempt, so the table does not grow without bound.

## Acceptance

- \`check: gates/test_session_prune.py\`
- empty state: sessions.jsonl absent -> gate skips
- provenance: executed-live
'''

print('violations:', ag.check_issue_body(2999, body))
"
```
produces one blocking violation demanding a `must not:` line. The only
difference between the two bodies is grammatical form of the same verb
describing the same mechanism.

Root cause: the `_MECHANISM_TRIGGER` alternation gives inconsistent tense
coverage per verb —
`append(?:s|ed|ing)?` and `force[- ]remov\w*` cover all inflections, but
`prunes?`, `purges?`, `retir(?:e|es|ing)`, `rotates?`, `refuses?`,
`rejects?`, and `den(?:y|ies)` all omit the past-tense/passive form
("pruned", "purged", "retired" [as adjective already excluded by design,
but "retired" as past-tense verb too], "rotated", "refused", "rejected",
"denied"). Confirmed directly against the regex:
```
python3 -c "
import re
_MECHANISM_TRIGGER = re.compile(
    r'\b(append(?:s|ed|ing)?|prunes?|pruning|purges?|retir(?:e|es|ing)|'
    r'rotates?|refuses?|rejects?|den(?:y|ies)|force[- ]remov\w*)\b',
    re.IGNORECASE)
for t in ['the old records were pruned', 'the log file is purged nightly',
          'access is denied to expired tokens',
          'requests are rejected past the deadline',
          'stale keys are retired', 'credentials are rotated weekly',
          'the request was refused']:
    print(t, '->', bool(_MECHANISM_TRIGGER.search(t)))
"
```
prints `False` for every one of those seven ordinary, realistic sentences.

### Expected
Per the code's own stated design intent (comment directly above
`_MECHANISM_TRIGGER`: "catching mechanism verbs that live in the '## Ask'
section", and the docstring's framing of `#2291`'s original incident text
as the motivating case), an issue whose Ask/Acceptance text describes a
prune/purge/retire/rotate/refuse/reject/deny mechanism — regardless of
whether it is phrased in present tense ("prunes") or the equally common
passive/past-tense phrasing ("is pruned" / "was pruned") — should trip the
same `must not:` requirement. Instead, the passive/past-tense phrasing is a
silent false negative: the exact failure mode (#2291/#2393-style
mechanism with no stated negative criteria) that this gate exists to catch
sails through undetected whenever the issue author happens to write in
passive voice, which is a common register for describing existing/planned
system behavior.
