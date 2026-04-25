# 🚀 설치 가이드

이 문서는 블로그 자동 발행 시스템을 새 PC에 설치하는 방법을 설명합니다.

## 📋 시스템 요구사항

| 항목 | 최소 버전 | 비고 |
|------|----------|------|
| Python | 3.10+ | 3.11, 3.12 권장 |
| Chrome | 최신 버전 | 자동화에 필요 |
| OS | Windows 10+, macOS 10.15+, Ubuntu 20.04+ | |
| RAM | 4GB+ | 브라우저 자동화로 인해 |
| 저장공간 | 1GB+ | |

---

## 🪟 Windows 설치 가이드

### 1단계: Python 설치

1. [Python 공식 사이트](https://www.python.org/downloads/) 접속
2. "Download Python 3.12.x" 클릭
3. 설치 시 **반드시** ✅ "Add Python to PATH" 체크
4. 설치 완료 후 확인:
   ```cmd
   python --version
   pip --version
   ```

### 2단계: Chrome 브라우저 설치

1. [Chrome 다운로드](https://www.google.com/chrome/) 접속
2. 다운로드 및 설치
3. Chrome이 최신 버전인지 확인 (설정 > Chrome 정보)

### 3단계: Git 설치 (선택사항)

1. [Git for Windows](https://git-scm.com/download/win) 다운로드
2. 기본 옵션으로 설치

### 4단계: 프로젝트 설정

```cmd
# 프로젝트 클론 (Git 사용 시)
git clone https://github.com/JiHooney/_blog_automatic.git
cd _blog_automatic

# 또는 ZIP 다운로드 후 압축 해제

# 가상환경 생성
python -m venv .venv

# 가상환경 활성화 (Windows CMD)
.venv\Scripts\activate

# 가상환경 활성화 (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# (선택) 이미지 업로드 기능 사용 시 - PowerShell이 작동하지 않으면 설치
pip install pywin32
```

### 5단계: 환경변수 설정

```cmd
# .env 파일 생성
copy .env.example .env

# 메모장으로 .env 파일 편집
notepad .env
```

`.env` 파일에 필요한 값들을 입력:
```
ANTHROPIC_API_KEY=sk-ant-xxxxx
TISTORY_ID=your_email@example.com
TISTORY_PASSWORD=your_password
TISTORY_BLOG_NAME=your_blog
```

### 6단계: 실행

```cmd
python main.py
```

---

## 🍎 macOS 설치 가이드

### 1단계: Homebrew 설치 (권장)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2단계: Python 설치

```bash
# Homebrew로 설치
brew install python@3.12

# 확인
python3 --version
pip3 --version
```

### 3단계: Chrome 브라우저 설치

```bash
brew install --cask google-chrome
```

### 4단계: 프로젝트 설정

```bash
# 프로젝트 클론
git clone https://github.com/JiHooney/_blog_automatic.git
cd _blog_automatic

# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 5단계: 환경변수 설정

```bash
cp .env.example .env
nano .env  # 또는 vi .env
```

### 6단계: 실행

```bash
python main.py
```

---

## 🐧 Linux (Ubuntu) 설치 가이드

### 1단계: Python 설치

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

### 2단계: Chrome 설치

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install
```

### 3단계: 프로젝트 설정

```bash
git clone https://github.com/JiHooney/_blog_automatic.git
cd _blog_automatic

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 4단계: 환경변수 설정 및 실행

```bash
cp .env.example .env
nano .env

python main.py
```

---

## 🔑 필수 환경변수

| 변수명 | 설명 | 필수 여부 |
|--------|------|----------|
| `ANTHROPIC_API_KEY` | Claude AI API 키 | ✅ 필수 |
| `TISTORY_ID` | 티스토리 로그인 ID (이메일) | 티스토리 발행 시 필수 |
| `TISTORY_PASSWORD` | 티스토리 비밀번호 | 티스토리 발행 시 필수 |
| `TISTORY_BLOG_NAME` | 티스토리 블로그 이름 | 티스토리 발행 시 필수 |
| `NAVER_ID` | 네이버 로그인 ID | 네이버 발행 시 필수 |
| `NAVER_PASSWORD` | 네이버 비밀번호 | 네이버 발행 시 필수 |
| `NAVER_BLOG_ID` | 네이버 블로그 주소 ID | 네이버 발행 시 선택 |

### API 키 발급 방법

**Anthropic API Key:**
1. [Anthropic Console](https://console.anthropic.com/) 접속
2. 회원가입 또는 로그인
3. API Keys 메뉴에서 새 키 생성
4. 결제 정보 등록 필요 (사용량 기반 과금)

---

## ⚠️ 주의사항

### Windows 관련
- PowerShell에서 스크립트 실행 정책 오류 시:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### 2차 인증 관련
- 티스토리 로그인 시 카카오톡 2차 인증이 필요할 수 있습니다
- `headless=False` 모드에서 수동으로 인증해야 합니다
- 첫 실행 시 브라우저 창이 열리면 직접 인증을 완료하세요

### 이미지 업로드
- ✅ **macOS**: 자동 지원 (osascript)
- ✅ **Windows**: 자동 지원 (PowerShell). 문제 발생 시 `pip install pywin32` 추가 설치
- ✅ **Linux**: `xclip` 필요 - `sudo apt install xclip`

---

## 🔧 문제 해결

### Chrome WebDriver 오류
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```
→ `webdriver-manager`가 자동으로 처리합니다. Chrome을 최신 버전으로 업데이트하세요.

### ModuleNotFoundError
```
ModuleNotFoundError: No module named 'xxx'
```
→ 가상환경이 활성화되어 있는지 확인하고, `pip install -r requirements.txt` 재실행

### Permission Denied (macOS/Linux)
```bash
chmod +x main.py
```

---

## 📁 프로젝트 구조

```
blog/
├── main.py              # 메인 실행 파일
├── requirements.txt     # Python 의존성
├── .env                 # 환경변수 (직접 생성)
├── .env.example         # 환경변수 예시
├── src/
│   ├── ai/              # AI 콘텐츠 생성
│   ├── publishers/      # 플랫폼별 발행기
│   └── utils/           # 유틸리티
├── input/               # 입력 파일 (원본 글, 이미지)
├── drafts/              # AI 생성 초안
├── approved/            # 승인된 글
└── published/           # 발행 완료 기록
```

---

## ✅ 설치 확인 체크리스트

- [ ] Python 3.10+ 설치됨
- [ ] Chrome 최신 버전 설치됨
- [ ] 가상환경 생성 및 활성화됨
- [ ] 의존성 설치 완료 (`pip install -r requirements.txt`)
- [ ] `.env` 파일 생성 및 API 키 입력됨
- [ ] `python main.py` 실행 시 메뉴가 표시됨
