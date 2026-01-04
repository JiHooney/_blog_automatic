"""
발행자 베이스 클래스
모든 블로그 발행자의 공통 인터페이스 정의
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union
import frontmatter
from loguru import logger


class BasePublisher(ABC):
    """블로그 발행자 베이스 클래스"""
    
    PLATFORM_NAME = "base"
    
    def __init__(self):
        """발행자 초기화"""
        self.driver = None
        self.is_logged_in = False
    
    @abstractmethod
    def login(self) -> bool:
        """블로그 로그인
        
        Returns:
            로그인 성공 여부
        """
        pass
    
    @abstractmethod
    def publish(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[list] = None,
        images: Optional[list] = None
    ) -> bool:
        """글 발행
        
        Args:
            title: 글 제목
            content: 글 내용 (마크다운 또는 HTML)
            category: 카테고리
            tags: 태그 목록
            images: 이미지 파일 경로 목록
        
        Returns:
            발행 성공 여부
        """
        pass
    
    def publish_from_file(self, file_path: Union[str, Path]) -> bool:
        """파일에서 글 정보를 읽어 발행
        
        Args:
            file_path: 마크다운 파일 경로
        
        Returns:
            발행 성공 여부
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"파일을 찾을 수 없습니다: {file_path}")
            return False
        
        # 파일 로드
        post = frontmatter.load(file_path)
        
        title = post.get("title", "제목 없음")
        content = post.content
        category = post.get("category", None)
        keywords = post.get("keywords", [])
        tags = keywords if isinstance(keywords, list) else keywords.split(", ")
        
        # 이미지 경로 추출 (같은 폴더의 media/ 디렉터리)
        media_dir = file_path.parent / "media"
        images = []
        if media_dir.exists():
            images = [f for f in media_dir.iterdir() if f.is_file()]
        
        logger.info(f"📝 발행 준비: {title}")
        
        return self.publish(
            title=title,
            content=content,
            category=category,
            tags=tags,
            images=images
        )
    
    @abstractmethod
    def logout(self):
        """로그아웃 및 브라우저 종료"""
        pass
    
    def __enter__(self):
        """Context manager 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료 - 자동 로그아웃"""
        self.logout()
