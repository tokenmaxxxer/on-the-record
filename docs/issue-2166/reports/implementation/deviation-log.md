# Deviation log — issue #2166

- 2026-08-24T00:00:00Z | inline | issue #2166's finding names issue-527
  as the interaction-design-role session that mounted `work-in-english`,
  implying its literal task text should ground the reproduction the same
  way issue-525's did for `market-analysis-mece-proposal`.
  derived: `gh issue view 527 --json title,body -R tokenmaxxxer/on-the-record` — result: an unrelated write_scope-split proposal (title `docs(issue-523): phase-1 proposal — technical-writing/devrel write_scope split`).
  derived: `gh issue view 527 -R tokenmaxxxer/tm-dicequest` — result: `GraphQL: Could not resolve to an issue or pull request with the number of 527.`
  Issue-527's actual text could not be recovered from either local
  product checkout. Substituted a direct code/data reproduction of the
  same mechanism instead — declared-phrase extraction plus BM25 rank
  measurement against issue-525's real text, recorded in
  `docs/issue-2166/reports/implementation.md` — which does not depend on
  that specific session's text. Stays inside this session's frozen
  write set (the record documents the substitution and both lookups
  above), no design/architecture/security judgment beyond picking an
  available stand-in input, does not change what the delivered fix
  claims to do, one-off (a single unresolvable citation, not a
  recurring pattern).
