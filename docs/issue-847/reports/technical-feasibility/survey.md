# issue-847 — research survey: faithful GitHub host for the #776 steady-state harness

market_argument_supplied: false

Scout: ran — see `docs/issue-847/reports/technical-feasibility/scout-brief.md`. This is a
platform/product-comparison question (real host vs mock vs hybrid) with real comparable prior art
(gh's own test-mocking approach, Probot's community gap), so it was in scope for scouting, unlike
issue #810's pure schema-fact question.

This reads issue #847 and PR #845's steady-state record without the market argument that
motivated either. No verdict here — the proposal
(`docs/issue-847/proposals/2026-08-11-faithful-github-host-for-steady-state-harness.md`)
converges the four probes below.

## Current-state survey

`harness/driver.py::instantiate_fixture_target(dest_dir, seed_remote_dir=None)` creates a local
bare repo at `seed_remote_dir` and wires it as `origin` when given — canonical:
harness/driver.py:23,28,50-51, read this session. This satisfies `git remote get-url origin`
(a preflight no-op) but is a `file://` path, not an `https://github.com/...` remote.

The steady-state re-run's own `session-end` refusal is the direct, load-bearing evidence of the
gap this issue exists to close — canonical: issue #847 body's quoted refusal text ("none of the
git remotes configured for this repository point to a known GitHub host. To tell gh about a new
GitHub host, please use gh auth login"), sourced from PR #845 §step 5, read this session.

`docs/issue-776/reports/execution-observation.md` open finding 2 already names this exact gap and
explicitly routes its resolution to a future design decision ("whether the scenario should seed a
real (or mocked) GitHub-shaped remote is a design decision out of this role's scope") — canonical:
docs/issue-776/reports/execution-observation.md, "Open findings" item 2, read this session. This
issue (#847) is that routed decision.

The same record's open finding 1 (missing `docs/specs/approvers.md` in the fixture template,
causing `board-gate.sh` to refuse) and open finding 3 (the top-level `-p` session's background
watch dying with its parent turn) are independent blockers on the same PR-open step — canonical:
docs/issue-776/reports/execution-observation.md, "Open findings" items 1 and 3, read this session.
Both are explicitly out of this issue's scope (issue #847's own execution plan step 1 asks only
for the GitHub-host judgment); this survey does not re-adjudicate them, and the proposal below
notes this as a scope boundary, not a silent gap.

Deploy/runtime config surface (contract s17): whichever candidate below is chosen, if it involves
a token it is a new harness-only env var (e.g. `NORTHPOLE_HARNESS_GH_TOKEN`), never a variable
the product's own plugin install path reads — the product's own `gh` calls already rely on the
operator's own `gh auth login`/ambient credentials, unchanged by this issue (see Probe 1 finding
2 below).

## Probe 1 — technical (spike-report + reversibility)

**Question (spike_goal):** can the #776 steady-state scenario's seeded remote be made to satisfy
`gh`'s "is this a known GitHub host" check, for each of the three candidate directions the issue
names, without patching `gh` itself?

**Findings**, gathered live 2026-08-11 via two parallel scout angles (see scout-brief.md) plus
this repo's own harness code:

1. A real GitHub repo works unmodified: `gh` reads `GH_TOKEN`/`GITHUB_TOKEN` env vars (checked in
   that order) for github.com auth with no `gh auth login` step required — <source:
   https://cli.github.com/manual/gh_help_environment>, fetched live 2026-08-11 (scout-brief.md
   angle 1). Fine-grained PATs can be scoped to exactly one repo with per-resource
   read/read-write permission (Contents, Issues, Pull requests) — <source:
   https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens>,
   fetched live 2026-08-11. This is a strict superset of what the harness needs: `gh issue
   create`/`gh pr create`/`gh pr merge` against one throwaway repo.
2. `gh`'s own host-recognition check that produced the observed refusal is not itself
   configurable per-repo away from "known GitHub host" — the only documented seam for pointing
   `gh` at a non-github.com host is `GH_HOST` + `GH_ENTERPRISE_TOKEN`/`GITHUB_ENTERPRISE_TOKEN`,
   built for GitHub Enterprise Server, not an arbitrary mock — <source:
   https://cli.github.com/manual/gh_help_environment>, fetched live 2026-08-11 (scout-brief.md
   angle 2). A mock-host candidate would have to answer at exactly the `github.com`/GHES shape
   `gh` expects on this seam; there is no documented "trust this arbitrary host" flag for `gh`.
3. No maintained, general-purpose "fake GitHub API server" exists at the fidelity a mock
   candidate would need (issues, PRs, merge, all answered correctly enough for `gh` to proceed).
   What exists is transport-layer stubbing inside `gh`'s own Go test suite (`pkg/httpmock`,
   per-call fixture registration, not a running server process a harness subprocess could point
   `gh` at) — <source: https://fossies.org/linux/gh-cli/pkg/httpmock/registry.go>, <source:
   https://github.com/cli/cli/blob/trunk/api/queries_repo_test.go>, both fetched live 2026-08-11.
   The closest community precedent (Probot/GitHub-App developers wanting a general GitHub-API
   mock with webhook support) is a still-open, unresolved feature request, not a shipped tool —
   <source: https://github.com/probot/probot/issues/601>, fetched live 2026-08-11.
4. Building a bespoke mock server faithful enough to pass would mean re-implementing (a) issue/PR
   CRUD, (b) `gh pr merge`'s merge-method semantics, and (c) whatever this repo's own gates
   (`board-gate.sh`, `contract-guard.sh`) probe via further `gh`/`git` calls once a PR exists —
   each of those gates is itself part of what issue #776's harness is trying to measure
   end-to-end (delegation → PR → merge → `final_report`), so a mock server would need to be
   re-verified against the same product behavior it exists to test, an ongoing maintenance
   liability with no offsetting fidelity win over the first candidate.

**Reversibility tag:** two-way / low-cost for the real-repo-plus-token candidate — a harness-only
env var and a `seed_remote_dir`-style parameter addition, removable by unsetting the var (falls
back to today's local-bare-repo behavior); one-way / higher-cost for the bespoke-mock candidate —
a new, ongoing-maintenance subsystem that would need continual re-fidelity work as `gh`/GitHub's
API evolves, not a single revertible file.

## Probe 2 — prior_art (build vs buy)

**Question:** is there a maintained dependency this harness could adopt instead of building
either a token-provisioning flow or a mock server from scratch?

- **Buy (adopt) direction — fine-grained PAT / GitHub App installation token provisioning**: this
  is a first-party GitHub primitive, not a third-party dependency to vet — no new supply-chain
  surface, no OpenSSF Scorecard applicable (GitHub's own auth infrastructure, not an installable
  package) — <source: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>,
  fetched live 2026-08-11.
- **Buy (adopt) direction — generic HTTP-mock library as a mock-server foundation**:
  `jarcoal/httpmock` and `h2non/gock` are the closest existing dependencies, but both intercept a
  Go `http.Client.Transport` in-process — usable inside `gh`'s own Go test suite, not as a
  standalone server process an external harness subprocess could point a separately-invoked `gh`
  binary at — <source: https://github.com/jarcoal/httpmock>, <source: https://github.com/h2non/gock>,
  both fetched live 2026-08-11. Neither ships a GitHub-shaped fixture/preset set (Probe 1 finding
  3), so adopting either still leaves the GitHub-schema modeling work to build, not buy.
  WireMock/MockServer are maintained, general-purpose mock-server projects that *could* run as a
  standalone process, but likewise ship no GitHub preset — <source:
  https://github.com/wiremock/WireMock.Net>, <source: https://github.com/mock-server/mockserver-monorepo>,
  both fetched live 2026-08-11.
- **Verdict of this probe:** the real-repo-plus-token direction is a pure "buy" (use GitHub's own
  first-party auth primitive, zero new dependency); the mock direction has no adoptable
  GitHub-fidelity dependency to buy — it would be a "build," and per Probe 1 finding 4, an
  open-ended one.

**Disposition:** mitigated — the harness need not choose "build a mock" at all; the buy-direction
(real repo + scoped token) fully covers the requirement per Probe 1.

## Probe 3 — legal_regulatory (license verdict + regulatory-applicability note)

- No new third-party software dependency is introduced by the real-repo-plus-token candidate — it
  uses GitHub's own REST API and the already-vendored `gh` CLI (already a harness/product
  dependency today, unchanged), so there is no new license surface to scan. License verdict:
  **not applicable — no new dependency**.
- Regulatory-applicability note: the token would be a *secret* (fine-grained PAT), which is
  security-sensitive but not personal data — no DPIA trigger (no processing of personal data by
  this change). The operative constraint is GitHub's Acceptable Use Policy's prohibition on
  "excessive automated bulk activity" and its REST rate limits (~80/min content-generating
  requests, 500/hr for authenticated non-Actions requests) — <source:
  https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies>,
  <source: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api>, both
  fetched live 2026-08-11. A single-scenario, occasionally-run harness (one issue, one PR, one
  merge per run) sits well under both limits; this is a scale/usage-pattern constraint on how the
  harness is run, not a license or DPIA blocker.

**Disposition:** mitigated — no new license exposure; the only regulatory-shaped constraint
(AUP/rate-limit compliance) is satisfiable by the harness's own low, infrequent call volume, which
this proposal states as an explicit operating constraint below.

## Probe 4 — threat_model (STRIDE table)

| Element | Category | Trust boundary | Finding | Disposition |
|---|---|---|---|---|
| Harness-only PAT (fine-grained, single-repo) | Information Disclosure | harness env → CI/local process env, vs. product's own install surface | Token must never leak into the product's normal plugin-install config or into any file the built harness artifact ships — canonical: survey.md "Current-state survey" Deploy/runtime config surface note above | mitigated — env-var-only injection, harness-side scenario code, never written to `docs/`, `.claude/settings.json`, or any committed file (see proposal Measurement design) |
| Throwaway GitHub repo under harness account | Elevation of Privilege | harness test account vs. the org's real repos | A PAT scoped to `read/write: Contents, Issues, Pull requests` on **one** named throwaway repo (fine-grained PAT's per-repo selection — <source: https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens>) cannot reach any other repo even if leaked | mitigated — scoping is enforced by GitHub server-side, not by harness discipline |
| Steady-state scenario silently running against a non-GitHub stand-in | Repudiation / false signal | harness scenario vs. the signals it reports (`docs/specs/northpole-harness.md` §3) | This is the issue's own named failure mode: a scenario that reports PASS while never having exercised a real GitHub host — canonical: docs/specs/northpole-harness.md §3 row 1's empty-state column already establishes the precedent (`UNMEASURED if session produces no transcript to inspect`), read this session | mitigated — proposal's chosen candidate makes "no token/host" an explicit `UNMEASURED`-with-reason branch, never a silent PASS (see Verdict / Measurement design) |
| Rate-limit / AUP exposure from harness runs | Denial of Service (against the harness's own future runs, via GitHub throttling/suspension) | harness process vs. GitHub's API | Per Probe 3, a single-scenario run's call volume (one issue, one PR, one merge) sits far under GitHub's documented rate limits — <source: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api> | accepted — bounded, low-frequency usage; no mitigation code needed beyond not running the scenario in a tight loop, which no current or proposed harness invocation does |
| Bespoke mock server (rejected direction) presenting false-positive GitHub-shaped responses | Tampering / Spoofing | mock process vs. `gh`'s trust that it is talking to real GitHub | A mock that under-models `gh pr merge`'s real semantics (merge-method validation, branch-protection interaction, `pull_request` vs `merge_group` check timing — <source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue>, <source: https://github.com/orgs/community/discussions/61326>) could let a scenario "pass" against behavior real GitHub would refuse | deferred — not built under this proposal's chosen candidate (Verdict below); recorded here so a future team is not tempted to revive this direction without re-reading this row |

## Timebox and acceptance criteria

**Timebox:** this phase-1 spike ran as a single research session, within the 1-3 day spike
convention, executed live 2026-08-11 — one round of parallel scouting (2 Agent-tool angles, see
scout-brief.md) plus direct repo inspection (`harness/driver.py`,
`docs/issue-776/reports/execution-observation.md`, `docs/specs/northpole-harness.md`). No further
phase-1 timebox requested; phase 2 (wiring the chosen host into the scenario, issue #847's
execution-plan step 2) is scoped and timeboxed separately at approval.

**Acceptance criteria (carried from issue #847's own Acceptance section verbatim):** in the #776
steady-state scenario, a delegated role opens and merges a PR against the harness's GitHub host
and the session produces a `final_report`; where no host/token is available the scenario reports
UNMEASURED explicitly, never PASS. Empty state: no token/host available → UNMEASURED with a clear
reason, not a crash and not a false PASS. Provenance: executed-live (phase 2's re-run, per issue
#847's own step 3).
