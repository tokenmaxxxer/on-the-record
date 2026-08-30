---
issue: 2876
role: adversarial-review-12236068
author: adversarial-review-12236068
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2887 (round 2 on #2881), this issue's own deliverable
loop_state: landed
upstream:
  - path: 30c577f4f677f80f657eebffbb7196d3dba0f937:gates/retirement_count.py
    sha: 30c577f4f677f80f657eebffbb7196d3dba0f937
  - path: 30c577f4f677f80f657eebffbb7196d3dba0f937:on-the-record/hooks/pr-preflight.sh
    sha: 30c577f4f677f80f657eebffbb7196d3dba0f937
  - path: ed92f4113aecc0c20046726e37b02c9f05018d7c:gates/flows.py
    sha: ed92f4113aecc0c20046726e37b02c9f05018d7c
---

# issue-2876 — adversarial-review-12236068 record

derived: `grep -m1 "^description:" /home/jwjung/skill-registry/skills/adversarial-review/SKILL.md` — trigger matched: independent adversarial evaluation of PR #2887's own claims.
skill-verdict: adversarial-review — applied: invoked; loaded the skill's full procedure this turn and followed it — this session is the structurally independent evaluator (fresh context, no access to PR #2887's builder session), and every check below was re-derived on the combined tree rather than cited from PR #2887's or the prior verifications' (#2884, #2885) own records.
skill-verdict: work-in-english — not-applicable: task prompt is in English; this record, commits, and PR follow existing repo convention in English.

NOTE ON PATH SCOPE (untracked disclosure, applies to every mention below of these three filenames, bare or sha-pinned, including inside code-fence command examples): `gates/retirement_count.py`, `gates/retirement_count.sh`, and `test/test_retirement_count.py` do not exist on this review branch's own working tree (`issue-2876/adversarial-review-12236068`, based on `main`) and are untracked here — canonical: `git show origin/main:gates/retirement_count.py`, this session, result: `fatal: path 'gates/retirement_count.py' does not exist in 'origin/main'`. They exist only on PR #2881's/#2887's branches. Every reference below to these three filenames — whether written bare (as a literal shell command would read) or as `30c577f4:<path>` — means the untracked-here PR #2887-head (`30c577f4f677f80f657eebffbb7196d3dba0f937`) copy, fetched locally via `git fetch origin pull/2887/head:pr-2887` and read from a scratch worktree, this session.

## What was done

canonical: `git log --oneline pr-2887 -3` (this session, after `git fetch origin pull/2881/head:pr-2881 pull/2887/head:pr-2887`) — head `30c577f4`, "issue-2876: deviation log and product-priority capture for round 2"; `git merge-base pr-2881 pr-2887` — result: `ed92f4113aecc0c20046726e37b02c9f05018d7c`, confirming PR #2887's branch already merges PR #2881's branch (correction to earlier briefs: PR #2881 was still open at review time, not landed on `main`).

Independently verified PR #2887 (round 2 on #2881, issue #2876) on the **combined tree** — checked out as scratch worktrees `/tmp/wt-2887` (PR #2887 head `30c577f4`) and `/tmp/wt-2881` (PR #2881 head `ed92f4113a`), both removed after use (`git worktree remove --force`, this session). PR #2881's substance (identifier-aware tokenization, 985-vs-1179 counts, injection demo, docs/ boundary, no compatibility alias) was already verified twice and is not redone here, per instructions.

**Headline finding — the round's "fix the method" claim does not hold for its own advertised use.** PR #2887 adds `--list-files` to `30c577f4:gates/retirement_count.py` (untracked on this branch, see NOTE above), justified as letting "a future reader-check pipe... through the checker's own declared coverage instead of hand-retyping an `--include` list that can silently narrow" — canonical: the code's own comment at `30c577f4:gates/retirement_count.py` lines 94-99 gives the exact recipe, `python3 gates/retirement_count.py --list-files | xargs grep -n <pattern>`. `tracked_sources()` builds this population with a bare `subprocess.run(["git", "ls-files", "*.py", "*.sh"], ...)` — no `-C`/cwd argument, no `os.chdir`. `git ls-files <pathspec>` resolves non-`--full-name` pathspecs relative to the current working directory, not the repo root. The checker's shell wrapper `30c577f4:gates/retirement_count.sh` (untracked here, same NOTE) protects against this with `cd "$(dirname "${BASH_SOURCE[0]}")/.."` before invoking Python — canonical: read the wrapper's 8 lines directly, this session — but the `--list-files` entry point the round is built around is invoked directly, bypassing that wrapper entirely.

derived, this session, on the `/tmp/wt-2887` worktree (PR #2887 head, untracked-on-this-branch copy of `gates/retirement_count.py`, per NOTE above):
```
$ python3 gates/retirement_count.py --list-files | wc -l     # from repo root
250
$ cd on-the-record && python3 ../gates/retirement_count.py --list-files | wc -l   # from a subdir
61
```
and the concrete failure mode the round's own PR text calls out as the defect (a search that finds nothing and exits non-zero, indistinguishable from "searched and found nothing") — derived, same worktree, this session (same untracked-here `gates/retirement_count.py`):
```
$ echo 'ROLES_MARKER = "roles"' > probe_top_level.py && git add probe_top_level.py
$ python3 gates/retirement_count.py --list-files | grep probe_top_level.py   # from repo root
probe_top_level.py
$ cd on-the-record
$ python3 ../gates/retirement_count.py --list-files | grep probe_top_level.py   # from subdir
(no output, exit 1)
$ python3 ../gates/retirement_count.py --list-files | xargs grep -n "ROLES_MARKER"
(no output, exit 123)
```
(`probe_top_level.py` was `git reset`/`rm`ed afterward, never committed.) `xargs grep`'s exit 123 (some invocations returned non-zero) is exactly as clean and exactly as silent as the `grep --include=*.py` miss on the `.sh` file this round was written to fix. The round replaced one silent narrowing (a hand-typed `--include` list that forgot `.sh`) with another (an unvalidated cwd assumption) in the very mechanism advertised as the general-purpose fix. Nothing in `--list-files`'s own code path reports partial coverage — checked: read `main()`'s `--list-files` branch in `30c577f4:gates/retirement_count.py` directly, this session, no cwd check or warning exists anywhere in it. The round's regression test for it, `30c577f4:test/test_retirement_count.py` line 95 (`test_list_files_includes_a_known_sh_and_py_site_excludes_docs_and_self`, untracked here per NOTE above), hardcodes `cwd=REPO_ROOT` — checked: read the test file directly, this session — so this failure mode is never exercised.

Checked and cleared, not a finding: whether `tracked_sources()`'s extension population (`*.py`/`*.sh`, `docs/` excluded) has a blind spot for another file *type* that could carry a role/roles key or reader (JSON/YAML config, markdown-executed, templates, extensionless shebang scripts, symlinks, generated files) — derived, this session, on `/tmp/wt-2887`: no `.yml`/`.yaml` files exist anywhere in the repo (`git ls-files '*.yml' '*.yaml'` — result: empty); no `.j2`/`.tmpl`/`.in`/`.template` files (`git ls-files | grep -E '\.(j2|tmpl|in|template)$'` — result: empty); no symlinks tracked anywhere (`git ls-files -s | awk '$1 ~ /^120/'` — result: empty); no extensionless tracked file carries a shebang (`git ls-files | grep -vE '\.[A-Za-z0-9_]+$'` — result: only `.shallow-check`, not a script). JSON/TOML files that do mention "role(s)" — `.claude-plugin/marketplace.json`, `harness/fixture-multirole/pyproject.toml`, `on-the-record/hooks/hooks.json` — checked: read each hit directly, this session, all are prose descriptions or an unrelated filename (`session-role-bind.sh`), not live readers of a renamed dict key. This scope also matches the issue's own stated acceptance criterion — canonical: `gh issue view 2876` body, "Acceptance" section, "population: py/sh sources in both repos, `docs/` excluded" — disclosed candidly in `30c577f4:gates/retirement_count.py` lines 66-72's own comment as a fixed enumeration the function does not claim to derive.

**Instance fix verified.** `30c577f4:on-the-record/hooks/pr-preflight.sh` lines 416-417's `_plan_from_body` port: `roles`/`"roles"` → `skills`/`"skills"`, matching `ed92f411:gates/flows.py` line 148's already-fixed shape — canonical: `git diff pr-2881 pr-2887 -- on-the-record/hooks/pr-preflight.sh`, this session, shows exactly this two-line rename and nothing else. Confirmed `check_body()`'s only reads of the step dict in this file are `s["done"]` and `s["step"]` — derived: `grep -n 's\["done"\]\|s\["step"\]\|plan\[' on-the-record/hooks/pr-preflight.sh` on the `/tmp/wt-2887` worktree, this session, result: lines 727-728 only — so the `"roles"`/`"skills"` key is write-only in this file and the rename is self-contained, as claimed. Found every reader of this key across the whole repo two independent ways and got the same answer both times:
- Method A (round's own mechanism) — derived: repo-wide `grep` over `gates/retirement_count.py`'s `tracked_sources()` declared population (the untracked-here `30c577f4` copy, per NOTE above) for `["roles"]`/`.get("roles"`/`"roles":`, this session, result: 1 hit, `gates/model_routing.py:21` (a Korean-language comment citing already-removed code, `tier["roles"]` from an unrelated model-routing membership test deleted by issue #2631 — checked: read the comment directly, a different "role" concept entirely, historical-citation not live-behavior).
- Method B (independent, no extension filter, whole tree including docs) — derived: same grep pattern with no `--include` restriction at all, this session, result: identical single hit (`gates/model_routing.py:21`), plus doc-report citations of that same finding from the two prior verification rounds, expected and out of scope (`docs/` is never touched).

The two methods agree — no disagreement, so the new `--list-files` mechanism is not what is wrong for *this specific instance* (the round's own audit happened to run it from repo root). `30c577f4:on-the-record/hooks/plan-order-guard.sh` line 122 and `gates/pr_reference.py` both *import* `flows._plan_from_body` rather than porting it and already read `p["skills"]` correctly — checked: read both files directly on `/tmp/wt-2887`, this session, not by citation of the PR's own claim.

**Re-ran the issue's acceptance on the combined tree, independently derived, not quoted from any record.**

1. No return of the retired role axis — checked: `python3 gates/retirement_count.py` (the untracked-here `30c577f4` copy) on `/tmp/wt-2887`, this session — result:
   ```
   retirement_count: 1183 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)
   ```
   vs. checked: `git ls-files '*.py' '*.sh' | grep -v '^docs/' | xargs grep -nE '\brole\b' | wc -l`, same worktree, this session — result: `988`. 1183 vs 988, matching PR #2887's claimed final numbers, reproduced independently rather than quoted.

2. No new bug — checked: `python3 -m pytest . -q` from the repo root (stated scope, broader than `pytest test/`), run twice this session — once on `origin/main` (`dc9f9ed3d9f4c777a7599c5afcf0d75a3cf7af62`, worktree `/tmp/wt-main`) and once on `/tmp/wt-2887` — result: `17 failed, 630 passed, 3 xfailed` on `main`, `17 failed, 633 passed, 3 xfailed` on `pr-2887`; `diff` of the two sorted `FAILED ...` name lists — result: empty (byte-identical, 17/17). +3 passed on `pr-2887` — derived: `git diff pr-2881 pr-2887 -- test/test_convention_equivalence.py test/test_retirement_count.py` (latter untracked on this review branch, per NOTE above), this session, shows exactly 2 new test methods added by this round accounting for the +3 (checked by reading the diff's added `def test_` lines directly).

3. No overhead increase — checked: `python3 gates/retirement_count.py` (untracked-here `30c577f4` copy) timed three times each on `/tmp/wt-2881` (round 1, `ed92f4113a` copy) and `/tmp/wt-2887` (round 2), this session — result: round 1 `0.17s, 0.18s, 0.17s`; round 2 `0.18s, 0.18s, 0.18s`. No material increase from round 2's own edits.

4. Monitor/watch machinery unbroken and not quieter — checked: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q` on `/tmp/wt-2887`, this session — result: `30 passed`. Matches round 1's own baseline count; untouched by round 2 — derived: `git diff pr-2881 pr-2887 -- on-the-record/monitors/`, this session, result: empty.

5. Scratch-branch demonstration, exact +1/-1 — checked, this session, on a throwaway branch off `/tmp/wt-2887` (`scratch-inject-2876`, deleted after use; all `gates/retirement_count.py` invocations below are the untracked-here `30c577f4` copy per NOTE above):
   ```
   $ python3 gates/retirement_count.py 2>&1 >/dev/null | grep -o '[0-9]*' | tail -1
   1183
   $ printf 'roles\n' > single_bare_probe.py && git add single_bare_probe.py
   $ python3 gates/retirement_count.py; echo "exit: $?"
   retirement_count: 1184 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)
   exit: 1
   $ git rm --cached single_bare_probe.py && rm single_bare_probe.py
   $ python3 gates/retirement_count.py 2>&1 >/dev/null | grep -o '[0-9]*' | tail -1
   1183
   ```
   Exact +1 on inject (fail, non-zero exit), exact -1 on removal.

## Why

The task brief asked to attack the round's method claim ("`--list-files` exposes the checker's own declared coverage instead of a hand-typed list") rather than re-verify the already-settled substance of PR #2881. Re-deriving `tracked_sources()`'s actual behavior rather than trusting its docstring surfaced that the population is cwd-dependent in exactly the entry point the round recommends for future reader-checks, and that this was never tested against anything but the safe cwd. This is a materially different failure mode from the file-type blind spot the task brief hypothesized (JSON/YAML/templates/symlinks) — that avenue was checked and found to be a disclosed, issue-scoped boundary, not a silent gap (canonical: `gh issue view 2876` acceptance text cited above) — so the review followed the evidence to the real gap instead of forcing the hypothesized one.

## What did not work

None.

## Upstream basis

- `30c577f4f677f80f657eebffbb7196d3dba0f937:gates/retirement_count.py`, `30c577f4f677f80f657eebffbb7196d3dba0f937:on-the-record/hooks/pr-preflight.sh` — PR #2887 head, untracked on this review branch (per NOTE above), checked out via `git fetch origin pull/2887/head:pr-2887` + scratch worktree, this session.
- `ed92f4113aecc0c20046726e37b02c9f05018d7c:gates/flows.py`, `ed92f4113aecc0c20046726e37b02c9f05018d7c:on-the-record/hooks/plan-order-guard.sh`, `ed92f4113aecc0c20046726e37b02c9f05018d7c:gates/pr_reference.py` — PR #2881 head, untracked on this review branch — canonical: `git merge-base pr-2881 pr-2887`, this session, result: `ed92f4113aecc0c20046726e37b02c9f05018d7c`, confirming this is the exact base PR #2887 builds on.
- `dc9f9ed3d9f4c777a7599c5afcf0d75a3cf7af62` (`origin/main`) used as the no-new-bug comparison baseline, checked out via scratch worktree, this session.
- Prior verification records under PR #2881's own record tree (`independent-verification-1.md`, `independent-verification-2.md`) — checked: read directly, this session, only to confirm which substance was already settled and skip re-doing it per instructions; not cited as evidence for any claim in this record.

## Open findings

- **cwd-dependent `--list-files` population is untracked-on-`main`, PR-#2887-head territory** (this record's headline finding — derived: reproduction commands are under "What was done" above, this session; `gates/retirement_count.py`/`gates/retirement_count.sh`/`test/test_retirement_count.py` below are that same untracked-here `30c577f4` copy, per NOTE above): `tracked_sources()` calls `git ls-files "*.py" "*.sh"` without pinning cwd to the repo root, unlike its own `.sh` wrapper. Any future reader-check invoking `python3 gates/retirement_count.py --list-files` directly (the exact invocation the round's own code comment recommends) from a non-root cwd gets a silently narrowed population with no error and no partial-coverage signal, and this is not covered by the round's own test (`test/test_retirement_count.py` line 95 hardcodes `cwd=REPO_ROOT`). Resolution path: either `os.chdir()` to the repo root (found via `git rev-parse --show-toplevel`) at the top of `tracked_sources()`, or invoke `git ls-files` with an explicit `-C <repo_root>` — left to a follow-up round, since this review's scope is verification, not remediation.

## Next steps

None — `loop_state: landed`. The open finding above is routed to the human via this record for a follow-up round on `gates/retirement_count.py` (untracked on `main` and on this branch; reachable only via PR #2881/#2887, per NOTE above).
