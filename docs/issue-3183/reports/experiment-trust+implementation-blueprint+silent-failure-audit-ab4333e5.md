---
issue: 3183
role: experiment-trust+implementation-blueprint+silent-failure-audit-ab4333e5
author: experiment-trust+implementation-blueprint+silent-failure-audit-ab4333e5
skills: experiment-trust (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
upstream:
  - path: docs/issue-3127/reports/experiment-trust+adversarial-review+silent-failure-audit-50e9d932.md
    sha: fb0bb0d349cfe27837b03c7ed9e3bc470887c9c8
  - path: scripts/issue-3127/run_consumer_pair.py
    sha: fb0bb0d349cfe27837b03c7ed9e3bc470887c9c8
  - path: docs/issue-3127/decisions/pre-registration.md
    sha: fb0bb0d349cfe27837b03c7ed9e3bc470887c9c8
  - path: PR #3180 merge commit -- independent verification of PR #3176's H1 re-operationalization
    sha: d9932f1ca36ce079cee559a5ee42145a89d7ddf5
---

# issue-3183 — experiment-trust+implementation-blueprint+silent-failure-audit-ab4333e5 record

## What was done

Two scripts under `scripts/consumer-path/`, replacing issue #3127's
in-session skills toggle with a launcher-owned trust root (R007):

- **`prepare_arms.py`** -- prepares both arms and writes a manifest
  before any session is dispatched. Each arm gets a fresh
  `tempfile.mkdtemp()` HOME (never reused, always this run's own).
  `resolve_skill_files()` recursively hashes every regular file under a
  skills root (sha256, dot-directories like `.git`/`.pytest_cache`
  excluded as tooling noise, not corpus content) -- this is the "on"
  arm's evidence. `demonstrate_absence()` runs that identical scan
  against the "off" arm's skills root and records the method plus its
  literal result; the "off" arm's skills root is a path this module
  never creates at all (`skills_root_exists: false` in the manifest), so
  there is nothing on disk for a spawned process to read there, stub or
  otherwise -- no `build_stub_skill_repo()`-shaped artifact exists in
  this design. `make_on_arm()`/`make_off_arm()` fail closed
  (derived: `python3 -m pytest tests/test_consumer_path_trust_root.py::test_on_arm_rejects_empty_corpus -v` —
  result: PASSED, raises `ArmPreparationError` on an empty "on" corpus)
  and `build_manifest()` cleans up any HOME it already created before
  re-raising, so a rejected preparation leaks nothing either. The
  manifest is written to `--out`, then its own bytes on disk are hashed
  and the digest is written to a sidecar (`<out>.sha256`) "alongside" it.
  `--dry-run` runs the identical preparation and prints the manifest as
  JSON on stdout without touching `--out` or writing any sidecar. Every
  mode cleans up the temporary HOMEs it created; the real "on" skills
  root (external, not created by this process) is never touched or
  deleted.

- **`verify_manipulation.py`** -- the fail-closed manipulation check.
  Reads exactly two files: the manifest (recomputing its sha256 against
  the sidecar before trusting anything else in it) and a transport
  record (the argv + env a dispatching process actually handed to each
  arm's subprocess, captured by that process before `Popen()`).
  Cross-checks, per arm: argv invokes `spawn.py` (not a bare
  `claude -p`), `env["HOME"]` matches the manifest's prepared HOME, and
  `env[MUSTER_SKILL_REPO]` matches the manifest's prepared skills root.
  A missing manifest, missing sidecar, hash mismatch, missing transport
  record, malformed JSON on either side, a missing arm, or any
  HOME/skills-root mismatch raises `VerificationFailure`, reported as
  `{"manipulation_held": false, "pair_excluded": true, "reason": ...}`
  and a nonzero exit -- including a last-resort `except Exception` so an
  unanticipated error still excludes the pair in the same shape rather
  than a bare traceback.

- `tests/test_consumer_path_trust_root.py` -- skill-file hashing and
  dot-directory exclusion, absence demonstration against both a
  nonexistent and an existing-but-populated path, the exactly-one-
  difference property (on/off arms share an identical dispatch argv
  template and differ only in `HOME` + the skills-root env key), HOME
  cleanup on both the success and the `ArmPreparationError` path, the
  verify happy path, and every fail-closed path (missing manifest via
  both the Python API and the CLI subprocess, missing transport, hash
  mismatch, missing sidecar, HOME mismatch, skills-root mismatch,
  bare-CLI argv rejection, missing arm in transport, malformed manifest
  JSON) --
  derived: `python3 -m pytest tests/test_consumer_path_trust_root.py -q`
  — result:
  ```
  ..................                                                       [100%]
  18 passed in 0.82s
  ```

- `docs/issue-3183/decisions/instrument-limitations.md` -- the four
  honesty items the issue requires, written as limitations this
  instrument does not solve: model memorization of skill content,
  partial self-identification of skill-shaped output defeating full
  blinding, single-run-per-arm not being evidence (n>=5 paired trials is
  the stated design target), and operator independence (who ran the
  launcher must be recorded and disclosed).

Acceptance checks, run live against the final tree this same turn
(canonical: this turn's own tool output, reproduced by running each
command verbatim):

- acceptance: `python3 scripts/consumer-path/prepare_arms.py --dry-run
  --out /tmp/arms-smoke | python3 <the issue's json-load assertion
  script>` — result:
  ```
  OK
  ```
- acceptance: `python3 -m pytest tests/test_consumer_path_trust_root.py
  -q` — result:
  ```
  18 passed in 0.82s
  ```
- acceptance: `bash -c "grep -rn 'session'
  scripts/consumer-path/verify_manipulation.py | grep -vi
  'session_id\|# ' | grep -q 'log\|transcript\|workspace' && exit 1 ||
  exit 0"` — result: exit 0 (the file contains zero occurrences of the
  word "session" at all, confirmed by `grep -n session
  scripts/consumer-path/verify_manipulation.py` returning no lines)
- acceptance: `bash -c "test -f
  docs/issue-3183/decisions/instrument-limitations.md && grep -qi
  memoriz ... && grep -qi blind ..."` — result: exit 0
- must-not demonstration: `python3
  scripts/consumer-path/verify_manipulation.py --manifest
  <a-prepared-manifest-with-the-file-then-deleted> --transport
  <matching-transport.json>` — result: exit 1, stdout:
  ```
  {
    "manifest": "/tmp/verify-smoke/manifest.json",
    "manipulation_held": false,
    "pair_excluded": true,
    "reason": "manifest not found at /tmp/verify-smoke/manifest.json -- pair excluded",
    "transport": "/tmp/verify-smoke/transport.json"
  }
  ```

## Why

canonical: commit `d9932f1ca36ce079cee559a5ee42145a89d7ddf5` (merge of PR
#3180), read via `git show d9932f1c --stat` this session -- commit
subject: "issue-3127: verify PR #3176 -- H1 re-operationalization
Incorrect (forgeable trust root + stub-invocation misclassified as
leak) (#3180)"; body states verdict "Incorrect" with two independent,
live-reproduced trust-root failures: (1) "Forgeable trust root --
`collect_skill_invocation()`'s signal (a `Skill` `tool_use` line in
`<workspace>.session.*.log`) can be fabricated by a spawned session
appending one raw line to its own log via Bash. No sandboxing exists on
this machine (confirmed: `spawn.py`'s `Popen()` call has no `preexec_fn`
/`user=`/uid drop)..."; (2) "Stub-invocation misclassified as corpus
leak -- the harness's own `build_stub_skill_repo()` frontmatter-only
stub is, by design, invoked by every off-arm session that reaches it.
`compute_h1_manipulation()` cannot distinguish that from a genuine leak
-- both read as `invoked: true`...".

Issue #3127's trust root was a signal read from inside the spawned
process's own runtime output. PR #3180's independent verification
reproduced, live, a spawned session forging that exact signal by
appending one line to its own log via Bash -- `spawn.py`'s `Popen()`
call carries no uid isolation on this machine, so nothing stops a
process from writing into a file path it can discover and already owns.
The same PR found a second, independent failure: the harness's own
frontmatter-only "skills-off" stub is *designed* to be invoked by every
off-arm run, so the old manipulation check could not tell that
invocation apart from a genuine corpus leak -- both read identically.
Five repair rounds across issues #3127/#3129/#3176 did not move the
trust root outside the thing being measured; the design-research consult
this issue cites recommends the structural fix instead: the launcher
prepares and records both arms *before* either session exists, and
verification never reads anything the session could have written.

This design closes both PR #3180 failures by construction rather than
by patching the old one:
- **No stub exists.** The "off" arm's skills root is never created at
  all (a nonexistent path), not an empty directory and not a
  frontmatter-only file. There is no invocation-vs-leak ambiguity
  because there is nothing there to invoke.
- **The trust root is two files the spawned process never writes.**
  `verify_manipulation.py` reads only the manifest (hashed at write time
  by the launcher, checked against that hash before anything else in it
  is trusted) and a transport record that, by construction, must be
  captured before `Popen()` runs -- i.e. before a child process exists
  to write anything at all. Every artifact PR #3180 showed forgeable is
  excluded by `verify_manipulation.py` never opening those paths at all
  -- derived: `grep -n session scripts/consumer-path/verify_manipulation.py`
  — result: no output (zero matches).

Dispatch path, and how it differs from #3041/#3053: those measurements'
floor condition dispatched a bare `claude -p` call directly. This design
documents (`dispatch_command()`, tested via the exactly-one-difference
property) an argv shape of `python3 spawn.py --skills <name> ... --issue
<n> --model <model> -C <repo>` -- spawn.py with an orchestrator, never a
bare CLI call -- and `verify_manipulation.py` mechanically rejects any
transport record whose argv does not invoke `spawn.py`
(derived: `python3 -m pytest
tests/test_consumer_path_trust_root.py::test_bare_cli_argv_rejected_not_real_consumer_path -v`
— result: PASSED). Actually running the pairs through that dispatch
shape is out of this issue's scope (see Rationale for deviations); this
issue delivers the instrument and its trust root only, per the issue's
own scope note.

Every rejected evidence source considered, and why:

| Artifact | Why rejected |
|---|---|
| A `Skill`/tool_use line in the spawned process's own runtime output | PR #3180: live-reproduced forgeable via Bash append, no uid isolation on this machine (see canonical citation above) |
| The spawned process's own workspace directory (e.g. `.on-the-record/directive/*.md` byte counts, issue #3127's original H1) | Written by the spawned process itself; a process that can write files can write whatever this check would read |
| A frontmatter-only "skills present but empty" stub file | PR #3180 finding 2: indistinguishable from a genuine leak once invoked, and invocation is the expected behavior of a stub by design |
| Ledger/token-cost entries (`runs/ledger.jsonl`) keyed by issue+skill | Written by the same infrastructure the spawned process runs under during its own turn, after the process has already started -- not available before dispatch, and not launcher-exclusive |
| A PR body or deliverable text the spawned process authored | The spawned process's own output; nothing stops a process from writing arm-revealing text into it |
| **What this design uses instead**: the manifest (launcher-written, hashed, checked before trust) + a transport record (argv/env captured by the dispatching process before `Popen()`, i.e. before a child process exists) | Both are written by a process the spawned session is not and cannot become before it starts |

## What did not work

- Writing skill_files without excluding dot-directories: the first
  `resolve_skill_files()` implementation, run live against the "on"
  arm's real skills root (`$MUSTER_SKILL_REGISTRY_ROOT`), also hashed
  `.pytest_cache/*` tooling artifacts sitting inside that checkout
  alongside the real `SKILL.md` files -- derived: `find
  /home/jwjung/skill-registry/skills -maxdepth 2 -type f !  -path
  "*.pytest_cache*" | awk -F/ '{print $NF}' | sort | uniq -c` — result:
  `273 SKILL.md` (vs. `find ... -type f | wc -l` — result: `357` total,
  including `.pytest_cache`'s 5 files and its subtree). Not incorrect,
  but noisy and not "skill files" in the sense the issue means. Fixed by
  skipping any path with a dot-prefixed component.
- `_cleanup()`'s first version used `shutil.rmtree(d,
  ignore_errors=True)` -- a cleanup failure would have been silently
  absorbed with no trace. Replaced with a per-directory try/except that
  prints a warning to stderr on failure.
- The first `build_manifest()` had `make_on_arm()`/`make_off_arm()` each
  create their own HOME internally before validating and possibly
  raising `ArmPreparationError`; running
  `test_on_arm_rejects_empty_corpus` and then checking `/tmp` caught
  this live -- derived: `ls -la /tmp | grep consumer-path-` — result
  (before the fix, this session): 4 leaked
  `consumer-path-on-home-*` directories, 0 `off-home` ones (the "off"
  arm's home was never created that call, since the "on" arm's
  validation raises first, before `off`'s `mkdtemp()` runs). Fixed by
  having `build_manifest()` create both HOMEs itself up front, track
  them immediately, and clean up everything it had created before
  re-raising on any `ArmPreparationError`. derived: `ls /tmp | grep -c
  consumer-path-` — result (after the fix, re-run of the full suite plus
  a manual `--dry-run`): `0`.
- `verify_manipulation.py`'s first version left the sidecar read with no
  try/except at all, and the transport-record read caught `OSError` and
  `json.JSONDecodeError` but not `UnicodeDecodeError` -- an unreadable
  sidecar or non-UTF-8 transport file would have escaped as a raw
  traceback instead of the expected `{"pair_excluded": true, ...}`
  shape. Hardened both, and added a last-resort `except Exception` in
  `main()` so no unanticipated error can exit 0 or skip the JSON
  verdict.

## Rationale for deviations

- The issue's scope note excludes running the pairs and scoring them
  from this issue; consistent with that, this session did not wire a
  real dispatcher that calls `Popen()` and writes a transport record
  from an actual `spawn.py` invocation. `verify_manipulation.py`'s
  contract for that record (argv/env captured before `Popen()`) is
  fully specified and tested against fixture transport records built to
  that same contract (`tests/test_consumer_path_trust_root.py`'s
  `_transport_for()`); wiring a live dispatcher to produce one for a
  real paired run is the separate "running the pairs" work the issue
  itself carves out.
- The transport record's `captured_before_dispatch` field is
  self-reported by whatever writes it, not independently proven by this
  module (which never runs a dispatcher itself and so cannot observe
  when `Popen()` was actually called). Stated here and in
  `docs/issue-3183/decisions/instrument-limitations.md`'s operator-
  independence item, not silently assumed solved.

## Upstream basis

- `docs/issue-3127/reports/experiment-trust+adversarial-review+silent-failure-audit-50e9d932.md`
  and PR #3180 (commit `d9932f1ca36ce079cee559a5ee42145a89d7ddf5`): the
  live-reproduced forgeability findings this issue's design replaces the
  trust root to avoid repeating (see canonical citation in "Why").
- `scripts/issue-3127/run_consumer_pair.py`: prior art for dispatch shape
  (`spawn_command()`) and for the #3041/#3053 bare-`claude -p` floor
  condition this issue's requirement names as invalidating that earlier
  measurement -- not reused directly (that harness's per-skill stub
  design is exactly what this issue replaces), but its dispatch-argv
  pattern is what `dispatch_command()` here follows.
- `docs/issue-3127/decisions/pre-registration.md`: source for the n>=5
  paired-trials framing in `instrument-limitations.md`'s item 3.

## Open findings

None -- nothing open here requires a resolution path; the remaining
work (wiring a real dispatcher) is scoped out of this issue by its own
scope note and tracked under Next steps below, not as an open finding
against this deliverable.

## Skill verdicts

skill-verdict: implementation-blueprint — applied: invoked; classified
both scripts as the `pipeline` archetype (backend/external=no/logic=
transform/async=no -> pipeline, "structure follows stages, not layers")
and followed its module layout (source/extractor stage, transformation
stage, idempotent sink, explicit error channel) when structuring
`prepare_arms.py`'s create-HOME -> resolve-or-demonstrate-absence ->
assemble-manifest -> hash-and-write stages and
`verify_manipulation.py`'s load-manifest -> check-integrity -> load-
transport -> cross-check stages; 2 units, well under the 5-unit fan-out
threshold, built solo in this session.

skill-verdict: silent-failure-audit — applied: invoked; audited both
scripts' planned error-handling sites before and after writing them per
the skill's Handled/Silently-Absorbed/Unreachable classification.
derived: same-commit "What did not work" section above, three
Silently-Absorbed sites named there with their fixes
(`shutil.rmtree(..., ignore_errors=True)` in `_cleanup()`; the leaked
temp HOME on the `ArmPreparationError` path in the original
`build_manifest()`; the two narrower exception catches in
`verify_manipulation.py`'s sidecar/transport reads than `load_manifest()`
already had).

other mounted skills: not triggered. experiment-trust's own trigger
condition gates on interpreting a variant-comparison result; canonical:
`gh issue view 3183` output, read at the start of this session, states
"this issue delivers the instrument and its trust root only. Running
the pairs and scoring them is separate work" -- no variant-comparison
result exists yet in this session for that trigger to fire against. Its
Twyman's-law framing is instead cited, not invoked, in
`instrument-limitations.md`'s operator-independence item.

## Next steps

- A future session wires a real dispatcher: calls `Popen()` for both
  arms using `prepare_arms.py`'s manifest (HOME + skills-root per arm),
  writes the transport record `verify_manipulation.py` already expects
  (argv + env, captured before `Popen()`), and runs `spawn.py watch
  --follow` per arm -- the "running the pairs" work this issue's scope
  note excludes.
- That session should also decide, and record, who operates the
  launcher for the first real pairs (the operator-independence honesty
  item), and should not interpret any single pair's result as evidence
  either way until at least 5 paired trials have been verified
  (single-run-per-arm honesty item).
- loop_state is set to `complete` for this deliverable's own acceptance
  criteria only (code + tests + docs on this branch), not for the
  broader R007 measurement, which needs the dispatcher work above first.
  acceptance: `python3 -m pytest tests/test_consumer_path_trust_root.py -q`
  — result:
  ```
  18 passed in 0.82s
  ```
