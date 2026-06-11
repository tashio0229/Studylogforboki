#!/usr/bin/env python3
"""exercise-log.md の演習テーブルを app.html に注入する。
使い方: python3 build_app.py  （このディレクトリで実行）
"""
import json, re, pathlib

base = pathlib.Path(__file__).parent
md = (base / "exercise-log.md").read_text(encoding="utf-8")
html_path = base / "app.html"
html = html_path.read_text(encoding="utf-8")

rows = []
in_log = False
for line in md.splitlines():
    if line.startswith("## 演習ログ"):
        in_log = True
        continue
    if not in_log or not line.startswith("|"):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 8 or cells[0] in ("問題番号", ":---", "---------"):
        continue
    if set(cells[0]) <= set("-: "):
        continue
    pid, title, subject, mark, date, nxt, count, memo = cells[:8]
    rows.append({
        "id": pid, "title": title, "subject": subject, "mark": mark,
        "date": "" if date == "-" else date,
        "next": "" if nxt == "-" else nxt,
        "count": int(count) if count.isdigit() else 0,
        "memo": memo,
    })

data_js = "const PROBLEMS = " + json.dumps(rows, ensure_ascii=False, indent=1) + ";"
html = re.sub(
    r"/\*DATA_START\*/.*?/\*DATA_END\*/",
    "/*DATA_START*/\n" + data_js + "\n/*DATA_END*/",
    html, flags=re.S,
)
html_path.write_text(html, encoding="utf-8")
print(f"OK: {len(rows)} problems injected into app.html")
