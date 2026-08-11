---
status: proposed
files:
  - on-the-record/hooks/credential-record-guard.sh
  - on-the-record/hooks/test_credential_record_guard.py
  - on-the-record/hooks/hooks.json
  - docs/issue-776/reports/execution-observation/run2.md
  - docs/issue-858/reports/implementation/survey.md
  - docs/issue-858/proposals/credential-record-guard.md
---

# Credential-pattern PreToolUse guard for docs records

## Request

Add a PreToolUse guard that refuses a Write/Edit under `docs/**` whose
new content contains a full-length credential (GitHub tokens `gho_`,
`ghp_`, `ghs_`, `ghr_`, `github_pat_`, and similar high-signal secret
shapes), while allowing an explicit `[REDACTED]` marker or a short
truncated prefix under ~12 chars. Register it in `hooks.json`, add
tests, and scrub the existing truncated `gho_A5ji` prefix already
committed in `docs/issue-776/reports/execution-observation/run2.md`
(near-miss from PR #855).

## Constraints

- Scope: any Write/Edit/MultiEdit whose target path is under `docs/**`
  (per the issue text, not narrowed to a role's own reports/ tree).
- Fail-closed on a full-length token; allow `[REDACTED]` and truncated
  prefixes under ~12 chars.
- Must not flag ordinary prose with no credential-shaped substring.
- Session-side hook only — no CI-diff-scan counterpart requested.

## Rationale

Considered folding this into `gates/record_lint.py` and calling it from
`record-claim-guard.sh`, the same way the four existing claim-shape
checks are shared with `gates/ci.py`'s full-PR-diff scan. Rejected: that
sharing exists because those checks run identically over two different
inputs (one write's fragment, and a full PR diff) for two real callers.
Issue #858 asks only for the write-time PreToolUse gate — no CI
diff-scan counterpart — so a shared module would serve a caller that
does not exist yet. A new, self-contained hook script
(`credential-record-guard.sh`) keeps the pattern match with its one
caller, matching how `gate-registration-guard.sh` keeps its own
classification check inline rather than factoring it out for a single
use site.

Also considered scoping to `docs/issue-[^/]+/reports/` (matching
`record-claim-guard.sh`'s narrower scope, which is a role's own record).
Rejected: the issue explicitly asks for `docs/**`, and the near-miss
this closes could equally land in a proposal, decision, or spec file
outside a reports/ tree — narrowing the scope would reopen exactly the
gap the issue is closing.

## What will be done

- New `on-the-record/hooks/credential-record-guard.sh`: PreToolUse
  Write/Edit/MultiEdit hook, modeled on `record-claim-guard.sh`'s
  shape (JSON payload via stdin, path-scoped to `docs/**`, checks
  `content` / `new_string` / `edits[].new_string` fragments, EXIT trap
  remapping any unexpected exit code to 2, `ORCHESTRATE_OFF` kill
  switch). Regex set: `gho_`, `ghp_`, `ghs_`, `ghr_` each followed by
  36+ base62 chars (GitHub's actual token shape), `github_pat_`
  followed by 22+ base62 chars, plus a generic high-signal shape
  (`sk-[A-Za-z0-9]{20,}` and AWS `AKIA[0-9A-Z]{16}`) as "similar
  high-signal secret" coverage. A match is allowed only when the
  matched span itself is immediately followed by `[REDACTED]` or is
  under ~12 chars from its prefix to the end of the matched run (i.e.
  the regex finds a short run, not a long one) — implemented as: the
  full high-length pattern requires the long run to trigger a deny; a
  short truncated prefix simply never matches the long-run pattern, so
  it is allowed by construction, and an explicit `[REDACTED]`
  replacing the secret span is allowed by construction (no credential
  characters remain to match).
- Register in `on-the-record/hooks/hooks.json`'s PreToolUse
  `Write|Edit|MultiEdit` group, alongside `record-claim-guard.sh`.
- `on-the-record/hooks/test_credential_record_guard.py`: full-length
  token denied (each prefix family), `[REDACTED]` marker allowed, short
  truncated prefix (<12 chars) allowed, ordinary prose untouched,
  non-docs path ignored.
- Scrub `docs/issue-776/reports/execution-observation/run2.md:39`'s
  `gho_A5ji...` prefix to `[REDACTED]`.

## Out of scope

- A CI-diff-scan mirror in `gates/record_lint.py` / `gates/ci.py` (no
  caller requested by this issue).
- Secret patterns for providers other than GitHub tokens plus the two
  generic high-signal shapes named above (OpenAI `sk-`, AWS `AKIA`) —
  a broader provider catalog is a follow-up if a future near-miss
  surfaces one.
- Redacting or scanning non-`docs/**` paths (e.g. `src/`, `on-the-record/`
  itself) — out of the issue's stated scope.

## How you'll know it worked

- `python3 -m pytest on-the-record/hooks/test_credential_record_guard.py -q`
  passes: full-token-denied cases exit 2 with a credential-guard
  message, redacted/short-prefix/prose cases exit 0.
- `grep -n "gho_A5ji" docs/issue-776/reports/execution-observation/run2.md`
  returns no match after the scrub.
- `hooks.json` lists `credential-record-guard.sh` in the same
  PreToolUse group as `record-claim-guard.sh`.
