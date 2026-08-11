import argparse

__version__ = "0.1.0"


def _build_parser():
    parser = argparse.ArgumentParser(prog="fixture-infeasible")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run")
    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "run":
        print("ok")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
