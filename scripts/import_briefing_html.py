#!/usr/bin/env python3
"""브리핑 아티팩트 HTML 한 판을 저장소에 등록한다.

원본 HTML을 data/editions/ 로 옮기고, data/briefings.json 에 메타 정보를 추가한다.
본문은 손대지 않으므로 사이트에서도 원래 판형 그대로 보인다.

사용법:
    python3 scripts/import_briefing_html.py <원본.html> 2026-09-23 [--edition 제5판]
"""
import argparse
from datetime import date
from html import unescape
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


TAGS = re.compile(r"<[^>]+>")


def strip(value):
    return unescape(TAGS.sub("", value)).strip()


def meta_from_html(html, day, edition=None):
    body = html[html.find("<body"):]
    mast = re.search(r'class="mast-meta"(.*?)</div>', body, re.S)
    spans = [strip(x) for x in re.findall(r"<span[^>]*>(.*?)</span>", mast.group(1), re.S)] if mast else []

    lede = re.search(r'class="lede"(.*?)</div>', body, re.S)
    items = re.findall(r"<li>(.*?)</li>", lede.group(1), re.S) if lede else []
    heads = [strip(re.search(r"<b>(.*?)</b>", item, re.S).group(1)).rstrip(".")
             for item in items if re.search(r"<b>(.*?)</b>", item, re.S)]
    summary = " ".join(strip(item) for item in items[:2])[:400]

    counts = {}
    for chunk in body.split("<section")[1:]:
        title = re.search(r'class="sec-head".*?<h2>(.*?)</h2>', chunk, re.S)
        if title:
            counts[strip(title.group(1))] = chunk.count('class="item"')

    corrections, correction_count = [], 0
    colophon = re.search(r'class="colophon"(.*?)</div>\s*</div>', body, re.S)
    if colophon:
        rows = re.split(r"<b>", colophon.group(1))
        for row in rows:
            if row.startswith("정정"):
                label = re.match(r"정정\s*(\d+)건", row)
                correction_count = int(label.group(1)) if label else 0
                text = strip(row.split("</b>", 1)[-1]).lstrip("—- ").rstrip(".")
                corrections = [text] if text else []

    sources = re.search(r'class="src-grid"(.*?)</div>', body, re.S)
    source_count = len(re.findall(r"<a ", sources.group(1))) if sources else 0

    return {
        "date": day,
        "edition": edition or next((value for value in spans if re.fullmatch(r"제\d+판", value)), None),
        "status": "edition",
        "file": f"{day}.html",
        "period": next((value for value in spans if "기준" in value), None),
        "summary": summary,
        "headlines": heads[:5],
        "counts": {name: count for name, count in counts.items() if count},
        "corrections": corrections,
        "correction_count": correction_count,
        "unverified_count": len(re.findall(r"미확인", strip(body))),
        "source_count": source_count,
        "figures": [],
        "market_date": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("html", type=Path, help="브리핑 원본 HTML 경로")
    parser.add_argument("date", help="판 날짜 (YYYY-MM-DD)")
    parser.add_argument("--edition", help="판 표기 (예: 제5판)")
    args = parser.parse_args()
    day = date.fromisoformat(args.date).isoformat()

    html = args.html.read_text(encoding="utf-8")
    (DATA / "editions").mkdir(parents=True, exist_ok=True)
    target = DATA / "editions" / f"{day}.html"
    shutil.copyfile(args.html, target)

    path = DATA / "briefings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = meta_from_html(html, day, args.edition)
    previous = next((item for item in data["briefings"] if item["date"] == day), None)
    if previous:
        for key in ("figures", "market_date"):
            entry[key] = previous.get(key, entry[key])
    data["briefings"] = [item for item in data["briefings"] if item["date"] != day] + [entry]
    data["briefings"].sort(key=lambda item: item["date"], reverse=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = ", ".join(f"{name} {count}건" for name, count in entry["counts"].items()) or "구성 미확인"
    print(f"{day} 등록: {entry['edition'] or '판 표기 없음'} · {counts} · 출처 {entry['source_count']}건 · 미확인 {entry['unverified_count']}건")
    print(f"원본 보관: {target.relative_to(ROOT)}")
    print("다음: data/threads.json 의 사안에 오늘 기록을 추가하고 python3 scripts/build.py 로 확인한다")


if __name__ == "__main__":
    main()
