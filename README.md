# 멀티 블로그 자동 포스팅 시스템

AI를 활용하여 블로그 글을 작성하고, 네이버/티스토리에 자동으로 포스팅하는 프로그램입니다.

**🎉 무료 AI 사용 가능!** - 로컬 free-claude-code 서버로 비용 0원

---

## 📋 목차

1. [사전 준비](#-사전-준비)
2. [설치하기](#-설치하기)
3. [환경 설정](#-환경-설정)
4. [AI 서버 설정](#-ai-서버-설정)
5. [글 작성하기](#-글-작성하기)
6. [발행하기](#-발행하기)
7. [다른 컴퓨터에서 사용](#-다른-컴퓨터에서-사용)
8. [자주 묻는 질문](#-자주-묻는-질문)

---

## 📦 사전 준비

프로그램 실행에 필요한 것들:

| 항목 | 설명 | 확인 방법 |
|------|------|----------|
| Python 3.9+ | 프로그래밍 언어 | `python --version` |
| Git | 버전 관리 도구 | `git --version` |
| Chrome 브라우저 | 웹 자동화용 | 설치 여부 확인 |

> 💡 **AI API 키 불필요!** 무료 로컬 서버를 사용합니다.

---

## 🔧 설치하기

### Windows 사용자

**1단계: 프로젝트 폴더로 이동**
```powershell
cd C:\Users\{사용자명}\study\_blog_automatic
```

**2단계: 가상환경 생성** (최초 1회만)
```powershell
python -m venv .venv
```

**3단계: 가상환경 활성화**

> ⚠️ **터미널 종류에 따라 다릅니다!**

| 터미널 | 활성화 명령어 |
|--------|--------------|
| Git Bash | `source .venv/Scripts/activate` |
| PowerShell | `.venv\Scripts\Activate.ps1` |
| CMD | `.venv\Scripts\activate.bat` |

**4단계: 패키지 설치**
```bash
pip install -r requirements.txt
```

---

### Mac / Linux 사용자

**1단계: 프로젝트 폴더로 이동**
```bash
cd ~/study/_blog_automatic
```

**2단계: 가상환경 생성** (최초 1회만)
```bash
python3 -m venv .venv
```

**3단계: 가상환경 활성화**
```bash
source .venv/bin/activate
```

**4단계: 패키지 설치**
```bash
pip install -r requirements.txt
```

---

## ⚙️ 환경 설정

### 1단계: 환경변수 파일 생성

**Windows (PowerShell)**
```powershell
copy .env.example .env
```

**Windows (Git Bash) / Mac / Linux**
```bash
cp .env.example .env
```

### 2단계: .env 파일 편집

메모장이나 VS Code로 `.env` 파일을 열고 아래 내용을 입력하세요:

```env
# AI 서버 설정 (무료 로컬 서버)
USE_LOCAL_SERVER=true
FREE_CLAUDE_CODE_URL=http://localhost:8083
ANTHROPIC_AUTH_TOKEN=freecc

# 외부 API 사용 시 (유료)
# USE_LOCAL_SERVER=false
# EXTERNAL_AI_URL=https://api.anthropic.com
# EXTERNAL_AI_KEY=sk-ant-api03-xxxxxxxxxxxxx

# 네이버 계정 (네이버 발행 시 필요)
NAVER_ID=네이버아이디
NAVER_PASSWORD=네이버비밀번호
NAVER_BLOG_ID=네이버블로그주소아이디

# 티스토리 계정 (티스토리 발행 시 필요)
TISTORY_ID=티스토리아이디
TISTORY_PASSWORD=티스토리비밀번호
TISTORY_BLOG_NAME=블로그주소명
```

> 💡 **TISTORY_BLOG_NAME**: `https://블로그주소명.tistory.com` 에서 `블로그주소명` 부분만 입력
> 💡 **NAVER_BLOG_ID**: `https://blog.naver.com/블로그주소아이디` 에서 마지막 아이디를 입력. 비워두면 `NAVER_ID`를 사용

---

## 🤖 AI 서버 설정

### 옵션 1: 무료 로컬 서버 사용 (추천)

**1단계: AI 서버 시작**
```bash
python blog_cli.py server start
```

**2단계: 다른 터미널에서 블로그 프로그램 실행**
```bash
python blog_cli.py content generate "input/2026/01/맛집_용인_보석한우/post.md"
```

**서버 관리 명령어:**
```bash
# 서버 시작
python blog_cli.py server start

# 서버 상태 확인
python blog_cli.py server status

# 서버 중지
python blog_cli.py server stop
```

### 옵션 2: 유료 외부 API 사용

`.env` 파일에서 설정 변경:
```env
USE_LOCAL_SERVER=false
EXTERNAL_AI_URL=https://api.anthropic.com
EXTERNAL_AI_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

---

## ✍️ 글 작성하기

### 폴더 구조 이해하기

```
input/
└── 2026/                          # 년도
    └── 02/                        # 월
        └── 맛집_강릉_카페클램/      # 카테고리_주제
            ├── post.md            # 글 내용 (필수)
            └── media/             # 이미지 폴더 (선택)
                ├── 1.카페외관.jpg
                └── 2.음료사진.jpg
```

### 1단계: 폴더 만들기

**Windows (PowerShell)**
```powershell
New-Item -ItemType Directory -Force "input\2026\02\맛집_강릉_카페클램\media"
```

**Windows (Git Bash) / Mac / Linux**
```bash
mkdir -p input/2026/02/맛집_강릉_카페클램/media
```

### 2단계: post.md 파일 작성

폴더 안에 `post.md` 파일을 생성하고 아래 형식으로 작성:

```yaml
---
title: "강릉 망상해수욕장 뷰 맛집! 베이커리카페 클램"
keywords:
  - 망상해수욕장
  - 강릉카페
  - 바다뷰카페
category: "맛집"
persona: "friendly_woman"
---

## 방문 정보
- 위치: https://naver.me/xxxxx
- 영업시간: 09:00~21:00
- 주차: 무료주차 가능

## 주요 내용
- 망상해수욕장이 한눈에 보이는 오션뷰
- 시그니처 메뉴: 클램 라떼, 딸기케이크
- 2층 창가석 추천

## 사진 설명
[IMAGE: 1.카페외관.jpg]
카페 외관이 너무 예뻤어요

[IMAGE: 2.음료사진.jpg]
시그니처 클램 라떼
```

### 필드 설명

| 필드 | 필수 | 설명 |
|------|:----:|------|
| `title` | ✅ | 글 제목 |
| `keywords` | ✅ | 태그/키워드 (리스트 형태) |
| `category` | ✅ | 블로그 카테고리명 |
| `persona` | ❌ | `friendly_woman`(기본) 또는 `it_expert` |

### 3단계: 이미지 추가 (선택)

`media` 폴더에 이미지 파일을 넣고, `post.md`에서 `[IMAGE: 파일명]` 형식으로 참조합니다.

---

## 🚀 발행하기

### 방법 1: 대화형 모드 (추천)

가장 쉬운 방법! 프로그램이 단계별로 안내해줍니다.

**Windows (Git Bash)**
```bash
source .venv/Scripts/activate
python main.py
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
python main.py
```

**Mac / Linux**
```bash
source .venv/bin/activate
python main.py
```

**실행 후 화면:**
```
📋 발행 가능한 글 목록:
  [1] 맛집_강릉_카페클램
  [2] 숙박_베이징_홀리데이인

👉 발행할 글 번호를 입력하세요 (예: 1, 1-3, all): 1
👉 발행 플랫폼을 선택하세요 (naver/tistory/all): all

✅ AI 초안 생성 중...
✅ 네이버 발행 완료!
✅ 티스토리 발행 완료!
```

### 방법 2: 직접 명령어

특정 글을 바로 발행하고 싶을 때:

```bash
# 네이버 + 티스토리 모두 발행
python main.py run input/2026/02/맛집_강릉_카페클램/post.md -y

# 네이버만 발행
python main.py run input/2026/02/맛집_강릉_카페클램/post.md -p naver -y

# 티스토리만 발행
python main.py run input/2026/02/맛집_강릉_카페클램/post.md -p tistory -y
```

### 명령어 옵션

| 옵션 | 설명 |
|------|------|
| `-y` | 확인 없이 바로 발행 |
| `-p naver` | 네이버만 발행 |
| `-p tistory` | 티스토리만 발행 |
| `--headless` | 브라우저 창 숨기고 실행 |

---

## 🌐 다른 컴퓨터에서 사용

### 방법 1: Git Clone (추천)

**1단계: 프로젝트 복제**
```bash
git clone https://github.com/JiHooney/_blog_automatic.git
cd _blog_automatic
```

**2단계: 가상환경 생성 및 활성화**
```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# 또는
.venv\Scripts\activate  # Windows
```

**3단계: 패키지 설치**
```bash
pip install -r requirements.txt
```

**4단계: 환경 설정**
```bash
cp .env.example .env
# .env 파일 편집
```

**5단계: AI 서버 시작**
```bash
python blog_cli.py server start
```

**6단계: 사용**
```bash
python blog_cli.py content generate "input/2026/01/맛집_용인_보석한우/post.md"
```

### 방법 2: 외부 API 사용 (서버 없이)

로컬 서버 없이 바로 사용하려면 `.env` 설정 변경:

```env
USE_LOCAL_SERVER=false
EXTERNAL_AI_URL=https://api.anthropic.com
EXTERNAL_AI_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

> ⚠️ **주의**: 외부 API 사용 시 비용이 발생합니다.

---

## 🔄 Git 동기화 (선택)

여러 컴퓨터에서 작업할 때 유용합니다.

### 최신 버전 가져오기

```bash
git pull origin main
```

### 변경사항 업로드하기

```bash
git add .
git commit -m "feat: 카페클램 블로그 발행"
git push origin main
```

---

## ❓ 자주 묻는 질문

### Q: AI 서버가 없다고 에러가 나요

**A:** AI 서버를 먼저 시작해야 합니다.

```bash
# 서버 시작
python blog_cli.py server start

# 다른 터미널에서 사용
python blog_cli.py content generate "input/2026/01/맛집_용인_보석한우/post.md"
```

### Q: 다른 컴퓨터에서 사용할 수 있나요?

**A:** 네! Git으로 복제하면 됩니다.

```bash
git clone https://github.com/JiHooney/_blog_automatic.git
cd _blog_automatic
# 설치 및 설정 후 사용
```

### Q: 무료로 사용할 수 있나요?

**A:** 네! 로컬 서버를 사용하면 비용 0원입니다.

- **무료**: 로컬 free-claude-code 서버 (USE_LOCAL_SERVER=true)
- **유료**: 외부 Anthropic API (USE_LOCAL_SERVER=false)

### Q: `ModuleNotFoundError: No module named 'typer'` 에러가 나요

**A:** 가상환경이 활성화되지 않았거나, 패키지가 설치되지 않은 경우입니다.

**Windows (Git Bash)**
```bash
source .venv/Scripts/activate
pip install -r requirements.txt
```

**Mac / Linux**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Q: 티스토리 로그인이 안 돼요

**A:** 카카오 2차 인증이 필요합니다. 브라우저가 뜨면 카카오톡에서 인증을 완료해주세요.

### Q: 카테고리를 못 찾는다고 해요

**A:** `post.md`의 `category` 값이 블로그에 실제로 있는 카테고리명과 **정확히 일치**해야 합니다.

### Q: 이미지가 업로드되지 않아요

**A:** 
1. `media` 폴더 안에 이미지 파일이 있는지 확인
2. `post.md`의 `[IMAGE: 파일명]`과 실제 파일명이 정확히 일치하는지 확인

---

## 📁 폴더 구조 상세

```
blog/
├── main.py                      # 실행 파일 (진입점)
├── requirements.txt             # Python 패키지 의존성
├── .env                         # 환경변수 (API 키, 계정 정보)
│
├── input/                       # 사용자 입력 폴더
│   └── {년도}/{월}/{카테고리}_{주제}/
│       ├── post.md              # 글 내용
│       ├── media/               # 이미지 폴더
│       └── generated/           # AI 생성 초안 (자동)
│
├── drafts/                      # AI 생성 초안 복사본
│
├── config/guidelines/           # AI 글 작성 지침
│   ├── general.md               # 공통 작성 지침
│   ├── personas.md              # 페르소나 설정
│   ├── naver.md                 # 네이버 블로그용 지침
│   └── tistory.md               # 티스토리용 지침
│
└── src/                         # 소스 코드
    ├── ai/                      # AI 글 작성 모듈
    ├── publishers/              # 블로그 발행 모듈
    ├── cli/                     # CLI 모듈
    └── utils/                   # 유틸리티
```

---

## 🎭 페르소나 종류

| 페르소나 | 스타일 | 예시 |
|---------|--------|------|
| `friendly_woman` (기본) | 친근하고 따뜻한 말투, 이모지 사용 | "여기 진짜 너무 좋았어요~! 💕" |
| `it_expert` | 전문적이고 객관적인 말투 | "해당 카페는 망상해수욕장에 위치하며..." |

---

## ⚠️ 주의사항

| 항목 | 내용 |
|------|------|
| 티스토리 발행 제한 | 하루 15개 글 제한 |
| 네이버 발행 제한 | 제한 없음 (과도한 발행 시 스팸 처리 가능) |
| 첫 로그인 | 브라우저에서 직접 로그인 필요 |
| 티스토리 인증 | 카카오 2차 인증 필요 (카카오톡 알림) |
| 이미지 형식 | JPG, PNG 지원 |

---

## 🛠️ 기술 스택

- **Python 3.9+**
- **AI API**: Free Claude Code (무료) / Anthropic Claude (유료)
- **웹 자동화**: Selenium + ChromeDriver
- **CLI**: Typer + Rich
- **서버 관리**: 자동 로컬 서버 시작/중지
