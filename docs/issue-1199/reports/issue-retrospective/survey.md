---
subject: issue-1199
role: issue-retrospective
kind: survey
loop_state: gathering
---

# Current-state survey (issue-1199, issue-retrospective tool-landscape unit)

Read basis (records-only, per this role's own contract): every sibling
tool-landscape fold-in record already landed under this subject's own
tree, to avoid re-deriving the applied-not-referenced and
no-tool-attribution amendments those sessions already discovered the
hard way.

canonical: `docs/issue-1199/reports/brand-design.md`, read this session
- Exemplar named in the issue's problem statement: rulebook edits go
  into the separate `<role>-rulebook` repo, on-the-record carries only
  the record; no tool-repo names or `source:` links inside the public
  rulebook.

canonical: `docs/issue-1199/reports/interaction-design.md`, read this
session
- Same pattern, additionally shows the applied-not-referenced bar being
  met (edits landed in `directive.sh` and a `playbook/*.md` file in the
  same delivery, not a separate unread pointer file).

canonical: `docs/issue-1199/reports/technical-writing.md`, read this
session (its own "Retrofit" section)
- Records a retrofit: this unit's first delivery (PR #26) only
  *referenced* its named upgrade targets without editing them, and its
  second delivery still carried tool-repo names/`source:` links inside
  the public rulebook until a further operator amendment
  (issuecomment-5276881749, cited in that same file) forced their
  removal.

canonical: `docs/issue-1199/reports/ux-engineering.md`, read this
session
- Same no-attribution pattern confirmed a third time; also notes the
  issue's 43-item tracker has no discoverable editable artifact to
  check off from a role session's write scope.

canonical: `docs/issue-1199/reports/implementation.md`, read this
session (its "Rationale for deviations" / "Resolution path" sections)
- Step-1 verification infra (`gates/tool_learnings_gate.py`,
  `gates/tool_learnings_tracker.py`) landed; also documents a
  `gh pr create` reconcile-then-retry deadlock against an external
  judgment-watcher that reposts an "escalate" comment every 10-40s,
  with the established fallback: stop retrying after repeated
  fresh-comment collisions, since commit+push to the target repo is the
  actual deliverable and PR-open can relay externally.

## Gap this unit fills

canonical: `find docs/issue-1199/reports -maxdepth 1 -type f`, run this
session — no `issue-retrospective.md` file existed at survey time
None of the five records above is for the `issue-retrospective` role
itself.

canonical: `issue-retrospective/hooks/directive.sh` in
`tokenmaxxxer/issue-retrospective-rulebook`, read this session
This role's own rulebook (mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/issue-retrospective-rulebook`)
encodes blameless-postmortem methodology (timeline-before-judgment,
plural contributing factors, advisory-only action items) but had not
been checked against how widely-adopted incident-postmortem tooling
operationalizes those same principles.

## Recurred-prediction check (this role's own use_when exemplar)

canonical: `docs/issue-1174/reports/issue-retrospective.md`, read this
session (this repo's only other file matching `docs/issue-*/reports/
issue-retrospective.md`)
That record retrospects issue #1174 and names no failure mode matching
this unit's own subject matter (tool adoption evidence, native fold-in,
no-attribution) — issue-1174 predates issue #1199, so it could not have
predicted #1199's own amendments. No recurred prediction applies.

canonical: `issue-retrospective/hooks/directive.sh` (`use_when` field)
in `tokenmaxxxer/issue-retrospective-rulebook`, read this session
That directive's recurred-prediction question governs a closed
subject's retrospective record, not this still-open fan-out unit; the
nearest usable precedent is the apply-not-reference / no-attribution
pattern the five sibling records above already document (each cited
above), which this unit follows directly.
