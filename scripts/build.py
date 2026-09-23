#!/usr/bin/env python3
"""표준 라이브러리만으로 docs/ 사이트를 생성한다.

세 가지를 만든다.
1. 날짜별 브리핑 페이지 — data/editions/ 의 원본 HTML을 그대로 쓰고 이동 막대만 덧붙인다.
2. 아카이브 목차 — data/briefings.json 의 메타 정보로 만든다.
3. 사건 계보 — data/threads.json 의 사안별 타임라인으로 만든다.
"""
import argparse
from datetime import date
from html import escape
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
SITE_PATH = "/newsgyu/"
WEEKDAYS = "월화수목금토일"
STATUSES = {"진행 중", "소강", "종결"}


def t(value):
    return escape(str(value), quote=True)


def weekday(value):
    return WEEKDAYS[date.fromisoformat(value).weekday()]


def load_briefings():
    data = json.loads((DATA / "briefings.json").read_text(encoding="utf-8"))
    if data.get("version") != 2 or not isinstance(data.get("briefings"), list):
        raise ValueError("data/briefings.json 은 version 2 와 briefings 배열이 필요하다")
    seen = set()
    for item in data["briefings"]:
        value = item.get("date")
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError("date 는 YYYY-MM-DD 형식이어야 한다")
        if value in seen:
            raise ValueError(f"날짜가 중복된다: {value}")
        seen.add(value)
        if item.get("status") not in {"edition", "summary"}:
            raise ValueError("status 는 edition 또는 summary 여야 한다")
        if not isinstance(item.get("summary"), str) or not item["summary"].strip():
            raise ValueError(f"{value}: summary 가 필요하다")
        if item["status"] == "edition":
            source = DATA / "editions" / (item.get("file") or "")
            if not item.get("file") or not source.is_file():
                raise ValueError(f"{value}: data/editions/{item.get('file')} 파일이 없다")
        for figure in item.get("figures", []):
            change = figure.get("change_pct")
            if change is not None and (type(change) not in (int, float) or not math.isfinite(change)):
                raise ValueError("change_pct 는 유한한 수 또는 null 이어야 한다")
    data["briefings"].sort(key=lambda item: item["date"], reverse=True)
    return data


def load_threads(dates):
    data = json.loads((DATA / "threads.json").read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("threads"), list):
        raise ValueError("data/threads.json 은 version 1 과 threads 배열이 필요하다")
    seen = set()
    for thread in data["threads"]:
        ident = thread.get("id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", ident):
            raise ValueError(f"사안 id 는 영문 소문자 슬러그여야 한다: {ident}")
        if ident in seen:
            raise ValueError(f"사안 id 가 중복된다: {ident}")
        seen.add(ident)
        if thread.get("status") not in STATUSES:
            raise ValueError(f"{ident}: status 는 {' / '.join(sorted(STATUSES))} 중 하나여야 한다")
        for key in ("title", "summary"):
            if not isinstance(thread.get(key), str) or not thread[key].strip():
                raise ValueError(f"{ident}: {key} 가 필요하다")
        entries = thread.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"{ident}: entries 가 최소 한 건 필요하다")
        for entry in entries:
            value = entry.get("date")
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                raise ValueError(f"{ident}: entries 의 date 는 YYYY-MM-DD 형식이어야 한다")
            if not isinstance(entry.get("headline"), str) or not entry["headline"].strip():
                raise ValueError(f"{ident}: entries 에 headline 이 필요하다")
            entry["archived"] = value in dates
        entries.sort(key=lambda entry: entry["date"], reverse=True)
        thread["last"] = entries[0]["date"]
        thread["first"] = entries[-1]["date"]
    data["threads"].sort(key=lambda thread: (thread["status"] != "진행 중", thread["last"]), reverse=False)
    data["threads"].sort(key=lambda thread: thread["last"], reverse=True)
    return data


def page(title, body, prefix="", script=False):
    tag = f'<script src="{prefix}assets/archive.js" defer></script>' if script else ""
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="description" content="오전 8시 브리핑을 날짜별로 보관하고 사건별 계보로 정리하는 아카이브입니다.">
  <meta name="color-scheme" content="light dark">
  <title>{t(title)} · 오전 8시 브리핑</title>
  <link rel="stylesheet" href="{prefix}assets/site.css">
  {tag}
</head>
<body>
  <a class="skip" href="#main">본문으로 이동</a>
  <div class="wrap">
{body}
    <footer class="foot">확인되지 않은 값은 추정하지 않고 확인 상태로 남깁니다. 기관마다 값이 갈리는 항목은 출처와 함께 구분합니다.</footer>
  </div>
</body>
</html>
'''


def nav(active, prefix=""):
    links = [("아카이브", f"{prefix}index.html", "archive"), ("사건 계보", f"{prefix}threads/index.html", "threads")]
    items = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if key == active else ""}>{label}</a>'
        for label, href, key in links
    )
    return f'<nav class="site-nav" aria-label="사이트 구역">{items}</nav>'


def figures_html(item):
    parts = []
    for figure in item.get("figures", []):
        change = figure.get("change_pct")
        css = "up" if change is not None and change > 0 else "down" if change is not None and change < 0 else ""
        display = "미확인" if change is None else f"{change:+.2f}%"
        parts.append(f'<span>{t(figure["label"])} <b class="{css}">{display}</b></span>')
    return '<p class="figs">' + "".join(parts) + "</p>" if parts else ""


def badges(item):
    parts = [f'<span class="tag">{t(name)} {count}건</span>' for name, count in item.get("counts", {}).items()]
    corrections = item.get("correction_count") or len(item.get("corrections", []))
    if corrections:
        parts.append(f'<span class="tag warn">정정 {corrections}건</span>')
    if item.get("unverified_count"):
        parts.append(f'<span class="tag">미확인 {item["unverified_count"]}건</span>')
    return '<p class="tags">' + "".join(parts) + "</p>" if parts else ""


def archive_page(items, threads):
    months = sorted({item["date"][:7] for item in items}, reverse=True)
    options = "".join(f'<option value="{m}">{m[:4]}년 {int(m[5:])}월</option>' for m in months)
    cards = []
    for item in items:
        heads = "".join(f"<li>{t(h)}</li>" for h in item.get("headlines", []))
        label = "브리핑 읽기" if item["status"] == "edition" else "요약만 보기"
        edition = f' · {t(item["edition"])}' if item.get("edition") else ""
        cards.append(f'''      <li class="card" data-month="{item['date'][:7]}" data-search="{t(item['date'] + ' ' + item['summary'] + ' ' + ' '.join(item.get('headlines', [])))}">
        <a href="briefings/{item['date']}.html">
          <p class="d"><b><time datetime="{item['date']}">{item['date']}</time> {weekday(item['date'])}</b><span>{t(item.get('period') or '')}{edition}</span></p>
          <p class="sum">{t(item['summary'])}</p>
          {f'<ul class="heads">{heads}</ul>' if heads else ''}
          {figures_html(item)}
          {badges(item)}
          <span class="go">{label} →</span>
        </a>
      </li>''')
    live = [thread for thread in threads if thread["status"] == "진행 중"][:6]
    chips = "".join(f'<a href="threads/{thread["id"]}.html">{t(thread["title"])} <b>{len(thread["entries"])}건</b></a>' for thread in live)
    body = f'''    <header class="mast">
      <p class="eyebrow">NEWS FOR GYU</p>
      <h1>오전 8시 브리핑</h1>
      <p class="mast-meta">보관 {len(items)}판 · 최신 {items[0]['date'] if items else '준비 중'} · 사안 {len(threads)}건</p>
    </header>
    {nav("archive")}
    <main id="main" tabindex="-1">
      <section class="live">
        <h2>진행 중인 사안</h2>
        <div class="chips">{chips}</div>
        <p class="more"><a href="threads/index.html">사건 계보 전체 보기 →</a></p>
      </section>
      <h2 class="sec">날짜별 브리핑</h2>
      <form class="filters" id="filters" role="search" hidden>
        <div class="field"><label for="query">검색</label>
          <input id="query" type="search" placeholder="날짜나 키워드 (예: 2026-09, 캄보디아)" autocomplete="off"></div>
        <div class="field"><label for="month">발행 월</label>
          <select id="month"><option value="">전체 기간</option>{options}</select></div>
        <button id="reset" type="button">초기화</button>
      </form>
      <p class="count" id="count" role="status" aria-live="polite">{len(items)}판 · 최신순</p>
      <ul class="cards" id="cards">{''.join(cards)}</ul>
      <p class="empty" id="empty" hidden>조건에 맞는 판이 없습니다.</p>
    </main>'''
    return page("아카이브", body, script=True)


def threads_index(threads):
    cards = []
    for thread in threads:
        span = thread["first"] if thread["first"] == thread["last"] else f'{thread["first"]} ~ {thread["last"]}'
        cards.append(f'''      <li class="card" data-search="{t(thread['title'] + ' ' + thread['summary'] + ' ' + thread.get('section', '') + ' ' + thread.get('field', ''))}">
        <a href="{thread['id']}.html">
          <p class="d"><b>{t(thread['title'])}</b><span>{t(thread.get('section') or '')}{' · ' + t(thread['field']) if thread.get('field') else ''}</span></p>
          <p class="sum">{t(thread['summary'])}</p>
          <p class="tags"><span class="tag {'warn' if thread['status'] == '진행 중' else ''}">{t(thread['status'])}</span><span class="tag">기록 {len(thread['entries'])}건</span><span class="tag">{t(span)}</span></p>
          <span class="go">계보 보기 →</span>
        </a>
      </li>''')
    body = f'''    <header class="mast">
      <p class="eyebrow">THREADS</p>
      <h1>사건 계보</h1>
      <p class="mast-meta">사안 {len(threads)}건 · 여러 날에 걸친 보도를 하나로 묶습니다</p>
    </header>
    {nav("threads", prefix="../")}
    <main id="main" tabindex="-1">
      <form class="filters" id="filters" role="search" hidden>
        <div class="field"><label for="query">검색</label>
          <input id="query" type="search" placeholder="사안명이나 지역 (예: 캄보디아, 유럽)" autocomplete="off"></div>
        <button id="reset" type="button">초기화</button>
      </form>
      <p class="count" id="count" role="status" aria-live="polite">{len(threads)}건 · 최근 기록순</p>
      <ul class="cards" id="cards">{''.join(cards)}</ul>
      <p class="empty" id="empty" hidden>조건에 맞는 사안이 없습니다.</p>
    </main>'''
    return page("사건 계보", body, prefix="../", script=True)


def thread_page(thread):
    rows = []
    for entry in thread["entries"]:
        link = f'<a href="../briefings/{entry["date"]}.html">그날 판 보기 →</a>' if entry["archived"] else '<span class="muted">보관된 판 없음</span>'
        source = f'<span class="src">{t(entry["source"])}</span>' if entry.get("source") else ""
        note = f'<p class="note">{t(entry["note"])}</p>' if entry.get("note") else ""
        rows.append(f'''        <li class="row">
          <p class="when"><time datetime="{entry['date']}">{entry['date']}</time> {weekday(entry['date'])}</p>
          <div class="what"><h3>{t(entry['headline'])}</h3>{note}<p class="meta">{source}{link}</p></div>
        </li>''')
    watch = f'<section class="watch"><h2>다음 확인 지점</h2><p>{t(thread["watch"])}</p></section>' if thread.get("watch") else ""
    span = thread["first"] if thread["first"] == thread["last"] else f'{thread["first"]} ~ {thread["last"]}'
    body = f'''    <a class="back" href="index.html">← 사건 계보</a>
    <header class="mast">
      <p class="eyebrow">{t(thread.get('section') or '')}{' · ' + t(thread['field']) if thread.get('field') else ''}</p>
      <h1>{t(thread['title'])}</h1>
      <p class="mast-meta">{t(thread['status'])} · 기록 {len(thread['entries'])}건 · {t(span)}</p>
    </header>
    <main id="main" tabindex="-1">
      <p class="intro">{t(thread['summary'])}</p>
      {watch}
      <h2 class="sec">기록</h2>
      <ol class="timeline">{''.join(rows)}</ol>
      <p class="more"><a href="../index.html">날짜별 아카이브 →</a></p>
    </main>'''
    return page(thread["title"], body, prefix="../")


def summary_page(item, older, newer):
    body = f'''    <a class="back" href="../index.html">← 아카이브</a>
    <header class="mast">
      <p class="eyebrow">오전 8시 브리핑</p>
      <h1>{item['date']} {weekday(item['date'])}</h1>
      <p class="mast-meta">{t(item.get('period') or '')}</p>
    </header>
    <main id="main" tabindex="-1">
      <aside class="notice"><b>본문 미등록</b><p>이 날짜는 요약만 보관하고 있습니다. 원본 브리핑 파일이 없어 수치의 출처는 확인되지 않았습니다.</p></aside>
      <p class="intro">{t(item['summary'])}</p>
      {figures_html(item)}
      {badges(item)}
      {move_nav(older, newer, plain=True)}
    </main>'''
    return page(item["date"], body, prefix="../")


def move_nav(older, newer, plain=False):
    parts = []
    if newer:
        parts.append(f'<a href="{newer["date"]}.html">← {newer["date"]}</a>')
    parts.append('<a href="../index.html">아카이브</a>')
    parts.append('<a href="../threads/index.html">사건 계보</a>')
    if older:
        parts.append(f'<a href="{older["date"]}.html">{older["date"]} →</a>')
    return f'<nav class="move" aria-label="판 이동">{"".join(parts)}</nav>'


BAR_STYLE = """<style id="archive-bar-style">
.archive-bar{position:sticky;top:0;z-index:99;display:flex;gap:6px 14px;flex-wrap:wrap;align-items:baseline;
padding:calc(8px + env(safe-area-inset-top,0px)) 16px 8px;background:#14130F;color:#F3EFE6;
font:13px/1.5 -apple-system,"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif}
.archive-bar b{font-weight:600}
.archive-bar a{color:#F3EFE6;text-decoration:none;border-bottom:1px solid rgba(243,239,230,.45);padding-bottom:1px}
.archive-bar a:hover,.archive-bar a:focus-visible{color:#F0A9A2;border-color:#F0A9A2}
.archive-bar .sp{flex:1}
@media print{.archive-bar{display:none}}
</style>"""


def edition_page(item, older, newer):
    html = (DATA / "editions" / item["file"]).read_text(encoding="utf-8")
    links = [f'<a href="../index.html">아카이브</a>', f'<a href="../threads/index.html">사건 계보</a>']
    if newer:
        links.append(f'<a href="{newer["date"]}.html">← {newer["date"]}</a>')
    if older:
        links.append(f'<a href="{older["date"]}.html">{older["date"]} →</a>')
    bar = (f'{BAR_STYLE}<div class="archive-bar"><b>{t(item["date"])} {weekday(item["date"])}'
           f'{" · " + t(item["edition"]) if item.get("edition") else ""}</b><span class="sp"></span>'
           + "".join(links) + "</div>")
    match = re.search(r"<body[^>]*>", html, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"{item['file']}: <body> 태그를 찾지 못했다")
    return html[: match.end()] + "\n" + bar + html[match.end():]


def outputs(data, threads):
    items = data["briefings"]
    files = {
        DOCS / "index.html": archive_page(items, threads),
        DOCS / "threads/index.html": threads_index(threads),
        DOCS / ".nojekyll": "",
        DOCS / "data/briefings.json": json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        DOCS / "data/threads.json": json.dumps({"version": 1, "threads": threads}, ensure_ascii=False, indent=2) + "\n",
        DOCS / "404.html": page("페이지를 찾을 수 없습니다", f'''    <main id="main" tabindex="-1">
      <p class="eyebrow">404</p><h1>페이지를 찾을 수 없습니다</h1>
      <p class="intro">주소가 바뀌었거나 아직 등록되지 않은 판입니다.</p>
      <p class="more"><a href="{SITE_PATH}">아카이브로 돌아가기 →</a></p></main>''', prefix=SITE_PATH),
    }
    for asset in ("site.css", "archive.js"):
        files[DOCS / "assets" / asset] = (ROOT / "assets" / asset).read_text(encoding="utf-8")
    for index, item in enumerate(items):
        older = items[index + 1] if index + 1 < len(items) else None
        newer = items[index - 1] if index else None
        target = DOCS / "briefings" / f"{item['date']}.html"
        files[target] = edition_page(item, older, newer) if item["status"] == "edition" else summary_page(item, older, newer)
    for thread in threads:
        files[DOCS / "threads" / f"{thread['id']}.html"] = thread_page(thread)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="파일을 쓰지 않고 현재 docs 와 비교한다")
    args = parser.parse_args()
    data = load_briefings()
    threads = load_threads({item["date"] for item in data["briefings"]})["threads"]
    files = outputs(data, threads)
    differences = []
    for path, content in files.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                differences.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    stale = sorted(
        set((DOCS / "briefings").glob("*.html")) | set((DOCS / "threads").glob("*.html")) - set(files)
    )
    stale = [path for path in stale if path not in files]
    if stale:
        raise SystemExit("등록되지 않은 페이지가 남아 있다: " + ", ".join(str(p.relative_to(ROOT)) for p in stale))
    if differences:
        raise SystemExit("python3 scripts/build.py 를 실행하고 결과를 커밋한다: " + ", ".join(differences))
    print(f"{'검사' if args.check else '생성'} 완료: 사이트 파일 {len(files)}개 (판 {len(data['briefings'])}, 사안 {len(threads)})")


if __name__ == "__main__":
    main()
