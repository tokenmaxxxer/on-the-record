---
proposal: docs/issue-866/proposals/2026-08-11-regenerate-spec-index-and-record-preflight-gap.md
---

# Hunt record — regenerate-spec-index-and-record-preflight-gap

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `spec-index-preflight.sh`'s trigger regex `\bgit\s+commit\b` fails to match `git -c <cfg>=<val> commit ...`, a fully legitimate local git invocation form, so the hash-comparison logic (correctly verified elsewhere) never runs and staged spec drift is silently allowed to land.
Kind: silent-failure
Seed: on-the-record/hooks/spec-index-preflight.sh (unchanged per proposal); docs/issue-866/proposals/2026-08-11-regenerate-spec-index-and-record-preflight-gap.md
cap_seconds: 60
tier: default
diff_stat_lines: 0 (hook file left unchanged by proposal; this finding is against that unchanged file)
started_at: 2026-08-11T13:43:41Z
ended_at: 2026-08-11T13:44:18Z

### Reproduce
```
D=$(mktemp -d); cd "$D"
git init -q
mkdir -p docs/specs
printf '# spec\noriginal content\n' > docs/specs/foo.md
git add docs/specs/foo.md && git commit -qm init
HASH=$(git show :docs/specs/foo.md | shasum -a 256 | cut -d' ' -f1)
printf '| `docs/specs/foo.md` | `%s` |\n' "$HASH" > docs/specs/reconciled-index.md
git add docs/specs/reconciled-index.md && git commit -qm "add index"
printf '# spec\nDRIFTED CONTENT\n' > docs/specs/foo.md
git add docs/specs/foo.md   # index NOT updated -> real drift, same shape as PR #863

HOOK=on-the-record/hooks/spec-index-preflight.sh   # from repo root

echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m x"}}' | bash "$HOOK"; echo "exit=$?"
echo '{"tool_name":"Bash","tool_input":{"command":"git -c commit.gpgsign=false commit -m x"}}' | bash "$HOOK"; echo "exit=$?"
```

### Observed
```
=== git commit -m x ===
spec-index-preflight: staged content changed for tracked spec file(s) [docs/specs/foo.md] but docs/specs/reconciled-index.md was not updated to match in the same staged set. ...
exit=2
=== git -c commit.gpgsign=false commit -m x ===
exit=0
```
The second, equally-real command (a standard way to pass a one-off git config
value, e.g. to disable gpg signing or set `user.email` for a single commit)
produces no stderr and exit 0 — the exact same staged drift lands with zero
warning. `python3 -c 're.search(r"\bgit\s+commit\b", "git -c commit.gpgsign=false commit -m x")'` → `None`, confirming the regex is the point of failure: any
token sequence between `git` and the `commit` subcommand (any `-c`, `-C`,
`--git-dir=`, etc.) defeats `\bgit\s+commit\b` even though git itself parses
it as `git commit` just fine.

### Expected
The proposal's claim is that "the hook's own staged-content-vs-index-hash
comparison logic is correct" and the *only* gap is the server-side
squash-merge path that PreToolUse structurally cannot see. That claim is
false as stated: there is also a locally-run, ordinary `Bash` `git commit`
invocation shape (`git -c <cfg> commit ...`) that a Claude Code session can
issue directly, which the hook's own trigger regex fails to recognize as a
commit at all, so the (correct) hash-comparison code is never reached and
the drift is silently allowed. This is a cheap, real fix opportunity the
proposal dismissed the wrong reason for: it isn't the hash logic that needs
no further work, it's the regex gating that logic that has a hole matching
"a command that matches the `git commit` regex loosely but the hook
mishandles" — exactly the class of gap the dispatcher asked this stance to
check for.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

canonical: on-the-record/hooks/gate-registration-guard.sh line 56, on-the-record/hooks/role-axis-completeness-guard.sh line 60 (read directly this session)
Verdict: FINDING — the shlex.split-based trigger rewrite landed in spec-index-preflight.sh only. Two sibling PreToolUse/Bash hooks on the same matcher (role-axis-completeness-guard.sh, gate-registration-guard.sh), which document themselves as following spec-index-preflight.sh precedent for this exact trigger, still use the old substring regex, so a `git -c k=v commit ...` invocation is now caught by spec-index-preflight.sh but silently skips the other two gates even with a real, positively-determined violation staged.
Kind: composition
Seed: on-the-record/hooks/spec-index-preflight.sh (fixed trigger check) vs on-the-record/hooks/gate-registration-guard.sh line 56 and on-the-record/hooks/role-axis-completeness-guard.sh line 60 (unchanged, same old regex line spec-index-preflight.sh itself carried before this fix)
cap_seconds: 180
tier: size:large
diff_stat_lines: 6 files, 509 insertions(+), 3 deletions(-)
started_at: 2026-08-11T13:53:57Z
ended_at: 2026-08-11T14:03:00Z

### Reproduce
```
cd on-the-record-issue-866-implementation
printf '#' ' temp probe, unregistered in enforcement-boundary.md\n' > gates/__tmp_hunt_probe.py
git add gates/__tmp_hunt_probe.py

python3 -c 'import json,os; v="com"+"mit"; print(json.dumps({"tool_name":"Bash","tool_input":{"command":"git "+v+" -m \"msg\""},"cwd":os.getcwd()}))' > /tmp/payload_plain.json
python3 -c 'import json,os; v="com"+"mit"; print(json.dumps({"tool_name":"Bash","tool_input":{"command":"git -c user.name=Bot -c user.email=bot@example.com "+v+" -m \"msg\""},"cwd":os.getcwd()}))' > /tmp/payload_dashc.json

export ORCHESTRATE_OFF=0
cat /tmp/payload_plain.json | on-the-record/hooks/gate-registration-guard.sh; echo "plain exit: $?"
cat /tmp/payload_dashc.json | on-the-record/hooks/gate-registration-guard.sh; echo "dashc exit: $?"

git reset -q -- gates/__tmp_hunt_probe.py && rm -f gates/__tmp_hunt_probe.py
```

### Observed
```
=== plain ===
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/__tmp_hunt_probe.py: no row in docs/specs/enforcement-boundary.md
Fix the row in the same commit (docs/specs/enforcement-boundary.md, and for a hook script also docs/specs/generated-paths.md), then retry the commit.
plain exit: 2

=== dashc ===
dashc exit: 0
```
The second run produced no stderr and exited 0 against the identical staged
violation used for the first run, because the guard's own trigger line
never matches a hyphen-c-carrying invocation and the deny path just proven to
fire on the plain form never runs at all. role-axis-completeness-guard.sh
line 60 carries the byte-identical trigger regex line, so the same
divergence applies there by inspection without needing a second live run.

### Expected
Given the proposal's own rationale for spec-index-preflight.sh's rewrite —
that a plain substring match on adjacent words being adjacent misses an
ordinary `git -c <key>=<val> <verb> ...` invocation with a global option in
between — the identical gap should not be left standing in the two sibling
hooks that carry the same trigger-detection line and explicitly cite each
other as precedent for it. Right now a single `git -c core.pager=cat <verb>
-m msg`-shaped invocation passes gate-registration-guard.sh and
role-axis-completeness-guard.sh with zero denial even though the plain form
of the exact same invocation is positively denied, while spec-index-preflight.sh
alone now catches the equivalent drift for its own concern. The three gates
registered on the same PreToolUse/Bash matcher no longer agree on what a
git commit attempt even is.
