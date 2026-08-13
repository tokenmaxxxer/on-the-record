# Current-state survey: execution-observation for issue #1174

## Scope statement
Observed role: `pr-communications`, its issue-#1174 fan-out unit (the
"operational playbook" program, requirement northpole req#1/req#5).

Observed artifacts, read in full this session:

- on-the-record PR #1218.
  canonical: `gh pr view 1218 --json number,title,mergedAt,commits,files`
  (run this session) — result: title `[issue-1174/pr-communications]`,
  mergedAt set (non-null), one commit
  `99a42ec0fdb9f6f04dda766c4a4967e3cdab5faa` ("issue-1174:
  pr-communications operational playbook evidence trail"), two files
  added under `docs/issue-1174/reports/pr-communications/`.
- That commit's own record file.
  canonical: `git show 99a42ec0:docs/issue-1174/reports/pr-communications/playbook-evidence-trail.md`
  (run this session, full file read) — result: file content quoted/
  summarized in the "Independent reproduction" section below; the
  companion `docs/issue-1174/reports/pr-communications/scout-brief.md`
  exists in the same commit per the file list cited above.
- The rulebook-repo artifact the evidence trail points at.
  canonical: `gh pr view 19 --repo tokenmaxxxer/pr-communications-rulebook --json number,state,url,mergedAt,files`
  (run this session) — result: `state: MERGED`, one file added
  `playbook/message-planning-and-evaluation-rules.md`.
  canonical: `git clone https://github.com/tokenmaxxxer/pr-communications-rulebook.git /tmp/prc-rb && git -C /tmp/prc-rb log --oneline -3 -- playbook/`
  (run this session) — result: commit `187048e` "issue-1174: add
  operational playbook (message planning, approval, Q&A, evaluation
  rules)".

## What was read to arrive at this scope
canonical: `gh issue view 1174` and `gh issue view 1174 --comments`
(both run this session, full 174-comment thread read) — result: the
program's fan-out structure (one branch/PR per role under issue #1174)
and the list of merged fan-out-unit PR numbers.

canonical: `git log --oneline -5` (run this session) — result: top
entry `c1d341b Merge pull request #1218 from
tokenmaxxxer/issue-1174/pr-communications`, i.e. PR #1218 is the most
recently merged fan-out unit on `main` at survey time. It was selected
as the observation target on that basis, plus its record and rulebook
PR both being independently reproducible (see below).

canonical: `gh pr list --repo tokenmaxxxer/on-the-record --head issue-1174/execution-observation --state all --json number,state,url`
(run this session) — result: empty array — no prior PR of my own
exists yet, so this survey is this role's first phase-1 output on this
issue.

## Independent reproduction (this session, not the observed role's claim alone)
canonical: commands below, executed this session against the cloned
rulebook file at `/tmp/prc-rb/playbook/message-planning-and-evaluation-rules.md`:
```
$ grep -cE '^[0-9]+\.' playbook/message-planning-and-evaluation-rules.md
13
$ grep -c '\*\*REMOVAL' playbook/message-planning-and-evaluation-rules.md
3
```
result: matches the evidence trail's claimed 13 numbered rules / 3
REMOVAL rules exactly.

canonical: `python3 gates/playbook_depth_gate.py /tmp/prc-rb/playbook/message-planning-and-evaluation-rules.md --role pr-communications --floor 12 --axes objective-channel-fit,message-hierarchy,approval-sequencing,risk-qa-prep,evaluation-criteria,persuasion-technique`
(run this session) — result:
```
role=pr-communications accepted=12 floor=12 count_ok=True
PASS
```
matching the evidence trail's claimed gate output field-for-field
(same accepted/floor values, same final line, same two rejected
non-rule lines "Counter-example" and "Open gap").

Scope limit of this reproduction: it checks rule count, REMOVAL count,
and the gate's accept/reject shape only (per the gate output quoted
directly above). It does not verify that the four cited source URLs
actually support the specific rule content attributed to them —
listed below as unchecked, not asserted either way.

## What has not yet been checked (deferred to phase 2)
- Whether a *live* role session actually cites a specific playbook rule
  in a judgment (issue #1174 acceptance check 5, "executed-live").
  Not checked this session — no such citation was searched for yet.
- Whether the four fetched-source URLs in the evidence trail actually
  support the specific rules attributed to them (spot-check of
  citation accuracy, not just citation presence).
- Whether `docs/issue-1174/proposals/operational-playbook-program.md`
  (the evidence trail's stated "Upstream basis") was itself validly
  approved before this fan-out unit built directly (single commit, no
  visible phase-1 proposal PR of its own) — i.e., whether the
  contract v3 s19a build-now bypass was applicable to this unit and,
  if so, on what authorization.
