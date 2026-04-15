from __future__ import annotations

import asyncio
import json
import os
import threading
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

PLATFORM_URL = os.getenv("TEST_PROCESSOR_PLATFORM_URL", "http://localhost:8000")
PROCESSOR_NAME = os.getenv("TEST_PROCESSOR_NAME", "test-adder")
TASK_TYPE = os.getenv("TEST_PROCESSOR_TASK_TYPE", "test")
DESCRIPTION = os.getenv("TEST_PROCESSOR_DESCRIPTION", "按行做两个数相加的测试处理器")
ENDPOINT_URL = os.getenv("TEST_PROCESSOR_ENDPOINT_URL", "http://localhost:9000")
HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("TEST_PROCESSOR_HEARTBEAT_INTERVAL", "30"))
REQUEST_TIMEOUT_SECONDS = 10
RESULT_FILE_NAME = "result.txt"
UPLOADS_DIR_NAME = "uploads"
DELIVERY_DIR_NAME = "delivery"

@asynccontextmanager
async def lifespan(_: FastAPI):
    _register_to_platform()
    heartbeat_task = asyncio.create_task(_heartbeat_loop())
    try:
        yield
    finally:
        heartbeat_task.cancel()
        with suppress(asyncio.CancelledError):
            await heartbeat_task


app = FastAPI(title="Test Adder Processor", lifespan=lifespan)


@dataclass
class ProcessorRuntimeState:
    processor_id: int | None = None
    api_token: str | None = None


STATE = ProcessorRuntimeState()


class InputFile(BaseModel):
    asset_id: int
    file_name: str
    file_path: str


class ExecuteRequest(BaseModel):
    task_id: int
    task_type: str
    callback_base_url: str
    input_files: list[InputFile]
    config: dict[str, str] = Field(default_factory=dict)
    output_dir: str


def parse_addition_line(line: str, *, line_number: int) -> tuple[Decimal, Decimal]:
    parts = line.strip().split()
    if len(parts) != 2:
        raise ValueError(f"第 {line_number} 行格式错误，必须是两个数字并以空格分隔")
    return _parse_decimal(parts[0], line_number=line_number), _parse_decimal(
        parts[1],
        line_number=line_number,
    )


def calculate_sum_lines(lines: list[str]) -> list[str]:
    sums: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        left, right = parse_addition_line(line, line_number=line_number)
        sums.append(str(left + right))
    return sums


def write_addition_output(*, input_files: list[Path], output_file: Path) -> int:
    all_lines = _read_input_lines(input_files)
    if not all_lines:
        raise ValueError("输入文件为空，无法执行加法测试")
    sum_lines = calculate_sum_lines(all_lines)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(sum_lines), encoding="utf-8")
    return len(sum_lines)


@app.post("/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute(
    request: ExecuteRequest,
    authorization: str = Header(...),
) -> dict[str, str]:
    _ensure_dispatch_token(authorization)
    thread = threading.Thread(
        target=_process_task,
        args=(request,),
        daemon=True,
    )
    thread.start()
    return {"status": "accepted"}


def _parse_decimal(value: str, *, line_number: int) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"第 {line_number} 行包含非数字内容: {value}") from exc


def _read_input_lines(input_files: list[Path]) -> list[str]:
    all_lines: list[str] = []
    for input_file in input_files:
        if not input_file.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        all_lines.extend(input_file.read_text(encoding="utf-8").splitlines())
    return all_lines


def _ensure_dispatch_token(authorization: str) -> None:
    if STATE.api_token is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="处理器尚未注册完成",
        )
    expected_token = f"Bearer {STATE.api_token}"
    if authorization != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的处理器调用令牌",
        )


def _register_to_platform() -> None:
    payload = {
        "name": PROCESSOR_NAME,
        "task_type": TASK_TYPE,
        "description": DESCRIPTION,
        "endpoint_url": ENDPOINT_URL,
    }
    data = _post_json(
        url=f"{PLATFORM_URL}/api/processors/register",
        payload=payload,
    )
    processor_id = data.get("processor_id")
    api_token = data.get("api_token")
    if not isinstance(processor_id, int) or not isinstance(api_token, str):
        raise RuntimeError(f"注册响应无效: {data}")
    STATE.processor_id = processor_id
    STATE.api_token = api_token
    print(f"注册成功: processor_id={STATE.processor_id}, task_type={TASK_TYPE}")


async def _heartbeat_loop() -> None:
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
        try:
            _send_heartbeat()
        except Exception as exc:  # noqa: BLE001
            print(f"心跳失败: {exc}")


def _send_heartbeat() -> None:
    if STATE.processor_id is None or STATE.api_token is None:
        raise RuntimeError("处理器尚未初始化")
    _post_json(
        url=f"{PLATFORM_URL}/api/processors/heartbeat",
        payload={"processor_id": STATE.processor_id},
        token=STATE.api_token,
    )


def _process_task(request: ExecuteRequest) -> None:
    try:
        if STATE.api_token is None:
            raise RuntimeError("处理器令牌不存在，无法回调平台")
        _report_progress(request=request, progress=20, message="开始读取输入文件")
        output_file = Path(request.output_dir) / RESULT_FILE_NAME
        input_paths = [Path(item.file_path) for item in request.input_files]
        line_count = write_addition_output(input_files=input_paths, output_file=output_file)
        _report_progress(request=request, progress=80, message=f"加法计算完成，共 {line_count} 行")
        _report_complete(request=request, output_file=output_file, line_count=line_count)
    except Exception as exc:  # noqa: BLE001
        _report_fail(request=request, error=type(exc).__name__, message=str(exc))


def _report_progress(*, request: ExecuteRequest, progress: int, message: str) -> None:
    _post_json(
        url=_build_callback_url(request.callback_base_url, f"/api/tasks/{request.task_id}/progress"),
        payload={"progress": progress, "message": message},
        token=STATE.api_token,
    )


def _report_complete(*, request: ExecuteRequest, output_file: Path, line_count: int) -> None:
    relative_file_path = _to_upload_relative_path(output_file)
    _post_json(
        url=_build_callback_url(request.callback_base_url, f"/api/tasks/{request.task_id}/complete"),
        payload={
            "output_files": [
                {
                    "file_path": relative_file_path,
                    "file_name": output_file.name,
                    "sample_count": line_count,
                }
            ],
            "message": f"test 加法处理完成，共 {line_count} 行",
        },
        token=STATE.api_token,
    )


def _report_fail(*, request: ExecuteRequest, error: str, message: str) -> None:
    _post_json(
        url=_build_callback_url(request.callback_base_url, f"/api/tasks/{request.task_id}/fail"),
        payload={"error": error, "message": message},
        token=STATE.api_token,
    )


def _build_callback_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _to_upload_relative_path(output_file: Path) -> str:
    resolved_parts = output_file.resolve().parts
    if UPLOADS_DIR_NAME not in resolved_parts:
        raise ValueError(f"输出文件不在 uploads 目录下: {output_file}")
    upload_index = resolved_parts.index(UPLOADS_DIR_NAME)
    relative_parts = resolved_parts[upload_index:]
    upload_relative_path = PurePosixPath(*relative_parts)
    expected_prefix = PurePosixPath(UPLOADS_DIR_NAME, DELIVERY_DIR_NAME)
    if not upload_relative_path.is_relative_to(expected_prefix):
        raise ValueError(f"输出文件必须位于 uploads/delivery 下: {output_file}")
    return str(upload_relative_path)


def _post_json(
    *,
    url: str,
    payload: dict[str, object],
    token: str | None = None,
) -> dict[str, object]:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {}
            return json.loads(body)
    except HTTPError as exc:
        raise RuntimeError(f"请求失败 {exc.code}: {_safe_read_error_body(exc)}") from exc
    except URLError as exc:
        raise RuntimeError(f"请求失败: {exc.reason}") from exc


def _safe_read_error_body(exc: HTTPError) -> str:
    try:
        return exc.read().decode("utf-8")
    except Exception:  # noqa: BLE001
        return ""
