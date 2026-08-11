---
proposal: docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md
---

# Hunt record — align-post-pr-record-guidance-with-gates

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the proposal's chosen fix (shape 2: warrant interpolates "the calling role's record directory" from the role's own rulebook) is built on a directory that does not exist: every rulebook declares its RECORD path as a flat `<role>.md` file, not a directory, so naive interpolation of `<record-dir>/hunt-<slug>.md` yields a broken path with a `.md` file as a path segment.
Kind: design-error
Seed: docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md ("What will be done" bullet 1: "replace the hardcoded hunt-record path text with a role-derived directory — the directive asks the calling role for its record directory ... and writes the hunt record as `<record-dir>/hunt-<slug>.md`")
cap_seconds: 120
tier: default
diff_stat_lines: 21-200
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:02:00Z

### Reproduce
```
grep -n '^RECORD:' docs/issue-170/_assets/rulebook-skeleton/*/*/hooks/directive.sh \
                    docs/issue-167/_assets/rulebook-skeleton/*/*/hooks/directive.sh
```
Every match, e.g. for `architecture`:
```
architecture/architecture/hooks/directive.sh:28:RECORD: docs/issue-<n>/reports/architecture.md, phase-gated per contract v3 s19
```
Apply the proposal's own literal template, "`<record-dir>/hunt-<slug>.md`", by substituting the value the rulebook actually declares as its record path (`docs/issue-<n>/reports/architecture.md`) for `<record-dir>`:
```
docs/issue-<n>/reports/architecture.md/hunt-<slug>.md
```
This is not a value `role_scope()` in `on-the-record/gates/gates.py` accepts as in-scope in the way the proposal implies — it treats a `.md` file as a directory component, which no filesystem write can satisfy as a normal path (a regular file named `architecture.md` cannot also be a directory containing `hunt-<slug>.md`), and it does not match `_always_writable`'s `docs/issue-*/reports/{role}.md` glob (extra path segment) even though it happens to match `docs/issue-*/reports/{role}/**` only by accident of the glob covering any nested path under a literal `{role}` directory that here is being confused with the `{role}.md` file.

### Observed
The proposal states, as the chosen (and only surviving) design: "the directive asks the calling role for its record directory (already known to every rulebook that owns a record path)". No rulebook directive.sh in this repo's skeleton corpus declares a record *directory* — all 34 checked declare a record *file* (`RECORD: docs/issue-<n>/reports/<role>.md`). The proposal's own Rationale section, arguing against option (1), claims option (2) avoids "retyping" the path, but it silently assumes a `record directory` fact that the surveyed rulebooks do not carry — it would have to be invented anew in phase 2, contradicting the proposal's claim that this fact is "already known to every rulebook."

### Expected
The proposal should either (a) name the actual derivation it means — e.g. strip the trailing `.md` and role-name segment from the declared `RECORD:` file path to construct a sibling directory, and say so explicitly, since `role_scope`'s `_always_writable` already grants `docs/issue-*/reports/{role}/**` as a distinct always-writable glob independent of the `{role}.md` file glob — or (b) acknowledge that "record directory" is not a fact any rulebook currently states, so phase 2 must add that declaration rather than treating it as already derivable.
