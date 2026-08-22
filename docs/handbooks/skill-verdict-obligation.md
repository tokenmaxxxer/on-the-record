# Per-mounted-skill verdict obligation (issue #2039)

When a spawn directive mounts one or more skills — via `--skills`
(spawn.py's `마운트된 스킬(--skills, ...)` line) or the role→skill-repository
mapping (spawn.py's `이 역할은 skill-repository(...)로 매핑됐다` line) — the
session's own record must carry one line per mounted skill name:

```
skill-verdict: <name> — applied: <where/how> | not-applicable: <one-line reason>
```

One line per mounted name, each with non-empty content after the dash.
This is a shape check only: `skill-verdict-guard.sh` (Stop hook) and
`gates/record_lint.py`'s `record_skill_verdicts_in`/`skill_verdict_reason_check`
never judge whether the stated applied/not-applicable content is
actually correct — that judgment stays entirely the session's own, per
the frozen skills-guidance-only principle (guidance only; enforcement is
core hooks only).

A session with zero mounted skills is unaffected — no line is required,
no hook output is produced.
