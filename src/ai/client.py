"""
AI API 클라이언트
로컬 free-claude-code 서버를 사용하여 블로그 글 생성
"""
import os
import requests
import json
from dotenv import load_dotenv
from loguru import logger

# 환경변수 로드
load_dotenv()


class AIClientError(RuntimeError):
    """AI 클라이언트 예외의 기본 클래스"""


class AICreditBalanceError(AIClientError):
    """Anthropic 크레딧 부족 예외"""


class AIGenerationError(AIClientError):
    """일반적인 AI 생성 실패 예외"""


class AIClient:
    """로컬 free-claude-code 서버 AI 클라이언트"""

    def __init__(self, model: str = None):
        """
        Args:
            model: 사용할 모델명. None이면 기본값 사용
        """
        self.use_local_server = os.getenv("USE_LOCAL_SERVER", "true").lower() == "true"

        if self.use_local_server:
            self.base_url = os.getenv("FREE_CLAUDE_CODE_URL", "http://localhost:8083")
            self.auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN", "freecc")
        else:
            # 외부 API 사용 (Anthropic 등)
            self.base_url = os.getenv("EXTERNAL_AI_URL", "https://api.anthropic.com")
            self.auth_token = os.getenv("EXTERNAL_AI_KEY", "")

        self.model = model or os.getenv("DEFAULT_AI_MODEL", "claude-sonnet-4-20250514")

        if self.use_local_server:
            logger.info(f"AI 클라이언트 초기화 완료 (로컬 서버: {self.base_url}, 모델: {self.model})")
        else:
            logger.info(f"AI 클라이언트 초기화 완료 (외부 API: {self.base_url}, 모델: {self.model})")

    def _parse_sse_response(self, response):
        """SSE 응답을 파싱하여 텍스트 추출"""
        content = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data = line[6:]  # "data: " 제거
                    if data == "[DONE]":
                        continue
                    try:
                        event_data = json.loads(data)
                        if event_data.get("type") == "content_block_delta":
                            delta = event_data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                content += delta.get("text", "")
                    except json.JSONDecodeError:
                        continue
        return content

    def _get_headers(self):
        """요청 헤더 생성"""
        headers = {
            "Content-Type": "application/json",
        }

        if self.use_local_server:
            headers["x-api-key"] = self.auth_token
        else:
            headers["x-api-key"] = self.auth_token
            headers["anthropic-version"] = "2023-06-01"

        return headers

    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> str:
        """텍스트 생성

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (AI 역할 정의)
            max_tokens: 최대 토큰 수
            temperature: 창의성 정도 (0~1)

        Returns:
            생성된 텍스트
        """
        try:
            # 서버 URL 결정
            if self.use_local_server:
                url = f"{self.base_url}/v1/messages"
            else:
                url = f"{self.base_url}/v1/messages"

            headers = self._get_headers()

            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt or "당신은 블로그 글을 작성하는 전문 작가입니다.",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            response = requests.post(url, json=payload, headers=headers, timeout=120, stream=True)
            response.raise_for_status()

            # SSE 응답 파싱
            result_text = self._parse_sse_response(response)

            logger.success(f"✅ 텍스트 생성 완료 ({len(result_text)}자)")
            return result_text

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ AI 생성 실패 (서버 연결 오류): {e}")
            raise AIGenerationError(f"서버 연결 실패: {e}")
        except Exception as e:
            logger.error(f"❌ AI 생성 실패: {e}")
            raise AIGenerationError(f"AI 생성에 실패했습니다: {e}")

    def generate_with_history(
        self,
        messages: list,
        system_prompt: str = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> str:
        """대화 히스토리를 포함한 텍스트 생성

        Args:
            messages: 대화 히스토리 [{"role": "user/assistant", "content": "..."}]
            system_prompt: 시스템 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 창의성 정도

        Returns:
            생성된 텍스트
        """
        try:
            # 서버 URL 결정
            if self.use_local_server:
                url = f"{self.base_url}/v1/messages"
            else:
                url = f"{self.base_url}/v1/messages"

            headers = self._get_headers()

            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt or "당신은 블로그 글을 작성하는 전문 작가입니다.",
                "messages": messages
            }

            response = requests.post(url, json=payload, headers=headers, timeout=120, stream=True)
            response.raise_for_status()

            # SSE 응답 파싱
            result_text = self._parse_sse_response(response)

            logger.success(f"✅ 텍스트 생성 완료 ({len(result_text)}자)")
            return result_text

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ AI 생성 실패 (서버 연결 오류): {e}")
            raise AIGenerationError(f"서버 연결 실패: {e}")
        except Exception as e:
            logger.error(f"❌ AI 생성 실패: {e}")
            raise AIGenerationError(f"AI 생성에 실패했습니다: {e}")
