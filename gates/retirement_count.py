"""Retirement invariant: count remaining occurrences of the retired `role`
axis across this repo's py/sh sources (docs/ excluded, per the standing
rule that historical records are never touched).

Why not `grep -rn '\\brole\\b'`: `\\b` is a transition between a `\\w`
character and a non-`\\w` character. Every character that actually
continues the word "role" in this codebase -- the plural suffix `s`
(`roles`), an adjoining underscore in a snake_case identifier
(`user_role`, `role_id`), or a case change in a camelCase/PascalCase
identifier (`RoleModel`) -- is itself a `\\w` character (or, for the case
change, no non-word character at all), so `\\b` never fires there. A
single-word regex, however many alternations it grows, cannot see past
this: the miss is structural (word-boundary matching is blind to
identifier-internal joins), not a missing spelling. Hyphenated compounds
(`role-handoff`, `per-role`) and singular possessives (`role's`) are
*not* part of the gap -- `-` and `'` are already non-word characters, so
`\\brole\\b` already matches those.

The fix tokenizes each line the way an identifier is actually built --
split on every non-letter (so underscores, digits, hyphens, apostrophes,
punctuation all separate tokens) and further split camelCase/PascalCase
runs at case transitions -- then checks each resulting token
case-insensitively against the retired axis's two English inflections:
the bare noun and its regular plural. That is a closed, 2-item
population derived from how the word is actually used in source (noun,
not verb; this codebase has no "roled"/"roling"/other inflection), not
an open-ended list of spellings extended until the regex stops finding
things.
"""

import re
import subprocess
import sys

RETIRED_WORDS = {"role", "roles"}

# This detector must name what it detects -- the docstring above and
# RETIRED_WORDS itself necessarily spell "role"/"roles" literally, and its
# test suite must feed it literal "role"/"roles" fixtures to prove it still
# matches them. That is a citation of the retired axis by a named contract
# (this check and its test), not a live use of it -- the
# tokenmaxxxer-core#361 trade, not a revival -- so this file, its thin
# shell wrapper, and its test file are the fixed self-exclusion, not an
# allowlist that grows.
_SELF_EXCLUDED = {
    "gates/retirement_count.py",
    "gates/retirement_count.sh",
    "test/test_retirement_count.py",
}

_LETTER_RUN = re.compile(r"[A-Za-z]+")
_SUBWORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[a-z]+")


def tokenize(text):
    for run in _LETTER_RUN.findall(text):
        for word in _SUBWORD.findall(run):
            yield word.lower()


def line_hits(line):
    return any(tok in RETIRED_WORDS for tok in tokenize(line))


# The `*.py`/`*.sh` population itself is an enumeration, not something this
# checker can derive from first principles: "what file types can carry a
# reader/writer of a Python dict key or a shell variable" has no computable
# answer in this repo -- a `.sh` file can embed a Python heredoc
# (on-the-record/hooks/*.sh all do; pr-preflight.sh:417 was exactly this),
# so extension does not even reliably predict language. The two extensions
# here are fixed by this issue's own acceptance criteria ("population:
# py/sh sources... docs/ excluded"), not derived by this function, and are
# not extended on suspicion -- a third extension only joins this set with
# the same evidence gate #2876 used for the plural (a demonstrated miss).
def tracked_sources():
    out = subprocess.run(
        ["git", "ls-files", "*.py", "*.sh"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return [f for f in out if not f.startswith("docs/") and f not in _SELF_EXCLUDED]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--list-files"]:
        # issue #2876 round 2: the population this check walks (py/sh
        # sources, docs/ and this module's own 3 self-excluded paths) is a
        # single source of truth, not a fact for every caller to retype.
        # A repo-wide "who reads/writes this key" search hand-typing its
        # own `--include=*.py` list can silently diverge from what this
        # checker actually covers -- as pr-preflight.sh:417 did: a `.sh`
        # file invisible to a `--include=*.py`-only reader search. Pipe
        # this instead: `python3 gates/retirement_count.py --list-files |
        # xargs grep -n <pattern>`.
        for path in tracked_sources():
            print(path)
        return 0

    sites = []
    for path in tracked_sources():
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for lineno, line in enumerate(fh, start=1):
                    if line_hits(line):
                        sites.append(f"{path}:{lineno}:{line.rstrip()}")
        except OSError:
            continue

    for site in sites:
        print(site)
    print(f"retirement_count: {len(sites)} occurrence(s) of the retired "
          f"role/roles axis in py/sh sources (docs/ excluded)",
          file=sys.stderr)
    return 1 if sites else 0


if __name__ == "__main__":
    sys.exit(main())
