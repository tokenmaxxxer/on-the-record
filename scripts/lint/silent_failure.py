#!/usr/bin/env python3
"""Static lint for one recurring defect class (issue #3228): a subprocess
call site whose failure to observe (a hang, a non-zero exit) reports the
same value a genuine, benign observation would have reported. Two of the
seven independently-found defects this issue names lived in exactly this
shape (scripts/issue-3127/verify_preregistration.py's missing timeouts,
and its git-failure/empty-result conflation) -- see
docs/issue-3228/reports/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103.md
for why this mechanism was chosen over the other three candidates the
issue weighed, and which of the seven it does and does not catch.

Three rules, each a plain AST fact -- no type inference, no dataflow
across functions:

  SF001 missing-timeout: a `subprocess.run`/`Popen`/`check_output`/
        `check_call` call has no `timeout=` keyword. Without one, a hung
        child process blocks forever instead of the caller ever learning
        it could not observe the result.
  SF002 unchecked-returncode: a `subprocess.run` call's result is never
        referenced by `.returncode` anywhere in the enclosing function
        (and `check=True` was not passed, which raises automatically on
        a non-zero exit). Nothing in the function can ever tell a failed
        process apart from one that exited 0.
  SF003 sentinel-on-failure: a branch guarded by a `.returncode` compare
        (e.g. `if r.returncode != 0:`) returns a bare sentinel literal
        (None/False/0/""/[]/{})  that the SAME function also returns,
        unconditionally, from a genuinely-different, non-failure branch.
        The failure path and the "nothing to report" path become the
        same value one line apart -- the literal shape of the defect
        this issue is named for.

A single-line trailing comment `# silent-failure: allow <reason>` on the
call's own source line exempts that call from SF001/SF002, or on the
guarding `if`'s own line exempts that branch from SF003 -- for the rare
case where an author has a documented reason (fire-and-forget dispatch,
a wrapper that already enforces a timeout upstream, or -- SF003's real
false-positive case, found by running this lint over this repo's own
`_pr_merge_commit`/`_repo_owner_repo`-shaped helpers -- every failure
mode of a function genuinely collapsing to the SAME uniform "fail
closed, exclude" action at every call site, never to two DIFFERENT
actions depending on which failure occurred). SF003 has no blanket
exemption from being checked at all, only this same per-site,
documented escape hatch as SF001/SF002 -- a silent, unexplained
exemption would defeat the rule as completely as never running it.

Usage:
  python3 scripts/lint/silent_failure.py <path> [<path> ...]
      Scans the given files (or every *.py file under given directories,
      skipping __pycache__), prints every SF00x finding and every file
      this scan could not read or parse (never silently skipped), and
      exits 0 only if it examined at least one subprocess call site
      across all targets and found neither findings nor read/parse
      errors. Zero call sites total is itself a failure -- see
      `scan_targets()`.
  python3 scripts/lint/silent_failure.py --self-check
      Runs the mechanism against its own bundled fixtures
      (scripts/lint/fixtures/silent_failure/) and exits nonzero the
      moment any expectation about its own behavior stops holding --
      this is the regression detector for the lint itself, not a scan
      of the working tree.
"""
from __future__ import annotations

import ast
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

_SUBPROCESS_ATTRS = {"run", "Popen", "check_output", "check_call"}
_SENTINEL_TYPES = (type(None), bool, int, float, str)
_ALLOW_MARKER = "silent-failure: allow"


@dataclass
class Finding:
    path: Path
    line: int
    rule_id: str
    message: str
    remedy: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule_id}] {self.message} -- {self.remedy}"


@dataclass
class FileResult:
    path: Path
    findings: list = field(default_factory=list)
    error: "str | None" = None
    call_sites: int = 0


def _literal_key(node: ast.AST):
    """A hashable identity for a return value AST node if (and only if)
    it is a bare literal this lint treats as a "nothing observed"
    sentinel -- None/True/False/an int/a float/a string, or a 2+ tuple
    whose FIRST element is one of those (the `(bool, str)` verdict shape
    this repo's own check_* functions use). Anything else (a name, a
    call, an f-string, a raised exception) returns None -- "not a
    sentinel this rule reasons about", never treated as a match by
    accident."""
    if isinstance(node, ast.Constant) and isinstance(node.value, _SENTINEL_TYPES):
        return ("const", node.value)
    if isinstance(node, ast.Tuple) and node.elts:
        head = node.elts[0]
        if isinstance(head, ast.Constant) and isinstance(head.value, _SENTINEL_TYPES):
            return ("tuple-head", head.value)
    if isinstance(node, ast.List) and not node.elts:
        return ("empty-list",)
    if isinstance(node, ast.Dict) and not node.keys:
        return ("empty-dict",)
    return None


def _sentinel_keys(node) -> set:
    """Every sentinel identity `node` could evaluate to. For a bare
    literal this is at most one key (`_literal_key`); for a conditional
    expression (`X if cond else None`, the exact shape
    `_first_commit_for_path`'s real pre-repair `return lines[0] if lines
    else None` has) it is the union of both branches' keys, recursively
    -- a sentinel hiding behind a ternary's `orelse` is exactly as
    "returned by this function" as a bare `return None` would be, and
    must not be missed just because of how the return expression is
    spelled."""
    if node is None:
        key = ("const", None)
        return {key}
    if isinstance(node, ast.IfExp):
        return _sentinel_keys(node.body) | _sentinel_keys(node.orelse)
    key = _literal_key(node)
    return {key} if key is not None else set()


class _Scope:
    """Bookkeeping for one function body (or the module, for code outside
    any function -- return statements can't occur there, but subprocess
    calls can). Kept separate per enclosing function so a call inside an
    inner nested function is never attributed to its outer function."""

    def __init__(self):
        self.calls = []          # list[(call_node, target_name_or_None)]
        self.returncode_refs = set()   # var names with a `.returncode` access anywhere
        self.returns = []        # list[ast.Return]
        self.guarded_returns = {}  # id(Return) -> guarding If node, for returncode-guarded ones


def _assign_targets(tree: ast.AST) -> dict:
    """Maps `id(value_node) -> variable name` for every `x = <value>`
    assignment in the file, single-Name targets only. Built as one
    upfront pass (rather than during the main scope-tracking walk) so
    `visit_Call` can look up "was this call's result assigned to a
    variable" without needing parent pointers."""
    targets = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            targets[id(node.value)] = node.targets[0].id
    return targets


def _raw_returned_call_ids(tree: ast.AST) -> set:
    """`id()`s of every Call node that IS (not merely contains) a
    `return`'s whole value -- `return subprocess.run(...)`, the shape
    `_run_git`'s real repaired code uses. A thin wrapper that hands the
    raw `CompletedProcess` straight to its caller is deferring the
    returncode check to that caller by design; SF002 must not demand the
    wrapper itself check what it deliberately passes through unexamined
    -- only a call whose result is bound to a variable and then never
    inspected, or silently discarded some other way, is suspicious."""
    return {id(node.value) for node in ast.walk(tree)
            if isinstance(node, ast.Return) and node.value is not None}


class _Visitor(ast.NodeVisitor):
    def __init__(self, lines: list, assign_targets: dict, raw_returned_call_ids: set):
        self.lines = lines
        self.assign_targets = assign_targets
        self.raw_returned_call_ids = raw_returned_call_ids
        self.subprocess_names = set()   # bare names imported via `from subprocess import X`
        self.subprocess_aliases = set()  # module aliases for `import subprocess as X`
        self.scopes = [_Scope()]  # stack; index 0 is module-level pseudo-scope

    # -- import tracking --------------------------------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "subprocess":
                self.subprocess_aliases.add(alias.asname or "subprocess")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module == "subprocess":
            for alias in node.names:
                if alias.name in _SUBPROCESS_ATTRS:
                    self.subprocess_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    # -- scope tracking -----------------------------------------------------
    def _push_scope(self):
        self.scopes.append(_Scope())

    def _pop_scope(self) -> _Scope:
        return self.scopes.pop()

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

    def _visit_function(self, node):
        self._push_scope()
        self.generic_visit(node)
        finished = self._pop_scope()
        node._sf_scope = finished  # stash for check_rules()

    # -- data collection within the current scope ---------------------------
    def _is_subprocess_call(self, call: ast.Call) -> bool:
        func = call.func
        if isinstance(func, ast.Attribute) and func.attr in _SUBPROCESS_ATTRS:
            if isinstance(func.value, ast.Name) and func.value.id in self.subprocess_aliases:
                return True
        if isinstance(func, ast.Name) and func.id in self.subprocess_names:
            return True
        return False

    def visit_Call(self, node: ast.Call):
        # Deliberately generic (not `visit_Assign`/`visit_Expr`-scoped):
        # a subprocess call is just as real a call site when it's the
        # expression of a `return subprocess.run(...)`, a comprehension,
        # or an argument to another call -- `_first_commit_for_path`'s own
        # `_run_git(...)` call site is exactly the `return`-embedded
        # shape, and restricting detection to statement-level Assign/Expr
        # nodes would silently miss it, which is the one failure mode
        # this lint itself must never have.
        if self._is_subprocess_call(node):
            target = self.assign_targets.get(id(node))
            is_raw_return = id(node) in self.raw_returned_call_ids
            self.scopes[-1].calls.append((node, target, is_raw_return))
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr == "returncode" and isinstance(node.value, ast.Name):
            self.scopes[-1].returncode_refs.add(node.value.id)
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return):
        self.scopes[-1].returns.append(node)
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        guards_returncode = any(
            isinstance(n, ast.Attribute) and n.attr == "returncode"
            for n in ast.walk(node.test)
        )
        self.generic_visit(node)
        if guards_returncode:
            scope = self.scopes[-1]
            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    scope.guarded_returns[id(stmt)] = node

    def _line_has_allow_marker(self, node: ast.AST) -> bool:
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", start)
        if start is None:
            return False
        for lineno in range(start, (end or start) + 1):
            if 1 <= lineno <= len(self.lines) and _ALLOW_MARKER in self.lines[lineno - 1]:
                return True
        return False

    def check_rules(self, path: Path) -> list:
        findings = []
        for scope in self._all_scopes_including_module():
            findings.extend(self._check_scope(path, scope))
        return findings

    def _all_scopes_including_module(self):
        # The module-level scope is whatever is left on the stack after
        # the walk finishes (index 0); every function's own scope was
        # stashed on its node by `_visit_function`.
        yield self.scopes[0]
        for node in ast.walk(self._root):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield node._sf_scope

    def _check_scope(self, path: Path, scope: _Scope) -> list:
        findings = []
        for call, target, is_raw_return in scope.calls:
            has_timeout = any(kw.arg == "timeout" for kw in call.keywords)
            has_check_true = any(
                kw.arg == "check" and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
                for kw in call.keywords
            )
            allowed = self._line_has_allow_marker(call)
            if not has_timeout and not allowed:
                findings.append(Finding(
                    path, call.lineno, "SF001",
                    "subprocess call has no explicit timeout=",
                    "add timeout=<seconds> and handle subprocess.TimeoutExpired, "
                    "or add a trailing '# silent-failure: allow <reason>' comment "
                    "on this call's line if a hang here is genuinely impossible"))
            if has_check_true or allowed or is_raw_return:
                # check=True raises on failure automatically; a raw
                # `return subprocess.run(...)` hands the whole
                # CompletedProcess to the caller by design, deferring the
                # returncode check rather than dropping it.
                continue
            if target is not None:
                if target not in scope.returncode_refs:
                    findings.append(Finding(
                        path, call.lineno, "SF002",
                        f"'{target}.returncode' is never checked in this function",
                        f"branch on {target}.returncode before trusting {target}.stdout, "
                        "or pass check=True to raise on a non-zero exit"))
            else:
                findings.append(Finding(
                    path, call.lineno, "SF002",
                    "subprocess call's result is discarded -- returncode can never be checked",
                    "assign the result to a variable and branch on its .returncode, "
                    "or pass check=True"))
        for ret in scope.returns:
            guard = scope.guarded_returns.get(id(ret))
            if guard is None or self._line_has_allow_marker(guard):
                continue
            keys = _sentinel_keys(ret.value)
            if not keys:
                continue
            for other in scope.returns:
                if other is ret or id(other) in scope.guarded_returns:
                    continue
                if keys & _sentinel_keys(other.value):
                    returned_shape = ast.dump(ret.value) if ret.value is not None else "None"
                    findings.append(Finding(
                        path, guard.lineno, "SF003",
                        f"the returncode-failure branch at line {ret.lineno} returns "
                        f"{returned_shape}, the same value line {other.lineno} returns "
                        "for a genuinely different, non-failure reason",
                        "return/raise something distinguishable from a legitimate "
                        "empty observation on the returncode-failure path (e.g. raise "
                        "an exception, or return a different sentinel) so the two "
                        "conditions can never be confused downstream"))
                    break
        return findings


def scan_file(path: Path) -> FileResult:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return FileResult(path=path, error=f"cannot read: {type(exc).__name__}: {exc}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return FileResult(path=path, error=f"cannot decode as utf-8: {exc}")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return FileResult(path=path, error=f"syntax error: {exc}")
    lines = text.splitlines()
    visitor = _Visitor(lines, _assign_targets(tree), _raw_returned_call_ids(tree))
    visitor._root = tree
    visitor.visit(tree)
    call_sites = sum(len(s.calls) for s in visitor._all_scopes_including_module())
    findings = visitor.check_rules(path)
    return FileResult(path=path, findings=findings, call_sites=call_sites)


def _expand_targets(paths) -> list:
    out = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            out.extend(sorted(
                f for f in p.rglob("*.py") if "__pycache__" not in f.parts))
        else:
            out.append(p)
    return out


@dataclass
class ScanSummary:
    findings: list
    errors: list  # list[(Path, str)]
    call_sites: int
    files_scanned: int


def scan_targets(paths) -> ScanSummary:
    targets = _expand_targets(paths)
    findings, errors, call_sites = [], [], 0
    for t in targets:
        r = scan_file(t)
        call_sites += r.call_sites
        if r.error is not None:
            errors.append((t, r.error))
        findings.extend(r.findings)
    return ScanSummary(findings, errors, call_sites, len(targets))


def _run_scan(paths) -> int:
    summary = scan_targets(paths)
    for t, err in summary.errors:
        print(f"ERROR {t}: {err}")
    for f in summary.findings:
        print(f.render())
    if summary.files_scanned == 0:
        print("no .py files found under the given target(s)")
        return 1
    if summary.errors:
        return 1
    if summary.call_sites == 0:
        print("no subprocess call sites found across the scanned target(s) -- "
              "refusing to report a clean pass (a scan that examined nothing "
              "is not distinguishable from a broken scan)")
        return 1
    if summary.findings:
        return 1
    print(f"OK: {summary.call_sites} subprocess call site(s) across "
          f"{summary.files_scanned} file(s), no findings")
    return 0


# ---------------------------------------------------------------------------
# --self-check
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).parent / "fixtures" / "silent_failure"

# The seven defects issue #3228 names, and this mechanism's own verdict on
# each -- kept next to the fixtures it is checked against so a change to
# either is visible in the same diff.
_CAUGHT_BEFORE = [
    "site3_git_failure_conflation.py",
    "site4_missing_timeout.py",
]
_MISSED_BEFORE = [
    "site1_2_consumer_preconditions.py",
    "site5_delegation_state_wildcard.py",
    "site6_forgeable_evidence.py",
    "site7_amendment_channel_fixture.py",
]
_ALL_AFTER = _CAUGHT_BEFORE + _MISSED_BEFORE


def run_self_check(verbose: bool = True) -> bool:
    assertions = []

    for name in _CAUGHT_BEFORE:
        r = scan_file(_FIXTURES / "history_before" / name)
        assertions.append((
            f"history_before/{name}: pre-repair shape is flagged",
            r.error is None and len(r.findings) > 0))

    for name in _MISSED_BEFORE:
        r = scan_file(_FIXTURES / "history_before" / name)
        assertions.append((
            f"history_before/{name}: outside this mechanism's documented "
            "scope (not a subprocess-observation defect)",
            r.error is None))

    for name in _ALL_AFTER:
        r = scan_file(_FIXTURES / "history_after" / name)
        assertions.append((
            f"history_after/{name}: repaired shape stays quiet",
            r.error is None and len(r.findings) == 0))

    # must-not: a file this lint cannot read is reported, never skipped.
    missing = _FIXTURES / "unreadable" / "does_not_exist.py"
    r = scan_file(missing)
    assertions.append((
        "a nonexistent/unreadable file reports an error, not a silent skip",
        r.error is not None))

    if hasattr(os, "geteuid") and os.geteuid() != 0:
        real_unreadable = _FIXTURES / "unreadable" / "_chmod000.py"
        real_unreadable.parent.mkdir(parents=True, exist_ok=True)
        real_unreadable.write_text("import subprocess\n", encoding="utf-8")
        os.chmod(real_unreadable, 0o000)
        try:
            r = scan_file(real_unreadable)
            assertions.append((
                "a permission-denied file reports an error, not a silent skip",
                r.error is not None))
        finally:
            os.chmod(real_unreadable, 0o644)
            real_unreadable.unlink()

    # must-not: a syntax error is reported, never silently parsed as "no findings".
    r = scan_file(_FIXTURES / "syntax_error" / "bad_syntax.py")
    assertions.append((
        "a file with a syntax error reports an error, not a silent skip",
        r.error is not None))

    # empty state: a target with zero subprocess call sites refuses to pass.
    summary = scan_targets([str(_FIXTURES / "no_subprocess")])
    assertions.append((
        "a target with zero subprocess call sites is distinguished from a clean pass",
        summary.call_sites == 0 and not summary.errors))
    exit_code = _run_scan([str(_FIXTURES / "no_subprocess")])
    assertions.append((
        "scanning that same zero-call-site target end-to-end exits nonzero",
        exit_code != 0))

    ok = True
    for label, passed in assertions:
        if verbose:
            print(f"{'PASS' if passed else 'FAIL'}: {label}")
        ok = ok and passed
    return ok


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--self-check" in argv:
        return 0 if run_self_check() else 1
    if not argv:
        print(__doc__)
        return 1
    return _run_scan(argv)


if __name__ == "__main__":
    sys.exit(main())
