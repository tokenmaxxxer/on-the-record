def format_output(data, mode):
    """Shared by both the `summarize` and `report` commands (core.py).

    Seeded defect (issue #895 type 3): json mode drops the trailing
    newline that text mode has, so both call sites print a malformed
    last line. The requirement is to fix this for BOTH commands without
    breaking the other's output.
    """
    if mode == "json":
        import json

        return json.dumps(data)  # missing trailing "\n"
    return f"{data}\n"
