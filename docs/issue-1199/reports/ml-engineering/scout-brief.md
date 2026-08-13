---
subject: issue-1199
role: ml-engineering
kind: scout-brief
---

# Scout brief: ml-engineering — Claude Code plugin/skill ecosystem (issue-1199, REWORK per 2026-08-14 operator amendment)

Supersedes the prior scout-brief in this same file (which surveyed the
general ML tooling ecosystem — MLflow/DVC/etc). Per the 2026-08-14
operator amendment on issue #1199, the survey target for this program
is the Claude Code plugin/skill ecosystem itself, not general domain
tools.

Mode: parallel WebSearch fan-out (3 angles: marketplace/awesome-lists
overview, plugin-specific search for ML/notebook/evaluation skills,
data-science/experiment-tracking skill search), 1 sweep stage, 1
verification stage via `gh api repos/<org>/<repo>` (adoption-evidence
method per tech-feasibility), 2 deepening fetches of the highest-signal
repos' actual skill/agent content. Star-count ranking from the
verification stage matched the sweep's category ranking, so a further
round was not run.

canonical: repo star/fork counts read live via `gh api
repos/<org>/<repo>` this session, one call per repo listed below.

## Surveyed plugins/skills (adoption evidence, live-fetched)

- **alirezarezvani/claude-skills**: 24,380 stars / 3,429 forks
  (canonical: `gh api repos/alirezarezvani/claude-skills --jq
  '{stars:.stargazers_count,forks:.forks_count}'`, run this session). A
  large multi-domain skill collection (330+ skills spanning
  engineering, research, and other functions) rather than an
  ML-specific one; included here as the ecosystem's highest-star
  general marketplace, establishing the scale bar other ML-specific
  entries are judged against.
- **jeremylongshore/claude-code-plugins-plus-skills**: 2,630 stars / 386
  forks (canonical: `gh api
  repos/jeremylongshore/claude-code-plugins-plus-skills --jq
  '{stars:.stargazers_count,forks:.forks_count}'`, run this session).
  Its `ai-ml/model-evaluation-suite` plugin ships an
  `evaluating-machine-learning-models` skill (canonical:
  raw.githubusercontent.com/jeremylongshore/claude-code-plugins-plus-skills/main/plugins/ai-ml/model-evaluation-suite/skills/evaluating-machine-learning-models/SKILL.md,
  fetched this session). Problem: a model-evaluation request from a
  user is usually answered as free-form prose with whichever metric
  the responder thinks of first. How: the skill activates on a named
  trigger condition (a performance-analysis/validation/testing
  request), then runs a fixed three-step shape — identify the model
  and the metrics that apply to it, execute the evaluation, present
  results with explicit improvement recommendations — with a
  documented error path for missing dependencies/invalid input.
  Learning: an evaluation deliverable should name its trigger
  condition and its metric-selection step explicitly, not assume the
  metric is obvious from context.
- **rohitg00/awesome-claude-code-toolkit**: 2,499 stars / 886 forks
  (canonical: `gh api repos/rohitg00/awesome-claude-code-toolkit --jq
  '{stars:.stargazers_count,forks:.forks_count}'`, run this session).
  Its `agents/data-ai/mlops-engineer.md` agent (canonical:
  raw.githubusercontent.com/rohitg00/awesome-claude-code-toolkit/main/agents/data-ai/mlops-engineer.md,
  fetched this session) states that a served model degrades
  continuously and frames promotion/rollback as needing a concrete
  bar rather than a judgment call. Its stated design: a quality gate
  names a specific minimum-improvement threshold before a new model
  version may promote over the production baseline (its own worked
  example: 0.5% AUC), the promoted version routes through a bounded
  canary monitoring window before full cutover, and rollback carries a
  stated time target (its own worked example: 5-minute restoration)
  that the agent's own pre-completion checklist lists as something to
  verify live, not merely document. Learning: (a) a promotion
  criterion should name its numeric threshold, not just the existence
  of a trigger; (b) a rollback requirement should carry a time-bound
  recovery target; (c) infrastructure-safety items (serving endpoint
  correctness, rollback procedure, monitoring dashboards) should be
  listed as items a completion checklist verifies, not items a design
  doc merely describes.
- **probabl-ai/skills**: 97 stars / 4 forks (canonical: `gh api
  repos/probabl-ai/skills --jq
  '{stars:.stargazers_count,forks:.forks_count}'`, run this session). A
  data-science skill set organized into four groups (canonical: its
  README, fetched this session): the ML pipeline lifecycle (explore
  data -> build pipeline -> evaluate -> test production-readiness ->
  stress-test on future/held-out data -> audit the finished model as a
  structured report), an iteration loop (track multiple experiments
  side by side, run diagnostic checks, fold user feedback into the
  next iteration), and workspace/tooling skills that enforce project
  structure and dependency hygiene before work starts. Problem: a "the
  model works" claim is usually checked once, against the same data
  slice it was built on. How: the pipeline explicitly separates
  present-data evaluation from a distinct stress-test step against
  data from a later time window, and closes with an audit skill whose
  stated output shape is a structured report rather than a single
  summary line. Learning: staleness/degradation testing should be
  checked against an explicitly later-in-time held-out slice, not only
  a general "staleness tolerance" number with no time-boundary named.

## Gap line (rulebook's current state vs. the surveyed field)

canonical: `cd /home/jwjung/tokenmaxxxer/rulebooks/ml-engineering-rulebook && git show origin/issue-1199/ml-engineering:ml-engineering/hooks/directive.sh | grep -n "rollback\|promotion\|staleness\|traffic-percentage"`, run this session.

The already-landed fold-in on this branch (from the prior, general-tooling
survey round) already requires a concrete rollout traffic-percentage
schedule and an automated promotion/rollback trigger, and already
requires an offline threshold to be measured against a pinned prior
run/model-version identifier. Reading that same file this session shows
it does NOT yet require: (1) the promotion trigger to name its own
numeric minimum-improvement threshold, (2) rollback to carry a
time-bound recovery target that a completion checklist verifies rather
than a design doc merely describes, or (3) the staleness/degradation
check to be run against an explicitly later-in-time held-out data
slice rather than a generic tolerance number. These three gaps map
directly onto the three plugin/skill design moves above and are the
scope of this round's fold-in (see the proposal for the exact
target-file edits).
