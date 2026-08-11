# issue-894 — current-state survey: permission/auto-grant posture (phase 1)

Phase-1 research survey for issue #894 step 1. No verdict or ranked findings here — those belong
in the record (docs/issue-894/reports/security-threat-model.md), phase-2 output gated on Approve
per contract v3 s19. This file is ground truth for the proposal's threat table.

## Scout: skip record

Skip condition: the spec (issue #894) names exact artifacts to review and leaves no external
design decision open — internal code audit against official docs, not a product build with
market exemplars. One doc fetch was still run below since the issue asks for official citations.

## code_under_review

- on-the-record/hooks/merge-allow-gate.sh
- on-the-record/hooks/spawn-allow-gate.sh
- on-the-record/hooks/gh-write-allow-gate.sh
- on-the-record/hooks/credential-record-guard.sh
- spawn.py (role_settings comment lines 546-575; `_resume_orchestrator_session` lines 2231-2270;
  `_resolve_gh_token`/`_git_env` lines 4388-4430; role-spawn bypassPermissions lines 3882-3927,
  4019)
- harness/driver.py (`resolve_harness_github_token`/`resolve_harness_github_host` lines 66-107;
  `resume_orchestrator_session` lines 257-304)

## Official-doc facts

canonical: WebFetch https://code.claude.com/docs/en/hooks — executed live, this session,
2026-08-12
- `session_id` reaches a hook as a plain string; the fetched page states there is no
  cryptographic binding (no signature/HMAC/token) tying it to the session that produced it.
- Documented `permissionDecision` values: `allow`/`deny`/`ask`/`defer`.
- `permission_mode` (including `bypassPermissions`) reaches every hook in the payload; PreToolUse
  fires on every tool call per the page's lifecycle section. The fetched excerpt did not resolve
  whether a hook's `deny` is honored under `bypassPermissions`.

## Hooks under review: allow-only, no deny

canonical: on-the-record/hooks/merge-allow-gate.sh:1-231,
on-the-record/hooks/spawn-allow-gate.sh:1-177, on-the-record/hooks/gh-write-allow-gate.sh:1-190 —
read live, this session
None of the three scripts contains a `"permissionDecision": "deny"` literal or `exit 2` — each
only emits `allow` JSON or bare `exit 0`.

## Identity check

canonical: on-the-record/hooks/merge-allow-gate.sh:131-153,
on-the-record/hooks/spawn-allow-gate.sh:81-102, on-the-record/hooks/gh-write-allow-gate.sh:58-77 —
read live, this session
All three hooks read `CLAUDE_ROLE` from process env, then prefer a JSON snapshot at
`$TMPDIR/otr-role-bind/<sanitized-session_id>.json` keyed by the payload's own `session_id`; a
non-empty resolved role excludes the hook. session-role-bind.sh (the snapshot writer) is outside
this issue's file list and was not read here — canonical: not read this session — so whether one
session can write/overwrite another session's snapshot file under a shared `$TMPDIR` is an open
gap the proposal must carry forward as unresolved.

## Command-shape validation

canonical: on-the-record/hooks/merge-allow-gate.sh:91-129,
on-the-record/hooks/spawn-allow-gate.sh:104-158, on-the-record/hooks/gh-write-allow-gate.sh:79-171
— read live, this session
All three reject any command containing a backtick, `$(`, or newline (outside one exception),
then tokenize with `shlex.shlex(cmd, posix=True, punctuation_chars=True)` and match a fixed shape
set (five recognized gh/spawn.py verb shapes, each optionally prefixed by exactly one
`cd DIR &&`); any operator token in the tail aborts the allow.

canonical: on-the-record/hooks/gh-write-allow-gate.sh:86-126 — read live, this session
gh-write-allow-gate.sh carves out one shape: `$(cat <<'DELIM' ... DELIM)` (quoted heredoc
delimiter, which disables expansion of its body by POSIX construction) collapses to an inert
placeholder before the backtick/`$(` check, only when it is the command's sole substitution.

## bypassPermissions-on-resume: in-repo claim

canonical: spawn.py:2245-2260, harness/driver.py:270-281 — read live, this session
Both resume functions cite `docs/issue-886/reports/implementation/
hunt-issue-886-permission-mode-fix.md`: under `bypassPermissions`, a Bash shape outside the
allow-hooks' recognized shapes previously fell back on the host's default-deny, and that
fallback default-deny does not exist under `bypassPermissions`. The comments state this is a
pre-existing property of the mode #700 already uses for role spawns, not a regression from #889.

canonical: docs/issue-886/reports/implementation/hunt-issue-886-permission-mode-fix.md — cited
in-code, not itself re-read live this session
The hunt record backing that claim was not independently re-read here; the proposal must treat
its content as asserted-by-citation, not independently reproduced in this survey.

## Credential flow

canonical: spawn.py:3927,4391-4415,4418-4430; harness/driver.py:66-107 — read live, this session
`_resolve_gh_token()` shells out to `gh auth token` once per process (cached in a module global),
injecting the result into role-session env as `GH_TOKEN` (spawn.py:3927) and into the
orchestrator's own git credential-helper env (`_git_env()`, spawn.py:4418+).
`resolve_harness_github_token()` (harness/driver.py:66-84) does the same for the harness's
separate `NORTHPOLE_HARNESS_GH_TOKEN` path.

canonical: on-the-record/hooks/credential-record-guard.sh:1-114 — read live, this session
credential-record-guard.sh denies a `docs/**` write matching a full-length GitHub/OpenAI/AWS
credential pattern (with a MultiEdit fragment-concatenation check), scoped only to `docs/**`
writes — it does not inspect Bash command text, subprocess stdout/stderr, or non-`docs/` writes.
