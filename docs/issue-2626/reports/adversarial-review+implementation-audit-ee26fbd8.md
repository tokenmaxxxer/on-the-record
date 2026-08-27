---
issue: 2626
role: adversarial-review+implementation-audit-ee26fbd8
author: adversarial-review+implementation-audit-ee26fbd8
skills: adversarial-review (skill-repository(297e350)), implementation-audit (skill-repository(297e350))
loop_state: landed
upstream:
  - path: same-commit
    sha: same-commit
---

# issue-2626 — adversarial-review+implementation-audit-ee26fbd8 record

skill-verdict: adversarial-review — applied: invoked; canonical: Skill tool call issued this turn (see this session's own transcript) — used its evaluator framing (blind to builder intent, incentivized to find survival, every finding cites file:line) for each of 7 structurally-independent audit agents, none of which received this session's running hypotheses.
skill-verdict: implementation-audit — applied: invoked; canonical: Skill tool call issued this turn (see this session's own transcript) — treated issue #2626's Scope list as the falsifiable-claims list (Step A1 already done by the issue author) and the two live repo checkouts as the implementation files (Step A2); derived: 7 Agent-tool dispatches below, each returning a verbatim PASS|FAIL|UNVERIFIABLE classification with command+output evidence (Steps 2-4).

## What was done

Audited every removal claim named in issue #2626's Scope against current `main` of both `tokenmaxxxer/on-the-record` (this checkout) and `tokenmaxxxer/tokenmaxxxer-core` (checked out at `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core`, both clean, both up to date with origin/main at audit time — canonical: `git status`/`git remote -v` run directly in this session at audit start). Seven structurally-independent evaluator agents (Agent tool, no shared context with this session's reasoning — adversarial-review protocol) each answered the #2548 three-question test with real commands and real output. Built a repeatable checker (`scripts/audit_removal_claim.py`, same-commit) mechanizing the same three questions, and ran it against one real claim and two synthetic fixtures.

canonical: this session's 7 Agent-tool dispatches (task-notifications received in-session, agent ids ac18f2a6f9b9a3f25, a34cda895ccf897ff, a8c944a0946f41bf1, a1d4d53a7b06ac6eb, abbae0fd45612a1c0, ab04422c7fe5d48e8, aa8f6aad4dc647f2a) are the source for every cell below; each agent's own EVIDENCE block quotes the exact command and output it ran. Bare counts below (write_scope 43/38-of-44) were independently re-derived in this session: `derived: grep -c '"write_scope":' spawn_roles.json` → `43`; `derived: python3 -c "import json;d=json.load(open('spawn_roles.json'));print(sum(1 for r in d.values() if isinstance(r.get('record_spec'),dict) and r['record_spec'].get('write_scope')))"` → `38`.

### Claim-by-claim verdict table

| # | Claim (issue) | Q1 gone? | Q2 reshaped elsewhere? | Q3 still branches on closed set? | Verdict |
|---|---|---|---|---|---|
| 1 | `PR_TRIGGERED_RECORD_KINDS` + `_filter_execution_observation` skip-eligibility exemption (#2615) | yes — `derived: grep -rln --include=*.py "PR_TRIGGERED_RECORD_KINDS" .` → empty (0 hits; 9 historical `docs/**/*.md`-only mentions) | **yes** — `git show 483d106d~1:gates/spawn_on_pr.py` → `PR_TRIGGERED_RECORD_KINDS = ("execution-observation", "conformance-review")`; `gates/spawn_on_pr.py:50` → `AUTO_SPAWN_ROLES = ("execution-observation", "conformance-review")`, byte-identical tuple | **yes** — `gates/spawn_on_pr.py:140-182` `applicable_record_kinds()`: `matched = kind_field if kind_field in kinds else (name if name in kinds else None)` against `AUTO_SPAWN_ROLES`, live-called from `missing_verification()` (line 366) and `spawn_missing_for_pr()` (line 746) | **FAIL** (partial — the merge-gate exemption `_filter_execution_observation` is genuinely deleted, 0 live hits either repo; the closed-set tuple survived, renamed, repurposed to auto-spawn selection) |
| 2 | `--role` CLI selector renamed to `--session` (#2592/#2595) | yes — `spawn.py` has no `add_argument("--role", ...)`; `spawn.py:2071-2073` hard-exits naming `--session` | no — `--session` resolves against a live, dynamic workspace index (`events.py:601-653`, string match on already-spawned sessions), not a closed roster; `--skills` path assigns identity as `f"{skill_slug}-{new_lease_disambiguator()}"` (`spawn.py:2116-2119`), machine-generated | no — `derived: python3 -c "import spawn; print(hasattr(spawn,'ROLES'))"` → `False`; `role_data()`/`spawn_roles.json` used once, informationally, to print the role catalog when no positional arg given — not a validation gate on `--session` | **PASS** — canonical: agent a34cda895ccf897ff's own live shell run, `python3 spawn.py --role foo` → exit 1 naming `--session`, quoted verbatim in its EVIDENCE block |
| 3 | `write_scope` removed entirely (#2559) | **no** — `derived` counts above: 43 literal `"write_scope":` keys remain in `spawn_roles.json`; 38 of 44 roles carry a non-empty `record_spec.write_scope` array that is byte-for-byte identical to the top-level `write_scope` glob list `git show 3d7bb6dc -- spawn_roles.json` shows deleted from each role | data-level only — no code reads `record_spec["write_scope"]` (0 hits per agent a8c944a0946f41bf1's grep); `gates/scope_adherence.py`'s "scope" is a different, non-role-derived, per-issue opt-in mechanism | **no live enforcement** — `gates/gates.py`/`gates/ci.py` have no `role_scope()`/`_roster_write_scope()` (`derived: grep -n "def role_scope\|def _roster_write_scope" gates/gates.py` → empty); `delegated-judgment-gate.sh`'s `write_scope` mentions are all `#`-comment history | **FAIL** — canonical: agent a8c944a0946f41bf1's EVIDENCE block, quoting `git show 3d7bb6dc -- spawn_roles.json` and `protocol.md:147-154` (still describes the deleted mechanism as live, factually false as of HEAD) |
| 4 | `spawn.ROLES` / `_ROLE_SKILLS` / post-role identity model (#2548, core #331/#328) | yes — `hasattr(spawn,'ROLES')`/`hasattr(spawn,'_ROLE_SKILLS')` both `False` (canonical: agent a1d4d53a7b06ac6eb live-ran this) | operator's named example (`skill_lease_name(role, ...)`) **refuted** — `derived: grep -rni "skill_lease_name" .` → 0 hits in either repo, any spelling. The real `_ROLE_SKILLS` successor, `resolve_role_family_source()` (`skills.py:402-442`, quoted verbatim in agent a1d4d53a7b06ac6eb's EVIDENCE), scans the live skill-repo directory for a `f"{role}-"` prefix, fail-**soft** on unknown role — a genuinely different mechanism, not a disguised table. But `core/hooks/record-fields-gate.sh:168-179` (`ROLE_TO_KIND`, 10-entry literal dict) is untouched and is exactly the pattern claimed retired | **yes, live** — `core/hooks/record-fields-gate.sh:346`: `if role in ("coding", "implementation"):`; `:413`: `kind = ROLE_TO_KIND.get(role)`, driven by live `CLAUDE_ROLE`/`RF_ROLE`; self-admitted by core commit 71234db's own message ("ROLE_TO_KIND dict and role-in-tuple check ARE a genuine closed-set validation... Reported, not fixed") | **FAIL** — canonical: agent a1d4d53a7b06ac6eb's EVIDENCE block quoting `record-fields-gate.sh:63,118,168-179,346,413` and core commit 71234db's message verbatim |
| 5 | 44-entry catalog / `spawn_roles.json` (#2610, verified against current `main`) | **no** — `find . -iname "spawn_roles.json"` → `./spawn_roles.json` still exists as one file; `python3 -c "import json;print(len(json.load(open('spawn_roles.json'))))"` → `44`; no `roles/` directory exists anywhere | not needed — it's the original, unmoved structure: `gates/gates.py:47-51` `_role_cfg(role)` does `json.loads(...)[role]`, docstring: "단일 사실 소스... 모르는 role 은 KeyError" | **yes** — same `_role_cfg` KeyError lookup gates 12+ live consumers listed verbatim in agent abbae0fd45612a1c0's EVIDENCE (`spawn.py`, `gates/gates.py`, `gates/roles_due.py`, `gates/scope_adherence.py`, `gates/closure_sweep.py`, `gates/spawn_on_pr.py`, `gates/patrol_wiring.py`, `consult.py`, `pipeline.py`, plus 4 hook `.sh` files) | **FAIL — open, unresolved on main.** Correction to the operator's own issue text: `canonical: gh pr view 2625 --json state,mergedAt,mergeCommit` (run by agent abbae0fd45612a1c0) → `{"state":"CLOSED","mergedAt":null,"mergeCommit":null}` — PR #2625 (the alleged glob-of-44-files reshape) was **never merged**; its own closing review comment names exactly this audit's failure pattern and rejected it. The un-reshaped original 44-entry file is what actually sits on `main` |
| 6 | retired spawn forms: role-positional / bare-task (#2572, verified against current `main`) | effectively yes — canonical: agent ab04422c7fe5d48e8's live run, `python3 spawn.py implementation "some task" --issue 9999 --dry-run` → exits 1 naming issue #2572; argparse positional slot is reused, not deleted | no fallback reincarnation — `--skills`-absent invocations exit before skill-resolution code runs; surviving BM25 task-text matcher only runs additively atop an already-supplied `--skills` list; per #2507 the prior fixed role→category table (`_cross_family_candidate_corpus`) literally does `del role` | no live caller constructs the old form internally (checked `gates/*.py`, `roster.py`, `watchdog.py`, `checkpoint.py`, `lifecycle.py`, hook scripts — agent's own search) | **PASS** (minor dead-code caveat: `pipeline.py`'s `_admission_check_degenerate_task` still prints "did you mean: spawn.py {role} ...\"" in the retired shape, but unreachable since `--skills` mandates `--issue` up front) |
| 7 | core hook/config role-axis removals (on-the-record #2537/#2538/#2545/#2560 map to core issue-331 rounds 1 & 2 and issue-327 — `derived: git log --oneline --all \| grep -iE "2537\|2538\|2545\|2560"` in the core checkout → empty, confirmed by agent aa8f6aad4dc647f2a) | yes for each of the 3 core commits individually — canonical: agent aa8f6aad4dc647f2a's EVIDENCE quoting `citation-gate.sh`/`facet-keyword-gate.sh` (0 `CLAUDE_ROLE` reads), `ordering-gate.sh` (`ROLES`→`MECHANISMS`, 0 identity reads), `gh-guard.sh:40`/`approval-gate.sh:86` (`TOKENMAXXXER_SPAWNED` OR-migration, live) | yes, `ordering-gate.sh` reshape is disclosed and genuinely non-identity (header comment quoted verbatim in agent's EVIDENCE: "static dispatch list matched by each mechanism's own file_path/command, never a validated identity axis") | see claim 4 — same `record-fields-gate.sh` survivor, plus a second, previously-unaudited instance: `core/hooks/record-shape-gate.sh:346-348` reads `PG_ROLE` against `record-shape-config.json` (~40+ role-keyed dict) — shape-identical to the eliminated pattern, but documented as a deliberate non-goal in `docs/issue-331/reports/implementation.md:471,494` ("kept") | **PASS for the 3 audited commits individually, FAIL for the "collectively removed" framing** — same root cause and same open tracking issue (core #331) as claim 4 |

`derived:` count of the Verdict column above — 3 PASS (rows 2, 6, and row 7's 3 individually-audited commits), 4 FAIL (rows 1, 3, 4, 5). No claim was UNVERIFIABLE — all 7 got a determinate verdict backed by executed evidence quoted above.

### Repeatable checker (acceptance bullet 3)

`scripts/audit_removal_claim.py` (same-commit) mechanizes the same three-question test from a JSON claim spec (`removed_names`, `member_samples` — known elements of the old closed set, `min_coloc`). It emits `VERIFIED_ABSENT`, `RESHAPE_DETECTED`, or `COULD_NOT_DETERMINE` — never a bare pass on missing data. Run against real claim 1 and two synthetic fixtures (one deliberately reshaped, not told the answer; one genuinely clean):

acceptance: `python3 scripts/audit_removal_claim.py <claims-file> --root <repo>` — result:
```
$ python3 scripts/audit_removal_claim.py /tmp/claims_demo.json --root .
=== PR_TRIGGERED_RECORD_KINDS (#2615, real) ===
verdict: RESHAPE_DETECTED
detail: closed set reconstructed in: [('gates/spawn_on_pr.py', 2)]

$ python3 scripts/audit_removal_claim.py /tmp/claim_fixture_reshaped.json --root /tmp/fixture_reshape_demo
=== OLD_ROLE_TABLE (deliberately reshaped fixture) ===
verdict: RESHAPE_DETECTED
detail: closed set reconstructed in: [('new_module.py', 3)]

$ python3 scripts/audit_removal_claim.py /tmp/claim_fixture_clean.json --root /tmp/fixture_clean_demo
=== OLD_ROLE_TABLE (clean control, genuinely absent) ===
verdict: VERIFIED_ABSENT
detail: name gone; no co-located member-set reconstruction; no live closed-set branch found
```
canonical: the three command blocks immediately above are this session's own executed output, run directly against the fixture's deliberately-reshaped `NEW_TABLE = {"alpha-role":1,"beta-role":2,"gamma-role":3}` (renamed from `OLD_ROLE_TABLE`, same three members) at `/tmp/fixture_reshape_demo/new_module.py` and the clean control at `/tmp/fixture_clean_demo/mod.py`. The tool caught the fixture's reshape via the same code path (co-located member strings in a non-doc/non-test file) that caught the real #2615 case, and did not false-positive on the clean control.

## Why

Session-separation per adversarial-review: 7 evaluator agents received only the claim text and the two repo checkouts — never this session's running hypotheses or the operator's stated examples (`skill_lease_name`, the #2625 characterization). This mattered concretely: agent a1d4d53a7b06ac6eb independently found `skill_lease_name` does not exist at all, and agent abbae0fd45612a1c0 independently found PR #2625 was rejected, not merged — both corrections to the operator's own issue text, arrived at without being told to look for them.

## Upstream basis

- Issue #2626 (Scope, acceptance, #2548 three-question test) — `gh issue view 2626`, same-commit.
- `tokenmaxxxer/on-the-record` @ `main` (this checkout, `origin/main`-current at audit start; no code changes made to it by this session beyond `scripts/audit_removal_claim.py` — audit only, per the issue's explicit "do not fix what you find").
- `tokenmaxxxer/tokenmaxxxer-core` @ `main` (clean, `origin/main`-current, read-only).
- `scripts/audit_removal_claim.py` — new file, same-commit.

## Open findings

1. **`AUTO_SPAWN_ROLES` reshape (claim 1) has no tracking issue.** This role session cannot file GitHub issues — `canonical: gh issue create --repo tokenmaxxxer/on-the-record ...` attempted in this session, refused by `gh-guard: issues are the user's requirement backlog, user-authored only (contract v3 s9) — no role touches them`. Drafted title/body is at `/tmp/followup_issue_body.md` in this session's environment for the operator to file directly; full evidence is in claim 1's table row above regardless.
2. **`write_scope` data survival (claim 3) has no tracking issue.** Same filing restriction applies (same refusal, same session). Evidence is in claim 3's table row above.
3. **Claims 4 and 5's failures already have open tracking issues** — no new filing needed: core issue #331 (self-scoped by its own retiring commit's message as "Advances #331", not closed, for the `record-fields-gate.sh` survivor) and on-the-record issue #2610 (open, targets exactly the `spawn_roles.json` closed-set catalog found still live). This audit's evidence should be attached to those rather than duplicated into new issues.
4. **`write_scope`'s live-enforcement path is genuinely gone** (claim 3's Q3 is clean) — what survives is inert data plus stale docs, not a functioning bypass; this is why claim 3 got its own row instead of being folded into claim 5.

## Next steps

None — audit and report only, per the issue's explicit instruction not to remediate mid-audit. The operator should: (a) file the two follow-up issues named in Open findings 1-2 using the drafted body at `/tmp/followup_issue_body.md`, (b) decide whether `resolve_role_family_source`'s fail-soft prefix-scan (claim 4) is an acceptable permanent design, and (c) use `scripts/audit_removal_claim.py` for the next claimed removal.
