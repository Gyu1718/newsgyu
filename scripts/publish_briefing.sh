#!/usr/bin/env bash
# 오늘 판 HTML 한 장을 저장소에 등록하고 푸시한다.
#   ./scripts/publish_briefing.sh <브리핑.html> [YYYY-MM-DD] [판 표기]
set -euo pipefail

cd "$(dirname "$0")/.."

HTML=${1:?브리핑 HTML 경로가 필요하다}
DAY=${2:-$(TZ=Asia/Seoul date +%F)}
EDITION=${3:-}

git pull --rebase --quiet

if [[ -n "$EDITION" ]]; then
  python3 scripts/import_briefing_html.py "$HTML" "$DAY" --edition "$EDITION"
else
  python3 scripts/import_briefing_html.py "$HTML" "$DAY"
fi

echo "→ data/threads.json 에 오늘 기록을 더했는지 확인한다"

python3 scripts/build.py
python3 scripts/site_extras.py
python3 scripts/check_site.py
git checkout -- docs

git add data
if git diff --cached --quiet; then
  echo "바뀐 데이터가 없다. 커밋을 건너뛴다."
  exit 0
fi

git commit -m "Add briefing $DAY"
git push
echo "완료: $(git rev-parse --short HEAD) · https://gyu1718.github.io/newsgyu/briefings/$DAY.html"
