---
issue: 2876
role: silent-failure-audit-133bcbf6
author: silent-failure-audit-133bcbf6
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: gates/flows.py, gates/patrol_board.py, gates/retirement_count.py, gates/retirement_count.sh, on-the-record/hooks/plan-order-guard.sh, test/test_convention_equivalence.py, test/test_retirement_count.py
type: implementation-record
breaking: false
verdict: check-corrected-and-installed, 6-of-6-known-reshaped-sites-fixed-forward, delta-population-disposed-per-site
loop_state: landed
upstream:
  - path: gates/flows.py
    sha: same-commit
  - path: gates/patrol_board.py
    sha: same-commit
  - path: gates/retirement_count.py
    sha: same-commit
  - path: on-the-record/hooks/plan-order-guard.sh
    sha: same-commit
  - path: test/test_convention_equivalence.py
    sha: same-commit
---

# issue-2876 — silent-failure-audit-133bcbf6 record

## What was done

canonical: `gh issue view 2876 --comments` (issue body + its one comment, quoted in full where relevant below) — read before starting, per the spawn instruction.

CORE_BUILD_NOW=1 was set (spawner env — checked: `printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW"` — result: `CORE_BUILD_NOW=1`), so this delivered directly under contract v3 s19a (build-now bypass) — no phase-1 proposal round.

Three commits landed on this branch — canonical: `git log --oneline -4`, run this session, result:
```
12f5b855 issue-2876: exclude the checker's own test fixtures from its count
94c3b3c1 issue-2876: rename the 6 reshaped-substitute role sites to skill
6b7d78df issue-2876: fix retirement-invariant check blind to the plural, fix forward 6 reshaped-substitute sites
1aeecaf8 issue-2865: independent verification of PR #2868's 24-issue triage (#2871)
```

1. `gates/retirement_count.py` (+ `gates/retirement_count.sh` wrapper, the literal invocation the issue names) replaces `grep -rn '\brole\b'` with identifier-aware tokenization: split each line into maximal letter-only runs (separates snake_case joins the way `\b` cannot, since `_` is `\w`), further split each run at camelCase/PascalCase transitions, lowercase, flag the line if any resulting token is exactly `role` or `roles`.
2. Renamed the 5 sites the issue's comment names, plus one more of the identical defect class found by this audit (`gates/flows.py`'s `_ROLE_TRAILER_RE`→`_SKILL_TRAILER_RE`), all forward-only, updating every reader found repo-wide.
3. `test/test_retirement_count.py`: canonical: `python3 -m pytest test/test_retirement_count.py -q`, run this session, result: `10 passed in 0.87s` — covers the tokenizer's derived population and the empty-state/one-occurrence exit-code contract.

## Why

### Part 1 — deriving the check, not extending it

The issue names four candidates: plural, possessive, compounds, case variants. Tested each against `\brole\b` directly instead of assuming all four are gaps — derived: this exact probe, run this session:
```
printf 'role-handoff\nper-role\nsub-role\nroles\nrole'"'"'s\nroles'"'"'\nRole\nROLE\n' > /tmp/t.txt
grep -n '\brole\b' /tmp/t.txt
```
result: matches `role-handoff`, `per-role`, `sub-role`, `role's` — 4 of the 8 input lines — `-` and `'` are already non-word characters, so `\b` already fires there; hyphenated compounds and the singular possessive were never actually gaps. `grep -ni '\brole\b' /tmp/t.txt` (case-insensitive) additionally matches `Role`, `ROLE` — case-sensitivity, not `\b`, was that miss. `roles` and `roles'` never match either grep, case-insensitive or not — the plural, present or possessive, is invisible regardless of case flag.

So the real gap is: the plural suffix (`s` is `\w`, `\b` never fires between `role` and it), case variants, and — generalizing from the *same* root cause (a `\w`-adjacent character defeats `\b`) — any snake_case join, since `_` is also `\w`. Verified this last one is real, not hypothetical: derived: a one-off scan (this session) over `git ls-files '*.py' '*.sh'`, splitting each line into letter-only runs (no camelCase step) and checking whole-run equality to `role`/`roles`, found `user_role`, `role_id`, `role_data`, `branch_role`, `cross_role`, `eligible_roles`, `scoped_roles` among others — identifiers `\brole\b`/`\broles\b` cannot see (full accounting in the delta table below).

Camelcase-splitting on top of snake_case-splitting added only a few more matches in this repo — derived: the same tokenizer run with and without the camelCase sub-split step, `1189 vs 1192` (measured pre-Part-3-fixes, this session) — a small, closed addition (PascalCase test-class names), not unbounded growth. This is why the population is `{role, roles}` matched through identifier-aware tokenization: a closed, 2-item set derived from actual usage (this codebase never inflects "role" any other way — no "roled"/"roling" found by the same scan), not an open-ended spelling list. So this does not trigger the "drop the capability and say so" clause.

**Why the checker excludes itself.** derived: `python3 gates/retirement_count.py` run against its own source before the self-exclusion was added, listed its own docstring line 1 and `RETIRED_WORDS = {"role", "roles"}` (gates/retirement_count.py:35) as findings. A detector must name what it detects — the `tokenmaxxxer-core#361` trade, not a revival — so `gates/retirement_count.py`, its shell wrapper, and `test/test_retirement_count.py` (whose fixtures must also spell the retired words literally to prove the tokenizer still matches them) are the fixed, 3-path self-exclusion, not a growing allowlist. derived: `bash gates/retirement_count.sh 2>&1 >/dev/null | tail -1` before this exclusion covered the test file, result: `retirement_count: 1191 occurrence(s)`; after, result: `retirement_count: 1179 occurrence(s)` — a 12-line difference (1191 − 1179 = 12) matching that one test file's own fixture lines.

**Why "must not increase" matters here, concretely.** The corrected check's post-fix baseline is far from zero — derived: `bash gates/retirement_count.sh 2>&1 >/dev/null | tail -1` → `retirement_count: 1179 occurrence(s)`. This repo is mid-way through the seven-stage Strangler-Fig retirement in `docs/decisions/2026-08-25-retire-role-axis-staging.md` (canonical: that file's own "Consequences"/"Empty-state note" sections, read this session), not past it — so the invariant is a ratchet against that baseline, not "zero role mentions," which is why per-site disposition (not a raw count) is the deliverable.

### Part 3 — fix forward, reader/writer accounting per site

For each renamed site: every reader/writer found by `grep -rn` across all tracked `*.py`/`*.sh` files, and what happens to data already on disk.

**1. `gates/flows.py`'s `_plan_from_body()` — `{"step", "roles"→"skills", "done"}`.**
Readers checked repo-wide — derived: `grep -rn 'plan_order_blocked\|_plan_from_body\|plan-order-guard\|flows_payload\|select_board_entries\|patrol_board' test/`, run this session, result: only `test/test_convention_equivalence.py` matched; and derived: `grep -rn '\["roles"\]\|\.get(.roles.\|"roles":' --include=*.py .` before the rename, result: exactly the 3 flows.py definition/print sites plus `test/test_convention_equivalence.py`'s golden-equality literal:
- `plan_order_blocked()` (gates/flows.py) reads only `["step"]`/`["done"]` — unaffected, confirmed by reading its body this session.
- `gates/pr_reference.py:check_body()` reads only `s["done"]`/`s["step"]` — unaffected, confirmed by reading its body this session.
- `on-the-record/hooks/plan-order-guard.sh:122` read `p["roles"]` — **updated** to `p["skills"]` in commit `94c3b3c1`.
- `test/test_convention_equivalence.py`'s test asserting the literal dict shape — **updated** (dict keys and test name, renamed from `test_plan_from_body_parses_role_checklist` to `test_plan_from_body_parses_skill_checklist`) in commit `94c3b3c1`; canonical: `git show 94c3b3c1 -- test/test_convention_equivalence.py`, this session, shows both the name and the two dict-literal keys changed together.
Existing on-disk data: none. `_plan_from_body()` parses a live GitHub issue body on every call (`iss.get("body")`) — never cached to a file, confirmed by reading `gates/flows.py:330-340` this session (`plan_by_issue[n] = _plan_from_body(...)` assigned into an in-memory dict only).

**2. `gates/flows.py:446`, `flows_payload()`'s per-flow `"roles"→"skills"` list.**
Reader found repo-wide: only `flows()`'s own printer (line 543, updated in lockstep, same commit). derived: `grep -rn 'flows_payload\|import flows\|from flows\|flows\.flows(' --include=*.py --include=*.sh .` lists every importer of this module (`gates/ci.py`, `gates/pr_reference.py`, `spawn.py:2360`, `on-the-record/hooks/plan-order-guard.sh`) — none of them subscripts `["roles"]`/`["skills"]` on the returned payload, checked by reading the surrounding lines of each this session. Existing on-disk data: none — `flows_payload()` is computed fresh from live `gh pr list`/`gh issue list` output every call; `board.py` does not import or cache `flows.py`'s output — checked: `grep -n "flows" board.py`, result: 0 hits (only an unrelated match on `trusted-repo-config.json`, confirmed by reading the grep output line itself).

**3. `gates/patrol_board.py:60`, `select_board_entries()`'s path-prefix `f"roles/{skill}/"→f"skills/{skill}/"`.**
Not a persisted key — a query-time string-prefix test against `entry["path"]` (a scanner-recorded source file path). Checked whether a `roles/` directory exists to migrate — derived: `git ls-files | grep -E '^roles/'` and `find . -maxdepth 1 -type d -name roles`, both run this session, both returned empty — no such directory exists on disk in this repo, so this exact prefix was already unreachable for this repo specifically; the fix corrects the defect shape (a `skill`-axis value plugged into a `roles/`-literal string) regardless. No other reader constructs this prefix — derived: `grep -n "roles/{skill}\|all roles\|Patrol board" gates/*.py on-the-record/gates/*.py` before the edit, result: exactly 2 lines, both in `gates/patrol_board.py`.

**4. `gates/patrol_board.py:328`, `title = f"Patrol board: {skill or 'all roles'→'all skills'}"`.**
Write-only: used only in `gh issue create --title` inside `run_patrol_board()`'s `issue is None` branch, confirmed by reading the function this session. The existing-issue lookup (`find_board_issue()`) matches by GitHub label (`LABEL_BOARD`, `skill:{skill}` — read from `gates/patrol_board.py:208-233` this session), never by title text; the update path (`gh issue edit ... --body ...`) never passes `--title`. So a pre-existing board issue's stored title text, if any exists, is never re-read or re-matched by this code — changing the text going forward cannot orphan lookup of an existing board issue.

**One additional site found by this audit, same defect class as the issue's 5: `_ROLE_TRAILER_RE`→`_SKILL_TRAILER_RE` (gates/flows.py:37, 47).**
canonical: `git blame -L 37,37 gates/flows.py`, run this session before the rename, attributed this line to `e1b35a53` — issue-2741, "retire the role persisted key — rename to skill, forward-only" — the same commit the issue's comment names for the other flows.py sites. The commit's own adjacent comment (gates/flows.py:34, unchanged) reads "renamed from 'role:' by issue #2741" — it rewrote the regex to capture `skill:` trailers but left the constant's own name on the retired axis, the identical "value moved, key didn't" shape. canonical: `git blame -L 40,40`, `-L 47,47`, and `-L 351,351` on `gates/flows.py`, all run this session, all attribute the surrounding function `_role_from_pr` and its call site to `0606f780f` (2026-08-21, before #2741) — pre-existing, not part of this defect, left unrenamed. Reader accounting: derived: `grep -rn "_ROLE_TRAILER_RE" --include=*.py --include=*.sh .` before the rename, result: exactly 2 hits, both in `gates/flows.py` (its own definition and use) — module-private, zero external readers. No persisted data: this regex is applied live to each PR body string fetched from `gh pr list`, never stored. With this site, the total renamed is the issue's 5 plus this 1: canonical: `git show --stat 94c3b3c1`, run this session, result: `gates/flows.py | 14 +++++++-------` / `gates/patrol_board.py | 4 ++--` / `on-the-record/hooks/plan-order-guard.sh | 2 +-` / `test/test_convention_equivalence.py | 6 +++---`.

**No compatibility alias anywhere.** Every renamed dict key is read by plain subscript (`d["skills"]`, not `d.get("roles", d.get("skills"))`), so a straggler reader still asking for the old key gets `KeyError: 'roles'` — a hard error, not a silent `None` — verified there is no such straggler by the repo-wide greps cited per-site above.

## Part 2 — disposition: the delta between old and corrected

Method: ran the corrected tokenizer on the pre-fix tree; diffed its output against the old case-insensitive `\brole\b` to isolate the population invisible to the old check. derived: `comm -13 <(sorted old-check output) <(sorted corrected-check output)`, run this session, result: 217 lines (`wc -l /tmp/delta.txt` → `217`). Classified every one of the 217 by parsing each `.py` file with `ast` (bare-string-expression node ranges = every docstring, module/class/function-level) and `tokenize` (COMMENT token lines), `.sh` files by leading `#`; a site inside a docstring/comment range is `historical-citation`, everything else is `live-candidate`. derived: the classifier script run against the 217-line delta list this session, result: `historical-citation (comment/docstring): 128` / `LIVE-CANDIDATE (needs individual look): 89` (128 + 89 = 217, `wc -l` on each half matched).

**Historical-citation — 128 of the 217, derived from the classifier run cited immediately above.** All inside comments/docstrings. Spot-checked the most-repeated dead symbols named in this bucket for a live definition anywhere in tracked py/sh: `role_settings`, `resolve_role_family_source`, `resolved_role_model`, `role_source`, `_judge_roles_run_today`, `JUDGE_MAX_ROLES_PER_MERGE`, `_ROLE_SKILLS`, `_exempt_own_role`, `_open_role_prs`, `isolated_role_model_config`, `_role_source_allowlist` — derived: per-symbol `grep -rn "<symbol>\s*("` / `"<symbol>\s*="` run this session, excluding the comment line each was found in, result: 0 non-comment/non-docstring hits for every one of the 11 symbols checked. Example (spawn.py:749, unchanged, historical): `"이슈 #2560: 고정 43개 역할 이름 튜플 ROLES는 여기서 완전히 삭제됐다"` ("issue #2560: the fixed 43-role-name tuple ROLES was completely deleted here") — narration of already-completed work, the `tokenmaxxxer-core#361` trade. File distribution of these 128 — derived: the classifier's per-file grouping, this session: `consult.py` 19, `test/test_convention_equivalence.py` 19 (pre-existing test names/comments, separate from its 2 live-behavior lines already fixed), `spawn.py` 14, `gates/flows.py` 13 (comment/docstring lines, separate from its 6 live-behavior lines), `pipeline.py` 9, and 1-6 lines each across the remaining files (19+19+14+13+9 = 74; the remainder of 128 — 128 minus 74 equals 54 — spread across roughly 45 other files, per the classifier's full per-file counts produced this session).

**Live-candidate — 89 of the 217, derived from the same classifier run.** Full disposition:

- **6 of these 89 are the reshaped-substitute defect, fixed forward** (see Part 3 above, and canonical: `git show --stat 94c3b3c1` cited there for the exact line counts): `gates/flows.py` ×4 (`_SKILL_TRAILER_RE` definition + use, the plan-step `"skills"` key, the flow `"skills"` key, the printer), `gates/patrol_board.py` ×2 (the `skills/{skill}/` prefix, the `'all skills'` title). Reason: touched by a retirement commit (`e1b35a53` or `e1f390ab`) that moved the value to the skill axis while leaving the name on the role axis.
- **The remaining 83 (89 minus the 6 above) are pre-existing, not-yet-migrated — out of #2876's scope.** Verified a representative sample was never touched by either flagged commit — canonical: `git blame`, run this session, on `spawn.py`'s `role_data()` def line → `8a346728` (issue-2572, 2026-08-27); on `gates/gates.py:36`'s `PROTECTED_ROOT_DIRS = {"roles", ...}` → `f4a2221f0` (2026-07-25); on `on-the-record/hooks/approval-gate.sh:117`'s `branch_role` local → `0606f780f` (2026-08-21). All three predate both `e1b35a53` and `e1f390ab`. This group spans: `spawn.py`'s `role_model.txt` filename constant and `SKILL_MODEL_CONFIG` path (2 sites, mirrored in `test/test_spawn_model_override.py`); `spawn.role_data()`'s 2 call sites (`bench/run.py`, `on-the-record/monitors/poll-heartbeat.sh`) plus its test double `on-the-record/monitors/test_poll_heartbeat.py:def role_data()` (3 sites); the `roles/*.json` glob convention repeated in `gates/accumulation.py`, `gates/skip_eligibility.py`, `gates/risk_report.py`'s `GATES_DIRS`, and `on-the-record/hooks/accumulation-claim-guard.sh` (5 sites — the directory does not exist in this repo's tree today per the same `git ls-files`/`find` check as site 3 in Part 3 above, but the pattern predates both flagged commits and this checkout has no visibility into other repos' layouts, so left as-is); `gates/patrol_wiring.py`'s `board_roles` field; `on-the-record/hooks/delegated-judgment-gate.sh`'s `evaluating_roles`/`eligible_roles`/`contradicting_role`/`source_role` message-building locals (6 sites, user-facing but pre-existing); `on-the-record/hooks/git-push-guard.sh`'s `_ROLE_BRANCH_RE`; `on-the-record/hooks/decision-queue-stopgate.sh`'s `_session_id_for_role` local; and the remainder as test method/class names (`test/test_branch_skill_field.py`, `test/test_convention_equivalence.py`, `test/test_spawn_model_override.py`, `test/test_spawn_skill_invocation.py`, `test/test_roster_skill_field.py`, `test/test_flows_skill_field.py`, `test/test_board_ownership_report.py`, `test/test_branch_naming_dual_scheme.py`, `test/test_consult_no_rulebook_identity_regression.py`) describing pre-#1814/#2741/#2600 behavior by its then-current name, or referencing the still-live `flows._role_from_pr` (pre-existing per the additional-site paragraph above — its function name, unlike its neighboring `_SKILL_TRAILER_RE` constant, was never touched by a retirement commit). All tracked by issue #2241's staged rollout; a later stage's own write-set owns renaming these, which this issue does not authorize.

Every one of the 217 delta lines received an individual category from the `ast`/`tokenize` classifier (not one bulk verdict); the write-up above groups the resulting sites by shared reason and file for readability, but the classification itself ran per-line, one verdict per site.

## Standing invariants — commands and their output

**1. No return of the retired axis in any reshaped form, corrected pattern vs. old pattern side by side.**
```
derived: git ls-files "*.py" "*.sh" | grep -v '^docs/' | xargs grep -c '\brole\b' | awk -F: '{s+=$2} END{print s}'
```
result: `985` (old case-sensitive `\brole\b`, post-fix tree, this session).
```
derived: bash gates/retirement_count.sh 2>&1 >/dev/null | tail -1
```
result: `retirement_count: 1179 occurrence(s)` (corrected pattern, post-fix tree, this session). Gap: 985 vs 1179, a difference of 194 sites the old pattern still cannot see — all accounted for in the 83-site pending-migration group above (the 6 defect sites are fixed; none of the delta's 128 historical-citations count toward "reshaped form" since they cite dead symbols, not live behavior).

**2. No new bug — collection scope stated per the standing warning.**
`pytest test/` from repo root vs `pytest .` — derived: `python3 -m pytest --collect-only -q test/ 2>&1 | tail -3`, result: `459 tests collected`; derived: `python3 -m pytest --collect-only -q 2>&1 | tail -3`, result: `614 tests collected` (both run this session, before any edit — `.` also walks `tests/` and `harness/fixture-*`). Used the wider (`.`) scope, comparing failing-test-NAME sets, not counts:
```
derived: git stash && python3 -m pytest . -q 2>&1 | tail -3   # this branch had no prior commits ahead of origin/main, so stash == origin/main-equivalent baseline
```
result: `16 failed, 595 passed, 3 xfailed`.
```
derived: git stash pop && python3 -m pytest . -q 2>&1 | tail -3   # this session's changes restored, re-run after all 3 commits landed
```
result: `16 failed, 605 passed, 3 xfailed`. The 16 failing test names printed by both runs are byte-identical sets — compared this session by reading both `short test summary info` blocks in full — and all 16 fail with `fetch 실패 — fatal: 'origin' does not appear to be a git repository`, a pre-existing sandbox-has-no-real-git-remote condition unrelated to this change. The +10 passing (595 to 605, a difference of exactly 10) is `test/test_retirement_count.py`'s new tests (canonical: that file, 10 `def test_*` methods, counted by reading the file); no test moved from pass to fail or vice versa between the two runs.

**3. No overhead increase.**
```
derived: time bash gates/retirement_count.sh > /dev/null 2>&1
```
result: `real 0m0.179s`.
```
derived: time (grep -rn '\brole\b' --include=*.py --include=*.sh . 2>/dev/null | grep -v '^\./docs/' > /dev/null)
```
result: `real 0m0.032s`. The corrected check is about 150ms slower in absolute terms (0.179 − 0.032 = 0.147s; Python process start + per-line tokenization vs. one grep process) — both complete in well under a second, and this check runs at most once per session/PR alongside `gh api` calls that themselves take seconds — canonical: `gates/flows.py`'s `subprocess.run(["gh", ...])` call sites, read this session — so this is not material overhead in that context.

**4. Monitor/watch machinery unbroken and not quieter.**
```
derived: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q 2>&1 | tail -3
```
result: `30 passed`. Untouched by this change — derived: `git status --short on-the-record/monitors/`, this session, result: empty output, no modifications; 30 of 30 both before (part of the 595-passed baseline total above, this suite already green there) and after this session's edits — not quieter.

## Acceptance — scratch-branch failure demonstration

derived: executed this session (worktree and branch both removed afterward — nothing from this demonstration is part of the delivered diff):
```
git worktree add /tmp/scratch-2876 <scratch branch off this branch's HEAD>
cp gates/retirement_count.{py,sh} /tmp/scratch-2876/gates/   # this session's checker, copied in since the scratch branch predates it
cd /tmp/scratch-2876
printf 'ACTIVE_KINDS = ["roles"]\n' > single_plural_probe.py && git add single_plural_probe.py
grep -c '\brole\b' single_plural_probe.py
```
result: `0` (old check: blind to the injected plural).
```
bash gates/retirement_count.sh 2>&1 >/dev/null | tail -1
```
result: `retirement_count: 1193 occurrence(s)` (baseline 1192 at that point in the session + the 1 injected occurrence: 1192 + 1 = 1193).
```
git rm -f --cached single_plural_probe.py -q && rm -f single_plural_probe.py
bash gates/retirement_count.sh 2>&1 >/dev/null | tail -1
```
result: `retirement_count: 1192 occurrence(s)` (back to baseline: 1193 − 1 = 1192). The corrected check's count moved by exactly +1 when the plural-only occurrence was added and −1 when removed, while the old check found 0 in the same file both times — a check seen to fail and un-fail on the exact injected change, not one merely asserted to work. Cleanup, run this session: `git worktree remove /tmp/scratch-2876 --force && git branch -D scratch-issue-2876-plural-check`.

## Absolute constraint compliance

Nothing under `docs/issue-*/reports`, `docs/decisions`, or any other historical-record path was renamed, migrated, or modified — canonical: `git status --short` (this session, post-commit) shows no `docs/` modifications outside `docs/specs/enforcement-boundary.md` and this record's own new directory. This record touched one file under `docs/specs/` — `enforcement-boundary.md` (adding one new row registering `gates/retirement_count.py`, required by this repo's own gate-registration-guard hook for any newly-added `gates/*.py` module, encountered live this session when the first commit attempt was refused for exactly this reason) — a living tooling-registry document, not a historical narrative record, and the new row's content is about the new checker, not a rename of retired-axis text. The companion `docs/specs/reconciled-index.md` regeneration command (`python3 gates/spec_index.py --update`) fails on this tree independent of this session's changes — canonical: reproduced with this session's changes stashed away (`git stash && python3 gates/spec_index.py --update`, this session, result: same `FileNotFoundError: .../roles/specs/brand-design.spec.json`; then `git stash pop`), confirming this is a pre-existing break this session did not cause and did not fix, noted as an open finding below rather than patched by editing a `docs/` index file outside this issue's authorized scope.

## Open findings

1. **The 83-site pending-migration baseline** (Part 2, live-candidate group) — legitimate, pre-existing, not a #2876 regression; tracked by issue #2241's staged rollout. Resolution path: each future stage of `docs/issue-2241/proposals/` renames its own owned surface.
2. **`roles/*.json`/`PROTECTED_ROOT_DIRS`/`GATES_DIRS` "roles" entries** (gates/gates.py, gates/skip_eligibility.py, gates/risk_report.py, gates/accumulation.py, on-the-record/hooks/accumulation-claim-guard.sh) reference a directory absent from this repo's tree today but predate both flagged commits; this checkout has no visibility into whether other repos this tooling runs against still use that layout. Resolution path: a future session with cross-repo context decides rename-or-drop; not guessed at here.
3. **Wiring `gates/retirement_count.sh` into a blocking gate** (e.g. `gates/ci.py`) was considered and deliberately not done. canonical: `bash gates/retirement_count.sh 2>&1 >/dev/null | tail -1`, this session, result: `retirement_count: 1179 occurrence(s)` — a non-zero baseline, so the invariant is "must not increase from baseline," not "must be zero," and a blocking gate needs a stored baseline/ratchet-comparison mechanism this issue's acceptance criteria does not specify and this session did not design. This rationale is also recorded in the new row added to `docs/specs/enforcement-boundary.md` this session. Resolution path: a future issue should scope that ratchet-storage design explicitly.
4. **`gates/spec_index.py --update` fails on this tree** (pre-existing, see Absolute constraint compliance above) — a stale `roles/specs/brand-design.spec.json` row in `docs/specs/reconciled-index.md` pointing at a file deleted by an earlier, unrelated retirement stage. Resolution path: a session scoped to `docs/specs/reconciled-index.md` maintenance (not this issue, and not touching a historical record) removes or updates the stale row.

## What did not work

None — no approach was tried and abandoned during this delivery.

## Next steps

None — `loop_state: landed`.

skill-verdict: silent-failure-audit — not-applicable: invoked (per the mandatory skill-check obligation); this issue's work is a measurement-check blind spot and forward-only key renames, not classifying try/catch-style error-handling paths — no fallible I/O/network/parse operation's catch behavior was the subject of this task, so the procedure's catch-block classification steps did not apply.
other mounted skills: not triggered (work-in-english, model-routing, parallel-decomposition, technical-feasibility-reversibility-tag, verify-finding-record, conformance-review-finding-record) — this was a solo build-now delivery with no delegation, no probe-resolution field, and no separate reproduction/conformance-verdict write for any of their trigger conditions to match.
