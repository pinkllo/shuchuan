from decimal import Decimal
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

import pytest

from app.test_processor_service import (
    calculate_sum_lines,
    parse_addition_line,
    write_addition_output,
)


def test_parse_addition_line_returns_two_numbers() -> None:
    left, right = parse_addition_line("12 30", line_number=1)
    assert left == Decimal("12")
    assert right == Decimal("30")


def test_parse_addition_line_rejects_invalid_column_count() -> None:
    with pytest.raises(ValueError, match="第 2 行"):
        parse_addition_line("7 8 9", line_number=2)


def test_calculate_sum_lines_returns_line_sums() -> None:
    result = calculate_sum_lines(["1 2", "3.5 4.5"])
    assert result == ["3", "8.0"]


def test_write_addition_output_reads_input_file_and_writes_result() -> None:
    temp_root = Path(".test_tmp")
    temp_root.mkdir(exist_ok=True)
    test_dir = temp_root / f"adder-{uuid4().hex}"
    test_dir.mkdir()
    try:
        input_file = test_dir / "input.txt"
        input_file.write_text("1 2\n10 25\n", encoding="utf-8")
        output_file = test_dir / "result.txt"

        count = write_addition_output(input_files=[input_file], output_file=output_file)

        assert count == 2
        assert output_file.read_text(encoding="utf-8") == "3\n35"
    finally:
        rmtree(test_dir, ignore_errors=True)
