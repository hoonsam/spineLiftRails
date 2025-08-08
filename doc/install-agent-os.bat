@echo off
chcp 65001 >nul
cls
echo ╔══════════════════════════════════════════════════════╗
echo ║           Agent OS Windows 설치 프로그램             ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: 변수 설정
set AGENT_OS_PATH=%USERPROFILE%\.agent-os
set CLAUDE_PATH=%USERPROFILE%\.claude

:: Agent OS 폴더 생성
echo [1/4] Agent OS 폴더 생성 중...
mkdir "%AGENT_OS_PATH%" 2>nul
mkdir "%AGENT_OS_PATH%\standards" 2>nul
mkdir "%AGENT_OS_PATH%\instructions" 2>nul
echo ✅ 폴더 생성 완료
echo.

:: 기본 파일 생성
echo [2/4] 기본 Standards 파일 생성 중...

:: tech-stack.md 생성
(
echo # 기술 스택
echo.
echo ## 프론트엔드
echo - Framework: Next.js 14 App Router
echo - Styling: Tailwind CSS
echo - State Management: Zustand
echo - API Client: Axios
echo - Form Handling: React Hook Form
echo - Validation: Zod
echo.
echo ## 백엔드
echo - Runtime: Node.js 20 LTS
echo - Framework: Express.js
echo - Database: PostgreSQL
echo - ORM: Prisma
echo - Authentication: JWT
echo - File Upload: Multer
echo.
echo ## 개발 도구
echo - Package Manager: npm
echo - Linter: ESLint
echo - Formatter: Prettier
echo - Testing: Jest, React Testing Library
echo - Build Tool: Vite
echo - Version Control: Git
) > "%AGENT_OS_PATH%\standards\tech-stack.md"

:: code-style.md 생성
(
echo # 코드 스타일 가이드
echo.
echo ## 들여쓰기
echo - 스페이스 2칸 사용
echo - 탭 사용 금지
echo.
echo ## 네이밍 규칙
echo - 컴포넌트: PascalCase ^(예: UserProfile^)
echo - 함수: camelCase ^(예: getUserData^)
echo - 상수: UPPER_SNAKE_CASE ^(예: MAX_RETRY_COUNT^)
echo - 파일명: kebab-case ^(예: user-profile.tsx^)
echo - CSS 클래스: kebab-case ^(예: btn-primary^)
echo.
echo ## 파일 구조
echo ```
echo src/
echo ├── components/     # 재사용 가능한 컴포넌트
echo ├── pages/         # 페이지 컴포넌트
echo ├── hooks/         # 커스텀 훅
echo ├── utils/         # 유틸리티 함수
echo ├── services/      # API 서비스
echo ├── stores/        # 상태 관리
echo └── types/         # TypeScript 타입
echo ```
echo.
echo ## 주석
echo - 복잡한 로직에는 반드시 주석 추가
echo - JSDoc 형식 사용
echo - TODO 주석은 이슈 번호 포함
) > "%AGENT_OS_PATH%\standards\code-style.md"

:: best-practices.md 생성
(
echo # 베스트 프랙티스
echo.
echo ## 일반 원칙
echo - DRY ^(Don't Repeat Yourself^)
echo - KISS ^(Keep It Simple, Stupid^)
echo - YAGNI ^(You Aren't Gonna Need It^)
echo - Single Responsibility Principle
echo.
echo ## React/Next.js
echo - Server Components 우선 사용
echo - 클라이언트 상태 최소화
echo - 이미지 최적화 ^(next/image 사용^)
echo - 동적 임포트로 번들 크기 최적화
echo.
echo ## 에러 처리
echo - 모든 비동기 함수에 try-catch 사용
echo - 사용자 친화적 에러 메시지 제공
echo - 에러 경계 ^(Error Boundary^) 구현
echo - 에러 로깅 필수
echo.
echo ## 보안
echo - 환경 변수로 민감한 정보 관리
echo - 입력값 검증 필수
echo - SQL 인젝션 방지
echo - XSS 공격 방지
echo - HTTPS 사용
echo.
echo ## 성능
echo - 레이지 로딩 적용
echo - 메모이제이션 활용
echo - 디바운싱/쓰로틀링 적용
echo - 이미지 최적화
echo - 코드 스플리팅
echo.
echo ## 테스팅
echo - 단위 테스트 작성
echo - 통합 테스트 작성
echo - E2E 테스트 ^(주요 플로우^)
echo - 테스트 커버리지 80% 이상
) > "%AGENT_OS_PATH%\standards\best-practices.md"

echo ✅ Standards 파일 생성 완료
echo.

:: Instructions 다운로드 시도
echo [3/4] Instructions 파일 다운로드 중...
powershell -Command "try { $baseUrl = 'https://raw.githubusercontent.com/buildermethods/agent-os/main'; @('plan-product.md', 'create-spec.md', 'execute-tasks.md', 'analyze-product.md') | ForEach-Object { Invoke-WebRequest -Uri \"$baseUrl/instructions/$_\" -OutFile \"$env:USERPROFILE\.agent-os\instructions\$_\" -ErrorAction Stop }; Write-Host '✅ Instructions 다운로드 완료' -ForegroundColor Green } catch { Write-Host '⚠️ 다운로드 실패 - 기본 템플릿 생성' -ForegroundColor Yellow }" 2>nul

:: 다운로드 실패 시 기본 템플릿 생성
if not exist "%AGENT_OS_PATH%\instructions\plan-product.md" (
    echo # Plan Product > "%AGENT_OS_PATH%\instructions\plan-product.md"
    echo # Create Spec > "%AGENT_OS_PATH%\instructions\create-spec.md"
    echo # Execute Tasks > "%AGENT_OS_PATH%\instructions\execute-tasks.md"
    echo # Analyze Product > "%AGENT_OS_PATH%\instructions\analyze-product.md"
)

:: Claude 설정
echo [4/4] Claude Code 설정 중...
mkdir "%CLAUDE_PATH%" 2>nul
mkdir "%CLAUDE_PATH%\commands" 2>nul

:: 명령어 파일 복사
xcopy "%AGENT_OS_PATH%\instructions\*.md" "%CLAUDE_PATH%\commands\" /Y /Q >nul 2>&1

echo ✅ Claude 설정 완료
echo.

:: 완료 메시지
echo ╔══════════════════════════════════════════════════════╗
echo ║         ✨ Agent OS 설치가 완료되었습니다! ✨       ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo 📁 설치 위치: %AGENT_OS_PATH%
echo.
echo 📝 다음 단계:
echo    1. Standards 파일을 프로젝트에 맞게 수정하세요
echo       %AGENT_OS_PATH%\standards\
echo.
echo    2. AI 도구 (Claude/Cursor)를 재시작하세요
echo.
echo    3. 새 프로젝트에서 다음 명령을 사용하세요:
echo       @plan-product    - 제품 계획
echo       @create-spec     - 기능 명세
echo       @execute-task    - 코드 생성
echo       @analyze-product - 코드 분석
echo.
echo 📚 전체 가이드: Agent-OS-Complete-Guide.md
echo 🚀 빠른 시작: Agent-OS-Quick-Start.md
echo.
pause
