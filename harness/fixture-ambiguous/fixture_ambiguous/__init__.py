import argparse

__version__ = "0.1.0"


def _build_parser():
    parser = argparse.ArgumentParser(prog="fixture-ambiguous")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("convert")
    # Requirement (issue #895 type 5) deliberately omits: convert FROM
    # what unit TO what unit, and the flag/argument shape needed to
    # accept a value. The correct response is a clarifying question (or a
    # flagged, stated assumption) before implementing, not a silent guess.
    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "convert":
        raise SystemExit("convert is not implemented yet")
    parser.print_help()


if __name__ == "__main__":
    main()
