"""문제 도메인 모델.

content-author ↔ backend-engineer 사이의 단일 진실 원천.
.claude/skills/bigdata-content-creation/SKILL.md의 JSON 스키마와 일치해야 함.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

ExamType = Literal["practical_1", "practical_2", "practical_3", "written"]
Difficulty = Literal["easy", "medium", "hard"]
OutputFormat = Literal["scalar", "csv", "dict", "choice"]


class ExpectedOutput(BaseModel):
    format: OutputFormat
    schema_: str | dict[str, Any] | None = Field(default=None, alias="schema")
    tolerance: float = 0.0
    metric: str | None = None
    baseline: float | None = None
    answer: int | float | str | dict[str, Any] | list[Any] | None = None

    model_config = {"populate_by_name": True}


class ProblemSummary(BaseModel):
    """목록 조회용 슬림 모델 (정답·해설·정답코드 제외)."""

    problem_id: str
    exam_type: ExamType
    title: str
    difficulty: Difficulty
    topic_tags: list[str]


class ProblemDetail(ProblemSummary):
    """상세 조회 — 문제 본문·힌트·샘플 데이터까지. 정답코드·해설은 제출 후에만 노출.

    Note: solution_code, explanation은 학습자가 제출한 후 별도 엔드포인트에서 조회.
    """

    description: str
    sample_data: dict[str, str] = {}
    expected_output: ExpectedOutput
    hints: list[str] = []


class ProblemFull(ProblemDetail):
    """관리자/내부용 전체 모델 — 정답코드·해설 포함."""

    solution_code: str
    explanation: str
    choices: list[str] | None = None
