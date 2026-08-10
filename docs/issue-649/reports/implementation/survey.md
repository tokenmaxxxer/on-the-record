# Survey — issue #649

Scope: `on-the-record/hooks/delegated-judgment-gate.sh`, its embedded
Python (`GATE` heredoc), and its two test suites.

## Scout skip

Pure bugfix — the fix corrects one control-flow branch to an explicit
observable outcome; no product-facing or architectural decision is open.
Scouting (external exemplars) skipped per scout-directive's mandatory
skip condition.

## Current-state read

`gh pr create` handling (script lines ~333-351):

```
if not re.search(r"\bgh\s+pr\s+create\b", cmd):
    sys.exit(0)

r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
if r is None:
    sys.exit(0)
branch = r.stdout.strip()
bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
if not bm:
    sys.exit(0)
issue = int(bm.group(1))

prm = re.search(r"--number\s+(\d+)", cmd)
pr_ref = prm.group(1) if prm else "?"

r = _run(["git", "diff", "--name-only", "origin/main...HEAD"])
paths = [p for p in (r.stdout.splitlines() if r else []) if p.strip()]
if not paths:
    sys.exit(0)
```

`_run` (lines 72-77):

```python
def _run(args):
    try:
        r = subprocess.run(args, cwd=TARGET, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return r if r.returncode == 0 else None
```

**Bug**: `git diff --name-only origin/main...HEAD` fails (non-zero exit)
when `origin/main` does not exist — a fresh consumer clone that never
fetched/tracked `origin/main`, or any repo shape without that ref.
`_run` swallows the non-zero exit into `None`, `paths` becomes `[]` by
the same code path as "the diff is genuinely empty," and the `if not
paths: sys.exit(0)` branch fires with **zero output**: no `gh` call, no
stderr, no exit-code signal — indistinguishable from "no files changed."
This is exactly the #628 hunt finding: a fresh-consumer-clone shape
silently defeats the gate. The same `_run(["git", "rev-parse", ...])`
pattern two lines above (line 336) already fails closed-but-silent the
same way if `HEAD` cannot be resolved, but that is not in scope — #649
names `origin/main` specifically, and rev-parse HEAD failing means there
is no repo at all, a different and pre-existing failure mode not raised
by the hunt.

## Write set (frozen)

- `on-the-record/hooks/delegated-judgment-gate.sh` — detect the missing
  `origin/main` ref distinctly from "diff succeeded, zero paths," and
  emit an explicit, non-silent outcome instead of falling through to the
  existing empty-diff exit.
- `on-the-record/hooks/test_delegated_judgment_gate.py` — add the
  red/green fixture pair (origin/main absent → explicit outcome;
  present → unchanged behavior, existing tests already cover "present").

## Alternatives for the proposal's Rationale

1. **Refuse-and-instruct**: when `origin/main` is absent, post an
   explicit `gh issue comment` describing the missing ref and how to fix
   it (`git fetch origin main` / set up the remote-tracking ref), then
   exit 0 (hook's own posture: never blocks the underlying `gh pr
   create`).
2. **Resolve a sensible default**: fall back to a local `main` branch or
   `git merge-base` against the first available ref (`main`,
   `refs/heads/main`) when `origin/main` is missing, and proceed with the
   diff against that default silently.

Alternative 2 changes the diff base silently on the exact shape the hunt
flagged as risky (fresh clone, unverified remote state) — it would trade
one silent behavior (no-op) for another (silently comparing against a
possibly-stale or wrong local `main`), which is the harder failure mode
to notice in exactly the same "fresh consumer clone" case the issue
names. Alternative 1 is chosen: rejected alternative and reason belong in
the proposal's `## Rationale`.
