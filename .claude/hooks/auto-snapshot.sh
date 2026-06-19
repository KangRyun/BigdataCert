#!/usr/bin/env bash
# Claude Code Stop 훅 — 작업이 끝날 때마다 변경사항을 자동 커밋.
#
# 동작:
#   - /home/kr9370/빅분기 가 git repo가 아니면 no-op
#   - 변경(staged or untracked)이 없으면 no-op
#   - 있으면 git add -A 후 "chore(auto): snapshot at <timestamp>" 커밋
#
# 제외:
#   - _workspace/, .venv/, node_modules/ 등은 .gitignore 로 자동 제외됨
#   - 자동 push 없음 (네트워크·실수 방지 — 사용자가 수동 push)
#
# 출력:
#   - 커밋 발생 시 systemMessage 로 SHA를 사용자에게 알림

set +e

REPO_DIR="/home/kr9370/빅분기"

cd "$REPO_DIR" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# 변경 없으면 no-op
if [ -z "$(git status --porcelain)" ]; then
  exit 0
fi

git add -A 2>/dev/null

MSG="chore(auto): snapshot at $(date '+%Y-%m-%d %H:%M:%S')"
if git -c commit.gpgsign=false commit -m "$MSG" >/dev/null 2>&1; then
  SHA=$(git rev-parse --short HEAD 2>/dev/null)
  # systemMessage 는 UI에 표시됨
  printf '{"systemMessage": "auto-snapshot %s"}\n' "$SHA"
fi

exit 0
