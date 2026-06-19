"""OpenAPI 스키마를 JSON으로 stdout에 출력.

프론트의 openapi-typescript가 입력으로 사용.
사용: python -m app.openapi_dump > ../_workspace/openapi.json
"""

import json
import sys

from app.main import app


def main() -> None:
    json.dump(app.openapi(), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
