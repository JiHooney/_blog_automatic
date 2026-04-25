"""
콘텐츠 생성기
사용자 입력을 바탕으로 블로그 글 생성
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Union
import frontmatter
from loguru import logger

from .client import AIClient
from .prompt_builder import PromptBuilder


class ContentGenerator:
    """블로그 콘텐츠 생성기"""
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    INPUT_DIR = ROOT_DIR / "input"
    DRAFTS_DIR = ROOT_DIR / "drafts"
    
    def __init__(self):
        """콘텐츠 생성기 초기화"""
        self.ai_client = AIClient()
        self.prompt_builder = PromptBuilder()
        logger.info("콘텐츠 생성기 초기화 완료")

    def _get_generated_drafts(self, input_path: Union[str, Path]) -> list[Path]:
        """입력 포스트의 기존 generated 초안 목록 조회"""
        input_path = Path(input_path)
        generated_dir = input_path.parent / "generated"

        if not generated_dir.exists():
            return []

        return sorted(
            [draft for draft in generated_dir.glob("*.md") if draft.is_file()],
            key=lambda draft: draft.stat().st_mtime,
            reverse=True,
        )
    
    def load_input(self, input_path: Union[str, Path]) -> dict:
        """입력 파일 로드
        
        Args:
            input_path: post.md 파일 경로
        
        Returns:
            파싱된 입력 데이터 (메타데이터 + 본문)
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")
        
        # frontmatter 파싱 (YAML 메타데이터 + 마크다운 본문)
        post = frontmatter.load(input_path)
        
        # 미디어 폴더 경로
        media_dir = input_path.parent / "media"
        media_files = []
        if media_dir.exists():
            media_files = list(media_dir.iterdir())
        
        result = {
            "title": post.get("title", "제목 없음"),
            "keywords": post.get("keywords", "").split(", ") if isinstance(post.get("keywords"), str) else post.get("keywords", []),
            "category": post.get("category", ""),
            "persona": post.get("persona", "friendly_woman"),
            "content": post.content,
            "media_files": media_files,
            "input_path": input_path,
        }
        
        logger.info(f"입력 파일 로드 완료: {result['title']}")
        return result
    
    def _parse_main_points(self, content: str) -> list:
        """본문에서 주요 포인트 추출"""
        points = []
        lines = content.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                points.append(line[2:])
            elif line.startswith("## "):
                # 섹션 제목도 포인트로 추가
                continue
        
        return points if points else [content[:500]]  # 포인트가 없으면 본문 일부 사용
    
    def _extract_media_descriptions(self, content: str, media_files: list) -> list:
        """미디어 설명 추출"""
        descriptions = []
        
        # 본문에서 이미지/영상 설명 추출
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("!["):  # 마크다운 이미지
                # ![설명](경로) 형식에서 설명 추출
                start = line.find("[") + 1
                end = line.find("]")
                if start > 0 and end > start:
                    descriptions.append(line[start:end])
            elif "<!-- " in line and "-->" in line:  # HTML 주석
                start = line.find("<!-- ") + 5
                end = line.find(" -->")
                if start > 4 and end > start:
                    descriptions.append(line[start:end])
        
        # 미디어 파일명도 추가
        for media_file in media_files:
            if media_file.is_file():
                descriptions.append(f"파일: {media_file.name}")
        
        return descriptions
    
    def generate_draft(self, input_path: Union[str, Path]) -> Path:
        """초안 생성
        
        Args:
            input_path: 입력 파일 경로 (post.md)
        
        Returns:
            생성되었거나 재사용된 초안 파일 경로
        """
        existing_drafts = self._get_generated_drafts(input_path)
        if existing_drafts:
            logger.info(f"⏭️ 기존 generated 초안 재사용: {existing_drafts[0]}")
            return existing_drafts[0]

        # 입력 로드
        input_data = self.load_input(input_path)
        
        # 주요 포인트 추출
        main_points = self._parse_main_points(input_data["content"])
        
        # 미디어 설명 추출
        media_descriptions = self._extract_media_descriptions(
            input_data["content"],
            input_data["media_files"]
        )
        
        # 프롬프트 생성
        system_prompt = self.prompt_builder.build_system_prompt(input_data["persona"])
        user_prompt = self.prompt_builder.build_content_prompt(
            title=input_data["title"],
            main_points=main_points,
            keywords=input_data["keywords"],
            category=input_data["category"],
            media_descriptions=media_descriptions
        )
        
        logger.info(f"AI 초안 생성 중: {input_data['title']}")
        
        # AI 생성
        draft_content = self.ai_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        # 초안 저장
        draft_path = self._save_draft(input_data, draft_content)
        logger.success(f"✅ 초안 저장 완료: {draft_path}")
        
        return draft_path
    
    def _save_draft(self, input_data: dict, content: str) -> Path:
        """초안 저장
        
        Args:
            input_data: 입력 데이터
            content: 생성된 콘텐츠
        
        Returns:
            저장된 파일 경로
        """
        # input 폴더 내 generated 하위 폴더에 저장
        input_path = Path(input_data["input_path"])
        generated_dir = input_path.parent / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성 (날짜_제목)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in input_data["title"] if c.isalnum() or c in " -_").strip()
        safe_title = safe_title.replace(" ", "_")[:50]
        filename = f"{timestamp}_{safe_title}.md"
        
        draft_path = generated_dir / filename
        
        # 기존 drafts 폴더에도 복사 (호환성 유지)
        self.DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        drafts_copy_path = self.DRAFTS_DIR / filename
        
        # 메타데이터와 함께 저장
        post = frontmatter.Post(content)
        post["title"] = input_data["title"]
        post["keywords"] = input_data["keywords"]
        post["category"] = input_data["category"]
        post["persona"] = input_data["persona"]
        post["created_at"] = datetime.now().isoformat()
        post["status"] = "draft"
        post["source"] = str(input_data["input_path"])
        post["input_dir"] = str(input_path.parent)  # 입력 디렉터리 경로 저장
        
        # generated 폴더에 저장
        draft_path.write_text(frontmatter.dumps(post), encoding="utf-8")
        
        # drafts 폴더에도 복사
        drafts_copy_path.write_text(frontmatter.dumps(post), encoding="utf-8")
        
        logger.info(f"📁 초안 저장: {draft_path}")
        logger.info(f"📁 복사본 저장: {drafts_copy_path}")
        
        return draft_path
    
    def list_drafts(self) -> list:
        """초안 목록 조회"""
        drafts = []
        
        if not self.DRAFTS_DIR.exists():
            return drafts
        
        for draft_file in sorted(self.DRAFTS_DIR.glob("*.md"), reverse=True):
            try:
                post = frontmatter.load(draft_file)
                drafts.append({
                    "path": draft_file,
                    "title": post.get("title", "제목 없음"),
                    "created_at": post.get("created_at", ""),
                    "status": post.get("status", "draft"),
                })
            except Exception as e:
                logger.warning(f"초안 로드 실패: {draft_file} - {e}")
        
        return drafts
    
    def list_input_posts(self, year: str = None, month: str = None) -> list:
        """입력 포스트 목록 조회
        
        새 디렉터리 구조: input/YYYY/MM/포스트명/post.md
        
        Args:
            year: 연도 필터 (예: "2026")
            month: 월 필터 (예: "01")
        
        Returns:
            포스트 정보 목록
        """
        posts = []
        
        if not self.INPUT_DIR.exists():
            return posts
        
        # 검색 경로 결정
        if year and month:
            search_path = self.INPUT_DIR / year / month
        elif year:
            search_path = self.INPUT_DIR / year
        else:
            search_path = self.INPUT_DIR
        
        if not search_path.exists():
            return posts
        
        # 모든 post.md 파일 찾기
        for post_file in search_path.rglob("post.md"):
            try:
                post = frontmatter.load(post_file)
                post_dir = post_file.parent
                
                # 미디어 파일 목록
                media_dir = post_dir / "media"
                media_files = list(media_dir.iterdir()) if media_dir.exists() else []

                # 업데이트 시간 계산 (post.md, media, generated, published.json 중 최신)
                try:
                    updated_ts = post_file.stat().st_mtime
                except Exception:
                    updated_ts = 0
                try:
                    generated_dir = post_dir / "generated"
                    if generated_dir.exists():
                        gen_times = [f.stat().st_mtime for f in generated_dir.glob("*.md") if f.is_file()]
                        if gen_times:
                            updated_ts = max(updated_ts, max(gen_times))
                except Exception:
                    pass
                try:
                    pub_file = post_dir / "published.json"
                    if pub_file.exists():
                        updated_ts = max(updated_ts, pub_file.stat().st_mtime)
                except Exception:
                    pass
                try:
                    if media_files:
                        media_times = [f.stat().st_mtime for f in media_files if f.is_file()]
                        if media_times:
                            updated_ts = max(updated_ts, max(media_times))
                except Exception:
                    pass
                updated_at = datetime.fromtimestamp(updated_ts).strftime("%Y-%m-%d %H:%M") if updated_ts else "-"
                
                # 경로에서 연/월 추출
                rel_path = post_dir.relative_to(self.INPUT_DIR)
                parts = rel_path.parts
                
                # 키워드 파싱 (문자열이면 쉼표로 분리)
                keywords = post.get("keywords", [])
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(",") if k.strip()]
                
                posts.append({
                    "path": post_file,
                    "dir": post_dir,
                    "title": post.get("title", post_dir.name),
                    "keywords": keywords,
                    "category": post.get("category", ""),
                    "persona": post.get("persona", "friendly_woman"),
                    "year": parts[0] if len(parts) > 0 else "",
                    "month": parts[1] if len(parts) > 1 else "",
                    "folder_name": parts[2] if len(parts) > 2 else post_dir.name,
                    "media_count": len(media_files),
                    "media_files": media_files,
                    "updated_ts": updated_ts,
                    "updated_at": updated_at,
                    "published": self._get_publish_status(post_dir),
                })
            except Exception as e:
                logger.warning(f"포스트 로드 실패: {post_file} - {e}")
        
        return sorted(posts, key=lambda x: (x.get("year", ""), x.get("month", ""), x.get("folder_name", "")))
    
    def _get_publish_status(self, post_dir: Path) -> dict:
        """발행 상태 확인
        
        Args:
            post_dir: 포스트 디렉터리
        
        Returns:
            발행 상태 딕셔너리 {"naver": "2026-01-06 10:30", "tistory": None}
        """
        import json
        
        published_file = post_dir / "published.json"
        if published_file.exists():
            try:
                with open(published_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"naver": None, "tistory": None}
    
    @staticmethod
    def mark_as_published(post_dir: Path, platform: str):
        """발행 완료 표시
        
        Args:
            post_dir: 포스트 디렉터리
            platform: 발행된 플랫폼 (naver, tistory)
        """
        import json
        
        published_file = Path(post_dir) / "published.json"
        
        # 기존 데이터 로드
        data = {"naver": None, "tistory": None}
        if published_file.exists():
            try:
                with open(published_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                pass
        
        # 발행 시간 기록
        data[platform] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 저장
        with open(published_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 발행 기록 저장: {platform} - {published_file}")
    
    def generate_all_drafts(self, year: str = None, month: str = None) -> list:
        """모든 입력 포스트에 대해 초안 생성
        
        Args:
            year: 연도 필터
            month: 월 필터
        
        Returns:
            생성된 초안 경로 목록
        """
        posts = self.list_input_posts(year=year, month=month)
        generated = []
        
        for post_info in posts:
            try:
                logger.info(f"📝 초안 생성 중: {post_info['title']}")
                draft_path = self.generate_draft(post_info["path"])
                generated.append(draft_path)
            except Exception as e:
                logger.error(f"❌ 초안 생성 실패: {post_info['title']} - {e}")
        
        return generated
