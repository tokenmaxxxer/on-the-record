# issue-730 — current-state survey: where the claim-citation shape is (and isn't) stated

## What enforces the shape today

on-the-record/gates/record_lint.py is the single source of truth for the
claim-citation rules (issue #517 aggregator, re-exporting/wrapping
gates.py plus four checks it owns outright):

- `bare_count_claim_check`, in on-the-record/gates/record_lint.py
  (function definition starts around line 97) — a bare `N of M` / `N
  items` count outside a code fence needs a `derived: ...` tag or it is
  refused (#333 mirror).
- `unverifiable_reason_check`, same file (around line 69) — an
  `unverifiable:` line with no reason text is refused (#310 mirror).
- `checked_claim_reason_check`, same file (around line 81) — an Acceptance
  `checked: X — result: unverifiable` line with no reason is refused
  (#331 mirror).
- `orphaned_path_reference_check`, same file (around line 121) — a
  backtick-quoted src/, test/, docs/, gates/, on-the-record/ path that
  does not resolve in the working tree is refused (#330 mirror).

`on-the-record/hooks/record-claim-guard.sh` is the live PreToolUse
enforcement point: a write-time approximation that imports
record_lint.py's functions directly (its own header comment says: "They
now call into gates/record_lint.py's functions ... so there is exactly
one place each rule's logic lives") and denies (exit 2) a Write/Edit/
MultiEdit under docs/issue-*/reports/** whose new content trips any of
the four checks.

## Where this hook actually fires

record-claim-guard.sh is wired only in on-the-record's own hooks.json
(PreToolUse, Write|Edit|MultiEdit matcher). It ships with the
on-the-record plugin itself — it is not copied into any per-role
rulebook.

derived: `grep -rl "record_lint\\|record-claim-guard" /home/jwjung/tokenmaxxxer/rulebooks/implementation-rulebook /home/jwjung/tokenmaxxxer/tokenmaxxxer-core` returned no matches (checked directly in this session).

spawn.py's `self_hosted_hooks()` only injects on-the-record's own
hooks.json into a spawned session when the session's target repo *is*
on-the-record itself (checked via `<cwd>/on-the-record/hooks/hooks.json`
existing). So the gate is live exactly in the case this very session is
in: a role spawned to work on the on-the-record repo — matching the
issue's own framing ("every role learns it only from refusal" during
on-the-record's self-hosted development, per the #726 audit).

## Where proactive directive text is assembled

Two independent injection points feed a role session's directives, and
neither states the citation shape:

1. tokenmaxxxer-core (core/hooks/directive.sh, core/hooks/lib/
   role-directive.sh) — the "Interaction protocol for role '<role>'"
   text every role gets (visible in this session's own SessionStart
   transcript). It states record *field* requirements (frontmatter
   presence, loop_state vocab, the "what/why/upstream/kind/loop_state/
   open findings" prose-marker rules) but never mentions counts,
   derived:, unverifiable: reasons, or path resolution — confirmed by
   reading the file directly in this session; no occurrence of "derived"
   or "unverifiable" in it.
2. Per-role rulebook (implementation-rulebook's coding/hooks/directive.sh,
   sourcing core's role-directive.sh helper) — the "[implementation] Role
   directive" block (YOU_DECIDE/USE_WHEN/PRODUCES/HAND_OFF strings).
   HAND_OFF states the record's frontmatter/path/loop_state requirement
   but likewise never mentions the citation shape. The same rulebook also
   bundles three narrower sub-plugins that each inject their own
   UserPromptSubmit directive and pair it with a matching PreToolUse
   gate — record-shape (record-shape-gate.sh: frontmatter + "## What did
   not work" heading), proposal-shape (proposal-shape-gate.sh: the
   seven-section proposal shape), survey-order (survey-order-gate.sh:
   survey-before-proposal ordering). Each is the established pattern this
   repo already uses: directive text and its enforcing gate travel
   together, in the same sub-plugin, phrased to mirror the gate exactly.

Neither tokenmaxxxer-core nor any rulebook references record_lint.py or
record-claim-guard.sh at all (same grep as above, run against both
directories, no matches). on-the-record's own hooks/directive.sh is the
third candidate injection point, but it explicitly exits early for any
session with CLAUDE_ROLE set — i.e. it fires only for the orchestrator,
never for a spawned role session, so it cannot be the fix site as-is
(read directly in this session, lines 10-12).

## Conclusion: whose repo owns the fix

The gate (record_lint.py, record-claim-guard.sh) lives entirely in
on-the-record and fires only in on-the-record-hosted sessions. The fix —
proactive directive text stating the same shape, paired with the gate the
way record-shape/proposal-shape/survey-order already are — belongs
entirely in on-the-record's own repo, not tokenmaxxxer-core: core's
shared directive covers concerns that apply to every repo a role might be
spawned into, but the citation-shape gate is on-the-record-specific
infrastructure that does not exist outside it. No core change is needed
or requested by this proposal.

The one thing on-the-record does not yet have that record-shape /
proposal-shape / survey-order do is an UserPromptSubmit hook that fires
for role sessions (not just the orchestrator) — hooks/directive.sh's
existing early-exit at CLAUDE_ROLE is deliberate for its own content
(orchestrator-only spawn/consult mechanics) and should not be
repurposed; a new, separate hook is the natural fit, mirroring the
sibling-plugin pattern already established in implementation-rulebook.

## Write set this survey projects

- on-the-record/hooks/record-claim-shape-directive.sh (new file to be
  created in phase 2) — the proactive UserPromptSubmit directive,
  role-session-scoped, wired alongside the existing record-claim-guard.sh
  PreToolUse gate.
- on-the-record/hooks/hooks.json — register the new hook.
- on-the-record/hooks/test_record_claim_guard.py — extend with a test
  that renders the directive text and asserts it names the four rule
  shapes (count-needs-citation, unverifiable-needs-reason,
  checked-unverifiable-needs-reason, path-must-resolve), per the issue's
  own Acceptance wording ("unit test renders the deployed role directive
  and asserts it names the ... rules"). Whether this lands as a new test
  file or an addition to the existing one is a phase-2 call, not a
  design decision — either satisfies the Acceptance shape.

No .env.example, dependency-manifest, or migration surface is touched —
this is a hooks/tests-only change entirely inside on-the-record's existing
plugin layout.
