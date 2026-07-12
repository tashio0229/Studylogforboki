#!/usr/bin/env python3
"""exercise-log.md から Obsidian 用の問題ノート（1問=1ノート）を自動生成する。

設計: exercise-log.md が唯一の正。このスクリプトの出力（.secretary/study/問題ノート/）は
完全な派生物であり、毎回フォルダごと作り直す（冪等）。手で編集してはいけない。
実行: python3 tools/generate_vault_views.py
"""
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / ".secretary/study/exercise-log.md"
OUT = REPO / ".secretary/study/問題ノート"

# 工原テキスト章 → 型カード（該当章のみ）
CARD_BY_CHAPTER = {
    12: "型カード④ 連産品の推定市価按分",
    13: "型カード③ 標準原価の差異と会計処理",
    14: "型カード② 全部vs直接・固定費調整",
    15: "型カード⑥ CVP応用",
    16: "型カード⑤ 販売数量差異の分解",
    18: "型カード① 差額原価の意思決定",
}

ROW = re.compile(r"^\|\s*([TPC][0-9][^|]*?)\s*\|")


def sanitize(name: str) -> str:
    """ファイル名に使えない文字を全角等へ退避"""
    table = {"/": "／", "\\": "＼", ":": "：", "*": "＊", "?": "？",
             '"': "”", "<": "〈", ">": "〉", "|": "｜"}
    for k, v in table.items():
        name = name.replace(k, v)
    return name.strip()


def parse_rows(text: str):
    for line in text.splitlines():
        if not ROW.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            continue
        pid, subtitle, subject_raw, grade, solved, due, reps, memo = cells[:8]
        yield {
            "id": pid, "subtitle": subtitle, "subject_raw": subject_raw,
            "grade": grade, "solved": solved, "due": due,
            "reps": reps, "memo": memo,
        }


def classify(pid: str, subject_raw: str):
    if pid.startswith("C"):
        subject, kind = "商会", "テキスト例題"
    elif pid.startswith("P"):
        subject, kind = "工原", "問題集"
    else:
        subject, kind = "工原", "テキスト例題"
    m = re.search(r"第(\d+)章", subject_raw)
    chapter_no = int(m.group(1)) if m else None
    # 章表記が無い行は科目プレフィックスを落とした残りを章ラベルに使う
    label = re.sub(r"^(工業|商業|原計)\s*(#\d+(-\d+)?)?\s*", "", subject_raw).strip()
    if chapter_no:
        rest = re.sub(r"^第\d+章\s*", "", label)
        chapter = f"第{chapter_no}章 {rest}".strip()
    else:
        chapter = label or subject_raw
    return subject, kind, chapter_no, chapter


def is_date(s: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", s))


def build_note(r) -> str:
    subject, kind, chapter_no, chapter = classify(r["id"], r["subject_raw"])
    # 要対策 = 現在も△/✕で、かつメモに要対策の記載がある問題のみ（○化済みは除外）
    flagged = ("要対策" in r["memo"]) and (r["grade"] in ("△", "✕"))
    reps = r["reps"] if r["reps"].isdigit() else ""
    lines = ["---"]
    lines.append(f'id: "{r["id"]}"')
    lines.append(f'subtitle: "{r["subtitle"]}"')
    lines.append(f'subject: "{subject}"')
    lines.append(f'kind: "{kind}"')
    lines.append(f'chapter: "{chapter}"')
    if chapter_no:
        lines.append(f"chapter_no: {chapter_no}")
    lines.append(f'grade: "{r["grade"]}"')
    if is_date(r["solved"]):
        lines.append(f'solved: {r["solved"]}')
    if is_date(r["due"]):
        lines.append(f'due: {r["due"]}')
    if reps:
        lines.append(f"reps: {reps}")
    lines.append(f"flagged: {str(flagged).lower()}")
    lines.append("tags:")
    lines.append("  - 問題")
    lines.append("---")
    lines.append("")
    lines.append(f"# {r['id']}「{r['subtitle']}」")
    lines.append("")
    lines.append("> [!warning] 自動生成ノート")
    lines.append("> このノートは `tools/generate_vault_views.py` が [[exercise-log|演習ログ]] から生成した派生物。**手で編集しない**（次回生成で消える）。記録の更新は演習ログ側で行う。")
    lines.append("")
    if r["memo"] and r["memo"] != "-":
        lines.append("## 履歴メモ（演習ログより）")
        lines.append("")
        lines.append(r["memo"])
        lines.append("")
    if subject == "工原" and chapter_no in CARD_BY_CHAPTER:
        lines.append(f"関連: [[{CARD_BY_CHAPTER[chapter_no]}]]")
        lines.append("")
    return "\n".join(lines)


def main():
    text = LOG.read_text(encoding="utf-8")
    rows = list(parse_rows(text))
    if not rows:
        sys.exit("no rows parsed — abort")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    names = set()
    for r in rows:
        base = sanitize(f'{r["id"]} {r["subtitle"]}')[:80]
        if base in names:  # 念のため衝突回避
            base = f'{base} ({len(names)})'
        names.add(base)
        (OUT / f"{base}.md").write_text(build_note(r), encoding="utf-8")
    # 検証サマリー
    grades = {}
    for r in rows:
        grades[r["grade"]] = grades.get(r["grade"], 0) + 1
    print(f"generated {len(rows)} notes -> {OUT}")
    print("grade counts:", dict(sorted(grades.items())))


if __name__ == "__main__":
    main()
