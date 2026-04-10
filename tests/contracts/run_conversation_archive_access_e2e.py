# ABOUTME: 运行 Conversation Archive Access Layer 的最小 live integration 验证
# ABOUTME: 启动本地 LangGraph dev server，发送一轮真实对话，再通过 archive access layer 读取稳定 conversation record

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
BACKEND_SRC = BACKEND_DIR / "src"

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from voliti.runtime_session_history_langgraph import create_conversation_archive_access_layer


load_dotenv(BACKEND_DIR / ".env")


def _require_env(name: str) -> None:
    value = os.environ.get(name)
    if isinstance(value, str) and value.strip():
        return
    raise RuntimeError(f"缺少必需环境变量: {name}")


def require_model_env() -> None:
    _require_env("AZURE_OPENAI_ENDPOINT")
    _require_env("AZURE_OPENAI_API_KEY")
    _require_env("AZURE_OPENAI_API_VERSION")


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(port: int, timeout_seconds: float = 30.0) -> None:
    deadline = time.time() + timeout_seconds
    url = f"http://127.0.0.1:{port}/docs"

    while time.time() < deadline:
        try:
            with urlopen(url) as response:
                if 200 <= response.status < 500:
                    return
        except URLError:
            time.sleep(0.25)

    raise RuntimeError(f"LangGraph dev server 未在 {timeout_seconds:.0f} 秒内就绪: {url}")


def start_backend_server(port: int) -> subprocess.Popen[str]:
    return subprocess.Popen(
        ["uv", "run", "langgraph", "dev", "--port", str(port)],
        cwd=BACKEND_DIR,
        env=os.environ.copy(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )


def stop_backend_server(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def run_assertions(port: int) -> None:
    import asyncio
    from langgraph_sdk import get_client

    async def _run() -> None:
        user_id = f"archive_e2e_{uuid4().hex[:8]}"
        correlation_id = f"corr_{uuid4().hex[:8]}"
        client = get_client(url=f"http://127.0.0.1:{port}")

        thread = await client.threads.create(
            metadata={
                "user_id": user_id,
                "session_mode": "coaching",
                "correlation_id": correlation_id,
            }
        )
        thread_ref = thread["thread_id"]

        await client.runs.wait(
            thread_ref,
            "coach",
            input={"messages": [{"role": "human", "content": "[2026-04-10T03:00:00Z] 请简单回应一句，方便我验证归档读取。"}]},
            config={
                "configurable": {
                    "user_id": user_id,
                    "correlation_id": correlation_id,
                    "session_mode": "coaching",
                }
            },
            raise_error=True,
        )

        layer = create_conversation_archive_access_layer(server_url=f"http://127.0.0.1:{port}")
        record = await layer.read_conversation_record(thread_ref)
        refs = await layer.list_conversation_refs(user_id=user_id, limit=5)

        assert record.conversation_ref == thread_ref
        assert record.runtime_thread_ref == thread_ref
        assert record.user_id == user_id
        assert record.session_type == "coaching"
        assert record.correlation_id == correlation_id
        assert len(record.messages) >= 2
        assert record.messages[0].role == "user"
        assert record.messages[-1].role == "assistant"
        assert thread_ref in refs

    asyncio.run(_run())


def main() -> None:
    require_model_env()
    port = find_free_port()
    server = start_backend_server(port)

    try:
        wait_for_server(port)
        run_assertions(port)
    finally:
        stop_backend_server(server)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        sys.exit(1)
