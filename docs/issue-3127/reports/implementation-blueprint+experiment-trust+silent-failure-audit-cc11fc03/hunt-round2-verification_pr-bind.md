---
proposal: none (CORE_BUILD_NOW bypass session, no formal proposal file)
---

# Hunt record — round2-verification_pr-bind

## before-landing -- stance 0: gate-bypassable

Verdict: FINDING -- verify_preregistration.py entirely skips ordering when RESULTS_PATH was ever introduced via a git-detected rename: `_first_commit_for_path` runs `git log --diff-filter=A --follow --format=%H --reverse -- path`, and on this repo's git (2.34.1) that exact combination (--follow + --diff-filter=A + --reverse together) returns EMPTY OUTPUT for any renamed path (reproduced even on a trivial two-commit git-mv, no content-similarity trickery needed); verify() then reads results_commit=None as "results file not yet committed (working tree only)" and returns True/exit-0 unconditionally, even though the results file was actually committed, and committed BEFORE the pre-registration -- the exact p-hacking order the whole script exists to catch.
Kind: silent-failure
Seed: scripts/issue-3127/verify_preregistration.py on ref pr3169-review (PR #3169, the round-2 merge-commit-bind fix to _resolve_via_pr_history); this finding is in _first_commit_for_path, upstream of that new bind -- it lets verify() reach a True return (the results_commit is None branch) without ever calling _resolve_via_pr_history or gh at all, so the new bind is simply never reached.
cap_seconds: 60
tier: size:docs
diff_stat_lines: 99
started_at: 2026-09-02T21:55:00+09:00
ended_at: 2026-09-02T22:20:00+09:00

### Reproduce
```
rm -rf /tmp/bypass-repo \&\& mkdir -p /tmp/bypass-repo \&\& cd /tmp/bypass-repo
git init -q \&\& git config user.email a@a.com \&\& git config user.name A
mkdir -p docs/issue-3127/decisions docs/issue-3127/_assets scripts/issue-3127
echo init > README.md \&\& git add README.md \&\& git commit -q -m init

# 1. write the RESULTS content first, under a placeholder filename (the real p-hacking act)
echo '{"result": "p<0.05, already known before pre-registering"}' > docs/issue-3127/_assets/placeholder.json
git add docs/issue-3127/_assets/placeholder.json \&\& git commit -q -m "add placeholder results (real content, committed first)"

# 2. rename the placeholder to the real RESULTS_PATH in its own commit (plain git mv, no similarity crafting)
git mv docs/issue-3127/_assets/placeholder.json docs/issue-3127/_assets/consumer-path-results.json
git commit -q -am "rename placeholder to consumer-path-results.json"

# 3. commit the pre-registration LAST, after the results already exist
printf -- "---\nverification_pr: 1\n---\npre-registration written after seeing results\n" > docs/issue-3127/decisions/pre-registration.md
git add docs/issue-3127/decisions/pre-registration.md \&\& git commit -q -m "add pre-registration (actually written LAST)"

# copy the real script in and run it
cp <repo>/scripts/issue-3127/verify_preregistration.py scripts/issue-3127/verify_preregistration.py
python3 scripts/issue-3127/verify_preregistration.py --repo-root .; echo "exit=$?"
```

### Observed
```
OK: docs/issue-3127/decisions/pre-registration.md committed at 7ce18a5...; docs/issue-3127/_assets/consumer-path-results.json not yet committed (working tree only), so it cannot precede the pre-registration
exit=0
```
Independently confirmed the underlying git behaviour in isolation (no script involved): `git log --diff-filter=A --follow --format=%H -- b.txt` (no --reverse) after a plain `git mv a.txt b.txt` correctly returns the add commit; adding `--reverse` to that exact same query returns nothing at all, on git 2.34.1 -- i.e. the emptiness is a generic property of `--follow --diff-filter=A --reverse` on any renamed path, not something requiring crafted content similarity.

### Expected
The script should fail (exit 1) reporting that the results file was committed before the pre-registration -- results_commit should resolve to the real "rename placeholder" commit (which is strictly after the results-first commit and strictly before the pre-registration commit), not silently collapse to None and be treated as "nothing to compare yet, pass."
