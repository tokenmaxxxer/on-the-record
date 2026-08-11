import argparse

__version__ = "0.1.0"


def _build_parser():
    parser = argparse.ArgumentParser(prog="fixture-feature")
    subparsers = parser.add_subparsers(dest="command")
    greet = subparsers.add_parser("greet")
    greet.add_argument("name")
    # Requirement (issue #895 type 2): add a --format json|text flag here,
    # default "text". Not present yet — this is the seeded missing feature.
    return parser


def greet(name):
    return f"Hello, {name}!"


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "greet":
        print(greet(args.name))
        return
    parser.print_help()


if __name__ == "__main__":
    main()
