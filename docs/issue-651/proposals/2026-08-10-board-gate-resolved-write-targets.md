---
status: proposed
files:
  - docs/issue-651/reports/implementation/survey.md
  - docs/issue-651/proposals/2026-08-10-board-gate-resolved-write-targets.md
  - docs/issue-651/reports/implementation.md
---

## Request

Issue #651 (bonus finding from the #628 hunt): `board-gate.sh` decides
write-target board membership by finding the literal substring "docs/"
anywhere in a candidate token, never checking whether that token, resolved
as an actual filesystem path, falls under the repository root the gate
itself already resolves. This produces spurious refusals against
out-of-repo paths that merely contain an unrelated docs-shaped component
(e.g. a `/tmp/...` fixture path), and the ask is to resolve actual write
targets against the repo root where the tool payload provides them, while
keeping the existing text-scoped handling honest where a target cannot be
resolved (a relative Bash token with no full shell cwd model available).

## Constraints

- Real enforcement must not weaken: a genuine foreign-record write inside
  the repo must still refuse, and a real Bash write that resolves under the
  board must still be caught — the fix narrows false positives, it does not
  loosen the ownership/layout/branch checks themselves.
- Both directions of the acceptance criterion must hold together: commands
  that merely mention a board-shaped path in commentary text pass, AND
  actual foreign-record writes still refuse — a fix that only widens
  `allow()` risks breaking the second half.
- The target file is not in this repo. It lives in the separate
  `tokenmaxxxer/tokenmaxxxer-core` repository, confirmed present and
  readable but not writable from this session's sandbox (repeating the
  exact blocker issue-40's coding record already documented). This
  proposal's own write set is therefore confined to what this session can
  actually deliver: the phase-1 research and proposal, plus this session's
  own phase-2 record documenting the blocker, matching issue-40's
  precedent rather than discovering it mid-build.

## Rationale

Two approaches were considered for where to add the root check.

Rejected: resolve every candidate token (absolute or relative) into a full
path using a hand-rolled shell cwd tracker, so relative Bash tokens are
also root-checked. Rejected because the gate has no reliable model of the
subshell/pipeline cwd a Bash command actually executes under — the same
class of complexity the gate's own comments already flag as an accepted,
deliberate limitation (sticky `cd`-tail tracking exists exactly because a
full relative-path resolver was "scouted and rejected" once already,
per the gate's own in-file comment). Reproducing that already-rejected
resolver here would silently reintroduce the class of bug it was rejected
to avoid, for a fix whose own issue only asks for text-matching to be
"scoped honestly," not made fully general.

Chosen approach: root-check only tokens the gate can already resolve
unambiguously — an absolute-path candidate (from a Write/Edit tool
payload's `file_path`, or an absolute Bash redirect target) is normalized
and compared against the already-resolved repo root before being counted
as a board hit; a relative Bash token keeps today's substring-scoped
handling exactly as-is, since the gate cannot honestly resolve it without
the rejected full-cwd-model approach. This directly fixes the confirmed
repro (an absolute out-of-repo path) without touching the relative-token
path the ownership/layout/branch checks depend on, and needs no new
shell-cwd machinery.

## What will be done

In `core/hooks/board-gate.sh`, in the Python program's candidate/hit
pipeline:

1. Move the `root = root_of()` resolution earlier, immediately after
   `candidates` is built (currently it runs after the hit list is already
   computed).
2. In the loop building `hits` from `candidates`, before accepting a
   candidate's docs-relative tail: if the candidate is an absolute path
   (starts with `/`), normalize it and check whether it lies under `root`
   (or `root` is unavailable, in which case fail closed — deny rather than
   silently allow, consistent with the gate's existing fail-closed
   posture for unresolvable state). If it does not lie under `root`,
   discard the candidate — it never becomes a hit, no matter what
   substring it contains.
3. A relative-path candidate is left untouched: it keeps going through the
   existing `_docs_relative_tail()` substring path exactly as it does
   today.
4. Add regression cases to `core/hooks/tests/run-board-gate-tests.sh`:
   an absolute out-of-repo path containing an unrelated docs-shaped
   component is allowed; the existing foreign-record-write and
   mention-only-text cases are re-asserted unchanged as fixed regression
   anchors (both already pass today and must keep passing).
5. Because the actual file lives in `tokenmaxxxer/tokenmaxxxer-core`,
   outside this session's write scope, this proposal's own delivery in
   this repo is the research plus this design — landing the code change
   itself requires a session scoped directly to that repo. This session's
   phase-2 record will state that plainly rather than attempting an edit
   this sandbox cannot make, per issue-40's precedent.

## Out of scope

- Any change to R1-R4 layout/contract/branch behavior beyond the root
  check itself.
- Building a full shell-cwd resolver for relative Bash tokens — explicitly
  rejected above.
- Actually landing the `tokenmaxxxer-core` code change from this session;
  that is cross-repo work this proposal identifies but cannot execute.

## How you'll know it worked

- The confirmed repro from issue #628 (an out-of-repo `/tmp/...` path
  containing a docs-shaped component) is allowed instead of refused, once
  the fix lands in `tokenmaxxxer-core`.
- The existing regression suite (`run-board-gate-tests.sh`) continues to
  pass in full, including the pre-existing foreign-record-write refusal
  and mention-only-text allow cases — the red/green pair issue #651's
  acceptance criterion names, both directions, neither regressed.
