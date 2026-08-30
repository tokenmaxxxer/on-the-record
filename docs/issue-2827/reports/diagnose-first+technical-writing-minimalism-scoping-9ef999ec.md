---
issue: 2827
role: diagnose-first+technical-writing-minimalism-scoping-9ef999ec
author: diagnose-first+technical-writing-minimalism-scoping-9ef999ec
skills: diagnose-first (skill-repository(c05de12)), technical-writing-minimalism-scoping (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
code_under_review: same-commit (docs/issue-2827/_assets/tokenmaxxxer-core-patch/*)
type: diagnostic
breaking: false
verdict: patch-prepared-887tok-cut-not-landable-from-this-repo
upstream:
  - path: docs/issue-2827/reports/diagnose-first-6c16a19d/item4-split-2026-08-30.md (PR #2851)
    sha: 98a0c80cc1bcd998cf45cbcadb39cca08216f542
  - path: docs/issue-2827/reports/adversarial-review-4f57bc82.md (PR #2856)
    sha: bc7b0f8bd2d8d6ceb32d8142bc26df085927a53e
---

# issue-2827 — diagnose-first+technical-writing-minimalism-scoping-9ef999ec record

## What was done

skill-verdict: diagnose-first — applied: invoked; used Stage 1
(instrument/baseline: re-derived items (a)/(b)/(d)'s byte composition
from this session's own live SessionStart hook output before proposing
any cut) and Stage 2's Amdahl check (sized each candidate's token share
before deciding whether it was worth a code change) to decide which of
the three newly-in-scope items actually had a lever, and which (item d)
did not once measured.
skill-verdict: technical-writing-minimalism-scoping — applied: invoked;
used rule 2 (move background the reader doesn't need out of the inline
path) to design the build-now variant of `session-protocol.md` — the
two-phase/Approve-mechanics block moves to a pointer sentence rather
than being deleted, since a build-now session that later hands off a
scope-exceeded remainder to a two-phase follow-up unit still needs to
know where to read it.
other mounted skills: not triggered (work-in-english governs this
record's own English-only prose per standing policy, not an
invoked-this-session skill in the sense the obligation above tracks).

This session picked up on-the-record#2827 after the user reopened it and
reframed ownership: tokenmaxxxer-core and warrant are **our** plugins (a
different repository, `tokenmaxxxer/tokenmaxxxer-core`, not a different
owner), so the diet's actionable share is 21.5% (9,645/44,860 —
canonical: on-the-record#2827's 2026-08-30 reopening comment's own
table, read via `gh issue view 2827 --repo tokenmaxxxer/on-the-record
--comments`), not the 8.06-9.99% PR #2851/#2856 measured under the old
(per-repository) ownership line. The reopening asked this round to
determine what can actually come out of the three newly-in-scope items —
core's SessionStart injection (2,701 tok), warrant's SessionStart
injection (257 tok), and the skill-backed slash-command listing
(2,208 tok) — under the same #2135 discipline: measure composition
before cutting, move normative content to on-demand rather than deleting
it, and never manufacture a bigger number by removing capability a
session actually uses.

Per this session's explicit instruction ("Do not re-measure what is
already measured. The numbers stand"), the four headline figures above
are taken as given. This session's own work was to open up their
*composition* — which of the bytes inside each one are load-bearing vs.
habitual, and whether either newly-scoped SessionStart hook can emit
less without losing anything a session actually reads.

**Central finding, discovered mid-session, that reshapes what "deliver"
means this round:** `tokenmaxxxer-core` is checked out at
`$CLAUDE_PLUGIN_ROOT_CORE/..` as a **separate git repository** —
canonical:
```
git -C /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core remote -v
```
result: `origin  https://github.com/tokenmaxxxer/tokenmaxxxer-core.git
(fetch)`. This session is spawned against on-the-record#2827 only — no
tokenmaxxxer-core issue, no branch, no PR target there. Contract v3's own
rules ("your issue is assigned in the spawning prompt — never pick or
file one"; "ALL of your output ... returns to the user as a PULL REQUEST"
against the assigned repo) scope this session's write authority to
on-the-record, branch
`issue-2827/diagnose-first+technical-writing-minimalism-scoping-9ef999ec`.
The ownership reframing (tokenmaxxxer-core is "ours") settles which
tokens count toward the 10% line; it does not grant this session commit
or push authority in a different GitHub repository it was never assigned
work in. So the code that actually cuts items (a) and (b) is **prepared
and measured, not landed**, in
`docs/issue-2827/_assets/tokenmaxxxer-core-patch/` (three files + a
README describing where each goes and the before/after it produces),
ready for a session spawned against a tokenmaxxxer-core issue to apply.
See "Next steps" for the recommended follow-up.

### Item (a) — core SessionStart hook injection (2,701 tok baseline)

canonical: `core/hooks/directive.sh` and `core/directive/session-
protocol.md` under `$CLAUDE_PLUGIN_ROOT_CORE/core/`, both read in full
this session. `directive.sh` prints a 9-line INVARIANTS block
(role-specific, ~700-900 B) then cats the ENTIRE `session-protocol.md`
verbatim, unconditionally, every session. derived: `wc -c
core/directive/session-protocol.md` -> `8729`.

Composition of `session-protocol.md`'s 8,729 B: roughly half of it
(the two-phase default description, the checkpoint-mode description, and
the full Approve-signal mechanics — two-account vs single-account
string-equality test, near-match reporting duty) describes a phase
boundary that **cannot fire** while `CORE_BUILD_NOW=1` — the environment
variable the spawner sets for every single-phase spawn, which is the
default since issue #2152 flipped it. canonical: `pipeline.py`, the
`single_phase` handling comment, read this session: "이슈 #2152 로
기본값 반전: 기본은 이제 참". That is load-bearing content for a
two-phase or checkpoint spawn and pure habit-carried-over for a
build-now spawn (this session's own mode).

Load-bearing regardless of phase mode (kept in the patch, verbatim):
issue/PR-only-output rule, layout/commit-trailer rule, headless/
single-shot delegation rule, board-is-merged rule, record required
fields, terminal `loop_state` per kind, operational-surface commit rule,
specs-regen rule, verify-at-landing rule.

Habitual for a build-now session (condensed to a one-line pointer in the
patch, not deleted): the two-phase default/checkpoint-mode narrative and
the full Approve-signal mechanics (contract v3 s19's phase-2-gating
detail) — none of it can execute while `CORE_BUILD_NOW=1` skips the
approval boundary entirely.

Measured effect (scratch reproduction under this session's own real env
— full command in
`docs/issue-2827/_assets/tokenmaxxxer-core-patch/README.md`, cross-
checked against this session's own live SessionStart hook output —
canonical: this session's own session log, `type=system,
subtype=hook_response` event `hook_id=7be3631f-...`, stdout length
10916 B):
```
before (unmodified, this session's live log):  10916 B = 2729.0 tok
after (build-now variant, scratch-patched):     8396 B = 2099.0 tok
delta:                                          2520 B =  630.0 tok
```
Saving applies only to `CORE_BUILD_NOW=1` spawns (the default per
#2152); a two-phase or checkpoint spawn's injection is byte-identical to
today, unchanged by this patch — verified: the patch's `else` branch is
untouched from the original file (`diff` of that branch against the
original `core/hooks/directive.sh` shows no change).

### Item (b) — warrant SessionStart hook injection (257 tok baseline)

canonical: `warrant/hooks/state.sh`, read in full this session. It is a
SessionStart hook (not the `warrant/hooks/directive.sh` UserPromptSubmit
hook — a second, differently-named file this session initially
mis-attributed the injection to before reading `warrant/hooks/
hooks.json`'s `SessionStart` array, which names `state.sh`; see "What did
not work"). It unconditionally scans the top-level `docs/proposals/`
directory and reports every `proposed`/`approved`/`withdrawn`/`rejected`/
malformed unit it finds there, regardless of which issue the spawned
session is working on.

This is stale for virtually every current spawn: on-the-record#2572
retired every spawn form except `--skills ... --issue <n>`. canonical:
`spawn.py`'s own usage banner, read this session: "이슈 #2572: 유일한
스폰 형태는 --skills 다". That is the role protocol's per-issue
layout — every session's own proposals go to
`docs/issue-<n>/proposals/`, never the top-level directory. derived:
```
find docs -maxdepth 2 -type d -name proposals | wc -l
```
result: `351` — 351 per-issue `docs/issue-<n>/proposals/` directories
already exist in this repo, vs. exactly one top-level `docs/proposals/`
containing the 5 stale entries this session's own SessionStart hook
printed (`shared-core-and-consent`, `closes-trailer-preflight-hardening`,
two `issue-659` proposals, `issue-666`) — none of which reference
issue-2827 or are actionable from an issue-2827-scoped session's write
authority (docs/issue-<n>/** only, per the layout rule). `state.sh`
never scans any `docs/issue-<n>/proposals/` directory at all — a genuine
blind spot alongside the noise, not just excess verbosity.

The patch: when the session is issue/role-scoped (`CLAUDE_SKILL` set and
current branch resolves to exactly `issue-<n>/<CLAUDE_SKILL>` — the same
detection warrant-protocol's own hunt-record routing already documents),
scan `docs/issue-<n>/proposals/` instead of the top-level directory; a
non-issue-scoped session's behavior is unchanged.

Measured effect, this session's real repo/branch — derived: `ls
docs/issue-2827/` -> `reports` only, no `proposals` subdirectory this
issue has created:
```
before (unmodified, this session's live log): 1026 B = 257.0 tok
after (patched):                                 0 B =   0.0 tok
```
canonical: this session's own session log, `type=system,
subtype=hook_response` event `hook_id=91afe276-...`, stdout `"warrant:
open work units in this repository — ..."`, length 1026 B, matching the
`before` figure exactly.

Verified the patch does not silently drop real signal when an issue DOES
have its own open unit — derived: ran the patched script's
report-building logic against `docs/issue-1000/proposals/
implementation.md` (a real `status: proposed` file already in this
repo, confirmed via `grep -m1 "^status:"
docs/issue-1000/proposals/implementation.md` -> `status: proposed`) with
`WARRANT_BRANCH=issue-1000/implementation`:
```
warrant: open work units in this repository —
  AWAITING APPROVAL: docs/issue-1000/proposals/implementation.md — do not start this work until the user approves it. — deferred (auto, stale since 2026-08-12T06:30:27Z)
```
— correctly surfaced. Branch-to-directory resolution also verified in
isolation against 5 cases (matching issue-scoped branch, `main`, no
`CLAUDE_SKILL`, and two non-matching branches) — all 5 resolve to the
expected directory. Full commands in
`docs/issue-2827/_assets/tokenmaxxxer-core-patch/README.md`.

### Item (d) — skill-backed slash-command listing (2,208 tok baseline): no lever found

The reopening comment frames this item as "OUR skills' slash-command
registrations" and asks whether every skill needs mounting in every
spawned session. derived: this session's own equivalent listing —
the literal "The following skills are available for use with the Skill
tool" reminder this session saw at turn 1, copied verbatim to a scratch
file, `wc -c /tmp/skills_reminder_2827_round2.txt` -> `8597` (8,597 B =
2,149.2 tok — close to but not identical to the reopening's 2,208, since
this session mounts 2 task skills vs. the prior round's 1) — splits into
four distinct sources, not one:

```
header (structural sentence):                      65 B =  16.2 tok
core-family plugin skills (terse:terse,
  freelunch:freelunch-code-fanout/-site-fanout):   319 B =  79.8 tok
task skills (diagnose-first,
  technical-writing-minimalism-scoping,
  work-in-english — this session's --skills set):2554 B = 638.5 tok
harness-default skills (dataviz, update-config,
  keybindings-help, code-review, simplify,
  fewer-permission-prompts, loop, schedule,
  claude-api, run, init, security-review):       5659 B =1414.8 tok
```
derived: line-by-line classification of the same scratch file by known
skill-name prefix, summed per group.

Checked whether the 12 harness-default entries come from any
tokenmaxxxer-controlled mount:
- Not from the 5 core-family plugins — derived: `find core terse
  freelunch scout warrant -iname SKILL.md` (from `tokenmaxxxer-core`'s
  root) returns nothing; only `terse` and `freelunch` register skills at
  all (3 total, all in the "core-family" group above).
- Not from `skill-registry` — derived: `find
  /home/jwjung/skill-registry/skills -maxdepth 1 -type d` lists 273
  directories, none of the 12 names among them, and only the 3
  `--skills`-requested entries from there are actually mounted —
  canonical: this session's own env, `printenv | grep MUSTER_SKILLS` ->
  `MUSTER_SKILLS=diagnose-first,technical-writing-minimalism-scoping,
  work-in-english`.
- Not from on-the-record's own plugin — derived: `find on-the-record
  -iname SKILL.md` -> empty — matching PR #2851's own finding that
  on-the-record ships zero skills.
- Not from the operator's user-level marketplace settings — canonical:
  `pipeline.py`, `spawn_cmd()`, read this session, comment citing issue
  #2135: "a spawned session inheriting the operator's USER-scope
  settings mounts the operator's entire personal skill registry ... none
  of it addressed to the session" — `spawn_cmd()` already passes
  `--setting-sources project,local` unconditionally, already fixed
  before this issue existed.

No SKILL.md for any of the 12 names exists anywhere this session's
`--plugin-dir` mounts reach. They are Claude Code's own built-in default
skill set, present in the harness regardless of plugin configuration —
the same ownership bucket as items (c)/(e)/(f), not a tokenmaxxxer
registration at all. **This refutes the reopening's working hypothesis
that a session mounts "forty other skills" it doesn't need**: the
tokenmaxxxer-controlled portion of this listing (core-family + task
skills, ~718 tok in this session) is already exactly and only what
`--skills` requested, plus the 3 small mechanism skills the freelunch/
terse directives reference. There is no unmounting lever here — cutting
the 12 harness-default entries would require a change to the Claude Code
CLI itself, outside any tokenmaxxxer repository. No patch is proposed for
item (d).

## Why

The reopening's own instruction set the discipline: "measure the
composition of each before cutting, and do not remove normative content
to hit a number" (per #2135, restated this round), and "must not:
unregister a skill or command that sessions actually use." Both items
(a) and (b) turned out to have real, measured non-load-bearing bytes —
(a) because `CORE_BUILD_NOW=1`'s existence makes half of the full
two-phase protocol text provably unreachable this session, and (b)
because `state.sh` reports on a directory (`docs/proposals/`) that no
current `--skills`-spawned session's own proposal activity ever uses
(351 issue-scoped directories exist vs. 1 top-level one, per the count
above) — so cutting each is subtraction of dead weight, not manufacturing
a number. Item (d) turned out to have no lever once measured: most of
its bytes are outside any tokenmaxxxer-owned mount point, and the part
that IS tokenmaxxxer-owned was already exactly as narrow as `--skills`
made it.

The repo-boundary finding governs delivery shape: contract v3's
issue-assignment and PR-target rules are unconditional regardless of who
"owns" a token — this session builds and measures against
tokenmaxxxer-core's checkout because that's readable, but does not
commit there because that's a different repository this session has no
issue or branch in.

## Upstream basis

- canonical: `docs/issue-2827/reports/diagnose-first-6c16a19d/item4-
  split-2026-08-30.md` (PR #2851, read via `git show
  98a0c80cc1bcd998cf45cbcadb39cca08216f542:docs/issue-2827/reports/
  diagnose-first-6c16a19d/item4-split-2026-08-30.md`) — established the
  four headline figures this round works from without re-measuring: core
  SessionStart 2,701 tok, warrant SessionStart 257 tok, skill-backed
  listing 2,208 tok, items 1-3 total 4,479-4,480 tok.
- canonical: `docs/issue-2827/reports/adversarial-review-4f57bc82.md`
  (PR #2856) — independently reproduced the same split; nothing in this
  round contradicts its arithmetic, only its ownership-line framing.
- canonical: on-the-record#2827's 2026-08-30 reopening comment
  (JiwonJung94), read via `gh issue view 2827 --repo tokenmaxxxer/on-
  the-record --comments` — the corrected ownership table (21.5%) and
  this round's scope (items a/b/d).
- canonical: `core/hooks/directive.sh`, `core/directive/session-
  protocol.md`, `warrant/hooks/state.sh`, `warrant/hooks/hooks.json`
  (all in `tokenmaxxxer/tokenmaxxxer-core`, read in full this session) —
  the actual hooks this round's patch touches.

## Standing invariants (all four, command + output)

1. No return of the retired role axis in any reshaped form:
acceptance: `grep -rn "role_axis\|retired.role\|role-axis" --include="*.py" .`
— result: 7 hits, all historical comments/doc references
(`directive_assembly.py`, `spawn.py`, `pipeline.py`, `roster.py`, two
test docstrings) naming `docs/decisions/2026-08-25-retire-role-axis-
staging.md` — no reintroduced code, matching PR #2851's own check.

2. No new bug, failing-test set vs `origin/main` as SETS OF NAMES:
acceptance: `git diff origin/main --stat` — result: empty (no output) —
this session's on-the-record tree is byte-identical to `origin/main` for
every tracked path; the only local additions are this record and the new
`_assets/tokenmaxxxer-core-patch/` directory, neither tracked before this
commit. So the failing set below IS `origin/main`'s failing set on this
sandbox, by construction, not a separate comparison:
acceptance: `python3 -m pytest -m "not slow" -q` — result: `16 failed,
593 passed, 3 xfailed` — all 16 failures are network/`origin`-remote-
dependent (fetch/gh calls unavailable in this sandbox), none touching
core/warrant hook logic or this session's `_assets/` addition (full
failing-test-name set captured at `/tmp/failing_2827r2.txt` this
session).

3. No overhead increase: canonical: `git diff origin/main --stat`
(cited above, empty) — this session adds zero code to on-the-record
itself; the prepared tokenmaxxxer-core patch is a net *decrease*
(887 tok/spawn for the common case, item a/b sections above) and touches
no on-the-record file.

4. Monitor/watch machinery unbroken and not quieter:
acceptance: `python3 -m pytest -m "not slow" -q -k "watchdog or
heartbeat or monitor or watch"` — result: `45 passed` — identical count
to PR #2851/#2856's own check (also 45 passed, 0 failed, canonical:
`docs/issue-2827/reports/diagnose-first-6c16a19d/item4-split-2026-08-30.md`,
cited in Upstream basis).

## Standing context, re-measured on this session's own real spawn

acceptance: `python3 -c "import json; ..."` reading this session's own
live session log for the first assistant-turn `usage` field (full
one-liner in `docs/issue-2827/_assets/tokenmaxxxer-core-patch/
README.md`) — result: `9902 35043` -> 9902+35043 = **44,945 tokens**,
under `$MUSTER_WORKSPACE_ROOT` — within 85 tok of the established 44,860
baseline (the difference is this session's 2 task skills vs. the prior
round's 1, plus a longer role-name string; both accounted for above),
confirming no drift.

derived: arithmetic — projected total if the prepared tokenmaxxxer-core
patch lands and this session were re-spawned unchanged (build-now, no
own open proposal): 44945 − 2520/4 − 1026/4 = 44945 − 630 − 257 =
**44,058 tok**, a 887-tok / 1.98%-of-baseline cut. This is a projection
from the measured static-heredoc byte deltas above (items a/b, this same
record), not a second live `claude -p` spawn — see "Rationale for
deviations" for why a nested spawn was not run.

## Open findings

- The patch in `docs/issue-2827/_assets/tokenmaxxxer-core-patch/` is
  measured and unit-verified against this repo's own real proposal
  directories (see item (b) above) but has not run tokenmaxxxer-core's
  own hook test suite (`core/hooks/tests/run-directive-shape-tests.sh`,
  `warrant/hooks/tests/run-directive-hunt-path-tests.sh`) — this session
  has no CI/write access to that repository to run them meaningfully
  against a landed change. Resolution path: run those suites in the
  tokenmaxxxer-core-scoped session that applies this patch, before
  merging.
- Item (d)'s harness-default skill listing (~1,415 tok, 66% of that
  item's total) has no owner this repository or tokenmaxxxer-core can
  act on. Resolution path: none identified; not actionable from either
  repository.

## Next steps

For the diet itself to actually land: open a companion issue in
`tokenmaxxxer/tokenmaxxxer-core` (the user's own act, per contract v3 —
this session does not file issues) referencing this record and the
prepared patch, so a session with real write/PR authority in that
repository can apply
`docs/issue-2827/_assets/tokenmaxxxer-core-patch/{core-hooks-directive.sh,
core-directive-session-protocol-build-now.md, warrant-hooks-state.sh}`,
run that repository's own hook test suites (named in "Open findings"),
and land the 887-tok/spawn cut there.

## What did not work

- Initially attributed item (b)'s SessionStart injection to
  `warrant/hooks/directive.sh` (a real file, but a `UserPromptSubmit`
  hook that prints a *different* string, "[warrant-directive] file-
  touching work starts with a proposal...") before reading
  `warrant/hooks/hooks.json`'s `SessionStart` array, which names
  `state.sh`. derived: `warrant/hooks/hooks.json`, read this session —
  corrected before any measurement was taken from the wrong file, no
  downstream figure was affected.
- An early three-line extraction of `state.sh`'s embedded Python body
  (`sed | tail -n +2 | head -n -2`) silently dropped the script's own
  final `print(...)` line along with the intended `PY` heredoc
  delimiter, because a line count assumption from before an edit was
  reused after the edit shifted every subsequent line number by one —
  the extracted script ran with exit 0 and produced no output, which
  looked like "no open units matched" rather than "the print statement
  is missing." derived: caught by re-deriving the heredoc's actual line
  range with `grep -n "^PY$"` instead of the stale offset, then
  confirmed by re-running the corrected extraction against
  `docs/issue-1000/proposals/implementation.md` (a real open unit,
  cited in item (b) above), which produced the expected report line only
  after the fix.

## Rationale for deviations

derived: item (a)/(b) measurement sections above (this same record) —
the two deviations below both trace to the central finding in "What was
done".

- Expected outcome per the spawning prompt's framing: land the (a)/(b)
  hook edits in this session's own delivery. Actual: discovered mid-
  session that `tokenmaxxxer-core` is a separate GitHub repository this
  session has no issue or branch in (canonical: `git -C
  .../tokenmaxxxer-core remote -v`, cited in "What was done") — landing
  there from an on-the-record#2827-scoped session would be picking up
  unassigned work in a different repository, which contract v3 forbids
  regardless of the ownership reframing this issue itself established.
  Deviated to: measure, patch, and unit-verify the change against a
  `/tmp` scratch copy (never against the live, hook-executing
  tokenmaxxxer-core checkout this session's own gates run from), commit
  the finished patch as a reviewable asset under `docs/issue-2827/
  _assets/`, and recommend the companion-issue path in "Next steps"
  instead of merging it directly.
- Did not run a second, nested `claude -p` spawn to re-measure standing
  context after the patch (the round's instruction: "Re-measure standing
  context on a real spawn after the change"). Both hooks this round
  edits are static heredocs keyed only on env vars and repo state (their
  own code comments assert byte-identical output regardless of role), so
  the scratch-copy reproduction under this session's exact real env
  (items a/b above) is deterministic and byte-exact for what a real
  spawn would inject — a second nested spawn would reproduce the same
  numbers while also creating a new branch/session/possible PR in a live
  repository purely to confirm arithmetic already exact. Used the
  cheaper, side-effect-free reproduction instead and labeled the combined
  44,058-tok figure (Standing context section above) as a derived
  projection, not a second live-spawn measurement.
