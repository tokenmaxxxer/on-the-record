# Current-state survey — issue #688

## Write surface

`on-the-record/hooks/delegated-judgment-gate.sh`, function `depth_match`
(line ~365-380):

```python
corpus_dir = TARGET / "docs" / "product"
if not corpus_dir.is_dir():
    return False
entries = list(corpus_dir.glob("*.md"))
```

This is the sole read of the retired product-docs corpus (formerly a flat
docs/product directory, no longer present on disk). `issue` (int, from
the `issue-<n>/<role>` branch match at line 343) is already in scope at
the point `depth_match` is called, and is the same variable
`TRIAGE_DECISIONS_DIR` (line 555) and `decisions_dir` (line 660) already
use to build the issue-scoped decisions path.

## Confirmed new location

Per `docs/specs/generated-paths.md` (issue #684 table) and
`product-capture-stopgate.sh` line 163 (`rel = os.path.join("docs",
f"issue-{issue_n}", "product", f"{cat}.md")`), the writer now targets
the issue-scoped product directory (`docs/issue-<n>/product/<cat>.md`).
The reader must match the same pattern, substituting the run's own
`issue` variable for `<n>`.

## Other stale references in the same file

- Docstring lines 6, 14 (flat product corpus mention) — comments, not
  code; update for accuracy since they describe this exact mechanism.
- Line 667: `"derivation_source: docs/product corpus match"` — a citation
  string written into the audit-trail body this hook posts. Same fix
  applies since it materially describes the corpus location the finding
  came from.

## Test surface

`on-the-record/hooks/test_delegated_judgment_gate.py`:
- helper `_product_corpus` (line 91-95) writes under a flat product
  subdirectory — must move under the issue-scoped equivalent (the
  fixture's branch is always `issue-42/gate`, see `_init_target` line 60,
  so the target issue number is always 42).
- `t_escalate_on_empty_corpus` (line 113) already covers the empty-state
  case (no corpus dir at all) — this continues to hold unchanged, since it
  exercises `depth_match` returning `False` when `corpus_dir.is_dir()` is
  false, which is location-independent.
- No existing test asserts the retired flat path is no longer referenced
  by the script text itself (acceptance criterion 2). The generated-paths
  test module's existing table only classified write calls, not this
  file's read-side reference.

## Skip condition

This is a single stale-path correction with no open design choice — the
new location is already fixed by #684's landed decision
(generated-paths spec) and the writer-side pattern already implemented in
`product-capture-stopgate.sh`. Scout-directive's pure bugfix skip
condition applies: there is no exemplar field to sweep, only one correct
target path to match against the already-landed writer.
