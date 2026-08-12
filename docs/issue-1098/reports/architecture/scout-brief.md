stage_count: 1 (sweep only — saturated at judge point 1, no deepening
needed)
mode: batched-sequential (two WebSearch calls issued in one turn/batch,
per the sweep's own tool-call-batching allowance)

## Field: GitOps continuous-reconciliation loops (closest external
comparable to "default post-landing verification lifecycle")

Non-product role (architecture), so the comparable field is systems
that solve "keep runtime state converged with a declared/landed state
without a human re-triggering each round" — GitOps controllers (ArgoCD,
Flux). This repo's own prior art (`gates/closure_sweep.py`,
`gates/landing_readiness.py`, `reexecution_gate.py`) was already
covered in the survey; the external sweep adds a naming/shape check
against a mature "loop that runs by itself" domain.

## Must-bes the field converges on
- **observe → compare → act → report**, run as one continuous loop, not
  a single one-off run (Flux CD's stated cycle).
- The loop is triggered by the state-change event itself (a push/sync),
  not by a human re-invoking it each round.
- **Self-heal is selective, not blanket** — ArgoCD's self-heal setting
  is opt-in per class of drift; the docs explicitly warn that
  auto-reconciling every difference without judging intent (a
  deliberate hotfix vs. an accidental change) causes harm. This maps
  directly onto req#7's "no CI, no explicit skill invocation" boundary
  and the issue's step 2 ("registered ... not worked around, not
  deferred silently") — the loop's job is to surface the obligation and
  force filing, not to auto-fix.

## Performance axes the field competes on
1. Detection latency (how fast drift/regression is observed after the
   triggering event) — the field's answer is "attach to the event
   itself," not a polling cadence.
2. Whether a failing reconciliation turns into a visible, actionable
   status (ArgoCD's `OutOfSync`/`Degraded` states) vs. a silent retry —
   the field always turns the obligation into a first-class, queryable
   state, never an internal log line only.
3. Rollback/remediation judgment: mature systems draw a hard line
   between mechanical health-check hooks (PostSync Jobs) and the
   decision to roll back/file, which is left to a human or a separate
   analysis step (Argo Rollouts' AnalysisTemplate), not automated
   blindly.

## Adopt
- PostSync-hook shape: attach the obligation-creation step to the event
  itself (this repo's `PostToolUse` matching `gh pr merge`, mirroring
  how `merge-allow-gate.sh` already matches the same command shape for
  `PreToolUse`), not a polling/cron sweep.
- First-class obligation state, not a log line: reuse
  `reexecution_gate.py`'s verdict-file precedent so `landing_readiness.py`
  can classify on it the same way it already classifies on
  `.reexecution/*.json`.

## Skip
- Blanket auto-remediation (ArgoCD self-heal applied without judging
  intent) — out of scope per the issue's own step 2 (file, don't
  silently fix) and per req#7 (no CI resync loop to author here).
- A cron/poll-based reconciliation controller — req#7 rules out CI, and
  polling duplicates the watchdog's already-established role
  (Monitor/#829/#947) rather than composing with it.

## Segment fit
This is internal plugin tooling, not a consumer product — the field
supplies a shape/vocabulary check (event-triggered, first-class
obligation state, judgment kept out of the mechanical hook), not a
UX bar to hit.

## Gap line
The surveyed current state already carries the "first-class obligation
artifact" and "pure classifier reads it" halves (`reexecution_gate.py`
+ `landing_readiness.py`). What it lacks, per the field's core must-be,
is the event trigger itself — nothing here plays the PostSync-hook role
that fires the moment the analog of `sync` (a landing) happens.

Sources:
- [How Flux CD Reconciliation Loop Works Step by Step](https://oneuptime.com/blog/post/2026-03-05-flux-cd-reconciliation-loop/view)
- [What Is ArgoCD Reconciliation? How It Works | Rafay](https://rafay.co/ai-and-cloud-native-blog/understanding-argocd-reconciliation-how-it-works-why-it-matters-and-best-practices)
- [Argo CD Hooks That Save Your Rollouts | Almog's Blog](https://almogshoshan.dev/devops/argocd-hooks/)
- [How to Implement Automatic Rollback on Health Degradation](https://oneuptime.com/blog/post/2026-02-26-argocd-automatic-rollback-health-degradation/view)
