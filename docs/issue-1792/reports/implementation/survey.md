# Survey: role-name convention inventory (issue-1792)

Subject: issue-1792
Upstream: HEAD of issue-1792/implementation at survey time.
canonical: `git rev-parse HEAD` (run in repo root), executed live this session — `7047545b154c6be88b08505395f7f592f64d2576`.

Skip-condition record (scout-directive): scouting (external field sweep) is
skipped — this issue is a mechanical inventory of this repo's own code
(design-research-skip: mechanical, stated in the issue body itself). There
is no design decision open about *what* to build (the issue enumerates all
6 consumers and forbids any convention change); the only open question is
migration ORDER, which is answered from the dependency facts this survey
establishes, not from external exemplars.

## Method

`grep -rn` for the branch/APPROVE regex family and role-name string
construction across `spawn.py`, `gates/`, `on-the-record/hooks/`. Each hit
below carries its own `canonical:` tag naming the exact command/read that
verified it, executed live this session.

## 1. Branch names — `issue-N/<role>`

Four independent regex definitions parse this shape; they are NOT the same
object, which is the core risk this harness must catch (a phase-5 migration
that fixes one and misses another).

- `on-the-record/hooks/approval-gate.sh:106` — `bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)`; extracts `(issue, branch_role)` from the current git branch name via `git rev-parse --abbrev-ref HEAD`. Downstream: `branch_role` gated against the hook's own `role` env (line 111-112: `if role != branch_role: sys.exit(0)`).
  canonical: `sed -n '100,112p' on-the-record/hooks/approval-gate.sh`, executed live this session.
- `on-the-record/hooks/pr-preflight.sh:106` — `bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)`; same shape, independent definition. Downstream: feeds `issue`/`role` used to build the `needle` (site 2 below) and the delegation-scope match.
  canonical: `grep -n "re.match(r\"\^issue-" on-the-record/hooks/pr-preflight.sh`, executed live this session.
- `on-the-record/hooks/contract-guard.sh:185` — `bm = re.match(r"^issue-(\d+)/([\w-]+)$", br.stdout.strip())`; same shape, third independent definition, used to gate the Closes-trailer check to the role's own subject.
  canonical: `grep -n "re.match(r\"\^issue-" on-the-record/hooks/contract-guard.sh`, executed live this session.
- `gates/flows.py:32` — `_BRANCH_RE = re.compile(r"^(issue-[0-9]+)/([a-z0-9-]+)$")`; a FOURTH, distinct definition — character class is `[a-z0-9-]+` here vs. `[\w-]+` (which also matches digits-only, underscore-only, or uppercase) in the hook trio. Used at `gates/flows.py:319` (`m = _BRANCH_RE.match(pr.get("headRefName") or "")`) to key `pr_by_branch[(m.group(1), m.group(2))] = pr` — this is the rsb consumer's own branch-parse site (see section 6).
  canonical: `sed -n '30,33p;315,322p' gates/flows.py`, executed live this session.
- `spawn.py:3115` — `_HEAD_REF_SUBJECT_RE = re.compile(r"^issue-(\d+)/")`; subject-only (no role capture group), a partial/weaker variant of the same shape.
  canonical: `grep -n "_HEAD_REF_SUBJECT_RE" spawn.py`, executed live this session.
- `spawn.py:4513` — `_LEGACY_WORKSPACE_KEY_RE = re.compile(r"^issue-\d+/[^/]+$")`; validates (not extracts) a workspace-index key against the same shape.
  canonical: `sed -n '4508,4514p' spawn.py`, executed live this session.

Emit sites (construct the branch-name string rather than parse it):
`spawn.py:3858` (`branch = f"issue-{issue}/{routed_to}"`), `spawn.py:1530`/`2188` (`subject = f"issue-{issue}"`, paired with role elsewhere to form the same shape), `spawn.py:7601` (`work = work_base / f"{repo_name}-issue-{issue}-{role}"` — the *workspace directory* naming convention, a sibling but distinct string shape, hyphen- not slash-joined).
canonical: `grep -n "f\"issue-{issue}/{" spawn.py` and `grep -n "repo_name}-issue-{issue}-{role}" spawn.py`, executed live this session.

## 2. APPROVE token grammar — `APPROVE issue-N/<role>`

- `on-the-record/hooks/approval-gate.sh:166` — `needle = "APPROVE issue-%d/%s" % (issue, role)`; emits the exact-match string compared against issue-comment bodies at line 168 (`(c.get("body") or "").strip() == needle`).
  canonical: `sed -n '160,170p' on-the-record/hooks/approval-gate.sh`, executed live this session.
- `on-the-record/hooks/approval-gate.sh:176` — `_CITE_RE = re.compile(r"^APPROVE issue-(\d+)/([\w-]+) VIA DELEGATION (\S+)$")`; the standing-delegation citation shape (issue #707), parsed at line 213 (`if int(cm.group(1)) != issue or cm.group(2) != role:`).
  canonical: `sed -n '174,214p' on-the-record/hooks/approval-gate.sh`, executed live this session.
- `on-the-record/hooks/pr-preflight.sh:137` — `needle = "APPROVE issue-%d/%s" % (issue, role)`; independent duplicate of the same emit.
- `on-the-record/hooks/pr-preflight.sh:154` — `_CITE_RE = re.compile(r"^APPROVE issue-(\d+)/([\w-]+) VIA DELEGATION (\S+)$")`; independent duplicate of the delegation-citation regex.
  canonical: `grep -n "needle = \|_CITE_RE" on-the-record/hooks/pr-preflight.sh`, executed live this session.
- `gates/ci.py` (`_approved_roles_on_issue`) — `prefix = f"APPROVE issue-{issue}/"` then `role_token = body[len(prefix):]` when `body.startswith(prefix)` and the comment author is in the approvers set; deliberately issue-wide-any-role rather than role-exact, per its own docstring reasoning (phase is a property of the issue, not the specific PR's role).
  canonical: `grep -n "_approved_roles_on_issue\|APPROVE issue-{issue}/" gates/ci.py`, executed live this session.
- `on-the-record/hooks/contract-guard.sh` — `prefix = "APPROVE issue-%d/" % issue`, `.startswith(prefix)` plus a non-empty-suffix and post-first-commit-timestamp check, gating whether a PR body may legally claim phase-2.
  canonical: `grep -n "APPROVE issue-%d/" on-the-record/hooks/contract-guard.sh`, executed live this session.
- Other files referencing the `APPROVE issue-<n>/<role>` string (construction, docstring citation, or classification): `on-the-record/hooks/stop-gate.sh`, `gates/spawn_on_pr.py`, `spawn.py`, `gates/delegation_metrics.py`, `gates/risk_report.py`, `gates/auto_approval_class.py`, `on-the-record/hooks/delegation-post-gate.sh`.
  canonical: `grep -rln "APPROVE issue" --include=*.py --include=*.sh .` (excluding docs/, test/), executed live this session — file list above is this command's literal output.
- `gates/flows.py:164` — `needle = f"APPROVE {subject}/{role}"`; the rsb consumer's own independent copy inside `_pr_approved()` (see section 6).
  canonical: `sed -n '158,168p' gates/flows.py`, executed live this session.

Two competing APPROVE-match semantics coexist by design: exact full-body
match (`flows.py:164`, `approval-gate.sh`, `pr-preflight.sh`) vs.
prefix-match-any-suffix (`gates/ci.py`, `contract-guard.sh`) — the latter
because issue-level phase state tolerates any approved role, while the
gate hooks need role-exact match.

## 3. approval-gate — `on-the-record/hooks/approval-gate.sh`

This is a distinct consumer from "APPROVE grammar" itself: it is the
PreToolUse hook that gates writes on the parsed result. Sites:

- Lines 100-112 (branch parse, quoted in section 1) — extracts `(issue, branch_role)`, refuses to act unless `role == branch_role` (fails open — `sys.exit(0)` — on mismatch or unparseable branch, per the file's own header comment).
  canonical: `sed -n '1,12p' on-the-record/hooks/approval-gate.sh`, executed live this session.
- Lines 160-170 (needle construction/match, quoted in section 2).
- Lines 174-214 (delegation-citation path, quoted in section 2) — additionally requires a live `DELEGATE <scope> UNTIL <date>` grant matching `scope == "issue-<n>/<role>"`, where `scope` is built from the same `issue`/`role` pair.
  canonical: `sed -n '174,214p' on-the-record/hooks/approval-gate.sh`, executed live this session.
- The hook's own trap deals with any unexpected exit code from the embedded Python by exiting 2 (fail-shut).
  canonical: `sed -n '42,42p' on-the-record/hooks/approval-gate.sh` — `trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT`.

Sibling hooks performing the same class of role-name gating, independently
duplicated rather than shared: `pr-preflight.sh` (gates `gh pr create/edit`)
and `contract-guard.sh` (gates git push / PR-body phase claims) — both
re-implement `^issue-(\d+)/([\w-]+)$` and the approvers.md-line regex
(`^\s*-\s*(\S+)`) as their own copies. `approval-gate.sh`'s own header
comment states this explicitly ("ported inline from pr-preflight.sh's
identical check").
canonical: `sed -n '20,30p' on-the-record/hooks/approval-gate.sh`, executed live this session.

## 4. Board records — `spawn.py:board()` / `docs/issue-N/reports/<role>.md`

canonical: `sed -n '1620,1638p' spawn.py`, executed live this session.
- `spawn.py:1620-1638` (`def board(root)`) — does NOT parse an arbitrary role-name string. It iterates the fixed `ROLES` tuple (`spawn.py:846`) and checks, per subject directory, whether `reports/{r}.md` exists for each named `r` — role identity here is a filename match against a fixed tuple, not a regex extraction from free text.
- `spawn.py:846` — `ROLES = ("product-discovery", "interaction-design", "technical-feasibility", ...)` — the fixed tuple board() iterates.
  canonical: `grep -n "^ROLES\s*=" spawn.py`, executed live this session.
- `spawn.py:1505` (`_front_role(root, subject, roles)`) — consumes the `roles: dict` board() already produced (role name is already a dict key here, not re-parsed from a string) to select the "front" (currently-active) role for a subject.
  canonical: `grep -n "_front_role" spawn.py`, executed live this session — used at `spawn.py:1539` and `gates/flows.py:396`.
- `board()`'s own docstring states its contract directly: "보드를 읽는다. 쓰지 않는다 (protocol.md §1)" ("reads the board. Does not write.") — board records are written by role sessions themselves via the gated `Write` tool, not constructed by this repo's own code.
  canonical: `sed -n '1620,1622p' spawn.py`, executed live this session.

This is the empty-state case the issue's acceptance §1 requires an explicit
row for: board records is a **zero role-name-parse-site consumer** — it
never decodes an unknown role name out of a string; it only tests
membership of a name already known from ROLES against the filesystem.
canonical: `sed -n '1620,1638p' spawn.py`, executed live this session (same read backs both the classification above and this zero-site claim).
Its dependency on the convention is only through the *directory layout*
`docs/issue-N/reports/<role>.md`, which section 1's file-path
constructions (e.g. `spawn.py:7601`'s workspace dir) still assume.

## 5. Watch/roster — `spawn.py` (ROSTER, `active.json`, workspace index)

- `spawn.py:2203` — `ROSTER = STATE_ROOT / "active.json"`; the roster store.
  canonical: `grep -n "^ROSTER = " spawn.py`, executed live this session.
- `spawn.py:5108` (`roster_kill`) — `key = f"issue-{issue}/{role}"`; emit, not parse (issue/role already known as function args).
  canonical: `sed -n '5106,5112p' spawn.py`, executed live this session.
- `spawn.py:4700-4712` (`_live_roster_matches`) — `role = k.rsplit("/", 1)[1]` parses a workspace-index key by splitting on the last `/`, then re-emits `f"issue-{issue}/{role}"` to look up the ROSTER.
  canonical: `sed -n '4700,4712p' spawn.py`, executed live this session.
- `spawn.py:4719` (`_ambiguous_watch_exit`) — `roles = [k.rsplit("/", 1)[1] for k, _ in matches]`; same split-based parse, over a list.
  canonical: `sed -n '4715,4726p' spawn.py`, executed live this session.
- `spawn.py:4727-4759` (`_roster_fallback_entry`) — two sites: `roster.get(f"issue-{issue}/{role}")` (emit, role known) at line 4738, and `re.match(rf"^issue-{issue}/([^/]+)$", k)` at line 4750 (parse — extracts `found_role` from a roster key when role is NOT known, the true "watch without --role" ambiguity-resolution case).
  canonical: `sed -n '4727,4761p' spawn.py`, executed live this session.
- `spawn.py:4762-4798` (`_lookup_roster_entry`) — `key = f"{repo}/issue-{issue}/{role}"` (emit) and `matches = [(k, v) for k, v in idx.items() if k.endswith(f"/issue-{issue}/{role}")]` (line 4798, suffix-match parse against workspace-index keys).
  canonical: `sed -n '4762,4798p' spawn.py`, executed live this session.
- `spawn.py:4576` (workspace-index register) — `key = f"{_repo_identity(work)}/issue-{issue}/{role}"`; emit, the canonical key shape (`<repo>/issue-<n>/<role>`) the parse sites above split apart.
  canonical: `sed -n '4574,4581p' spawn.py`, executed live this session.
- `spawn.py:2312-2330` (`_format_roster_row`) — display formatting keyed by a roster entry's role (role already carried as a dict field, not re-parsed here); feeds `spawn.py ps` output.
  canonical: `sed -n '2312,2330p' spawn.py`, executed live this session.

Downstream: `spawn.py watch`/`spawn.py ps` CLI surfaces, `_self_trigger_respawn`, `roster_watchdog` — session liveness and auto-respawn logic keyed on these role-bearing strings.

## 6. rsb (repo-status-board) — `gates/flows.py`

- `gates/flows.py:32` — `_BRANCH_RE = re.compile(r"^(issue-[0-9]+)/([a-z0-9-]+)$")` (quoted fully in section 1) — a fourth independent branch-shape definition, narrower charset than the hook trio.
- `gates/flows.py:319-321` — `m = _BRANCH_RE.match(pr.get("headRefName") or "")`; `pr_by_branch[(m.group(1), m.group(2))] = pr` — parses every open PR's branch name into `(subject, role)`, the rsb's primary role-name ingestion point.
  canonical: `sed -n '316,322p' gates/flows.py`, executed live this session.
- `gates/flows.py:158-168` (`_pr_approved`) — `needle = f"APPROVE {subject}/{role}"` (line 164, quoted in section 2); independent duplicate of the APPROVE-grammar emit, consuming `subject`/`role` already split out by `_BRANCH_RE`.
- `gates/flows.py:373-411` — `for (subject, role), pr in sorted(pr_by_branch.items())` / `for role, fm in roles.items()`; iterates the `(subject, role)` pairs `_BRANCH_RE` produced, cross-referencing them against `board()`'s `roles` dict (section 4) via `spawn._front_role(root, subject, roles) == role` (line 396) to compute the rsb's "front" role indicator and PR/approval status per row.
  canonical: `sed -n '373,412p' gates/flows.py`, executed live this session.
- `gates/flows.py:88-130` (`_plan_from_body`) — parses `- [ ] step N ... <role>[ ‖ <role2> ...]` checklist lines out of an issue body via `roles = [r.strip() for r in m.group(3).split("‖")]` (line 129); a distinct role-name ingestion shape (issue-body checklist text, not branch/APPROVE) feeding the rsb's per-issue plan/step display.
  canonical: `sed -n '88,131p' gates/flows.py`, executed live this session.

Note on naming:
canonical: `sed -n '1,3p' gates/flows.py`, executed live this session.
`gates/flows.py`'s docstring names its own output the
"상황판(repo-status-board)" (status board) — a repo-internal docstring
label, not a separate module.
canonical: `grep -rn "rsb" --include=*.py --include=*.sh .`, executed live this session — no matches.
No repo-internal module or file is literally named `rsb`. The term
appears in this session's own reading only inside `docs/**/*.md`, including
a citation of an external, separately-installed `rsb.cli` package used for
cross-checking, not code this repo ships.
canonical: `grep -n "rsb.cli" docs/issue-674/reports/implementation.md`, executed live this session.
This survey treats consumer 6 ("rsb status board") as `gates/flows.py`'s
status-board computation — the only repo-internal artifact matching the
issue's description of consumer 6.

## Existing sample/golden data available for the harness

- `on-the-record/hooks/test_approval_gate.py:105-106` — `APPROVED_COMMENTS = [{"body": f"APPROVE {BRANCH}", ...}]` / `UNAPPROVED_COMMENTS`; a real fixture pairing a branch constant with its matching APPROVE comment string, directly reusable as a golden case for consumers 1-3.
  canonical: `sed -n '100,110p' on-the-record/hooks/test_approval_gate.py`, executed live this session.
- `docs/issue-983/reports/implementation.md:79` — a real, merged-record citation of the literal approval comment `APPROVE issue-983/implementation`, usable as a real-repo golden APPROVE string.
  canonical: `grep -n "APPROVE issue-983/implementation" docs/issue-983/reports/implementation.md`, executed live this session.
- `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md:45-46` — cites two real near-miss rsb cases (`APPROVE issue-23/implementation` and a subject/role-swapped variant), reusable as golden *negative* (non-matching) cases.
  canonical: `sed -n '40,58p' docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md`, executed live this session.
- `gates/test_delegation_metrics.py` — real-shaped fixture comments including `"APPROVE issue-707/implementation"` and `"APPROVE issue-707/implementation VIA DELEGATION issue-707/implementation"`.
  canonical: `grep -n "APPROVE issue-707" gates/test_delegation_metrics.py`, executed live this session.
- Repo's own current branch, `issue-1792/implementation`, is itself a live real branch-name sample matching the convention (subject `issue-1792`, role `implementation`).
  canonical: `git rev-parse --abbrev-ref HEAD`, executed live this session — `issue-1792/implementation`.

## Dependency facts for the migration-order proposal

- Consumers 1 (branch names) and 2 (APPROVE grammar) are read by consumer 3 (approval-gate) and consumer 6 (rsb) — both parse branch names via their own independent regex, then independently reconstruct/parse the APPROVE needle. Neither reads the other's output.
- Consumer 5 (watch/roster) depends on consumer 1's *key shape* (`issue-N/role` and `repo/issue-N/role`) but never touches the APPROVE grammar (consumer 2) or the approval-gate hook (consumer 3) — it is process-liveness bookkeeping, orthogonal to approval.
- Consumer 4 (board records) has zero role-name-parse sites (section 4) — it depends only on the ROLES tuple and the `reports/<role>.md` filename shape. Nothing downstream re-derives a role name FROM a board record's frontmatter key.
- Consumer 6 (rsb / `gates/flows.py`) is the most tightly coupled: it calls `spawn._front_role()` directly (cross-module dependency on consumer 4's module, `spawn.py`) and duplicates both the branch regex (consumer 1) and the APPROVE needle (consumer 2) independently.
  canonical: `grep -n "spawn._front_role" gates/flows.py`, executed live this session.
- Consumers 1 and 2 are each independently duplicated across multiple files (branch regex: `approval-gate.sh`, `pr-preflight.sh`, `contract-guard.sh`, `flows.py`; APPROVE needle: `approval-gate.sh`, `pr-preflight.sh`, `flows.py`, plus the prefix-match variants in `gates/ci.py` and `contract-guard.sh`) — a phase-5 sub-issue touching consumer 1 or 2 must enumerate all of its own duplicate sites, not just one file.
  canonical: this document's sections 1-2 (per-site `canonical:` tags above).
