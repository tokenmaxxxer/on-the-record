---
issue: 2719
role: architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd
author: architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd
skills: architecture-coupling-classification (skill-repository(c05de12)), refactoring-legacy-seam-selection (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: d329e9b9
loop_state: landed
type: fix
breaking: true
verdict: mixed — 1 site kept (documented, no functional change), 1 site given a non-identity signal, 1 site's capability removed (asymmetric loss)
upstream:
  - path: docs/issue-2626/reports/adversarial-review+silent-failure-audit-9ea418cf.md
    sha: same-commit
---

# issue-2719 — architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd record

## What was done

Dispositioned the three sites named by #2626's "Related finding A" (the
#2719 issue body itself quotes only two; the third,
`board.py:907-909` in its pre-change form, is in the linked record's
finding-A block) — canonical: `docs/issue-2626/reports/adversarial-
review+silent-failure-audit-9ea418cf.md` lines 53-73, read directly.
Applied the classification test the assignment asked for — is the
hardcoded name doing identity dispatch (must go), or is it naming what
the gate is genuinely about (may stay) — using
`architecture-coupling-classification`'s rule 4 (control coupling: a
mode flag steering callee behavior → split apart or invert control) and
rule 9 (connascence of Name) as the classification vocabulary, and
core#343's `OBSERVER_ROLES` removal as the direction-of-effect
precedent (canonical: `gh pr diff 345 --repo tokenmaxxxer/
tokenmaxxxer-core`, read live).

All three edits, plus a new regression test, landed in commit
`d329e9b9` on this branch — derived: `git show d329e9b9 --stat`:
```
 board.py                                           |  27 ++++-
 on-the-record/hooks/merge-allow-gate.sh            | 126 +++++++--------------
 on-the-record/hooks/upstream-defect-scope-guard.sh |  31 +++++
 test/test_board_ownership_report.py                |  54 +++++++++
 4 files changed, 152 insertions(+), 86 deletions(-)
```

1. **`on-the-record/hooks/upstream-defect-scope-guard.sh:140,170`**
   (`CHANNEL_SKILL = "upstream-defect-report"`,
   `channel_role_active = CHANNEL_SKILL in mounted`) — **kept, not
   removed.** Classified as "naming what the gate is genuinely about,"
   not identity dispatch: documented the reasoning in a comment block
   above the constant. Zero functional lines changed — derived:
   `git show d329e9b9 -- on-the-record/hooks/upstream-defect-scope-guard.sh | grep -E '^[+-]' | grep -v '^+++\|^---' | grep -vE '^\+#|^-#|^\+$'`
   → no output (every added/removed line is a `#`-comment or blank).

2. **`on-the-record/hooks/merge-allow-gate.sh` (pre-change lines
   210-252: `_routing_fix_should_withhold` and its `("secure-coding",
   "release-engineering")` 2-name tuple + `TRIGGER_PATH_PATTERNS`
   dispatch table)** — **removed**, per the core#343 precedent (same
   shape as the deleted `OBSERVER_ROLES`). Replaced with a
   documentation block naming the removed capability; 83 lines deleted,
   43 inserted — derived: `git show d329e9b9 --stat -- on-the-record/
   hooks/merge-allow-gate.sh` → `1 file changed, 43 insertions(+), 83
   deletions(-)`. Because the loss is asymmetric across the two skills,
   the comment states each half separately (see "Why").

3. **`board.py:907,909` (pre-change: `role == "technical-feasibility"
   and rest.startswith("spikes/")` / `role == "release-engineering" and
   rest.startswith("postmortems/")`)** — **given a new, non-identity
   decision signal.** Replaced with one path-only check
   (`ALT_RECORD_SUBDIRS = ("spikes/", "postmortems/")`, current
   `board.py:911,930` — derived: `grep -n
   "^ALT_RECORD_SUBDIRS\|rest.startswith(ALT_RECORD_SUBDIRS)" board.py`
   → `911:ALT_RECORD_SUBDIRS = ("spikes/", "postmortems/")` and
   `930:        if rest.startswith(ALT_RECORD_SUBDIRS):`). Pinned by a
   new test — derived: `python3 -m pytest
   test/test_board_ownership_report.py -q` → `6 passed in 0.77s`.

Also enumerated all hardcoded closed-set skill/role membership tests in
both enforcement repos per the acceptance's third bullet (full command
and output in "Enumeration" below): four live sites exist in
on-the-record, not three — the fourth (`board.py:587`, `_front_role`'s
2-name tie-break) and a fifth borderline shape (`quality-bar-gate.sh`'s
own 7-domain `_TRIGGER_PATH_PATTERNS` dict) were found, not named by
#2626, and are left untouched (see "Open findings"). tokenmaxxxer-core
has zero live hits.

## Why

### Classification test applied (assignment framing) vs. the issue's own two-outcome Acceptance

The assignment asked for a three-way classification (dispatch → must go;
"genuinely about the gate" → may stay); the issue's own Acceptance
bullet 1 reads as only two outcomes (new signal, or capability removed +
loss stated) — canonical: `gh issue view 2719` Acceptance section, read
live at the start of this session. These two framings collide exactly
at site 1: the issue's own must-not clause forbids "widening a gate to
allow everything... a regression dressed as a removal," and removing
`CHANNEL_SKILL` would do precisely that — condition (b) of `in_scope`
(target-repo mismatch) cannot on its own catch a channel session's
own-origin or target-less (GraphQL `createPullRequest`, `hub
pull-request`) PR-creation attempt, all of which issue #1131 req#4
requires this file to refuse. I resolved the conflict in favor of the
explicit must-not clause over the Acceptance's summary phrasing, and
made the resolution itself the deliverable for that site: a documented
classification, not a code change.

### The distinguishing test, and why it sorts the three sites differently

Direction of effect, not just "does this read an identity string,"
separates a site that must lose its check from one that may keep it.
core#343 removed `OBSERVER_ROLES` because it was a special EXEMPTION
carved out of a stricter baseline (deny-on-closed-issue) — deleting it
made the gate deny MORE, the safe direction, and the operator's ruling
("remove the capability, say what stops working") applies cleanly there
— canonical: `gh pr diff 345 --repo tokenmaxxxer/tokenmaxxxer-core`,
read live.

- `merge-allow-gate.sh`'s `candidates` tuple is the same shape as
  `OBSERVER_ROLES`: a differential-treatment carve-out among an
  open-ended, extensible field of skills (not the one subject a whole
  file exists for), dispatched via a name-keyed table
  (`TRIGGER_PATH_PATTERNS`). Its own pre-change history already named it
  as unreshaped debt — canonical: the removed comment at the deleted
  site (read via `git show d329e9b9^:on-the-record/hooks/merge-allow-gate.sh`
  lines 254-259): "issue #2610: this used to look these two skills'
  trigger up in the (now-deleted) 44-entry role catalog... inlining
  their trigger data here drops the JSON dependency without shrinking
  or reshaping the set this hook special-cases." Removed, per the same
  ruling core#343 applied — asymmetrically, because the actual safety
  consequence differs per skill (next section).
- `board.py:907-909`'s two branches are the same shape *structurally*,
  but a genuine non-identity replacement exists: the branch never
  needed "which role" — it needed "is this a recognized alternate
  record-location convention," a fact fully determined by the path
  alone. This is not a container/config relocation of the identity
  literal (the #2548 must-not) — it drops the identity read entirely.
- `upstream-defect-scope-guard.sh`'s `CHANNEL_SKILL` does the *opposite*
  of `OBSERVER_ROLES`: it is condition (a) of `in_scope`'s OR, adding an
  extra denial beyond what the target-repo check alone would refuse.
  Deleting it widens the gate — the forbidden direction — for exactly
  the shape issue #1171/#2669's own file history documents as a real,
  previously-fixed incident (issue-1163's own delivery PR wrongly
  denied by an earlier, under-scoped version of this file) — canonical:
  `on-the-record/hooks/upstream-defect-scope-guard.sh` lines 22-29, read
  directly. It is also not a dispatch table: there is only one channel
  this file exists to constrain, nothing to add a second name to, no
  catalog reconstructed.

### Why merge-allow-gate.sh's capability loss is asymmetric, not uniform

`on-the-record/hooks/quality-bar-gate.sh`'s own `_TRIGGER_PATH_PATTERNS`
dict carries a `"secure-coding"` entry whose path-pattern list is
byte-identical to the one removed from `merge-allow-gate.sh` — derived:
```
$ diff <(git show d329e9b9^:on-the-record/hooks/merge-allow-gate.sh | sed -n '261,263p') \
       <(sed -n '240,242p' on-the-record/hooks/quality-bar-gate.sh)
(no output — identical)
```
That hook independently **denies** (not merely withholds an allow) any
`gh pr merge` on a secure-coding-bar-scoped PR lacking a
`quality_bar_verdict: bar-met` line — canonical:
`on-the-record/hooks/quality-bar-gate.sh` lines 1-13 (file header, read
directly): "Unlike merge-allow-gate.sh (which only ever ADDS an
'allow'), this hook emits a `deny`... reusing the existing deny-wins-
over-allow composition merge-allow-gate.sh's own docstring already
documents." So removing the secure-coding half of the routing-fix is
not a net capability loss — `quality-bar-gate.sh` already blocks the
same merges, unconditionally, on a completely separate,
non-identity-in-*this*-file mechanism. `release-engineering` has no
such domain in `quality-bar-gate.sh`'s dict — derived: `grep -n
'"release-engineering"' on-the-record/hooks/quality-bar-gate.sh` → no
output; its loss is real and is named in the removal comment.

## Site-by-site: gate exercised on an allow payload and a refuse payload, before and after (acceptance bullet 2)

### Site 1 — `upstream-defect-scope-guard.sh` (unchanged both ways)

derived (payload:
`{"tool_name":"Bash","tool_input":{"command":"gh pr create --repo
tokenmaxxxer/on-the-record"},"cwd":"<this checkout>"}`, run against both
`git show d329e9b9^:...` (BEFORE) and the current tree (AFTER) via `git
stash`):
```
$ env MUSTER_SKILLS=upstream-defect-report on-the-record/hooks/upstream-defect-scope-guard.sh < payload.json; echo rc=$?
BEFORE: upstream-defect-scope-guard: `gh pr create` (including a GH_REPO/GH_HOST-env-var-prefixed invocation) is denied — the upstream defect channel files issues only, never PRs (issue #1131 req#4).
rc=2
AFTER:  identical stderr line
rc=2

$ env -u MUSTER_SKILLS on-the-record/hooks/upstream-defect-scope-guard.sh < payload.json; echo rc=$?
BEFORE: rc=0, no output
AFTER:  rc=0, no output
```
This before/after pair is a proof of no functional change (the
comment-only-diff check in "What was done" item 1), not an assumption.

### Site 2 — `merge-allow-gate.sh` (the real, intended behavior change)

Fixture: a throwaway git repo at `/tmp` (outside this checkout), branch
`issue-4242/secure-coding`, one commit touching `auth/**` (a
secure-coding trigger path), `TOKENMAXXXER_SPAWNED` unset (orchestrator
identity), `MUSTER_SKILLS=secure-coding`, a stub
`gates/landing_readiness.py` that always reports `PR #42: READY`.
derived:
```
$ printf '%s' "$PAYLOAD" | on-the-record/hooks/merge-allow-gate.sh   # record ABSENT for the fixture issue
BEFORE (git show d329e9b9^, original routing-fix): rc=0, no output — withheld
AFTER  (d329e9b9):
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": "merge-allow-gate: PR #42 is landing_readiness=READY (gates/landing_readiness.py) and this is the orchestration session (not spawned) — issue #810."}}
rc=0

$ same payload, docs/issue-4242/reports/secure-coding.md now PRESENT
BEFORE: same allow JSON as AFTER above — the routing-fix only withholds when the record is absent, so this payload is unaffected either way
AFTER:  same allow JSON

$ same payload, MUSTER_SKILLS unset (control: non-scoped skill)
BEFORE: same allow JSON
AFTER:  same allow JSON
```
The only observable behavior change across all three payload shapes is
the first (secure-coding mounted, sensitive path touched, record
absent) — exactly the capability named as removed above, live and
reproducible.

### Site 3 — `board.py` ownership_report (pure function, exercised directly)

derived:
```
$ python3 -c "import board; print(board.ownership_report('.', 'technical-feasibility', [<own spikes path>]))"
BEFORE (d329e9b9^): []      AFTER (d329e9b9): []      (unchanged — the historically-exempted case)

$ same, role='coding', same spikes path
BEFORE: ['[소유권] coding 이 자기 것이 아닌 보드 경로를 건드렸다 ...', '  - .../spikes/foo.md (다른 역할의 기록)']
AFTER:  []      (the disclosed widening — flips)

$ same, role='coding', unrelated path
BEFORE: ['[소유권] ...', '  - .../other-role.md (다른 역할의 기록)']
AFTER:  identical      (unrelated paths still flagged, unchanged)
```
Pinned permanently — derived: `python3 -m pytest
test/test_board_ownership_report.py -q` → `6 passed in 0.77s`.

## Enumeration (acceptance bullet 3): the command that produced it

derived:
```
$ grep -rnE '\brole\s*==\s*"|\brole\s+in\s*\(|\bskill\s*==\s*"|\bskill\s+in\s*\(|MUSTER_SKILLS.*in\s*\(|in\s*\("[a-z-]+",\s*"[a-z-]+"\)|ROLES\s*=|_ROLES\s*=' \
    --include='*.py' --include='*.sh' . 2>/dev/null | grep -v -E '/(test|tests)/|docs/|\.md:'
```
Non-noise hits (CLI-subcommand-dispatch matches like `spawn.py`'s
`a.role == "init"`/`"ps"`/`"rebase"` — literal CLI verbs, not a
skill/role identity catalog — and stdlib-shaped `argv[0] in
("open","resolve")` tuples in unrelated gates, are excluded as out of
population — canonical: full raw grep output inspected line by line
this session):

- `board.py:587` (current tree) — `for r in ("product-discovery",
  "technical-feasibility"): if r in roles: return r` inside
  `_front_role`, a 2-name tie-break used when a subject has more than
  one rootless record, feeding `approve_scope`'s choice of which
  record/branch the scope-approval flow targets. Not named by #2626.
  **Not fixed in this PR** — flagged in "Open findings" below.
- `board.py:892` (current tree) — the doc-comment above
  `ALT_RECORD_SUBDIRS` narrating the removed shape (matches the search
  pattern as prose, not code).
- `scripts/behavior_metrics.py:35` — `EXPECTED_COMMIT_ROLES =
  {"implementation", "coding"}`, a reporting/metrics threshold, not a
  gate/hook enforcement decision. Out of population (a metrics script,
  not a "hook or gate"); noted for completeness, not dispositioned.

A second sweep for dict-shaped (not tuple-`in`) dispatch tables found
one more borderline shape not caught by the regex above — derived:
`sed -n '225,243p' on-the-record/hooks/quality-bar-gate.sh`:
```
_TRIGGER_PATH_PATTERNS = {
    "interaction-design": ["docs/issue-*/reports/product-discovery.md"],
    "test-authoring": ["src/**", "lib/**", "app/**"],
    "ux-engineering": ["**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.svelte"],
    "api-design": [],
    "performance-engineering": [],
    "accessibility": ["**/*token*", "**/*.css", "**/*.tsx", "**/*.jsx",
                       "**/interaction*"],
    "secure-coding": ["**/auth/**", "**/*credential*", "**/*permission*",
                       "**/*secret*", "**/*password*", "**/*login*",
                       "**/*input*", "**/*sanitiz*", "**/*validat*"],
}
```
A 7-key dict mapping domain name → trigger path patterns, the hook's
own per-domain quality-bar configuration (issue #1156). Structurally
similar to the removed `merge-allow-gate.sh` table, but the hook's own
header states this data IS the subject the file exists to encode
(per-domain quality bars, covering 7 domains generic to any bar-scoped
skill), rather than a 2-name special-case carve-out inside a different,
general-purpose gate. Not named by #2626, not touched here — flagged in
"Open findings."

tokenmaxxxer-core: derived (fresh shallow clone, not recalled from the
issue body):
```
$ git clone --depth 1 https://github.com/tokenmaxxxer/tokenmaxxxer-core.git /tmp/core-audit
$ grep -rnE '\brole\s*==\s*"|\brole\s+in\s*\(|\bskill\s*==\s*"|\bskill\s+in\s*\(|MUSTER_SKILLS.*in\s*\(|in\s*\("[a-z-]+",\s*"[a-z-]+"\)|_ROLES\s*=|OBSERVER_ROLES' \
    --include='*.py' --include='*.sh' . 2>/dev/null | grep -v -E '/(test|tests)/|docs/|\.md:'
core/hooks/approval-gate.sh:301:# auto-closed via that role's PR merge, implemented as OBSERVER_ROLES =
core/hooks/approval-gate.sh:303:# runtime (`role in OBSERVER_ROLES`) plus a hard-coded second identity,
```
Zero live hits — the two remaining mentions are both inside
`approval-gate.sh`'s own `#`-prefixed CAPABILITY-REMOVED comment block
(core#343, PR #345, merged — confirmed above via `gh pr diff`).

**Not exactly three sites** (empty state named, per acceptance bullet
3's own "three sites and no more — state that as the finding"): four
hardcoded-literal closed-set membership tests exist in on-the-record
(the three named plus `board.py:587`), plus one further borderline
dict-shaped configuration table (`quality-bar-gate.sh`). tokenmaxxxer-
core has zero.

## What did not work

A test-fixture command mid-session accidentally ran `git rm -rq --cached
docs` against this checkout's own working directory instead of the
throwaway `/tmp` fixture repo it was intended for (the Bash tool call's
cwd was this checkout; the fixture path was only referenced inside a
JSON payload string, not `cd`-ed into). This staged a deletion of every
tracked path under `docs/` in the git index — derived: `git status
--short | cut -c1-2 | sort | uniq -c` immediately after showed `3776 D`.
Caught before any commit by running `git status --short` per this
session's own safety protocol; verified the working-tree file content
was untouched and byte-identical to `HEAD` — derived: `git show
HEAD:docs/specs/upstream-defect-channel.md | diff -
docs/specs/upstream-defect-channel.md` → no diff output (confirmed by an
explicit `IDENTICAL` echo appended after the diff, which printed).
Recovered with `git reset -q -- docs/` (unstage only, no working-tree
write). Confirmed clean afterward — derived: `git status --short`
immediately after showed only the three intended file modifications
plus the untracked `docs/issue-2719/` skeleton this role's own record
lives in. No data was lost; nothing from this incident reached a commit.

## Upstream basis

- `docs/issue-2626/reports/adversarial-review+silent-failure-audit-9ea418cf.md` (same-commit) — "Related finding A" section, the source of the three named sites and their file:line citations.
- `core/hooks/approval-gate.sh` in tokenmaxxxer-core (external repo, PR tokenmaxxxer/tokenmaxxxer-core#345, merged) — canonical: `gh pr diff 345 --repo tokenmaxxxer/tokenmaxxxer-core`, read live this session — the `OBSERVER_ROLES` removal precedent this issue's spawn prompt named explicitly as the pattern to study.
- `on-the-record/hooks/quality-bar-gate.sh` (same-commit, read not modified) — the independent secure-coding backstop that makes half of site 2's removal a non-loss.

## Open findings

1. `board.py:587` (`_front_role`'s `("product-discovery",
   "technical-feasibility")` 2-name tie-break, feeding `approve_scope`'s
   choice of which record/branch a scope-approval targets) — a fourth
   hardcoded closed-set membership test, same shape as the three named
   by #2626, not itself named by #2626 or this issue. Not fixed here —
   this issue named three sites; a fourth needs its own operator-filed
   follow-up, matching #2626's own practice of flagging rather than
   silently expanding scope. Resolution path: file a follow-up issue; a
   candidate non-identity signal exists (this function only runs when
   `len(rootless) != 1`, i.e., already an ambiguous multi-root case — a
   plausible replacement is ordering by earliest commit rather than by
   name), but that is a design decision for that issue, not this one.
2. `on-the-record/hooks/quality-bar-gate.sh:232-243`
   (`_TRIGGER_PATH_PATTERNS`, 7 hardcoded domain names) — borderline
   shape, discussed above, not named by #2626, not touched here.
   Resolution path: a follow-up issue should judge whether this dict is
   "naming what the gate is about" (its own header's framing) or an
   extensible catalog that should instead read domains from live skill
   specs — a judgment this record does not make since the file was not
   named in scope.
3. `on-the-record/hooks/merge-allow-gate.sh`'s `record_path` (both
   before and after this change, in the surrounding, untouched code) is
   built from `role + ".md"` — derived: `grep -n 'reports.*role +
   ".md"\|role + ".md"' on-the-record/hooks/merge-allow-gate.sh` →
   `os.path.join(cwd, "docs", "issue-%s" % issue, "reports", role +
   ".md")` — the pre-#2555/#2568 role-named record convention, not the
   current slug-named one `quality-bar-gate.sh` already migrated to
   (canonical: `on-the-record/hooks/quality-bar-gate.sh` lines 19-27,
   read directly: "records are slug-named, not role-named (#2555)").
   Noticed while reading the surrounding legacy code per
   `refactoring-legacy-seam-selection` rule 7, not fixed here (out of
   this issue's scope — fixing it would require redesigning the
   withhold mechanism this record just removed). Left named rather than
   silently carried forward.

## Next steps

None from this session. `loop_state` is `landed` — every disposition and
before/after exercise this record claims is cited with its own
`derived:`/`canonical:` evidence in the "What was done," "Site-by-site,"
and "Enumeration" sections above; this section does not restate results.
The enumeration's two extra findings were handed to the operator via
"Open findings" above (this role session cannot file issues itself, per
#2626's own precedent for the same constraint).

## Skill verdicts

- skill-verdict: architecture-coupling-classification — applied: invoked; used rule 4 (control coupling — a hardcoded identity flag steering callee behavior, corrective action "split apart or invert control") to classify `merge-allow-gate.sh`'s and `board.py`'s sites as dispatch requiring removal/inversion, and rule 9 (connascence of Name) plus the direction-of-effect distinction (does removing the check tighten or widen the gate) to classify `upstream-defect-scope-guard.sh`'s `CHANNEL_SKILL` as the gate's own subject rather than dispatch.
- skill-verdict: refactoring-legacy-seam-selection — applied: invoked; used rule 6 (narrow the seam to the smallest enclosing scope, no scope creep) to keep each of the three edits local to its own decision branch rather than restructuring the surrounding functions, and rule 7 (read the surrounding legacy code for hidden business rules before choosing a seam) to find `quality-bar-gate.sh`'s independent secure-coding backstop (which changed the asymmetric-loss finding) and the pre-existing `role + ".md"` staleness bug (named in Open findings, not fixed, per the same rule's scope discipline).
- skill-verdict: adversarial-review — applied: invoked; spawned a fresh, structurally independent subagent with only the raw `git diff` of the three changed files (no spec, no issue text, no builder intent) and the minimal evaluator prompt the skill specifies. It returned four findings: (1) in-code comments cited "this issue's record" as evidence before the record existed — fixed by writing this record with the actual derived commands/outputs the comments point to; (2) `board.py`'s widening claim ("no such write has ever been observed") was asserted, not verified — fixed by running `git log --all --diff-filter=A -- 'docs/issue-*/reports/spikes/*' 'docs/issue-*/reports/postmortems/*'` (zero commits, derived) and by adding `test/test_board_ownership_report.py`; (3) `merge-allow-gate.sh`'s 83-line removal has no permanent automated test, before or after — acknowledged as a pre-existing test-infrastructure gap for this hook (no `stub_gh`-style harness exists for it, unlike `approval-gate.sh`), out of this issue's scope to build from scratch; the live git-stash reproduction above is the acceptance-mandated evidence instead; (4) `upstream-defect-scope-guard.sh`'s comment-only diff was flagged as scope-inflating — kept as-is, since the assignment explicitly asked this classification decision to be shown, not just made silently.
- other mounted skills: not triggered (work-in-english followed implicitly throughout — code, comments, tests, and this record are in English).
