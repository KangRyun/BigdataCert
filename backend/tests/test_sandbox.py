"""샌드박스·정적검사 단위 테스트."""

import pytest

from app.sandbox import StaticCheckError, check_user_code, run_in_sandbox


class TestStaticCheck:
    def test_allows_pandas_code(self) -> None:
        check_user_code("import pandas as pd\ndf = pd.DataFrame()\nprint(len(df))")

    def test_blocks_import_os(self) -> None:
        with pytest.raises(StaticCheckError) as exc:
            check_user_code("import os\nprint(os.getcwd())")
        assert "import os" in exc.value.violations

    def test_blocks_eval(self) -> None:
        with pytest.raises(StaticCheckError):
            check_user_code("x = eval('1+1')\nprint(x)")

    def test_blocks_subprocess(self) -> None:
        with pytest.raises(StaticCheckError):
            check_user_code("import subprocess\nsubprocess.run(['ls'])")

    def test_blocks_open(self) -> None:
        with pytest.raises(StaticCheckError):
            check_user_code("with open('x') as f: pass")


class TestRunner:
    def test_simple_print(self) -> None:
        result = run_in_sandbox("print(42)")
        assert result.error_code is None
        assert result.stdout.strip() == "42"

    def test_forbidden_pattern_short_circuits(self) -> None:
        result = run_in_sandbox("import os\nprint(os.environ)")
        assert result.error_code == "FORBIDDEN_PATTERN"
        # subprocess는 호출되지 않아야 함
        assert result.stdout == ""

    def test_runtime_error_captured(self) -> None:
        result = run_in_sandbox("1/0")
        assert result.error_code == "RUNTIME_ERROR"
        assert "ZeroDivisionError" in result.stderr

    def test_timeout(self) -> None:
        # 1초 타임아웃으로 짧게
        result = run_in_sandbox("while True: pass", timeout=1)
        assert result.error_code == "TIMEOUT"

    def test_pandas_reads_sample_data(self, tmp_path) -> None:
        csv = tmp_path / "data.csv"
        csv.write_text("a,b\n1,2\n3,4\n")
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df['b'].sum())"
        result = run_in_sandbox(code, sample_data_paths={"data.csv": csv})
        assert result.error_code is None, result.stderr
        assert result.stdout.strip() == "6"
