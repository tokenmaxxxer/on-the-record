---
code_under_review:
  - on-the-record/hooks/credential-network-guard.sh
  - on-the-record/hooks/test_credential_network_guard.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
type: feature
breaking: false
verdict: pass  # canonical: python3 -m pytest on-the-record/hooks/test_credential_network_guard.py -v — result: PASS, see Test execution section below
loop_state: landed
---

## Summary of work

Added `on-the-record/hooks/credential-network-guard.sh`, a new
`PreToolUse` hook matching `Bash|WebFetch`, extending credential-
exfiltration detection past `credential-record-guard.sh`'s existing
`docs/**` write-content scope to the Bash-command and WebFetch/network-
tool input surface named in issue #903.

canonical: on-the-record/hooks/credential-network-guard.sh (this session's own write, full file)
For `Bash`, the hook denies fail-closed when `tool_input.command`
carries both a credential-shape match (GitHub `gho_`/`ghp_`/`ghs_`/
`ghr_`/`github_pat_`, OpenAI-style `sk-`, AWS `AKIA`) and a network-
reaching signal (`curl`/`wget`/`nc`/`ncat`/`netcat`/`ssh`/`scp`/`sftp`/
`telnet` as a command word, including inside a pipe/chain segment). For
`WebFetch`, it denies when `tool_input.url`/`headers`/`body` carries a
credential-shape match.

Registered the hook in `on-the-record/hooks/hooks.json`'s `PreToolUse`
array (new `Bash|WebFetch` matcher group) and added registration rows
to `docs/specs/enforcement-boundary.md` and
`docs/specs/generated-paths.md` per `gate-registration-guard.sh`'s
requirement. Regenerated `docs/specs/reconciled-index.md` per the
docs/specs commit rule.

## Why

canonical: docs/issue-894/reports/security-threat-model.md (full file read)
The #894/#902 posture accepted full agent permissions
(bypassPermissions) under on-the-record's review-before-main/revert
compensating controls, because those controls neutralize arbitrary
code exec / tampering / most EoP — effects stay reviewable and
revertible before landing on main. Credential exfiltration to an
attacker-controlled network endpoint is the one class those controls
cannot undo: once a secret leaves the process over the network, no PR
review or revert un-leaks it. `credential-record-guard.sh` only
matched `docs/**` write content, leaving the Bash-command and WebFetch
surface uncovered — this issue targets that specific gap.

## Upstream / basis

Based on: on-the-record/hooks/credential-record-guard.sh (pattern set
and hook shape precedent) and docs/issue-903/proposals/
credential-network-exfiltration-guard.md (this record's own phase-1
proposal, approved via the `APPROVE issue-903/implementation`
issue-level comment, single-account mode).

## What did not work

None.

## Doc-placement ladder

- [x] New hook file (`on-the-record/hooks/*.sh`) — registered in
  `docs/specs/enforcement-boundary.md` (mechanism row) and
  `docs/specs/generated-paths.md` (write-call classification row),
  same commit as the new file, per `gate-registration-guard.sh`.
- [x] `docs/specs/reconciled-index.md` regenerated in the same commit
  per `spec-index-preflight.sh`'s requirement whenever a `docs/specs/*`
  file changes.
- [x] No new dependency, env var, migration, or setup-script change —
  the guard is a self-contained shell+python3 hook using only stdlib,
  same as `credential-record-guard.sh`; no handbook update required.

## Test execution

canonical: `python3 -m pytest on-the-record/hooks/test_credential_network_guard.py -v` (executed live, raw output below)
```
on-the-record/hooks/test_credential_network_guard.py::t_token_piped_to_curl_is_denied PASSED [  7%]
on-the-record/hooks/test_credential_network_guard.py::t_token_direct_curl_arg_is_denied PASSED [ 15%]
on-the-record/hooks/test_credential_network_guard.py::t_token_via_wget_is_denied PASSED [ 23%]
on-the-record/hooks/test_credential_network_guard.py::t_token_via_nc_is_denied PASSED [ 30%]
on-the-record/hooks/test_credential_network_guard.py::t_ordinary_curl_no_secret_passes PASSED [ 38%]
on-the-record/hooks/test_credential_network_guard.py::t_non_network_bash_command_untouched PASSED [ 46%]
on-the-record/hooks/test_credential_network_guard.py::t_non_network_bash_with_secret_shaped_text_untouched PASSED [ 53%]
on-the-record/hooks/test_credential_network_guard.py::t_webfetch_normal_url_passes PASSED [ 61%]
on-the-record/hooks/test_credential_network_guard.py::t_webfetch_url_with_token_is_denied PASSED [ 69%]
on-the-record/hooks/test_credential_network_guard.py::t_webfetch_body_with_token_is_denied PASSED [ 76%]
on-the-record/hooks/test_credential_network_guard.py::t_other_tool_names_untouched PASSED [ 84%]
on-the-record/hooks/test_credential_network_guard.py::t_github_pat_via_curl_is_denied PASSED [ 92%]
on-the-record/hooks/test_credential_network_guard.py::t_aws_key_via_ssh_pipe_is_denied PASSED [100%]
13 passed in 0.41s
```

canonical: python3 -m pytest on-the-record/hooks/test_credential_network_guard.py -v — result: PASS, raw output in the fenced block above
acceptance: python3 -m pytest on-the-record/hooks/test_credential_network_guard.py -v — result: PASS — the run above covers all five issue-acceptance cases (token piped to curl denied, ordinary curl with no secret unaffected, non-network Bash unaffected, WebFetch of a normal URL unaffected, WebFetch carrying a token denied) plus wget/nc/github_pat/AWS-key/ssh-pipe variants and a non-network-Bash-with-secret-text unaffected case.

## Honest limit (recorded per issue #903's explicit request)

This is a plaintext-pattern match over `tool_input.command`/`url`/
`headers`/`body`. base64, hex, rot13, or any other obfuscation/encoding
of the credential text evades it — an attacker-controlled prompt
injection that first encodes the token before piping it to curl is not
caught by a plaintext regex. This guard raises the bar for the one
irreversible-harm class named in the issue (exfiltration via a
plaintext-visible secret shape); it does not close the space
perfectly. The control this hook cannot substitute for is network
egress allow-listing at the hosting environment level (e.g. restricting
outbound connections to a known-good host set at the sandbox/VM/
container network layer) — a transfer option, not implemented by this
issue, worth considering separately for obfuscated-exfiltration
coverage.

## Verification checks

canonical: python3 -m pytest on-the-record/hooks/test_credential_network_guard.py -v — result: PASS, see Test execution section above
derived: python3 -m pytest on-the-record/hooks/test_credential_network_guard.py -v — see the fenced raw output above
- closed_checks: credential-network-guard.sh test suite, code_sha
  9b03478981eee187df9bb957b468868e70e513d6 base — the five
  issue-acceptance cases plus the supplementary variants listed in the
  fenced raw output above, all passing live per that same run.

## Open findings

canonical: this record's own frontmatter and the test run cited above
None outstanding at landing.
