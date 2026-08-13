# Scout brief — issue #1131 upstream defect channel

mode: parallel (2 WebSearch calls, one turn) — 1 sweep stage, saturated
after judge point 1 (both hits converge on the same must-bes; no
deepening round needed).

## Category must-bes
- Explicit, per-report user consent gate before anything leaves the
  machine — not a global opt-in toggle (Sentry desktop crash reporter:
  `sentry_options_set_require_user_consent`, per-report consent
  discussion in getsentry/sentry-native#110).
- Preview of exactly what will be submitted before submission (VS Code
  Issue Reporter's "Preview on GitHub" step — microsoft/vscode Submitting
  Bugs and Suggestions wiki).
- Dedup against existing reports before creating a new one (Sentry
  fingerprint/trace-id correlation — oneuptime.com dedup-by-trace-id
  writeup; getsentry/sentry-javascript#530 "prevent duplicate issues from
  same user").
- Version/environment diagnostics auto-attached to the draft, not
  hand-typed (VS Code issue reporter autofill; GitLab VS Code extension
  issue #1766 tracks adding instance version specifically because it was
  missing).

## Performance axes (what strong tools compete on)
1. How little the user has to type manually (auto-filled diagnostics vs.
   blank template).
2. Whether a report that is too large or otherwise can't go out directly
   is surfaced with an explicit warning, rather than silently dropped
   (VS Code's issue reporter shows a size-limit warning instead of
   truncating quietly).
3. How tight the dedup loop is (checked before draft is shown, not after
   submission).

## Adopt
canonical: web search results quoted above (sentry-native#110,
vscode Submitting-Bugs-and-Suggestions wiki)
- Draft-then-preview-then-confirm as one linear flow, never a background
  auto-send (matches Sentry consent + VS Code preview).

canonical: web search results quoted above (sentry-javascript#530,
oneuptime.com dedup writeup)
- Dedup check runs before the draft is shown to the user, so a
  duplicate finding short-circuits to "already reported, see #N" instead
  of building a redundant draft.

canonical: web search results quoted above (vscode issue-reporter
autofill, gitlab-vscode-extension#1766)
- Auto-attach machine-derivable evidence (version sha, repro steps,
  observation context) so the user only has to confirm, not compose it
  by hand.

## Skip
canonical: issue #1131 body, requirement 3 ("no silent auto-submission")
- Sentry's flood-limiting / rate-window logic — this channel is designed
  as human-confirmed per event, not auto-batched telemetry, so the
  flooding failure mode Sentry's rate-window guards against does not
  apply here; adding it would be unmotivated complexity.
- Full crash-report auto-upload — issue #1131 requirement 3 (no silent
  submission) already forecloses this; not adopting it is not a gap, it
  is the operator's stated constraint.

## Segment fit
This is a plugin-internal, hooks/command-only channel (req#7: no CI, no
background service) — closer to VS Code's in-editor issue reporter
(built entirely from client-side commands) than to Sentry's SDK-based
telemetry pipeline (has a server-side ingestion tier this repo has no
equivalent of). Sentry's consent/dedup *ideas* transfer; its
infrastructure shape does not.

## Gap line
canonical: on-the-record/hooks/gh-write-allow-gate.sh (read this
session), on-the-record/hooks/ directory listing (read this session),
docs/specs/northpole.md (read this session)
Current repo state already has: a confirmation-gate pattern
(`hooks/approval-gate.sh`), a scoped gh-write allow-gate
(`hooks/gh-write-allow-gate.sh`, five verbs: issue create/comment, pr
comment/close, issue close — `gh pr create` is not among them), and
version-sha citation conventions (record-claim-guard). Missing against
the must-bes above: (a) no draft-assembly path that gathers
version+repro+context into an issue body, (b) no dedup-before-draft
check against upstream open issues, (c) no unreachable-upstream fallback
path/dir, (d) no structural (not just absent-from-allowlist) block on a
PR-shaped gh invocation specifically from a consumer-session
defect-report flow.

Sources:
- https://github.com/getsentry/sentry-desktop-crash-reporter
- https://github.com/getsentry/sentry-native/issues/110
- https://github.com/microsoft/vscode/wiki/Submitting-Bugs-and-Suggestions
- https://gitlab.com/gitlab-org/gitlab-vscode-extension/-/issues/1766
- https://oneuptime.com/blog/post/2026-02-06-deduplicate-errors-sentry-otel-trace-ids/view
- https://github.com/getsentry/sentry-javascript/issues/530
