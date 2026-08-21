# Current-state survey — issue #1750 (keep-role precision sample)

Scout-directive skip: this task's design-research-skip label is `mechanical`
and assumptions-skip is `mechanical` — the issue leaves no design decision
open (the sampling rule, sample size, script-fetch method, and the
precision threshold are all specified verbatim in the issue text, nothing
left undecided). Scouting is skipped per the scout-directive's first skip
condition (spec leaves no design decision open); this is the mandatory skip
record.

## Source report

`docs/reports/rulebook-hook-audit.md` (issue #1746 delivery) is a 630-line
Markdown table-per-rulebook audit classifying every hook across 44 rulebook
repos as `promote` / `keep-role` / `retire`.

derived:
```
grep -n '| keep-role |' docs/reports/rulebook-hook-audit.md | awk -F'|' 'NF==8' | wc -l
```
Result: 307 keep-role hook rows (one extra `NF==4` match is the summary
table's `| keep-role | 307 |` count row, correctly excluded by the `NF==8`
filter that isolates the 8-column per-hook table rows).

## Sampling rule (frozen by the issue, not a design choice)

Every 15th keep-role row by report order (1-indexed among the 307 keep-role
rows only, not among all 314 hooks), starting at index 1, wrapping if it
overruns — i.e. indices `1 + 15k` for k=0..19. Applied via:
```
grep -n '| keep-role |' docs/reports/rulebook-hook-audit.md | awk -F'|' 'NF==8' \
  | nl -ba | awk 'NR==1 || (NR-1)%15==0 {print}'
```
This yields indices 1, 16, 31, 46, 61, 76, 91, 106, 121, 136, 151, 166, 181,
196, 211, 226, 241, 256, 271, 286 — twenty values, no wraparound needed
since 1+15*19=286 is still <= 307.

## Full-script fetch mechanism

For each sampled row, the rulebook repo name (from the nearest preceding
`### <repo>` heading) plus the plugin/hook-file columns identify a candidate
path. `gh api repos/tokenmaxxxer/<repo>/git/trees/main?recursive=true` was
fetched once per distinct repo (20 repos, one call each) to resolve the
exact `<plugin>/hooks/<file>` path, then
`gh api repos/tokenmaxxxer/<repo>/contents/<path> --jq '.content' | base64 -d`
retrieved the full script body. One sample (data-engineering's
`failure-handling-gate.sh`) is a thin bash entrypoint whose actual check
logic lives in a sibling `.py` file — the audit's own methodology note
documents this thin-wrapper pattern, so that file needs fetching too for the
re-judgment to read actual check content rather than the wrapper.

## What the audit's classification rule already documents

The audit's `## Methodology` section states one explicit exception: a hook
is classified `keep-role` "unless the check content itself restates a
role-handoff-contract-wide (not domain-wide) requirement" — in which case it
lists candidates for `promote` from implementation-rulebook
(`proposal-shape`, `record-shape`, `survey-order`, all restating contract
v3 s19/s20's generic phase-1/phase-2 shape). This exception is the operative
test for re-judgment: does the sampled hook's actual check content encode
domain-specific methodology (ISO 31000, MQM, BATNA/ZOPA, Fowler's catalog,
etc.), or does it restate a generic cross-role norm (phase ordering,
generic ADR spine, anti-vendoring/citation discipline) that already exists,
or could exist, as one core mechanism?
