"""사용자 제출 코드의 정적 위험 패턴 검사.

regex 기반. 문자열·주석 안의 패턴도 매칭되는 false positive 한계가 있으나,
MVP로는 충분하고 실패 시 사용자에게 명확한 안내 메시지를 제공한다.

향후 강화: AST 기반으로 전환하여 노드 종류별 검사.
"""

import re

_PATTERNS: list[tuple[str, str]] = [
    (r"\bimport\s+os\b", "import os"),
    (r"\bfrom\s+os\b", "from os ..."),
    (r"\bimport\s+subprocess\b", "import subprocess"),
    (r"\bimport\s+socket\b", "import socket"),
    (r"\bimport\s+urllib\b", "import urllib"),
    (r"\bimport\s+requests\b", "import requests"),
    (r"\bimport\s+shutil\b", "import shutil"),
    (r"\b__import__\s*\(", "__import__()"),
    (r"\beval\s*\(", "eval()"),
    (r"\bexec\s*\(", "exec()"),
    (r"\bcompile\s*\(", "compile()"),
    (r"\bopen\s*\(", "open()"),
    (r"\bglobals\s*\(", "globals()"),
    (r"\blocals\s*\(", "locals()"),
]


class StaticCheckError(Exception):
    """금지 패턴이 발견되었을 때 발생."""

    def __init__(self, violations: list[str]):
        super().__init__(f"forbidden patterns: {', '.join(violations)}")
        self.violations = violations


def check_user_code(code: str) -> None:
    """위반이 있으면 StaticCheckError, 없으면 None을 반환."""
    violations: list[str] = []
    for pattern, label in _PATTERNS:
        if re.search(pattern, code):
            violations.append(label)
    if violations:
        raise StaticCheckError(violations)
