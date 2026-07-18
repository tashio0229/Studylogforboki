#!/usr/bin/env python3
"""exercise-log.md から Obsidian 用のノート群を自動生成する。

生成物（すべて exercise-log.md からの派生・毎回フォルダごと作り直す冪等動作）:
  .secretary/study/問題ノート/  … 1問=1ノート（Basesが集計する層）
  .secretary/study/章ノート/    … 科目ノート2枚＋章ノート37枚（グラフの樹形図を作る層）

グラフ設計: 科目（工原/商会）→ 章 → 問題 の樹形。問題は自分の章にだけ繋がり（演習ログの巨大ハブは張らない）、
型カード（解法パターン）だけが章をまたぐ横断リンクとして残る。

実行: python3 tools/generate_vault_views.py
"""
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / ".secretary/study/exercise-log.md"
OUT = REPO / ".secretary/study/問題ノート"
OUT_STRUCT = REPO / ".secretary/study/章ノート"

# 工原テキスト章 → 型カード（該当章のみ・横断リンク）
CARD_BY_CHAPTER = {
    12: "型カード④ 連産品の推定市価按分",
    13: "型カード③ 標準原価の差異と会計処理",
    14: "型カード② 全部vs直接・固定費調整",
    15: "型カード⑥ CVP応用",
    16: "型カード⑤ 販売数量差異の分解",
    18: "型カード① 差額原価の意思決定",
}

ROW = re.compile(r"^\|\s*([TPC][0-9][^|]*?)\s*\|")
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"
GRADE_ICON = {"○": "🟢", "△": "🟠", "✕": "🔴"}


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
    label = re.sub(r"^(工業|商業|原計)\s*(#\d+(-\d+)?)?\s*", "", subject_raw).strip()
    if chapter_no:
        rest = re.sub(r"^第\d+章\s*", "", label)
        chapter = f"第{chapter_no}章 {rest}".strip()
    else:
        chapter = label or subject_raw
    return subject, kind, chapter_no, chapter


def chapter_group(pid: str, subject_raw: str):
    """科目・章番号(あれば)・章トピック名を返す。第N章表記の有無に関わらず同じ章に正規化する。"""
    subject = "商会" if pid.startswith("C") else "工原"
    s = re.sub(r"^(工業|商業|原計|工原|商会)\s*", "", subject_raw)
    s = re.sub(r"#\d+(\s*/\s*#?\d+)?\s*", "", s)
    m = re.search(r"第(\d+)章", s)
    cno = int(m.group(1)) if m else None
    s = re.sub(r"第\d+章\s*", "", s)
    topic = s.rstrip(CIRCLED + " 　").strip()
    return subject, cno, topic


def chapter_ref(subject: str, cno, topic: str) -> str:
    """章ノートのファイル名／wikilink名（科目プレフィックスで衝突回避）"""
    label = f"第{cno}章 {topic}" if cno else topic
    return sanitize(f"{subject}・{label}")


def subject_ref(subject: str) -> str:
    return f"科目・{subject}"


def is_date(s: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", s))


def build_note(r) -> str:
    subject, kind, chapter_no, chapter = classify(r["id"], r["subject_raw"])
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
    lines.append("> このノートは `tools/generate_vault_views.py` が演習ログ（exercise-log.md）から生成した派生物。**手で編集しない**（次回生成で消える）。記録の更新は演習ログ側で行う。")
    lines.append("")
    if r["memo"] and r["memo"] != "-":
        lines.append("## 履歴メモ（演習ログより）")
        lines.append("")
        lines.append(r["memo"])
        lines.append("")
    # 章への上リンク（樹形図の枝）
    lines.append(f"所属: [[{r['_chapter_ref']}|{r['_chapter_label']}]]")
    # 型カードへの横断リンク
    if subject == "工原" and chapter_no in CARD_BY_CHAPTER:
        lines.append(f"関連: [[{CARD_BY_CHAPTER[chapter_no]}]]")
    lines.append("")
    return "\n".join(lines)


def build_chapter_note(subject, cno, topic, members) -> str:
    label = f"第{cno}章 {topic}" if cno else topic
    counts = defaultdict(int)
    for m in members:
        counts[m["grade"]] += 1
    summary = " ・ ".join(f"{GRADE_ICON.get(g, g)}{g}{counts[g]}" for g in ("○", "△", "✕") if counts[g])
    lines = ["---", "tags:", "  - 章", f'subject: "{subject}"']
    if cno:
        lines.append(f"chapter_no: {cno}")
    lines.append(f"problems: {len(members)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {subject}・{label}")
    lines.append("")
    lines.append(f"科目: [[{subject_ref(subject)}]]")
    lines.append("")
    lines.append(f"> [!info] 自動生成（{len(members)}問）")
    lines.append(f"> {summary or '—'}")
    lines.append("")
    lines.append("## この章の問題")
    lines.append("")
    for m in sorted(members, key=lambda x: x["id"]):
        icon = GRADE_ICON.get(m["grade"], m["grade"])
        lines.append(f"- {icon} [[{m['_basename']}|{m['id']} {m['subtitle']}]]")
    lines.append("")
    return "\n".join(lines)


def build_subject_note(subject, chapters) -> str:
    total = sum(len(m) for _, _, _, m in chapters)
    lines = ["---", "tags:", "  - 科目", "---", ""]
    full = "工業簿記＋原価計算" if subject == "工原" else "商業簿記＋会計学"
    lines.append(f"# 科目・{subject}（{full}）")
    lines.append("")
    lines.append("入口: [[ホーム]]")
    lines.append("")
    lines.append(f"> [!info] {len(chapters)}章 ・ {total}問")
    lines.append("")
    lines.append("## 章一覧")
    lines.append("")
    for subj, cno, topic, members in sorted(chapters, key=lambda c: (c[1] or 999, c[2])):
        ref = chapter_ref(subj, cno, topic)
        label = f"第{cno}章 {topic}" if cno else topic
        lines.append(f"- [[{ref}|{label}]] … {len(members)}問")
    lines.append("")
    return "\n".join(lines)


def main():
    text = LOG.read_text(encoding="utf-8")
    rows = list(parse_rows(text))
    if not rows:
        sys.exit("no rows parsed — abort")

    # 1) 問題ノートのファイル名を先に確定（衝突回避）＋章グループを付与
    names = set()
    groups = defaultdict(list)          # (subject, topic) -> [rows]
    group_cno = {}                      # (subject, topic) -> 代表章番号
    for r in rows:
        base = sanitize(f'{r["id"]} {r["subtitle"]}')[:80]
        if base in names:
            base = f'{base} ({len(names)})'
        names.add(base)
        r["_basename"] = base
        subject, cno, topic = chapter_group(r["id"], r["subject_raw"])
        key = (subject, topic)
        groups[key].append(r)
        if cno and (key not in group_cno or cno < group_cno[key]):
            group_cno[key] = cno

    # 各問題に「所属章」の参照名を付与（グループの代表章番号を使う）
    for (subject, topic), members in groups.items():
        cno = group_cno.get((subject, topic))
        ref = chapter_ref(subject, cno, topic)
        label = f"第{cno}章 {topic}" if cno else topic
        for r in members:
            r["_chapter_ref"] = ref
            r["_chapter_label"] = label

    # 2) 出力フォルダを作り直す
    for d in (OUT, OUT_STRUCT):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    # 3) 問題ノート
    for r in rows:
        (OUT / f"{r['_basename']}.md").write_text(build_note(r), encoding="utf-8")

    # 4) 章ノート
    for (subject, topic), members in groups.items():
        cno = group_cno.get((subject, topic))
        ref = chapter_ref(subject, cno, topic)
        (OUT_STRUCT / f"{ref}.md").write_text(
            build_chapter_note(subject, cno, topic, members), encoding="utf-8")

    # 5) 科目ノート
    by_subject = defaultdict(list)
    for (subject, topic), members in groups.items():
        by_subject[subject].append((subject, group_cno.get((subject, topic)), topic, members))
    for subject, chapters in by_subject.items():
        (OUT_STRUCT / f"{subject_ref(subject)}.md").write_text(
            build_subject_note(subject, chapters), encoding="utf-8")

    # 検証サマリー
    grades = defaultdict(int)
    for r in rows:
        grades[r["grade"]] += 1
    print(f"generated {len(rows)} problem-notes -> {OUT.name}/")
    print(f"generated {len(groups)} chapter-notes + {len(by_subject)} subject-notes -> {OUT_STRUCT.name}/")
    print("grade counts:", dict(sorted(grades.items())))


if __name__ == "__main__":
    main()
