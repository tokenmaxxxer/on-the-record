# Current-state survey — issue #577

Skip condition check: neither scout-skip condition applies cleanly (a design
decision is open — which signal scopes "phase-2 obligation" to a round), so
scouting is not skipped; however the acceptance criterion itself prescribes
the shape of the fix ("mechanically simplest sound rule ... approval comment
newer than the head branch's first commit, matched to the PR's own role"),
so the decision space is a choice between that named rule and close variants
of it, not an open product-shaped exploration. No external scout brief was
produced; the alternative comparison lives in the proposal's Rationale
instead, per the issue's own acceptance text.

## Write surface

`on-the-record/hooks/contract-guard.sh` (single file, ~164 lines, pure
Python embedded in bash via heredoc). Phase-2 determination lives at lines
143-152:

```python
comments = gh_json("issue", "view", str(issue), "--json", "comments", "-q", ".comments") or []
prefix = "APPROVE issue-%d/" % issue
phase2 = any(
    (c.get("body") or "").strip().startswith(prefix)
    and c.get("author", {}).get("login") in approvers
    and (c.get("body") or "").strip()[len(prefix):]
    for c in comments
)
```

This scans ALL historical comments on the issue for ANY `APPROVE
issue-<n>/<role>` from any approver, for any role, from any round. It never
looks at: which role the PR under merge belongs to, which round the PR
belongs to, or when the approval was posted relative to the PR's own work.

## Existing tests (`on-the-record/hooks/test_contract_guard.py`)

`grep -c "^def test_" on-the-record/hooks/test_contract_guard.py` derives 7
test functions, all for issue #443 (target-repo resolution: `cd`, `-R`,
PR-URL forms). None touch round/role scoping. Test harness:
- `_run_guard(cmd, fixtures, tmp_path, cwd)` invokes `contract-guard.sh` as a
  subprocess with a fake `gh` shim on PATH (`FAKE_GH`, defined in
  `on-the-record/hooks/test_contract_guard.py`) driven by a `GH_FIXTURES`
  JSON file.
- The fake `gh` currently answers only `pr view` (returns `body`, `number`)
  and `issue view` (returns the fixture's `issue_comments` list, each item
  only `body` + `author.login`).
- `_approve_comment(issue, login)` fixture helper hardcodes
  `f"APPROVE issue-{issue}/implementation"` — always role `implementation`,
  no timestamp field.

To exercise round/role scoping, the fake `gh` and fixtures need to also
carry: `headRefName` on the PR (branch name `issue-<n>/<role>`, the existing
naming convention per contract v3 — `Work on the branch
issue-<n>/implementation`), a per-PR "head branch first-commit time" surface,
and a `createdAt` per issue comment.

## What `gh` actually exposes

- `gh pr view <n> --json headRefName` — the PR's head branch name, format
  `issue-<n>/<role>` per contract v3's branch-naming rule (verified against
  this repo's own branch: `issue-577/implementation`).
- `gh pr view <n> --json commits` — ordered list of commits on the PR;
  `commits[0]` is the branch's first commit relative to its merge base, each
  with a `committedDate` field. This is the natural mechanical proxy for
  "the head branch's first commit" the issue's acceptance text names.
- `gh issue view <n> --json comments` — each comment already carries
  `createdAt` (ISO-8601), not just `body`/`author`; the current script's
  `-q .comments` projection simply never selected it.

No new dependency, no new gh subcommand — every field needed is already
covered by `--json` on calls the script already makes (`pr view`, `issue
view`), just with the field list widened.

## Round/role identity available at merge time

The PR's own role is recoverable from `headRefName` (`issue-<n>/<role>`)
without needing any new input — the contract already commits to
one-branch-per-issue-per-role, so `headRefName`'s suffix after the last `/`
is the PR's role, matching the same `<role>` token the `APPROVE
issue-<n>/<role>` comment format itself carries in prefix construction
(`contract-guard.sh:144`, `prefix = "APPROVE issue-%d/" % issue`, currently
role-blind because it only interpolates the issue number).

"Round" has no first-class field anywhere in GitHub's data model for this
repo (no round number in branch names, PR bodies, or comments) — every
round of a role reuses the same branch (`issue-<n>/<role>`) and its own
sequence of commits/PRs on top of it. The only round-differentiating signal
mechanically available is *time*: a new round's phase-1 commit lands after
the previous round's approval comment; the same-round's own approval (if
any) lands before that round's own delivering commit exists. This matches
the issue's own suggested rule almost exactly: "the approval comment that
should gate PR N is ... newer than the PR's phase-1 predecessor merge" (or,
per the acceptance's minimum-viable framing, newer than the head branch's
first commit).
