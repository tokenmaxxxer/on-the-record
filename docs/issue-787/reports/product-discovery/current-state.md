# Current-state survey — issue #787: plain-session auto-orchestration (root gap)

## Background / context

`docs/issue-776/reports/execution-observation.md` (provenance executed-live) ran the northpole
harness against a fresh fixture-target repo with `on-the-record` installed plugin-only, no explicit
skill invocation, no CI. One representative requirement ("fix the crashing `--version` flag, add a
test"). Result: 17 tool calls, all `Bash`/`Read`/`Edit`/`Write`, zero `Task`/delegation events.
Signals: #1 orchestration=FAIL, #2 record-ability=UNMEASURED, #5 problems-not-pushed-back=FAIL. The
session read the injected directive and fixed the bug directly instead of decomposing/delegating.

## Delivery is already confirmed — the gap is enforcement, not injection

`on-the-record/hooks/hooks.json` wires `UserPromptSubmit -> hooks/directive.sh` unconditionally
(every prompt, not session-start-only — its own header comment: "steering must be freshly read to
steer, and a session-start-only injection drifts out of a long context"). `directive.sh` exits
early only on two conditions: `ORCHESTRATE_OFF` set, or `CLAUDE_ROLE` set (a spawned role session).
Neither held in the #776 baseline (plain session, plugin-installed, no role bind) — so the full
orchestration directive (issue drafting, `spawn.py`, background-spawn discipline, the goal loop)
was delivered to that exact session on its first prompt. Issue #776's own text already names this:
"receives the hook/directive DELIVERY (req #7 delivery layer confirmed) but is NOT driven to ACT as
an orchestrator by default." The gap this issue must close is therefore not "does the plugin ever
tell the session to orchestrate" (yes, always) — it is "what makes the session act on that telling
when it would rather just fix the bug."

## A mechanism enforcing exactly this already exists, and already fails silently on this scenario

`on-the-record/hooks/deliverable-guard.sh` is a `PreToolUse` gate on
`Write|Edit|MultiEdit|NotebookEdit`. Its own header states the policy issue #787 asks for, verbatim:
"In an orchestrator session ..., deliverables are ROLE WORK — the coding-rulebook lesson, enforced
mechanically after a live session authored a requirements doc itself despite the directive." When
CLAUDE_ROLE resolves empty (orchestrator session, exactly the #776 baseline's shape), it denies the
write with an explicit redirect: "this is an orchestrator session and %s is a deliverable path... 
Deliverables are role work: draft the issue,... spawn the role (spawn.py <role> ... --issue <n>)."

Reading the gate's logic (`on-the-record/hooks/deliverable-guard.sh`) shows two independent reasons
it did not fire during the #776 baseline run:

1. **Tree regex too narrow.** `re.search(r"(^|/)(src|tests?|docs)/", n)` only matches paths under a
   `src/`, `test/`/`tests/`, or `docs/` directory segment. The #776 baseline's two touched files —
   the fixture's `fixture_target/__init__.py` and `test_fixture_target.py` — sit in a flat top-level
   package layout (the package directory is `fixture_target/` directly, not nested under a `src/`
   segment) with the test file living beside the package rather than inside a `tests/` directory.
   Neither path matches the regex, so the gate's `if not m: sys.exit(0)` allows both writes through
   unexamined.
2. **Target-repo detection requires the target to already BE a board repo.** Even for a path that
   did match the tree regex, the gate additionally requires
   `os.path.isfile(os.path.join(root, "docs", "specs", "approvers.md"))` to be true for the nearest
   enclosing `.git` root — i.e. the write is only guarded when the target repo already carries this
   repo's own board machinery (an `approvers.md` file). A freshly instantiated fixture-target
   scratch copy (`harness.driver.instantiate_fixture_target`, per
   `docs/issue-776/reports/execution-observation.md` step 1: copy + `git init`, no board files
   seeded) has no `docs/specs/approvers.md`, so `root is None or not os.path.isfile(...)` is true
   and the gate falls through to allow regardless of path.

Both gaps trace to the same root assumption: `deliverable-guard.sh` was built to protect
*this* repo's own layout and board conventions from an orchestrator writing deliverables to
`on-the-record` itself, not to protect an arbitrary, ordinary target repo the plugin has been
installed into for real product work — which is exactly issue #787's scenario and exactly what the
#776 harness fixture represents. The policy line ("Installing this plugin IS the opt-in," carried
in `directive.sh`'s own header comment) already states the intended default-on posture; the
enforcement code has not caught up to it for non-self-hosted targets.

## Composition with the existing explicit path

`spawn.py`-launched role sessions set `CLAUDE_ROLE` before any session-controlled code runs
(`docs/issue-698` — unforgeable via the `session-role-bind.sh` SessionStart snapshot). Every gate
examined here (`directive.sh`, `deliverable-guard.sh`) already exits early when a bound role
snapshot or live `CLAUDE_ROLE` resolves non-empty. A fix that only widens `deliverable-guard.sh`'s
target-repo/tree detection changes nothing about that exemption — the explicit `/orchestrate:run`
path and spawned role sessions are unaffected by construction.

## The empty state is already satisfied by construction, not by prompt classification

A candidate mechanism could try to classify the *first user prompt* as requirement-shaped vs.
chat/question (a UserPromptSubmit-time heuristic) and gate on that classification. But
`deliverable-guard.sh`'s existing design gates on the *tool call*, not the prompt: a pure
question/chat exchange never issues a `Write`/`Edit`/`MultiEdit`/`NotebookEdit` to a deliverable
path in the first place, so the gate never fires for it — no prompt-shape guessing is needed, and
no false-positive risk exists for non-requirement conversations. This is a materially stronger
empty-state guarantee than a text classifier would be, and it is already the shape of the existing
enforcement point this survey found.

## Problem, stated without the proposed solution (JTBD)

- **Job performer**: the operator, installing `on-the-record` into an ordinary target repo (not
  `on-the-record` itself) and handing a plain Claude Code session one representative requirement,
  with no explicit skill/command invocation and no CI.
- **Job**: have that session's first attempt to satisfy the requirement go through decomposition,
  role delegation, board recording, and reporting — the northpole behavior — rather than direct
  Bash/Edit/Write against the target's own source, without the operator having to know or type the
  `/orchestrate:run` incantation themselves.
- **Circumstance**: the directive is already delivered on every prompt regardless of target repo
  (confirmed above); a real enforcement mechanism for "don't write deliverables directly" already
  exists and already carries the exact intended message, but its target-repo/tree detection was
  built for `on-the-record`'s own layout and silently no-ops on an ordinary target repo that has no
  board files and no established source/test/docs convention — precisely the shape most real target
  repos (and the #776 fixture) have.
- **Desired outcome**: re-running the #776 harness after this lands shows at least one
  delegation-shaped event (a `spawn.py`/`Task` call) before any direct deliverable write in the
  transcript, and a non-requirement (chat/question) prompt in the same target repo produces zero
  denies — asserted, not merely claimed.

## Where this sits on the opportunity-solution tree

- **Outcome**: `orchestration_to_completion` (#1) and its downstream signals (#2 record-ability, #5
  problems-not-pushed-back) move from FAIL/UNMEASURED toward PASS on the next #776 harness re-run.
- **Opportunity**: `deliverable-guard.sh` already encodes the correct policy and message but its two
  target-repo/tree checks were scoped to `on-the-record`'s own conventions, so it never engages on
  an ordinary target repo — the #776 baseline's flat-package fixture and missing `approvers.md`
  both fall outside its current detection.
- **Candidate solutions**: scored in the proposal below — widen the tree match, drop or relax the
  `approvers.md` precondition, and/or add a session-scoped requirement-shape signal as a secondary
  gate; compared against inventing a wholly new UserPromptSubmit-classifier-plus-PreToolUse pair.
- **Discriminating assumption test**: whether widening `deliverable-guard.sh`'s existing detection
  (no new mechanism) is sufficient to move signal #1 on a harness re-run, or whether the gap is
  wider than target-repo detection and a new session-scoped enforcement layer is also needed (e.g.
  because the model, once denied, cannot complete a `spawn.py` call in a target repo with no GitHub
  remote — `docs/issue-776/reports/execution-observation.md` step 1 shows the fixture copy is only
  `git init`-ed, no remote added).

## What is NOT yet decided here (left to the proposal / to architecture-implementation)

- The exact regex/allowlist replacing the current `src`/`test(s)`/`docs`-segment match and the exact
  replacement condition for the `approvers.md` precondition.
- Whether `Bash`-mediated file mutation (e.g. `sed -i`, heredoc redirection) needs a matching gate —
  `deliverable-guard.sh` today only matches the `Write|Edit|MultiEdit|NotebookEdit` tool names; the
  #776 baseline's 17 tool calls included `Bash` calls whose content was not inspected here.
- Whether `spawn.py` can complete a delegation in a target repo with no GitHub remote (a precondition
  the #776 fixture does not have) — if not, widening the gate alone denies the direct write but may
  not produce a completed delegation, only a stall.

These are named so the proposal's RICE table has a fixed current-state floor to score candidates
against, not because this survey is answering them.
