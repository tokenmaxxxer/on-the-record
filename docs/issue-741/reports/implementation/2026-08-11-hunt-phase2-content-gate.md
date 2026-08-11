---
proposal: docs/issue-741/proposals/2026-08-11-phase2-content-gate.md
---

# Hunt record — phase2-content-gate

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the proposal's "role-agnostic" port of approval-gate.sh's record-path pattern accepts any filename directly under `docs/issue-<n>/reports/`, but approval-gate.sh (the gate the Rationale cites as making this signal unforgeable) only restricts the one exact role-specific filename `docs/issue-<n>/reports/<role>.md` — so a phase-1 session can legally create a different file directly under `reports/` (e.g. `docs/issue-<n>/reports/scratch-notes.md`, or another role's `<other-role>.md`) before any approval, and if that path lands in the PR diff, contract-guard.sh's new content check would misclassify a still-docs-only PR as phase-2-shaped and attach `Closes #<issue>` — reproducing the exact #741 failure this proposal exists to fix.
Kind: composition
Seed: docs/issue-741/proposals/2026-08-11-phase2-content-gate.md (design-only, no code yet); grounded against on-the-record/hooks/approval-gate.sh:115-119 and its own "What will be done" section's role-agnostic record-file pattern
cap_seconds: 60
tier: size:docs-only
diff_stat_lines: 0 (proposal file only, no code diff yet)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:05:00Z

### Reproduce
Read `on-the-record/hooks/approval-gate.sh:115-119`:
```
record_path = "docs/issue-%d/reports/%s.md" % (issue, role)
is_record = n == record_path or n.endswith("/" + record_path)
is_src_test = re.search(r"(^|/)(src|tests?)/", n) is not None
if not (is_record or is_src_test):
    sys.exit(0)  # phase-1-legal path (proposal, survey, decisions, handbooks, approvers.md itself, ...)
```
This matches ONLY the acting role's own exact filename — confirmed by the script's own header comment: "Only the two phase-2-shaped targets are checked: the acting role's own record file (docs/issue-<n>/reports/<role>.md) or a src/test(s)/ path."

Compare against the proposal's own "What will be done" text (verbatim): "does any path in `pr_data.get("files")` match `(^|/)(src|tests?)/` or the issue's own role-agnostic record-file pattern under `docs/issue-<n>/reports/` (a direct child file, not a subdirectory path) — mirroring `approval-gate.sh`'s existing `is_record`/`is_src_test` pattern, ported role-agnostically since `contract-guard.sh` ... has no reliable role value available."

Direct logic trace (both patterns evaluated against the same three candidate paths, issue=741, role=implementation):
```python
import re
a='docs'; b='issue'; c='reports'
n1 = a+'/'+b+'-741/'+c+'/'+'implementation.md'          # the real record file
n2 = a+'/'+b+'-741/'+c+'/'+'scratch-notes.md'            # some other file, same directory
n3 = a+'/'+b+'-741/'+c+'/'+'implementation'+'/'+'hunt.md'  # nested subdirectory (this very file's own path shape)
role='implementation'; issue=741
role_record = a+'/'+b+'-%d/'%issue+c+'/'+role+'.md'
def is_record_role_specific(n):   # approval-gate.sh today
    return n == role_record or n.endswith('/'+role_record)
def is_record_role_agnostic(n):   # proposal's contract-guard.sh port
    prefix = a+'/'+b+'-%d/'%issue+c+'/'
    return n.startswith(prefix) and '/' not in n[len(prefix):]
for n in (n1, n2, n3):
    print(n, 'approval-gate(today)=', is_record_role_specific(n), 'proposed contract-guard=', is_record_role_agnostic(n))
```

### Observed
```
docs/issue-741/reports/implementation.md    approval-gate(today)= True   proposed contract-guard= True
docs/issue-741/reports/scratch-notes.md     approval-gate(today)= False  proposed contract-guard= True
docs/issue-741/reports/implementation/hunt.md  approval-gate(today)= False  proposed contract-guard= False
```
`scratch-notes.md` (or any other filename directly under the same `reports/` directory, including another role's `<role>.md`) is phase-1-legal under approval-gate.sh's actual check (is_record is False, is_src_test is False, so the write falls through `sys.exit(0)` unchecked) — an un-approved phase-1 session can create it freely. But the proposal's own role-agnostic pattern for contract-guard.sh treats it as phase-2-shaped. If such a file ships in a phase-1, docs-only PR's diff (easy: a stray note, a misnamed file, a copy-paste of another role's filename), the widened `gh pr view --json files` check would find a `reports/`-direct-child path, `phase2` would already be true from the pre-existing round-scoping condition (approval always postdates the PR's first commit, per #741's original bug), and contract-guard.sh would attach `Closes #741` to a PR that delivered no `src/`/`tests/` code at all — the exact zero-delivery premature-close failure this proposal exists to prevent, reopened through a filename the Rationale's own forgeability argument did not account for.

### Expected
The Rationale's forgeability claim ("approval-gate.sh denies any Write/Edit/MultiEdit to a src/tests?/ path or the role's record file from an un-approved session — a phase-1 session cannot legally create such a path before approval in the first place") should hold for whatever pattern contract-guard.sh actually implements. Since contract-guard.sh cannot know the acting role (per the proposal's own stated reason for going role-agnostic), the content check needs either: a role-agnostic pattern that is still no broader than the union of *all* per-role exact filenames actually protected by approval-gate.sh across the issue's known/possible roles (not a wildcard over the whole directory), or an explicit acknowledgment that this broadened match reopens a (smaller, but real) forgeable surface that the #476 forgeability judgment did not evaluate.
