# 작업 지침 (Claude)

이 저장소는 매일 아침 받는 「오전 8시 브리핑」을 날짜별로 보관하고, 사건을 사안별 계보로 묶는 정적 사이트다.

- 사이트: https://gyu1718.github.io/newsgyu/
- Pages 설정: Deploy from a branch → main → /docs
- Python 3.10 이상, 외부 패키지 없이 동작한다.

## 손대는 곳과 손대지 않는 곳

| 경로 | 성격 |
| --- | --- |
| `data/editions/YYYY-MM-DD.html` | 브리핑 원본. 내용을 고치지 않는다. |
| `data/briefings.json` | 판 메타(요약·요점·건수·정정·출처 수). 스크립트가 채운다. |
| `data/threads.json` | 사건 계보. 사안 분류와 기록 추가는 손으로 한다. |
| `docs/` | 생성 결과물. 직접 편집하지 않는다. |

## 새 판이 올라오면

```bash
python3 scripts/import_briefing_html.py <브리핑.html> YYYY-MM-DD
# data/threads.json 의 해당 사안에 오늘 기록을 추가한다
python3 scripts/build.py && python3 scripts/check_site.py
git checkout -- docs
git add data && git commit -m "Add briefing YYYY-MM-DD" && git push
```

푸시하면 `Publish briefing site` 워크플로가 `docs/`를 다시 만들어 커밋한다. 로컬에서 만든 `docs/` 변경분은 커밋하지 않는다.

증시 섹션이 실린 판은 `figures`에 지수 등락률, `market_date`에 직전 미국장 마감일을 직접 채운다. 확인하지 못한 값은 `null`로 둔다.

## 사건 계보 기록 규칙

- 같은 사건의 후속 보도는 해당 사안 `entries`에 새 기록으로 더한다. 기존 기록은 고치지 않는다.
- 정정과 미확인 해소도 기록으로 남기고 `note`에 무엇이 달라졌는지 적는다.
- 출처마다 수치가 갈리면 그 차이를 `note`에 함께 적는다. 확인되지 않은 값은 추정하지 않는다.
- `status`는 `진행 중` / `소강` / `종결` 중 하나다. 새 사안의 `id`는 영문 소문자와 하이픈만 쓴다.
- `watch`에는 다음에 확인할 지점을 한 줄로 적는다.

## 문체

- 부정 후 긍정 구조("~이 아니라 ~이다")와 "그러나 / 오히려 / 다만"을 쓰지 않는다.
- "깊은", "바라보다", "자리", "~를 넘어" 같은 상투어와 "현대 사회에서는", "결론적으로" 같은 연결어를 피한다.
- 훈계조("~해야 합니다")를 쓰지 않는다. 주술 상응과 조사를 정확히 쓴다.
- 같은 문형을 반복하지 않고 문장 길이에 변주를 준다.
