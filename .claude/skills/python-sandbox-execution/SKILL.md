---
name: python-sandbox-execution
description: "사용자가 제출한 Python 코드를 안전하게 격리 실행하는 패턴. subprocess 기반 1차 격리 → Docker 격리 → 채점기 연동까지. backend-engineer가 빅분기 코드 실행·채점 엔드포인트를 구현할 때 반드시 이 스킬을 사용. '샌드박스', '코드 실행', '채점', '격리', '타임아웃', 'Python 격리' 같은 요청에도 트리거."
---

# Python 코드 샌드박스 실행 가이드

빅분기 학습 사이트에서 학습자가 제출한 Python 코드를 서버에서 실행하고 결과를 채점하는 엔진의 설계 표준. 보안과 채점 정합성을 동시에 보장한다.

## 핵심 원칙

1. **다층 방어** — 단일 격리 메커니즘 신뢰 금지. 정적 분석 + 프로세스 격리 + 컨테이너 격리를 직렬 적용
2. **결정적 채점** — 동일 코드는 항상 동일 결과. 시간·환경 변수 의존 금지
3. **빠른 거부** — 위험 코드는 실행 전에 거부. 실행 시작 후 발견은 비용 큼
4. **에러는 구조화** — 사용자가 무엇이 잘못됐는지 알 수 있도록 (`SYNTAX_ERROR`, `TIMEOUT`, `MEMORY`, `FORBIDDEN_IMPORT`, `RUNTIME_ERROR` 등)

## 실행 파이프라인

```
[제출된 user_code]
    ↓
[1. 정적 분석] - AST 파싱, 금지 패턴 검출
    ↓ (통과)
[2. 임시 작업공간 생성] - tempfile.TemporaryDirectory, sample_data 복사
    ↓
[3. 격리 실행] - subprocess.run(timeout, rlimit) 또는 docker run --network none
    ↓
[4. 결과 캡처] - stdout, stderr, 생성된 파일
    ↓
[5. 채점기 호출] - expected_output 스키마에 따라 grade()
    ↓
[6. 결과 반환] - {score, passed, feedback, error_code?}
```

## 1차 격리: subprocess + rlimit (로컬 개발 우선)

```python
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

ALLOWED_IMPORTS = {
    "pandas", "numpy", "sklearn", "scipy", "statsmodels",
    "matplotlib", "math", "json", "csv", "os.path",
}

FORBIDDEN_PATTERNS = [
    "import os",                     # os 자체 import (os.path는 별도 허용 필요)
    "import subprocess",
    "import socket",
    "import urllib", "import requests",
    "open(",                          # 임시 디렉토리 외 파일 접근 위험
    "__import__",
    "eval(", "exec(",
    "compile(",
    "globals(", "locals(",
]

def static_check(code: str) -> list[str]:
    """반환: 위반 사유 목록. 빈 리스트면 통과."""
    violations = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in code:
            violations.append(f"forbidden pattern: {pattern}")
    return violations

def run_in_sandbox(code: str, data_dir: Path, timeout: int = 30) -> SandboxResult:
    violations = static_check(code)
    if violations:
        return SandboxResult(error_code="FORBIDDEN_PATTERN", detail=violations)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(data_dir, tmp_path / "data", dirs_exist_ok=True)
        script = tmp_path / "user.py"
        script.write_text(code)

        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"},
                # POSIX 한정: resource.setrlimit를 preexec_fn으로
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(error_code="TIMEOUT", detail=f">{timeout}s")

        if result.returncode != 0:
            return SandboxResult(
                error_code="RUNTIME_ERROR",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        return SandboxResult(
            stdout=result.stdout,
            artifacts=collect_artifacts(tmp_path),
        )
```

## 2차 격리: Docker (배포 단계)

배포 시에는 subprocess만으로 불충분. 별도 컨테이너로 격리한다:

```bash
docker run --rm \
  --network none \
  --read-only \
  --tmpfs /tmp:rw,size=128m \
  --memory 512m --memory-swap 512m \
  --cpus 1.0 \
  --user 1000:1000 \
  -v /path/to/data:/data:ro \
  -v /path/to/user.py:/work/user.py:ro \
  --workdir /work \
  python-sandbox:latest \
  python user.py
```

> Dockerfile은 `python:3.11-slim`에 pandas/sklearn/scipy/statsmodels만 사전 설치, non-root user, network none 가정으로 빌드.

## 채점기 인터페이스

채점기는 `grade(expected_output_spec, sandbox_result) -> GradingResult` 형태로 단일 진입점을 갖는다:

```python
from typing import Protocol

class GradingResult(BaseModel):
    passed: bool
    score: float                # 0.0 ~ 1.0 또는 metric 값
    metric_name: str            # roc_auc, rmse, exact 등
    feedback: str               # 사용자용 한국어 메시지
    error_code: str | None = None

class Grader(Protocol):
    def grade(self, spec: ExpectedOutput, result: SandboxResult) -> GradingResult: ...
```

format 별 그레이더는 `references/graders.md` 참조.

## 보안 체크리스트

- [ ] 정적 분석으로 위험 패턴 차단 (forbidden imports, eval/exec, 임의 파일 접근)
- [ ] 실행 타임아웃 (작업형 1·3: 10s, 작업형 2: 60s)
- [ ] 메모리 제한 (512MB)
- [ ] 네트워크 차단 (Docker --network none)
- [ ] 작업공간은 tempdir, 실행 후 즉시 삭제
- [ ] non-root user 실행
- [ ] 출력 크기 제한 (stdout 1MB, artifact 10MB)
- [ ] 시크릿·환경변수 차단 (`env`에 PATH·PYTHONDONTWRITEBYTECODE만)

## 채점 정합성 보장

content-author의 모든 `solution_code`가 본인의 채점기를 만점으로 통과해야 한다. QA 회귀 스크립트:

```python
# tests/integration/test_grading_regression.py
@pytest.mark.parametrize("problem", load_all_problems())
def test_solution_passes_grader(problem):
    result = run_in_sandbox(problem.solution_code, data_dir=problem.data_dir)
    graded = grade(problem.expected_output, result)
    assert graded.passed, f"{problem.problem_id} 의 정답코드가 채점기를 통과하지 못함"
```

이 테스트가 CI에서 통과되지 않으면 어떤 문제도 배포 금지.

## 자주 발생하는 채점 실패 패턴

| 패턴 | 원인 | 해결 |
|------|------|------|
| SHAPE_MISMATCH (csv) | 사용자 컬럼명이 schema와 다름 | 채점기에서 사전 검증 + 한국어 피드백 |
| TOLERANCE_FAIL | random_state 미고정 | content-author가 solution_code에 random_state 강제 |
| TIMEOUT | 비효율적 알고리즘 | 사용자에게 시간 제한 안내 + 데이터 크기 명시 |
| FORBIDDEN_IMPORT | open() 또는 os.system() 사용 시도 | 사용자에게 허용 라이브러리 목록 안내 |

## 디렉토리 구조

```
backend/app/sandbox/
├── __init__.py
├── runner.py          # run_in_sandbox 구현
├── static_check.py    # 정적 분석
├── docker_runner.py   # 2차 격리 (배포 단계)
└── tests/

backend/app/grading/
├── __init__.py
├── base.py            # Grader 프로토콜, GradingResult
├── scalar.py
├── csv_grader.py      # roc_auc, rmse, accuracy
├── dict_grader.py
└── choice.py
```
