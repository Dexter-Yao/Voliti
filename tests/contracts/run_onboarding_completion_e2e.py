# ABOUTME: 运行 onboarding completion 的最小 API 集成验证
# ABOUTME: 启动本地 LangGraph dev server，并执行依赖真实 Store API 的 iOS 集成测试

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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
XCODEPROJ = PROJECT_ROOT / "frontend-ios" / "Voliti.xcodeproj"
DEFAULT_SIMULATOR_ID = "B998C101-9B78-4EE3-BE2C-A4EAEAB5EF20"
TEST_USER_ID = "e2e_device_onboarding"


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
    env = os.environ.copy()
    env.setdefault("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    env.setdefault("AZURE_OPENAI_API_KEY", "test-key")
    env.setdefault("AZURE_OPENAI_API_VERSION", "2024-02-01")
    env.setdefault("DASHSCOPE_API_KEY", "test-key")

    process = subprocess.Popen(
        ["uv", "run", "langgraph", "dev", "--port", str(port)],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process


def stop_backend_server(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def run_xcode_test(port: int) -> None:
    env = os.environ.copy()
    env["LANGGRAPH_API_URL"] = f"http://127.0.0.1:{port}"
    env["VOLITI_USER_ID"] = TEST_USER_ID
    env["VOLITI_E2E_BACKEND"] = "1"

    command = [
        "xcodebuild",
        "test",
        "-project",
        str(XCODEPROJ),
        "-scheme",
        "Voliti",
        "-sdk",
        "iphonesimulator",
        "-destination",
        f"id={env.get('VOLITI_SIMULATOR_ID', DEFAULT_SIMULATOR_ID)}",
        "-only-testing:VolitiTests/BackendIntegrationTests",
    ]

    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )


def main() -> None:
    port = find_free_port()
    server = start_backend_server(port)

    try:
        wait_for_server(port)
        run_xcode_test(port)
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
