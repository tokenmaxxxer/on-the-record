import json, re, glob, os, collections

WORK_DIR = os.path.expanduser("~/.tokenmaxxxer/work/")

def latest_logs(n):
    files = glob.glob(WORK_DIR + "*.session*.log")
    files.sort(key=os.path.getmtime, reverse=True)
    # dedupe by base task name (strip .session...  suffix) keeping most recent log
    seen = set()
    out = []
    for f in files:
        base = re.sub(r"\.session(\.\d{8}T\d{6}\.\d+)?\.log$", "", os.path.basename(f))
        if base in seen:
            continue
        seen.add(base)
        out.append((base, f))
        if len(out) >= n:
            break
    return out

def analyze(base, path):
    try:
        size = os.path.getsize(path)
    except OSError:
        return {"base": base, "path": path, "status": "unmeasurable", "reason": "stat-failed"}
    mounted = None
    skill_calls = 0
    joinable = False
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            if '"subtype":"init"' in line and '"plugins":[' in line:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                plugins = obj.get("plugins", [])
                mounted = [p["name"] for p in plugins
                           if "/skill-registry/skills/" in p.get("path", "")]
                joinable = True
            if '"name":"Skill"' in line and '"type":"tool_use"' in line:
                skill_calls += line.count('"name":"Skill"')
    if not joinable:
        return {"base": base, "path": path, "status": "unmeasurable", "reason": "no-init-plugins-line"}
    return {"base": base, "path": path, "status": "measured",
            "mounted": mounted, "mounted_count": len(mounted),
            "skill_calls": skill_calls}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # explicit log paths (issue #1960 phase B re-measurement: point at a
        # specific fresh sample instead of "N most recent under WORK_DIR",
        # so a re-measurement sample can be pinned to sessions spawned after
        # a given change lands rather than drifting with whatever else runs
        # in the meantime).
        pairs = [(re.sub(r"\.session(\.\d{8}T\d{6}\.\d+)?\.log$", "", os.path.basename(p)), p)
                 for p in sys.argv[1:]]
    else:
        N = 40
        pairs = latest_logs(N)
    results = [analyze(b, p) for b, p in pairs]
    for r in results:
        print(json.dumps(r))
