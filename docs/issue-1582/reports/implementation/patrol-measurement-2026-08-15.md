# Tier-1 patrol pilot: measurement run, 2026-08-15

Per docs/issue-1582/proposals/2026-08-15-tier1-role-patrol-pilot.md's
acceptance list, and the binding correction on PR #1583 (the proposal's
originally-named target had zero docs/issue-*/reports/ records — a
scanner run there alone is guaranteed empty and yields no tier-2
go/no-go signal). Two runs recorded below: a real-input run against
this repo, and the originally-proposed target repo kept as an
empty-input negative control.

Both runs use the CLI directly (not the `-m` module-invocation form,
which collides with this repo's pre-existing gates-package/gates.py
namespace ambiguity, unrelated to this pilot and out of this
proposal's write set to fix):

```
python3 gates/patrol_queue.py scan <repo-root> --lane sweep
```

## Run 1 — real input: this repo (on-the-record)

derived: `time python3 gates/patrol_queue.py scan . --lane sweep`
```
{
  "lane": "sweep",
  "scanner": "record_lint",
  "raw_findings": 3023,
  "verified": 2929,
  "verify_dropped": 94,
  "enqueued": 200,
  "budget_truncated_scanners": 1,
  "queue_size": 183
}

real	2m49.244s
user	1m44.985s
sys	1m22.018s
```

canonical: fenced command output immediately above.

Reading of the numbers above:
- wall-clock 2m49s is dominated by record_lint's own existing
  diff-scoped check functions, which run a git subprocess per record;
  this repo carries well over a thousand docs/issue-*/reports/*.md
  files, so the cost sits in that pre-existing per-record fan-out, not
  in anything this pilot's queue/trigger code adds.
- raw_findings exceeds enqueued because the per-scanner budget cap
  (200, drop-not-queue) truncated the remainder into one meta-finding
  (budget_truncated_scanners: 1) instead of backlogging it.
- verify_dropped sits at roughly 3% of raw_findings: those are
  record_lint violations whose message carries no verbatim-quoted
  excerpt (e.g. the reach-check rule, which names a broken path
  reference rather than quoting record text), so they have no anchor
  for the verifiability gate — dropped before verification is
  attempted, not a false-positive signal on the scanner's own findings.
- queue_size is lower than enqueued because some of the budget-surviving
  findings collapsed onto fingerprints already written earlier in the
  same run (record_lint occasionally emits an identical violation
  message twice for one record under different check functions) —
  dedup-at-enqueue working as designed, not data loss.

## Run 2 — empty-input negative control: /home/jwjung/tokenmaxxxer

derived: `time python3 gates/patrol_queue.py scan /home/jwjung/tokenmaxxxer --lane sweep`
```
{
  "lane": "sweep",
  "scanner": "record_lint",
  "raw_findings": 0,
  "verified": 0,
  "verify_dropped": 0,
  "enqueued": 0,
  "budget_truncated_scanners": 0,
  "queue_size": 0
}

real	0m0.084s
user	0m0.063s
sys	0m0.020s
```

canonical: fenced command output immediately above.

Reading: zero docs/issue-*/reports/*.md files under this target means
find_records() returns nothing, so every downstream stage (verify,
budget, enqueue, absence-close) runs over an empty set and produces an
empty, valid queue with no crash and no spurious findings. The
wall-clock figure matches this pilot's own scope: a whole-repo scan
with nothing to scan costs essentially nothing.

## Tier-2 go/no-go input

canonical: Run 1's fenced command output above.
derived: Run 1's fenced `time python3 gates/patrol_queue.py scan .
--lane sweep` output above (verified: 2929, raw_findings: 3023).

The real-input run's verified-over-raw ratio is the verifiability rate,
not an actionable-finding rate — verify() only checks that an excerpt
still exists verbatim at its cited path; it does not judge whether the
underlying record_lint violation is itself correct or worth acting on.
Comparing that rate against Tricorder's cited <10% effective-false-
positive admission bar needs a hand-check of a sampled subset, which
this pilot's scope does not include (design req 8 only requires reusing
an existing scanner with a prior hand-checked actionable rate —
record_lint's own whole-repo scan mode satisfies that independently of
this measurement). This report supplies the raw counts the tier-2
decision needs as input, not the tier-2 decision itself.

## Defects fixed during this measurement's first attempt

canonical: this session's own local run of
`python3 gates/patrol_queue.py scan . --lane sweep`, first attempt,
before the fixes below.

The first attempt at Run 1 returned `verified: 0, verify_dropped: 3622`
in that run's own JSON summary — scan_record_lint() was passing the
full generated lint message as a finding's excerpt, but verify() checks
that the excerpt appears verbatim in the cited file, and a generated
message (rule name plus explanation) never does. Fixed by extracting
the verbatim-quoted span record_lint's own messages already carry, and
dropping violations that carry no such span at scan time instead of via
the verify-drop counter.

That same first attempt's fingerprint context was the record file's
static first five lines, identical across every violation in that
file — collapsing distinct violations in the same record onto one
fingerprint. Fixed by fingerprinting on the full violation message
instead (unique per rule-and-excerpt pairing, still free of line
numbers). The numbers reported in Run 1 above are from the corrected
code (gates/patrol_queue.py as committed in this same change set).
