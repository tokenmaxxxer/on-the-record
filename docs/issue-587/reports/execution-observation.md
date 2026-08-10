# Issue #587 step 3 — execution-observation record (phase 2, third re-verification round)

kind: execution-observation
loop_state: handed-off

## Independence statement

This role did not author or edit the observed artifact this session. Nothing under gates/,
on-the-record/, spawn.py, or roles/ was touched by this record — the fixture drive ran the
shipped code as-is (commit 16773ec, the merge of PR #606) from a disposable temp-dir fixture
repo under the session scratchpad, never this repository's own board. The above precedes every
verdict below.

## What was done

Re-ran the step-3 fixture-target-repo e2e drive per the still-standing approved methodology
(docs/issue-587/proposals/execution-observation.md), scoped to event 4 per the prior round's own
resolution path (commit 08d874e's record, "## Resolution path": "A remediation-round PR wires
`_remediation_merge_sweep` into a caller the shipped surface actually exposes ... then this role
... re-runs this same fixture drive's Steps A-B ... and confirms a 'Remediation merged' comment
appears in gh.log through the shipped entry point"), since PR #606's diff (`git show 53f9d16
--stat`, read this session) touched only spawn.py, test_spawn.py, and
docs/issue-587/reports/implementation.md — confirmed no change to
on-the-record/hooks/delegated-judgment-gate.sh or gates/remediation_spawn.py, the code the other
four events depend on.

Built a fresh disposable fixture target repo under the session scratchpad, drove the shipped,
unmodified `spawn.py reconcile --remediation-merged --issue 9999 -C <fixture>` CLI verb against a
merged remediation branch, then isolated the result by (a) grepping spawn.py's sole `ROOT`
assignment and (b) calling `_remediation_merge_sweep` directly with the correct root to separate
"the posting logic is broken" from "the wiring is broken." Full fenced output and the updated
five-event table are in
docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md ("## Round 3" section,
written first, this file second, per the phase-2 record-requirements facet).

## Why

The operator relayed (2026-08-10) that PR #606 wired the `reconcile --remediation-merged` CLI
verb and asked for a third step-3 re-verification before #587 can close — per this role's own
prior resolution path, verification must be by independent execution against the fixture through
the shipped entry point, never by accepting PR #606's own implementation.md claims.

## Upstream basis

docs/issue-587/proposals/execution-observation.md (this role's own approved phase-1 proposal,
governing this round too since scope and write set are unchanged); commit 08d874e (this role's
own prior-round record and its resolution path); PR #606 (merged 2026-08-10, commit 53f9d16,
`git show 53f9d16` read this session — added the `--remediation-merged` argparse flag, threaded
`a.remediation_merged` into `roster_reconcile`, and added `RosterReconcileRemediationMergedCLI`
to test_spawn.py); docs/issue-587/proposals/implementation-remediation-merged-wiring.md (PR #605's
approved proposal, read this session).

## Verdicts

### Outcome

Per this role's spec's recomputation rule (roles/specs/execution-observation.spec.json: "overall
verdict = the worst-case result across all cited test entries"), the outcome is the worst case
among the five step-level results below: event 4 (Remediation PR merged) still does not fire on
the shipped code's exposed surface, so the recomputed outcome is **still failed** — the shipped
code (spawn.py, as merged in PR #606) does not fully satisfy issue #587's "end to end ...
exercising the five issue-timeline firing events" acceptance criterion, per the drive captured in
docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md ("## Round 3", "Per-event
table" subsection).

The other four events (PR-opened, verdict-synthesized, remediation-routed, escalation) carry
forward as passing, unaffected by PR #606's write set (diff-confirmed: `git show 53f9d16 --stat`
shows only spawn.py, test_spawn.py, and docs/issue-587/reports/implementation.md changed — the
gate script and remediation_spawn.py that those four events depend on are untouched —
e2e-fixture-target-repo.md, "## Round 3 — ### Scope of this round").

### Trajectory

Sound for this round specifically. The remediation-round proposal PR #605 was approved (this
session read `docs/issue-587/proposals/implementation-remediation-merged-wiring.md`'s presence
and PR #606's own implementation.md, which states it "follows the approved proposal's 'What will
be done' exactly") before PR #606's phase 2 began. This role's own re-verification proceeds
without a fresh `APPROVE issue-587/execution-observation` comment on this specific round; as in
the prior round, the operator's direct task assignment to this session plus the unchanged
scope/write-set inherited from the still-standing prior approval on this same proposal is the
basis relied on here — noted plainly rather than asserted as a genuine fresh approval, since no
new exact-string APPROVE for execution-observation was found on the issue thread after PR #603
merged (this session did not re-search the full comment thread beyond what the prior round's
record already established; carrying that finding forward rather than re-asserting it as newly
confirmed). The overall #587 chain otherwise repeats the already-verified pattern: architecture
(PR #589) and implementation (PR #592, #601, #603, #605) each had their own approval gates per
the prior round's record.

### Step

One confirmed deficiency, changed in kind from both prior rounds; the four already-verified
subjects carry forward unchanged from the prior rounds' records and are not re-asserted here as
fresh findings:

- subject: `spawn.py`'s `_remediation_merge_sweep` call site inside `roster_reconcile`
  (`spawn.py:2183`) and the `--remediation-merged` CLI flag's `-C`/`--cwd` threading
  test: fixture-repo drive, Steps A-C (shipped `--help` flag listing and call-site grep, then
  driving `reconcile --remediation-merged --issue 9999 -C <fixture>` against a merged fixture
  branch, then grepping `spawn.py`'s sole `ROOT` assignment to confirm it is never reassigned from
  `a.cwd`), in e2e-fixture-target-repo.md, "## Round 3"
  result: failed
  assertedBy: execution-observation (this role, this session)

- subject: `_remediation_merge_sweep`'s posting logic itself (message format, idempotency
  marker), called directly with the fixture's own root rather than via the CLI's `-C`-ignoring
  path
  test: fixture-repo drive, Step D (direct function call with the correct root against a merged
  fixture branch), in e2e-fixture-target-repo.md, "## Round 3"
  result: passed
  assertedBy: execution-observation (this role, this session)

Blameless four-part shape for the confirmed deficiency:
- impact: identical in kind to both prior rounds' impact — issue #587's acceptance criterion
  ("all five issue-timeline events ... observed on the git surface") is still not met for a real
  target repo. An operator running the shipped `reconcile --remediation-merged --issue N -C
  <target-repo>` command against any repo other than wherever `spawn.py` itself happens to be
  checked out will see exit 0 and silence — no error, no comment, no indication that `-C` was
  ignored — even though the underlying posting logic is correct and the CLI flag now exists.
- timeline: PR #605's approved proposal (implementation-remediation-merged-wiring.md) chose the
  CLI-verb shape and PR #606 built the flag, the `roster_reconcile` delegation, and a passing
  test (`RosterReconcileRemediationMergedCLI`, per implementation.md) — but that test drives
  `roster_reconcile(issue=587, remediation_merged=True)` directly with `spawn.ROOT` monkeypatched
  to the test's own temp dir (test_spawn.py, `spawn.ROOT = self.root` in `setUp`, read via `git
  show 53f9d16` above), never through `main()`'s actual `-C`/`a.cwd` argument-parsing path. The
  test therefore could not have caught this gap: it exercises the same code shape this round's
  Step D isolated (correct logic, correct root passed directly) rather than the CLI's real
  argument-to-root threading that Step B-C exercised and found broken.
- root cause: `_remediation_merge_sweep(ROOT, issue)` at `spawn.py:2183` references the
  module-level global `ROOT = Path(__file__).resolve().parent` (`spawn.py:37`, the file's only
  assignment to that name) instead of the `root` value implied by the CLI's own `-C`/`--cwd`
  argument (`a.cwd`, threaded explicitly to every other cwd-sensitive role dispatch in `main()`,
  e.g. `spawn.py:3521,3644,3648,3650,3694`). Every prior round's fix targeted the observable
  symptom (no posting logic, then no caller) without checking whether the eventual caller would
  actually receive the caller-supplied target directory — it does not.
- action item: a fourth remediation round, routed to the same owners as the prior two rounds, to
  thread `a.cwd`/`Path(a.cwd).resolve()` through `roster_reconcile`'s `remediation_merged` branch
  down to `_remediation_merge_sweep`'s `root` parameter (mirroring how every other cwd-sensitive
  role dispatch in `main()` already does this), and to update
  `RosterReconcileRemediationMergedCLI` (or add a sibling test) to drive the real CLI/argparse
  entry point with an explicit `-C <temp-dir>` rather than monkeypatching `spawn.ROOT` directly —
  followed by a re-run of this same fixture drive's Steps A-C confirming the comment posts via
  `-C` against a fixture repo distinct from wherever `spawn.py` itself resides.

## Open findings

- Event 4 (Remediation PR merged): `_remediation_merge_sweep` is now called from a real CLI
  entry point (`reconcile --remediation-merged`), but that entry point never threads its own
  `-C`/`--cwd` argument to the function's `root` parameter — it silently operates against
  `spawn.py`'s own module-level `ROOT` constant instead, so on any fixture or client repo other
  than wherever `spawn.py` is physically checked out, event 4 still never fires, with no error.
  See Step verdict above for the full blameless shape and the fixture evidence.

## Next steps

Recommend a fourth remediation round (not closure) targeting the `-C`-threading gap above. This
PR does not carry "Closes #587" for that reason — the orchestrator reopens work on this issue per
the still-open finding.

## Resolution path

A remediation-round PR threads `a.cwd` through `roster_reconcile`'s `remediation_merged` branch
into `_remediation_merge_sweep`'s `root` parameter, and its own test drives the change through
the real CLI/`main()` path with an explicit `-C <temp-dir>` rather than monkeypatching `ROOT`
directly. Then this role (or a fresh execution-observation session) re-runs this same fixture
drive's Steps A-C and confirms a "Remediation merged" comment appears in `gh.log` through
`reconcile --remediation-merged --issue N -C <fixture>` run against a fixture repo distinct from
`spawn.py`'s own checkout location, before recommending closure.
