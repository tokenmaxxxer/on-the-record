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
    injected = []  # issue #2124: cross-family skills injected by the directive
    invoked = set()
    # The spawn directive names the injected cross-family set verbatim:
    # "(이 중 X, Y 는 이번 과제 텍스트와의 키워드 매치로 추가된 크로스-패밀리
    # 스킬 — 이슈 #2001)". The name-charset restriction keeps quoted source
    # code containing the same template (with \" escapes) from matching.
    inj_re = re.compile(r"이 중 ([a-z0-9-]+(?:, [a-z0-9-]+)*) 는 이번 과제 "
                        r"텍스트와의 키워드 매치로 추가된 크로스-패밀리")
    # issue #2124 fast-path picks are ledger-tagged, and also appear in the
    # same directive clause; nothing extra to parse here.
    call_re = re.compile(r'"name":"Skill","input":\{[^}]*"skill":"([^"]+)"')
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
                for m in call_re.finditer(line):
                    invoked.add(m.group(1))
            if not injected and "크로스-패밀리" in line:
                m = inj_re.search(line)
                if m:
                    injected = m.group(1).split(", ")
    if not joinable:
        return {"base": base, "path": path, "status": "unmeasurable", "reason": "no-init-plugins-line"}
    orphaned = [s for s in injected if s not in invoked]
    return {"base": base, "path": path, "status": "measured",
            "mounted": mounted, "mounted_count": len(mounted),
            "skill_calls": skill_calls,
            "injected_cross_family": injected,
            "invoked_skills": sorted(invoked),
            "orphaned_cross_family": orphaned}

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
    # issue #2124: aggregate orphan-injection rate (injected cross-family
    # skills that were never invoked in their session).
    inj = sum(len(r.get("injected_cross_family", [])) for r in results
              if r.get("status") == "measured")
    orph = sum(len(r.get("orphaned_cross_family", [])) for r in results
               if r.get("status") == "measured")
    print(json.dumps({"summary": "orphan-injection-rate",
                      "injected_total": inj, "orphaned_total": orph,
                      "orphan_rate": (round(orph / inj, 3) if inj else None)}))
