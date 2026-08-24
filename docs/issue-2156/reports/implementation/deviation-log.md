# Deviation log — issue-2156/implementation

(Written under this role's own subtree per board-gate.sh R5 — a role
session may not write docs/issue-<n>/reports/deviation-log.md directly,
only <role>.md and <role>/**.)

canonical: on-the-record/directive/spawn-and-board.md (this commit's diff)
2026-08-24T15:01Z | inline | before-landing warrant-hunter (stance 0)
found the first wording draft of the new spawn-and-board.md rule scoped
its prohibition to the `Agent` tool only, letting a `Bash
(run_in_background)` sleep-and-poll loop reproduce the exact forbidden
pattern — reworded to prohibit the standing-loop pattern regardless of
mechanism before landing, same commit. Location:
on-the-record/directive/spawn-and-board.md (diff, "NO REDUNDANT WATCHER,
BY ANY MECHANISM" block); full detail in
docs/issue-2156/reports/implementation/2026-08-24-hunt-spawn-watcher-guidance.md
and the implementation record's `## What did not work` section.
