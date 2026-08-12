#!/usr/bin/env bash
# UserPromptSubmit: the role-session variant of the #958/#803 deviation
# loop (issue #983 — audit E Finding 1: the loop was structurally
# orchestrator-only, docs/issue-754/reports/defect-verification.md).
#
# Audience: a spawned ROLE session only (CLAUDE_ROLE set) — the
# orchestrator already gets the loop from directive.sh's own "YOUR
# DEVIATION LOOP" paragraph; this hook never fires there. Mirrors
# record-tiering-directive.sh's/record-claim-shape-directive.sh's
# CLAUDE_ROLE-set gate, the opposite of directive.sh's own gate.
#
# FILE-AS-ISSUE differs from the orchestrator variant: a role session
# cannot spawn a peer role or open an issue on its own initiative
# mid-task (role-handoff contract v3's SCOPE-EXCEEDED RULE) — it
# resolves to the stop-and-report a role already owes, not a `spawn.py
# spawn` call.
#
# Fails open: no CLAUDE_ROLE -> silent no-op, never blocks the turn.
# Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -n "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

cat <<'TXT'
<role-deviation-directive>
YOUR DEVIATION LOOP (issue #803, role-session variant — issue #983):
mid-task, a deviation surfaces the same way a new judgment does.
RECOGNIZE: a deviation is anything mid-task that is NOT normal task
friction — it counts only if resolving it needs something the current
task's own scope did not already call for (an edit outside the frozen
write set, a judgment a reviewer would need to weigh alternatives on, a
risk that would recur beyond this one task). A test failure the task
exists to fix, a routine lint/type error in a file already being edited,
or an expected retry is NOT a deviation. Most turns recognize zero.

CLASSIFY, only once RECOGNIZE fires: INLINE-FIX iff ALL hold — (a) stays
inside the frozen write set, (b) mechanical (no design/architecture/
security/product judgment), (c) does not change what the deliverable
claims to do, (d) a one-off, not a recognizable systemic pattern.
Otherwise FILE-AS-ISSUE.

RESOLVE-AND-CONTINUE:
- Inline: apply the fix, append one line to the deviation log
  (docs/issue-<n>/reports/deviation-log.md when this session is
  issue-scoped, else docs/reports/deviation-log.md) — timestamp,
  `inline`, one-line description, the diff's location; resume the
  original task same turn.
- File case: a role session never spawns a peer role or opens an issue
  mid-task on its own initiative (SCOPE-EXCEEDED RULE) — finish what the
  frozen write set covers, STOP, report the deviation plainly in this
  turn's reply for the orchestrator/next role to act on, and append one
  `filed` line to the same deviation log — timestamp, `filed`, one-line
  description, "reported, not spawned". Do not call spawn.py from inside
  this session for this purpose.

Every deviation, inline or filed, leaves exactly one traceable log
entry — no entry for non-deviations. Enforced at Stop by
deviation-log-guard.sh, which now binds in role sessions too. Full
format: docs/handbooks/deviation-loop.md.
</role-deviation-directive>
TXT

trap - EXIT
exit 0
