from pathlib import Path
EXT_LANG={".py":"Python",".go":"Go",".rs":"Rust",".java":"Java",".kt":"Kotlin",".cs":"C#",".js":"JavaScript",".ts":"TypeScript",".cpp":"C++",".c":"C"}
def inventory(root: Path):
    counts={}; tests=[]; build_files=[]; ignored={".git",".forge","node_modules","venv",".venv","__pycache__","dist","build"}
    for p in root.rglob("*"):
        if not p.is_file() or any(x in ignored for x in p.parts): continue
        ext=p.suffix.lower(); lang=EXT_LANG.get(ext)
        if lang: counts[lang]=counts.get(lang,0)+1
        if p.name.lower() in {"pyproject.toml","requirements.txt","package.json","go.mod","cargo.toml","pom.xml","build.gradle","build.gradle.kts"} or p.suffix.lower()==".csproj": build_files.append(str(p.relative_to(root)))
        if p.name.startswith("test_") or p.name.endswith("_test.py") or "tests" in p.parts: tests.append(str(p.relative_to(root)))
    return {"root":str(root.resolve()),"languages":counts,"build_files":build_files[:200],"tests":tests[:200],"status":"OBSERVED"}
