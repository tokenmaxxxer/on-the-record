# issue-847 — scout brief

Mode: parallel Agent-tool fan-out, 2 angles, 1 sweep round (batched via one message, two
`Agent` calls). canonical: both agents' returned findings, this session, quoted throughout this
brief. No deepening round run: both angles' results below are directly decision-relevant with no
overlap gap between them, so judge point 2 (saturation) stopped after round 1.

## Angle 1 — real throwaway GitHub repo + scoped token

- Fine-grained PATs scope to one or more selected repos, per-resource permission (Contents,
  Issues, Pull requests) settable read or read/write —
  Sources: https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens ,
  https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- `gh` reads `GH_TOKEN`/`GITHUB_TOKEN` (in that precedence) for github.com auth, no `gh auth
  login` needed — Source: https://cli.github.com/manual/gh_help_environment
- No GitHub doc for "disposable test repos" specifically; governing constraint is the general
  Acceptable Use Policy (no excessive automated/bulk activity) plus REST rate limits
  (~80/min content-generating, 500/hr authenticated) —
  Sources: https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies ,
  https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- Actions' `secrets.GITHUB_TOKEN` is repo-scoped and permission-configurable but only minted
  inside an Actions run — not usable by an external, non-Actions harness process; a fine-grained
  PAT or GitHub App installation token is the correct out-of-Actions analog —
  Sources: https://docs.github.com/en/actions/concepts/security/github_token ,
  https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token

## Angle 2 — gh-mock / local GitHub-API stand-in

- `gh` supports pointing at a non-github.com host via `GH_HOST` + `GH_ENTERPRISE_TOKEN` —
  designed for GitHub Enterprise Server, not for an arbitrary mock host, but mechanically the
  same env-var seam a stand-in server would need to hijack —
  Source: https://cli.github.com/manual/gh_help_environment
- No maintained, general-purpose "fake GitHub REST/GraphQL server" project exists at the fidelity
  needed to fool `gh` end-to-end on issues/PRs/merge — canonical: agent-2 research return, this
  session. What exists is transport-layer stubbing inside `gh`'s own Go test suite
  (`pkg/httpmock`, per-call `Registry.Register()` fixtures, not a running server process) —
  Sources: https://fossies.org/linux/gh-cli/pkg/httpmock/registry.go ,
  https://github.com/cli/cli/blob/trunk/api/queries_repo_test.go
- Generic HTTP-mock libraries (`jarcoal/httpmock`, `h2non/gock`, WireMock, MockServer) can be
  hand-configured to answer GitHub-shaped requests but ship no GitHub preset/fixture set — the
  test author must hand-build the schema — Sources: https://github.com/jarcoal/httpmock ,
  https://github.com/h2non/gock , https://github.com/wiremock/WireMock.Net ,
  https://github.com/mock-server/mockserver-monorepo
- The Probot/GitHub-App community explicitly requested a general GitHub-API mock with webhook
  support and never got one — still-open issue, evidence the gap is real and known, not just
  unsearched — Source: https://github.com/probot/probot/issues/601
- Known ceiling on any mock approach: server-side semantics (merge-queue interaction with branch
  protection, `pull_request` vs `merge_group` check-name timing, real PR-review state machine,
  actual merge-conflict resolution) live server-side and are not reproducible against a stub —
  Sources: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue ,
  https://github.com/orgs/community/discussions/61326

## Must-bes (Kano) for a harness GitHub host

1. `gh issue create`/`gh pr create`/`gh pr merge` must succeed against it unmodified (no gh
   source patch, no custom transport) — otherwise the harness stops measuring the product's own
   `gh`-calling code path and starts measuring a fork of it.
2. Must never let a non-GitHub stand-in silently score PASS — this is the issue's own explicit
   bar — canonical: docs/specs/northpole-harness.md §3 row 1 empty-state column, read this
   session ("UNMEASURED if session produces no transcript to inspect").
3. Must stay runnable for a normal plugin user with no token/network (northpole req #7 is about
   the *product* install, not the harness — canonical: issue #847 body, "the harness may use
   more, but should stay runnable", read this session).

## Performance axes (where real-repo vs mock actually differ)

- **Fidelity**: real repo exercises `gh`'s real HTTP client against real GitHub semantics
  (branch protection, merge mechanics, rate limits) end-to-end; a mock stops at whatever the
  mock author modeled — gap evidenced by the Probot issue and the merge-queue check-timing quirk
  above.
- **Cost/isolation**: mock needs no network, no account, no token, no cleanup; real repo needs a
  token secret, network egress, and a cleanup/GC story for throwaway repos.
- **Maintenance**: no maintained GitHub-fidelity mock exists to adopt (angle 2 finding) — building
  one is bespoke, ongoing maintenance against every GitHub API surface the harness's `gh` calls
  touch (issues, PRs, merge, at minimum).

## Adopt / skip

- Adopt: real throwaway repo under a harness-controlled account, scoped fine-grained PAT injected
  only into the harness's own env (not the product's normal install surface) — matches req #7's
  "product install stays runnable" boundary because the token lives in the harness, never in what
  a normal user installs.
- Skip: building a bespoke GitHub-API mock server — no maintained one exists to adopt (angle 2),
  and hand-building one large enough to fool `gh`'s issue/PR/merge calls is itself a multi-surface
  maintenance burden with a real fidelity ceiling (Probot gap, merge-queue quirk) — worse cost/
  benefit than a scoped real token.

## Gap line

The current harness state (`seed_remote_dir`, PR #840) already satisfies "an `origin` remote
exists" but meets none of the three must-bes above — it is not a GitHub host at all, so `gh`
correctly refuses it — canonical: issue #847 body's quoted `session-end` refusal text (PR #845
§step 5), read this session. The gap is not "needs a more faithful mock" — it is "needs a real
GitHub host or an explicit UNMEASURED fallback," per the adopt/skip judgment above.

Stages used: 1 sweep (2 parallel Agent-tool angles) + judge point 1, no deepening round
(saturation reached — see header). Wall-clock: well under the 3-minute budget.
