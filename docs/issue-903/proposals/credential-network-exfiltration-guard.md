---
status: approved
files:
  - on-the-record/hooks/credential-network-guard.sh
  - on-the-record/hooks/test_credential_network_guard.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
  - docs/issue-903/proposals/credential-network-exfiltration-guard.md
  - docs/issue-903/reports/implementation/survey.md
  - docs/issue-903/reports/implementation.md
---

## Request

Extend credential-exfiltration detection past docs/** writes
(credential-record-guard.sh) to the Bash-command and WebFetch/network-tool
input surface: a PreToolUse guard that denies fail-closed when a known
credential/secret pattern (gho_/ghp_/ghs_/ghr_/github_pat_ and similar)
appears in a Bash command that reaches the network (curl/wget/nc/ssh, or
a pipe to one of those), or in a WebFetch input. Universal,
pattern-based — not a per-project command allow/deny list. Non-credential
commands stay untouched; full agent permissions otherwise unchanged
(#894/#902 posture).

## Constraints

- Fail-closed on match (exit 2), matching credential-record-guard.sh's
  existing convention.
- Universal secret-shape patterns only, never a target/command
  allow-list (operator already rejected that approach per the issue
  body).
- Must not restrict non-credential Bash or non-credential network use —
  the #894/#902 full-open posture stays intact outside this one class.
- Register in hooks.json following the existing PreToolUse/Bash group
  shape, plus a new WebFetch matcher.
- Registration rows required in docs/specs/enforcement-boundary.md and
  docs/specs/generated-paths.md in the same commit (gate-registration-guard.sh).
- Tests: token piped to curl denied; ordinary curl with no secret
  passes; non-network Bash command untouched; WebFetch of a normal URL
  passes.

## Rationale

Chosen approach: a single new hook file, `credential-network-guard.sh`,
matching `Bash|WebFetch`, sharing credential-record-guard.sh's
pattern-and-python3 shape but adding (a) a network-sink detector over
`tool_input.command` for Bash, and (b) a bare credential-pattern check
over `tool_input.url` for WebFetch.

Alternative considered and rejected: extending
credential-record-guard.sh itself to also handle Bash/WebFetch, instead
of adding a new file. Rejected because credential-record-guard.sh's
docstring and tests are scoped specifically to docs/** writes (a
different tool_name set, a different fragment-extraction shape for
Edit/MultiEdit), and folding an unrelated tool_name branch into it would
make one file answer two different questions (write-content leakage vs.
command/network leakage) — the existing precedent in this repo is one
hook file per concern (contract-guard.sh, pr-preflight.sh,
gh-write-allow-gate.sh, etc., each narrow). A second alternative
considered and rejected: a command allow/deny list keyed on known
exfiltration targets — rejected per the issue body itself, which states
the operator already rejected that approach as intractable across
diverse targets; the pattern-based approach generalizes past any
enumerable target list.

## What will be done

- Add `on-the-record/hooks/credential-network-guard.sh`: PreToolUse
  hook, matcher `Bash|WebFetch`. For Bash: parse `tool_input.command`,
  detect a credential-shape match AND a network-reaching signal
  (curl/wget/nc/ssh/scp as a command token, or any `|` pipe segment
  invoking one of those) in the same command string; deny (exit 2) on
  both being present. For WebFetch: check `tool_input.url` (and, if
  present, `tool_input.headers`/`tool_input.body`) for a credential
  pattern; deny on match. Same credential pattern set as
  credential-record-guard.sh (gho_/ghp_/ghs_/ghr_/github_pat_/sk-/AKIA),
  factored so both hooks stay independently readable (duplication over
  a shared module — no existing shared gates module for hooks per the
  survey, and credential-record-guard.sh's own precedent is
  self-contained with no shared module).
- Add `on-the-record/hooks/test_credential_network_guard.py` covering
  the five cases from the issue acceptance criteria plus the
  non-network-Bash-with-secret-text case (must NOT deny, since no
  network sink is present).
- Register the hook in `on-the-record/hooks/hooks.json`'s PreToolUse
  array with matcher `Bash|WebFetch`.
- Add registration rows to `docs/specs/enforcement-boundary.md` and
  `docs/specs/generated-paths.md`.
- Record the honest limit in the hook's own header comment and in the
  implementation record: base64/hex/rot13/other obfuscation of the
  credential text evades a plaintext-pattern match; this guard raises
  the bar for the one irreversible-harm class, it is not a perfect
  boundary. Note the transfer option — network egress allow-listing at
  the hosting environment level — as the complementary control for
  obfuscated exfiltration this guard cannot see.

## Out of scope

- Detecting exfiltration through channels other than Bash/WebFetch
  (e.g. a custom MCP network tool) — the issue names Bash + WebFetch/
  network-tool surface; other tool integrations are a future issue if
  one is added to this install.
- Obfuscated/encoded credential detection (base64, hex, split strings) —
  named explicitly as an accepted, honest limit in the issue body.
- Any change to the #894/#902 full-open permission posture outside this
  one credential-exfiltration class.
- Host-level network egress controls — noted as the transfer option,
  not implemented here.

## How you'll know it worked

`python3 -m pytest on-the-record/hooks/test_credential_network_guard.py -v`
passes all cases, including: a `curl ... $(cat creds)` style command
carrying a `ghp_`-shaped token is denied (exit 2); a plain `curl
https://example.com` with no secret passes (exit 0); a non-network Bash
command containing secret-shaped text is unaffected (exit 0); a
WebFetch of an ordinary URL passes (exit 0); a WebFetch whose url/body
carries a token is denied (exit 2). `gate-registration-guard.sh`'s own
check (implicit at commit time, since the new hook file is staged
alongside its two spec rows) does not refuse the commit.
