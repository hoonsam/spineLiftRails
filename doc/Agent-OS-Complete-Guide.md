# Agent OS 완전 가이드 (Windows 버전) 🪟

## 목차
1. [Agent OS란?](#agent-os란)
2. [핵심 개념](#핵심-개념)
3. [Windows 설치 방법](#windows-설치-방법)
4. [사용 방법](#사용-방법)
5. [명령어 가이드](#명령어-가이드)
6. [베스트 프랙티스](#베스트-프랙티스)
7. [문제 해결](#문제-해결)

---

## Agent OS란?

**Agent OS**는 AI 코딩 에이전트를 "혼란스러운 인턴"에서 "생산적인 개발자"로 변화시키는 무료 오픈소스 시스템입니다. 

### 🎯 주요 목표
- AI가 **첫 번째 시도**에서 올바른 코드를 작성하도록 지원
- 무작정 프롬프트를 입력하고 재작성을 반복하는 과정을 제거
- 팀의 코딩 표준과 스타일을 AI가 따르도록 학습

### ✨ 3가지 핵심 차별점

1. **3계층 컨텍스트 시스템**
   - Standards (표준): 팀의 코딩 방식
   - Product (제품): 무엇을 만들고 있는지
   - Specs (사양): 다음에 무엇을 만들 것인지

2. **구조화된 워크플로우**
   - 명확한 요구사항 문서 (PRD) 자동 생성
   - 상세한 기술 사양 자동 작성
   - 작업 분해 및 순차적 실행

3. **완전한 커스터마이징**
   - 마크다운 파일로 모든 설정 관리
   - 팀의 고유한 방식에 맞게 조정 가능
   - 모든 AI 도구와 호환

---

## 핵심 개념

### 📂 3계층 구조

#### 1️⃣ **Standards Layer (표준 계층)**
```
C:\Users\%USERNAME%\.agent-os\standards\
├── tech-stack.md      # 기술 스택 정의
├── code-style.md       # 코딩 스타일 가이드
└── best-practices.md   # 베스트 프랙티스
```

**역할**: 팀이 소프트웨어를 만드는 방식을 정의
- 사용하는 프레임워크와 라이브러리
- 코드 포맷팅 규칙
- 네이밍 컨벤션
- 아키텍처 패턴

#### 2️⃣ **Product Layer (제품 계층)**
```
C:\프로젝트폴더\.agent-os\product\
├── overview.md         # 제품 개요
├── roadmap.md         # 로드맵
├── decisions.md       # 주요 결정사항
└── user-stories.md    # 사용자 스토리
```

**역할**: 무엇을 만들고 있는지 문서화
- 제품의 목적과 비전
- 타겟 사용자
- 핵심 기능
- 개발 로드맵

#### 3️⃣ **Specs Layer (사양 계층)**
```
C:\프로젝트폴더\.agent-os\specs\
└── 2025-01-15-user-auth\
    ├── requirements.md  # 요구사항
    ├── technical.md    # 기술 사양
    └── tasks.md        # 작업 목록
```

**역할**: 각 기능의 상세 구현 계획
- 기능 요구사항
- 기술적 접근 방법
- 단계별 작업 분해

---

## Windows 설치 방법

### 🚀 자동 설치 (PowerShell 사용)

#### 사전 준비
1. **PowerShell을 관리자 권한으로 실행**
   - Windows 키 + X 누르기
   - "Windows PowerShell (관리자)" 선택

2. **실행 정책 확인**
   ```powershell
   Get-ExecutionPolicy
   ```
   
   만약 "Restricted"라면:
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

#### 1단계: 기본 설치 스크립트

**PowerShell에서 실행:**
```powershell
# Agent OS 설치 스크립트 다운로드 및 실행
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/buildermethods/agent-os/main/setup.sh" -OutFile "$env:TEMP\setup.sh"

# Git Bash가 있는 경우
& "C:\Program Files\Git\bin\bash.exe" "$env:TEMP\setup.sh"

# 또는 WSL이 있는 경우
wsl bash "$env:TEMP\setup.sh"
```

### 🔧 수동 설치 (Windows 전용)

#### 1. 폴더 구조 생성

**CMD 또는 PowerShell에서:**
```cmd
:: Agent OS 기본 폴더 생성
mkdir %USERPROFILE%\.agent-os
mkdir %USERPROFILE%\.agent-os\standards
mkdir %USERPROFILE%\.agent-os\instructions

:: Claude Code 사용자
mkdir %USERPROFILE%\.claude
mkdir %USERPROFILE%\.claude\commands
```

#### 2. 파일 다운로드 및 복사

**PowerShell 스크립트로 자동 다운로드:**
```powershell
# GitHub에서 파일 다운로드
$baseUrl = "https://raw.githubusercontent.com/buildermethods/agent-os/main"
$agentOsPath = "$env:USERPROFILE\.agent-os"

# Standards 파일 다운로드
@("tech-stack.md", "code-style.md", "best-practices.md") | ForEach-Object {
    Invoke-WebRequest -Uri "$baseUrl/standards/$_" -OutFile "$agentOsPath\standards\$_"
}

# Instructions 파일 다운로드
@("plan-product.md", "create-spec.md", "execute-tasks.md", "analyze-product.md") | ForEach-Object {
    Invoke-WebRequest -Uri "$baseUrl/instructions/$_" -OutFile "$agentOsPath\instructions\$_"
}

Write-Host "✅ Agent OS 파일 다운로드 완료!" -ForegroundColor Green
```

#### 3. AI 도구별 설정

### 📝 Claude Code 설정

**설정 파일 위치:**
```
C:\Users\%USERNAME%\.claude\claude_desktop_config.json
```

**PowerShell로 설정:**
```powershell
# Claude 설정 폴더 생성
$claudePath = "$env:USERPROFILE\.claude"
New-Item -ItemType Directory -Force -Path $claudePath
New-Item -ItemType Directory -Force -Path "$claudePath\commands"

# CLAUDE.md 파일 생성
$claudeMd = @"
# Claude Configuration

## Global Preferences
- Use Agent OS standards from ~/.agent-os/standards/
- Follow instructions from ~/.agent-os/instructions/

## Available Commands
- @plan-product
- @create-spec
- @execute-tasks
- @analyze-product
"@

Set-Content -Path "$claudePath\CLAUDE.md" -Value $claudeMd -Encoding UTF8

# 명령어 파일 복사
$commands = @("plan-product", "create-spec", "execute-tasks", "analyze-product")
foreach ($cmd in $commands) {
    Copy-Item "$env:USERPROFILE\.agent-os\instructions\$cmd.md" -Destination "$claudePath\commands\$cmd.md"
}

Write-Host "✅ Claude Code 설정 완료!" -ForegroundColor Green
```

### 🖱️ Cursor 설정

**프로젝트별 설정 (프로젝트 폴더에서 실행):**
```powershell
# 현재 프로젝트에 Cursor 설정 추가
$projectPath = Get-Location

# .cursor 폴더 생성
New-Item -ItemType Directory -Force -Path "$projectPath\.cursor\rules"

# 명령어 파일 복사 (.mdc 확장자로)
$commands = @("plan-product", "create-spec", "execute-tasks", "analyze-product")
foreach ($cmd in $commands) {
    $source = "$env:USERPROFILE\.agent-os\instructions\$cmd.md"
    $dest = "$projectPath\.cursor\rules\$cmd.mdc"
    Copy-Item $source -Destination $dest
}

Write-Host "✅ Cursor 설정 완료!" -ForegroundColor Green
```

---

## 사용 방법

### 🎬 Windows에서의 전체 워크플로우

#### **1단계: 표준 커스터마이징**

**파일 편집 (메모장 또는 VS Code):**
```cmd
:: 메모장으로 편집
notepad %USERPROFILE%\.agent-os\standards\tech-stack.md

:: VS Code로 편집 (설치되어 있는 경우)
code %USERPROFILE%\.agent-os\standards\
```

**tech-stack.md 예시:**
```markdown
# 기술 스택

## 프론트엔드
- Framework: Next.js 14
- Styling: Tailwind CSS
- State: Zustand
- API: Axios

## 백엔드
- Runtime: Node.js
- Framework: Express
- Database: PostgreSQL
- ORM: Prisma

## 개발 도구
- Package Manager: npm (Windows 호환성 우선)
- Linter: ESLint
- Formatter: Prettier
```

**code-style.md 예시:**
```markdown
# 코드 스타일 가이드

## 네이밍 규칙
- 컴포넌트: PascalCase (예: UserProfile)
- 함수: camelCase (예: getUserData)
- 상수: UPPER_SNAKE_CASE (예: MAX_RETRY_COUNT)
- 파일명: kebab-case (예: user-profile.tsx)

## 들여쓰기
- 스페이스 2칸 사용
- 탭 사용 금지

## 주석
- 복잡한 로직에는 반드시 주석 추가
- JSDoc 형식 사용
- TODO 주석은 이슈 번호 포함
```

**best-practices.md 예시:**
```markdown
# 베스트 프랙티스

## 일반 원칙
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- YAGNI (You Aren't Gonna Need It)

## 에러 처리
- 모든 비동기 함수에 try-catch 사용
- 사용자 친화적 에러 메시지 제공
- 에러 로깅 필수

## 보안
- 환경 변수로 민감한 정보 관리
- 입력값 검증 필수
- SQL 인젝션 방지
```

#### **2단계: 새 프로젝트 생성**

**CMD에서:**
```cmd
:: 프로젝트 폴더 생성
mkdir C:\Projects\my-saas-app
cd C:\Projects\my-saas-app

:: Git 초기화
git init

:: Agent OS 구조 생성
mkdir .agent-os
mkdir .agent-os\product
mkdir .agent-os\specs
```

**AI 도구에서:**
```
@plan-product

SaaS 피드백 관리 도구를 만들고 싶습니다.
주요 기능: 피드백 수집, 감정 분석, 대시보드
타겟: B2B SaaS 제품 매니저
기술 스택: 제 기본 설정 사용
```

#### **3단계: 기능 개발**

```
@create-spec

사용자 인증 기능을 추가해주세요.
- 이메일/비밀번호 로그인
- Google OAuth
- JWT 토큰 기반
```

#### **4단계: 코드 생성**

```
@execute-task

사용자 인증 프로젝트의 다음 작업을 진행해주세요
```

---

## 명령어 가이드

### 📋 주요 명령어

| 명령어 | 용도 | 사용 시점 |
|--------|------|-----------|
| `@plan-product` | 제품 계획 수립 | 새 프로젝트 시작 |
| `@analyze-product` | 기존 코드베이스 분석 | 기존 프로젝트에 Agent OS 도입 |
| `@create-spec` | 기능 명세 작성 | 새 기능 개발 전 |
| `@execute-task` | 작업 실행 | 코딩 시작 |

### 💡 명령어 활용 예시

#### **기존 프로젝트에 Agent OS 적용:**
```
@analyze-product

기존 코드베이스에 Agent OS를 설치하고 싶습니다
```

#### **다음 작업 자동 선택:**
```
@create-spec

로드맵에서 다음 기능은 무엇인가요?
```

#### **여러 작업 한번에 실행:**
```
@execute-task

작업 1과 2를 모든 하위 작업과 함께 완료해주세요
```

#### **버그 수정:**
```
@create-spec

사용자가 대시보드 필터링 시 속도가 느리다고 보고했습니다
```

#### **특정 기술로 구현:**
```
@execute-task

Next.js App Router와 Server Components를 사용해서 구현해주세요
```

---

## 베스트 프랙티스

### ✅ DO (권장사항)

1. **표준을 구체적으로 작성**
   ```markdown
   # 좋은 예
   - API 응답: camelCase 사용
   - 예: { userId: 123, userName: "John" }
   
   # 나쁜 예
   - API 응답: 일관된 형식 사용
   ```

2. **명세 검토를 철저히**
   - AI가 생성한 작업 분해 확인
   - 비즈니스 로직 검증
   - 엣지 케이스 추가

3. **점진적 개선**
   - 각 기능 완료 후 표준 업데이트
   - 패턴 발견 시 문서화
   - 팀과 지식 공유

4. **정기적 유지보수**
   ```markdown
   # 주간 체크리스트
   - [ ] roadmap.md 진행상황 업데이트
   - [ ] decisions.md에 주요 결정 기록
   - [ ] 새로운 패턴을 best-practices.md에 추가
   ```

### ❌ DON'T (피해야 할 것)

1. **너무 많은 작업을 한번에 실행하지 않기**
   - 최대 2-3개 부모 작업씩 진행
   - 각 작업 완료 후 검토

2. **표준 없이 시작하지 않기**
   - 최소한의 표준이라도 정의
   - 프로젝트 진행하며 개선

3. **AI 출력을 맹신하지 않기**
   - 비즈니스 로직은 항상 검토
   - 테스트 코드 실행 확인

---

## Windows 환경 특별 고려사항

### 🔧 경로 설정
```cmd
:: 짧은 경로 사용
C:\Projects\my-app (좋음)
C:\Users\hoons\Documents\My Projects\Application\Frontend (나쁨)

:: 공백 없는 폴더명
my-saas-app (좋음)
My SaaS App (나쁨)
```

### 📝 인코딩 설정
```cmd
:: UTF-8 설정
chcp 65001

:: Git 설정
git config --global core.autocrlf true
git config --global core.eol lf
```

### 🚀 성능 최적화
- OneDrive 폴더 피하기
- Windows Defender 예외 추가
- 안티바이러스 예외 설정

---

## 문제 해결

### 🔧 일반적인 문제와 해결책

#### 1. "명령을 찾을 수 없음" 오류
```powershell
# PATH 환경 변수 확인
$env:PATH -split ';'

# Node.js 경로 추가
[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;C:\Program Files\nodejs", "User")
```

#### 2. 권한 오류
```cmd
:: 관리자 권한으로 CMD 실행
runas /user:Administrator cmd

:: 또는 PowerShell
Start-Process powershell -Verb RunAs
```

#### 3. 인코딩 문제
```cmd
:: UTF-8 설정
chcp 65001

:: VS Code 설정
"files.encoding": "utf8"
```

#### 4. Git Bash 관련 문제
```bash
# .bashrc 파일에 추가
export AGENT_OS_HOME="$HOME/.agent-os"
alias aos-init="mkdir -p .agent-os/{product,specs}"
alias aos-status="ls -la $AGENT_OS_HOME"
```

---

## 파일 구조 요약

### 🏠 전역 설정
```
C:\Users\%USERNAME%\
├── .agent-os\
│   ├── standards\
│   │   ├── tech-stack.md
│   │   ├── code-style.md
│   │   └── best-practices.md
│   └── instructions\
│       ├── plan-product.md
│       ├── create-spec.md
│       ├── execute-tasks.md
│       └── analyze-product.md
└── .claude\
    ├── CLAUDE.md
    └── commands\
        └── [명령어 파일들]
```

### 📁 프로젝트 구조
```
C:\Projects\my-app\
├── .agent-os\
│   ├── product\
│   │   ├── overview.md
│   │   ├── roadmap.md
│   │   └── decisions.md
│   └── specs\
│       └── 2025-01-15-feature\
│           ├── requirements.md
│           ├── technical.md
│           └── tasks.md
├── .cursor\              (Cursor 사용 시)
│   └── rules\
│       └── *.mdc
└── [소스 코드]
```

---

## 빠른 시작 체크리스트

- [ ] Windows PowerShell 또는 Terminal 설치
- [ ] Git 설치
- [ ] Node.js 설치 (선택사항)
- [ ] VS Code 설치 (권장)
- [ ] Agent OS 설치 스크립트 실행
- [ ] Standards 파일 커스터마이징
- [ ] AI 도구 (Claude/Cursor) 설정
- [ ] 첫 프로젝트 생성
- [ ] @plan-product 명령 실행

---

## 실제 사용 예시

### 🎯 전자상거래 사이트 개발
```
@plan-product
전자상거래 플랫폼을 개발하려고 합니다.
- 상품 관리
- 장바구니
- 결제 시스템
- 사용자 인증
기술 스택: Next.js, Supabase, Stripe

@create-spec
상품 목록 페이지를 만들어주세요.
- 그리드 레이아웃
- 필터링 기능
- 정렬 옵션
- 페이지네이션

@execute-task
상품 목록 기능의 다음 작업을 진행해주세요
```

### 🔄 기존 프로젝트 마이그레이션
```
@analyze-product
React 프로젝트를 Next.js로 마이그레이션하고 싶습니다

@create-spec
라우팅 시스템을 App Router로 변경해주세요

@execute-task
라우팅 마이그레이션 작업을 시작해주세요
```

---

## 고급 팁

### 🎨 커스텀 명령어 만들기
```markdown
# ~/.agent-os/instructions/custom-review.md
당신은 코드 리뷰어입니다.
다음 기준으로 코드를 검토하세요:
- 성능
- 보안
- 가독성
- 테스트 커버리지
```

### 🔄 CI/CD 통합
```yaml
# .github/workflows/agent-os.yml
name: Agent OS Validation
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Agent OS Structure
        run: |
          test -d .agent-os/product
          test -f .agent-os/product/roadmap.md
```

### 📊 메트릭 추적
```markdown
# .agent-os/metrics.md
## 2025년 1월
- 생성된 코드 라인: 5,000
- 완료된 기능: 12개
- AI 명령 실행: 45회
- 평균 작업 완료 시간: 2시간
```

---

## 추가 리소스

- 📺 [YouTube 채널](https://youtube.com/@briancasel) - 튜토리얼 영상
- 📧 [Builder Briefing 뉴스레터](https://buildermethods.com) - 최신 업데이트
- 💬 [X (Twitter)](https://x.com/casjam) - 제작자 Brian Casel
- 📚 [GitHub 저장소](https://github.com/buildermethods/agent-os) - 소스 코드

---

## 결론

Agent OS는 AI 코딩 에이전트를 팀의 실제 개발자처럼 만들어주는 강력한 시스템입니다. 

**핵심 가치:**
- ⏱️ 개발 시간 95% 단축
- 📈 코드 품질 향상
- 🎯 일관된 코딩 스타일
- 🔄 반복 작업 자동화

**시작하기:**
1. 설치는 5분
2. 설정은 10분
3. 첫 기능 개발은 30분

**Windows에서 Agent OS로 AI 코딩의 미래를 경험하세요!** 🚀

---

*이 문서는 Agent OS 공식 문서를 기반으로 Windows 사용자를 위해 작성되었습니다.*
*최종 업데이트: 2025년 1월*
