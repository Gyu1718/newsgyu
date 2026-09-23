# 오전 8시 브리핑

매일 아침 받는 브리핑을 날짜별로 보관하고, 여러 날에 걸친 사건을 사안별 계보로 묶는 정적 사이트입니다.

- 사이트: https://gyu1718.github.io/newsgyu/
- 최신 판 고정 주소: https://gyu1718.github.io/newsgyu/latest.html
- 사건 계보: https://gyu1718.github.io/newsgyu/threads/index.html
- RSS: https://gyu1718.github.io/newsgyu/rss.xml
- Pages 설정: **Deploy from a branch → main → /docs**
- 실행 환경: Python 3.10 이상, 외부 패키지와 API 키 없이 동작합니다

## 세 층으로 나뉜다

| 층 | 파일 | 하는 일 |
| --- | --- | --- |
| 원본 | `data/editions/YYYY-MM-DD.html` | 그날 브리핑 HTML을 손대지 않고 그대로 보관합니다. 사이트에서도 원래 판형으로 열립니다. |
| 메타 | `data/briefings.json` | 날짜, 판, 요약, 요점, 섹션별 건수, 정정·미확인 건수, 출처 수를 담습니다. 아카이브 목차의 재료입니다. |
| 계보 | `data/threads.json` | 여러 날에 걸친 사건을 사안 단위로 묶습니다. 사안마다 날짜순 기록과 다음 확인 지점이 붙습니다. |

`docs/`는 생성 결과물입니다. 직접 수정하지 않습니다.

## 새 판 등록

```bash
python3 scripts/import_briefing_html.py <브리핑.html> 2026-09-23        # 원본 보관 + 메타 추출
python3 scripts/build.py && python3 scripts/check_site.py               # 생성 확인
git checkout -- docs                                                    # docs 변경분은 되돌린다
git add data && git commit -m "Add briefing 2026-09-23" && git push
```

푸시하면 `Publish briefing site`가 사이트를 다시 만들고 `docs/`를 자동 커밋합니다.

메타 추출기는 요점 목록, 섹션별 기사 수, 정정 문구, 출처 링크 수, 미확인 표기 횟수를 원본에서 읽습니다. 증시 섹션을 실은 판은 `figures`에 지수 등락률을, `market_date`에 직전 미국장 마감일을 직접 채웁니다. 확인하지 못한 값은 `null`로 둡니다.

본문 없이 요약만 남은 날짜는 `status`를 `summary`로 두고 `file`을 `null`로 둡니다.

## 사안 등록과 갱신

`data/threads.json`의 `threads` 배열에 사안을 만들고, 보도가 이어질 때마다 `entries`에 한 줄씩 더합니다.

```json
{
  "id": "cambodia-scam-crackdown",
  "title": "캄보디아 온라인 스캠 단속과 제재 압박",
  "section": "캄보디아",
  "field": "치안·사회",
  "status": "진행 중",
  "summary": "사안 한 줄 설명",
  "watch": "다음에 확인할 지점",
  "entries": [
    {
      "date": "2026-09-22",
      "headline": "그날 판의 기사 제목",
      "note": "이 사안에서 달라진 점",
      "source": "매체명"
    }
  ]
}
```

- `id`는 영문 소문자와 하이픈만 씁니다. 사안 페이지 주소가 됩니다.
- `status`는 `진행 중` / `소강` / `종결` 중 하나입니다.
- `entries`의 날짜가 보관된 판과 같으면 그날 판 링크가 자동으로 붙습니다. 보관 전 사건은 링크 없이 기록만 남습니다.
- 기존 기록은 고치지 않습니다. 사실이 바뀌면 새 기록을 추가하고 `note`에 무엇이 달라졌는지 적습니다.

## 검사

```bash
python3 scripts/build.py --check      # 생성 결과와 커밋된 docs 비교
python3 scripts/site_extras.py --check
python3 scripts/check_site.py         # 내부 링크·자산·앵커 확인
```

`Validate site`가 PR과 `main` 변경에서 같은 검사를 돌립니다. 날짜 중복, 사안 id 중복, 빠진 원본 파일, 잘못된 상태 값은 생성 단계에서 걸러집니다.

## 오프라인 보기

저장소를 클론하거나 ZIP으로 내려받으면 `docs/`의 페이지가 인터넷 없이 열립니다. 원문 기사 링크만 연결이 필요합니다.
