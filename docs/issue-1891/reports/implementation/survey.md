---
subject: issue-1891
type: survey
---

# Survey: exclude the role sidecar from git staging

## Sidecar write site

canonical: `spawn.py` (read live), `_write_role_sidecar` at spawn.py:7625-7639:

```python
def _write_role_sidecar(work: str, issue: int, role: str) -> None:
    d = Path(work) / ".on-the-record"
    try:
        d.mkdir(parents=True, exist_ok=True)
        (d / "role.json").write_text(
            json.dumps({"role": role, "issue": issue}) + "\n", encoding="utf-8")
    except OSError as e:
        print(f"경고: {work} 에 role.json 사이드카를 쓰지 못했다 ({e})",
              file=sys.stderr)
```

canonical: `spawn.py` (read live) — `_write_role_sidecar` is called from
exactly 3 sites inside `issue_workspace()`: spawn.py:7684 (`src ==
work.resolve()`, cwd already is the workspace), spawn.py:7708 (existing
work dir reused via fetch), and spawn.py:7753 (fresh clone path, after
`_fetch_or_halt`). None of the 3 call sites currently ensures a
`.git/info/exclude` entry for the sidecar before or after writing it —
this is the gap PR #1890 hit.

## Existing `.git/info/exclude` mechanism (precedent, not yet covering the sidecar)

canonical: spawn.py:7717-7745 (read live) — the fresh-clone branch of
`issue_workspace()` already writes a workspace-local
`.git/info/exclude` for a different purpose (issue #289 H1: Claude Code
sandbox dotfile overlay leaking credential-shaped files into `git add
-A`):

```python
ex = work / ".git" / "info" / "exclude"
lines = [".muster-cache/"]
lines += [".bashrc", ".bash_profile", ".profile", ".zshrc",
          ".zprofile", ".gitconfig", ".gitmodules", ".mcp.json",
          ".claude/", ".idea", ".vscode", ".ripgreprc"]
skipped = lines
try:
    ex.parent.mkdir(parents=True, exist_ok=True)
    existing = ex.read_text() if ex.exists() else ""
    missing = [ln for ln in lines if ln.rstrip("/") not in existing]
    skipped = missing
    if missing:
        with ex.open("a") as fh:
            for ln in missing:
                fh.write(ln + "\n")
except OSError as e:
    print(f"경고: 워크스페이스 {work} 의 자격증명 유출 방지 exclude 항목을 "
          f"쓰지 못했다 ({e}) — 빠진 항목: {', '.join(skipped)}",
          file=sys.stderr)
```

Two gaps against this issue's requirement:

1. `.on-the-record/role.json` is not in the `lines` list — even the
   fresh-clone path, the only path that touches `.git/info/exclude` at
   all today, does not exclude the sidecar.
2. This block runs only in the fresh-clone branch (before
   `_write_role_sidecar` is called at spawn.py:7753). The two reuse
   branches (spawn.py:7684, spawn.py:7708) call `_write_role_sidecar`
   directly with no exclude step at all — a respawned/reused workspace
   (the PR #1890 shape: an already-cloned workspace, sidecar written on
   a later session) never gets the append-only-if-missing exclude
   treatment.

## PR #1890 near-miss shape

canonical: `gh issue view 1891` (read live) — Program context states
PR #1890 (issue #1882, wave-2a knowledge-management family) committed
`.on-the-record/role.json`; caught and stripped by the orchestrator
before merge, not by any mechanical gate in this repo. Confirms
requirement 1's exact fix point: the exclude entry must exist by the
time `_write_role_sidecar` first writes the file, on every call path
(fresh clone, reused work dir, reused src==work), not only the
fresh-clone path the current dotfile-leak block covers.

## Regression test file and existing sidecar-write test class

canonical: `test/test_branch_role_field.py:35-60` (read live) — a
`SidecarWriteShapeTest` class already exercises
`spawn._write_role_sidecar` directly against a bare `tempfile` dir (no
git repo underneath), asserting the written JSON shape. This class is
the natural home for the new acceptance-check case, but its existing
cases use a plain `tempfile.TemporaryDirectory()` with no `.git` —
requirement 1's `git status --porcelain` check needs an actual git repo
initialized in the temp dir first (`git init`), which none of the
existing cases in this class currently set up.

## Non-goals confirmation

canonical: `gh issue view 1891` (read live) — non-goals line: "changing
the sidecar format or any reader." The fix is confined to where/when the
exclude entry is written; `_write_role_sidecar`'s own JSON-write body
and every reader of `.on-the-record/role.json` (the 3 shell hooks +
`gates/flows.py`, per test/test_branch_role_field.py's module
docstring) are out of scope and untouched by this change.

## Live reproduction of the gap in this session's own workspace

canonical: `git status --porcelain` (executed live in this session's own
workspace, `/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1891-implementation`) —
output includes `?? .on-the-record/role.json`, confirming the gap this
issue describes is reproducible in the exact workspace this session is
running in, not only a hypothetical.

## Skip-condition check

The mechanism is spec-frozen by the issue itself (design-research line:
"`.git/info/exclude` is the standard untracked-local mechanism; no repo
file change") and precedent for exactly this mechanism already exists in
this same function's caller (the dotfile-leak block above) — there is no
external field to scout and no design choice left open on *which*
mechanism to use. The open question this survey resolves is purely
internal: *where* in `_write_role_sidecar`'s 3 call sites the exclude
write must happen so all 3 paths are covered, which the call-site
enumeration above settles. Scouting is not run as a separate external
sweep for this reason — this is the mandatory skip-condition case where
"the spec leaves no design decision open" on the mechanism, and the one
open implementation-placement question is answered by reading this
repository's own existing precedent rather than external sources.
