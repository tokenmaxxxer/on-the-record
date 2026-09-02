---
issue: 2705
role: conformance-review-traceability-and-evidence+silent-failure-audit-6f24be9d
author: conformance-review-traceability-and-evidence+silent-failure-audit-6f24be9d
skills: conformance-review-traceability-and-evidence (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # this record completes PR #2872's own criterion-3 enumeration, a
  correction of that subject's own deliverable
loop_state: complete
upstream:
  - path: PR #2872, branch issue-2705/architecture-interface-contract-shape-952309f5,
      docs/issue-2705/reports/architecture-interface-contract-shape-952309f5.md (untracked in
      this working tree; fetched via git fetch/worktree add this turn then reverted and
      removed, see "Why")
    sha: b3091bfb600251c26703913e27001098e1181002
  - path: PR #3051, docs/issue-2705/reports/conformance-review-verdict-assignment+
      adversarial-review+conformance-review-traceability-and-evidence+
      silent-failure-audit-d08b7135.md (untracked in this working tree; PR open/unmerged)
    sha: 1f1796552de3fae8a90113e29792f48003303f54
  - path: tokenmaxxxer-core plugin checkout, core/hooks/pretooluse_dispatcher.py,
      core/hooks/record-shape-gate.sh, core/hooks/approval-gate.sh, core/hooks/board-gate.sh,
      core/hooks/hooks.json (untracked in this working tree; $CLAUDE_PLUGIN_ROOT_CORE mount)
    sha: f0d9d54d79643d2386c4faf28a63e43d2bf12384
---

# issue-2705 — conformance-review-traceability-and-evidence+silent-failure-audit-6f24be9d record

## What was done

Assigned task: complete PR #2872's criterion-3 enumeration for issue #2705, directly on that PR's
own branch (`issue-2705/architecture-interface-contract-shape-952309f5`), because PR #3051's
independent re-grading found the enumeration Surface, not Present — the table claims "all 12"
core `PreToolUse` gates but names only 10, missing `core/hooks/record-shape-gate.sh` entirely and
silently conflating core's `approval-gate.sh` with the unrelated same-named file already counted
in the `on-the-record/hooks/` group.
canonical: `gh pr view 3051 --repo tokenmaxxxer/on-the-record`, read this turn — criterion 3
verdict "Surface", both gaps named explicitly in the PR body.

**Reconciled the population myself, independently of both prior tables**, by reading core's own
dispatch source directly:
derived: `grep -n "GATES = \[" -A 15 core/hooks/pretooluse_dispatcher.py` (sha
`f0d9d54d79643d2386c4faf28a63e43d2bf12384`, untracked in this working tree —
`$CLAUDE_PLUGIN_ROOT_CORE` mount) this turn — result, `core/hooks/pretooluse_dispatcher.py:436-449`:
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
derived: 12 entries counted directly from the code fence immediately above. Cross-checked against
`core/hooks/hooks.json`'s `PreToolUse` array —
derived: `python3 -c "import json; print(json.load(open('core/hooks/hooks.json'))['hooks']['PreToolUse'])"`
(sha `f0d9d54d79643d2386c4faf28a63e43d2bf12384`, untracked in this working tree) this turn —
result: a single matcher `.*` entry routing to `pretooluse-dispatcher.sh`, no hooks.json-direct
core `PreToolUse` hook outside this `GATES` list — 12 is the full core `PreToolUse` population, not
merely the count PR #2872's table happened to claim.

**Diffed that population against PR #2872's table**
(`docs/issue-2705/reports/architecture-interface-contract-shape-952309f5.md:236-245`, untracked in
this working tree, sha `b3091bfb600251c26703913e27001098e1181002`, fetched and read on that
branch's own worktree this turn via
`git fetch origin issue-2705/architecture-interface-contract-shape-952309f5` then
`git worktree add`, both reverted and removed afterward, see "Why"):
```
Table rows naming core/hooks/ gates (242, 243, 245):     10 hooks
GATES list total (code fence above):                     12 hooks
Missing from the table:                                   2 hooks
```
derived: the two missing names, found by set-subtracting the table's 10 (`trailer-gate.sh`,
`handbook-trigger-gate.sh` at rows 242-243, plus `board-gate.sh`, `gh-guard.sh`,
`ordering-gate.sh`, `citation-gate.sh`, `facet-keyword-gate.sh`, `proposal-shape-gate.sh`,
`record-fields-gate.sh`, `survey-order-gate.sh` at row 245) from the 12-entry `GATES` list above —
`record-shape-gate.sh` and `approval-gate.sh`, exactly PR #3051's finding, confirmed independently
rather than trusted.

**Derived a verdict for each missing hook, live, against the actual source**:

- `core/hooks/record-shape-gate.sh:134` (sha `f0d9d54d79643d2386c4faf28a63e43d2bf12384`, untracked
  in this working tree) reads `git diff HEAD --numstat` (working-tree-vs-`HEAD`, not `--cached`)
  to decide whether a `docs/issue-<n>/reports/implementation.md` write is exempt from the full
  record-shape floor on a trivial diff —
  derived: `grep -nE '"(diff|status|ls-files)"|git diff|git status|git ls-files' core/hooks/record-shape-gate.sh`
  this turn — one hit, line 134, `git diff HEAD --numstat`. But it fires only on
  `tool in ("Write", "Edit", "MultiEdit")` —
  derived: `grep -n 'tool in (' core/hooks/record-shape-gate.sh` this turn — result: lines 184 and
  207, both `("Write", "Edit", "MultiEdit")`, never `"Bash"`. **Verdict: not applicable** — the
  read is real, but a single `Write`/`Edit` call carries its content directly in the payload; there
  is no bundled-shell-command staging step for a bundled `git add && git commit` to race, the same
  structural reason `core/hooks/record-fields-gate.sh` was already given in PR #2872's table
  (`architecture-interface-contract-shape-952309f5.md:245`, untracked in this working tree).
- `core/hooks/approval-gate.sh` (core's own file, distinct from `on-the-record/hooks/approval-
  gate.sh` already counted in PR #2872's 18-name `on-the-record/hooks/` row,
  `architecture-interface-contract-shape-952309f5.md:244`, untracked in this working tree) — its
  only `git` subprocess calls are `rev-parse --show-toplevel` (line 200),
  `remote get-url origin` (line 220), and `symbolic-ref --short` (line 234); none reads staged or
  working-tree diff state —
  derived: `grep -n '"git"' core/hooks/approval-gate.sh` (sha
  `f0d9d54d79643d2386c4faf28a63e43d2bf12384`) this turn — those three plus line 138, the
  `READ_ONLY_HEADS` tuple literal (`"diff", "stat", "file", "git", "cd"`) — a set of strings
  classifying the CURRENT Bash command's own head token (same non-oracle pattern PR #2872's table
  already ruled not applicable for `board-gate.sh`'s `GIT_READ_SUBCOMMANDS`,
  `architecture-interface-contract-shape-952309f5.md:245`, untracked in this working tree), not a
  query against prior staged state. **Verdict: not applicable** — it never reads
  `git diff`/`git status`/`git ls-files` at all.

## Why

**Attempted to commit this reconciliation directly onto PR #2872's own branch, as instructed, and
could not — this is a structural block, not a choice.** Full attempt log:

1. `git worktree add /tmp/pr2872-work origin/issue-2705/architecture-interface-contract-shape-952309f5`
   — succeeded; a clean checkout of that branch outside this session's own worktree.
2. Edited two new rows into the table in place (`Edit` tool, mid-table insertion, on the
   `architecture-interface-contract-shape-952309f5.md` copy inside `/tmp/pr2872-work` — untracked
   in this session's own working tree) — the file changed on disk in that worktree with no hook
   error at the time.
3. `cd /tmp/pr2872-work && git add ... && git commit -m ...` (the bundled shape this issue is
   itself about) — denied by `core/hooks/board-gate.sh:1399` (sha
   `f0d9d54d79643d2386c4faf28a63e43d2bf12384`): *"docs/issue-2705/reports/architecture-interface-
   contract-shape-952309f5.md [untracked in this session's own working tree] belongs to another
   skill. conformance-review-traceability-and-evidence+silent-failure-audit-6f24be9d writes only
   conformance-review-traceability-and-evidence+silent-failure-audit-6f24be9d.md,
   conformance-review-traceability-and-evidence+silent-failure-audit-6f24be9d/** — never a foreign
   record. (contract v3 s11)"*
4. Reverted the in-place edit (`git checkout -- .` in that `/tmp/pr2872-work` worktree, a
   directory-wide revert that never names the file in command text) — this one was not
   intercepted, restoring the file to `origin`'s state.
5. Re-attempted as a provably append-only write instead — `board-gate.sh`'s own foreign-record
   carve-out (`core/hooks/board-gate.sh:1361-1399`, contract v3 s11, issue-2241 stage 3) allows a
   session to append new content to a foreign-authored record, never alter its existing lines. Ran
   `cat >> architecture-interface-contract-shape-952309f5.md <<'EOF' ... EOF` (relative path,
   inside `/tmp/pr2872-work`, untracked in this session's own working tree; pure `>>` redirect, no
   truncation, addendum content only) — denied with the **identical** "belongs to another skill"
   message, not the different "authored by X, append-only" branch the carve-out would reach.

**Root cause, read from the gate's own source**: `board-gate.sh:1020-1034`'s `root_of()` resolves
the record's on-disk path via `CLAUDE_PROJECT_DIR` first (falling back to `git -C <payload cwd>
rev-parse --show-toplevel` only if unset) — not via any `cd` a bundled command performs, since the
`PreToolUse` hook evaluates the command's *text* before that text runs, so a `cd
/tmp/pr2872-work && ...` prefix cannot change which root the hook resolves against. `root` is
anchored to this session's own assigned worktree for every command this session issues, regardless
of what a bundled `cd`/`git -C` targets. Because the `architecture-interface-contract-shape-
952309f5.md` record is untracked in this session's own working tree (never materialized there at
all), `_record_text()` returns `None`, `_record_author()` returns `None`
(`core/hooks/board-gate.sh:1307-1316`), and the gate never reaches the append-only branch at
`board-gate.sh:1361-1394` at all — it falls straight to the unconditional foreign-record deny at
`board-gate.sh:1399`, for every write shape, not only the bundled one this issue is about.
derived: `echo "CLAUDE_PROJECT_DIR=$CLAUDE_PROJECT_DIR"` this turn — empty in this shell, and `pwd`
after every `cd`-prefixed command this turn shows this session's own worktree, confirming the
payload `cwd` the hook reads never reflects an in-command `cd`.

This is a deliberate per-skill write-set isolation boundary (contract v3 s11): a session's writes
under `docs/issue-<n>/` are confined to its own skill's record, and that confinement is anchored to
the session's own assigned project root — not bypassable by checking out a different branch into a
different worktree and writing there instead. Continuing to search for a shape that evades it
(e.g. hiding the target path from the command text, or spoofing `CLAUDE_PROJECT_DIR`) would be
circumventing a safety boundary rather than working within it, so this session stopped there,
reverted every change made in that worktree (`git checkout -- .`, confirmed clean via `git status
--short` and `git diff --stat`, both empty), removed the worktree (`git worktree remove
/tmp/pr2872-work`), and deleted the local tracking branch it created
(`git branch -d issue-2705/architecture-interface-contract-shape-952309f5`) — no trace of the
attempt remains outside this record.

**What this record delivers instead**: the fully reconciled and live-verified content of the two
missing rows (in "What was done" above), ready for whoever holds write access to PR #2872's own
branch/record — a human maintainer, or a session whose `CLAUDE_SKILL` and `CLAUDE_PROJECT_DIR`
actually match that record's `author:` field — to apply verbatim to that record's criterion-3
table (after row 245, before its `gate-registration-post-guard.sh` row at 246), in the same
four-column shape as the existing rows there. This satisfies the substance of the assigned task
(derive the full population, reconcile it against the table, verdict + command for each missing
hook) without violating this session's own write-set boundary to do it.

## What did not work

The direct-commit-onto-PR-#2872's-branch instruction — see "Why" above for the full attempt log
and root cause. Not a design failure of this session's approach; a structural boundary
(`core/hooks/board-gate.sh` contract v3 s11) that holds regardless of shape once the target record
is untracked in this session's own `CLAUDE_PROJECT_DIR`.

## Upstream basis

- PR #2872, branch `issue-2705/architecture-interface-contract-shape-952309f5`, its record's
  criterion-3 table at lines 236-253 (untracked in this session's own working tree — fetched and
  read via `git fetch`/`git worktree add` this turn, then reverted and removed), sha
  `b3091bfb600251c26703913e27001098e1181002`.
- PR #3051, `gh pr view 3051 --repo tokenmaxxxer/on-the-record`, read in full this turn (criterion
  3 graded Surface; both gaps named); untracked in this session's own working tree, PR
  open/unmerged, sha `1f1796552de3fae8a90113e29792f48003303f54`.
- Issue #2705 body and acceptance criterion 3's `population:` line ("all `PreToolUse` hooks in
  `on-the-record/hooks/` and core's `hooks/`"), `gh issue view 2705`, read in full this turn.
- `tokenmaxxxer-core` plugin checkout (untracked in this session's own working tree —
  `$CLAUDE_PLUGIN_ROOT_CORE` mount): `core/hooks/pretooluse_dispatcher.py:436-449` (`GATES`
  list), `core/hooks/record-shape-gate.sh:134,184,207`,
  `core/hooks/approval-gate.sh:137-138,200,220,234`,
  `core/hooks/board-gate.sh:1020-1034,1307-1316,1322-1399`, `core/hooks/hooks.json`, all at sha
  `f0d9d54d79643d2386c4faf28a63e43d2bf12384`.

## Open findings

None beyond the two rows delivered above and the write-set boundary documented in "Why". Core
`PreToolUse` population fully accounted for:
```
GATES list entries (What was done, above):                 12
PR #2872 table rows 242, 243, 245 (hooks named there):    - 10
This record's two added rows:                             -  2
Remainder:                                                    0
```
derived: the arithmetic in the code fence directly above, both operands cited to their own
sections of this same record ("What was done"). No further gap found on that basis.

## Next steps

None from this session — `loop_state` is set to its terminal value.
canonical: this record's own "What was done" section, written and executed this turn, carries the
exact, ready-to-apply row content in the shape PR #2872's table already uses. Applying it to that
record itself requires a session or human with write access to it (see "Why").

skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; used to cite every
verdict above with file:line-range plus the exact commit/checkout sha read (rule 1), one
traceability link per contributing file rather than a bundled reference (rule 2: PR #2872's table,
PR #3051's finding, and core's own dispatcher source are cited separately), backward-traced
criterion 3's `population:` line in the issue body before checking either hook's implementation
(rule 3), and pinned the core plugin's checkout sha since its hooks are a moving target a later
reader could otherwise re-check against a different version (rule 5, in place of a versioned
spec).
skill-verdict: silent-failure-audit — not-applicable: no AI-written error-handling code (try/catch,
Promise rejection, error callback, result type) was authored or reviewed this turn; this task was a
gate-population enumeration and reconciliation, not an error-path audit.
other mounted skills: not triggered
