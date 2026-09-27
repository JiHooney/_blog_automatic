"""
플랫폼별 리라이터
원본 글을 각 플랫폼에 맞게 리라이팅 (중복 콘텐츠 방지)
"""
import re
from pathlib import Path
from datetime import datetime
from typing import Union, Tuple
import frontmatter
from loguru import logger

from .client import AIClient
from .prompt_builder import PromptBuilder


class PlatformRewriter:
    """플랫폼별 콘텐츠 리라이터"""
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    APPROVED_DIR = ROOT_DIR / "approved"
    PLATFORM_DIR = ROOT_DIR / "platform_versions"
    
    PLATFORMS = ["naver", "tistory", "wordpress"]
    
    def __init__(self):
        """리라이터 초기화"""
        self.ai_client = AIClient()
        self.prompt_builder = PromptBuilder()
        logger.info("플랫폼 리라이터 초기화 완료")
    
    def rewrite_content(
        self,
        content: str,
        platform: str,
        title: str = None,
        persona: str = PromptBuilder.DEFAULT_PERSONA,
    ) -> Tuple[str, str]:
        """콘텐츠 문자열을 직접 리라이팅
        
        Args:
            content: 원본 글 내용
            platform: 대상 플랫폼 (naver / tistory / wordpress)
            title: 원본 제목
        
        Returns:
            (새 제목, 리라이팅된 콘텐츠) 튜플
        """
        if platform not in self.PLATFORMS:
            raise ValueError(f"지원하지 않는 플랫폼: {platform}. 가능한 값: {self.PLATFORMS}")
        
        # 프롬프트 생성
        system_prompt = self.prompt_builder.build_platform_rewrite_prompt(platform, persona)
        user_prompt = self.prompt_builder.build_rewrite_prompt(
            content, platform, title, persona
        )
        
        logger.info(f"🔄 {platform.upper()}용 리라이팅 중: {title or '제목 없음'}")
        
        # AI 리라이팅
        rewritten_result = self.ai_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.8
        )
        
        # 제목과 본문 분리
        new_title, new_content = self._extract_title_and_content(rewritten_result, title)
        
        logger.success(f"✅ {platform.upper()} 리라이팅 완료 - 제목: {new_title}")
        return new_title, new_content
    
    def _extract_title_and_content(self, text: str, fallback_title: str = None) -> Tuple[str, str]:
        """AI 결과에서 제목과 본문 분리
        
        Args:
            text: AI 생성 결과
            fallback_title: 제목 추출 실패시 사용할 기본 제목
        
        Returns:
            (제목, 본문) 튜플
        """
        lines = text.strip().split('\n')
        
        # 첫 줄에서 제목 찾기 (# 제목 형식)
        new_title = fallback_title or "제목 없음"
        content_start = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('# '):
                new_title = stripped[2:].strip()
                content_start = i + 1
                break
        
        # 본문 추출 (제목 제외)
        content_lines = lines[content_start:]
        # 빈 줄 제거 (앞부분)
        while content_lines and not content_lines[0].strip():
            content_lines.pop(0)
        
        new_content = '\n'.join(content_lines)
        
        return new_title, new_content
    
    def rewrite_for_platform(
        self,
        original_path: Union[str, Path],
        platform: str
    ) -> str:
        """특정 플랫폼용으로 리라이팅
        
        Args:
            original_path: 원본 글 경로 (approved/ 폴더의 파일)
            platform: 대상 플랫폼 (naver / tistory / wordpress)
        
        Returns:
            리라이팅된 콘텐츠
        """
        if platform not in self.PLATFORMS:
            raise ValueError(f"지원하지 않는 플랫폼: {platform}. 가능한 값: {self.PLATFORMS}")
        
        original_path = Path(original_path)
        
        # 원본 로드
        post = frontmatter.load(original_path)
        original_content = post.content
        original_title = post.get("title", "제목 없음")
        persona = post.get("persona", PromptBuilder.DEFAULT_PERSONA)
        
        # 프롬프트 생성
        system_prompt = self.prompt_builder.build_platform_rewrite_prompt(platform, persona)
        user_prompt = self.prompt_builder.build_rewrite_prompt(
            original_content, platform, original_title, persona
        )
        
        logger.info(f"🔄 {platform.upper()}용 리라이팅 중: {original_title}")
        
        # AI 리라이팅
        rewritten_content = self.ai_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.8  # 약간 더 높은 창의성
        )
        
        # 저장
        saved_path = self._save_platform_version(post, rewritten_content, platform, original_path)
        logger.success(f"✅ {platform.upper()} 버전 저장 완료: {saved_path}")
        
        return rewritten_content
    
    def rewrite_for_all_platforms(self, original_path: Union[str, Path]) -> dict:
        """모든 플랫폼용으로 리라이팅
        
        Args:
            original_path: 원본 글 경로
        
        Returns:
            {platform: content} 딕셔너리
        """
        results = {}
        
        for platform in self.PLATFORMS:
            try:
                results[platform] = self.rewrite_for_platform(original_path, platform)
            except Exception as e:
                logger.error(f"❌ {platform} 리라이팅 실패: {e}")
                results[platform] = None
        
        return results
    
    def _save_platform_version(
        self,
        original_post: frontmatter.Post,
        content: str,
        platform: str,
        original_path: Path
    ) -> Path:
        """플랫폼 버전 저장
        
        Args:
            original_post: 원본 포스트 객체
            content: 리라이팅된 콘텐츠
            platform: 플랫폼명
            original_path: 원본 파일 경로
        
        Returns:
            저장된 파일 경로
        """
        # 플랫폼 디렉터리 생성
        platform_dir = self.PLATFORM_DIR / platform
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명은 원본과 동일하게
        filename = original_path.name
        save_path = platform_dir / filename
        
        # 메타데이터 복사 및 추가
        post = frontmatter.Post(content)
        post["title"] = original_post.get("title", "")
        post["keywords"] = original_post.get("keywords", [])
        post["category"] = original_post.get("category", "")
        post["platform"] = platform
        post["persona"] = original_post.get(
            "persona", PromptBuilder.DEFAULT_PERSONA
        )
        post["original_file"] = str(original_path)
        post["rewritten_at"] = datetime.now().isoformat()
        post["status"] = "ready"  # 발행 준비 완료
        
        save_path.write_text(frontmatter.dumps(post), encoding="utf-8")
        
        return save_path
    
    def list_platform_versions(self, platform: str = None) -> list:
        """플랫폼 버전 목록 조회
        
        Args:
            platform: 특정 플랫폼만 조회. None이면 전체
        
        Returns:
            버전 목록
        """
        versions = []
        
        platforms = [platform] if platform else self.PLATFORMS
        
        for p in platforms:
            platform_dir = self.PLATFORM_DIR / p
            if not platform_dir.exists():
                continue
            
            for version_file in sorted(platform_dir.glob("*.md"), reverse=True):
                try:
                    post = frontmatter.load(version_file)
                    versions.append({
                        "path": version_file,
                        "platform": p,
                        "title": post.get("title", "제목 없음"),
                        "rewritten_at": post.get("rewritten_at", ""),
                        "status": post.get("status", "ready"),
                    })
                except Exception as e:
                    logger.warning(f"버전 로드 실패: {version_file} - {e}")
        
        return versions
