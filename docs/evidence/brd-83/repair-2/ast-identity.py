import ast, subprocess, sys
NAMES = ("admit", "biu_from_body", "disposition_from_record", "disposition_from_native_comment",
         "project_status_from_issue", "main")
def funcs(src):
    return {n.name: ast.dump(n) for n in ast.parse(src).body if isinstance(n, ast.FunctionDef)}
imp = funcs(subprocess.run(["git", "show", "1439457:tools/live/release_admission.py"], capture_output=True, text=True, check=True).stdout)
prev = funcs(subprocess.run(["git", "show", "9b42ad5:tools/live/release_admission.py"], capture_output=True, text=True, check=True).stdout)
cur = funcs(open("tools/live/release_admission.py").read())
for n in NAMES:
    print(f"{n:34} identical_to_import={imp.get(n) == cur.get(n)!s:5} identical_to_9b42ad5={prev.get(n) == cur.get(n)}")
print("functions changed since 9b42ad5:", sorted(k for k in set(prev) | set(cur) if prev.get(k) != cur.get(k)))
