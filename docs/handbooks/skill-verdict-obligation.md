# Per-invoked-skill verdict obligation (issue #2039, scoped by issue #2153)

When a spawn directive mounts one or more skills — via `--skills`
(spawn.py's `마운트된 스킬(--skills, ...)` line) or the role→skill-repository
mapping (spawn.py's `이 역할은 skill-repository(...)로 매핑됐다` line) — the
session's own record must carry one line per skill it actually **invoked**
via the Skill tool this session:

```
skill-verdict: <name> — applied: <where/how> | not-applicable: <one-line reason>
```

One line per invoked name, each with non-empty content after the dash.
A mounted skill the session never invoked owes no per-skill line at all —
a "not-applicable" row for a skill that was never even considered closely
enough to invoke answers no audit question (issue #2153's live
measurement: 17 of 19 mounted skills got a ceremonial "not used" row
though only 1-2 ever fired).

Issue #2681/#2893: a session that invokes **none** of its mounted skills
is a distinct, checked case, not a silent no-op. The Stop hook
(`skill-verdict-guard.sh`) always surfaces an advisory zero-invocation
notice in that case (issue #2681), and the session's own record must
additionally carry one summary line: `other mounted skills: not
triggered` (issue #2893 — this line was optional before #2893; the hook
now folds a reminder into its advisory notice when the record is missing
it, `gates/record_lint.py`'s `zero_invocation_summary_check`). The
summary line does not claim any mounted skill was appropriate or
inappropriate — it only records that the session actually checked the
mounted list against the task, closing the gap where "correctly judged
nothing applied" and "never considered the list at all" produced the
same (silent) record.

This is a shape check only: `skill-verdict-guard.sh` (Stop hook) and
`gates/record_lint.py`'s `record_skill_verdicts_in`/`skill_verdict_reason_check`/
`zero_invocation_summary_check` never judge whether the stated applied/
not-applicable/not-triggered content is actually correct — that judgment
stays entirely the session's own, per the frozen skills-guidance-only
principle (guidance only; enforcement is core hooks only). Every check
here is advisory (`additionalContext`), never `decision: "block"`.

Invocation is detected from the full session transcript: an assistant
`tool_use` block named `Skill` whose `input.skill` names a mounted
skill. A session with zero mounted skills is unaffected — no line is
required, no hook output is produced.
