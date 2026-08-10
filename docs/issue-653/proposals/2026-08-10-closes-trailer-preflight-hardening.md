# ADR: auto-attach Closes trailer at the merge broker (issue #653)

## Context
Phase-2 delivering PRs must carry `Closes #<n>`. `pr-preflight.sh` already
denies at `gh pr create`/`edit` time when this is missing, and
`contract-guard.sh` denies again at `gh pr merge` time, round-scoped per
#577. See [survey.md](../reports/architecture/survey.md) for the
code-level detail; the survey itself does not need revision — the facts it
records (no hook here rewrites `Bash` tool input; `pr-preflight.sh`'s
`phase2` check is unscoped; its `--body-file` read races the write) are all
still accurate.

**Revision (orchestrator relay, consumer-session evidence, 2026-08-10,
issue #653 comment):** the phase-1 direction above (harden the pre-create
*refusal*) was reviewed against five real recurrences of the same failure
in one day: detection already fires correctly every time — the session
simply never gets a working `Closes #n` line into the merged PR, no matter
how loudly preflight or contract-guard object, because a refusal only helps
a session that is *capable* of correcting itself, and the evidence is that
it structurally isn't. The fix this revision adopts instead: the merge
broker attaches the trailer itself, mechanizing the exact
edit-body-then-merge workaround a human has been doing by hand 6+ times.
Judged against operating-principle-5 (don't route around a gate by tightening
it instead of removing the friction) — refusal-hardening tightens a gate a
non-compliant session still can't pass; auto-attach removes the need to
pass it. Deadlock-freedom is the bar: a decided merge must not stall even
if the session under review never once writes the trailer itself.

This is **not** the previously-rejected "rewrite the intercepted Bash
command" auto-attach. `contract-guard.sh` fires as a `PreToolUse` hook on
`gh pr merge` and already shells out to `gh` read-only (`gh pr view`,
`gh issue view`) before deciding allow/deny (`contract-guard.sh:63-71`,
`:141-147`). Calling `gh pr edit <pr> --body ...` as one more `gh` call from
inside that same hook, *before* returning `allow` for the merge that was
about to run anyway, needs no command-rewrite capability — the intercepted
`gh pr merge` command itself is never touched, only a side effect the hook
performs ahead of allowing it. The survey's "no hook rewrites Bash input"
finding stays true; it just doesn't rule this out, because this isn't that.

## Decision
Replace the phase-2 deny in `contract-guard.sh` with an auto-attach-then-allow:

1. **On a would-deny phase-2 merge, edit the PR body instead of denying.**
   At the point the current code calls `deny(...)` (missing/wrong
   `Closes #<issue>`), instead run
   `gh pr edit <pr> --body "<original body>\n\nCloses #<issue>"` (or, if a
   *wrong* `Closes #<m>` is present, correct it in place rather than
   appending a duplicate), check the edit's exit code, and only then `exit 0`
   to let the merge proceed. This is the same repo-write privilege the hook
   already exercises implicitly (it's running inside the same `gh`-authenticated
   environment that is about to execute `gh pr merge`) — no new credential
   or scope is introduced.
   - If the `gh pr edit` call itself fails (network, permissions, `gh` not
     writable), fall back to the existing `deny(...)` — auto-attach must
     never silently wave through a merge whose body it failed to fix; failing
     open here would reintroduce exactly the "closes trailer missing on a
     merged PR" defect this issue exists to eliminate. Deny-on-write-failure
     is the one place this design still needs the old refusal path, so it
     stays in the code, demoted from primary mechanism to fallback.
2. **Keep `pr-preflight.sh`'s pre-create refusal as an early, non-blocking-of-merge
   signal.** It still gives a role session the earliest possible feedback
   (before a PR even exists) when it's capable of correcting itself — cheap
   and still useful — but per the revised judgment criterion it is no longer
   load-bearing for correctness: even a session that never sees or acts on
   that refusal still merges with a correct trailer, because
   `contract-guard.sh` fixes the body at the one point (merge) nothing
   downstream can route around. Its round-scoping/body-file gaps (phase-1
   items 1–2 of the prior revision) are downgraded from "must fix" to
   "nice to have, out of scope for this pass" — they only sharpen a
   best-effort early warning now, not the actual guarantee.
3. **Round-scoping already exists where it now matters.** The auto-attach
   only needs to fire on a *genuinely* phase-2 merge; `contract-guard.sh`'s
   phase2 determination is already round-scoped (#577,
   `contract-guard.sh:119-165`) and untouched by this change — the
   deny-vs-attach decision reuses that same signal computation, so no new
   phase-2 detection code is added.

## Consequences
- The deadlock this issue reports cannot recur structurally: the one
  broker that actually executes every merge is also the one place that
  guarantees the trailer, independent of what any spawning session did or
  didn't write.
- `contract-guard.sh` goes from read-only-then-decide to
  read-then-write(if needed)-then-decide — a small increase in blast radius
  (a bad edit could corrupt a PR body) bounded by: it only ever appends/
  corrects one `Closes #<n>` line, and any edit failure still denies rather
  than guessing.
- `pr-preflight.sh` is unchanged in this pass; its previously-scoped
  hardening work (round-scoping port, body-file race fix) is deferred, not
  cancelled — worth doing later as defense-in-depth, but not required to
  close #653 under the revised criterion.
- No new install/CI dependency; still zero-install, `gh` + `python3` only.
- Residual risk: `gh pr edit` itself can race a concurrent human edit to the
  same PR body between contract-guard's read and its write — same class of
  TOCTOU already accepted for the existing read-only checks in this hook,
  and bounded the same way (fail closed on the write, not blind-append).

## Alternatives considered
- **Harden the pre-create refusal only (this proposal's prior direction).**
  Rejected on revision: refusal only helps a session capable of correcting
  itself in response, and the operator-relayed evidence (5 recurrences in
  one day, including a spawn-and-respawn case that produced 0 fixes) shows
  that premise doesn't hold in practice. A stronger refusal is still a
  refusal — it does not change what a non-compliant session does next.
- **Auto-attach via rewriting the intercepted `gh pr create`/`gh pr merge`
  Bash command in flight.** Still rejected: no hook in this deployment
  returns a modified tool input, and this ADR's chosen mechanism doesn't
  need that capability — it acts via a plain `gh pr edit` side effect, not
  input rewriting.
- **Auto-attach via a wrapper script the role is told to call instead of
  `gh` directly.** Rejected: reintroduces the model-compliance dependency
  #653 exists to eliminate.
- **Move the check to CI (GitHub Actions).** Rejected by the issue's
  zero-install/no-Actions constraint, and because CI runs post-merge-attempt
  at the earliest, later than the `PreToolUse` hook that can still act
  before the merge lands.

## C4 (context/boundary)
```
[Role session (Claude Code, this repo)]
        | Bash: gh pr create --body ...       | Bash: gh pr merge <pr>
        v                                     v
[pr-preflight.sh]                     [contract-guard.sh]  (the broker)
   pre-create refusal,                   round-scoped phase2 signal (#577,
   best-effort/non-blocking               unchanged)
   (unchanged this pass)                     |
        |                              would-deny? -> gh pr edit <pr> --body
        v  allow / deny(reason)              (attach/correct Closes #<n>)
[gh CLI] --(if allowed)--> [GitHub PR]        |
                                          edit ok? -> allow (merge proceeds
                                                       with correct body)
                                          edit failed? -> deny (fallback,
                                                       unchanged old path)
```
Boundary: this issue touches only `contract-guard.sh`'s merge-time
decision (deny -> attach-then-allow, fallback to deny on write failure); it
does not add any new hook, script, or CI job, and leaves `pr-preflight.sh`
itself unchanged in this pass.

## Hand-off
The `gh pr edit --body` shape stays inside `on-the-record/hooks/` — no
`api-design` hand-off needed. No performance budget is at stake (one
additional `gh` call, only on the would-deny path) — no
`performance-engineering` hand-off needed. Implementation (phase 2, after
approval) stays within this same architecture role's branch per contract
v3 s19.
