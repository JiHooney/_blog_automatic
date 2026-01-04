"""
AI API 클라이언트
Claude API를 사용하여 블로그 글 생성
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv
from loguru import logger

# 환경변수 로드
load_dotenv()


class AIClient:
    """Claude AI 클라이언트"""
    
    def __init__(self, model: str = None):
        """
        Args:
            model: 사용할 모델명. None이면 환경변수에서 로드
        """
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        
        self.model = model or os.getenv("DEFAULT_AI_MODEL", "claude-sonnet-4-20250514")
        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"AI 클라이언트 초기화 완료 (모델: {self.model})")
    
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
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "당신은 블로그 글을 작성하는 전문 작가입니다.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = message.content[0].text
            logger.success(f"✅ 텍스트 생성 완료 ({len(result)}자)")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI 생성 실패: {e}")
            raise
    
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
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "당신은 블로그 글을 작성하는 전문 작가입니다.",
                messages=messages
            )
            
            result = message.content[0].text
            logger.success(f"✅ 텍스트 생성 완료 ({len(result)}자)")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI 생성 실패: {e}")
            raise
