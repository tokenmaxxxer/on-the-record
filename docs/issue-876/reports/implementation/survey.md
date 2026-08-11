# Survey — issue #876

## Write set

- `on-the-record/hooks/gate-registration-guard.sh`
- `on-the-record/hooks/role-axis-completeness-guard.sh`
- `on-the-record/hooks/test_gate_registration_guard.py`
- `on-the-record/hooks/test_role_axis_completeness_guard.py`
- `docs/issue-876/**` (this survey, the proposal, the record)

`on-the-record/hooks/spec-index-preflight.sh` is frozen (issue's own
"범위 밖") — read-only reference for the shape to port, never edited here.

## Scout-directive skip condition

This is a pure bugfix: the issue names the exact landed correction to
port (`spec-index-preflight.sh`'s `shlex.split`-based token check, PR
#875/issue #866) and explicitly says not to design anything new
("새로 설계하지 말고 그 모양을 그대로 옮겨라"). No product-shaped surface,
no exemplar field to scout. Scouting is skipped per the scout-directive's
first skip condition; the one open design question the issue does pose
(shared helper vs. a third duplication) is answered by codebase
constraint-checking below, not by scouting external prior art.

## What the landed fix looks like

canonical: `on-the-record/hooks/spec-index-preflight.sh` lines 30-60,
read this session, this branch (post-PR #875, commit `7d97bd6`).

The GUARD python body imports `shlex`, tokenizes the raw command string,
and requires both `"git"` and `"commit"` as standalone tokens:

```
try:
    tokens = shlex.split(cmd)
except ValueError:
    sys.exit(0)
if "git" not in tokens or "commit" not in tokens:
    sys.exit(0)
```

This survives any number of global options between `git` and `commit`
(`git -c k=v commit`, `git -C /path commit`, ...), does not fire on
`commit` inside an unrelated token (`--grep=commit`, `commit-tree`) or a
quoted string, and fails open (exit 0) on an unparseable command
(unbalanced quote) rather than raising.

canonical: `on-the-record/hooks/test_spec_index_preflight.py` lines
177-211, read this session, this branch — carries 6 regression cases for
this exact shape (`_t7`-`_t12`). Ran this session:

```
$ python3 on-the-record/hooks/test_spec_index_preflight.py
PASS: trigger: plain `git commit` is recognized
PASS: trigger: issue #866 regression — `git -c k=v commit` is recognized
PASS: trigger: `git log --grep=commit` is not a commit invocation
PASS: trigger: `git commit-tree` is not `git commit`
PASS: trigger: 'commit' only inside a quoted string is not a commit invocation
PASS: trigger: unparseable command (unbalanced quote) fails open -> False
all tests passed
```

(full 12-case run; six pre-existing cases omitted above for brevity, all
passed in the same run.)

## Current state of the two sibling hooks

canonical: `git show HEAD:on-the-record/hooks/gate-registration-guard.sh`
and `git show HEAD:on-the-record/hooks/role-axis-completeness-guard.sh`
(pre-edit tree, this branch before this session's own change), read this
session via:

```
$ grep -n 'git\s+commit' on-the-record/hooks/*.sh
on-the-record/hooks/gate-registration-guard.sh:56:if not re.search(r"\bgit\s+commit\b", cmd):
on-the-record/hooks/role-axis-completeness-guard.sh:60:if not re.search(r"\bgit\s+commit\b", cmd):
```

Both byte-identical to the pre-fix regex `spec-index-preflight.sh` moved
away from in #866/PR #875.

canonical: `docs/issue-866/reports/implementation/resolution.md`,
"## Open findings" section, read this session — the #866 after-proposal
hunt already reproduced the bypass shape live against
`gate-registration-guard.sh` (`git -c user.name=Bot -c
user.email=bot@example.com commit -m msg` against a staged, unregistered
gate module: exit 0, no stderr) and named this exact port as the
follow-up issue, which is this issue's origin.

canonical: `grep -rn "git -c\|shlex" on-the-record/hooks/test_gate_registration_guard.py on-the-record/hooks/test_role_axis_completeness_guard.py`,
read this session against the pre-edit tree — no match in either file;
neither sibling hook had a regression test for the `git -c ...` shape
before this session. Both files drive the real hook script end-to-end
via `subprocess.run(["bash", str(GUARD)], ...)` against a real `git
init` fixture repo (not a pure-python mirror the way
`test_spec_index_preflight.py` tests its trigger check), so the
regression case for each hook is a real staged-violation +
`git -c k=v commit ...` invocation asserting `returncode == 2`, matching
each file's own existing test convention rather than importing
`test_spec_index_preflight.py`'s `is_git_commit_invocation` mirror.

## The shared-helper question

The issue asks explicitly: extract a shared helper for this token check
(now triplicated across three hook scripts), or accept a third
duplication — and to verify whether this repo's own stated
"no guaranteed checkout, inline-port instead of import" convention still
holds before answering.

### Evidence the constraint is real and current, not stale

1. **Hooks run from the plugin install directory, not a guaranteed repo
   checkout.**

   canonical: `on-the-record/hooks/hooks.json`, read this session:

   ```
   $ grep -n 'spec-index-preflight\|role-axis-completeness-guard\|gate-registration-guard' on-the-record/hooks/hooks.json
   { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/spec-index-preflight.sh" },
   { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/role-axis-completeness-guard.sh" },
   { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/gate-registration-guard.sh" },
   ```

   All three are invoked by absolute path under `${CLAUDE_PLUGIN_ROOT}`,
   the plugin's own install location — not necessarily inside the
   consumer repo's working tree at all. A shared helper module living
   anywhere in the *consumer* repo (e.g. `gates/`) is not guaranteed to
   exist relative to the hook at invocation time.

2. **The one hook in this trio that already imports instead of
   inline-porting documents exactly this risk, and the risk is live, not
   hypothetical.** `role-axis-completeness-guard.sh` imports
   `gates/role_spec_shape.py` (with a two-candidate fallback: consumer
   repo's `gates/`, then the packaged `on-the-record/gates/` copy),
   because that module's `check_axis_ownership`/`check_role_judgment_axes`
   are too large to re-port. Its own top comment states "The packaged
   on-the-record/gates copy can lag the top-level gates/."

   canonical: `diff on-the-record/gates/role_spec_shape.py
   gates/role_spec_shape.py`, run this session against this branch's
   working tree:

   ```
   90a91,202
   > _JUDGMENT_AXES = {
   >     "alignment", "maintenance_complexity", "external_burden",
   ...
   > def check_role_judgment_axes(role: dict) -> list[str]:
   ...
   ```

   The packaged copy is missing both functions the hook needs; the hook
   only works because of its own fallback-and-fail-open probing, not
   because the shared module is reliably present. A new shared helper for
   this issue's much smaller check would inherit the identical staleness
   risk, and — unlike `role_spec_shape.py`'s two real functions, which
   justify the fallback-probe complexity — a five-line tokenize-and-check
   is not proportionate to carrying that complexity a third time.

3. **Every other hook in this directory that needs Python logic ports it
   inline; none share a Python helper module.**

   canonical: `grep -l '^source\|^\. ' on-the-record/hooks/*.sh`, run
   this session:

   ```
   on-the-record/hooks/directive.sh
   on-the-record/hooks/stop-poll-rearm.sh
   ```

   Both matches are shell-level `source`, not a Python import. Across the
   ~30 other `*.sh` hooks in this directory (`spec-index-preflight.sh`,
   `gate-registration-guard.sh`'s own
   `_WRITE_CALL_RE`/`_ISSUE_PLACEHOLDER_RE` ported from
   `gates/test_generated_paths.py`, etc.), the established convention is:
   duplicate the small check inline, cite the upstream source in a
   comment, keep each hook a standalone zero-install script. This
   trigger-detection snippet (9 lines) is well inside that established
   "small enough to duplicate" band — `role_spec_shape.py`'s two
   functions (112 lines) are the outlier that needed the import-with-
   fallback treatment, not the norm.

4. **A shared helper would reintroduce a fail-open gap identical to the
   one this issue is fixing.** If the token check moved to an importable
   module and that module were missing/stale/unreadable at hook-invocation
   time, the only safe behavior consistent with this hook family's
   documented fail-open policy (`spec-index-preflight.sh`'s own header:
   "Fail-open by design: any environment gap ... exits 0") is to skip the
   check silently — precisely the silent-bypass shape issue #876 exists to
   close. Duplication removes that failure mode entirely: the check is
   always present because it is the hook's own source text.

### Decision

Port inline, as a third duplication — do not extract a shared helper.
Recorded with rationale in the proposal's `## Rationale` section.
