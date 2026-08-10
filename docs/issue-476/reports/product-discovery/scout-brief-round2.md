# Scout brief — issue #476 round 2 (wiring the H1 mechanism)

## Scope and mode

Skip condition does not apply generically (real design space: which hook
event/chokepoint fires `claim_scan`/`reexecution_gate`), but this is not a
product/exemplar space to sweep externally — it is a decision about this
repo's own deployed hook surface. Per scout-directive's product-shaped vs
own-deliverable-kind split: scouted this repo's OWN prior art for "how did
a CI-only `gates/*.py` check get ported to a session-side hook before,"
since two such ports already exist and are the strongest available
comparable-system evidence (stronger than an external blog post on hook
design). One stage, internal read, no external search — stated per the
directive's fallback-and-say-so requirement.

## Prior-art found (this repo, `on-the-record/hooks/`, read this session)

- `record-claim-guard.sh` (PreToolUse, matcher `Write|Edit|MultiEdit`):
  mirrors `gates/record_lint.py` checks at write time — its own header
  comment states this is "a write-time approximation of the same intent,
  not a byte-identical port: catch the claim shape at the moment it is
  typed, instead of at PR-review time days later" — derived: source read
  this session, quoting the header verbatim. It calls the same functions
  CI's `gates/ci.py` uses (its own comment cites issue #517 as the dedup
  point), not a second regex copy. Fails closed via an EXIT trap that
  remaps an unexpected exit code to a denial. Kill switch
  `ORCHESTRATE_OFF=1`. File read this session:
  `on-the-record/hooks/record-claim-guard.sh`.
- `pr-preflight.sh` (PreToolUse, matcher `Bash`, matches `gh pr create`/
  `gh pr edit`): intercepts the PR body at the moment it is set, before
  the PR exists — its own header names this "deny-before-effect." Fails
  OPEN on parse failure / missing tool / non-matching command (opposite
  fail posture from `record-claim-guard.sh`) — derived: source read this
  session, `on-the-record/hooks/pr-preflight.sh`.
- `role-test-claim-guard.sh` + `stop-gate.sh` (Stop event, per
  `on-the-record/hooks/hooks.json`'s `Stop` array, read this session):
  the last checkpoint before a session ends. `stop-gate.sh` reads only
  `last_assistant_message` (cheap, no subprocess). No existing Stop hook
  runs a subprocess re-execution today, per this session's own read of
  `hooks.json`'s full `Stop` array.

## Must-bes extracted (from this repo's own two successful ports)

1. No second copy of check logic — the hook calls the same `gates/*.py`
   function CI calls (avoids the drift `record-claim-guard.sh`'s own
   issue #517 note names as the reason it stopped carrying its own regex
   copies).
2. Fail posture matches blast radius — the write-time hook (cheap retry)
   fails closed; the hook blocking an irreversible external act (`gh pr
   create`) fails open on ambiguity, closed only on a positive hit.
3. A kill switch (`ORCHESTRATE_OFF=1`) is present on every ported guard —
   this repo's own house convention, not optional.

## Gap line

What the field (this repo's two existing ports) already gives for free:
a write-time chokepoint pattern and a pre-PR-creation chokepoint pattern,
both directly reusable shapes. What round two actually needs and neither
pattern currently does: call `claim_scan.scan_text()` or
`reexecution_gate.run_reexecution()` at all. Per `docs/issue-476/reports/
execution-observation.md`'s dated 2026-08-10 section (read this session):
no workflow file references either module, no file under
`on-the-record/hooks/` references either module, and
`reexecution_gate.main()` is invoked from nowhere but its own CLI/test —
found by that session's own search, cited there, re-confirmed by this
session's own `find`/`grep` producing the same empty match set.

## Adopt / skip

- Adopt: `pr-preflight.sh`'s deny-before-effect chokepoint shape as the
  wiring point for `claim_scan` (cheap, regex-only, no subprocess —
  matches its fail-open-on-ambiguity posture).
- Skip: running full `reexecution_gate` (subprocess re-execution in a
  SHA-pinned worktree) synchronously inside any `PreToolUse` hook — this
  changes the operator-visible latency of every `gh pr create` call,
  which is round two's actual design tension, addressed in the proposal
  rather than decided here.

Sources consulted (read this session, no external fetch):
`on-the-record/hooks/record-claim-guard.sh`,
`on-the-record/hooks/pr-preflight.sh`, `on-the-record/hooks/stop-gate.sh`,
`on-the-record/hooks/hooks.json`, `docs/issue-476/reports/
execution-observation.md`.

Stages used: one (internal prior-art read only, no external sweep —
reason stated above). Wall-clock well under the three-minute budget.
