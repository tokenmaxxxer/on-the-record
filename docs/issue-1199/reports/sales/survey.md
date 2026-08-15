# sales — current-state survey (issue #1199, plugin-ecosystem round)

Subject: issue-1199. Scope: `tokenmaxxxer/sales-rulebook`, mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/sales-rulebook` (main branch).
canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/sales-rulebook
log --oneline -5`, read this session.

## Existing methodology plugins (four)

- `sales-proposal-norm` — phase-1 proposal shape gate. Not in scope for
  this round (phase-1 proposal shape has no plugin-adoption angle).
- `sales-qualification-meddpicc` — MEDDPICC (default) / BANT (fallback)
  qualification. canonical: `sales-qualification-meddpicc/README.md`,
  read this session — 7 required fields checked for presence-or-explicit-
  unknown; Economic Buyer and Champion additionally required to be
  named individuals before advancement. No rule ties a field's value to
  the observable evidence behind it, and no rule places a named
  Economic Buyer/Champion inside a wider buying-committee map.
- `sales-stage-definitions` — 5-7 stages, >=2 falsifiable past-tense
  exit criteria per stage, named next-stage handoff, `Deal state:`
  5-word vocabulary. canonical:
  `sales-stage-definitions/README.md`, read this session.
- `sales-playbook` — five required sections (process overview,
  qualification framework, ICP/persona, objection-handling, metrics),
  marketing hand-off boundary. canonical: `sales-playbook/README.md`,
  read this session — objection-handling is required as a section but
  the methodology has no rule that recurring objections across deals
  get tracked as a pattern set rather than restated per-deal.

## Required fields (qualification-meddpicc, current)

canonical: `sales-qualification-meddpicc/README.md`, read this session
— Metrics, Economic Buyer, Decision Criteria, Decision Process,
Identify Pain, Champion, Verdict (7 required); Paper Process,
Competition (2 optional, must carry a value if declared).

## Prior plugin-ecosystem survey

canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/sales-rulebook log --all --oneline
--grep=plugin -i`, read this session — the matching commits (#8/#9/#11/
#12/#17/#18) all concern this repo's OWN plugin set (methodology
enforcement, gate remediation); none surveys the external Claude Code
plugin/skill ecosystem. This is the first external-plugin-ecosystem
round for `sales`.
