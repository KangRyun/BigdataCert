"""문제 JSON 파일을 읽어서 메모리에 캐시.

content/problems/{exam_type}/*.json 을 모두 로드한다. 부팅 시 한 번.
sample_data, truth_data 의 상대경로는 content_dir 기준으로 해석되어 절대경로로 저장된다.
truth_data 는 학습자에게 노출되지 않고 채점기만 접근 가능.
"""

import json
import logging
from collections.abc import Iterable
from pathlib import Path

from app.config import settings
from app.schemas.problem import ProblemFull

logger = logging.getLogger(__name__)


class ContentRepository:
    def __init__(self, content_dir: Path):
        self.content_dir = content_dir
        self._by_id: dict[str, ProblemFull] = {}
        self._sample_paths: dict[str, dict[str, Path]] = {}
        self._truth_paths: dict[str, dict[str, Path]] = {}

    def load(self) -> int:
        problems_dir = self.content_dir / "problems"
        if not problems_dir.exists():
            logger.warning("content directory not found: %s", problems_dir)
            return 0

        count = 0
        for json_path in problems_dir.rglob("*.json"):
            try:
                raw = json.loads(json_path.read_text(encoding="utf-8"))
                problem = ProblemFull.model_validate(raw)
                self._by_id[problem.problem_id] = problem
                self._sample_paths[problem.problem_id] = self._resolve_rel(
                    problem.problem_id, problem.sample_data, "sample_data"
                )
                self._truth_paths[problem.problem_id] = self._resolve_rel(
                    problem.problem_id, problem.truth_data, "truth_data"
                )
                count += 1
            except Exception as exc:
                logger.error("failed to load %s: %s", json_path, exc)
        logger.info("loaded %d problems from %s", count, problems_dir)
        return count

    def _resolve_rel(
        self, problem_id: str, mapping: dict[str, str], kind: str
    ) -> dict[str, Path]:
        paths: dict[str, Path] = {}
        for filename, rel in mapping.items():
            resolved = (self.content_dir / rel).resolve()
            if not resolved.exists():
                logger.warning(
                    "missing %s for %s: %s", kind, problem_id, resolved
                )
                continue
            paths[filename] = resolved
        return paths

    def get(self, problem_id: str) -> ProblemFull | None:
        return self._by_id.get(problem_id)

    def sample_data_paths(self, problem_id: str) -> dict[str, Path]:
        return self._sample_paths.get(problem_id, {})

    def truth_data_paths(self, problem_id: str) -> dict[str, Path]:
        return self._truth_paths.get(problem_id, {})

    def all(self) -> Iterable[ProblemFull]:
        return self._by_id.values()


repository = ContentRepository(settings.content_dir)
