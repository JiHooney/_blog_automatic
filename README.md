# 멀티 블로그 자동 포스팅 시스템

AI를 활용하여 블로그 글을 작성하고, 네이버/티스토리/워드프레스에 자동으로 포스팅하는 프로그램입니다.

## 주요 기능

1. **AI 기반 글 작성**: AI API를 활용하여 초안 자동 생성 (사용자 제공 주제/미디어 기반)
2. **멀티미디어 지원**: 사진, 영상 등 미디어 파일 포함
3. **다중 플랫폼 포스팅**: 네이버, 티스토리, 워드프레스 자동 업로드
4. **검수 시스템**: AI 초안 → 사용자 확인 → 최종 발행
5. **플랫폼별 글 변환**: 원본 글에서 각 플랫폼 전용 글로 리라이팅 (중복 콘텐츠 방지)
6. **GitLab 연동**: Git pull/push를 통한 버전 관리 및 협업
7. **SEO 최적화**: 각 플랫폼별 SEO 기준에 맞춘 글 작성
8. **페르소나 선택**: 친근한 여자 스타일(기본) / IT 전문가 스타일 선택 가능

## 프로젝트 구조

```
blog/
├── README.md                    # 프로젝트 설명서
├── requirements.txt             # Python 패키지 의존성
├── .env.example                 # 환경변수 템플릿 (API 키 등)
├── config/
│   ├── __init__.py
│   ├── settings.py              # 전역 설정 (API 키, 블로그 계정 정보 등)
│   └── guidelines/              # AI 글 작성 지침 문서
│       ├── general.md           # 공통 작성 지침 (SEO 포함)
│       ├── personas.md          # 페르소나 설정 (friendly_woman / it_expert)
│       ├── naver.md             # 네이버 블로그용 지침
│       ├── tistory.md           # 티스토리용 지침
│       └── wordpress.md         # 워드프레스용 지침
│
├── src/
│   ├── __init__.py
│   │
│   ├── ai/                      # AI 글 작성 모듈
│   │   ├── __init__.py
│   │   ├── client.py            # AI API 클라이언트 (OpenAI, Claude 등)
│   │   ├── prompt_builder.py    # 프롬프트 생성기
│   │   ├── content_generator.py # 콘텐츠 생성 로직
│   │   └── rewriter.py          # 플랫폼별 리라이팅 (중복 방지)
│   │
│   ├── media/                   # 미디어 처리 모듈
│   │   ├── __init__.py
│   │   ├── image_handler.py     # 이미지 처리 (리사이즈, 최적화)
│   │   ├── video_handler.py     # 영상 처리
│   │   └── uploader.py          # 미디어 업로드 공통 로직
│   │
│   ├── publishers/              # 블로그 발행 모듈
│   │   ├── __init__.py
│   │   ├── base.py              # 발행자 베이스 클래스
│   │   ├── naver.py             # 네이버 블로그 자동화
│   │   ├── tistory.py           # 티스토리 자동화
│   │   └── wordpress.py         # 워드프레스 자동화
│   │
│   ├── editor/                  # 글 편집/검수 모듈
│   │   ├── __init__.py
│   │   ├── draft_manager.py     # 초안 관리
│   │   ├── preview.py           # 미리보기 기능
│   │   └── revision.py          # 수정/버전 관리
│   │
│   ├── git/                     # Git 연동 모듈
│   │   ├── __init__.py
│   │   └── sync.py              # GitLab pull/push 자동화
│   │
│   └── utils/                   # 유틸리티
│       ├── __init__.py
│       ├── browser.py           # Selenium/Playwright 브라우저 관리
│       ├── logger.py            # 로깅
│       └── file_handler.py      # 파일 입출력
│
├── templates/                   # 글 템플릿
│   ├── default.md               # 기본 템플릿
│   └── review.md                # 리뷰 글 템플릿
│
├── input/                       # 사용자 입력 (주제, 미디어)
│   └── 2026/                    # 년도별 디렉터리
│       └── 01/                  # 월별 디렉터리
│           └── 글제목-폴더/      # 글 단위 폴더
│               ├── post.md      # 글 내용 (마크다운)
│               └── media/       # 첨부 이미지/영상
│                   ├── 01_이미지.jpg
│                   └── 02_영상.mp4
│
├── drafts/                      # AI 생성 초안 저장소
│   └── .gitkeep
│
├── approved/                    # 사용자 승인된 원본 글
│   └── .gitkeep
│
├── platform_versions/           # 플랫폼별 변환된 글
│   ├── naver/                   # 네이버 전용 버전
│   ├── tistory/                 # 티스토리 전용 버전
│   └── wordpress/               # 워드프레스 전용 버전
│
├── published/                   # 발행 완료된 글 보관
│   └── .gitkeep
│
├── tests/                       # 테스트 코드
│   ├── __init__.py
│   ├── test_ai.py
│   ├── test_publishers.py
│   └── test_media.py
│
└── main.py                      # 메인 실행 파일 (CLI)
```

## 워크플로우

```
┌─────────────────┐
│  Git Pull       │ ← GitLab에서 최신 상태 동기화
└────────┬────────┘
         ▼
┌─────────────────┐
│ 주제/미디어 입력 │ ← input/ 폴더에 저장
└────────┬────────┘
         ▼
┌─────────────────┐
│ AI 초안 생성    │ ← 지침문서 + 입력 내용 참조
└────────┬────────┘
         ▼
┌─────────────────┐
│ 사용자 검수     │ ← 미리보기 & 수정
└────────┬────────┘
         ▼
┌─────────────────┐
│ 원본 글 확정    │ ← approved/ 폴더에 저장
└────────┬────────┘
         ▼
┌─────────────────────────────────────────┐
│      플랫폼별 리라이팅 (AI)             │
│  (중복 콘텐츠 방지를 위한 변환)          │
├─────────────┬─────────────┬─────────────┤
│ 네이버 버전  │ 티스토리 버전 │ 워드프레스 버전 │
└─────────────┴─────────────┴─────────────┘
         ▼
┌─────────────────┐
│ 최종 확인       │ ← 각 버전 검토
└────────┬────────┘
         ▼
┌─────────────────────────────────────────┐
│           자동 발행                      │
├─────────────┬─────────────┬─────────────┤
│   네이버    │  티스토리   │ 워드프레스  │
└─────────────┴─────────────┴─────────────┘
         ▼
┌─────────────────┐
│  Git Push       │ ← GitLab에 변경사항 동기화
└─────────────────┘
```

## 기술 스택

- **Python 3.10+**
- **AI API**: OpenAI GPT / Anthropic Claude
- **웹 자동화**: Selenium 또는 Playwright
- **이미지 처리**: Pillow
- **CLI**: Click 또는 Typer
- **Git 연동**: GitPython

## 설치 및 실행

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 및 계정 정보 입력

# 실행
python main.py
```

## CLI 명령어

```bash
# GitLab 동기화
python main.py sync pull          # 원격 저장소에서 pull
python main.py sync push          # 변경사항 push

# 글 작성 플로우
python main.py new                # 새 글 작성 시작 (input/ 폴더 기반)
python main.py draft list         # 초안 목록 조회
python main.py draft preview      # 초안 미리보기
python main.py approve            # 초안 승인 → 원본 확정

# 플랫폼별 변환
python main.py convert            # 원본 → 네이버/티스토리/워드프레스 버전 생성

# 발행
python main.py publish            # 모든 플랫폼에 발행
python main.py publish --platform naver  # 특정 플랫폼에만 발행
```
