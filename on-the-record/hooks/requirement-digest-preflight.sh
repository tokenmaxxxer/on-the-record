#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on `docs/specs/requirements.md`
# drift — issue #930 (northpole req#6). Mirrors spec-index-preflight.sh's
# staged-content-vs-index-content shape, applied to the requirement digest
# instead of the reconciled spec index.
#
# issue #930 after-proposal hunt: a naive port of spec-index-preflight.sh's
# staged-only detection (`git diff --cached --name-only`, evaluated before
# the intercepted command runs) lets `git commit -a`/`-am` bypass the check
# entirely — `-a` stages tracked changes as part of the commit's own
# execution, so the file never appears in this hook's pre-run cached-diff
# snapshot. This hook closes that gap: when the intercepted command's
# tokens include `-a`/`--all`/`-am` (or any bundled short flag containing
# `a`, e.g. `-am`), detection also diffs the working tree against HEAD for
# `docs/specs/requirements.md`, not staged-only.
#
# Fail-open by design, same contract as spec-index-preflight.sh: any
# environment gap exits 0 rather than blocking an unrelated commit. What
# must never happen is silently allowing a commit this script positively
# determined changed `requirements.md` without a matching digest
# regeneration in the same effective change set; that path exits 2.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys
from pathlib import Path

# Zero-install baseline (same contract as spec-index-preflight.sh, issue
# #459's comment on this file): this hook ships with the plugin and must
# not require a `gates/` checkout in the consumer repo. The parse/render
# logic is ported inline from gates/requirement_digest.py's `parse()`/
# `render()` rather than imported — keep the two in sync by hand; a repo
# that *does* carry gates/requirement_digest.py is exercised the same way
# via gates/test_requirement_digest.py and gates/ci.py's backstop call.
_REQ_HEADING = re.compile(r"^##\s+(R\d+)\s*$")
_REQ_FIELD = re.compile(r"^([a-z_]+):\s*(.*)$")
_REQ_REQUIRED = ("quote", "source_issue", "check", "status")
_MAX_PARAPHRASE = 120


def _parse(text):
    entries = []
    current_id = None
    current = {}

    def flush():
        if current_id is None:
            return
        if all(f in current for f in _REQ_REQUIRED):
            entries.append({"id": current_id, **current})

    for line in text.splitlines():
        m = _REQ_HEADING.match(line)
        if m:
            flush()
            current_id, current = m.group(1), {}
            continue
        m = _REQ_FIELD.match(line.strip())
        if m and current_id is not None:
            current[m.group(1)] = m.group(2).strip()
    flush()
    return entries


def _paraphrase(quote):
    q = " ".join(quote.split())
    if len(q) <= _MAX_PARAPHRASE:
        return q
    return q[: _MAX_PARAPHRASE - 1].rstrip() + "…"


def _render(entries):
    lines = [
        "# Requirement Digest (auto-generated — do not hand-edit)",
        "",
        "Source: `docs/specs/requirements.md`. Regenerate: "
        "`python3 gates/requirement_digest.py --update`.",
        "",
    ]
    live = [e for e in entries if e.get("status") != "stale"]
    if not live:
        lines.append("(no live requirements)")
    for e in live:
        lines.append(
            f"- {e['id']}: {_paraphrase(e['quote'])} [{e['status']}] "
            f"(source: #{e['source_issue']})"
        )
    lines.append("")
    return "\n".join(lines)


def deny(msg):
    sys.stderr.write("requirement-digest-preflight: %s\n" % msg)
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

try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)
if "git" not in tokens or "commit" not in tokens:
    sys.exit(0)

# issue #930: `-a`/`--all`/any bundled short-flag token containing `a`
# (e.g. `-am`) stages tracked-file changes as part of the commit itself —
# those never show up in a pre-run `git diff --cached` snapshot.
commit_tokens = tokens[tokens.index("commit") + 1:]
stages_all = any(
    t == "--all" or (t.startswith("-") and not t.startswith("--") and "a" in t[1:])
    for t in commit_tokens
)

REGISTRY_REL = "docs/specs/requirements.md"
DIGEST_REL = "docs/specs/requirement-digest.md"

cwd = os.getcwd()
if not os.path.isfile(os.path.join(cwd, REGISTRY_REL)):
    sys.exit(0)

try:
    r = subprocess.run(["git", "diff", "--cached", "--name-only"],
                       capture_output=True, text=True, timeout=20, cwd=cwd)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
staged = set(line.strip() for line in r.stdout.splitlines() if line.strip())

registry_touched = REGISTRY_REL in staged
if not registry_touched and stages_all:
    try:
        wr = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", REGISTRY_REL],
                            capture_output=True, text=True, timeout=20, cwd=cwd)
    except (OSError, subprocess.SubprocessError):
        sys.exit(0)
    registry_touched = wr.returncode == 0 and bool(wr.stdout.strip())

if not registry_touched:
    sys.exit(0)

# 실제로 랜딩될 requirements.md 내용을 구해 기대 digest 를 계산한다:
# staged 면 인덱스의 blob, `-a` 로만 잡히는 경우면 워킹트리 내용.
if REGISTRY_REL in staged:
    show = subprocess.run(["git", "show", ":" + REGISTRY_REL],
                          capture_output=True, timeout=20, cwd=cwd)
    reg_text = show.stdout.decode("utf-8", errors="replace") if show.returncode == 0 else None
else:
    try:
        reg_text = Path(cwd, REGISTRY_REL).read_text(encoding="utf-8", errors="replace")
    except OSError:
        reg_text = None
if reg_text is None:
    sys.exit(0)

expected = _render(_parse(reg_text))

digest_will_land = DIGEST_REL in staged or stages_all
if not digest_will_land:
    deny(f"staged/working changes touch {REGISTRY_REL} but {DIGEST_REL} is "
         f"not part of this commit. Regenerate with "
         f"`python3 gates/requirement_digest.py --update`, stage it, and "
         f"retry the commit.")

if DIGEST_REL in staged:
    show = subprocess.run(["git", "show", ":" + DIGEST_REL],
                          capture_output=True, timeout=20, cwd=cwd)
    actual = show.stdout.decode("utf-8", errors="replace") if show.returncode == 0 else None
elif stages_all:
    try:
        actual = Path(cwd, DIGEST_REL).read_text(encoding="utf-8", errors="replace")
    except OSError:
        actual = None
else:
    actual = None

if actual is None or actual != expected:
    deny(f"{DIGEST_REL} does not match the {REGISTRY_REL} content this "
         f"commit would land. Regenerate with "
         f"`python3 gates/requirement_digest.py --update`, stage it, and "
         f"retry the commit.")
PY

CG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
