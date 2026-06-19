"""문제 도메인 모델.

content-author ↔ backend-engineer 사이의 단일 진실 원천.
.claude/skills/bigdata-content-creation/SKILL.md의 JSON 스키마와 일치해야 함.

보안 분리:
- ExpectedOutputPublic: 공개 응답 (학습자가 보는 모델). format/schema/tolerance/metric만.
- ExpectedOutput: 내부 (학습자에게 노출 금지). baseline, answer 포함.
- ProblemDetail (공개) ⊂ ProblemFull (내부) — Full에만 정답·해설·truth_data·choices가 있음.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ExamType = Literal["practical_1", "practical_2", "practical_3", "written"]
Difficulty = Literal["easy", "medium", "hard"]
OutputFormat = Literal["scalar", "csv", "dict", "choice"]


class ExpectedOutputPublic(BaseModel):
    """공개 응답용. 정답 단서가 들어가는 필드는 모두 제외."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    format: OutputFormat
    schema_: str | dict[str, Any] | None = Field(default=None, alias="schema")
    tolerance: float = 0.0
    metric: str | None = None


class ExpectedOutput(ExpectedOutputPublic):
    """내부용. answer, baseline 등 채점 비밀을 포함."""

    baseline: float | None = None
    answer: int | float | str | dict[str, Any] | list[Any] | None = None


class ProblemSummary(BaseModel):
    """목록 조회용 슬림 모델."""

    problem_id: str
    exam_type: ExamType
    title: str
    difficulty: Difficulty
    topic_tags: list[str]


class ProblemDetail(ProblemSummary):
    """상세 조회 (학습자 노출 안전). 정답·해설·정답코드·truth_data·answer/baseline 없음."""

    description: str
    sample_data: dict[str, str] = {}
    expected_output: ExpectedOutputPublic
    hints: list[str] = []
    choices: list[str] | None = None  # 객관식은 선지를 노출 — 답이 아니므로 안전


class ProblemFull(ProblemDetail):
    """관리자/내부용 — 정답, 해설, truth_data 모두 포함."""

    expected_output: ExpectedOutput  # type: ignore[assignment]
    truth_data: dict[str, str] = {}  # 채점용 정답 파일 경로. content_dir 기준 상대.
    solution_code: str
    explanation: str
