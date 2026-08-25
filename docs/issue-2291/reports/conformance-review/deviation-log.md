# Deviation log — issue-2291 (conformance-review role)

(Written under this role's own subtree per board-gate.sh R5 — a role
session may not write docs/issue-2291/reports/deviation-log.md directly,
only conformance-review.md and conformance-review/**.)

2026-08-25T14:20:00Z | inline | while independently probing whether PR
#2305's new spawn-attempt trace covers a halt in `spawn.py::main()`'s
pre-existing `require_acceptance_gate`/`require_requirement_linkage` gates
(R1/R3 in the review record), an unmocked probe invoked the real `spawn.py`
CLI end-to-end against a real GitHub remote with a fabricated issue number
(99999999) instead of halting where expected — acceptance: `ps aux` (this
session, captured immediately after) — result:
```
jwjung   1923350  ...  python3 -c ... spawn.main() ...
jwjung   1923351  ...  /usr/bin/python3 /tmp/pr2305-wt/spawn.py -C .../on-the-record-issue-99999999-implementation watch --issue 99999999 --role implementation ...
jwjung   1923353  ...  claude -p --settings ... --permission-mode bypassPermissions --output-format stream-json ...
```
(`pgrep -P 1923350` returned `1923353`, confirming the live `claude`
session was a child of the probe script) — full block also pasted in
docs/issue-2291/reports/conformance-review.md's "## Why"
mid-review-incident section.

canonical: this session's own follow-up `kill -TERM 1923353 1923350
1923351` then `ps -p 1923353,1923350,1923351 -o pid,cmd` (returned nothing,
exit 1) plus `git status`/`git branch -vv`/`gh pr list --search 99999999`
(confirmed no commit, no push, no PR) — same "## Why" block, same record.

Not this task's own scope (conformance-review's frozen write set is
docs/issue-2291/reports/conformance-review.md and its subtree) — an
unintended operational side effect, not a design/architecture judgment
call, so resolved inline rather than filed: killed all three related pids
within seconds of discovery (canonical above), confirmed nothing had
committed or pushed (canonical above), and removed the scratch workspace
directory (`rm -rf`, this session, confirmed empty by a follow-up
`pgrep -af 99999999`). All subsequent R1/R3/R4/R11 probing in the same
review used safe, non-CLI reproductions (direct calls to the functions
`main()` itself calls) that cannot spawn a session.
Location: session-wide (probe script, not a repo file).
