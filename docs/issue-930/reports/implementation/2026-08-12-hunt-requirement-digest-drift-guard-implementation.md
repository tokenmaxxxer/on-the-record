
## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned hook (mirroring spec-index-preflight.sh's design) determines "staged diff touches requirements.md" via `git diff --cached --name-only`, evaluated by the PreToolUse hook *before* the intercepted Bash command runs; `git commit -a` stages tracked working-tree changes as part of the commit's own execution, so at hook-evaluation time the file is not yet in the cached diff, the drift check finds nothing to compare, and the commit is allowed through — landing an un-regenerated requirements.md/digest pair.
Kind: composition
Seed: docs/issue-930/proposals/requirement-digest-drift-guard-implementation.md (plans on-the-record/hooks/requirement-digest-preflight.sh to mirror on-the-record/hooks/spec-index-preflight.sh's `git diff --cached --name-only` staged-detection, which the existing sibling hook already uses at on-the-record/hooks/spec-index-preflight.sh line ~103-113)
cap_seconds: 60
tier: default
diff_stat_lines: docs-only (proposal + survey.md)
started_at: 2026-08-12T10:12:00+09:00
ended_at: 2026-08-12T10:22:00+09:00

### Reproduce
```
cd /tmp && rm -rf demo && mkdir demo && cd demo && git init -q \
  && printf 'orig\n' > requirements.md && git add requirements.md && git commit -qm init
printf 'changed\n' > requirements.md      # working-tree edit, NOT `git add`ed
git diff --cached --name-only             # <- what the hook's staged-detection sees
git commit -qa -m "sneaky change via -a"  # -a stages+commits in the same invocation
git show --stat HEAD | head -5
```

### Observed
`git diff --cached --name-only` prints nothing (empty staged set) right before the
`git commit -a` command runs, so the sibling hook's (and by direct mirroring, the
planned hook's) staged-touch check finds no reason to inspect `requirements.md` at
all; the subsequent `git commit -a` then commits the changed `requirements.md`
unchecked. `git show --stat HEAD` confirms `requirements.md` is the changed file in
the landed commit, with no digest-drift denial ever evaluated against it.

### Expected
A commit that lands a changed `docs/specs/requirements.md` without a matching
regenerated `docs/specs/requirement-digest.md` should be denied regardless of
whether the change was staged via `git add` beforehand or picked up implicitly by
`git commit -a`; the detection needs to account for `-a`/`--all`/`--interactive`-style
commits (e.g. by unioning `git diff --cached --name-only` with `git diff --name-only`
whenever the commit invocation includes `-a`/`--all`, or by always diffing
working-tree-vs-HEAD for tracked files) rather than trusting the pre-execution
staged snapshot alone.
