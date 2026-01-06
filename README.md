# 멀티 블로그 자동 포스팅 시스템

AI를 활용하여 블로그 글을 작성하고, 네이버/티스토리에 자동으로 포스팅하는 프로그램입니다.

## 🚀 빠른 시작

### 1. 글 작성 준비

```bash
# 1. input 폴더에 글 디렉터리 생성 (년/월/카테고리_주제명)
mkdir -p input/2026/01/맛집_강릉_카페클램

# 2. post.md 파일 생성
# 3. media 폴더에 이미지 추가 (선택)
```

### 2. 발행 (대화형 모드 - 추천)

```bash
# 가상환경 활성화
source .venv/bin/activate

# 대화형 모드 실행 (인자 없이 실행)
python main.py
```

**대화형 모드 흐름:**
1. 자동으로 Git pull 동기화
2. 입력 포스트 목록 표시
3. 발행할 글 번호 선택 (1, 1,2,3, 1-3, all)
4. 발행 플랫폼 선택 (all/naver/tistory)
5. AI 초안 생성 및 발행
6. 완료 후 Git push 제안

### 3. 발행 (직접 명령어)

```bash
# 특정 글 발행 (네이버 + 티스토리)
python main.py run input/2026/01/맛집_강릉_카페클램/post.md -y

# 특정 플랫폼만 발행
python main.py run input/2026/01/맛집_강릉_카페클램/post.md -p naver -y
python main.py run input/2026/01/맛집_강릉_카페클램/post.md -p tistory -y
```

---

## � Git 동기화

### Pull (원격 저장소에서 가져오기)

```bash
cd /Users/jihoon/study/blog
git pull origin main
```

### Push (변경사항 업로드)

```bash
# 모든 변경사항 스테이징
git add .

# 커밋 (메시지 작성)
git commit -m "feat: 블로그 글 발행 - 2026.01.05"

# 원격 저장소에 푸시
git push origin main
```

### 일반적인 작업 흐름

```bash
# 1. 대화형 모드로 실행 (추천)
python main.py

# 또는 수동으로 작업하는 경우:

# 1. 작업 시작 전 최신 상태 동기화
git pull origin main

# 2. 글 작성 및 발행
python main.py run input/2026/01/맛집_카페클램/post.md -y

# 3. 작업 완료 후 저장소에 업로드
git add .
git commit -m "feat: 카페클램 블로그 발행 완료"
git push origin main
```

---

## �📁 디렉터리 명명 규칙

### input 폴더 구조

```
input/
└── {년도}/
    └── {월}/
        └── {카테고리}_{상호명 또는 주제명}/
            ├── post.md          # 글 내용 (필수)
            ├── media/           # 이미지 폴더 (선택)
            │   ├── 1.카페로고.jpg
            │   ├── 2.내부인테리어.jpg
            │   └── 3.메뉴판.jpg
            └── generated/       # AI 생성 초안 저장 (자동 생성)
```

### 디렉터리 이름 규칙

| 구분 | 형식 | 예시 |
|------|------|------|
| 년도 | `YYYY` | `2026` |
| 월 | `MM` | `01`, `12` |
| 글 폴더 | `{카테고리}_{상호명/주제명}` | `맛집_강릉_카페클램`, `여행_제주도_성산일출봉` |

**⚠️ 중요**: 카테고리명은 블로그에 실제로 존재하는 카테고리와 일치해야 합니다!

---

## 📝 post.md 작성법

### 기본 구조

```yaml
---
title: "[강릉여행] 망상해수욕장 뷰 맛집~! 베이커리카페 클램"
keywords: 망상해수욕장, 카페, 감성카페, 분위기카페, 강릉카페
category: 맛집
persona: friendly_woman
---

## 주요 내용
- 방문날짜: 2026-01-04
- 네이버 지도 링크: https://naver.me/xxxxx
- 영업시간: 07:00~22:00
- 특징: 망상해수욕장 바다뷰

## 글의 순서
- 방문날짜
- 위치 정보
- 영업 정보
- 주차 정보
- 가격 정보
```

### 필드 설명

| 필드 | 필수 | 설명 | 예시 |
|------|:----:|------|------|
| `title` | ✅ | 글 제목 (AI가 플랫폼별로 변환) | `"[강릉여행] 카페 클램 방문기"` |
| `keywords` | ✅ | 태그 (쉼표로 구분) | `망상해수욕장, 카페, 강릉카페` |
| `category` | ✅ | 블로그 카테고리 (정확히 일치) | `맛집`, `여행`, `일상` |
| `persona` | ❌ | 글 스타일 | `friendly_woman` (기본), `it_expert` |

### 이미지 삽입

글 본문에서 이미지를 넣을 위치에 `[IMAGE: 파일명]` 형태로 작성:

```markdown
## 주요 내용
- 카페 외관이 예뻤어요

[IMAGE: 1.카페로고.jpg]

- 내부 인테리어도 깔끔했습니다

[IMAGE: 2.내부인테리어.jpg]
```

---

## 🏷️ 카테고리 설정

### 지원되는 카테고리

카테고리는 **각 블로그에 실제로 존재하는 카테고리**를 사용해야 합니다.

**예시 (티스토리):**
- `맛집`
- `여행`
- `숙소`
- `일상`
- `공부&인생`

**예시 (네이버):**
- `맛집`
- `여행`
- `일상`

### 카테고리 확인 방법

1. 티스토리: 블로그 관리 → 카테고리 관리
2. 네이버: 블로그 관리 → 카테고리 설정

---

## 🎭 페르소나

### friendly_woman (기본)
- 친근하고 따뜻한 말투
- 이모지 사용
- 개인적인 경험 공유 스타일
- 예: "여기 진짜 너무 좋았어요~! 💕"

### it_expert
- 전문적이고 객관적인 말투
- 정보 중심의 글
- 예: "해당 카페는 망상해수욕장에 위치하며..."

---

## ⚙️ CLI 명령어

```bash
# 대화형 모드 (추천)
python main.py

# 기본 발행 (네이버 + 티스토리)
python main.py run <post.md 경로> -y

# 특정 플랫폼만 발행
python main.py run <post.md 경로> -p naver -y
python main.py run <post.md 경로> -p tistory -y

# 미리보기 모드 (발행 전 확인)
python main.py run <post.md 경로>

# headless 모드 (브라우저 숨김)
python main.py run <post.md 경로> --headless -y
```

### 옵션 설명

| 옵션 | 설명 |
|------|------|
| `-y`, `--yes` | 확인 없이 바로 발행 |
| `-p`, `--platforms` | 발행 플랫폼 지정 (`naver`, `tistory`, `all`) |
| `--headless` | 브라우저 창 숨김 |

---

## 📊 발행 결과

발행 후 생성되는 파일:

```
input/2026/01/맛집_강릉_카페클램/
├── post.md
├── media/
│   └── ...
└── generated/                    # 자동 생성
    └── 20260104_210000_제목.md   # AI 생성 초안
```

또한 `drafts/` 폴더에도 초안 복사본이 저장됩니다.

---

## ⚠️ 주의사항

### 발행 제한
- **티스토리**: 하루 15개 글 제한
- **네이버**: 제한 없음 (단, 과도한 발행 시 스팸 처리 가능)

### 로그인
- 첫 실행 시 브라우저에서 로그인 필요
- 티스토리: 카카오 2차 인증 필요 (카카오톡 알림)
- 네이버: 자동 로그인 (쿠키 저장)

### 이미지
- 지원 형식: JPG, PNG
- 파일명에 한글 사용 가능
- 본문의 `[IMAGE: 파일명]`과 media 폴더의 파일명이 정확히 일치해야 함

---

## 🔧 설치 및 설정

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일 편집:
```env
# AI API
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 네이버 계정
NAVER_ID=your_naver_id
NAVER_PW=your_password

# 티스토리 계정
TISTORY_ID=your_tistory_id  
TISTORY_PW=your_password
TISTORY_BLOG_NAME=your_blog_name
```

---

## 주요 기능

1. **AI 기반 글 작성**: Claude API를 활용하여 초안 자동 생성
2. **멀티미디어 지원**: 이미지 파일 자동 업로드
3. **다중 플랫폼 포스팅**: 네이버, 티스토리 자동 업로드
4. **플랫폼별 글 변환**: 원본 글에서 각 플랫폼 전용 글로 리라이팅 (중복 콘텐츠 방지)
5. **카테고리 자동 선택**: post.md의 category 필드로 자동 선택
6. **태그 자동 입력**: keywords 필드의 태그 자동 입력
7. **페르소나 선택**: 친근한 여자 스타일(기본) / IT 전문가 스타일 선택 가능

## 프로젝트 구조

```
blog/
├── README.md                    # 프로젝트 설명서
├── requirements.txt             # Python 패키지 의존성
├── .env                         # 환경변수 (API 키, 계정 정보)
├── main.py                      # CLI 실행 파일 (진입점)
│
├── config/
│   └── guidelines/              # AI 글 작성 지침 문서
│       ├── general.md           # 공통 작성 지침 (SEO 포함)
│       ├── personas.md          # 페르소나 설정
│       ├── naver.md             # 네이버 블로그용 지침
│       └── tistory.md           # 티스토리용 지침
│
├── src/
│   ├── ai/                      # AI 글 작성 모듈
│   │   ├── client.py            # Claude API 클라이언트
│   │   ├── prompt_builder.py    # 프롬프트 생성기
│   │   ├── content_generator.py # 콘텐츠 생성 로직
│   │   └── rewriter.py          # 플랫폼별 리라이팅
│   │
│   ├── publishers/              # 블로그 발행 모듈
│   │   ├── naver.py             # 네이버 블로그 자동화
│   │   └── tistory.py           # 티스토리 자동화
│   │
│   ├── cli/                     # CLI 모듈
│   │   └── main.py              # CLI 명령어 처리
│   │
│   └── utils/                   # 유틸리티
│       ├── browser.py           # Selenium 브라우저 관리
│       └── logger.py            # 로깅
│
├── input/                       # 사용자 입력 (주제, 미디어)
│   └── {년도}/
│       └── {월}/
│           └── {카테고리}_{주제명}/
│               ├── post.md
│               ├── media/
│               └── generated/
│
└── drafts/                      # AI 생성 초안 복사본
```

## 기술 스택

- **Python 3.9+**
- **AI API**: Anthropic Claude
- **웹 자동화**: Selenium + ChromeDriver
- **CLI**: Typer + Rich
