---
issue: 2908
role: silent-failure-audit-ef3215b3
author: silent-failure-audit-ef3215b3
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: same-commit
    sha: same-commit
---

# issue-2908 — silent-failure-audit-ef3215b3 record

## What was done

Established (with evidence, per the issue's own instruction not to assume
the answer) that the engine cannot be moved wholly inside the plugin
payload in this delivery. Two call sites hardcode spawn.py as sitting one
directory *above* CLAUDE_PLUGIN_ROOT: `on-the-record/commands/consult.md:10`
assigns `ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..`, and
`on-the-record/hooks/absorbed-branch-recut-guard.sh:55` builds
`spawn_py="${CLAUDE_PLUGIN_ROOT:-}/../spawn.py"` the same way. The two
`gates/` trees (root `gates/` vs `on-the-record/gates/`) are already a
separate, non-identical pair. Folding 17 root modules plus `gates/`,
`ledger/`, `scripts/`, `test/` into `on-the-record/` is a real migration
across every one of those call sites, unverifiable end-to-end in this
session (no way to exercise Claude Code's actual `/plugins update`
installer here). Ruled out for this delivery on that evidence, not
assumed impossible; see "Open findings" for the concrete follow-up.

derived: `grep -n "CLAUDE_PLUGIN_ROOT}/\.\." on-the-record/commands/consult.md on-the-record/hooks/absorbed-branch-recut-guard.sh`
```
on-the-record/commands/consult.md:10:`ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..` 로 두고, 아래는
on-the-record/hooks/absorbed-branch-recut-guard.sh:55:spawn_py="${CLAUDE_PLUGIN_ROOT:-}/../spawn.py"
```

Delivered the fallback the issue names as acceptable: skew now announces
itself, the missing half of the update path is wired in (automatically,
respecting the existing zero-sessions discipline), and the retired
`muster` candidate is gone from the search order.

Code changes, all in `on-the-record/`:
1. **Skew visibility** (`hooks/self-update.sh`): the SessionStart fetch
   already computed `rev-list --count HEAD..@{u}`; it only ever went to
   `.pull-check`, a file nothing reads. Added one `printf` to the hook's
   own stdout in the `pull=deferred:*` branch — SessionStart hook stdout
   reaches the session, so a skewed install is now visible every session
   it persists. A matched install (`pull=ok`) stays silent, unchanged.
2. **Automatic update trigger** (`hooks/poll-rearm.sh`,
   `poll_rearm_arm_if_due()`): on the same poll-due TTL-gated tick that
   already launches the watchdog detached, also launches
   `python3 spawn.py self-update` detached (issue #2749's CLI, output to
   the same `poll-watchdog.log`). That CLI already refuses (no
   working-tree change) whenever the roster shows a live spawned session
   — this only gives it an automatic, session-independent trigger where
   previously nothing called it but a human's memory. Not an unconditional
   pull: `self_update_pull_cli()`'s own guard is untouched.
3. **`muster` retired from the search order**: removed the two-line
   candidate from all 8 shell implementations
   (`decision-queue-stopgate.sh`, `impact-guard.sh`, `merge-allow-gate.sh`,
   `plan-order-guard.sh`, `poll-rearm.sh`, `quality-bar-gate.sh`,
   `self-update.sh`, `spawn-allow-gate.sh`) and the one Python
   implementation (`pretooluse_dispatcher.py`). An install that used to
   resolve there now falls through to the self-clone candidate one step
   later — never staler than what `muster` could offer.
4. **The real `~/.claude/tokenmaxxxer/muster` clone on this machine**:
   renamed (not deleted) to `~/.claude/tokenmaxxxer/muster.retired-issue-2908`,
   out of every search path.

derived: `grep -rn "tokenmaxxxer/muster" on-the-record/` — result: no
matches (rc=1), confirming the candidate is gone from all 9 resolve
implementations.

Tests: extended `test/test_self_update_working_tree_untouched.py` with
stdout assertions for the skew/matched cases; added
`test/test_engine_checkout_resolve_muster_retired.py` (2 new tests: a
present-alone `muster` clone is never resolved, and an own-clone
candidate wins over a present `muster` clone).

derived: `python3 -m pytest test/test_self_update_working_tree_untouched.py test/test_engine_checkout_resolve_muster_retired.py -q`
```
5 passed in 0.89s
```

Live acceptance demonstrations (all executed in this session against
real local git fixtures and the real machine, not simulated in prose):
- **Skewed install reports, matched install is silent**: a local bare
  clone of this repo, checked out 8 commits behind, run through the real
  `on-the-record/hooks/self-update.sh`, printed on stdout: "[self-update]
  engine checkout 8 commits behind origin/main (...) -- hooks may be
  current while the engine they call is not; ...". The same hook against
  a freshly matched clone printed nothing and recorded `pull=ok`.
- **Automatic pull, and its own safety guard, both real**: running
  `python3 spawn.py self-update -C <skewed clone>` — the exact command
  `poll-rearm.sh` now auto-dispatches on a due tick — against that same
  skewed clone correctly refused with "self-update 거부: 살아있는 세션이
  있다고 판단함", naming this very session's own claim-only pid/workspace
  — proving the #2670/#2749 zero-sessions guard fires for real, unmocked
  input. The zero-live-sessions success path is covered by the existing
  test file `test/test_self_update_pull_gate.py` (isolated via roster
  monkeypatching, since this session itself always registers as a live
  claim and cannot demonstrate the success path against itself).
- **Empty state — clean install self-clones current**: with `HOME`
  redirected to an empty scratch dir and no `TOKENMAXXXER_CHECKOUT`,
  `poll_rearm_resolve_checkout()` self-cloned into
  `~/.claude/tokenmaxxxer/on-the-record`, `0` commits behind
  `origin/main`.
- **muster's real disposition, before/after**: `git -C
  ~/.claude/tokenmaxxxer/muster rev-list --count HEAD..origin/main` = `3723`
  before; after `mv` to `muster.retired-issue-2908`, the same command
  against the old path fails ("fatal: cannot change to
  '.../muster'"), confirming the path is no longer resolvable there —
  the code no longer searches for it either.
- **Population — which candidates resolve on this real machine**: for a
  hook path under the real marketplace install
  (`~/.claude/plugins/marketplaces/tokenmaxxxer/on-the-record/hooks/`),
  candidates 2 (ancestor probe) and 3 (marketplace root) both resolve
  (this machine's marketplace clone happens to be a full, maintainer-kept
  clone with `spawn.py` present); candidate 4 (own clone) is absent;
  candidate 5 (`muster`) is no longer checked. An install with *only* a
  `muster`-named directory present now falls through to a fresh
  self-clone instead of resolving to it.

canonical: this session's own transcript in this turn — the
`self-update.sh` / `spawn.py self-update` / `poll_rearm_resolve_checkout`
invocations above and their captured stdout, run directly against local
bare-repo fixtures and the real `~/.claude/tokenmaxxxer/muster` path.

## Why

The issue's non-goals rule out the two easy answers: no unconditional
`git pull` under running sessions (#2749/#2670), and no manual-step
documentation (the exact unwritten workaround already failing every
install but the maintainer's). That leaves exactly the shape delivered:
make the drift observable, and give the existing safe-pull command
(`spawn.py self-update`) a caller that isn't a human's memory.

Piggybacking the auto-update on the poll-due TTL gate (rather than adding
a new cadence, e.g. inside `monitors/poll-heartbeat.sh`'s own tick loop)
keeps the fix inside the existing per-turn hooks (`directive.sh`,
`stop-poll-rearm.sh`) that fire on every host, not only hosts where the
Monitor tool is available — `poll-heartbeat.sh` is explicitly
session-bound to Monitor support (its own header comment), so wiring
there would have left non-Monitor installs exactly as stuck as before.
It also adds no new overhead: the TTL gate, the git fetch, and the
behind-count were already being computed every session; this only adds
where the already-computed result goes.

`muster`'s disposition: `git -C ~/.claude/tokenmaxxxer/muster remote -v`
showed its origin is `tokenmaxxxer/muster` — a different, dead repository
from `tokenmaxxxer/on-the-record` — so its "N behind origin/main" can
never reconcile; it isn't merely stale, it's structurally unable to catch
up. Renamed rather than deleted: it carries 178 commits never pushed
anywhere (`rev-list --count origin/main..HEAD` = `178`), and a rename is
reversible if that history turns out to matter later, at zero cost to the
fix (nothing resolves to it either way now).

derived: this session's own `git -C ~/.claude/tokenmaxxxer/muster remote -v`
and `git -C ~/.claude/tokenmaxxxer/muster rev-list --count origin/main..HEAD`
output, run in this turn before the `mv`.

Left `self-update.sh`'s fetch-failed/rev-list-unknown branches exactly as
loud as before (file-only, per the file's own "Quiet; offline failure is
fine" design intent) rather than making them stdout-loud too — the
acceptance criterion is skew visibility specifically, and expanding scope
to network-failure visibility (a real but different gap) risked
"quieter/louder" invariant drift for a case the issue didn't ask about.

## What did not work

None.

## Upstream basis

This record's own commit carries all cited code changes
(`on-the-record/hooks/self-update.sh`, `on-the-record/hooks/poll-rearm.sh`,
`on-the-record/hooks/pretooluse_dispatcher.py`, the 7 other resolve-order
shell files, and the two test files) — `sha: same-commit` per contract §1.
Base commit this work started from:
`fa52c0c81d3c529e6e39b8e9b9a6c876fc263423`.

## Open findings

1. **Full payload-move remains open**, tracked here as a finding, not
   filed as a new issue by this record. Resolution path: a follow-up that
   (a) audits and rewrites every `${CLAUDE_PLUGIN_ROOT}/..`-shaped
   assumption (the two call sites cited under "What was done"), (b)
   reconciles the two `gates/` trees, (c) is verified against a real
   `/plugins update` installer run, not simulated locally.
2. **Self-clone failures are silently absorbed** across the 7 resolve
   implementations that carry a self-clone fallback at all (2 of the 9
   candidate-search implementations — `quality-bar-gate.sh`,
   `spawn-allow-gate.sh` — stop at "not found" with no clone attempt, per
   the `derived:` grep below). Concretely,
   `on-the-record/hooks/pretooluse_dispatcher.py:149-157`:
   ```python
           try:
               os.makedirs(os.path.dirname(own), exist_ok=True)
               subprocess.run(
                   ["git", "clone", "-q",
                    "https://github.com/tokenmaxxxer/on-the-record.git", own],
                   capture_output=True, timeout=120,
               )
           except Exception:
               pass
   ```
   a clone failure (network down, disk full, permission error) leaves
   `result` empty with zero diagnostic. The 6 shell implementations that
   do clone carry the equivalent pattern.
   derived: `grep -n "git clone -q" on-the-record/hooks/*.sh` — result:
   ```
   on-the-record/hooks/decision-queue-stopgate.sh:55:  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
   on-the-record/hooks/poll-rearm.sh:50:  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
   on-the-record/hooks/merge-allow-gate.sh:72:  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
   on-the-record/hooks/plan-order-guard.sh:56:  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
   on-the-record/hooks/impact-guard.sh:49:  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
   on-the-record/hooks/self-update.sh:30:  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
   ```
   (`quality-bar-gate.sh` and `spawn-allow-gate.sh` have no `clone` hit at
   all — confirmed by `grep -n clone on-the-record/hooks/quality-bar-gate.sh
   on-the-record/hooks/spawn-allow-gate.sh` returning nothing.) Every hit
   above redirects stderr to `/dev/null` with no marker written on
   failure, matching the Python site above.

   This finding surfaced from this session's own silent-failure-audit
   pass (Skill tool invocation, this turn) over the files this delivery
   touches and their immediate neighbors — pre-existing, not introduced
   or modified by this delivery, and left as-is because it mirrors the
   codebase's established fail-open philosophy
   (`on-the-record/hooks/fail-open-wrapper.sh`'s own stated design: "a
   wrapper that could change a verdict would be a worse defect than the
   one it records"). Resolution path: a follow-up silent-failure pass
   over the 9 resolve implementations' self-clone branch specifically, if
   the silent-absorb cost is judged to outweigh the fail-open benefit
   there.

skill-verdict: silent-failure-audit — applied: invoked; ran the audit
procedure (Skill tool, this turn) over the files this delivery touches
and their immediate neighbors (`self-update.sh`, `poll-rearm.sh`,
`pretooluse_dispatcher.py`, `spawn.py`'s `self_update_pull_cli()` /
`_pull_check_write()`) — classified `self_update_pull_cli()` as fully
Handled (every branch records to `.pull-check` and prints why; verified
by reading spawn.py:3352-3414 in this turn), and surfaced the
Silently-Absorbed self-clone `except Exception: pass` pattern above
(Open findings item 2) rather than silently leaving it uninspected.
other mounted skills: not triggered (work-in-english followed as ambient
style without a separate invocation; technical-feasibility-spike-report
and model-routing did not match this delivery's shape — no probing-state
spike negotiation and no multi-agent delegation decision was in play).

## Acceptance verification

- skew announces itself on stdout, matched install stays silent — checked: test/test_self_update_working_tree_untouched.py — result: pass: derived: `python3 -m pytest test/test_self_update_working_tree_untouched.py -q` this turn, all green, including the new stdout assertions for both the skewed and matched cases
- muster dropped from every resolve implementation, own-clone still wins priority — checked: test/test_engine_checkout_resolve_muster_retired.py — result: pass: derived: `python3 -m pytest test/test_engine_checkout_resolve_muster_retired.py -q` this turn, both new tests green
- zero-live-sessions self-update pull path — checked: test/test_self_update_pull_gate.py — result: pass: derived: `python3 -m pytest test/test_self_update_pull_gate.py -q` this turn, all green (pre-existing coverage, unmodified by this delivery)
- live-session refusal path, unmocked, against a real skewed clone — checked: this-session-transcript — result: pass: derived: `python3 spawn.py self-update -C <local bare-repo clone, behind by a handful of commits>` this turn printed "self-update 거부: 살아있는 세션이 있다고 판단함", naming this very session's own claim-only pid/workspace, and `HEAD` in that clone stayed unchanged afterward
- clean install with no existing clone self-clones current — checked: this-session-transcript — result: pass: derived: with `HOME` redirected to an empty scratch dir and no `TOKENMAXXXER_CHECKOUT`, `poll_rearm_resolve_checkout()` run this turn self-cloned into `~/.claude/tokenmaxxxer/on-the-record`, then `git rev-list --count HEAD..origin/main` there printed a zero count
- real ~/.claude/tokenmaxxxer/muster clone before/after disposition — checked: this-session-transcript — result: pass: derived: `git -C ~/.claude/tokenmaxxxer/muster rev-list --count HEAD..origin/main` before this turn's `mv` to `muster.retired-issue-2908` printed a count in the thousands; the identical command against the old path afterward printed `fatal: cannot change to '.../muster'`
- full pytest suite has no new failures vs origin/main — checked: pytest-full-suite-diff — result: pass: derived: `python3 -m pytest . -q` run twice this turn, with this delivery's changes `git stash`ed and unstashed — the FAILED test names in both runs' `short test summary info` blocks are identical
- no return of the retired role/roles axis in this delivery's own diff — checked: gates/retirement_count.py — result: pass: derived: `git diff --cached | grep -iE '^\+' | grep -iE '\brole'` this turn returned no matches against the staged diff

## Next steps

None — loop_state is terminal (`landed`). Both open findings above are
handed off as findings, not left as in-progress work on this record.
