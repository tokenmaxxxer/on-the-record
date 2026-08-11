#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on a `git commit` staging a
# done/works/requirement-met claim citing `live-fire: <hook or gate path>
# — result: allow|deny|log` -- issue #914 step 2, mechanism (c). General
# done-claim gate that COMPOSES mechanism (a) (acceptance-command-real-
# run-guard.sh) and mechanism (b) (live-fire-test-guard.sh) instead of
# duplicating either: (b) already forces a newly-staged gate/hook to
# carry a live-fire test shaped correctly at introduction time; (a)
# already re-runs a target's acceptance command at claim time. This
# guard supplies the (c) half of #914's design (artifact type 3, phase-1
# proposal docs/issue-914/proposals/2026-08-12-standing-real-build-and-
# use-verification.md) for the plugin gate/hook artifact type: it
# actually EXECUTES the live-fire test a `live-fire:` citation points at,
# the same way mechanism (a) actually executes the acceptance command an
# `acceptance:` citation points at -- turning #892's "citation LOOKS like
# a run" into "a real live-fire (b) run actually happened, right now,
# for this claim", not merely that a live-fire test exists in the
# required shape.
#
# Sibling to gate-registration-guard.sh / live-fire-test-guard.sh /
# acceptance-command-real-run-guard.sh on the same `git commit`
# interception point.
#
# Trigger: any staged (`A`/`M`, or the destination side of `R`/`C`) file
# whose staged content contains a `live-fire: <path> — result:
# allow|deny|log` line.
#
# For each such citation:
#   - the cited path must be a `on-the-record/hooks/*.sh` or `gates/*.py`
#     module (mechanism (b)'s two artifact shapes) that exists in the
#     staged tree or on disk;
#   - the corresponding live-fire test file is derived with the exact
#     same slug rule live-fire-test-guard.sh already uses
#     (`on-the-record/hooks/test_<slug>.py` for a hook script,
#     `gates/test_<stem>.py` for a gate module) -- missing test file is
#     refused;
#   - that test file is then actually EXECUTED via `python3 -m pytest -q`
#     (bounded timeout) against the real current working tree; a
#     nonzero exit refuses the commit -- a `live-fire:` citation that
#     does not currently pass its own live-fire test is not a real
#     verification, whatever the claim says.
#
# `result: log` (the third mechanism-(b) outcome shape, no allow/deny
# exit-code pair to compare against) is accepted identically to
# allow/deny for the purposes of this guard: this guard checks that the
# cited live-fire test itself passes right now, not which of the three
# outcome labels was written -- the label is provenance, the pytest run
# is the verification.
#
# Where NEITHER an `acceptance:` (mechanism a) nor a `live-fire:`
# (mechanism b) citation backs a done/works/requirement-met claim, this
# guard does not itself refuse -- #892's `outcome_claim_citation_check`
# (gates/record_lint.py, called from record-claim-guard.sh) already
# requires an executed-live citation of SOME accepted shape or a
# `UNMEASURED-with-reason` degrade; this guard only strengthens the two
# shapes it recognizes (acceptance/live-fire) from "shape accepted" to
# "actually re-run this turn", never re-implements the presence check
# #892 already owns.
#
# Escape hatch: commit-message trailer `Live-fire-recheck-N/A: <reason>`
# for a citation that genuinely cannot be re-run at commit time (mirrors
# acceptance-command-real-run-guard.sh's `Acceptance-recheck-N/A:`
# convention).
#
# Fails open on any environment gap (missing python3/pytest/git, not a
# `git commit`, no staged `live-fire:` citation, cited module/test
# missing entirely -- refused as a positive determination, not an
# environment gap). Fails closed only on a positively-determined
# missing/failing live-fire test.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }
command -v git >/dev/null 2>&1 || { trap - EXIT; exit 0; }

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys

def deny(msg):
    sys.stderr.write("live-fire-claim-real-run-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("LFCRG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)
if "git" not in tokens or "commit" not in tokens:
    sys.exit(0)

if re.search(r"(?im)^\s*Live-fire-recheck-N/A\s*:\s*\S", cmd):
    sys.exit(0)

cwd = e.get("cwd") or os.getcwd()

try:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                        capture_output=True, text=True, timeout=20, cwd=cwd)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
repo_root = r.stdout.strip()
if not repo_root:
    sys.exit(0)

try:
    r = subprocess.run(["git", "diff", "--cached", "--name-status"],
                        capture_output=True, text=True, timeout=20, cwd=repo_root)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)

staged = set()
for line in r.stdout.splitlines():
    if not line.strip():
        continue
    parts = line.split("\t")
    if len(parts) < 2:
        continue
    status, path = parts[0], parts[-1]
    if status == "D":
        continue
    staged.add(path)

if not staged:
    sys.exit(0)


def read_staged(rel_path):
    rr = subprocess.run(["git", "show", ":" + rel_path],
                         capture_output=True, timeout=20, cwd=repo_root)
    if rr.returncode != 0:
        return None
    try:
        return rr.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def path_exists(rel_path):
    if rel_path in staged:
        return True
    return os.path.isfile(os.path.join(repo_root, rel_path))


_LIVE_FIRE_CITE_RE = re.compile(
    r"live-fire:\s*(\S.+?)\s*(?:—|--|-)\s*result:\s*(allow|deny|log)\b",
    re.IGNORECASE)

citations = []  # (record_path, cited_path)
for path in sorted(staged):
    text = read_staged(path)
    if text is None:
        continue
    for m in _LIVE_FIRE_CITE_RE.finditer(text):
        citations.append((path, m.group(1).strip().strip("`")))

if not citations:
    sys.exit(0)

problems = []
for record_path, cited_path in citations:
    if cited_path.startswith("on-the-record/hooks/") and cited_path.endswith(".sh") \
            and "/" not in cited_path[len("on-the-record/hooks/"):]:
        name = os.path.basename(cited_path)
        slug = re.sub(r"[^0-9a-zA-Z]+", "_", name[:-3]).strip("_")
        test_path = f"on-the-record/hooks/test_{slug}.py"
    elif cited_path.startswith("gates/") and cited_path.endswith(".py") \
            and "/" not in cited_path[len("gates/"):]:
        name = os.path.basename(cited_path)
        stem = name[:-3]
        test_path = f"gates/test_{stem}.py"
    else:
        problems.append(
            f"{record_path}: cites `live-fire: {cited_path} — result: ...` "
            "but that path is not a recognized on-the-record/hooks/*.sh or "
            "gates/*.py module -- cannot resolve its live-fire test"
        )
        continue

    if not path_exists(cited_path):
        problems.append(
            f"{record_path}: cites `live-fire: {cited_path} — result: ...` "
            f"but {cited_path} does not exist in the staged tree or on disk"
        )
        continue
    if not path_exists(test_path):
        problems.append(
            f"{record_path}: cites `live-fire: {cited_path} — result: ...` "
            f"but its live-fire test {test_path} does not exist -- cannot "
            "confirm the claimed result this turn"
        )
        continue

    try:
        run = subprocess.run(
            ["python3", "-m", "pytest", "-q", test_path],
            cwd=repo_root, capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        problems.append(
            f"{record_path}: live-fire test {test_path} did not complete "
            "within 180s -- cannot confirm the claimed result this turn; "
            "add a `Live-fire-recheck-N/A: <reason>` commit trailer if it "
            "is genuinely too slow to re-run at commit time"
        )
        continue
    except OSError as ex:
        problems.append(
            f"{record_path}: live-fire test {test_path} failed to start "
            f"({ex}) -- cannot confirm the claimed result"
        )
        continue

    if run.returncode != 0:
        problems.append(
            f"{record_path}: cites `live-fire: {cited_path} — result: ...` "
            f"but its own live-fire test {test_path} just exited "
            f"{run.returncode} when actually re-run -- the claim does not "
            "match a real re-execution of the cited live-fire test"
        )

if problems:
    deny(
        "a done/works/requirement-met claim citing a live-fire (mechanism "
        "b) marker must be backed by an actual re-run of that marker's own "
        "live-fire test, right now (issue #914 mechanism c):\n"
        + "\n".join(problems)
    )
PY

LFCRG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
