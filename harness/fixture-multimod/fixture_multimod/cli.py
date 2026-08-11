import argparse

from fixture_multimod.core import report, summarize


def _build_parser():
    parser = argparse.ArgumentParser(prog="fixture-multimod")
    subparsers = parser.add_subparsers(dest="command")

    summarize_p = subparsers.add_parser("summarize")
    summarize_p.add_argument("--mode", choices=["text", "json"], default="text")
    summarize_p.add_argument("items", nargs="*")

    report_p = subparsers.add_parser("report")
    report_p.add_argument("--mode", choices=["text", "json"], default="text")
    report_p.add_argument("items", nargs="*")

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "summarize":
        print(summarize(args.items, args.mode), end="")
        return
    if args.command == "report":
        print(report(args.items, args.mode), end="")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
