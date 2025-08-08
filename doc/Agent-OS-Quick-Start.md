# Agent OS 빠른 시작 가이드 🚀

## 5분 안에 시작하기

### 1️⃣ 설치 (2분)

**PowerShell 관리자 권한으로 실행:**
```powershell
# Agent OS 폴더 생성
mkdir "$env:USERPROFILE\.agent-os\standards" -Force
mkdir "$env:USERPROFILE\.agent-os\instructions" -Force

# GitHub에서 파일 다운로드
$baseUrl = "https://raw.githubusercontent.com/buildermethods/agent-os/main"
$agentOsPath = "$env:USERPROFILE\.agent-os"

# Standards 파일
@("tech-stack.md", "code-style.md", "best-practices.md") | ForEach-Object {
    Invoke-WebRequest -Uri "$baseUrl/standards/$_" -OutFile "$agentOsPath\standards\$_"
}

# Instructions 파일
@("plan-product.md", "create-spec.md", "execute-tasks.md", "analyze-product.md") | ForEach-Object {
    Invoke-WebRequest -Uri "$baseUrl/instructions/$_" -OutFile "$agentOsPath\instructions\$_"
}

Write-Host "✅ Agent OS 설치 완료!" -ForegroundColor Green
```

### 2️⃣ AI 도구 설정 (1분)

**Claude Code 사용자:**
```powershell
# Claude 설정
mkdir "$env:USERPROFILE\.claude\commands" -Force

# 명령어 복사
Copy-Item "$env:USERPROFILE\.agent-os\instructions\*.md" -Destination "$env:USERPROFILE\.claude\commands\"
```

**Cursor 사용자 (프로젝트 폴더에서):**
```powershell
# Cursor 설정
mkdir ".cursor\rules" -Force

# 명령어 복사 (.mdc 확장자)
Get-ChildItem "$env:USERPROFILE\.agent-os\instructions\*.md" | ForEach-Object {
    Copy-Item $_.FullName -Destination ".cursor\rules\$($_.BaseName).mdc"
}
```

### 3️⃣ 표준 설정 (2분)

**VS Code로 편집:**
```cmd
code %USERPROFILE%\.agent-os\standards\
```

**tech-stack.md 수정 예시:**
```markdown
# 기술 스택
## 프론트엔드
- Framework: Next.js 14
- Styling: Tailwind CSS

## 백엔드  
- Runtime: Node.js
- Database: PostgreSQL
```

---

## 🎯 첫 프로젝트 시작

### 새 프로젝트 생성
```
@plan-product

TODO 앱을 만들고 싶습니다.
- 할일 추가/삭제
- 완료 체크
- 카테고리 분류
```

### 기능 추가
```
@create-spec

할일 목록 CRUD 기능을 만들어주세요
```

### 코드 생성
```
@execute-task

다음 작업을 진행해주세요
```

---

## 💡 핵심 명령어 4개

| 명령어 | 용도 |
|--------|------|
| `@plan-product` | 제품 계획 |
| `@create-spec` | 기능 명세 |
| `@execute-task` | 코드 생성 |
| `@analyze-product` | 기존 코드 분석 |

---

## 📁 생성되는 구조

```
프로젝트폴더\
├── .agent-os\
│   ├── product\
│   │   ├── overview.md    # 제품 개요
│   │   └── roadmap.md     # 로드맵
│   └── specs\
│       └── 2025-01-15-feature\
│           └── tasks.md    # 작업 목록
└── [생성된 코드]
```

---

## ⚡ 프로 팁

### 더 나은 결과를 위해:
1. **구체적인 표준 작성** - 예시 코드 포함
2. **명세 검토** - AI가 생성한 작업 목록 확인
3. **단계별 실행** - 한번에 2-3개 작업씩

### 시간 절약 팁:
```
# 다음 기능 자동 선택
@create-spec
로드맵의 다음 기능을 진행해주세요

# 중단한 곳부터 계속
@execute-task
어제 중단한 곳부터 계속해주세요
```

---

## 🔧 문제 해결

### 파일을 찾을 수 없음
```powershell
# 설치 확인
Test-Path "$env:USERPROFILE\.agent-os"

# 재설치
Remove-Item "$env:USERPROFILE\.agent-os" -Recurse -Force
# 위의 설치 스크립트 다시 실행
```

### 명령어가 작동하지 않음
1. AI 도구 재시작
2. 설정 파일 경로 확인
3. .mdc 확장자 확인 (Cursor)

---

## 📚 추가 자료

- 📖 [전체 가이드](Agent-OS-Complete-Guide.md)
- 📺 [YouTube 튜토리얼](https://youtube.com/@briancasel)
- 💬 [제작자 트위터](https://x.com/casjam)
- 📧 [뉴스레터](https://buildermethods.com)

---

**5분 투자로 AI 코딩 95% 자동화! 🚀**

*질문이 있으신가요? 전체 가이드를 참고하세요.*
