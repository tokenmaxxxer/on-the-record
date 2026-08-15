kind: report
subject: issue-1199
doc-type: reference

# defect-verification — Claude Code plugin/skill scout brief (2026-08-14 amendment)

canonical: WebSearch results this turn (queries: "Claude Code plugin
skill marketplace debugging bug reproduction testing github stars
2026"; "\"claude code\" plugin skill QA test failure triage
reproduction github marketplace"; "claude code skill systematic
debugging OR root-cause"), plus `gh api` stargazer/tree lookups against
`anthropics/claude-plugins-official`, `LerianStudio/ring`, and
`awesome-skills/5-whys-skill` this turn — full list under Sources.

## Skip record

Not skipped — scouting ran (3 sweep angles: general plugin/skill
marketplace debugging coverage, QA/test-failure-triage-specific, and a
targeted "systematic debugging" repo search), followed by 1 deepening
round reading `pr-review-toolkit`'s and `5-whys-skill`'s own READMEs.
4 stages total, within the 5-stage/3min budget.

## Category must-bes (from sweep)

canonical: `gh api repos/anthropics/claude-plugins-official --jq
'.stargazers_count, .forks_count'` this turn -> `33504`, `3786`.

- Anthropic's own official plugin marketplace
  (`anthropics/claude-plugins-official`) carries a dedicated
  `pr-review-toolkit` plugin bundling per-concern review agents,
  including one scoped specifically to test-coverage quality and one
  scoped specifically to silent-failure detection — both directly
  adjacent to this role's job, at the highest-adoption tier available.
- A standalone root-cause-analysis skill pattern (5-Whys) is popular
  enough as an installable Claude Code skill to exist as its own
  repo, distinct from general debugging assistants.
- The broader devrel-surveyed finding holds here too: marketplace
  breadth (6,364 plugins / 549 marketplaces per aggregator sites) is
  real, but adoption evidence concentrates on a small number of
  official/high-star entries, not the long tail.

## Performance axes (dimensions the field competes on)

canonical: `gh api repos/anthropics/claude-plugins-official/contents/plugins/pr-review-toolkit/README.md
--jq '.content' | base64 -d` this turn (agent sections 2 and 3).

1. Whether a coverage/pass verdict is judged by behavior actually
   checked vs. merely by code path executed (`pr-test-analyzer`:
   "behavioral vs line coverage" as an explicit, named distinction).
2. Whether error-absorption paths (empty/log-only catch, silent
   fallback) are checked as their own category vs. only checked when
   a crash or failing assertion already surfaced them
   (`silent-failure-hunter`'s explicit scope).
3. canonical: `gh api repos/awesome-skills/5-whys-skill/contents/README.md
   --jq '.content' | base64 -d` this turn — whether a causal chain's
   evidence is attached per intermediate step (5-Whys' per-row
   Evidence column) vs. only at the chain's terminal claim.

## Adopt / skip

- Adopt as a pattern: behavioral-vs-surface-execution as an explicit
  judgment axis when evaluating a Present/passing claim, silent
  error-absorption as its own always-considered attempt category, and
  per-causal-step evidence attachment for multi-step verdicts — all
  three added natively to `playbook/reproduction-evidence-quality.md`
  rules 11-13 in the rulebook fold-in (no tool-name attribution in the
  rulebook itself; provenance stays in this file).
- Skip: `LerianStudio/ring`'s "systematic debugging" claim in its own
  README could not be traced to an actual debugging-specific skill
  file in its tree (`git/trees/main?recursive=true` lists 22
  `default/skills/*` entries, none debugging/root-cause named) —
  dropped as a source rather than cited from an unverified claim.
- Skip: adding a new required gate field per plugin — issue-1199
  requirement 3 scopes this unit to existing-axis rule additions on
  top of the prior (non-plugin) survey round, not a new gate shape.

## Gap line

canonical: docs/issue-1199/reports/defect-verification.md (this repo,
read this turn), "## Tool-landscape survey" section — the prior round's
4 sources (rr, Playwright trace viewer, jam.dev/marker.io-class tools,
severity-matrix guidance) are general QA/debugging-domain tooling, not
Claude Code plugins/skills. This round's 3 entries (pr-test-analyzer,
silent-failure-hunter, 5-whys-skill) are Claude Code plugin/skill
sources, additive to the prior 4, targeting the amendment's stated gap.

## Sources

- https://github.com/anthropics/claude-plugins-official
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/pr-review-toolkit
- https://github.com/awesome-skills/5-whys-skill
- https://github.com/LerianStudio/ring

## kind / loop_state

kind: report
loop_state: phase-1-scouted
