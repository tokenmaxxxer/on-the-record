---
kind: implementation
code_under_review:
  - on-the-record/hooks/hook_input.py
  - on-the-record/hooks/hook_ledger.py
  - on-the-record/hooks/fail-open-wrapper.sh
  - on-the-record/hooks/test_hook_input.py
  - on-the-record/hooks/test_hook_ledger.py
  - on-the-record/hooks/test_hook_crash_conformance.py
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/merge-allow-gate.sh
  - on-the-record/hooks/post-landing-obligation-gate.sh
  - on-the-record/hooks/quality-bar-gate.sh
  - on-the-record/hooks/absorbed-branch-recut-guard.sh
  - on-the-record/hooks/test_hook_cache_layout.py
  - gates/test_hooks_parity.py
  - docs/handbooks/hooks.md
loop_state: committing
type: hardening
breaking: false
verdict: delivered
---

# Implementation record — issue #2093 hook-crash class fix

kind: implementation
loop_state: committing

Phase 2, opened by the issue-level `APPROVE issue-2093/implementation` comment from
`JiwonJung94`, an approvers.md account, single-account mode, contract v3 s19.
canonical: `gh issue view 2093 --comments`, run this session, whose output carries that
comment body verbatim.

## What was done

The approved proposal (`docs/issue-2093/proposals/hook-crash-class-fix.md`) steps 1-9,
in order, with step 7 held until step 5 was green.

1. **`on-the-record/hooks/hook_input.py`** — the shared total parser. Standard library
   only; no function in it raises for any `str`/`bytes`/`None`/arbitrary input.
   `parse_payload -> Payload | Unparseable(reason)`, `tool_command -> str`,
   `cd_target -> CdTarget | NoCdTarget | OpaqueCommand` with `~` expanded, plus
   `cd_target_dir`, `usable_dir`, `resolved_cwd`.
2. **`on-the-record/hooks/test_hook_input.py`** — unit tests over that contract,
   including a parametrized totality property over a hostile-input corpus.
3. **`on-the-record/hooks/hook_ledger.py`** — `record_fail_open(...)` appending one JSON
   line to `$OTR_FAIL_OPEN_LEDGER`, default `~/.claude/on-the-record/fail-open.jsonl`,
   with the input recorded as a sha256 digest, never verbatim. The whole write is wrapped
   so a ledger failure can never change a verdict.
4. **`on-the-record/hooks/fail-open-wrapper.sh`** — runs the real hook with its original
   argv and stdin, re-emits stdout/stderr/exit code unchanged, and writes a ledger line
   when the child exits nonzero-and-not-2 or emits a `Traceback` even at exit 0.
   `on-the-record/hooks/test_hook_ledger.py` drives it end to end, including a
   deliberately-broken stub hook.
5. **`on-the-record/hooks/test_hook_crash_conformance.py`** — parametrized over every
   `hooks.json` entry crossed with an edge-input corpus, asserting exit in `{0, 2}` and no
   traceback on stderr, in a throwaway HOME/cwd with `gh`/`curl` stubbed. The full matrix
   is `slow`-marked; a fast-tier smoke runs the same corpus against the five migrated
   hooks; two negative controls prove the check can go red.

   canonical: `docs/handbooks/on-the-record.md:8-11`, read this session, which states the
   fail-closed-on-unverifiable-stdin posture for one hook.
   `deliverable-guard.sh` deliberately fails *closed* on unverifiable stdin, so the matrix
   encodes that as a declared expectation rather than an exemption.

6. **The five divergent `cd`-extraction sites migrated** onto the shared parser:
   `on-the-record/hooks/contract-guard.sh`, `on-the-record/hooks/merge-allow-gate.sh`,
   `on-the-record/hooks/post-landing-obligation-gate.sh`,
   `on-the-record/hooks/quality-bar-gate.sh`,
   `on-the-record/hooks/absorbed-branch-recut-guard.sh`.
7. **`on-the-record/hooks/hooks.json` rewired** — every registration now runs as
   `fail-open-wrapper.sh <hook> [args]`, argv preserved.

   derived: `python3 -c "import re;t=open('on-the-record/hooks/hooks.json').read();
   print(len(re.findall(r'\"command\": \"', t)),
   len(re.findall(r'fail-open-wrapper.sh ', t)))"`

   ```
   58 58
   ```

8. **`docs/handbooks/hooks.md`** — parser contract, ledger location and line format,
   wrapper shape, and the forbidden import direction.
9. **This record.**

**The conformance matrix caught a live instance of the class while it was being written.**
`contract-guard.sh` resolved `cd ~/work/repo && gh pr merge 1 --squash` to a directory
that does not exist in the hook process's world and handed that claim straight to
`subprocess(cwd=...)`.
canonical: the live `python3 -m pytest -q -p no:randomly
on-the-record/hooks/test_hook_crash_conformance.py` run this session, whose transcript is
quoted here:

```
E       AssertionError: PreToolUse:contract-guard.sh:- sprayed a traceback on the
        unexpanded-tilde-cd-merge case:
E         Traceback (most recent call last):
E           File "<string>", line 85, in <module>
E           File "<string>", line 74, in gh_json
E           File "/usr/lib/python3.10/subprocess.py", line 1863, in _execute_child
E             raise child_exception_type(errno_num, err_msg, err_filename)
E         FileNotFoundError: [Errno 2] No such file or directory: '.../home/work/repo'
```

`cd_target_dir()` was added in response: a `cd` target is *claimed*, not verified, and a
claim that names no existing directory is dropped rather than handed to a subprocess.

Doc-placement ladder outcomes:

- [x] survey → `docs/issue-2093/reports/implementation/survey.md` (phase 1)
- [x] scout brief → `docs/issue-2093/reports/implementation/scout-brief.md` (phase 1)
- [x] proposal → `docs/issue-2093/proposals/hook-crash-class-fix.md` (phase 1)
- [x] handbook update → `docs/handbooks/hooks.md`
- [x] record → `docs/issue-2093/reports/implementation.md` (this file)
- [x] deviation log → `docs/reports/deviation-log.md` (one inline entry; the per-issue
      path under docs/issue-2093/reports/ is refused by board-gate.sh as a foreign record)

## Why

The platform's exit-code table is fixed: 0 = allow, 2 = block, every other nonzero —
including the 1 a traceback produces — is non-blocking. A crashing guard therefore cannot
be made to block. The only two things that can change are whether it crashes at all, and
whether the crash is *visible*. The shared total parser addresses the first at the
boundary, so an invalid state is unrepresentable past the parse instead of depending on
every call site remembering to catch; the wrapper plus ledger addresses the second, so a
fail-open stops being an absence and becomes a readable line.

## Upstream

`docs/issue-2093/proposals/hook-crash-class-fix.md`, itself based on
`docs/issue-2093/reports/implementation/survey.md` and
`docs/issue-2093/reports/implementation/scout-brief.md`. Branch base commit
`54f4ccee60604cb519e093c2d4bd49a73b4cdebb`.

## Acceptance verification

The repo's declared tiers (`.on-the-record/test-tiers.json`) both ran; this diff touches
`on-the-record/hooks/*.sh` and `on-the-record/hooks/test_*.py`, which are declared
`trigger_change_classes` for the slow tier, so the slow tier was required and run.

canonical: `python3 -m pytest -q -p no:randomly
on-the-record/hooks/test_hook_crash_conformance.py`, run live this session as part of the
combined invocation whose summary is pasted below.
checked: `python3 -m pytest -q on-the-record/hooks/test_hook_crash_conformance.py`
(acceptance check 1) — result: green.

canonical: `python3 -m pytest -q -p no:randomly on-the-record/hooks/test_hook_input.py`,
run live this session in the same invocation.
checked: `python3 -m pytest -q on-the-record/hooks/test_hook_input.py` (acceptance
check 2) — result: green.

canonical: `python3 -m pytest -q -p no:randomly on-the-record/hooks/test_hook_ledger.py`,
run live this session in the same invocation.
checked: `python3 -m pytest -q on-the-record/hooks/test_hook_ledger.py` (acceptance
check 3) — result: green.

canonical: live run of `python3 -m pytest -q -p no:randomly
on-the-record/hooks/test_hook_crash_conformance.py on-the-record/hooks/test_hook_input.py
on-the-record/hooks/test_hook_ledger.py on-the-record/hooks/test_contract_guard.py
on-the-record/hooks/test_merge_allow_gate.py
on-the-record/hooks/test_post_landing_obligation_gate.py
on-the-record/hooks/test_quality_bar_gate.py
on-the-record/hooks/test_absorbed_branch_recut_guard.py` this session, transcript below.

```
867 passed in 6.73s
```

canonical: live run of the fast tier this session, transcript below.

```
$ python3 -m pytest -q -m "not slow"
2784 passed, 18 xfailed, 3 xpassed in 40.92s
```

Fast-tier wall-clock: 42s, inside the declared 300s budget. No SKIPPED lines appeared in
either summary.

canonical: live run of the slow tier this session, transcript below.

```
$ python3 -m pytest -q -m slow
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
1 failed, 813 passed, 1 xfailed, 1 xpassed in 398.23s (0:06:38)
```

That single slow-tier failure is pre-existing on `main` and unrelated to this write set —
see Open findings. Every other slow test, the full conformance matrix included, was green.

canonical: live run of `python3 -m pytest -q -p no:randomly on-the-record/hooks/ gates/`
this session, transcript below.

```
2341 passed, 10 xfailed in 12.48s
```

## Rationale for deviations

Two divergences from the approved proposal's plan:

1. **`cd_target_dir()` and `usable_dir()` were added to `hook_input.py`** beyond the
   proposal's named entry points. Forced by evidence, not preference: the conformance
   matrix (proposal step 5) surfaced the `FileNotFoundError` quoted above, an instance of
   the very class the issue targets, and the fix belongs at the shared boundary rather
   than duplicated in each guard. Same file, same write set, same contract — still total,
   still standard-library-only.
2. **Two files outside the frozen write set were edited**:
   `gates/test_hooks_parity.py` and `on-the-record/hooks/test_hook_cache_layout.py`.
   The approved step-7 rewire changes every `hooks.json` command string from `<hook.sh>`
   to `fail-open-wrapper.sh <hook.sh>`, and both files read those strings assuming a
   single script path.
   canonical: `python3 -m pytest -q -p no:randomly on-the-record/hooks/
   gates/test_hooks_parity.py` run this session before the adaptation, whose transcript
   is quoted here:

   ```
   FAILED on-the-record/hooks/test_hook_cache_layout.py::t_seeded_non_exec_wired_script_is_refused
   FAILED gates/test_hooks_parity.py::t_live_fire_deny_before_commit_lands - Ass...
   2 failed, 1414 passed, 2 xfailed in 12.19s
   ```

   The parity test handed the whole command string to `bash` as one argv element (exit
   127); the cache-layout test's `re.search` matched only the wrapper's basename, silently
   dropping the exec-bit check for the wrapped scripts. Both adaptations are mechanical
   (argv split; `re.findall`) and were logged inline in `docs/reports/deviation-log.md`.
   Leaving them red to stay inside the write set would have shipped a failing suite and a
   silently-weakened exec-bit check, a worse outcome than a reported one-line-each
   adaptation. Flagged here for the approver.

canonical: `git diff main...HEAD --stat`, run this session, whose changed-path list
contains no guard-verdict rewrite and no new consumer module.
The proposal's out-of-scope list held: no guard's verdict logic changed, nothing was made
to block on its own crash, no ledger consumer or watchdog was built, and the env-var
payload transport was left as it was.

## What did not work

- The proposal's `NoCdTarget`/`OpaqueCommand` split was not sufficient on its own. A
  typed `CdTarget` still carries an *unverified* claim, and the first conformance run
  proved a well-typed claim can still crash a guard downstream. Totality at the parse
  boundary does not imply safety at the filesystem boundary; `cd_target_dir()` closes the
  second one.
- canonical: the board-gate.sh PreToolUse refusal message emitted against that path this
  session — "docs/issue-2093/reports/deviation-log.md belongs to another role.
  implementation writes only implementation.md, implementation/** — never a foreign
  record. (contract v3 s11)".
  The per-issue deviation-log path named in the deviation directive is refused by
  board-gate.sh as a foreign record for the implementation role, so the entry went to
  `docs/reports/deviation-log.md` instead.

## Open findings

- The slow tier carries one failure in `tests/test_spawn_gate_wiring.py`, the
  `Ledger::test_toolchain_cache_env_redirected_into_workspace` case. It is pre-existing
  on `main` and unrelated to this write set: it asserts `spawn.py`'s `CARGO_HOME`
  workspace redirection, and this diff touches no `spawn.py` path.
  canonical: the same single test run this session in a clean worktree checked out at
  `main` (`git worktree add -f /tmp/otr-main-check main`), transcript below.

  ```
  $ python3 -m pytest -q -p no:randomly "tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace"
  1 failed in 97.52s (0:01:37)
  ```

- canonical: the board-gate.sh refusal message quoted in "What did not work" above,
  emitted live this session.
  The deviation directive names a per-issue deviation-log path for issue-scoped sessions,
  but board-gate.sh refuses that path for the implementation role. The two rules
  contradict each other; a session cannot satisfy both.
- canonical: `git log --oneline --all | grep 2092`, run during the phase-1 survey and
  recorded in `docs/issue-2093/reports/implementation/survey.md` section 8, which found
  only a one-line consult-trace.
  `#2092` never landed, so step 6 subsumes it rather than building on it, as the proposal
  planned for.
- The wrapper adds one `bash` exec per hook invocation across every registration. It was
  not measured against a no-wrapper baseline this session; the fast tier still finished in
  42s of its 300s budget, which bounds the cost loosely but is not a direct measurement.
  unverifiable: no per-invocation timing harness exists in this repo, and building one is
  outside the approved write set.

## Next steps

- Push the branch and update PR #2095 to the phase-2 delivery body carrying
  `Closes #2093`, then wait for the merge decision.
- After merge, the fail-open ledger has no consumer: "guard X failed open N times" is
  deliberately out of scope here and is the natural follow-up unit.

## Resolution path

- The pre-existing `tests/test_spawn_gate_wiring.py` failure resolves outside this issue:
  it needs an edit to `spawn.py` or that test file, both outside this write set, so it is
  reported here for the orchestrator rather than fixed in-session.
- The deviation-log path contradiction resolves by whichever of the two rules the user
  amends — either board-gate.sh allows a role's own per-issue deviation log, or the
  deviation directive drops the per-issue path for role sessions. Reported, not decided.
- The wrapper's per-invocation cost resolves by a direct measurement, wrapped versus
  unwrapped invocation of one representative hook, if the merge review asks for one.
- The `#2092` coordination resolves at merge: this branch's step 6 is that instance fix,
  so #2092 needs no separate instance commit.

## Skill verdicts (issue #2039)

skill-verdict: implementation-blueprint — applied: invoked; classify routed
backend/no-external-callers/transform/sync to the pipeline archetype, which shaped
`on-the-record/hooks/hook_input.py` as staged total transforms (raw -> payload -> command
-> cd-target -> verified directory), each independently testable with an explicit
input/output shape and an explicit error channel; its speculative-generality anti-pattern
drove the rule-of-three check, so five real call sites migrated rather than an abstraction
being built on spec.

skill-verdict: implementation-complexity-coupling-management — applied: invoked; rule 7
(encode a forbidden import direction at the point of introduction) became the
standard-library-only rule on `on-the-record/hooks/hook_input.py`, documented in
`docs/handbooks/hooks.md` and held in the delivered file, which imports `json`, `os`,
`re`, `shlex` and `typing` and nothing else. Rule 6 (do not grow a low-cohesion shared
module) kept the ledger in a separate `on-the-record/hooks/hook_ledger.py` instead of
bolting it onto the parser.

skill-verdict: implementation-performance-data-structure-choice — applied: invoked; rule 4
(a fixed per-message cost linear-scales into the dominant cost at volume) drove the
`slow`-marker placement for the real-subprocess matrix plus a fast-tier smoke over the
five migrated hooks, and the same reasoning set `MAX_STRUCTURAL_COMMAND` so a 100KB paste
short-circuits before `shlex` rather than stalling a per-invocation guard.

skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-style
pattern was under consideration; returning a typed failure from a total parse boundary is
a function-contract decision, not Strategy/Factory/Visitor/Observer/Decorator indirection.

skill-verdict: work-in-english — applied: invoked; every repository-bound artifact this
session produced is in English — the parser, ledger and wrapper source and their comments,
all four test files, the handbook section, the commit messages, this record, and the
deviation-log entry — with only the closing summary to the user written in Korean.

skill-verdict: model-routing — applied: invoked; its acceptance rule (the brief names an
executable check, and neither a reasoner's approval nor a delegate's narration substitutes
for that check's traceable output) is why this session ran the tiers itself and pasted the
real summaries above rather than delegating and relaying a claim. Its routing half
resolved to solo execution: the work is one frozen contract (`hook_input.py`) that every
other unit depends on, in a headless single-shot turn where contract v3 s22 forbids ending
on an unconsumed delegation.
