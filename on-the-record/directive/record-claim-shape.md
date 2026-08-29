<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. Guidance landing for the demoted record-claim-shape-directive.sh (issue #2138 disposition, row 4) — the citation shape record-claim-guard.sh still enforces at write time. -->

record-claim-guard.sh (gates/record_lint.py) checks every write under
docs/issue-*/reports/** for this shape, in this order — cite correctly
the first time instead of learning it from a refusal:

1. bare count/ratio claim (issue #333): a bare "N of M"/"N items" count
   needs `derived:` or a code-fence reproduction — fences are excluded.
2. `unverifiable:` line (issue #310): an `unverifiable:` escape line
   needs a reason.
3. `checked: ... — result: unverifiable` line (issue #331): an
   Acceptance-verification `unverifiable` result needs a reason.
4. backtick-quoted path reference (issue #330): a backtick-quoted
   relative path must resolve somewhere in the working tree.
5. state/defect claim with no canonical source (issue #793): a
   state/defect-claim line (session output "found", session/PR/board state
   "halted|merged|closed|is running|is gone|is stale", or a bare count
   claim) needs a `canonical: <what was read>` tag within 3 lines above
   it, citing the actual session's record/diff, raw ground-truth command
   output, or file:line-context read — not a summary/grep/watcher signal
   with nothing named.
6. outcome claim with no executed-live citation (issue #870): an OUTCOME
   claim ("requirement(s) met", "done", "PASS(es/ed)", "complete(d)")
   needs a `canonical:` tag within 3 lines above it whose cited source is
   itself an executed-live reference (a command string, an
   `acceptance: <command> — result: ...` line, or — issue #923 — a
   citation naming the transcript/measurement an observation/verdict
   record's own live run produced) — not a bare file-read/summary
   citation. Fail-closed: no qualifying citation -> refused.
7. defect/root-cause claim with no grounded citation (issue #791): a
   defect/root-cause claim needs grounded evidence, not a bare
   grep/keyword hit — either (a) a fenced quote of >=3 contiguous lines
   verbatim-matching (whitespace-normalized) the cited `file:line` range
   in the working tree, or (b) a `derived: <command>` fenced
   reproduction. Grep/keyword search stays legal for locating a
   candidate; it is not itself evidence for the claim.
