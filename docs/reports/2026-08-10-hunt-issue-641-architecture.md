---
proposal: docs/issue-641/proposals/architecture.md
---

# Hunt record — issue-641-architecture

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the detection design only inspects `gh pr comment`/`gh issue comment` Bash invocations; an orchestrator that delivers the same review critique as a plain chat reply to the operator (never running it through `gh`) is invisible to the gate, and this channel-bypass is not acknowledged anywhere in the proposal's "what's not detectable" section (which only discusses lexical-wording gaming of the trigger vocabulary, not channel avoidance).
Kind: design-error
Seed: docs/issue-641/proposals/architecture.md, docs/issue-641/reports/architecture/survey.md (git show HEAD)
cap_seconds: 120
tier: default
diff_stat_lines: 2 files changed (docs/issue-641/proposals/architecture.md, docs/issue-641/reports/architecture/survey.md), no code
started_at: 2026-08-10T14:27:20+09:00
ended_at: 2026-08-10T14:33:00+09:00

### Reproduce
Read `on-the-record/hooks/delegated-judgment-gate.sh` header: it is documented and implemented as a `PreToolUse (Bash)` hook — it only fires when the orchestrator issues a `gh ...` Bash command matched by literal case arms (`gh pr create`, `gh pr merge`, `gh issue reopen`, `gh issue close`, and per this proposal's phase-2 plan, `gh pr comment`/`gh issue comment`). Confirmed via:
```
sed -n '1,40p' on-the-record/hooks/delegated-judgment-gate.sh
```
which shows `# PreToolUse (Bash): delegated-judgment-gate.sh` and a `case` dispatch keyed on the literal command string, with no path for inspecting orchestrator text that never becomes a tool call.

The proposal text itself (section 2, "What's not detectable, honestly stated" and "Gaming-resistance stated plainly") only discusses two gaps: (a) provenance — can't tell relayed vs. authored prose — and (b) lexical wording avoidance of the trigger vocabulary while still critiquing. It never states or accepts the much simpler bypass: don't call `gh pr comment`/`gh issue comment` at all — just answer the operator's "what do you think of this PR" in the chat transcript, or paste the critique into a commit message / local file the operator later reads. Since the hook is scoped to Bash tool calls, none of those channels are covered, and the design proposes no other channel of enforcement (e.g. Stop-hook transcript scan, or PostToolUse coverage of a broader gh surface like `gh api ... /comments`).

### Observed
Proposal's stated threat model for the new detection mechanism ("Gaming-resistance stated plainly") covers only in-band wording games on the two named `gh` subcommands; it is silent on out-of-band delivery (chat-only reply, or posting via `gh api` instead of `gh pr comment`), both of which fully evade the PreToolUse/Bash match and leave the orchestrator's self-authored review critique completely unflagged.

### Expected
A detectability verdict claiming to be "honest about what's not detectable" should name the channel-bypass gap explicitly (chat-only critique never reaching a `gh` Bash call, or reaching GitHub via an un-matched command like `gh api`) alongside the wording-avoidance gap it does name — otherwise the "advisory, not solved here" framing understates how easily the gate is avoided (skip `gh pr comment` entirely, not just reword it).
