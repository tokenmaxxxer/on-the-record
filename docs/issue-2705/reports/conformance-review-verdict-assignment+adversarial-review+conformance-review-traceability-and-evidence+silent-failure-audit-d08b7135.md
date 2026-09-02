---
issue: 2705
role: conformance-review-verdict-assignment+adversarial-review+conformance-review-traceability-and-evidence+silent-failure-audit-d08b7135
author: conformance-review-verdict-assignment+adversarial-review+conformance-review-traceability-and-evidence+silent-failure-audit-d08b7135
skills: conformance-review-verdict-assignment (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), conformance-review-traceability-and-evidence (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # this record is a builder-blind re-grade of PR #2872's own deliverable
loop_state: graded
upstream:
  - path: PR #2872 (branch issue-2705/architecture-interface-contract-shape-952309f5)
    sha: b3091bfb600251c26703913e27001098e1181002
  - path: issue #2705 disposition comment amending criterion 1 (2026-09-02, following PR #3048's builder-blind grading)
    sha: same-commit
---

# issue-2705 — conformance-review-verdict-assignment+adversarial-review+conformance-review-traceability-and-evidence+silent-failure-audit-d08b7135 record

## What was done

Re-graded PR #2872 (branch `issue-2705/architecture-interface-contract-shape-952309f5`, head
`b3091bfb600251c26703913e27001098e1181002`) against issue #2705's three Acceptance criteria,
builder-blind (judged from the diff and issue text, not the PR's own narrative), with criterion 1
graded against the text amended 2026-09-02. Re-derived every claim live in this session rather than
carrying forward the prior grading session's (PR #3048) findings on trust — including the ones the
spawning prompt itself supplied as background.

canonical: `gh issue view 2705 --json title,body,number,state,url`, read in full this turn —
Acceptance section quoted verbatim in the criteria below.

**Criterion 1 — "the bundled shape is caught and reported, with the weaker promise named explicitly
in the text a session reads" (AMENDED 2026-09-02) — verdict: Present.**

Built a fresh scratch git repo (`/tmp/grg-live-fixture/repo`, outside this repo's tracked tree, no
reuse of the PR's own test fixture) and ran the literal shape the issue names, `git add
gates/new_gate.py && git commit -m "add new gate"`, as ONE Bash call —
acceptance: `git add gates/new_gate.py && git commit -m "add new gate"` (single call, this turn) —
result:
```
[master 895ef6d] add new gate
 1 file changed, 1 insertion(+)
 create mode 100644 gates/new_gate.py
```
Fed that real stdout, inside a realistic `PostToolUse`/`Bash` payload (`tool_input.command` +
`tool_response`, matching the shape Claude Code actually sends — my first attempt omitted
`tool_input` and the guard's own cheap grep short-circuit correctly skipped it, which is itself
evidence the short-circuit works as designed, not a guard defect), to PR #2872's own
`b3091bfb600251c26703913e27001098e1181002:on-the-record/hooks/gate-registration-post-guard.sh`
in `post` mode —
acceptance: `OTR_GRG_POST_STATE_DIR=/tmp/grg-live-fixture/state bash gate-registration-post-guard.sh
post < post_payload.json` (this turn, script checked out from PR #2872's branch into
`/tmp/pr2872-review`) — result: exit 0, state file written: `{"violations": [{"sha": "895ef6d",
"path": "gates/new_gate.py", "message": "gates/new_gate.py: no row in
docs/specs/enforcement-boundary.md"}]}`.
Then fed a `PreToolUse` payload for the next tool call (any matched tool — `on-the-record/hooks/
hooks.json:46` wires `pre` mode to `Write|Edit|MultiEdit|NotebookEdit|Bash|WebFetch`, verified
against this same file's own copy in this branch's own working tree, unchanged by the PR's diff
aside from adding the two new lines wiring the companion) to the same script's `pre` mode —
acceptance: `OTR_GRG_POST_STATE_DIR=/tmp/grg-live-fixture/state bash gate-registration-post-guard.sh
pre < pre_payload.json` (this turn) — result: exit 0, stdout:
```
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "gate-registration-guard
(post-commit report, issue #2705): the following commit(s) already exist in git history and cannot
be blocked or reverted by this hook -- gate-registration-guard.sh only sees a `git commit`'s staged
set BEFORE the command runs, so a bundled `git add ... && git commit ...` call left nothing to
refuse at the time it fired:\n  - 895ef6d: gates/new_gate.py: no row in
docs/specs/enforcement-boundary.md\nAdd the missing row(s) above in a follow-up commit now. This
report is the weaker half of a deliberate two-guard split (issue #2705): gate-registration-guard.sh's
own PreToolUse/`--cached` check is unchanged and still REFUSES the commit outright when the file was
staged in an earlier, separate Bash call -- only the single-call bundled shape lands first and is
reported after the fact."}}
```
This is, verbatim, "the text a session actually reads" naming that this is a report after the fact
rather than a refusal before it — both sub-checks of the amended criterion are satisfied by a live
run this session executed, not by the PR's own claims.

Caveat, named rather than absorbed: the report is not emitted synchronously as part of the bundled
`git add && git commit` call's own tool result — `post` mode only ever writes state and, per
`b3091bfb600251c26703913e27001098e1181002:docs/handbooks/hooks.md` (this PR's diff, +79 lines) and
`retry-loop-bound.sh`'s own established precedent in this repo, never emits `additionalContext`
itself. The text above surfaces only on the session's *next* tool call matched by the `pre`-mode
matcher. If a session bundles the commit and ends its turn immediately after with no further matched
tool call, the report does not surface in that turn. This is an architectural constraint of
`PostToolUse` (it cannot inject context into a `PreToolUse`-shaped field), not a hidden defect, and
the criterion's own check text does not demand synchronicity — but it is a real, load-bearing gap
between "reported" and "reported immediately" that a reader of this grade should know about.

**Criterion 2 — "the unbundled shape still behaves as today" — verdict: Present.**

acceptance: `git diff main -- on-the-record/hooks/gate-registration-guard.sh` (PR #2872's branch,
this turn) — result: 0 lines changed — the file this PR must not touch is byte-identical to `main`.
Staged a second new gate file in the same fixture repo in one call, then fed a `PreToolUse` payload
for `git commit -m "add another gate"` alone (a following call) to that unmodified script —
acceptance: `bash gate-registration-guard.sh < pre_unbundled.json` (this turn) — result:
```
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue
#441/#684):
gates/another_gate.py: no row in docs/specs/enforcement-boundary.md
Fix the row in the same commit (docs/specs/enforcement-boundary.md, and for a hook script also
docs/specs/generated-paths.md), then retry the commit.
```
exit 2. Unchanged refusal, live-verified.

**Criterion 3 — "every other hook that reads staged or working-tree state from PreToolUse is
enumerated, with a verdict... population: all PreToolUse hooks in `on-the-record/hooks/` and core's
`hooks/`" — verdict: Surface. Failing clause: population is not actually complete despite being
claimed complete.**

PR #2872's own enumeration
(`b3091bfb600251c26703913e27001098e1181002:docs/issue-2705/reports/architecture-interface-contract-shape-952309f5.md:231-232`)
claims coverage of "all 12 `PreToolUse` gates in `tokenmaxxxer-core`'s `core/hooks/`". I did not
carry that count forward — I independently walked
`f0d9d54d79643d2386c4faf28a63e43d2bf12384:core/hooks/pretooluse_dispatcher.py:437-448` (the
`tokenmaxxxer-core` plugin checkout at `$CLAUDE_PLUGIN_ROOT_CORE`), which is the actual dispatch
table for every core `PreToolUse` gate — core's `hooks.json` `PreToolUse` section wires only
`pretooluse-dispatcher.sh` —
derived: `python3 -c "import json; d=json.load(open('hooks.json')); ..."` against
`f0d9d54d79643d2386c4faf28a63e43d2bf12384:core/hooks/hooks.json` (this turn) — result: exactly one
`PreToolUse` command, `pretooluse-dispatcher.sh`, confirming the `GATES` list below is the full
population:
```
GATES = [
    ("approval-gate.sh", _setup_approval_gate, "keep"),
    ("board-gate.sh", _setup_board_gate, "keep"),
    ("gh-guard.sh", _setup_gh_guard, "keep"),
    ("ordering-gate.sh", _setup_ordering_gate, "keep"),
    ("record-shape-gate.sh", _setup_record_shape_gate, "keep"),
    ("citation-gate.sh", _setup_citation_gate, "demote"),
    ("facet-keyword-gate.sh", _setup_facet_keyword_gate, "demote"),
    ("handbook-trigger-gate.sh", _setup_handbook_trigger_gate, "demote"),
    ("proposal-shape-gate.sh", _setup_proposal_shape_gate, "demote"),
    ("record-fields-gate.sh", _setup_record_fields_gate, "demote"),
    ("survey-order-gate.sh", _setup_survey_order_gate, "demote"),
    ("trailer-gate.sh", _setup_trailer_gate, "demote"),
]
```
That is genuinely 12 entries — derived: counted this turn by reading the block above in full. But
PR #2872's own table
(`b3091bfb600251c26703913e27001098e1181002:docs/issue-2705/reports/architecture-interface-contract-shape-952309f5.md:238-246`)
only names 10 distinct core hooks — derived: counted this turn from that same file's rows —
`trailer-gate.sh` (line 242), `handbook-trigger-gate.sh` (line 243), and 8 more folded into the
"remaining `core/hooks/` `PreToolUse` gates" row at line 245: `board-gate.sh`, `gh-guard.sh`,
`ordering-gate.sh`, `citation-gate.sh`, `facet-keyword-gate.sh`, `proposal-shape-gate.sh`,
`record-fields-gate.sh`, `survey-order-gate.sh`. Two of the 12 are missing:

1. `f0d9d54d79643d2386c4faf28a63e43d2bf12384:core/hooks/record-shape-gate.sh` is never named
   anywhere in the enumeration, and it does read working-tree state —
   acceptance: `grep -nE '"(diff|status|ls-files)"|git diff|git status|git ls-files'
   core/hooks/record-shape-gate.sh` (this turn, that checkout) — result: line 134,
   `["git", "-C", root, "diff", "HEAD", "--numstat"]` — the same class of read
   `record-fields-gate.sh` (which the table DOES cover, at line 245, correctly reasoning through why
   it's not vulnerable) has. `record-shape-gate.sh` got no equivalent reasoning; it got no mention.
2. The table's own line 244 lists `approval-gate.sh` once, inside the "remaining 15
   `on-the-record/hooks/`" bucket — that is `on-the-record/hooks/approval-gate.sh`, a different,
   unrelated file, not `core/hooks/approval-gate.sh` —
   derived: `diff on-the-record/hooks/approval-gate.sh core/hooks/approval-gate.sh` (this turn, PR
   #2872's checkout vs. the `tokenmaxxxer-core` checkout) — result: 878 lines of diff, files not
   identical (16,381 bytes vs. 27,909 bytes). `core/hooks/approval-gate.sh` is never independently
   addressed anywhere in the table.

The enumeration mechanism itself is real, not fabricated — the 21-dispatcher-routed +1-direct count
for `on-the-record/hooks/` checks out —
derived: read `on-the-record/hooks/pretooluse_dispatcher.py:259-315` this turn (this branch's own
copy, unmodified by the PR) — result: 21 `GATES` entries, counted in full — the new guard's
`hooks.json` wiring is real (`on-the-record/hooks/hooks.json:46,70` in PR #2872's diff, confirmed by
reading that file this turn), and most of the named rows carry their own live-executed command, not
a bare assertion. But "population: all PreToolUse hooks in ... core's `hooks/`" is the literal text
of the criterion's check, and the population walked is short two of twelve — one of which
(`record-shape-gate.sh`) reads exactly the kind of state this criterion exists to survey. Per this
session's own conformance-review-verdict-assignment skill (rule 1): the enumeration artifact exists
and does real work, but a check of what it actually covers shows it does not fire on the full
condition ("every other hook... population: all") the criterion names — that is Surface, not
Present.

**Must-not clause — verdict: respected.**
"Do not move the check to PostToolUse without saying what that costs... it must be stated as a
change in what the guard promises, not presented as the same guard fixed." `gate-registration-
guard.sh` was not moved — it is untouched (criterion 2 evidence above, 0-line diff against `main`)
and still REFUSES the unbundled shape exactly as before. A separate, new file
(`gate-registration-post-guard.sh`) was added as an explicitly weaker companion, and the live
`additionalContext` text captured under criterion 1 above names the split itself, in-band, in the
words a session reads at runtime: "This report is the weaker half of a deliberate two-guard split...
only the single-call bundled shape lands first and is reported after the fact." That is the cost
being named, not absorbed, and it is named in the artifact a session actually sees at runtime, not
only in a header comment or this record. The other two must-not clauses ("stop bundling" and
"silently widen to fail-closed") are also respected: bundling still works end to end (criterion 1
demo above), and `gate-registration-guard.sh`'s own refusal scope is unchanged (criterion 2 demo
above, 0-line diff).

## Why

The issue's own disposition comment (posted 2026-09-02, after PR #3048's builder-blind grading)
amended criterion 1 because the unamended text demanded a `PreToolUse` refusal on the bundled shape,
which this issue's own four adversarial-review rounds and seam consult established is undecidable
in general — the amendment brought the criterion in line with the issue's own later ruling rather
than leaving a frozen criterion asking for something the issue had already concluded was not
achievable at that seam. This session's job was to re-grade PR #2872 against that amended text, not
to re-litigate the amendment itself (out of scope — the amendment's own bound is stated in the
disposition comment, and this session did not touch it).

I re-derived rather than trusted every claim the spawning prompt handed me as background (the
"zero refusal paths" grep, the "34-hook enumeration spot-checks accurate" characterization) because
the prompt itself said not to carry those forward on trust. The zero-refusal-paths claim held up —
acceptance: `grep -n 'exit 2\|deny(' on-the-record/hooks/gate-registration-post-guard.sh` (this turn,
PR #2872's checkout) — result: no matches, 435 lines (`wc -l`, same file, this turn) — but
re-deriving the enumeration's completeness surfaced a population gap the prior characterization did
not: 2 of the 12 claimed core hooks are not actually enumerated (criterion 3 above). Re-deriving
rather than reusing is why that gap is now on the record instead of carried forward silently.

## What did not work

None.

## Upstream basis

- PR #2872, branch `issue-2705/architecture-interface-contract-shape-952309f5`, head
  `b3091bfb600251c26703913e27001098e1181002` — the subject graded. Fetched via `gh pr view 2872
  --json ...` and `git fetch origin pull/2872/head` into a scratch worktree at `/tmp/pr2872-review`
  this turn (that worktree and `/tmp/grg-live-fixture` are scratch, outside this repo's tracked
  tree, not part of this delivery, and not committed).
- Issue #2705 body and comment thread, read fresh via `gh issue view 2705 --comments` this turn —
  the amended Acceptance text and the disposition comment explaining the amendment's bound are both
  quoted from that read above.
- `tokenmaxxxer-core` checkout at `f0d9d54d79643d2386c4faf28a63e43d2bf12384` (`$CLAUDE_PLUGIN_ROOT_CORE`,
  a separate repository from this one) — read for the core `PreToolUse` dispatch table (criterion 3
  evidence).
- Prior grading record referenced by the spawning prompt (PR #3048's builder-blind grading, quoted
  in issue #2705's disposition comment) — used only as a pointer to what to re-check, not as a
  source of any verdict carried forward without re-derivation.

## Open findings

- **Criterion 3 population gap** (this session's own finding, not carried from PR #3048): as shown
  above, `core/hooks/record-shape-gate.sh` and `core/hooks/approval-gate.sh` are absent from PR
  #2872's enumeration table (the latter conflated with an unrelated same-named file in
  `on-the-record/hooks/`). Resolution path: PR #2872's own enumeration table needs two more rows
  before criterion 3 can grade Present — `record-shape-gate.sh`'s verdict (it reads `git diff HEAD
  --numstat`, working-tree-vs-HEAD, same class as the already-covered `record-fields-gate.sh`) and a
  genuine, separate row for `core/hooks/approval-gate.sh`.
- **Minor, non-blocking, from the silent-failure-audit lens**:
  `b3091bfb600251c26703913e27001098e1181002:on-the-record/hooks/gate-registration-post-guard.sh`'s
  `_load()` and `_save()` functions both swallow `(OSError, ValueError)`/`OSError` with a bare
  except/default-return —
  acceptance: read
  `b3091bfb600251c26703913e27001098e1181002:on-the-record/hooks/gate-registration-post-guard.sh:147-182`
  this turn (PR #2872's checkout) — result:
  ```
  def _load():
      try:
          with open(state_path, "r", encoding="utf-8") as f:
              data = json.load(f)
          if isinstance(data, dict) and isinstance(data.get("violations"), list):
              return data
      except (OSError, ValueError):
          pass
      return {"violations": []}
  ```
  A corrupted or unwritable state file silently drops an outstanding violation report rather than
  surfacing the failure. This matches this repo's established fail-open convention for hooks
  generally (documented inline, consistent with `post-landing-obligation-gate.sh`/
  `approach-cap-warning.sh`'s own precedent, both present in this branch's own
  `on-the-record/hooks/` tree) rather than being a defect specific to this PR, and does not bear on
  any of the three graded criteria — noted for completeness, not as a criterion failure.
- Criteria 1 and 2: none open — both live-verified Present in this session above, with their own
  `acceptance:`/`derived:` evidence, no open gap.

## Next steps

loop_state is terminal (`graded`, frontmatter) — the three criteria and the must-not clause each
carry their own `acceptance:`/`derived:` evidence in "What was done" above (Present, Present,
Surface, and respected respectively), independently re-derived this turn rather than carried forward
from PR #3048. The one open item (criterion 3's population gap, "Open findings" above) is a finding
for a future PR #2872 revision or reviewer action to act on, not further work for this record.

## Skill verdicts

skill-verdict: conformance-review-verdict-assignment — applied: invoked; used rule 1 (Surface vs.
Present when matching artifact exists but doesn't fire on the full stated condition) to grade
criterion 3, and rule 5 (name the failing clause) throughout "What was done" above.
skill-verdict: adversarial-review — applied: invoked; graded PR #2872 builder-blind per this
session's own prompt (diff and issue text only, PR's own narrative claims never taken as evidence)
and re-derived every claim independently rather than carrying forward the prior grading session's
characterizations, per Step 4's "user filters, evaluator doesn't self-defend" mechanism applied to
this session's own prior-background inputs.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; cited file:line plus
commit sha for every evidence location above (rule 1), including sha-pinning
`b3091bfb600251c26703913e27001098e1181002:docs/issue-2705/reports/architecture-interface-contract-shape-952309f5.md`
and `f0d9d54d79643d2386c4faf28a63e43d2bf12384:core/hooks/*` paths that live outside this branch's own
working tree.
skill-verdict: silent-failure-audit — applied: invoked; classified
`gate-registration-post-guard.sh`'s `_load()`/`_save()` swallow-and-default pattern as Silently
Absorbed (Open findings above), traced forward to its downstream consequence (a corrupted state file
silently drops an outstanding violation report), and judged it non-blocking against this repo's own
established fail-open hook convention rather than a defect unique to this PR.
