# Upstream Defect Channel Spec

Issue #1131. Consumer sessions (target repos with on-the-record
installed) have no channel to report on-the-record plugin defects
upstream. This spec is EARS-pattern (Easy Approach to Requirements
Syntax): each requirement states its pattern, a verification method, and
a verification condition. Serves northpole req#2 (full record-ability)
and req#5 (problems are not pushed back to the human — the human still
must confirm filing, but the draft assembly, dedup check, and fallback
are agent-driven, not "go file this yourself") from
[docs/specs/northpole.md](northpole.md). req#7 (hooks/plugin elements
only, no CI) bounds every requirement below to a hooks/command
implementation.

## Requirements

### UDC-1 (ubiquitous)
The `/report-upstream` command SHALL assemble a defect draft containing
the plugin version (a commit sha), reproduction evidence, and
observation context whenever a consumer session invokes it with a
defect observation.
- verification_method: gate test (fixture consumer repo, defect
  statement in, draft out)
- verification_condition: `gates/test_upstream_finding_channel.py`
  asserts the produced draft contains a version-sha line, a
  reproduction section, and an observation-context section
- source: issue #1131 requirement 1

### UDC-2 (event-driven)
WHEN a defect draft has been assembled, the channel SHALL check it
against open upstream issues for a duplicate before presenting it to the
user.
- verification_method: gate test (fixture with a pre-existing matching
  open issue)
- verification_condition: `gates/test_upstream_finding_channel.py`
  asserts the dedup check runs (a `gh issue list`/search call against
  the upstream repo) before any `gh issue create` call, and that a
  detected duplicate is reported to the user instead of re-filed
- source: issue #1131 requirement 2

### UDC-3 (state-driven)
WHILE the draft has not yet received explicit user confirmation in the
consumer session, the channel SHALL NOT invoke any network call that
files the draft upstream.
- verification_method: gate test (fixture asserting no `gh issue
  create`/`gh api` call fires before a confirmation step)
- verification_condition: `gates/test_upstream_finding_channel.py`
  asserts the draft is shown and the session halts for confirmation
  before any filing call-shape appears in the command's execution trace
- source: issue #1131 requirement 3

### UDC-4 (ubiquitous, constraint)
The channel SHALL file confirmed drafts as GitHub issues only, and SHALL
NOT offer, scaffold, or allow any pull-request-creation call shape
(`gh pr create`, `gh api ... /pulls`, GraphQL `createPullRequest`,
`GH_REPO`-env-var-driven `gh pr create`, or non-`gh` tooling such as
`hub`/`curl` against the GitHub API) from a consumer session's
upstream-defect-channel code path.
- verification_method: (a) hook unit test exercising
  `on-the-record/hooks/upstream-defect-scope-guard.sh` against each
  named call shape; (b) gate test asserting the channel's own code never
  contains a PR-creation call
- verification_condition:
  `on-the-record/hooks/test_upstream_defect_scope_guard.py` exits 0 with
  every named shape denied; `gates/test_upstream_finding_channel.py`
  asserts (call-shape/argument assertion) the channel never invokes
  `gh pr create` or the other named shapes against the upstream repo
- source: issue #1131 requirement 4 (operator constraint, 2026-08-13);
  coverage widened by
  docs/issue-1131/reports/requirements-engineering/2026-08-13-hunt-upstream-defect-channel-requirements.md

### UDC-5 (event-driven)
WHEN the upstream repo is unreachable (permission or network failure)
at filing time, the channel SHALL save the draft to the consumer repo's
`docs/reports/upstream-findings/` and report the fallback to the user.
- verification_method: gate test (fixture simulating an unreachable
  upstream)
- verification_condition: `gates/test_upstream_finding_channel.py`
  asserts a draft file lands under `docs/reports/upstream-findings/` and the
  command's reported output states the fallback occurred
- source: issue #1131 requirement 5

## Traceability matrix

| ID | description | source | downstream_link | status |
| --- | --- | --- | --- | --- |
| UDC-1 | draft assembly (version sha + repro + context) | issue #1131 req 1 | `on-the-record/commands/report-upstream.md`, `gates/test_upstream_finding_channel.py` | open |
| UDC-2 | duplicate check before filing | issue #1131 req 2 | `on-the-record/commands/report-upstream.md`, `gates/test_upstream_finding_channel.py` | open |
| UDC-3 | confirmation gate before any network filing call | issue #1131 req 3 | `on-the-record/commands/report-upstream.md`, `gates/test_upstream_finding_channel.py` | open |
| UDC-4 | issues-only, PR-path structurally denied | issue #1131 req 4 | `on-the-record/hooks/upstream-defect-scope-guard.sh`, `on-the-record/hooks/hooks.json`, `on-the-record/hooks/test_upstream_defect_scope_guard.py`, `gates/test_upstream_finding_channel.py` | open |
| UDC-5 | unreachable-upstream fallback to `docs/reports/upstream-findings/` | issue #1131 req 5 | `on-the-record/commands/report-upstream.md`, `docs/reports/upstream-findings/`, `gates/test_upstream_finding_channel.py` | open |
| northpole-req2 | full record-ability | docs/specs/northpole.md §2 | UDC-1, UDC-5 (draft always lands in the repo, upstream or local) | open |
| northpole-req5 | problems not pushed back to the human wholesale | docs/specs/northpole.md §5 | UDC-1, UDC-2 (agent assembles + dedups; human only confirms) | open |
| northpole-req7 | hooks/plugin elements only, no CI | docs/specs/northpole.md §7 | `roles/upstream-defect-report.json` (report_only role, no CI), `on-the-record/commands/report-upstream.md`, `on-the-record/hooks/upstream-defect-scope-guard.sh` | open |

## Ambiguity list

- **Statement:** "Filing happens only with user confirmation" (issue
  #1131 req 3).
  **Candidate readings:** (a) confirmation gates the single `gh issue
  create` call only; (b) confirmation must also gate the dedup-check
  network call (a read, not a write).
  **Resolution:** (a). The dedup check (UDC-2) is a read-only lookup
  needed to show the user an accurate draft (including "this looks like
  a duplicate of #N"); gating reads behind confirmation would make the
  draft shown to the user incomplete. Only the write call (`gh issue
  create`) is the "filing" req 3 constrains — matches UDC-3's wording
  ("network call that files the draft upstream").

- **Statement:** "the plugin ... assembles an upstream issue draft
  carrying: plugin version (sha)" (issue #1131 req 1).
  **Candidate readings:** (a) the sha of the on-the-record plugin
  install in the consumer repo; (b) the sha of the consumer's own
  target-repo HEAD.
  **Resolution:** (a). The defect being reported is a plugin defect
  (issue body: "report plugin defects upstream"); the version that
  matters for upstream triage is which plugin commit exhibited the bug,
  not the unrelated target repo's state.

- **Statement:** "the upstream repo is unreachable (permissions/network)"
  (issue #1131 req 5).
  **Candidate readings:** (a) unreachable means the `gh issue create`
  call itself errors (auth failure, network timeout, rate limit); (b)
  unreachable also covers the dedup-check call failing.
  **Resolution:** both trigger the same fallback path — either failure
  leaves the channel unable to safely complete filing (a failed dedup
  check cannot rule out a duplicate), so UDC-5's fallback condition is
  "any network call in the filing path fails," not narrowly the create
  call.
