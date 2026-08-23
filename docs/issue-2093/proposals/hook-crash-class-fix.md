---
status: proposed
issue: 2093
files:
  - on-the-record/hooks/hook_input.py
  - on-the-record/hooks/test_hook_input.py
  - on-the-record/hooks/hook_ledger.py
  - on-the-record/hooks/test_hook_ledger.py
  - on-the-record/hooks/fail-open-wrapper.sh
  - on-the-record/hooks/test_hook_crash_conformance.py
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/merge-allow-gate.sh
  - on-the-record/hooks/post-landing-obligation-gate.sh
  - on-the-record/hooks/quality-bar-gate.sh
  - on-the-record/hooks/absorbed-branch-recut-guard.sh
  - docs/handbooks/hooks.md
  - docs/issue-2093/reports/implementation.md
---

# Proposal — hook-crash class fix: shared total parser, registry-driven crash
# conformance, visible fail-open ledger

Upstream: docs/issue-2093/reports/implementation/survey.md and
docs/issue-2093/reports/implementation/scout-brief.md.

## Request

Fix the class of defect that #2092 is one instance of. Registered hooks each carry their
own ad-hoc input parsing; an edge input (an unexpanded `~` in a `cd` target, a heredoc
body, nested quotes, unicode, an empty or 100KB command, missing JSON fields) can raise,
and because the hook runtime treats a crash's exit code as non-blocking, the guard then
skips silently while spraying a traceback across the consuming session's terminal. Deliver
three things: one shared total input-parsing library, a conformance test driven from
`hooks.json` that proves every registration survives an edge-input corpus, and a ledger
line whenever a hook still fails open, so silence stops being the failure mode.

## Constraints

- Platform semantics are fixed and not ours to change: exit 0 = success, exit 2 = block,
  every other nonzero — including the 1 a traceback produces — is non-blocking. Timeouts
  and missing scripts behave identically. A crashing guard cannot be made to fail closed.
- Zero-install: hooks must run against an arbitrary consumer repo. `pr-preflight.sh:7-9`
  documents this constraint verbatim — "a zero-install hook cannot assume gates/ is on
  sys.path in the consumer repo". No new third-party dependency is available either;
  adding one would touch `requirements-dev.txt`, which contract §21 refuses without a
  handbook change and which consumer repos would not install regardless.
- Contract §21: an operational-surface file cannot be staged without a `docs/handbooks/`
  change in the same commit. `docs/handbooks/hooks.md` is in the write set for that reason
  as well as on its own merits.
- The unit of registration is the `hooks.json` entry, not the script file: 58 entries
  across 5 events, and the same script appears under different argv (survey §1). argv
  selects the parse path, so the conformance matrix must key on the entry.
- `.on-the-record/test-tiers.json` already declares `on-the-record/hooks/*.sh` and
  `on-the-record/hooks/test_*.py` as slow-tier triggers, so this diff runs the slow suite
  by the repo's own contract. `pytest.ini` supplies `-n auto` and a `slow` marker.
- `deliverable-guard.sh` deliberately fails *closed* on unverifiable stdin
  (`docs/handbooks/on-the-record.md:8-11`). For it, exit 2 on garbage is correct, and the
  conformance test must encode that rather than "fix" it.
- #2092 has not landed: the only commit anywhere referencing it is a one-line consult-trace
  (survey §8). This work cannot treat the instance fix as an upstream.

## Rationale

**Placement — `on-the-record/hooks/hook_input.py`, rejecting `gates/hook_input.py`.**
`gates/` is the obvious home and nine hooks already `sys.path.insert` it, so it was a live
candidate — but those are all hooks that only ever run inside this repo.
`pr-preflight.sh:7-9` records why the general case cannot: `gates/` is not guaranteed to
exist in a consumer checkout, which is precisely where the crash class bites. The hook's
own directory is the only path that always exists next to a copied hook, and
`credential-network-guard.sh:72` already demonstrates inserting it. Rejecting `gates/`
costs us proximity to the other checkers; keeping it would cost the library its
availability in exactly the deployment the issue exists to protect.

**Typed failure return, rejecting exception-plus-try/except-at-each-call-site.**
The status quo *is* try/except at each call site, and it demonstrably does not hold: every
sampled hook already wraps its `json.loads`, and the class still exists, because the crash
moved downstream of the decode into the `cd` extraction and the filesystem calls fed from
it (survey §3). A boundary that returns `Unparseable(reason)` instead of raising makes the
invalid state unrepresentable past the parse, rather than relying on ~58 call sites each
remembering to catch. The gptme project hit the same wall with `bashlex` and landed on the
same shape — try structured parse, catch broadly, fall back to an opaque verdict, log
rather than crash.

**Fixed parametrized corpus, rejecting a Hypothesis-generated fuzz gate.** Property-based
generation would find edge cases we did not enumerate, which is genuinely attractive for a
"must never crash" property. Rejected because this test is a merge gate: a generator that
surfaces a new failure on an unrelated commit converts the gate into a flake, and a flaky
gate gets disabled. The corpus stays a versioned, eyeball-able table; Hypothesis remains
available as a local discovery tool that promotes its finds *into* the table.

**Ledger under `~/.claude/on-the-record/`, rejecting `runs/`.** The issue text names
`runs/`. Rejected because `runs/` is a repo-relative path and a hook crashing in a consumer
repo would scatter ledgers across every checkout, while the existing hook-authored ledger
precedent — `contract-guard.sh:249-274` — is a single env-overridable JSONL under
`~/.claude/on-the-record/`, which is where a watchdog can actually find it. Adopting the
existing shape also inherits its two good properties: env-overridable (hence testable) and
wrapped so a log failure can never change a verdict.

**Wrapper process, rejecting a sourced bash preamble.** A preamble would be cheaper (no
extra process per hook) but cannot observe a crash it is running inside, and cannot see
stderr after the fact. A thin wrapper that execs the real hook, inspects the child's exit
code and stderr, appends the ledger line, and re-emits the child's exit code unchanged is
the only shape that records a fail-open without altering the verdict. The per-invocation
cost is one extra `bash` exec.

**Do not fight the exit-code table.** Explicitly rejected: making a hook exit 2 on its own
internal error to force fail-closed. Reaching a deliberate exit 2 already requires the
crash-handling path to have run correctly, so it protects only the cases that were never
at risk.

## What will be done

1. `hook_input.py` — the shared total parser, structured as a pipeline of independently
   testable stages, each with an explicit input/output shape and an explicit error channel:
   `parse_payload(raw) -> Payload | Unparseable`, `tool_command(payload) -> str`,
   `cd_target(command) -> CdTarget | NoCdTarget | OpaqueCommand` with `expanduser` applied,
   and a `Unparseable`/`OpaqueCommand` type carrying a machine-readable `reason`. Entry
   point takes a **string**, never stdin, because the survey found the payload reaches
   python through an env var in the majority of hooks (§2). No function in this module
   raises on any `str`/`bytes`/`None` input.
2. `test_hook_input.py` — unit tests for the parser: unexpanded `~` expands, heredoc body
   returns a typed opaque result, malformed JSON returns `Unparseable` with a reason,
   unbalanced quotes do not propagate `ValueError`, empty and 100KB inputs return typed
   results. Satisfies acceptance check 2.
3. `hook_ledger.py` — `record_fail_open(hook, argv, digest, exit_code, reason)` appending
   one JSON object per line to `$OTR_FAIL_OPEN_LEDGER` or
   `~/.claude/on-the-record/fail-open.jsonl`, the whole write wrapped so it can never
   change a verdict. Plus `test_hook_ledger.py`.
4. `fail-open-wrapper.sh` — execs the wrapped hook with its original argv and stdin,
   captures stderr, re-emits the child's stdout/stderr/exit code unchanged, and calls
   `record_fail_open` when the child exits nonzero-and-not-2 or emits a `Traceback` on
   stderr. Its test (a deliberately-broken stub hook driven through it, asserting one
   ledger line) satisfies acceptance check 3.
5. `test_hook_crash_conformance.py` — parametrized over every entry parsed out of
   `hooks.json` x the edge-input corpus (unexpanded `~` cd, heredoc body, nested quotes,
   unicode, empty command, 100KB command, missing `tool_input`, non-dict payload, empty
   stdin). Asserts exit code in `{0, 2}` and zero `Traceback` on stderr, with
   `deliverable-guard.sh`'s fail-closed behaviour encoded as a declared expectation rather
   than an exemption. Marked `slow` — 58 entries x 9 cases is ~522 real subprocess spawns,
   which is slow-marker territory by `pytest.ini`'s own definition — with a fast-tier smoke
   over the corpus against the five migrated hooks so the fast suite is not blind.
   Satisfies acceptance check 1.
6. Migrate the five divergent `cd`-extraction sites onto `hook_input.cd_target`:
   `contract-guard.sh`, `merge-allow-gate.sh`, `post-landing-obligation-gate.sh`,
   `quality-bar-gate.sh`, `absorbed-branch-recut-guard.sh`. This is where #2092 actually
   gets fixed, and it is five real call sites, not a speculative abstraction.
7. Rewire `hooks.json` so every registration runs through `fail-open-wrapper.sh`, argv
   preserved. Done last, gated on 5 being green — the conformance test is the safety net
   that makes this mechanical rewrite checkable rather than hopeful.
8. `docs/handbooks/hooks.md` — document the parser contract, the ledger location and line
   format, the wrapper, and the forbidden import direction (`hook_input.py` imports only
   the standard library: never `gates/`, never another hook).
9. `docs/issue-2093/reports/implementation.md` — the phase-2 record.

## Out of scope

- Changing any guard's verdict logic. This is hardening of the input path only; a hook that
  correctly denies today must deny identically after.
- Making any guard fail closed, including on its own crash (see Rationale).
- A watchdog or reporting surface that consumes the fail-open ledger. This issue makes the
  failure *recordable*; "guard X failed open N times" is a consumer of that record and a
  separate unit.
- Rewriting the env-var payload transport into direct stdin reads across the hook corpus.
  It is a larger mechanical change with its own risk, and the parser is designed around the
  existing transport precisely so it is not required here.
- Fixing #2092 as a separate instance commit. If #2092 lands first this branch rebases onto
  it; otherwise step 6 subsumes it.

## How you'll know it worked

- `python3 -m pytest -q on-the-record/hooks/test_hook_crash_conformance.py -m slow` — green,
  every `hooks.json` entry x corpus case exits in `{0, 2}` with no `Traceback` on stderr.
- `python3 -m pytest -q on-the-record/hooks/test_hook_input.py` — green: tilde expansion,
  heredoc, malformed JSON, unbalanced quotes, empty and 100KB inputs all return typed
  results and nothing raises.
- `python3 -m pytest -q on-the-record/hooks/test_hook_ledger.py` — green: a deliberately
  broken stub hook driven through `fail-open-wrapper.sh` produces exactly one ledger line
  naming the hook and an input digest, and the wrapper re-emits the child's exit code.
- The repo's declared tiers both run: `python3 -m pytest -q -m "not slow"` within its
  300s budget, and `python3 -m pytest -q -m slow`, which this diff triggers by
  `.on-the-record/test-tiers.json`'s own `trigger_change_classes`.
- Negative control: reverting the `expanduser` in `cd_target` turns the conformance test's
  tilde case red. A test that cannot fail is not evidence.
