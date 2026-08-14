# Current-state survey — issue #1310

## Write surface

canonical: on-the-record/hooks/pr-preflight.sh (read, lines 199-290)

`on-the-record/hooks/pr-preflight.sh`, the issue #1177 "amendments-reconciled"
block (lines 199-290 as of `ec6c344c`). It fetches all issue comments via
`gh issue view <n> --json comments`, finds the single newest comment, and if
its timestamp is after the session's own `session-start` event, refuses
`gh pr create`/`gh pr edit` unless the role's own record
(`docs/issue-<n>/reports/<role>.md`) already carries a line
`amendments-reconciled: issuecomment-<id>` naming that exact newest comment's
id. It does not distinguish who posted the comment — any comment newer than
spawn time blocks, machine or human.

`on-the-record/hooks/test_pr_preflight.py` already exercises this block
end-to-end (`test_hook_denies_pr_when_post_spawn_comment_unreconciled`,
`test_hook_allows_pr_when_post_spawn_comment_reconciled`,
`test_hook_allows_pr_when_no_post_spawn_comments`,
`test_hook_allows_pr_when_no_comments_at_all`,
`test_hook_allows_pr_when_no_events_file`) via a stubbed `gh` binary reading
JSON fixtures (`_run_preflight`/`_write_fake_gh` helpers) — the shape this
delivery's new tests reuse.

## Machine-comment shapes actually posted to issue comments

canonical: grep -n "gh api.*comments\|COMMENT_MARKER\s*=" spawn.py on-the-record/hooks/*.sh (command output below)

```
derived: grep -n "gh api.*comments\|COMMENT_MARKER\s*=" spawn.py on-the-record/hooks/*.sh
spawn.py:2949:_REMEDIATION_MERGE_COMMENT_MARKER = "[watch] remediation-merged: {path}"
spawn.py:2992:                            "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
spawn.py:3266:_CRASH_COMMENT_MARKER = "[on-the-record] {key}: crashed, respawn cap ({cap}) reached"
spawn.py:3267:_STALL_COMMENT_MARKER = "[on-the-record] {key}: stalled"
spawn.py:3311:                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
spawn.py:3337:                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
spawn.py:3340:_SESSION_END_COMMENT_MARKER = "[watch] {key}: session-end:"
spawn.py:3390:                        "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
spawn.py:3396:_STRANDED_PUSH_COMMENT_MARKER = "[on-the-record] stranded-relay: {key}"
spawn.py:3419:                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
```

canonical: spawn.py grep output above (this file, same section)

Every machine-authored issue comment found in the tree carries a fixed
marker prefix baked into the body text, defined at the spawn.py lines above.
`on-the-record/hooks/delegated-judgment-gate.sh`, function
`build_framing_snapshot` (canonical: on-the-record/hooks/delegated-judgment-gate.sh,
read around its `_gh(["issue", "comment", ...` call), builds the
judgment-pair comment body starting `## Framing snapshot — {transition}
({issue}...)` and posts it via `gh issue comment ... --body-file -`.

canonical: on-the-record/monitors/poll-heartbeat.sh (read, TAG_RE definition)

`on-the-record/monitors/poll-heartbeat.sh` defines a `TAG_RE` regex
matching a leading `[poll-report]`, `[watchdog]`, `[health]`, `[reconcile]`,
`[orphaned]`, `[resume]`, `[watchdog-crash]`, or `[returned-pr]` tag on its
own tick-output text — that script emits to the Monitor notification
channel rather than posting issue comments, but the tag vocabulary is the
same machinery family the issue names ("watchdog judgment pairs,
poll-reports, consult traces, reconcile lines"), so the same bracket-prefix
shape is the stable fallback signature for any of them that do land as
issue comments.

canonical: spawn.py, `_append_consult_trace` (read)

`_append_consult_trace` writes consult-trace lines to `docs/issue-<n>/
reports/consult-log.md` and commits them — not to issue comments directly —
but produces the recognizable line shape `- <ts> | role=... | verb=... |
issue=... | question=... | outcome=...` the issue names; included as a
fallback pattern in case that shape is ever relayed into an issue comment
body.

## Author-account signal

canonical: spawn.py (read, all `-f", f"body=` call sites above)

All of the above machine comments are posted via `gh api
repos/<slug>/issues/<n>/comments -f body=<text>` — i.e. as whatever account
`gh auth status` resolves to in the environment that ran `spawn.py`. This
plugin's approvers model (`docs/specs/approvers.md`) documents both
two-account and single-account modes (role-handoff contract v3 s19); in
single-account mode the same login posts both machine comments (via
`spawn.py`/hooks) and human/operator comments (via the GitHub UI or `gh`
directly) — so author login alone cannot always separate machine from
operator. This matches the phase-1 conformance-review consult
(canonical: docs/issue-1199/reports/consult-log.md, read directly,
2026-08-14T00:40:29Z entry): a hybrid is needed — author-based detection
where a distinct bot login is present (e.g. a login ending in `[bot]`, or
`github-actions`), falling back to the stable text-pattern signatures
above.

## Decision this proposal must make

canonical: grep -rn "\[bot\]" docs/ on-the-record/ spawn.py (no matches, command run directly)

No committed list of "machine bot logins" exists anywhere in the repo, so
author detection can only ever be a primary fast-path for the common
CI-bot login shape; the pattern fallback carries the actual weight for this
repo's single-account-mode operation. The proposal scopes the change to
extending the existing issue #1177 block with an `_is_machine_comment()`
classifier (author pattern OR body-prefix pattern) and filtering by it,
plus new unit tests mirroring the acceptance bar's three named cases.
