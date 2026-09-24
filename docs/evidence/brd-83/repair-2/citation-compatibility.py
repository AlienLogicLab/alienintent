import importlib.util, json, subprocess, sys, tempfile, pathlib
def load(rev, name):
    src = subprocess.run(["git", "show", f"{rev}:tools/live/release_admission.py"], capture_output=True, text=True, check=True).stdout
    p = pathlib.Path(tempfile.mkdtemp()) / f"{name}.py"; p.write_text(src)
    spec = importlib.util.spec_from_file_location(name, p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
old = load("9b42ad5", "ra_old")
spec = importlib.util.spec_from_file_location("ra_new", "tools/live/release_admission.py"); new = importlib.util.module_from_spec(spec); spec.loader.exec_module(new)
issues = [i for i in json.load(open("/tmp/brd83-issues.json")) if "pull_request" not in i]
comments = json.load(open("/tmp/brd83-comments.json"))
texts = [(f"#{i['number']} body", i.get("body") or "") for i in issues]
texts += [(f"#{c['issue_url'].rsplit('/',1)[1]} comment {c['id']}", c.get("body") or "") for c in comments]
resolved = differ = 0
for label, t in texts:
    a, b = old.assessment_record_path(t), new.assessment_record_path(t)
    if a or b:
        resolved += 1
        same = a == b; differ += not same
        print(f"{label}: {'SAME' if same else 'DIFFER'} {a} -> {b}")
print(f"{len(issues)} Issue bodies and {len(comments)} comments; {resolved} resolve a record; {differ} differ between 9b42ad5 and the repair")
sys.exit(1 if differ else 0)
