---
issue: 2725
role: independent-verification-2
author: independent-verification-2
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2725/reports/architecture-coupling-classification+adversarial-review-e1b1ee1a.md
    sha: c58323c8905f19775119717ed4153700f06a4d79
  - path: board.py
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
  - path: gates/flows.py
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
  - path: test/test_board_front_skill.py
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
---

# issue-2725 — independent-verification-2 record

## What was done

canonical: `gh pr view 2735` output — state OPEN, `Closes #2725`, head
`a366617aa7ea5b8a10cbeaafbd419064b2cedf77`, files changed: `board.py`
(+64/-10), `gates/flows.py` (+6/-1), `test/test_board_front_skill.py`
(new, untracked on this session's own branch — exists only on PR #2735's
branch), `docs/issue-2725/reports/architecture-coupling-classification+adversarial-review-e1b1ee1a.md`
(new, untracked on this session's own branch — exists only on PR #2735's
branch, hereafter "the subject record"), plus that record's own
`deviation-log/` entry.

Independently verified PR #2735 (`issue-2725/architecture-coupling-classification+adversarial-review-e1b1ee1a`),
the deliverable for this issue. Read the PR body and the subject record,
then re-derived the issue's own acceptance checks in a disposable `git
worktree`, not this session's tracked tree — `git fetch origin
issue-2725/architecture-coupling-classification+adversarial-review-e1b1ee1a:pr-2735-check
&& git worktree add /tmp/pr2735check pr-2735-check` — and constructed one
additional scenario the subject's own test file (untracked on this
session's own branch, read from the worktree above) does not cover.

**Acceptance check 1** — `_front_skill` no longer decides by testing
membership in a hardcoded name list:

derived: `cd /tmp/pr2735check && grep -n "for r in (" board.py` — result:
no match, exit code 1.

**Subject's own test suite, reproduced independently**:

derived: `cd /tmp/pr2735check && python3 -m pytest test/test_board_front_skill.py -q`
— result:

```
7 passed in 0.85s
```

matching count = subject record's own claimed count (both 7).

**Historical-fallback claim** (the subject's strongest finding — that the
issue's premise "the fallback can no longer match anything" does not
actually hold): confirmed the on-disk files it cites exist —

canonical: `git ls-files 'docs/issue-1199/reports/product-discovery.md' 'docs/issue-1199/reports/technical-feasibility.md'`
run against this session's own tracked tree (read-only `git ls-files`,
writes nothing) — result: both paths listed, both tracked. Supports the
subject record's claim that the pre-fix `_front_skill` would still
literally match one of these two retired names on `issue-1199`, rather
than falling through to `None` as the issue's premise assumed.

**Additional adversarial scenario, beyond what the subject's own tests
construct**: the subject's tie-break only reports `ok=False` ("cannot
decide") when *every* candidate's introducing commit is identical — it
never checks whether the *winning* (earliest) position is uniquely held
once 3 or more rootless records exist (derived above: the subject's test
file exercises exactly 2-rootless scenarios in all 7 passing cases, none
with 3+). Reproduced against `/tmp/pr2735check`'s `board.py` in a scratch
git repo (`tempfile.TemporaryDirectory`, no writes to any tracked path),
with three rootless records `b`, `c`, `d`, where `b` and `c` are added in
the same commit (a genuine tie for earliest) and `d` is added later in a
separate commit:

derived: script executed against `/tmp/pr2735check`'s `board._front_skill`
and `board._record_add_commit` — result:

```
b b16b48ed808033fa3fd4de271e693cd58c75a929
c b16b48ed808033fa3fd4de271e693cd58c75a929
d ac507ec56f2e55ee2bceffa6a84d8a78d4bfb1cb
front,ok: b True
```

`_front_skill(root, "issue-9", {"b": {}, "c": {}, "d": {}})` returns
`("b", True)` — a plausible, silently-returned answer, decided only by
`b`'s and `c`'s relative position in the `skills` dict / `rootless` list
(both share the identical commit SHA, shown above), not by any signal the
records themselves carry. Full code-level cause, with citation, is in
"Open findings" below.

`gates/flows.py`'s call site (`spawn._front_skill` hoisted out of the
per-skill loop) was read in full and is sound:

canonical: `gates/flows.py` lines 416-424 on `/tmp/pr2735check` —

```
        stage_source = None
        # ok=False (front record 를 결정할 수 없음, 이슈 #2725) 일 때는
        # front 가 None 이라 아래 비교가 어차피 매칭되지 않는다 —
        # stage_source 는 "front record 없음"과 마찬가지로 None 에 머문다;
        # 대시보드 단계 표시에는 두 경우가 같은 영향이라 여기서는 구분하지 않는다.
        front, _front_ok = spawn._front_skill(root, subject, skills)
        for skill, fm in skills.items():
```

Matches the PR body's description: the call moved from once-per-skill
inside the loop to once per subject before it, and `ok=False` /
`front=None` are deliberately left un-distinguished at this call site
since it only drives a dashboard label, not a gate decision.

## Why

derived: `cd /tmp/pr2735check && python3 -m pytest test/test_board_front_skill.py -q`
— result: `7 passed in 0.85s` (same execution as above, cited again here
since this section's claim stands on it).

Verify-at-landing means reproducing a record's own citations is not
sufficient by itself when the deliverable's whole point is "stop silently
guessing in the ambiguous case" — a test suite that only exercises the
cases its author thought of cannot prove the absence of exactly that
failure mode. The highest-value independent check was therefore to look
for an ambiguous case outside what the subject's own passing tests
construct, rather than only re-running what the subject already tested.
Used a disposable `git worktree` plus a `tempfile.TemporaryDirectory`
scratch git repo for every executed check, never this session's own
tracked tree.

## What did not work

None.

## Upstream basis

The subject record (sha `c58323c8905f19775119717ed4153700f06a4d79`, the
commit that landed it; untracked on this session's own branch — read via
the `/tmp/pr2735check` worktree fetched from PR #2735's branch) is the
subject's own deliverable record for this issue. `board.py` and
`gates/flows.py` at `e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2` are the
code changes that record documents.

canonical: `gh pr view 2735` — head `a366617aa7ea5b8a10cbeaafbd419064b2cedf77`,
state OPEN.

## Open findings

1. **Confirmed defect, not yet fixed.**

   canonical: `board.py` lines 631-640 on `/tmp/pr2735check` —

   ```
       candidates = [(r, sha) for r, sha in candidates if sha is not None]
       if len(candidates) < 2 or len({sha for _, sha in candidates}) == 1:
           return None, False
       log = subprocess.run(
           ["git", "-C", str(root), "log", "--reverse", "--format=%H"],
           capture_output=True, text=True,
       )
       order = {sha: i for i, sha in enumerate(log.stdout.split())}
       candidates.sort(key=lambda rc: order.get(rc[1], len(order)))
       return candidates[0][0], True
   ```

   `len({sha for _, sha in candidates}) == 1` only catches the case where
   *every* candidate shares one commit; it does not check whether the
   post-sort `candidates[0]` position is uniquely held once a third,
   later-committed candidate is also present. So `_front_skill`'s
   tie-break can silently return an arbitrary, unjustified answer
   (`ok=True`) instead of reporting `ok=False` when 3 or more rootless
   records exist and exactly a subset of them (not all) share the
   earliest introducing commit — exactly the "What was done" reproduction
   above (`front,ok: b True` on a 3-way case where `b`/`c` tie for
   earliest and `d` is later): the guard never fires for that case, and
   the arbitrary sort-order winner (`"b"`) is returned with `ok=True`.
   This violates issue #2725's own "must not" clause: *"Do not replace
   the fallback with something that silently returns a plausible answer
   in the ambiguous case; if the ambiguity cannot be resolved from the
   records, saying so is the correct output."* Not contrived for this
   repository: the subject record itself was landed in one commit
   together with its own multi-skill-name record, i.e. this repository's
   own build-now convention routinely lands multiple skill records for
   one subject in a single commit — the precondition the reproduction
   above depends on. Resolution path: either PR #2735 is amended before
   merge to also check whether the *minimum*-position commit among
   `candidates` is uniquely held (not only whether the whole set
   collapses to one SHA), or a follow-up issue is filed against this same
   fourth site referencing this record's reproduction. Not resolved by
   this record — reporting, not fixing, is this role's scope.
2. Minor, non-blocking.

   canonical: `board.py` lines 589-596 (`_record_add_commit`'s body) on
   `/tmp/pr2735check` —

   ```
       rel = path.relative_to(root)
       r = subprocess.run(
           ["git", "-C", str(root), "log", "--reverse", "--diff-filter=A",
            "--format=%H", "--", str(rel)],
           capture_output=True, text=True,
       )
       lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
       return lines[0] if lines else None
   ```

   `_front_skill`'s new path runs one `git log` subprocess per rootless
   candidate (`_record_add_commit`, above) plus one whole-history `git
   log` whenever 2+ rootless records exist, versus the retired O(1) name
   check. `gates/flows.py` now calls `_front_skill` once per subject
   inside a loop over `all_subjects`. Not measured for actual cost on
   this repository's current history size; noted for whoever next
   touches this path, not a correctness objection.

## Next steps

None for this record — terminal (`loop_state: landed`). Open finding 1 is
this verification's substantive output and stands as a blocker candidate
for PR #2735, not for this record.

skill-verdict: work-in-english — applied: invoked; this record and all
derived/canonical/acceptance blocks are in English; only the final chat
summary to the user is in Korean.
other mounted skills: not triggered — no chart/visualization surface
(dataviz), no settings.json change (update-config), no keybinding change
(keybindings-help), no code-review/simplify invocation requested by the
task (this record's own reproduction served that purpose directly), no
Claude/Anthropic-API surface (claude-api), no app-launch requested (run),
no new CLAUDE.md requested (init), no separate security-review requested.
