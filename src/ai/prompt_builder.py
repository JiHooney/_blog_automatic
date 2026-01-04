"""
프롬프트 빌더
지침 문서와 페르소나를 기반으로 AI 프롬프트 생성
"""
import os
from pathlib import Path
from loguru import logger


class PromptBuilder:
    """AI 프롬프트 생성기"""
    
    # 프로젝트 루트 디렉터리
    ROOT_DIR = Path(__file__).parent.parent.parent
    GUIDELINES_DIR = ROOT_DIR / "config" / "guidelines"
    
    # 페르소나 매핑
    PERSONAS = {
        "friendly_woman": "친근한 젊은 여자 스타일",
        "it_expert": "IT 전문가 스타일"
    }
    
    def __init__(self):
        """프롬프트 빌더 초기화"""
        self.guidelines = self._load_guidelines()
        logger.info("프롬프트 빌더 초기화 완료")
    
    def _load_guidelines(self) -> dict:
        """지침 문서 로드"""
        guidelines = {}
        
        for file_path in self.GUIDELINES_DIR.glob("*.md"):
            key = file_path.stem  # 파일명 (확장자 제외)
            try:
                guidelines[key] = file_path.read_text(encoding="utf-8")
                logger.debug(f"지침 로드: {key}")
            except Exception as e:
                logger.warning(f"지침 로드 실패 ({key}): {e}")
        
        return guidelines
    
    def build_system_prompt(self, persona: str = "friendly_woman") -> str:
        """시스템 프롬프트 생성
        
        Args:
            persona: 페르소나 타입 (friendly_woman / it_expert)
        
        Returns:
            시스템 프롬프트 문자열
        """
        persona_name = self.PERSONAS.get(persona, self.PERSONAS["friendly_woman"])
        
        # 공통 지침 + 페르소나 정보
        general = self.guidelines.get("general", "")
        personas = self.guidelines.get("personas", "")
        
        system_prompt = f"""당신은 블로그 글을 작성하는 전문 작가입니다.

## 적용할 페르소나: {persona_name}

## 작성 지침
{general}

## 페르소나 상세
{personas}

## 중요 규칙
1. 지정된 페르소나의 말투와 스타일을 일관되게 유지하세요.
2. SEO 최적화 지침을 반드시 따르세요.
3. 이미지/영상 위치는 [IMAGE: 설명] 또는 [VIDEO: 설명] 형식으로 표시하세요.
4. 자연스럽고 읽기 쉬운 글을 작성하세요.
"""
        return system_prompt
    
    def build_content_prompt(
        self,
        title: str,
        main_points: list,
        keywords: list = None,
        category: str = None,
        media_descriptions: list = None
    ) -> str:
        """콘텐츠 생성용 프롬프트
        
        Args:
            title: 글 제목
            main_points: 주요 내용 포인트들
            keywords: SEO 키워드 목록
            category: 카테고리
            media_descriptions: 미디어 설명 목록
        
        Returns:
            사용자 프롬프트 문자열
        """
        prompt = f"""다음 정보를 바탕으로 블로그 글을 작성해주세요.

## 글 정보
- 제목: {title}
- 카테고리: {category or "일반"}
- 키워드: {", ".join(keywords) if keywords else "없음"}

## 주요 내용
{chr(10).join(f"- {point}" for point in main_points)}

"""
        
        if media_descriptions:
            prompt += f"""## 포함할 미디어
{chr(10).join(f"- {desc}" for desc in media_descriptions)}

미디어는 본문 중간중간에 자연스럽게 배치해주세요.
이미지 위치는 [IMAGE: 파일명 또는 설명] 형식으로,
영상 위치는 [VIDEO: 파일명 또는 설명] 형식으로 표시해주세요.

"""
        
        prompt += """## 작성 요청
1. 서론-본론-결론 구조로 작성해주세요.
2. 각 섹션에 적절한 소제목(##)을 사용해주세요.
3. 2,000자 이상으로 충분히 상세하게 작성해주세요.
4. 마지막에 독자 소통 문구를 추가해주세요.
"""
        return prompt
    
    def build_platform_rewrite_prompt(self, platform: str) -> str:
        """플랫폼별 리라이팅용 시스템 프롬프트
        
        Args:
            platform: 플랫폼명 (naver / tistory / wordpress)
        
        Returns:
            플랫폼별 시스템 프롬프트
        """
        platform_guideline = self.guidelines.get(platform, "")
        
        return f"""당신은 블로그 콘텐츠를 리라이팅하는 전문가입니다.

## 플랫폼: {platform.upper()}

## 플랫폼별 지침
{platform_guideline}

## 리라이팅 규칙
1. 원본의 핵심 내용과 의미는 유지하세요.
2. 문장 구조, 표현, 어순을 변경하여 중복 콘텐츠가 되지 않도록 하세요.
3. 해당 플랫폼에 최적화된 스타일로 변환하세요.
4. SEO 요소 (제목, 키워드, 메타 설명)도 플랫폼에 맞게 조정하세요.
5. 이미지/영상 마커 [IMAGE: ...], [VIDEO: ...]는 그대로 유지하세요.
"""
    
    def build_rewrite_prompt(self, original_content: str, platform: str, original_title: str = None) -> str:
        """리라이팅 요청 프롬프트
        
        Args:
            original_content: 원본 글 내용
            platform: 대상 플랫폼
            original_title: 원본 제목
        
        Returns:
            리라이팅 요청 프롬프트
        """
        platform_style = {
            "naver": "친근하고 대화하는 듯한 말투, 이모티콘 적극 활용, 짧은 문단",
            "tistory": "정보 전달 중심, 깔끔한 구조, 전문적인 느낌",
            "wordpress": "글로벌 독자 대상, 체계적인 구조, 상세한 설명"
        }
        
        title_style = {
            "naver": "이모티콘 포함, 호기심 유발, 구어체 (예: '진짜 찐 후기!', '솔직히 말해서요...')",
            "tistory": "키워드 중심, 명확한 정보 전달 (예: '[리뷰] 제품명 - 장단점 분석')",
            "wordpress": "SEO 최적화, 영어 표현 가능 (예: 'Product Review: Pros and Cons')"
        }
        
        return f"""다음 원본 글을 {platform.upper()} 플랫폼에 맞게 완전히 리라이팅해주세요.

## 원본 제목
{original_title or "제목 없음"}

## 원본 글
{original_content}

## 필수 변경 사항

### 1. 제목 변경 (첫 줄에 "# 새로운 제목" 형식으로 작성)
- 스타일: {title_style.get(platform, "명확하고 흥미로운 제목")}
- 원본 제목과 완전히 다르게 작성
- 같은 핵심 키워드는 유지하되 표현 방식을 변경

### 2. 본문 리라이팅
- 스타일: {platform_style.get(platform, "자연스러운 블로그 글")}
- 문장 구조, 어순, 표현을 완전히 다르게
- 핵심 정보는 유지하되 설명 방식을 변경
- 동일한 문장이 3개 이상 연속으로 나오지 않도록

### 3. 구조 변경
- 소제목 표현 방식 변경 (예: "장점" → "좋았던 점", "👍 이건 진짜 좋아요" 등)
- 단락 순서나 구성 변경 가능
- 플랫폼에 맞는 인사말/마무리 추가

## 출력 형식
```
# 새로운 제목

본문 내용...
```
"""
