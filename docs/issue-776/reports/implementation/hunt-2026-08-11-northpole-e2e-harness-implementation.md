---
proposal: docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-implementation.md
---

# Hunt record — northpole-e2e-harness-implementation

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — the write set omits a `docs/handbooks/*.md` touch that contract §21 requires for the `pyproject.toml` commit; `harness/README.md` does not satisfy the gate.
Kind: design-error
Seed: docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-implementation.md (lines 43-47, "Output layout" constraint)
cap_seconds: 120
tier: default
diff_stat_lines: ~230 (2 new files, docs-only)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:20:00Z

### Reproduce

```
grep -n "operational-surface file needs a docs/handbooks" docs/issue-503/reports/implementation.md
grep -n "contract §21" docs/issue-245/reports/implementation.md docs/issue-460/reports/implementation.md
find . -iname "handbook-trigger-gate.sh" | head -1 | xargs grep -n "docs/handbooks"
```

### Observed

Every real precedent in this repo where contract §21's handbook-pairing
fired required (and was satisfied only by) a touch under
`docs/handbooks/<component>.md`:

- `docs/issue-503/reports/implementation.md:135-136`: "`.claude/settings.json`
  is an operational-surface file change (falls under contract v3's
  'operational-surface file needs a docs/handbooks/ touch in the same
  commit' rule)".
- `docs/issue-245/reports/implementation.md:188-196`: a commit was
  "mechanically refused by `handbook-trigger-gate.sh`: any commit
  touching a `.github/workflows/*.yml` operational surface must touch a
  `docs/handbooks/<component>.md` in the same commit (contract §21)" —
  satisfied only by editing `docs/handbooks/operations.md`.
- `docs/issue-460/reports/implementation.md:60-70`: same gate, same fix
  target — `docs/handbooks/operations.md` was "not in the approved
  proposal's frozen write set" and had to be added to unblock the commit.
- The gate's own canonical definition (skeleton copy, e.g.
  `docs/issue-167/_assets/.../hooks/handbook-trigger-gate.sh`): "the
  same commit must also touch docs/handbooks/*.md" — the path is
  hard-coded to the `docs/handbooks/` bucket, not to any
  README/handbook-shaped doc elsewhere in the tree.

None of these instances, and no other grep hit for "operational-surface"
+ "handbook" across the repo's history, ever treats a component-local
`README.md` as satisfying the pairing. The implementation proposal's own
Output-layout constraint (lines 43-47) asserts the opposite: that
`harness/README.md` — a file under `harness/`, not `docs/handbooks/` —
"satisf[ies] contract §21's pairing rule" for the `harness/fixture-target/pyproject.toml`
commit. Building exactly the proposal's listed write set (which contains
no `docs/handbooks/*.md` entry at all) will reproduce the exact refusal
pattern documented in issue-245/issue-460: if/when this repo's own
`handbook-trigger-gate.sh` instance is live for commits touching
`harness/fixture-target/pyproject.toml`, the commit is refused, and step 2
cannot land without adding a `docs/handbooks/<component>.md` edit — a
path the proposal's frozen `files:` list does not include.

### Expected

The proposal's write set should include a `docs/handbooks/*.md` edit
(e.g. `docs/handbooks/harness.md` or a new subsection in an existing
handbook) alongside `harness/fixture-target/pyproject.toml`, matching
every other precedent for satisfying contract §21 in this repo — not
substitute `harness/README.md`, which no prior instance of the rule
accepts as the "handbook" half of the pairing.
