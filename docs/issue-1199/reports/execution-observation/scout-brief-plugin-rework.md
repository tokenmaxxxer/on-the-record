# Scout brief — Claude Code plugin/skill ecosystem (2026-08-14 amendment rework)

Mode: batched-sequential WebSearch + WebFetch + `curl` (GitHub API), one session, no
parallel subagent fan-out (task scope did not warrant it). Stages: 1 sweep (2 WebSearch
queries) + 1 deepening (3 WebFetch reads + 3 `curl` star lookups) = 2 stages, well under
the 5-stage/3min budget.

Segment: this role's whole deliverable is verdict-writing over evidence (PR diffs,
commits, records) — the matching plugin segment is Claude Code skills/plugins for PR
review, verification-before-completion, and evidence discipline, not general dev tools.

## Surveyed plugins (adoption evidence: GitHub stars, fetched this session)

- **obra/superpowers** — `"stargazers_count": 271747` (canonical: `curl -s
  https://api.github.com/repos/obra/superpowers`, run this session),
  https://github.com/obra/superpowers. Problem: coding agents claim completion without
  verifying it. How: "Evidence over claims" as a stated core philosophy — a dedicated
  verification-before-completion skill makes test/review artifacts mandatory waypoints,
  never trusting an agent's own assertion of done (fetched
  https://raw.githubusercontent.com/obra/superpowers/main/README.md this session).
- **aidankinzett/claude-git-pr-skill** — `"stargazers_count": 44` (canonical: `curl -s
  https://api.github.com/repos/aidankinzett/claude-git-pr-skill`, run this session),
  https://github.com/aidankinzett/claude-git-pr-skill. Problem: PR feedback posted in
  haste skips human sign-off. How: a strict three-stage draft → review-and-approval →
  post workflow; nothing reaches GitHub until the exact planned content is shown and
  explicitly confirmed (fetched
  https://raw.githubusercontent.com/aidankinzett/claude-git-pr-skill/main/README.md this
  session).
- **tag1consulting/claude-comprehensive-review** — `"stargazers_count": 7` (canonical:
  `curl -s https://api.github.com/repos/tag1consulting/claude-comprehensive-review`, run
  this session), https://github.com/tag1consulting/claude-comprehensive-review. Problem:
  single-perspective review both misses issues and drowns real ones in noise. How: seven
  parallel specialist agents each score findings 0-100 confidence, normalize severity
  across agents into one taxonomy, and a "blind-hunter" agent reviews the raw diff with
  zero repo context to catch what familiarity blinds the others to (fetched
  https://raw.githubusercontent.com/tag1consulting/claude-comprehensive-review/main/README.md
  this session).

## Gap line
Current rulebook already has diff-scope citation admissibility and a `mode`
(read/command/asserted) field (landed via the prior, now-superseded domain-tool survey,
commit 67049c6). It does NOT yet: (a) distinguish confidence by evidence mode inside the
verdict prose itself — `mode: asserted` only gates the *result* enum today, not how the
verdict sentence reads; (b) require reading the observed artifact fresh before reading
the observed role's own narrative summary of itself, risking anchoring on that role's
self-report.

## Adopt / skip
- Adopt: superpowers' "evidence over claims" framing → verdict prose for an
  `asserted`-mode claim must say so inline ("unverified, per the observed role's own
  record"), not just restrict its result enum.
- Adopt: tag1's zero-context/blind-hunter ordering → read the observed PR's diff and
  commits before reading the observed role's own record narrative, so the scope
  statement is built from the artifact, not anchored on the artifact's own author's
  framing of it.
- Skip: claude-git-pr-skill's interactive draft/approve/post loop — this role's phase
  gating (contract v3 s19) already supplies an equivalent human-approval boundary at a
  different layer; duplicating it inside the directive would be redundant, not additive.

Sources:
- https://github.com/obra/superpowers
- https://raw.githubusercontent.com/obra/superpowers/main/README.md
- https://github.com/aidankinzett/claude-git-pr-skill
- https://raw.githubusercontent.com/aidankinzett/claude-git-pr-skill/main/README.md
- https://github.com/tag1consulting/claude-comprehensive-review
- https://raw.githubusercontent.com/tag1consulting/claude-comprehensive-review/main/README.md
