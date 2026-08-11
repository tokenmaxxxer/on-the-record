---
proposal: docs/issue-839/proposals/generated-paths-row-fix-and-guard-extension.md
---

# Hunt record — generated-paths-row-fix-and-guard-extension

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned classification-vs-write-call check can never catch a genuinely in-tree, non-issue-scoped ("collision-risk") hook that is mislabeled `out-of-tree` in its `generated-paths.md` row, because the check (mirroring `gates/test_generated_paths.py::check()` exactly, as the proposal specifies) only rejects the literal string `collision-risk`, a value outside `{out-of-tree, issue-scoped}`, or `issue-scoped` with no placeholder — it never verifies that an `out-of-tree` claim is actually true.
Kind: design-error
Seed: docs/issue-839/proposals/generated-paths-row-fix-and-guard-extension.md ("What will be done", item 2); underlying logic ported from gates/test_generated_paths.py::check()
cap_seconds: (not specified by dispatcher; used ~15 min)
tier: default
diff_stat_lines: 538 insertions, 2 files (docs/-only)
started_at: 2026-08-11T20:15:00Z
ended_at: 2026-08-11T20:40:00Z

### Reproduce

```bash
mkdir -p /tmp/otr_repro/docs/specs /tmp/otr_repro/on-the-record/hooks

cat > /tmp/otr_repro/on-the-record/hooks/evil-writer.sh <<'SH'
#!/usr/bin/env bash
# Writes into the TARGET REPO's own worktree (collision-risk): no
# issue-<n> placeholder anywhere, path is a plain "$1/..." join.
set -euo pipefail
mkdir -p "$1/some-shared-state-dir"
SH
chmod +x /tmp/otr_repro/on-the-record/hooks/evil-writer.sh

cat > /tmp/otr_repro/docs/specs/generated-paths.md <<'MD'
# Generated write-path disjointness (issue #684)

| mechanism | classification | verdict |
|---|---|---|
| `evil-writer.sh` | out-of-tree | safe — writes into the shared plugin checkout, not the target repo |
MD

python3 - <<'PY'
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("tgp", "gates/test_generated_paths.py")
tgp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tgp)
tgp.ROOT = Path("/tmp/otr_repro")
tgp.SPEC = tgp.ROOT / "docs" / "specs" / "generated-paths.md"
tgp.HOOKS_DIR = tgp.ROOT / "on-the-record" / "hooks"
print("problems found:", tgp.check())
print("hooks_with_write_calls:", tgp._hooks_with_write_calls())
PY
```

Run from repo root (`gates/test_generated_paths.py` imported unmodified,
only `ROOT`/`SPEC`/`HOOKS_DIR` repointed at the scratch fixture — the
exact derivation function, `check()`, that the proposal's item 2 commits
to porting into the guard's Python heredoc verbatim: "duplicate
`_WRITE_CALL_RE` and `_ISSUE_PLACEHOLDER_RE`... deny the commit if: ...
has a write-call match and is recorded `collision-risk` or a value
outside `{out-of-tree, issue-scoped}`; or is recorded `issue-scoped` with
no issue-placeholder match").

### Observed

```
problems found: []
hooks_with_write_calls: {'evil-writer.sh'}
```

`evil-writer.sh` genuinely has a write call (`mkdir -p "$1/..."`, no
issue-`<n>` placeholder, no shared-checkout/`$TMPDIR` indirection — an
actual `collision-risk` generator by issue-684's own definition: "a
generator [that is] neither of the above [out-of-tree or issue-scoped]").
Its row claims `out-of-tree`. `check()` — the exact logic the proposal's
item 2 ports inline into `gate-registration-guard.sh` — reports zero
problems. A commit adding this hook with this row would sail through the
extended guard exactly as specified.

### Expected

A commit that newly stages a hook whose own source writes into an
in-tree, non-issue-scoped path, recorded `out-of-tree` in
`generated-paths.md`, should be denied (or at minimum flagged) by a check
whose entire stated purpose (proposal Rationale, Decision 2: "the exact
failure mode #839 reports — row exists, classification wrong — uncaught
at commit time") is to catch exactly this: a row that exists but is
classified wrong. Instead the derivation only ever positively confirms
membership in `{out-of-tree, issue-scoped}` plus the `issue-scoped`
placeholder sub-check; it has no way to falsify an `out-of-tree` claim
for a hook that does write in-tree, so this specific misclassification
(arguably the most dangerous one — it is exactly what issue-684's
disjointness property exists to prevent) still lands undetected once the
extension is built precisely as the proposal's item 2 specifies. This is
inherited, not novel to the port — `gates/test_generated_paths.py::check()`
itself has the same blind spot today — but the proposal explicitly
frames item 2 as closing "the exact failure mode #839 reports" at commit
time, and this bypass shows that framing overstates what the ported logic
actually catches.
