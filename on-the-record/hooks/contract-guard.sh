#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on gh pr merge — issue #441.
#
# Zero-install baseline (contract, not CI-supplement): this script ships
# with the plugin like deliverable-guard.sh; it needs no gates/ checkout in
# the consumer repo, only `gh` on PATH, because the checks it runs
# (ci.py/pr_reference.py/closure_sweep.py single-PR case/landing_readiness.py
# per the proposal's item-1 table, docs/issue-441/proposals/
# 2026-08-07-contract-enforcement-boundary.md) are all read-only `gh`
# lookups against GitHub, not local-checkout diffs.
#
# Scope: intercepts only `gh pr merge` (the delivering act). It folds in
# the phase-2 "Closes/Fixes/Resolves #<issue>" requirement (pr_reference.py
# phase2 path, closure_sweep.py single-PR case's specific violating act) —
# the requirement a consumer without any local install would otherwise
# never see enforced at all. Phase is determined the same way
# gates/ci.py._approved_roles_on_issue does: an `APPROVE issue-<n>/<role>`
# comment from an approvers.md account on the issue means phase-2.
#
# Fail-open by design difference from deliverable-guard.sh: deliverable-guard
# denies WRITES (cheap to re-attempt, high blast radius if wrong-allowed).
# This gates a PR MERGE (expensive to undo, and `gh`/network failures are
# common in sandboxed sessions) — so a lookup failure here is reported and
# passed through rather than blocking an unrelated command. What must never
# happen is silently approving a merge this script positively determined
# violates the contract; that path is the only one that exits 2.
#
# Broker-attach at merge (issue #653, revising #441's original refusal-only
# design): a phase-2 merge missing/wrong 'Closes #<issue>' is no longer
# denied outright. Five same-day recurrences (orchestrator relay, issue #653
# comment) showed the refusal only helps a session capable of correcting
# itself, and that premise doesn't hold in practice. Instead this hook, the
# one broker that actually executes every merge, attaches/corrects the
# trailer itself via `gh pr edit` before allowing the merge — so a decided
# merge never deadlocks on a session that never wrote the trailer. Deny is
# now the fallback: it fires only if the `gh pr edit` write itself fails,
# never as the primary response to a missing trailer.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v gh >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, subprocess, sys

def deny(msg):
    sys.stderr.write("contract-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("CG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

if not re.search(r"\bgh\s+pr\s+merge\b", cmd):
    sys.exit(0)

# Target-repo resolution (issue #443): a `gh pr merge` command may target a
# repo other than this hook process's own cwd, via a leading `cd <path> &&`
# prefix, a `-R`/`--repo owner/repo` flag, or a full PR URL argument. Each
# form is resolved to either a local cwd override (real checkout, full fix)
# or a `-R owner/repo` flag passed straight to `gh` (no local checkout,
# approvers.md unreadable — explicit unreached below).
target_cwd = None
target_repo_flag = None  # "owner/repo" string, used with gh -R when no local checkout

cd_m = re.match(r"^\s*cd\s+(\S+)\s*&&", cmd)
if cd_m:
    target_cwd = cd_m.group(1)

rest = re.split(r"\bgh\s+pr\s+merge\b", cmd, maxsplit=1)[1]

url_m = re.search(r"github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)", rest)
repo_flag_m = re.search(r"(?:-R|--repo)[= ]([^\s/]+/[^\s/]+)", rest)

if url_m:
    pr = url_m.group(2)
    # An explicit repo selector (URL or -R/--repo) always wins over an
    # incidental `cd <path> &&` prefix — `gh` itself honors -R/URL over cwd
    # repo inference, and a `cd` path has no guaranteed correlation to the
    # flagged repo, so any `target_cwd` is discarded here rather than
    # trusted to also be that repo's checkout (issue #443 before-landing
    # hunt: cd+flag combo was silently judging the cd repo and dropping
    # the flag).
    target_cwd = None
    target_repo_flag = url_m.group(1)
elif repo_flag_m:
    num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
    if not num_m:
        sys.exit(0)  # -R/--repo present but no explicit PR number — unreached, same rationale as below
    pr = num_m.group(1)
    target_cwd = None
    target_repo_flag = repo_flag_m.group(1)
else:
    num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
    if not num_m:
        # `gh pr merge` with no explicit number merges the PR for the current
        # branch — can't resolve that without a repo checkout, which this
        # zero-install hook does not assume. Recorded honestly as unreached
        # rather than guessed at.
        sys.exit(0)
    pr = num_m.group(1)

def gh_json(*args):
    extra = ["-R", target_repo_flag] if target_repo_flag else []
    r = subprocess.run(
        ["gh", *args, *extra],
        capture_output=True, text=True, timeout=20, cwd=target_cwd,
    )
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None

pr_data = gh_json("pr", "view", pr, "--json", "body,number,commits,files")
if pr_data is None:
    sys.exit(0)  # gh lookup failed — fail-open per header note, not a verdict
body = pr_data.get("body") or ""

# Round-scoping (issue #577): only an approval comment newer than this PR's
# own head branch's first commit counts as phase-2 for THIS pr — a
# prior-round approval (older than the new round's first commit) must not
# gate a new round's phase-1 proposal PR. Missing/empty commits leaves
# first_commit_at None, which fails open (unchanged from pre-#577 behavior).
commit_dates = [
    c.get("committedDate") for c in (pr_data.get("commits") or [])
    if isinstance(c, dict) and c.get("committedDate")
]
first_commit_at = min(commit_dates) if commit_dates else None

_CLOSES_REF = re.compile(r"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")
_PLAIN_REF = re.compile(r"(?<!\w)#(\d+)")
closes_m = _CLOSES_REF.search(body)
plain_refs = [int(n) for n in _PLAIN_REF.findall(body)]
issue = int(closes_m.group(2)) if closes_m else (plain_refs[0] if plain_refs else None)
if issue is None:
    sys.exit(0)  # no issue reference at all — pr_reference.py's own scope, not this hook's new ground

if target_repo_flag and target_cwd is None:
    # -R/--repo or a full URL with no local `cd` checkout: the target repo
    # is known, but docs/specs/approvers.md for it cannot be read from the
    # local filesystem (zero-install hook, no API-fetch capability — see
    # proposal Rationale). The phase-2 determination needs approvers.md, so
    # this stays an explicit unreached/fail-open exit rather than a guess.
    sys.exit(0)

approvers_path = os.path.join(target_cwd or os.getcwd(), "docs", "specs", "approvers.md")
approvers = set()
if os.path.isfile(approvers_path):
    for line in open(approvers_path, encoding="utf-8"):
        mm = re.match(r"^\s*-\s*(\S+)", line)
        if mm:
            approvers.add(mm.group(1))

comments = gh_json(
    "issue", "view", str(issue), "--json", "comments",
    "-q", "[.comments[] | {body, author, createdAt}]",
) or []
prefix = "APPROVE issue-%d/" % issue
phase2 = any(
    (c.get("body") or "").strip().startswith(prefix)
    and c.get("author", {}).get("login") in approvers
    and (c.get("body") or "").strip()[len(prefix):]
    and (not first_commit_at or c.get("createdAt", "") > first_commit_at)
    for c in comments
)
if not phase2:
    sys.exit(0)  # phase-1 PR: no closing-keyword obligation (pr_reference.py phase1 path)

# Content-based phase-2 gate (issue #741): the round-scoping `phase2` bool
# above is trivially true for ANY same-round approval, including a
# docs-only phase-1 proposal PR — approval by definition postdates
# phase-1's first commit on a shared branch. A second, independent
# condition confirms this PR's own diff is actually phase-2-shaped before
# attaching/requiring Closes, using the same two path patterns
# approval-gate.sh already gates writes on (src/tests? path, or the
# acting role's own exact record file).
files = [
    f.get("path") for f in (pr_data.get("files") or [])
    if isinstance(f, dict) and f.get("path")
]
is_src_test = any(re.search(r"(^|/)(src|tests?)/", f) for f in files)

role = None
try:
    br = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, timeout=20, cwd=target_cwd or os.getcwd(),
    )
    if br.returncode == 0:
        bm = re.match(r"^issue-(\d+)/([\w-]+)$", br.stdout.strip())
        if bm and int(bm.group(1)) == issue:
            role = bm.group(2)
except (OSError, subprocess.SubprocessError):
    role = None  # unreached: git ships wherever contract-guard.sh does

is_record = role is not None and (
    "docs/issue-%d/reports/%s.md" % (issue, role) in files
)

if not (is_src_test or is_record):
    sys.exit(0)  # approved but this PR's own diff isn't phase-2-shaped (issue #741)

if not closes_m or int(closes_m.group(2)) != issue:
    if closes_m:
        old_num = closes_m.group(2)
        match_text = closes_m.group(0)
        fixed_text = match_text[: len(match_text) - len(old_num)] + str(issue)
        new_body = body[: closes_m.start()] + fixed_text + body[closes_m.end():]
    else:
        sep = "\n\n" if body.strip() else ""
        new_body = body + sep + f"Closes #{issue}"

    extra = ["-R", target_repo_flag] if target_repo_flag else []
    edit = subprocess.run(
        ["gh", "pr", "edit", pr, "--body", new_body, *extra],
        capture_output=True, text=True, timeout=20, cwd=target_cwd,
    )
    if edit.returncode != 0:
        deny(f"PR #{pr} merges against a phase-2 issue (#{issue}) with no "
             f"'Closes #{issue}' (or Fixes/Resolves) in its body, and the "
             f"broker's attempt to attach/correct it via `gh pr edit` "
             f"failed ({(edit.stderr or '').strip()}). Denied before the "
             f"merge executes.")
    sys.exit(0)
PY

CG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
