# Current-state survey — issue #903

## Write set (frozen, new paths not yet created)

- on-the-record/hooks/credential-network-guard.sh (new)
- on-the-record/hooks/test_credential_network_guard.py (new)
- on-the-record/hooks/hooks.json (register the new hook)
- docs/specs/enforcement-boundary.md (registration row)
- docs/specs/generated-paths.md (registration row)
- docs/issue-903/proposals/credential-network-exfiltration-guard.md
- docs/issue-903/reports/implementation/survey.md (this file)
- docs/issue-903/reports/implementation.md

## What already exists (precedent)

canonical: on-the-record/hooks/credential-record-guard.sh (full file read)
The existing credential guard fires on PreToolUse matcher
Write|Edit|MultiEdit, scopes to docs/** paths, and matches full-length
credential shapes (gho_/ghp_/ghs_/ghr_ + 36 base62, github_pat_ + 22
base62, sk- + 20, AKIA + 16). Its only tool_name check is the
`in ("Write", "Edit", "MultiEdit")` line — no branch anywhere in the
file reads tool_input.command or a WebFetch url field.

canonical: on-the-record/hooks/credential-record-guard.sh (full file read)
Its shape: stdin JSON payload, a trap remapping unexpected exit to 2,
an ORCHESTRATE_OFF kill switch checked first, python3 for the
JSON/regex logic, exit 2 with a stderr message when a match hits, exit
0 in the remaining fall-through path.

canonical: on-the-record/hooks/test_credential_record_guard.py (full file read)
Test shape: a t_-prefixed pytest module invoking the shell script via
subprocess.run with a JSON stdin payload built by a small _run helper
(tool_name, tool_input, cwd), asserting on returncode and stderr.
conftest.py and pytest.ini at repo root are the test collection config
this project already relies on for every other t_-prefixed hook test
module (e.g. test_gh_write_allow_gate.py).

canonical: on-the-record/hooks/gate-registration-guard.sh (full file read)
Registration requirement written into that file's own logic: a
newly-staged on-the-record/hooks/*.sh file needs a row in
docs/specs/enforcement-boundary.md and docs/specs/generated-paths.md in
the same commit, or that commit's exit code is remapped to 2 by the
gate itself.

canonical: `grep -n credential-record-guard docs/specs/enforcement-boundary.md docs/specs/generated-paths.md` output (see below)
```
docs/specs/generated-paths.md:41:| `credential-record-guard.sh` | n/a | reads/validates only, no write call |
docs/specs/enforcement-boundary.md:87:| `credential-record-guard.sh` | contract | new (#858): ...
```
Existing rows for credential-record-guard.sh sit at those two lines;
the new guard needs sibling rows in the same two files.

canonical: on-the-record/hooks/hooks.json (full file read)
The PreToolUse array's Bash matcher group currently lists 9 hooks
(contract-guard.sh through gh-write-allow-gate.sh). No WebFetch matcher
group exists yet anywhere in this file.

## Official hooks doc (scout — issue asks to reference it)

canonical: WebFetch of https://code.claude.com/docs/en/hooks (redirected from docs.claude.com/en/docs/claude-code/hooks)
PreToolUse stdin payload carries tool_name + tool_input; for Bash,
tool_input.command is the shell string; for WebFetch, tool_input.url is
the target URL. The doc documents exit code 2 as a blocking deny,
matching the convention credential-record-guard.sh already uses in
this repo. The doc's matcher syntax section shows a pipe-separated list
("Bash|WebFetch") matching either tool from one hook entry.

## Skip condition for design-decision scouting (product-shaped scout)

This is a security control matching a known, issue-specified pattern
set (credential prefixes) and a known, issue-specified network-tool set
(curl/wget/nc/ssh, WebFetch) — the issue text and the accepted #894/#902
posture (canonical: docs/issue-894/reports/security-threat-model.md,
full file read) already fix the shape of the design: pattern-based,
fail-closed, universal, explicitly not a command allow-list. The only
open engineering question — hook wiring shape and stdin schema — is
answered by the official hooks doc cited above. No category-exemplar
scouting applies beyond that.

## Gaps this guard closes (from the issue body, restated as requirements)

1. Bash command carrying a credential pattern AND reaching the network
   (curl/wget/nc/ssh literally, or piped to one) is the target case for
   denial.
2. WebFetch tool_input.url (or other network-tool input surface)
   carrying a credential pattern is the target case for denial.
3. An ordinary curl/wget/network Bash command with no credential
   pattern is the target case for the non-denial path.
4. A non-network Bash command (with or without secret-shaped text) is
   the target case for the non-denial path — the guard is scoped to
   only the network-reaching subset of Bash, not all Bash.
5. An ordinary WebFetch of a normal URL is the target case for the
   non-denial path.

Each of the five becomes a test case in
on-the-record/hooks/test_credential_network_guard.py. Actual test
execution output is reported in docs/issue-903/reports/implementation.md
(acceptance-level claims belong there, cited against a live command
run, not in this survey).
