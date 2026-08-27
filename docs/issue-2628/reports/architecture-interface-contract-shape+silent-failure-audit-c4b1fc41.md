---
issue: 2628
role: architecture-interface-contract-shape+silent-failure-audit-c4b1fc41
author: architecture-interface-contract-shape+silent-failure-audit-c4b1fc41
skills: architecture-interface-contract-shape (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
code_under_review:
  - gates/spawn_on_pr.py
  - gates/test_spawn_on_pr.py
  - test/test_verifies_subject_scaffold.py
type: fix
breaking: true
verdict: pass
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: gates/merge_gate.py (verifying_record_count()/REQUIRED_INDEPENDENT_VERIFICATIONS, issue #2609)
    sha: 7c3c68f7fbdf9a80e6cae0d15deee23b3a9b8073
  - path: docs/issue-2626/ (removal audit that found this survivor)
    sha: 4d72e9a68f5cedaa13ef0bdceea4f34d12538ffa
  - path: docs/issue-2610/ (retired the 44-entry role catalog)
    sha: 49c4854b8d699130fe88e6f6db6e4287feb313c0
  - path: docs/issue-2628/reports/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41/2026-08-27-hunt-auto-spawn-roles-removal.md
    sha: same-commit
---

# issue-2628 — architecture-interface-contract-shape+silent-failure-audit-c4b1fc41 record

## What was done

Deleted `AUTO_SPAWN_ROLES = ("execution-observation", "conformance-review")`
from `gates/spawn_on_pr.py` — the byte-identical survivor of the tuple
issue #2615 claimed removed, found live at `gates/spawn_on_pr.py:50` by the
removal audit (#2626/#2627). Deleted `applicable_record_kinds()`, the
function that matched it. Nothing renamed, relocated, or re-shaped the same
closed set under another name — the auto-spawn tick's "does this subject
still need verification" signal is now `verification_deficit()`, a pure
count (`REQUIRED_INDEPENDENT_VERIFICATIONS - verifying_record_count(...)`)
that mirrors `gates/merge_gate.py::required_verification_missing()`'s
count-only branch exactly (issue #2609) — no `kind:` value, filename, or
role/skill name participates.

canonical: `git show HEAD --stat` — this session's single landing
commit; the non-doc code diff is confined to `gates/spawn_on_pr.py`,
`gates/test_spawn_on_pr.py`, `test/test_verifies_subject_scaffold.py`
(the other two changed paths are this record and the hunt record below).

`spawn_missing_for_pr()`/`backfill_closed()` now invite `deficit`-many
*generic* verification sessions (branch/roster identity
`independent-verification-<n>`, matched by `_VERIFICATION_SLOT_RE =
re.compile(r"^independent-verification-\d+$")`) instead of iterating two
fixed role names. That same regex replaces the old `not in AUTO_SPAWN_ROLES`
exclusion in `subject_deliverable_branch()`; the equivalent exclusion in
`_implementation_session_active()` was dropped outright rather than
replaced (that function no longer has anything to exclude by name — see
its docstring).

canonical: `grep -rn 'AUTO_SPAWN_ROLES' --include=*.py .` — result:
```
(no output, exit 1)
```

A same-session before-landing warrant hunt (stance 0: "assume the
gate/mechanism just touched is bypassable") reproduced a real defect in
the first version of this change: slot numbers computed positionally from
the *current* deficit (`range(1, deficit + 1)`, recomputed fresh every
tick) let a genuinely-stuck verification slot's `park_state`/
`MAX_RESPAWN_ATTEMPTS` history be silently discarded whenever a
lower-numbered sibling slot resolved first, defeating the respawn ceiling
backstop issue #2238 built specifically to catch "a guard that can fail
without saying so." Fixed within this same session, before landing, in
this session's landing commit by moving park/ceiling/re-arm tracking from
`(subject, role)` pair granularity to `subject` granularity: `park_state`
keys are now `subject`
alone, `attempts` is the subject's cumulative count of verification
sessions ever auto-spawned (never reset by how individual slots resolve),
and a new slot's number is drawn from `attempts + 1, attempts + 2, ...`
(strictly increasing, never reused) rather than from the live deficit
count. `is_approval_blocked()`'s re-arm check now targets one fixed
generic string per subject (`VERIFICATION_APPROVAL_TARGET =
"independent-verification"`, not a role name) since park state is no
longer per-role. `unpark()`/`clear_ceiling()`/`parked_report()` and the
`unpark`/`clear-ceiling` CLI subcommands dropped their `--role` argument
to match (CLI-breaking for any caller passing `--role`; no such caller
found in this repo's own consumers — see acceptance below — hence
`frontmatter: breaking: true` stated honestly rather than omitted because
no live caller happened to be found).

canonical: this session's own before-landing warrant-hunter dispatch
(agent a1743abd90159eec1), transcript landed in this session's single commit as
`docs/issue-2628/reports/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41/2026-08-27-hunt-auto-spawn-roles-removal.md`
— "Verdict: FINDING", full ad hoc reproduction script and observed
output.

A new regression test,
`test_sibling_slot_resolving_does_not_reset_ceiling_progress`
(`gates/test_spawn_on_pr.py`), encodes the hunt's exact scenario (deficit
2 → one slot resolves → deficit 1 → subject still hits the ceiling at the
correct cumulative attempt count).

derived: `python3 -m pytest gates/test_spawn_on_pr.py test/test_verifies_subject_scaffold.py test/test_watchdog_heartbeat_noise.py test/test_merge_gate_record_kind.py -q` — result:
```
43 passed
```

## Why

canonical: `gh issue view 2628` — operator ruling (2026-08-27, quoted in
the spawn task): "if the capability cannot be provided without
enumerating identities, remove the capability and state plainly what
stops working. Renaming, relocating to another module, sharding into
per-entry files, or reading the same names from config/env/JSON all count
as failure."

Applying that test to `AUTO_SPAWN_ROLES`: the capability it served —
*deciding which named expertise to auto-invite* — cannot be provided
without enumerating identities (that is what a name is). So that half is
dropped outright, per the ruling, rather than re-expressed. What
*survives* is the half issue #2609 already proved is expressible as a
property of the subject: *how many* independent verifications are still
needed. `spawn_on_pr.py`'s auto-spawn tick and `merge_gate.py`'s merge
gate now compute that same count the same way — before this issue they
used two different definitions of "verified" (kind-matching here,
`verifying_record_count()` there), which was itself a latent
inconsistency this change also removes.

What stops working, stated plainly (the ruling's own requirement): the
auto-spawn tick can no longer target a specific kind of expertise by
name. A subject that specifically needs, say, a conformance-style review
versus an execution-observation-style read is no longer distinguished by
this automation — it invites `N` generic "read the PR and verify
independently" sessions and relies on the spawned session's own
task-text-driven skill matching (the same free-form mechanism issue
#2610 already made the only mechanism in this repo) to decide how to
verify.

canonical: `on-the-record/directive/spawn-and-board.md` (read live, this
session) — its own text: "There is no auto-routing table — who runs next
is your judgment call" (the human-driven `spawn.py --skills
conformance-review-verdict-assignment ...` manual workflow, untouched by
this issue) and, on `execution-observation` specifically: "has no
corresponding skill yet ... this is a skill-repository gap" — meaning at
least half of the removed tuple's "invitation" was already degraded to a
bare literal string with no matching skill behind it, even before this
change.

Why `verification_deficit()` mirrors `merge_gate.required_verification_
missing()` instead of importing it directly: `merge_gate.py` imports
`spawn_on_pr` (`gates/merge_gate.py:19: import spawn_on_pr`), so the
reverse import would be circular. `merge_gate.required_verification_
missing()` also carries a `repo`/`pr` exemption path
(`_own_pr_supplies_verification()`, issue #2233/#2380 cycle-break)
specific to evaluating a PR under review; the auto-spawn tick evaluates
*other* subjects' boards, not the PR under review, so that exemption does
not apply here — `verification_deficit()` is the smaller, count-only
subset both callers actually share.

Why subject-level park/ceiling tracking (not a stable-but-sparse
per-slot scheme, e.g. persisting slot identity forever once minted): a
monotonically-increasing subject-level counter is the smallest change
that closes the hunt's reproduced gap. An alternative considered
mid-session — keep per-slot keys but never renumber a slot once it is
first minted (grow the tracked set, never shrink it) — was rejected
after tracing it through: since landed verifications are anonymous (no
record declares which slot it satisfies, by design — that is the whole
point of the count-based model), there is no way to know which specific
already-tracked slot a resolved deficit corresponds to, so "keep slot
identity stable" degrades to guessing. Subject-level tracking sidesteps
the guess entirely: it never needs to know *which* slot resolved, only
that *a* verification session was spawned and how many times, which is
exactly the information the ceiling actually needs to protect.

## What did not work

- First implementation pass used `range(1, deficit + 1)` for slot
  numbers, recomputed fresh every tick, with `park_state` still keyed
  `f"{subject}/{role}"` (a direct, minimal-diff port of the old
  `(subject, role)` shape onto the new generic slot names). The
  before-landing warrant hunt reproduced a silent respawn-ceiling defeat
  in this version.
  canonical: this session's own before-landing warrant-hunter dispatch
  (agent a1743abd90159eec1), transcript landed in this session's single commit as
  `docs/issue-2628/reports/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41/2026-08-27-hunt-auto-spawn-roles-removal.md`.
  Replaced with subject-level `park_state` keys and a
  monotonically-increasing attempts-derived slot counter, landed in
  this same commit.
  derived: `python3 -m pytest gates/test_spawn_on_pr.py::test_sibling_slot_resolving_does_not_reset_ceiling_progress -q` — result:
  ```
  1 passed
  ```
- Considered keeping per-slot park-state keys stable by only ever
  *growing* the tracked set (never renumbering downward). Rejected once
  traced through: it requires knowing which already-tracked slot a
  resolved verification corresponds to, and the count-based model
  deliberately makes verifications anonymous — there is no such mapping
  to read. See "Why" above.

## Upstream basis

canonical: `gh issue view 2628` — cites `docs/issue-2626/` (removal audit
that classified the original issue #2615 claim FAIL and found this
survivor) and `docs/issue-2610/` (retired the 44-entry role catalog,
establishing that role/slug identity is free-form and task-derived
everywhere else in this repo).

- `gates/merge_gate.py`'s `verifying_record_count()`/
  `REQUIRED_INDEPENDENT_VERIFICATIONS` re-export and
  `required_verification_missing()`'s count-only branch (issue #2609) —
  `verification_deficit()` in this change mirrors that branch's formula
  exactly. sha: 7c3c68f7fbdf9a80e6cae0d15deee23b3a9b8073.
- `docs/issue-2626/` — sha: 4d72e9a68f5cedaa13ef0bdceea4f34d12538ffa.
- `docs/issue-2610/` — sha: 49c4854b8d699130fe88e6f6db6e4287feb313c0.
- This session's own before-landing warrant hunt — see frontmatter
  `upstream:` for the full path and sha (same as cited above in "What
  was done"/"What did not work").

## Open findings

None open. The one finding raised this session (positional slot-number
reuse defeating the respawn ceiling) was fixed and regression-tested in
this session's landing commit — see "What did not work" and "What was done" above.

## Next steps

None for this issue. `loop_state: landed`.

## Acceptance verification

- check: `grep -rn 'AUTO_SPAWN_ROLES' --include=*.py .`
  acceptance: `grep -rn 'AUTO_SPAWN_ROLES' --include=*.py .` — result:
  ```
  (no output, exit 1)
  ```

- check: a subject with a returned deliverable PR, showing what gets
  invited and by what rule.
  acceptance: end-to-end demonstration, run this session against the
  real `verification_deficit()`/`spawn_missing_for_pr()` code (only the
  `gh`/`git` boundary functions monkeypatched — the decision functions
  are the real, unmodified production code):
  ```
  deficit with 0 verifying records: 2
  deficit with 1 verifying record: 1
  deficit with 1 SELF-authored verifying record (must not count): 2
  spawn_missing_for_pr() dry-run pairs for a subject needing 2 verifications: [('issue-2628', 'independent-verification-1'), ('issue-2628', 'independent-verification-2')]
  ```
  The rule, stated plainly: a subject with a returned deliverable PR gets
  `REQUIRED_INDEPENDENT_VERIFICATIONS (2) - verifying_record_count(subject_board, subject_author)` generic invitations, never a
  named role — a property of the subject's own board state, not a
  roster lookup.

- check: the tool's output on this claim (`scripts/audit_removal_claim.py`).
  acceptance: `python3 -c "import json; json.dump({'name': 'AUTO_SPAWN_ROLES tuple removed from gates/spawn_on_pr.py, no closed set of names replaces it (issue #2628)', 'removed_names': ['AUTO_SPAWN_ROLES', 'applicable_record_kinds'], 'member_samples': ['execution-observation', 'conformance-review'], 'min_coloc': 2}, open('/tmp/audit_claim_2628_repro.json','w'))" && python3 scripts/audit_removal_claim.py /tmp/audit_claim_2628_repro.json --root .` — result:
  ```
  verdict: RESHAPE_DETECTED
  q1 (name gone): AUTO_SPAWN_ROLES / applicable_record_kinds — 0 live hits
    outside .git internals (classified below).
  q2 (reshaped, member_samples co-located >= 2 in one file):
    ./.claude-plugin/marketplace.json, ./.git/*, ./directive_assembly.py,
    ./gates/merge_gate.py, ./gates/spawn_on_approve.py,
    ./on-the-record/commands/run.md,
    ./on-the-record/directive/spawn-and-board.md,
    ./on-the-record/hooks/pr-base-guard.sh, ./spawn.py,
    ./runs/rulebooks/tokenmaxxxer-core/* (nested, different repo checkout)
  q3 (still branches on membership): none found (branch_hits: [])
  ```
  Tool verdict is RESHAPE_DETECTED; hand classification of every hit
  follows — the tool's own doc states "a rename passes [Q1] trivially",
  and by construction it does not itself distinguish narrative/unrelated
  co-location from a live reconstructed closed set, hence this manual
  pass, as this task instructed.

  **Q1 hits (3, all after this session's own checkpoint commit
  this session's landing commit):** `./.git/logs/HEAD`, `./.git/logs/refs/heads/issue-2628/...`,
  `./.git/COMMIT_EDITMSG` — **false positive**. These are the reflog/
  commit-message artifacts of *this session's own commit*, which
  necessarily narrates the name it removed ("issue-2628: drop
  AUTO_SPAWN_ROLES, replace with..."). Not source, and not `docs/`/
  `test/` either (the tool's own exclude regex only covers those two
  directory names), so the tool's Q1 exclude doesn't catch it — a gap in
  the tool's path filter, not a reconstruction.

  **Q2 hits, classified individually:**
  - git internals (`./.git/FETCH_HEAD`, `./.git/index`,
    `./.git/objects/pack/*.pack`,
    `./runs/rulebooks/tokenmaxxxer-core/.git/*`) — **false positive**:
    not source; the `runs/` path is a *different*, nested repository
    checkout entirely (the core rulebook plugin mount).
  - `./directive_assembly.py` — **false positive**.
    derived: `grep -n "execution-observation\|conformance-review" directive_assembly.py` — result:
    ```
    273:# observed live (issue-2379 conformance-review session): a PR was already
    582:    "execution-observation"/"conformance-review") would reintroduce
    692:# conformance-review-severity-classification 이 16/16 -> 7/16 로, model-routing
    ```
    Line 582 is the *anti-pattern warning itself* ("keying this stamp
    off `role` ... would reintroduce exactly the closed set #2609
    deleted, one layer up"); lines 273/692 are unrelated historical
    comments (a PR-conflict observation, a model-routing metric). No
    dict/tuple/dispatch structure present.
  - `./gates/merge_gate.py` — **false positive**.
    derived: `grep -n "execution-observation\|conformance-review" gates/merge_gate.py` — result:
    ```
    123:    `issue-2204/execution-observation`) must not be blocked from merging by
    327:    # issue #2381 R1 (conformance-review CHANGES round): 아래 `stale_revert_reasons()`
    ```
    Two unrelated docstring/comment examples (an illustrative branch
    name, an unrelated issue-#2381 CHANGES-round note). No structure.
  - `./gates/spawn_on_approve.py` — **false positive**.
    derived: `grep -n "execution-observation\|conformance-review" gates/spawn_on_approve.py` — result:
    ```
    8:(execution-observation/conformance-review)만 스폰하고, 승인 여부는 그
    ```
    A background-context comment describing what `spawn_on_pr.py` *used
    to do*, in a module whose own actual mechanism
    (`ready_for_phase2()`/`_role_session_active()`) is already fully
    role-name-agnostic (read live this session).
  - `./on-the-record/commands/run.md`,
    `./on-the-record/directive/spawn-and-board.md` — **false positive
    for this claim, real staleness noted for a future issue**: these
    document the *separate*, human-driven `spawn.py --skills ...`
    workflow (spawn-and-board.md's own text, quoted in "Why" above: "no
    auto-routing table"), not `gates/spawn_on_pr.py`'s automatic tick.
    Not touched here (out of this issue's write scope, and out of the
    frozen files listed in this record's `code_under_review:`
    frontmatter); flagged as doc-currency drift worth a future pass now
    that the automatic half no longer uses these names at all.
  - `./on-the-record/hooks/pr-base-guard.sh` — **false positive**.
    derived: `grep -n "execution-observation\|conformance-review" on-the-record/hooks/pr-base-guard.sh` — result:
    ```
    12:# observation.watcher.log, ~14:2x KST) shows issue-1202/execution-observation
    13:# issuing `gh pr create --base issue-247/conformance-review --head
    14:# issue-1202/execution-observation` — a different issue's role branch,
    16:# bleed: the session's own conversation had issue-247/conformance-review's
    ```
    Prose narrating a specific 2026-08-14 incident by the exact branch
    names involved, not live bash/python logic — the guard's actual code
    (read live this session) never references either string.
  - `./spawn.py` — **false positive**.
    derived: `grep -n "execution-observation\|conformance-review" spawn.py` — result:
    ```
    9:  python3 spawn.py --skills conformance-review-verdict-assignment "PR 12 를 리뷰해라" --issue 12
    740:LEGACY = {"conformance-review": "review-record.md",
    1548:            # CHANGES 라운드(execution-observation, PR #2438 merged로 지적):
    3673:            # (docs/issue-1960/reports/execution-observation/baseline-measurement.md)
    ```
    Line 9 is a `--skills` CLI help-text example; lines 1548/3673 (both
    above, in the same `derived:` grep result) are unrelated historical
    comments. Line 740's `LEGACY` dict
    (`{"conformance-review": "review-record.md", ...}`) is an unrelated,
    pre-existing "contract v1 stragglers" warning-only lookup (its own
    comment: "말해주기 위해서만 본다") that this issue's own Non-goals
    section excludes ("write_scope data survival — filed separately")
    and contains only 1 of the 2 member_samples anyway.
  - `./.claude-plugin/marketplace.json` — **false positive**: lists
    unrelated marketplace plugin packages literally named
    `execution-observation-rulebook`/`conformance-review-rulebook` — a
    different subsystem (the plugin marketplace) with a coincidental
    naming overlap, not this repo's auto-spawn mechanism.

  **Q3:** 0 branch_hits (per the tool's own JSON output above) —
  confirms no live comparison/dispatch keyed on either member sample
  outside docs/tests.

  Net: every live-code hit traced to either narrative/historical prose,
  an unrelated pre-existing lookup out of this issue's scope, or a
  different subsystem/repository — none reconstructs a closed set that
  gates *this automation's* auto-spawn decision. The tool's raw verdict
  (RESHAPE_DETECTED) is reported here in full rather than suppressed,
  per this task's own instruction not to let a claim be accepted on an
  unclassified tool run.

### Skill verdicts

skill-verdict: architecture-interface-contract-shape — applied: invoked;
rule 11b ("A public module interface carries methods with zero live
callers after a feature removal or refactor → REMOVAL — delete the
unused method(s)") directly motivated deleting `applicable_record_kinds()`
outright rather than keeping it as a dead alternate path once
`verification_deficit()` took over every caller. Rule 8 ("expose an Open
Host Service with a Published Language... instead of bespoke per-consumer
contracts") shaped the replacement invitation contract: a spawned
verification session receives one generic, published task description
("independent verification of subject's deliverable") rather than a
bespoke contract keyed to a specific named consumer role. Rule 12 ("expose
only the minimal contract needed") shaped `verification_deficit()`'s
signature — an `int`, not a role-name list, is the minimal surface the
callers actually need.

skill-verdict: silent-failure-audit — applied: invoked; the audit's own
trace-forward method (follow a guard from its catch/check site to its
downstream consequence) is exactly what this session's before-landing
warrant hunt did to `spawn_missing_for_pr()`'s respawn-ceiling guard.
canonical: this session's own before-landing warrant-hunter dispatch
(agent a1743abd90159eec1), transcript landed in this session's single commit as
`docs/issue-2628/reports/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41/2026-08-27-hunt-auto-spawn-roles-removal.md`
— its "Observed"/"Root cause" sections trace the guard site (`if attempts
>= max_respawn_attempts`) through the `park_state` write and show the
ceiling check read the wrong `attempts` value (silently reassigned to a
different logical requirement) and never fired for the genuinely-stuck
case — the same shape as a Silently Absorbed classification in this
skill's taxonomy (a guard that exists but whose effect is defeated
without any error, log, or signal). Classified, fixed (subject-level
`attempts`, this same commit), and regression-tested
(`test_sibling_slot_resolving_does_not_reset_ceiling_progress`, same
commit, `derived:` tag above in "What did not work") per the audit's
Step 5 remediation guidance.
