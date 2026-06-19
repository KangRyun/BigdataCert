"""Python 코드 격리 실행 모듈.

.claude/skills/python-sandbox-execution/SKILL.md 의 사양을 따른다.
1차 격리: subprocess + timeout. 2차 격리(Docker)는 배포 단계에서 추가.
"""

from app.sandbox.runner import SandboxResult, run_in_sandbox
from app.sandbox.static_check import StaticCheckError, check_user_code

__all__ = ["SandboxResult", "StaticCheckError", "check_user_code", "run_in_sandbox"]
