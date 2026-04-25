"""
서버 관리 모듈
로컬 free-claude-code 서버 시작/중지 기능
"""
import os
import subprocess
import time
import requests
from pathlib import Path
from loguru import logger


class ServerManager:
    """로컬 AI 서버 관리"""

    def __init__(self):
        self.server_process = None
        self.server_url = os.getenv("FREE_CLAUDE_CODE_URL", "http://localhost:8083")
        self.use_local_server = os.getenv("USE_LOCAL_SERVER", "true").lower() == "true"

    def is_server_running(self) -> bool:
        """서버가 실행 중인지 확인"""
        try:
            headers = {}
            if self.use_local_server:
                auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN", "freecc")
                if auth_token:
                    headers["x-api-key"] = auth_token

            response = requests.get(f"{self.server_url}/v1/models", headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    def start_server(self) -> bool:
        """로컬 서버 시작"""
        if not self.use_local_server:
            logger.info("로컬 서버 사용하지 않음 (USE_LOCAL_SERVER=false)")
            return True

        if self.is_server_running():
            logger.info(f"서버 이미 실행 중: {self.server_url}")
            return True

        try:
            logger.info("로컬 AI 서버 시작 중...")

            # free-claude-code 서버 시작
            # uvicorn server:app --host 0.0.0.0 --port 8082
            cmd = [
                "python", "-m", "uvicorn",
                "server:app",
                "--host", "0.0.0.0",
                "--port", "8082"
            ]

            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=Path(__file__).parent.parent.parent.parent / "free-claude-code"
            )

            # 서버 시작 대기
            max_wait = 30  # 최대 30초 대기
            for i in range(max_wait):
                time.sleep(1)
                if self.is_server_running():
                    logger.success(f"✅ 서버 시작 완료: {self.server_url}")
                    return True
                if i % 5 == 0:  # 5초마다 메시지
                    logger.info(f"서버 시작 대기 중... ({i}/{max_wait}초)")

            logger.error("❌ 서버 시작 실패 (시간 초과)")
            return False

        except Exception as e:
            logger.error(f"❌ 서버 시작 오류: {e}")
            return False

    def stop_server(self):
        """서버 중지"""
        if self.server_process:
            logger.info("서버 중지 중...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            logger.success("✅ 서버 중지 완료")
            self.server_process = None

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.stop_server()


# 전역 서버 관리자 인스턴스
_server_manager = None


def get_server_manager() -> ServerManager:
    """서버 관리자 인스턴스 가져오기"""
    global _server_manager
    if _server_manager is None:
        _server_manager = ServerManager()
    return _server_manager


def ensure_server_running() -> bool:
    """서버가 실행 중인지 확인하고 필요하면 시작"""
    manager = get_server_manager()
    return manager.start_server()
