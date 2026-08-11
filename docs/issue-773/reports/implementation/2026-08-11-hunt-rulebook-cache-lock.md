---
proposal: docs/issue-773/proposals/rulebook-cache-lock.md
---

# Hunt record — rulebook-cache-lock

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — core_root() (spawn.py ~3210-3265) performs the identical exists-check-then-clone into `runs/rulebooks/tokenmaxxxer-core` but is a wholly separate code path from rulebook_checkout(); the proposed flock only wraps rulebook_checkout()'s exists-check+clone, so the exact same TOCTOU race the proposal targets remains open for the core clone.
Kind: composition
Seed: docs/issue-773/proposals/rulebook-cache-lock.md (proposes wrapping spawn.py:207-251 rulebook_checkout()'s `_mkt(d).exists()` check + `git clone` in a per-mkt fcntl.flock on `runs/rulebooks/<mkt>.lock`, mirroring the ROSTER lock at spawn.py:1732-1739)
cap_seconds: 120
tier: default
diff_stat_lines: N/A (docs-only proposal, no code diff yet)
started_at: 2026-08-11T15:50:00+09:00
ended_at: 2026-08-11T16:00:00+09:00

### Reproduce
Read spawn.py:3234-3261 (core_root()): it does its own `d = ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"`, checks `(d / "core" / ".claude-plugin" / "plugin.json").is_file()`, and if absent does `d.parent.mkdir(...)` then `git clone ... str(d)` — the same pattern rulebook_checkout() has, but never calling rulebook_checkout() or taking any lock. Two concurrent processes calling core_root() (which happens on every spawn, since core is mandatory per line 3231-3232) race exactly like rulebook_checkout() does today. Confirmed the underlying git behavior with a minimal harness outside the repo:

```
cd /tmp && rm -rf race_test && mkdir race_test && cd race_test && git init -q --bare src.git
SHA=$(GIT_DIR=src.git git commit-tree -m init $(GIT_DIR=src.git git hash-object -t tree /dev/null))
GIT_DIR=src.git git update-ref refs/heads/master $SHA
for i in 1 2; do ( if [ ! -d dest ]; then git clone -q src.git dest 2>>err$i.log; fi ) & done; wait
cat err2.log
```

### Observed
```
fatal: 작업 폴더를('dest') 만들 수 없습니다: 파일이 있습니다
```
(one of the two concurrent clones fails with "could not create work tree dir 'dest': File exists" — the identical failure mode described in the proposal for rulebook_checkout(), reproduced against core_root()'s own exists-check+clone which the proposed fix does not touch.)

### Expected
The proposed fix should either (a) note explicitly that core_root() is out of scope and carries the same unfixed race, or (b) also wrap core_root()'s exists-check+clone in the same `runs/rulebooks/tokenmaxxxer-core.lock` flock, since core_root() runs unconditionally on every role spawn (it is the mandatory gate the docstring at 3230-3232 describes) and hits the exact same shared-cache race as rulebook_checkout(). As written, the proposal only closes the race for per-role rulebook marketplaces and leaves the always-invoked core clone racing.
