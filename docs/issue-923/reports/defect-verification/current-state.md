---
kind: current-state-survey
loop_state: handed-off
---

# Current-state survey — issue #923 (integrity gates block a legitimate observation/verdict record)

## Scope

canonical: `gh issue view 923`, read this session — quotes the #895
regression.

Reproduce the silent commit-block on an observation-role scoreboard
record whose evidence is its own executed-live measurement citation
(transcript/derived), per #923 step 1: pin which gate refuses, why the
observation's own citations don't satisfy it, and whether the refusal is
silent. No fix — that is #923 step 2 (implementation).

```
The #895 ambiguous-scenario execution-observation ran the measurement
successfully (fixture PR #15 merged, requirement met) but its scoreboard
record NEVER committed — no ambiguous scoreboard PR exists on
on-the-record ... Likely cause: the just-landed real-build-use integrity
gates — #892 outcome-claim citation, #920 live-fire-claim-real-run-guard,
#919 acceptance-command-real-run-guard — fail-closed on the observation
record's 'this requirement is PASS' verdict claims
```

code_under_review:
- gates/record_lint.py
- on-the-record/hooks/record-claim-guard.sh
- on-the-record/hooks/hooks.json

## Finding 1 — the gate that fires is `outcome_claim_citation_check` (issue #870), not #919/#920

canonical: on-the-record/hooks/hooks.json, read this session, lines
63-65 — matcher `Write|Edit|MultiEdit` wires
`${CLAUDE_PLUGIN_ROOT}/hooks/record-claim-guard.sh`.

`#919` (acceptance-command-real-run-guard.sh) and `#920`
(live-fire-claim-real-run-guard.sh) instead gate the `Bash`/`git commit`
surface — real-run proof that an acceptance/live-fire command executed
this turn — not a `Write`/`Edit` to a `docs/issue-*/reports/**` path, so
neither one fires on the record-write itself that #895 hit. The check
that fires on that write is `outcome_claim_citation_check` (issue #870),
called from `record-claim-guard.sh`
(on-the-record/hooks/record-claim-guard.sh, line 117-119) into
`gates/record_lint.py` (lines 96-146).

## Finding 2 — a synthetic observation-style write is refused

derived: `bash on-the-record/hooks/record-claim-guard.sh`, fed a
synthetic `PreToolUse` `Write` payload (file_path a hypothetical docs/issue-895/reports/execution-observation.md,
not backtick-quoted here since that path does not exist in this tree) with this content:
```
## Scoreboard

- ambiguous-scenario requirement met: PASS
  canonical: execution transcript for the ambiguous-scenario run, fixture PR #15 merged 2026-08-05

derived: docs/issue-895/transcripts/ambiguous-run.log
```
Output:
```
record-claim-guard: 레코드에 실행-근거 없는 OUTCOME 주장 (issue #870): '- ambiguous-scenario requirement met: PASS' — ...
EXIT: 2
```

## Finding 3 — the gate accepts two citation shapes; one is reachable by an observation record, the other isn't its natural style

canonical: gates/record_lint.py, read this session, lines 88-94:
```
_OUTCOME_CLAIM_MARKER = re.compile(
    r"(?i)\b(requirement(?:s)?\s+met|done|PASS(?:es|ed)?|complete[ds]?)\b")
_EXECUTED_LIVE_CANONICAL = re.compile(
    r"(?i)^(?:gh\s|git\s|pytest\b|python3?\s|npm\s|npx\s|bash\s|sh\s|\./|"
    r"acceptance:\s*\S.*\bresult:\s*(?:PASS|FAIL|UNMEASURED)\b|"
    r"live-fire:\s*\S.*\bresult:\s*(?:allow|deny|log)\b)")
```
canonical: gates/record_lint.py, read this session, lines 127-136:
```
        window = "\n".join(lines[max(0, i - 3):i + 1])
        m = _CANONICAL_TAG.search(window)
        cited = m.group(1).strip().strip("`") if m and m.group(1).strip() else ""
        has_executed_live = bool(cited) and bool(
            _EXECUTED_LIVE_CANONICAL.search(cited))
        ...
        has_derived = bool(_CLAIM_DERIVED_TAG.search(window))
        if not has_executed_live and not has_derived:
```

Path 1, `has_executed_live`, needs the `canonical:` tag's own cited text
to start with a shell-command token (`gh `/`git `/`pytest`/`python3
`/`npm `/`npx `/`bash `/`sh `/`./`) or match one of the two fixed result-tag shapes quoted above — a
this-turn command re-run, the evidence shape an implementation's own
claim would carry.

canonical: gates/record_lint.py, read this session, line 66:
```
_CLAIM_DERIVED_TAG = re.compile(r"`derived:\s*\S.*?`")
```
Path 2, `has_derived`, needs a backtick-quoted `derived:` tag anywhere in
the same 4-line window. An observation record CAN reach this path:

derived: `bash on-the-record/hooks/record-claim-guard.sh`, fed the same
payload shape with a backtick-quoted `derived:` line placed before the
claim:
```
## Scoreboard

`derived: docs/issue-895/transcripts/ambiguous-run.log`
- ambiguous-scenario requirement met: PASS
  canonical: execution transcript for the ambiguous-scenario run, fixture PR #15 merged 2026-08-05
```
Output: `EXIT: 0` (accepted).

canonical: gates/record_lint.py, read this session, lines 96-102 (the
function's own docstring): the intent named there is to reject a citation
with nothing behind it, while accepting a proven-live one. The check
cannot actually tell those two cases apart on its own terms — it
pattern-matches only the citation's surface shape (a command-prefixed
string, or a stand-alone backtick-quoted `derived:` tag), never what
role or process produced the underlying evidence.

canonical: this session's own start-of-session `<system-reminder>`
blocks (`record-tiering-directive`, `record-claim-citation-directive`),
read this session — neither instructs a role to add a stand-alone
backtick-quoted `derived:` line; the convention they describe for a
count/outcome claim is a plain `canonical:`/`derived:` prose line
preceding the claim, the same shape #870 additionally rejects when the
line also carries an OUTCOME marker.

canonical: gates/record_lint.py, read this session, lines 213-226
(`canonical_source_claim_check`, issue #793's own sibling check) —
accepts exactly the plain-prose `canonical: <what was read>` shape
`outcome_claim_citation_check` rejects here, so the same citation style
this survey itself relies on throughout satisfies #793 and fails #870
whenever the same line also trips the OUTCOME marker.

## Finding 4 — the refusal itself is not silent

canonical: on-the-record/hooks/record-claim-guard.sh, read this session,
lines 63-67 and 139-142:
```
def deny(msg):
    sys.stderr.write("record-claim-guard: %s\n" % msg)
    sys.exit(2)
...
if bad:
    deny("\n".join(bad))
sys.exit(0)
```
Finding 2's reproduction above shows this live: exit code 2 plus a
non-empty stderr message naming the exact violated rule. `hooks.json`
wires this script as a `PreToolUse` hook (Finding 1's citation); Claude
Code's `PreToolUse` contract feeds a hook's exit-2 stderr back to the
calling model as the tool's denial reason in the same turn — no file
under on-the-record/hooks/ or gates/ intercepts or discards a sibling
hook's stderr. The acting session's model turn receives a concrete,
named reason for the block at the moment it happens.

canonical: `gh issue view 923`, read this session — the issue body's own
account is that the #895 session ended its turn with no scoreboard PR
and with nothing said about why. That is a gap one layer above the gate
examined here: the reason reaches the model per Finding 4's first
citation, but the issue's own account shows it did not reach the human.
This survey has no #895 session transcript to re-run and does not
attempt to reproduce that separate absorption step; it names the layer
only, distinct from and not contradicting the gate-layer result above.

## Conclusion

1. The gate that fires is `record-claim-guard.sh` calling
   `gates/record_lint.py`'s `outcome_claim_citation_check` (issue #870),
   wired at on-the-record/hooks/hooks.json lines 63-65, PreToolUse
   `Write|Edit|MultiEdit` on any `docs/issue-*/reports/**` path — not
   #919/#920, which gate `Bash`/`git commit`, a surface the record-write
   itself never reaches. (Finding 1)
2. Reproduced live: an observation verdict record's natural prose
   `canonical: <transcript/measurement description>` citation is refused
   (Finding 2); a separate, stand-alone backtick-quoted `derived:
   <path>` tag placed in the same 4-line window is accepted (Finding 3)
   — a narrow escape hatch the record-authoring conventions this session
   was given never instruct a role to reach for, not a blanket refusal of
   all observation-role evidence.
3. The gate's own refusal is not silent — it prints the violated rule
   and blocks with exit 2, surfaced to the calling model that same turn
   (Finding 4, first citation). The silence #923 reports sits one layer
   above the gate — the issue's own account of that turn ending with
   nothing relayed to the human (Finding 4, second citation) — which
   this survey names but cannot itself re-reproduce without the original
   session's transcript.

## Open findings

None new beyond Findings 1-4 above; all four route to #923 step 2
(implementation), which the issue body already scopes: let an
observation/verdict record satisfy the outcome-claim gate via its
executed-live measurement citations — close Finding 3's gap by
extending `_EXECUTED_LIVE_CANONICAL`/`has_derived` to accept a plain
prose `canonical:` transcript/measurement citation as a sibling
executed-live source, not only a bare command string or a separate
stand-alone backtick-quoted `derived:` line — and make any refused
record-commit surface its reason toward the human, not only the model
(Finding 4 shows the gate already surfaces to the model; any remaining
further work belongs at the session/role-protocol layer, not
`record-claim-guard.sh`'s stderr path, which this survey shows
already fires as intended).

## What did not work

None.
