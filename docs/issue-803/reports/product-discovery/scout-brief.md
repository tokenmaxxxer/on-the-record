---
kind: scout-brief
---

# Scout brief — issue #803 (self-driven find→file→resolve loop)

Stages used: 1 sweep (2 angles, parallel WebSearch in one turn) + judge point,
no deepening round needed (saturation reached — both angles converged on the
same two structural points below, no build decision would change with a
third round). Wall-clock well under budget.

Category fit: this is not a consumer-product surface with direct
competitors: it is an internal control-loop for an autonomous coding agent
deciding problem-severity routing. The comparable field is "autonomous
coding/ops agents' escalation and self-healing design," not a product
category with a UI.

## Must-bes (what the strong field assumes)
- Escalation must be classification-gated, not blanket: "classification
  gates everything, retries handle the transient, the breaker handles the
  persistently broken, escalation handles the rest" (Taskade, AI Agent
  Error Recovery). Applies directly: #803 needs a classifier upstream of
  "file vs inline," not a uniform policy.
- Noise must be filtered at the emission source, not the queue: "alert
  fatigue is a unit-of-detection problem at the emission source, not a
  triage problem" (ARMO). Applies: the empty-state guard belongs in the
  recognize step (decide whether something IS a problem), not as a
  downstream count-and-suppress pass.
- Autonomy without a stop/ask judgment is treated as a liability, not a
  feature, across 2026 coding-agent evaluations (aidevdayindia.org
  roundup) — matches this issue's own framing (recognize vs plow through).
- Precedent already exists for issue-driven agent handoff: GitHub Copilot's
  coding agent and OpenHands both take an issue and return a PR
  autonomously (dev.to 2026 roundup) — validates "file as issue → resolve
  via role → PR" as a known-good shape, not a novel one.

## Performance axes the field competes on
1. Precision of the file-vs-inline classifier (false-positive issue-filing
   rate vs missed real risks).
2. Trail legibility (can a human reconstruct why a deviation was filed or
   inlined, after the fact, without re-running the session).
3. Time-to-resolution once filed (does the loop actually continue, or
   stall waiting on the spawned role).

## Adopt / skip
- Adopt: gate at the recognition step (classify before acting), matching
  the "unit-of-detection" finding — this issue's own "empty-state so it
  does not over-file trivia" requirement is exactly this.
- Adopt: reuse an existing issue→spawn→PR shape (Copilot/OpenHands
  precedent) rather than invent a new resolution mechanism — matches this
  repo's own #699 consult+spawn primitives, so no new primitive is needed.
- Skip: SOC-style ML-scored alert prioritization (statistical thresholds
  tuned on volume) — wrong fit; #803's volume is far too low (one deviation
  per session at most) for a statistical model to be meaningful or
  buildable within scope.

## Gap line
This repo already has the resolution mechanism (consult + spawn, #699) and
the entry point (#787, in progress). What is missing, matching the
must-be "classification gates everything": a recognition/classification
step that runs INSIDE the plain session's own turn, gated on the
already-declared write-set/scope boundary this repo's own warrant
directive uses (SCOPE EXCEEDED clause) — that boundary already exists as a
convention; #803's gap is making it drive an autonomous decision instead
of a stop-and-report.

Sources:
- [AI Agent Error Handling & Self-Healing Patterns (2026)](https://www.taskade.com/blog/ai-agent-error-recovery)
- [How to Reduce Alert Fatigue in AI Agent Detection: Why It's a Unit-of-Detection Problem, Not a Triage Problem — ARMO](https://www.armosec.io/blog/how-to-reduce-alert-fatigue-in-ai-agent-detection/)
- [Best AI Agents for Autonomous Code Review 2026 Revealed](https://aidevdayindia.org/blogs/vibe-coding-ai-governance-rules/best-ai-agents-autonomous-code-review-2026.html)
- [8 AI Coding Agents That Actually Ship Production Code in 2026 — DEV Community](https://dev.to/sonotommy/8-ai-coding-agents-that-actually-ship-production-code-in-2026-18ch)
