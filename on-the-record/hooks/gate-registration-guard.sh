#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on a newly-staged gate/hook
# module with no matching row in docs/specs/enforcement-boundary.md (and,
# for a new on-the-record/hooks/*.sh file, docs/specs/generated-paths.md)
# — issue #759.
#
# #689 fixed this exact registration gap once (2026-08-11 00:08); the
# omission recurred within a day because only gates/test_boundary.py /
# gates/test_generated_paths.py catch it, and this repo runs no CI
# (#460) to run that pytest suite automatically. This hook ports the
# same derive-and-compare presence check those two test modules already
# implement inline (zero-install, no repo checkout guaranteed at
# hook-invocation time beyond the commit's own cwd), so the next
# newly-added gate/hook module has to land its spec row in the same
# commit instead of relying on someone remembering to run the suite.
#
# Trigger is narrow by design (matching spec-index-preflight.sh/
# role-axis-completeness-guard.sh precedent): only a NEWLY-STAGED (git
# diff --cached --name-status "A", or the destination side of an "R"/"C"
# rename/copy — before-landing hunt, stance 0: a rename lands a
# never-registered file at a target path without ever showing "A")
# gates/*.py (excluding test_*.py/__init__.py) / on-the-record/hooks/*.sh
# / .github/workflows/*.yml file fires this check — editing an
# already-registered module's internals (plain "M"), or any unrelated
# commit, is untouched (the ambient-noise failure mode #744
# investigates). The `git commit` detection itself is a `shlex.split`
# token check, not a substring regex (issue #876, porting the fix
# #866 landed in spec-index-preflight.sh) — a plain `\bgit\s+commit\b`
# substring match misses `git -c <key>=<val> commit ...`, letting a
# global option between `git` and `commit` bypass the trigger entirely.
#
# Fail-open on any environment gap (missing python3/git, not a `git
# commit` command, no newly-staged mechanism file, unreadable spec
# file). Fail-closed (exit 2) only when a newly-staged mechanism file's
# basename has no row in the relevant spec(s).
#
# issue #2705: PreToolUse fires BEFORE the guarded command's text runs,
# so `git diff --cached` alone is blind to a bundled `git add X && git
# commit` (this repo's own recommended landing shape, #2135) -- nothing
# is staged yet at hook time and this guard passed silently. Fixed by
# also parsing the pending command's own `git add` segment(s) for path
# arguments and cross-referencing them against `git status --porcelain`
# (untracked files only -- the "newly-added" case this guard cares
# about); a path that would be freshly staged by THIS SAME command is
# treated identically to one already staged by a prior call. No new
# fail-closed surface: a `git add` segment this guard cannot parse
# (unsupported flag ordering, path it cannot resolve) simply contributes
# no pending targets, same fail-open posture as every other environment
# gap here.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
# issue #2016 phase 2: cheap bash-level short-circuit before the python3 spawn below --
# skip the interpreter launch entirely when the raw payload plainly can't match this
# gate's own command-shape condition (checked again, authoritatively, in python).
{ grep -qF 'git' <<<"$payload" && grep -qF 'commit' <<<"$payload"; } || exit 0
command -v python3 >/dev/null 2>&1 || { echo "[$(basename "${BASH_SOURCE[0]}")] skipping: python3 not found (fail-open)" >&2; exit 0; }
command -v git >/dev/null 2>&1 || { echo "[$(basename "${BASH_SOURCE[0]}")] skipping: git not found (fail-open)" >&2; exit 0; }

IFS='' read -r -d '' GUARD <<'PY' || true
import fnmatch, json, os, re, shlex, subprocess, sys

def deny(msg):
    sys.stderr.write("gate-registration-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("GRG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

# issue #2210: tokenize a heredoc-body-blanked skeleton, not the raw
# command — see heredoc_scope.py's docstring for why: profiled in issue
# #2210 against the exact 7KB command that case's session log recorded,
# this shlex call alone dropped from ~2ms to ~0.08ms (~26x), redone
# across 4 gates every dispatch of a heredoc-shaped Bash call (record).
sys.path.insert(0, os.environ.get("OTR_HOOKS_DIR", ""))
from heredoc_scope import strip_heredoc_bodies
cmd_skeleton = strip_heredoc_bodies(cmd)

# issue #866/#876: a plain `\bgit\s+commit\b` substring match misses an
# ordinary `git -c <key>=<val> commit ...` (or any other global option
# between `git` and its `commit` subcommand) -- tokenizing first and
# checking for the two tokens survives any number of intervening
# options, and (unlike a looser substring check) does not fire on
# `commit` appearing inside an unrelated token (`--grep=commit`,
# `commit-tree`) or inside a quoted string.
#
# issue #882: plain `shlex.split` fuses an unspaced opening punctuation
# character onto the following word -- `(git commit -m x)` tokenizes to
# `["(git", "commit", ..., "x)"]`, so `"git" in tokens` is False and a
# real, ordinary subshell-wrapped commit silently escapes this trigger.
# `shlex.shlex(..., punctuation_chars=True)` (the design issue
# #824/#834 already landed in merge-allow-gate.sh/spawn-allow-gate.sh)
# splits `(` and `)` into their own tokens instead of fusing them, so
# `"git"`/`"commit"` land standalone again -- `whitespace_split = True`
# is required alongside it, or unquoted characters like `@`/`.` also
# get split out of tokens such as `user.email=b@e`.
try:
    _lexer = shlex.shlex(cmd_skeleton, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)
if "git" not in tokens or "commit" not in tokens:
    sys.exit(0)

cwd = e.get("cwd") or os.getcwd()

try:
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=20, cwd=cwd,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
repo_root = r.stdout.strip()
if not repo_root:
    sys.exit(0)

try:
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        capture_output=True, text=True, timeout=20, cwd=repo_root,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)

staged_all = set()
added = []
for line in r.stdout.splitlines():
    if not line.strip():
        continue
    parts = line.split("\t")
    if len(parts) < 2:
        continue
    status, path = parts[0], parts[-1]
    staged_all.add(path)
    # "A" is a plain new file. A rename/copy ("R100"/"C100"/"R<NN>") also
    # introduces its destination path fresh -- an existing tracked file
    # renamed into a target location is indistinguishable from a brand
    # new, never-registered module at that path, and a follow-up edit
    # would show as plain "M" (which this guard intentionally leaves
    # untouched for already-registered modules), so the rename step
    # itself is the only point this can still be caught (before-landing
    # hunt, stance 0).
    if status == "A" or status[:1] in ("R", "C"):
        added.append(path)


# issue #2705: the bundled `git add X && git commit` shape this repo's
# own batching guidance (#2135) recommends stages nothing before this
# hook runs -- `staged_all`/`added` above only ever reflect a PRIOR
# `git add` call. Parse the pending command's own `git add` segment(s)
# for path arguments the command is ABOUT to stage, and treat any that
# are currently untracked exactly like an already-staged "A". An
# adversarial review of the first cut of this fix (blind evaluator
# session, no issue context) live-reproduced three bypasses fixed below:
# `git add -A`/`-u`/`--all` was dead code (its own flag-token was
# stripped by the generic `-`-prefix filter before the special case
# ever saw it); `git -c k=v add`/`git -C dir add` (this file's own
# lines ~88-94 already call out `-c`/`-C` as a known two-token global-
# option bypass class for the sibling `commit`-detection check, never
# hardened here); and `git add .` was treated as repo-wide instead of
# scoped to the acting directory's subtree.
def _shell_segments(text):
    """Ordered ("seg", tokens) / ("open", None) / ("close", None) items
    for `text` -- `(`/`)` are reported as their own boundary markers
    (issue #2705 follow-up) instead of being folded in as plain
    separators, so a caller can track which segments run inside a
    `(...)` subshell and restore state when it closes, the same way
    bash itself does not leak a subshell's own `cd` to its parent."""
    items = []
    for line in text.replace("\\\n", " ").split("\n"):
        if not line.strip():
            continue
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            toks = list(lexer)
        except ValueError:
            continue
        seps = {"&&", "||", ";", "|", "<", ">", "&"}
        cur = []
        for t in toks:
            if t in ("(", ")"):
                if cur:
                    items.append(("seg", cur))
                    cur = []
                items.append(("open" if t == "(" else "close", None))
            elif t in seps:
                if cur:
                    items.append(("seg", cur))
                cur = []
            else:
                cur.append(t)
        if cur:
            items.append(("seg", cur))
    return items


def _pending_add_segments(text, start_cwd):
    """(effective_cwd, argument_list) for every `git add` segment in
    `text` -- tolerant of a leading wrapper/keyword before `git` (`env
    FOO=bar git add x`, `then git add x`) by locating the first `git`
    token rather than requiring it at position 0, and of two-token
    global options (`-c <key>=<val>`, `-C <dir>`) between `git` and
    `add`.

    issue #2705 follow-up: an earlier `cd`/`pushd` segment in the same
    command shifts the directory every later relative `git add` path
    resolves against -- the payload's static top-level `cwd` is only
    the STARTING effective cwd, not necessarily the one in force by
    the time the `add` segment runs. A cwd stack mirrors bash's own
    subshell scoping: entering `(` pushes a copy of the current
    effective cwd, and closing `)` pops back to it, discarding any `cd`
    done inside -- a subshell's directory change never leaks to its
    parent."""
    out = []
    stack = [start_cwd]
    for kind, value in _shell_segments(text):
        if kind == "open":
            stack.append(stack[-1])
            continue
        if kind == "close":
            if len(stack) > 1:
                stack.pop()
            continue
        seg = value
        if not seg:
            continue
        if seg[0] in ("cd", "pushd"):
            args = [a for a in seg[1:] if not a.startswith("-")]
            if args:
                target = args[0]
                stack[-1] = target if os.path.isabs(target) else os.path.normpath(
                    os.path.join(stack[-1], target))
            continue
        if "git" not in seg:
            continue
        i = seg.index("git") + 1
        while i < len(seg):
            t = seg[i]
            if t in ("-C", "-c"):
                i += 2
                continue
            if t.startswith("-"):
                i += 1
                continue
            break
        if i >= len(seg) or seg[i] != "add":
            continue
        out.append((stack[-1], seg[i + 1:]))
    return out


def _pathspec_exclude_pattern(arg):
    """The path pattern `arg` excludes, if `arg` is a `:(exclude)path`/
    `:!path`/`:^path` pathspec-magic token -- otherwise None.

    Only the exclude direction is special-cased. Other pathspec magic
    (`:(glob)`, `:(icase)`, `:(top)`, ...) is not implemented; an
    argument carrying it falls through to the generic literal/glob
    handling in `_pending_add_targets` below (best effort), same as
    any other shape this file cannot fully interpret."""
    if arg.startswith(":!") or arg.startswith(":^"):
        return arg[2:]
    if arg.startswith(":("):
        end = arg.find(")")
        if end == -1:
            return None
        keywords = [k.strip() for k in arg[2:end].split(",")]
        if "exclude" in keywords:
            return arg[end + 1:]
    return None


def _match_untracked(raw, seg_cwd, untracked):
    """Untracked repo-relative paths that positional argument `raw`
    resolves to, given `seg_cwd` as the acting directory: `.` or an
    existing directory argument sweep in cwd-relative prefix-matched
    form (issue #2705 follow-up: `git add gates/` stages every
    untracked file beneath it, the same as `git add .` already did for
    the whole cwd subtree -- a named directory is that case with a
    different spelling), otherwise an exact match or an fnmatch glob."""
    if raw == ".":
        cwd_rel = os.path.relpath(seg_cwd, repo_root).replace(os.sep, "/")
        prefix = "" if cwd_rel == "." else cwd_rel + "/"
        return {u for u in untracked if u.startswith(prefix)}
    abs_p = raw if os.path.isabs(raw) else os.path.normpath(
        os.path.join(seg_cwd, raw))
    if os.path.isdir(abs_p):
        try:
            dir_rel = os.path.relpath(abs_p, repo_root).replace(os.sep, "/")
        except ValueError:
            return set()
        prefix = "" if dir_rel in (".", "") else dir_rel + "/"
        return {u for u in untracked if u.startswith(prefix)}
    try:
        rel = os.path.relpath(abs_p, repo_root).replace(os.sep, "/")
    except ValueError:
        return set()
    if rel in untracked:
        return {rel}
    return {u for u in untracked if fnmatch.fnmatch(u, rel)}


def _pending_add_targets(seg_args, untracked, seg_cwd):
    """Repo-relative untracked paths a single `git add` segment's
    argument list would stage, given the already-computed `untracked`
    set (git status's `??` entries, repo-root-relative) and that
    segment's own effective cwd."""
    whole_tree = False
    positional = []
    excludes = []
    after_dashdash = False
    for a in seg_args:
        if not after_dashdash and a == "--":
            after_dashdash = True
            continue
        if not after_dashdash and a in ("-A", "--all"):
            whole_tree = True
            continue
        if not after_dashdash and a in ("-u", "--update"):
            # only stages modifications to ALREADY-tracked files -- never
            # stages a new untracked file by itself (finding #4).
            continue
        if not after_dashdash:
            excl = _pathspec_exclude_pattern(a)
            if excl is not None:
                excludes.append(excl)
                continue
        if not after_dashdash and a.startswith("-"):
            continue
        positional.append(a)
    if whole_tree:
        out = set(untracked)
    else:
        out = set()
        for raw in positional:
            out.update(_match_untracked(raw, seg_cwd, untracked))
    for excl in excludes:
        out -= _match_untracked(excl, seg_cwd, untracked)
    return out


pending_add_segments = _pending_add_segments(cmd_skeleton, cwd)
if pending_add_segments:
    try:
        # `-z`: NUL-separated, unquoted paths -- porcelain's default
        # quoting mangles names with spaces/non-ASCII, which a plain
        # `line[3:]` slice cannot undo (finding #6).
        st = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            capture_output=True, text=True, timeout=20, cwd=repo_root,
        )
    except (OSError, subprocess.SubprocessError):
        st = None
    if st is not None and st.returncode == 0:
        untracked = set()
        fields = st.stdout.split("\0")
        idx = 0
        while idx < len(fields):
            entry = fields[idx]
            idx += 1
            if not entry:
                continue
            status = entry[:2]
            if status[0] in ("R", "C"):
                idx += 1  # rename/copy carries a paired orig-path field
                continue
            if status == "??":
                untracked.add(entry[3:])
        for seg_cwd, seg_args in pending_add_segments:
            for u in _pending_add_targets(seg_args, untracked, seg_cwd):
                if u not in staged_all:
                    added.append(u)
                    staged_all.add(u)


def is_gate_module(p):
    if not p.startswith("gates/") or "/" in p[len("gates/"):]:
        return False
    name = os.path.basename(p)
    if not name.endswith(".py") or name.startswith("test_") or name == "__init__.py":
        return False
    return True


def is_hook_script(p):
    if not p.startswith("on-the-record/hooks/") or "/" in p[len("on-the-record/hooks/"):]:
        return False
    return os.path.basename(p).endswith(".sh")


def is_workflow(p):
    if not p.startswith(".github/workflows/") or "/" in p[len(".github/workflows/"):]:
        return False
    return os.path.basename(p).endswith(".yml")


gate_modules = sorted(p for p in added if is_gate_module(p))
hook_scripts = sorted(p for p in added if is_hook_script(p))
workflows = sorted(p for p in added if is_workflow(p))

targets = gate_modules + hook_scripts + workflows
if not targets:
    sys.exit(0)

_ROW_RE = re.compile(r"^\|\s*`?([^`|]+?)`?\s*\|\s*(.+?)\s*\|", re.MULTILINE)
_SEP_ROW = re.compile(r"^\|[\s:-]+\|")

# Ported from gates/test_generated_paths.py's _WRITE_CALL_RE/_ISSUE_PLACEHOLDER_RE
# (issue #839) -- same inline-porting convention _ROW_RE above already uses
# for that module's _ROW_RE, for the same no-guaranteed-checkout reason.
_WRITE_CALL_RE = re.compile(
    r"write_text\(|open\([^)]*['\"]w|\.mkdir\(|shutil\.(copy|move)|"
    r"\bmkdir\s+-p\b|\bgit\s+clone\b"
)
_ISSUE_PLACEHOLDER_RE = re.compile(
    r"issue-\$\{?issue|issue-\{issue|f[\"'].*issue[_-]?\{|issue-\(\?P<n>|"
    r"docs/issue-|issue-\d\+.*rev-parse|re\.match.*issue-"
)


def recorded_names(text):
    out = set()
    for line in text.splitlines():
        if not line.startswith("|") or _SEP_ROW.match(line):
            continue
        m = _ROW_RE.match(line)
        if not m:
            continue
        name, verdict = m.group(1).strip(), m.group(2).strip()
        if name in ("mechanism", "act") or not verdict:
            continue
        out.add(name)
    return out


def recorded_classifications(text):
    """{mechanism: classification} from a generated-paths.md-shaped table.

    _ROW_RE's second (non-greedy) capture group lands on the classification
    column for a 3-column table (mechanism | classification | verdict) --
    same regex recorded_names() already uses for the 2-column presence
    check, reused here for its second group instead of discarding it.
    """
    out = {}
    for line in text.splitlines():
        if not line.startswith("|") or _SEP_ROW.match(line):
            continue
        m = _ROW_RE.match(line)
        if not m:
            continue
        name, classification = m.group(1).strip(), m.group(2).strip()
        if name in ("mechanism", "act") or not classification:
            continue
        out[name] = classification
    return out


def read_spec(rel_path):
    if rel_path in staged_all:
        rr = subprocess.run(["git", "show", ":" + rel_path],
                             capture_output=True, timeout=20, cwd=repo_root)
        if rr.returncode == 0:
            try:
                return rr.stdout.decode("utf-8")
            except UnicodeDecodeError:
                pass
    abs_path = os.path.join(repo_root, rel_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


boundary_text = read_spec("docs/specs/enforcement-boundary.md")
boundary_names = recorded_names(boundary_text) if boundary_text is not None else set()

missing = []
mismatches = []
for p in targets:
    name = os.path.basename(p)
    if name not in boundary_names:
        missing.append(f"{p}: no row in docs/specs/enforcement-boundary.md")

# issue #909: a doc row alone does not mean the hook actually fires --
# absorbed-branch-recut-guard.sh had a docs/specs/enforcement-boundary.md
# row asserting it is a live PreToolUse/Bash hook while carrying no
# on-the-record/hooks/hooks.json entry, so it satisfied this guard's
# original (row-presence-only) check while never running in an installed
# session. A row is only exempt from the hooks.json cross-check when it
# says so explicitly (same convention `poll-rearm.sh`/`record-scaffold.sh`
# already use: "not a hook itself", "not wired into `hooks.json`",
# "CLI-invoked") -- any other row is read as a live-hook claim and must
# have a matching hooks.json command entry in the same staged tree.
_NOT_WIRED_RE = re.compile(
    r"not a hook itself|not wired into `?hooks\.json`?|CLI-invoked",
    re.IGNORECASE,
)


def boundary_row_text(text, name):
    for line in text.splitlines():
        if line.startswith("|") and not _SEP_ROW.match(line) and f"`{name}`" in line:
            return line
    return ""


if hook_scripts:
    hooks_json_text = read_spec("on-the-record/hooks/hooks.json")
    # No hooks.json in this tree at all -> nothing to cross-check against
    # (e.g. a test fixture repo that never sets one up); stay fail-open,
    # same posture the rest of this guard already takes on environment
    # gaps, rather than deny on a signal that was never available.
    hooks_json_names = None
    if hooks_json_text is not None:
        try:
            parsed_hooks = json.loads(hooks_json_text).get("hooks", {})
            hooks_json_names = set()
            for group_list in parsed_hooks.values():
                for group in group_list:
                    for h in group.get("hooks", []):
                        cmd_text = h.get("command", "")
                        # issue #2262: a wrapped registration
                        # ("fail-open-wrapper.sh <script>.sh <mode>")
                        # previously only ever contributed the wrapper's
                        # own basename here (`.split()[0]`) -- the
                        # wrapped script's name never entered this set,
                        # so any newly-added *wrapped* hook script failed
                        # this cross-check unconditionally regardless of
                        # its real hooks.json entry. Every `.sh` token in
                        # the command (wrapper AND wrapped script alike)
                        # now counts.
                        for tok in cmd_text.split():
                            if tok.endswith(".sh"):
                                hooks_json_names.add(os.path.basename(tok))
        except ValueError:
            hooks_json_names = None
    for p in hook_scripts:
        name = os.path.basename(p)
        if name not in boundary_names:
            continue
        row = boundary_row_text(boundary_text, name)
        if _NOT_WIRED_RE.search(row):
            continue
        if hooks_json_names is None:
            continue
        if name not in hooks_json_names:
            missing.append(
                f"{p}: docs/specs/enforcement-boundary.md claims this is a "
                "live hook but on-the-record/hooks/hooks.json has no "
                "command entry for it (issue #909)"
            )

if hook_scripts:
    paths_text = read_spec("docs/specs/generated-paths.md")
    paths_names = recorded_names(paths_text) if paths_text is not None else set()
    paths_classifications = (
        recorded_classifications(paths_text) if paths_text is not None else {}
    )
    for p in hook_scripts:
        name = os.path.basename(p)
        if name not in paths_names:
            missing.append(f"{p}: no row in docs/specs/generated-paths.md")
            continue
        # issue #839: existence alone (above) does not catch a row that
        # exists but is classified wrong (the incident this guard missed) --
        # derive write-call/issue-placeholder presence from this hook's own
        # staged text and compare against its recorded classification, same
        # bounded scope as the presence check (only this commit's own
        # newly-staged hook_scripts, never the whole directory).
        source_text = read_spec(p)
        if source_text is None:
            continue
        classification = paths_classifications.get(name, "")
        has_write = bool(_WRITE_CALL_RE.search(source_text))
        if not has_write:
            if classification != "n/a":
                mismatches.append(
                    f"{p}: recorded '{classification}' in "
                    "docs/specs/generated-paths.md but has no write call in "
                    "its own staged text (expected n/a)"
                )
        elif classification == "collision-risk" or classification not in (
            "out-of-tree", "issue-scoped",
        ):
            mismatches.append(
                f"{p}: recorded '{classification}' in "
                "docs/specs/generated-paths.md, which is not out-of-tree/"
                "issue-scoped"
            )
        elif classification == "issue-scoped" and not _ISSUE_PLACEHOLDER_RE.search(
            source_text
        ):
            mismatches.append(
                f"{p}: recorded issue-scoped in docs/specs/generated-paths.md "
                "but no issue-number placeholder found in its own staged text"
            )

if missing or mismatches:
    parts = []
    if missing:
        parts.append(
            "newly-added gate/hook module(s) missing a spec registration row "
            "(issue #441/#684):\n" + "\n".join(missing)
        )
    if mismatches:
        parts.append(
            "newly-added hook script(s) with a classification mismatch in "
            "docs/specs/generated-paths.md (issue #839):\n" + "\n".join(mismatches)
        )
    parts.append(
        "Fix the row in the same commit (docs/specs/enforcement-boundary.md, "
        "and for a hook script also docs/specs/generated-paths.md), then "
        "retry the commit."
    )
    deny("\n".join(parts))
PY

OTR_HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)" GRG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
