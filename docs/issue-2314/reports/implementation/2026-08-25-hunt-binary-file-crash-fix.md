# issue-2314 warrant hunt log

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `_git_show()`'s UnicodeDecodeError-to-`""` fallback lets a real (non-binary-per-git) stale revert of a security fix pass as ALLOW when the fixed line contains a non-UTF-8 byte, because `""` makes `classify()`'s `_added_lines()` see zero additions and short-circuit to ALLOW before ever comparing to `head`.
Kind: silent-failure
Seed: gates/stale_revert_guard.py (`_git_show`, `changed_paths`) per /tmp/issue-2314-before-landing.diff; also reproducible via `git diff HEAD -- gates/stale_revert_guard.py gates/test_stale_revert_guard.py`
transition: before-landing
cap_seconds: 180
tier: default
diff_stat_lines: ~40 (gates/stale_revert_guard.py hunk) + 175 new test file
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:20:00Z

### Reproduce
```python
python3 - <<'EOF'
import sys, tempfile, subprocess
from pathlib import Path
sys.path.insert(0, "gates")
import stale_revert_guard as srg

def run(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout

with tempfile.TemporaryDirectory() as td:
    repo = Path(td) / "repo"
    repo.mkdir()
    run(repo, "init", "-q", "-b", "main")
    run(repo, "config", "user.email", "t@example.com")
    run(repo, "config", "user.name", "T")

    (repo / "app.py").write_bytes(b"line1\nline2\nline3\n")
    run(repo, "add", "app.py")
    run(repo, "commit", "-q", "-m", "init")
    run(repo, "branch", "pr-branch")

    # base HEAD adds a "security fix" line containing one non-UTF-8 byte
    # (Latin-1 e-acute, 0xE9) -- no NUL byte anywhere, so git's own
    # binary heuristic does NOT mark this file binary.
    fix_line = b"FIX_caf\xe9_validate\n"
    (repo / "app.py").write_bytes(b"line1\n" + fix_line + b"line2\nline3\n")
    run(repo, "add", "app.py")
    run(repo, "commit", "-q", "-m", "security fix (non-utf8 byte)")

    run(repo, "checkout", "-q", "pr-branch")
    (repo / "app.py").write_bytes(b"line1\nOLDLINE2\nline3\n")  # stale, overlapping, lacks the fix
    run(repo, "add", "app.py")
    run(repo, "commit", "-q", "-m", "unrelated stale change")
    stale_head = run(repo, "rev-parse", "HEAD").strip()
    run(repo, "checkout", "-q", "main")

    mb = run(repo, "merge-base", "main", stale_head).strip()
    print("numstat:", repr(run(repo, "diff", "--numstat", f"{mb}..main")))  # "1\t0\tapp.py" -- NOT binary per git
    print("git_show(base_head):", repr(srg._git_show(repo, "main", "app.py")))  # -> ''
    print("refusals:", srg.check_pr(repo, "main", mb, stale_head))  # -> []  (should REFUSE)
EOF
```

### Observed
```
numstat: '1\t0\tapp.py\n'
git_show(base_head): ''
refusals: []
```
`changed_paths()` correctly keeps `app.py` (git's own `--numstat` binary marker is `-\t-`, and this file gets real numbers `1\t0`, so it is not skipped as binary). But `_git_show()` for the base-HEAD ref fails to `.decode("utf-8")` on the single non-UTF-8 byte and falls back to `""` per this diff's new try/except. `classify()` then computes `_added_lines(merge_base_content, "")` = `[]` (nothing "added" relative to an empty string), and returns `ALLOW` at the `if not added` short-circuit — without ever inspecting `head_content` to see it lacks the fix. `check_pr()` therefore returns `[]` (ALLOW) for a PR that genuinely reverts a just-landed fix.

### Expected
A stale PR branch that reverts a real, recently-added line in a file git itself treats as text (non-binary per `--numstat`) should be caught by `classify()`'s added/lost-lines logic, i.e. `check_pr()` should return a non-empty refusal list (as the pre-existing live test `test_live_stale_branch_refused_then_allowed_after_rebase` demonstrates for pure-ASCII content). Instead, the new decode-failure fallback silently converts "gate can't read the base-HEAD content" into "nothing was added, therefore ALLOW", which is the opposite of the fail-closed intent stated in the same diff's own docstring ("defense in depth; primary defense is `changed_paths()`'s binary-path exclusion" — but `changed_paths()` does *not* exclude this path, since git itself does not consider it binary). The old crashing behavior at least surfaced loudly (no verdict, exception propagates); this fix trades a loud, blocking failure for a silent pass on a class of inputs (non-UTF-8, non-binary-per-git text: Latin-1/Shift-JIS/UTF-16-without-BOM-detected-as-NUL-free/etc.) that `changed_paths()`'s binary filter does not catch.
