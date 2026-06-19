"""subprocess 기반 1차 샌드박스 러너.

격리 방어:
- 임시 디렉토리(tempfile.TemporaryDirectory)에서 실행 → 외부 파일 접근 차단
- subprocess.run timeout → 무한루프/장시간 실행 차단
- 환경변수 최소화 → 시크릿 노출 차단
- 정적 검사로 위험 import/eval 차단 (static_check.py)

배포 단계에서 Docker --network none --read-only로 2차 격리 추가 예정.

Artifact 캡처:
- 학습자 코드가 작업형 2 등에서 pred.csv 같은 결과 파일을 생성하면
  tempdir 가 삭제되기 전에 텍스트로 읽어 SandboxResult.artifacts 에 담아 반환
- 입력으로 들어간 sample_data 파일과 user.py 는 제외
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pydantic import BaseModel

from app.sandbox.static_check import StaticCheckError, check_user_code


class SandboxResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    artifacts: dict[str, str] = {}  # filename -> 텍스트 내용 (UTF-8)
    error_code: str | None = None


_MAX_OUTPUT_BYTES = 4000
_MAX_ARTIFACT_BYTES = 5_000_000
_SAFE_ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8"}


def _truncate(s: str, limit: int = _MAX_OUTPUT_BYTES) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n... (출력 {len(s) - limit} 바이트 절단)"


def _collect_artifacts(tmp_path: Path, exclude: set[str]) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    for child in tmp_path.iterdir():
        if child.name in exclude or not child.is_file():
            continue
        try:
            size = child.stat().st_size
        except OSError:
            continue
        if size > _MAX_ARTIFACT_BYTES:
            continue
        try:
            artifacts[child.name] = child.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # 바이너리 등은 건너뜀
            continue
    return artifacts


def run_in_sandbox(
    code: str,
    sample_data_paths: dict[str, Path] | None = None,
    timeout: int = 30,
) -> SandboxResult:
    """사용자 코드를 격리 실행. 정적 위반 → FORBIDDEN_PATTERN, 타임아웃 → TIMEOUT,
    종료 코드 != 0 → RUNTIME_ERROR.
    """
    try:
        check_user_code(code)
    except StaticCheckError as exc:
        return SandboxResult(error_code="FORBIDDEN_PATTERN", stderr=str(exc))

    sample_data_paths = sample_data_paths or {}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for filename, source in sample_data_paths.items():
            shutil.copy(source, tmp_path / filename)
        script = tmp_path / "user.py"
        script.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=_SAFE_ENV,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                error_code="TIMEOUT",
                stderr=f"실행 시간 초과 (>{timeout}s)",
            )

        # artifact 캡처는 성공/실패 모두에서 시도 (실패 분석에 도움)
        exclude = set(sample_data_paths.keys()) | {"user.py"}
        artifacts = _collect_artifacts(tmp_path, exclude)

        if result.returncode != 0:
            return SandboxResult(
                error_code="RUNTIME_ERROR",
                stdout=_truncate(result.stdout),
                stderr=_truncate(result.stderr),
                artifacts=artifacts,
            )

        return SandboxResult(
            stdout=_truncate(result.stdout),
            stderr=_truncate(result.stderr),
            artifacts=artifacts,
        )
