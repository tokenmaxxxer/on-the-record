---
issue: 2637
role: silent-failure-audit+secure-coding-input-validation-injection-defense-e281acf4
author: silent-failure-audit+secure-coding-input-validation-injection-defense-e281acf4
skills: silent-failure-audit (skill-repository(297e350)), secure-coding-input-validation-injection-defense (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2637/reports/adversarial-review+silent-failure-audit-aba56a87.md
    sha: a93cbf95af82d194fddff5a980284dc3a0349f37
  - path: on-the-record/hooks/deliverable-guard.sh (PR #2643, branch issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985, untracked in this branch)
    sha: 2354b1e7764b0dc3b56b1f641c214c76da902e5e
---

# issue-2637 — silent-failure-audit+secure-coding-input-validation-injection-defense-e281acf4 record

## What was done

Fixed the fourth verification finding recorded in
`docs/issue-2637/reports/adversarial-review+silent-failure-audit-aba56a87.md`
(landed on main): PR #2643's `^`-anchored
`PRODUCT_CAPTURE_PRIORITIES_DIR_RE` exemption in
`on-the-record/hooks/deliverable-guard.sh` correctly closes the
warrant-hunt's `src/`-rooted bypass, but wrongly DENIES a legitimate
priorities-shard write when `file_path` arrives absolute, because the
anchored pattern was matched against the raw (possibly-absolute) `n`
instead of a path guaranteed to start with the literal `docs` segment.

canonical: `2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh:129-155`
(untracked in this branch, read from the pushed PR #2643 branch) —
quoted diff hunk:
```
priorities_candidate = n
_cwd_for_exemption = e.get("cwd")
if (posixpath.isabs(n) and isinstance(_cwd_for_exemption, str)
        and _cwd_for_exemption and posixpath.isabs(_cwd_for_exemption)):
    _rel = posixpath.relpath(n, posixpath.normpath(_cwd_for_exemption))
    if _rel != "." and not _rel.startswith(".."):
        priorities_candidate = _rel
if (n.endswith(EXEMPT_SUFFIXES) or PRODUCT_CAPTURE_ISSUE_RE.search(n)
        or PRODUCT_CAPTURE_PRIORITIES_DIR_RE.search(priorities_candidate)):
    sys.exit(0)
```

Fix, pushed directly to the PR #2643 branch (per this task's explicit
instruction — not opened as a new PR): when `n` (the normalized
`file_path`) is absolute and `cwd` is a usable absolute path, compute
`priorities_candidate` as the lexical (no `realpath`) relative path of
`n` against `cwd` — matching the existing git-root walk's own
non-resolving convention three lines below — and match the anchored
`PRODUCT_CAPTURE_PRIORITIES_DIR_RE` against `priorities_candidate`
instead of `n`. When `n` is relative, or the absolute path's relpath
against `cwd` escapes via `..`, or `cwd` is missing/invalid,
`priorities_candidate` falls back to the raw `n` unchanged — i.e. no new
bypass is possible, only a narrower exemption than an unconditional
match would give. `EXEMPT_SUFFIXES` (`.endswith`) and
`PRODUCT_CAPTURE_ISSUE_RE` (unanchored `.search`) are untouched — both
already tolerated absolute paths before this fix and are out of this
finding's scope.

A regression test, `test/test_deliverable_guard_priorities_shard.py`
(untracked in this branch, pushed on the PR #2643 branch,
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:test/test_deliverable_guard_priorities_shard.py`),
runs the real shipped hook via a real PreToolUse JSON payload on stdin
against a real git checkout, same harness shape as
`test/test_approval_gate_carriers.py`.
derived: `git -C <PR-2643-worktree> show 2354b1e7:test/test_deliverable_guard_priorities_shard.py | grep -c "def test_"` — result: 8

## Why

Reproduced both directions with the real hook script and real payloads,
not by reasoning about the regex, per this task's explicit instruction
and the mounted `secure-coding-input-validation-injection-defense`
skill's scoping (an allowlist-regex fix must be checked against its own
new condition holding for every input shape the surrounding code already
supports, not just the one shape a single passing reproduction covered).

canonical: this session's own reproduction, run against a disposable
fixture repo (`/home/jwjung/dgfix3`, not on any write set, not committed
anywhere) — a fixture rooted in the system tempdir was tried first and
rejected: `deliverable-guard.sh` unconditionally exempts any path
carrying a literal `tmp`/`scratch` segment
(`2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh:135-140`),
so a fixture rooted under the system tempdir masks every absolute-path
case behind that unrelated exemption instead of exercising the
priorities-shard regex — derived: with the fixture rooted under the
system tempdir, both the pre-fix and post-fix hooks returned rc=0 for
`exploit abs src-rooted` (a `src`-rooted absolute path under that
fixture), which should have stayed denied; moving the fixture to
`/home/jwjung/dgfix3` reproduced the pre-fix hook's correct rc=2 deny
for that same case.

derived, against the pre-fix hook (`git show
aa152c797e60e6620e8162dec586b97fc8f171e1:on-the-record/hooks/deliverable-guard.sh`,
piping a real PreToolUse JSON payload on stdin via `bash
deliverable-guard.sh`, `TOKENMAXXXER_SPAWNED` unset, fixture rooted at
`/home/jwjung/dgfix3`):
```
rel shard legit           docs/reports/product/priorities/x.md              -> rc=0 (exempt, correct)
exploit rel src-rooted    src/docs/reports/product/priorities/hack.md       -> rc=2 (denied, correct)
exploit abs src-rooted    /home/jwjung/dgfix3/src/docs/reports/product/priorities/hack.md -> rc=2 (denied, correct)
abs shard legit           /home/jwjung/dgfix3/docs/reports/product/priorities/x.md       -> rc=2 (WRONGLY DENIED -- the finding)
abs issue-shard legit     /home/jwjung/dgfix3/docs/issue-99/reports/product/priorities/x.md -> rc=2 (WRONGLY DENIED)
abs shard legit w/ ..     /home/jwjung/dgfix3/foo/../docs/reports/product/priorities/x.md  -> rc=2 (WRONGLY DENIED)
real deliverable rel      src/foo.py                                        -> rc=2 (denied, correct)
abs legacy priorities.md  /home/jwjung/dgfix3/docs/reports/product/priorities.md         -> rc=0 (exempt, correct -- EXEMPT_SUFFIXES tolerates absolute)
abs docs/specs/approvers  /home/jwjung/dgfix3/docs/specs/approvers.md                    -> rc=0 (exempt, correct)
```
derived, same payloads, same fixture shape (fresh `git init` repo), run
against the post-fix hook
(`2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh`):
```
rel shard legit           -> rc=0
exploit rel src-rooted    -> rc=2 (still denied -- bypass stays closed)
exploit abs src-rooted    -> rc=2 (still denied -- bypass stays closed)
abs shard legit           -> rc=0 (FIXED)
abs issue-shard legit     -> rc=0 (FIXED)
abs shard legit w/ ..     -> rc=0 (FIXED)
real deliverable rel      -> rc=2 (unchanged, correct)
abs legacy priorities.md  -> rc=0 (unchanged, correct)
abs docs/specs/approvers  -> rc=0 (unchanged, correct)
```
derived: an absolute shard path reached through a symlinked root
(`ln -s /home/jwjung/dgfix3 /home/jwjung/dgfix3link`, `cwd` and
`file_path` both given with the `dgfix3link` prefix, not resolved) ->
rc=0, correct, since the fix's `relpath` is purely lexical/string-based
on the two inputs as given — this case was tried in addition to the
finding's own reproduction, to check the symlinked-root shape the task
asked about.

derived: `test/test_deliverable_guard_priorities_shard.py`
(untracked in this branch) run against the pre-fix hook content
(temporarily swapped into the PR #2643 worktree, then restored) via
`python3 -m pytest test/test_deliverable_guard_priorities_shard.py -q`
— result: `3 failed, 5 passed` (`test_absolute_shard_write_is_exempt`,
`test_absolute_issue_scoped_shard_write_is_exempt`,
`test_absolute_shard_write_with_dotdot_is_exempt` fail on the pre-fix
hook), confirming this is a real regression test rather than a
tautology; the same invocation against the fix in place returned
`8 passed`.
derived: `git -C <PR-2643-worktree> diff --stat` after restoring the
post-fix hook content showed the working tree byte-identical to the
committed `2354b1e7` state (empty diff), confirming the swap-and-restore
left no stray edits.
derived: `python3 -m pytest test/ -q` run on the PR #2643 branch both
before this change (worktree at `aa152c797e60e6620e8162dec586b97fc8f171e1`)
and after (worktree at `2354b1e7764b0dc3b56b1f641c214c76da902e5e`) —
result before: `15 failed, 342 passed`; result after: `15 failed, 350
passed` — the same 15 failing test IDs both times (network-dependent
`gh`/skill-selection tests and one pre-existing
`test_convention_equivalence.py` baseline-shape assertion, none
importing or invoking `deliverable-guard.sh`), and the 8-test delta
(350 - 342 = 8) accounted for entirely by the new regression test file,
confirming no other test regressed.

skill-verdict: secure-coding-input-validation-injection-defense —
applied: invoked; confirmed via the skill's own rules that the fix keeps
the anchored-regex allowlist as the sole control (rule 1 — no denylist
introduced) and fails closed rather than exempting on an
ambiguous/unresolvable relpath (rule 8 — the fallback path matches the
raw, still-un-prefixed absolute string against the same anchored
pattern, which cannot match, so it falls through to the existing deny
path in
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh:186-193`
rather than silently granting exemption).
skill-verdict: silent-failure-audit — not-applicable: the diff (quoted
in full under "What was done" above) adds no new try/except, error
callback, or Promise-rejection path — the `..`/relpath handling is an
unconditional fallback assignment, not a caught exception — so there is
nothing new for this skill's Handled/Silently-Absorbed/Unreachable
classification to apply to.

## What did not work

None.

## Upstream basis

- `docs/issue-2637/reports/adversarial-review+silent-failure-audit-aba56a87.md`
  (landed on main via PR #2649) — the fourth verification finding this
  record fixes, read for the reproduction and resolution path but
  re-derived independently rather than trusted (see Why).
- `on-the-record/hooks/deliverable-guard.sh`,
  `test/test_deliverable_guard_priorities_shard.py` (both untracked in
  this branch) — PR #2643, branch
  `issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985`,
  commit `2354b1e7764b0dc3b56b1f641c214c76da902e5e` (pushed directly to
  that branch per this task's explicit instruction; not part of this
  record's own commit).

## Open findings

None from this fix. Two findings from the same verification round are
explicitly out of this task's scope and were left untouched, per
instruction: `deliverable-guard.sh`'s git-root walk looping on
`//`-prefixed absolute paths (pre-existing, unrelated to PR #2643), and
the same-process/same-microsecond filename collision in
`priorities.py`'s `_priorities_entry_path()` (cross-session collision is
covered by the pid component, which is what issue #2637's acceptance
requires).

Untested/known limit, noted rather than fixed (out of the anchor-fix's
own scope): an absolute `file_path` reached through a symlinked `cwd`
that differs textually from the symlink prefix used in `file_path`
itself (i.e. `cwd` given as the resolved real path while `file_path`
still carries the symlink segment, or vice versa) would not match via
the lexical `relpath`, falling back to the raw absolute string and
therefore being denied rather than exempted — a false-deny in that one
mismatched-symlink shape, not a bypass. Not observed as a real payload
shape in this codebase's own hook-payload construction (`cwd` and
`file_path` are always sourced from the same tool-call context), so left
as a known limit rather than fixed speculatively.

## Next steps

None — `loop_state: landed`. PR #2643 already carries the fix (pushed
directly to its branch); this record documents that action for issue
#2637's own audit trail.
