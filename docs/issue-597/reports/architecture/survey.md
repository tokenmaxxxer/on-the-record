# Current-state survey — issue-597

## Section 12 (the surface this extends)

`docs/issue-573/proposals/architecture.md` s11-12: the writer for both the
audit-record comments and the issue timeline is `on-the-record/hooks/delegated-judgment-gate.sh`,
a `PreToolUse` hook registered on the `Bash` matcher in `on-the-record/hooks/hooks.json` —
it inspects outgoing `gh` commands and posts via `gh pr comment <n> --body-file -` /
`gh issue comment <n> --body-file -`. Section 12 posts one line + links per firing
event (PR opened under judgment, verdict synthesized, remediation routed,
remediation PR merged, escalation to operator) and explicitly reuses an
*existing* merge-watching surface for PR-merge detection — "this phase does
not invent a new merge-detection channel, it reuses the one already observed
posting `[watch] ... session-end: PR ... opened` style messages" (`spawn.py`'s
watch/session-end mechanism). No existing mechanism detects issue
reopened/closed; #597 is the first requirement needing that.

## issue-320 (the four-element schema)

`docs/issue-320/proposals/2026-08-07-semantic-effect-reporting.md` defines
the four elements (resolved problem / prior cost / newly possible / still
broken). The only existing enforcement is `on-the-record/hooks/report-framing-check.sh`,
a `Stop`-hook that regex-detects keyword presence in `last_assistant_message`
and blocks if an element is missing. This is a **prose-content checker on
free orchestrator text** — it never checks that an element cites a record
path, and it never writes anything itself. It cannot be reused as #597's
writer; it is the failure mode #597 replaces (manual/free-text framing that
"evaporates with the session," per the issue body).

## issue-476 (the anti-theater line)

Not literally "anti-theater line" — that phrase is later shorthand. The
canonical statement, per `docs/issue-573/reports/product-discovery/current-state.md`:
"a gate that checks field presence is gameable; the countermeasure is
mechanized independent re-execution, not a self-report." Mechanism:
`gates/reexecution_gate.py`, re-runs a cited command in a pinned worktree
and checks actual exit code/output. For #597 the applicable form is
narrower — there is no command to re-execute for a "what got resolved"
narrative — so the anti-theater floor here is **citation, not
re-execution**: every element must resolve to a record path that exists on
disk (or a commit sha), checked mechanically, never trusted as free prose.

## Trigger detection precedent

- **PR merged**: `spawn.py`'s watch/session-end mechanism already posts to
  the issue on PR-merge-adjacent events; s12 reuses it rather than inventing
  detection. #597 can reuse the same signal for the "delivery merged"
  transition.
- **Issue reopened / closed**: no existing surface. `delegated-judgment-gate.sh`
  is a `PreToolUse` hook on `Bash` — it already sees every outgoing `gh`
  command before it runs, including `gh issue close` / `gh issue reopen`.
  This is the same vantage point, just a different command-pattern match.

## Citation-path convention

No dedicated spec. Convention observed in s11/s12: comments link
repo-native paths — `#<n>` PR/issue references, `docs/.../*.md` paths — the
same zero-external-URL convention the rest of the plugin uses for
audit-record citations.

## Baseline / empty-state precedent

Issue body's acceptance criteria already states it: "a transition with no
prior records (first proposal of a new issue) states baseline framing
explicitly — absence of prior cost evidence is stated, not fabricated."
No existing hook does this today; `report-framing-check.sh`'s regex would
happily pass a fabricated "prior cost" sentence with no citation. This is
the concrete floor #597 must clear that no current mechanism clears.

## Hand-off boundary

Detecting *which* Bash command constitutes "delivery merged" vs "issue
reopened" vs "issue closed" and wiring the actual regex/parse is
implementation-role territory once this proposal is approved. This survey
and the proposal fix only the write-path shape, the trigger taxonomy, the
comment format, and the citation rule — not the parsing code itself.
