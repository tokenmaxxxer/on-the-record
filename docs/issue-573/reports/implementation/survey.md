# Current-state survey — issue #573 implementation (phase 1)

Skip condition: neither applies (this is not a pure bugfix and the merged
architecture.md leaves several implementation choices open — module
boundaries, gh-matching pattern, test layout). Scouting is skipped: the
spec (architecture.md, PR #581, 12 sections) already fixes every product
direction — schema shape, gate composition, audit-record fields,
degradation rule, panel synthesis rule — leaving only mechanical porting
decisions with no external best-in-class comparison to make (this is a
deployed-hook implementation task, not a product surface).

## Write set this proposal covers (per architecture.md's "Files" section)

- `roles/*.json` — add `judgment_axes` on the roles that plausibly own an
  axis. architecture.md defers *which* roles own which axis to "each
  role's own domain" — out of scope for a single implementation pass to
  invent for all 30 roles. This proposal seeds `judgment_axes` only on
  the roles this issue's own gate machinery needs to exercise its tests
  (architecture, security-threat-model) and leaves the rest for
  follow-up per-role decisions, matching architecture.md's own framing.
- `roles/specs/architecture.spec.json`, `roles/specs/security-threat-model.spec.json`
  — add `axis_evaluation` (ref[], optional) to `required_fields`, plus
  the `reference_resolution` clause (section 1) and the section 6
  conditional-finding clause.
- `gates/role_spec_shape.py` — extend its check/reference-resolution
  functions to accept `judgment_axes` on `roles/*.json` and the
  `axis_evaluation` shape (including the conditional finding-object
  presence, section 6) on `roles/specs/*.spec.json`.
- new deployed hook under `on-the-record/hooks/` implementing
  delegated-judgment-gate, PreToolUse/Bash, mirroring `impact-guard.sh`'s
  structure exactly: `_checkout_resolve()` verbatim copy,
  `TARGET_REPO="$(pwd -P)"`, Python heredoc importing
  `gates.risk_report`'s existing axis classifier plus a new small
  depth-axis matcher against docs/product/*.md.
- `on-the-record/hooks/hooks.json` — register the new hook under
  `PreToolUse`/`Bash`. Architecture's own hunt already flagged (in its
  own hunt record under docs/reports/) that omitting this registration
  silently no-ops the gate — confirmed still true by reading the current
  hooks.json (`impact-guard.sh` sits in the same `PreToolUse`/`Bash`
  matcher block, so the new hook is a one-line addition to that block's
  hooks array).
- one new small test file following the `gates/test_role_spec_shape_batch*.py`
  numbered-batch convention, for the `judgment_axes`/`axis_evaluation`
  shape additions (a new batch file, not a growth of an existing large
  batch file).
- a new colocated test file under `on-the-record/hooks/` for the new
  gate, following that directory's existing `test_impact_guard.py`
  convention — one test per firing event (auto-approve, auto-reject,
  escalate-on-no-quorum, escalate-on-empty-corpus/degradation,
  remediation-routed, loop-bound exhausted, repeat-contradiction) and one
  per synthesis branch (approve / reject / escalate, from section 9's
  three composition clauses).
- decision-record files under docs/issue-573/decisions/ with an
  auto-<sequence> or remediation-<sequence> naming pattern — written by
  the gate at runtime, not hand-authored; this proposal's own write set
  only needs to produce the writer, not pre-populate example records.
  Tests exercise the writer against a temp target repo, per
  impact-guard.sh's own test pattern (checked below).

## Existing patterns confirmed by reading, not assumed

- `on-the-record/hooks/impact-guard.sh` (its opening section) — the
  `_checkout_resolve()` / `TARGET_REPO="$(pwd -P)"` / kill-switch
  (`ORCHESTRATE_OFF`) / Python-heredoc pattern this new gate must mirror
  verbatim (architecture.md section 2 names this explicitly; confirmed
  by reading the file).
- `gates/risk_report.py` — its axis classifier (four-axis structural
  impact) exists, is fail-closed (unparseable write-set escalates to the
  max grade), and is already the import target of `impact-guard.sh`. No
  modification needed; the new gate imports it the same way.
- `roles/architecture.json` / `roles/specs/architecture.spec.json` — the
  existing `write_scope`, `record_fields.loop_state`, and the spec's
  `required_fields`/`reference_resolution`/`recomputation`/`write_scope`/
  `loop_state`/`use_when` top-level shape are exactly what
  `gates/role_spec_shape.py`'s top-level-required-keys check enforces —
  confirms architecture.md's claim that `axis_evaluation` can reuse this
  mechanism verbatim with no new file format.
- `gates/role_spec_shape.py`'s field-type set already includes `ref[]` —
  `axis_evaluation`'s declared type is already a legal value; no
  enum-set change needed there.
- `on-the-record/hooks/role-spec-reference-guard.sh` calls into
  `gates/role_spec_shape.py`'s reference-resolution check — the existing
  reference-walking mechanism section 1 of architecture.md says the new
  `axis_evaluation` entries reuse; confirmed present and already wired
  into hooks.json, so `axis_evaluation`'s reference checks ride the
  existing enforcement path with a shape-checker extension only, no new
  hook needed for reference resolution itself (the *gate*'s own
  AND/composition logic is the new hook; reference resolution of
  individual `axis_evaluation` entries is not).
- hooks.json's `PreToolUse`/`Bash` matcher block already lists
  `contract-guard.sh`, `pr-preflight.sh`, `claim-scan-preflight.sh`,
  `spec-index-preflight.sh`, `impact-guard.sh` in sequence — the new
  hook is appended to this same array.

## Alternatives considered (feeds the proposal's Rationale)

- Single combined test file vs. one test file per firing
  event/synthesis branch: the repo's own numbered-batch test convention
  already splits by batch rather than growing one file indefinitely; a
  single file covering all ~10 event/branch cases for the new gate is
  still small enough (an impact-guard.sh-sized hook, per architecture.md's
  own effort framing) to stay in one file without exceeding what the
  existing impact-guard test file already does — checked by reading that
  file's size class before deciding.
- Extending gates/role_spec_shape.py in place vs. a new dedicated shape
  module: architecture.md section 1 explicitly asks for "same validator,
  not a new checker" — confirmed compatible by reading the existing
  module's top-level-required-keys/field-type constants, which need no
  redesign, only additive checks.
