# Current-state survey — issue #476 round 2 architecture (wiring candidate A)

## Scope

Round 2's product-discovery phase (`docs/issue-476/proposals/discovery-
round2.md`) pre-registered candidate A as primary: a `PreToolUse` `Bash`
hook on `gh pr create`/`gh pr edit`, calling `claim_scan.scan_text()`
inline, warn-only first per H1b. This survey reads the actual chokepoint
this hook must join and the actual constraints on how it may call
`claim_scan`, before the architecture proposal fixes matcher shape, fail
posture, kill switch, and copy-avoidance.

## What exists now (read this session, current commit)

- `on-the-record/hooks/hooks.json`: `PreToolUse` -> `matcher: "Bash"` array
  already runs, in order, `contract-guard.sh`, `pr-preflight.sh`,
  `spec-index-preflight.sh`, `impact-guard.sh` on every `Bash` call. A new
  hook joins this same array as a sibling entry, not a new matcher group --
  `hooks.json`'s existing shape takes an ordered list per matcher.
- `on-the-record/hooks/pr-preflight.sh`: the hook that already fires on
  exactly `gh pr create`/`gh pr edit` (regex `\bgh\s+pr\s+(create|edit)\b`
  against the raw command string), extracts `--body`/`--body-file`
  inline, and is explicitly documented (its own header, read this
  session) as porting `gates/pr_reference.py`'s `check_body` function
  (and `gates/flows.py`'s `_plan_from_body`) inline "rather than
  importing them, because a zero-install hook cannot assume gates/ is on
  sys.path in the consumer repo." Fails open on: parse failure, missing
  python3/gh, non-matching command, absent --body/--body-file, unreadable
  body-file, non-issue-<n>/<role> branch, gh lookup failure.
  `ORCHESTRATE_OFF` kill switch checked first, before any parsing
  (`case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;;
  esac`).
- `on-the-record/hooks/record-claim-guard.sh`: the repo's OTHER pattern
  for reaching a gates/*.py function -- resolves its gates directory
  relative to the hook script's own location (one or two levels up from
  the script), and **fails closed** if that resolution fails. This
  precedent only holds inside this repo's own dev checkout, where
  `on-the-record/` (the shipped plugin tree, per this repo's own
  enforcement-boundary note: "on-the-record/ tree so a consumer session
  can read it zero-install") and `gates/` (this repo's own dev/CI
  tooling, NOT under `on-the-record/`) sit side by side in the same
  checkout. In a consumer repo where on-the-record is installed as a
  marketplace plugin, gates/ has no guaranteed location relative to the
  plugin's install path -- record-claim-guard.sh's relative-path
  resolution is a same-repo convenience, not a zero-install guarantee,
  and its own fail-closed choice is defensible there because it targets a
  cheap-to-retry write (Write|Edit|MultiEdit), not an irreversible act.
- `gates/claim_scan.py`: `scan_text(text: str, repo_targets: set[str] |
  None = None) -> list[Finding]` (line 114), pure-Python, module-level
  regex constants, no subprocess except optionally its own repo-targets
  helper's git call. No hidden state, safe to call inline from a small
  wrapper.
- This repo's own gates-status table (read this session): both
  `claim_scan.py` and `reexecution_gate.py` are listed as CI-supplement,
  "not yet a PreToolUse hook, CI-only where installed" -- unchanged since
  round one; confirms the gap this round closes is real and still open at
  this commit.

## The two competing precedents, and which one governs this hook

`pr-preflight.sh` (irreversible act, gh pr create/edit, ports logic
inline, fails open) and `record-claim-guard.sh` (cheap-retry write, calls
into gates/ by relative path, fails closed) are not two equally available
options -- they differ by blast radius, and this new hook's blast radius
matches pr-preflight.sh's, not record-claim-guard.sh's: it fires on the
exact same gh pr create/gh pr edit command line, before the same
irreversible act. discovery-round2's scout brief already named this
hook's adopt pattern as "pr-preflight.sh's deny-before-effect chokepoint
shape" for the same reason. The architecture decision below follows that
precedent rather than record-claim-guard.sh's, and states explicitly why
the resulting inline port is not a second copy of check logic in the
sense the discovery brief's must-be #1 warns against.

## Named gap this survey must resolve for the proposal

discovery-round2's registered failure signature: "fails quietly if a
session routes the claim through a call shape ... this hook's identical
matcher does not cover -- e.g. gh pr create invoked via a wrapper script,
or the PR body set through gh api directly instead of
--body/--body-file." Read this session: pr-preflight.sh's own regex
(`gh\s+pr\s+(create|edit)`) already fails to match a `gh api
repos/.../pulls -f body=...` call (no "pr create"/"pr edit" substring at
all -- a structurally different gh subcommand, not a synonym the regex
could be widened to catch by adding words), and a wrapper script that
itself shells out to gh pr create fires the hook's matcher on the wrapper
invocation (the Bash tool call is the wrapper's own command line, no "gh
pr create" substring present in it), never on the nested call the wrapper
makes internally (hooks fire per Bash tool invocation, not per subprocess
spawned inside one). Both are real, distinct blind spots this repo's own
existing Bash-matcher hooks (contract-guard.sh on gh pr merge,
pr-preflight.sh on gh pr create/edit) already carry unaddressed -- this
round's proposal cannot silently inherit them without saying so.
