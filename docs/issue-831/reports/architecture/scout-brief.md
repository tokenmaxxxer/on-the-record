---
subject: issue-831
kind: scout-brief
role: architecture
status: skipped
---

# Scout brief (architecture role) — issue #831 step 2 — SKIPPED

Scouting skipped. Skip condition: no design decision open at the field/
product level remains for this step.

canonical: `docs/issue-831/reports/product-discovery/scout-brief.md` (read this session)
The phase-1 product-discovery scout pass already ran the field sweep for
the decision that has external-practice bearing (which candidate
direction matches how responsible 2026 agentic tools gate invasive/
irreversible actions).

canonical: `docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md` "Recommendation" section (read this session)
That decision is settled there (candidate c, phase-1 proposal).

What remains for this step is purely internal: which `spawn.py` call
sites to gate ahead of `issue_workspace`, and which already-existing
internal signal (`--unattended` vs. `sys.stdin.isatty()`) to key the gate
on. Neither question has an external field/product analogue to scout —
it is resolved by reading `spawn.py`'s own call graph and existing
conventions, done in
`docs/issue-831/reports/architecture/survey.md` and settled in
`docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md`'s
"Alternatives considered" section.
