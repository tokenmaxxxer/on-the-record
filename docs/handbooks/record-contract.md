# Record contract: lease, author identity, record-kind (stage 1)

Issue #2241 (role-axis retirement) decomposes what the `role` string does
today into four independent concepts (`docs/decisions/2026-08-25-retire-
role-axis-staging.md`, Option A). Stage 1
(`docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-
kind.md`) lands three of them — issue-scoped lease, author identity,
record-kind — while every role-keyed consumer keeps working unchanged.
Nothing depends on these yet; this stage only proves they exist and
behave correctly in isolation.

## Issue-scoped lease

`roster.py`'s existing TTL lease (issue #2101: `lease_expires_at`,
`lease_progress`, `lease_flat_renewals`, the detector-free requeue path)
already keys its roster entries as `issue-<n>/<second-half>`. Stage 1
names that second half explicitly — `roster.lease_key(issue,
disambiguator)` — and generalizes it to accept any session-scoped
disambiguator string, not only a role name. Lease renewal, expiry, and
requeue never inspect the key's internal structure; they only compare it
as an opaque dict key, so this is a naming/documentation generalization
of already-correct behavior, not a mechanism change. Every existing
caller still passes its role string through unchanged — same key shape,
byte-identical lease behavior.

## Author identity

Every record a session writes now carries an `author:` frontmatter
line — the session's stable identity, populated once when the record's
skeleton is first written (`spawn.py::write_record_skeleton`) and never
rewritten afterward. `write_record_skeleton` already refuses to touch a
record file that exists, so a respawn into the same workspace cannot
clobber a prior session's `author:` line — the field is append-only by
construction, not by a separate enforcement check.

`author:` is deliberately a separate field from the lease key: a lease
is TTL-scoped and expected to expire and be reclaimed, while a record's
authorship must stay permanent for the audit trail to mean anything
(`docs/decisions/2026-08-25-retire-role-axis-staging.md` Option D
explains why merging the two into one field was rejected).

Stage 1 keeps roles fully in place, so `author:` is populated with the
writing role — the only session-scoped identity available at this
stage. A later stage may widen what populates it once a non-role-shaped
identity axis exists; `spawn.py::_stamp_additive_record_fields` is the
single call site that widening touches.

## Record-kind

`docs/specs/record-kind-vocabulary.md` formalizes the `kind:` field
already used ad hoc across the record corpus into a closed vocabulary.
`gates/record_lint.py::record_kind_vocabulary_check` flags a `kind:`
value outside that vocabulary — **advisory only** at this stage, never
wired into `lint_record()`'s blocking aggregation. A later stage (3 or
5) may promote it once record-kind becomes load-bearing for observer
verification (preventing the same actor from providing both an artifact
and its independent check).

## Supersession

A correcting session can never write into or delete the record it is
correcting — `board-gate.sh`'s write-set isolation (contract v3 s11)
resolves ownership from the *writing* session's own project root, not
from the path being written, so no write shape (in-place edit, revert,
append-only) reaches a peer session's record (issue #3050 root-cause
comment). When a correction round is instructed to fix a prior session's
artifact, it writes only its own record and adds a `supersedes:`
frontmatter line naming the record it corrects:

```
---
supersedes: docs/issue-9101/reports/coding.md  # three fabricated figures
...
---
```

The reason travels as a plain-text comment on the same line, visible to a
reader without parsing YAML. `supersession.py`'s `resolve_authoritative()`
is the reader-side half: given every record's raw content (no git, no PR
body, no issue comment), it decides which paths are authoritative from
tree content alone — the target of a `supersedes:` line is superseded,
the correcting record is authoritative, a dangling target or two records
both claiming to supersede the same one fails closed (neither the target
nor either corrector counts as authoritative).

`supersedes:` only replaces a whole artifact. It has no shape for
correcting one section inside a larger foreign record without marking
that entire record non-authoritative — a correction confined to one
section of a foreign record cannot use this field; see
`docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4.md`
("Partial supersession" section) for what such a correction should do
instead.

## What stays additive

Per the stage-1 proposal's Constraints: `author:` and `kind:` are never
required, and no gate refuses a write for their absence — every record
written before this stage stays valid exactly as it is. Nothing in this
repo yet reads `author:` or the generalized lease-key shape to make a
decision; stages 3-6 are what wire consumers onto these fields, each
against its own gate.
