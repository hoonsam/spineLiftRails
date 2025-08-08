@echo off
chcp 65001 >nul
cls
echo ╔══════════════════════════════════════════════════════╗
echo ║         Agent OS 프로젝트 초기화                     ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo 현재 폴더: %CD%
echo.

:: 확인
set /p confirm="이 폴더에 Agent OS를 초기화하시겠습니까? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo 취소되었습니다.
    pause
    exit /b
)
echo.

:: Agent OS 프로젝트 구조 생성
echo [1/3] 프로젝트 구조 생성 중...
mkdir .agent-os 2>nul
mkdir .agent-os\product 2>nul
mkdir .agent-os\specs 2>nul
echo ✅ 폴더 구조 생성 완료
echo.

:: 기본 Product 파일 생성
echo [2/3] Product 문서 생성 중...

:: overview.md
(
echo # 프로젝트 개요
echo.
echo ## 제품명
echo ^[프로젝트 이름^]
echo.
echo ## 설명
echo ^[제품에 대한 간단한 설명^]
echo.
echo ## 목표
echo - ^[주요 목표 1^]
echo - ^[주요 목표 2^]
echo - ^[주요 목표 3^]
echo.
echo ## 타겟 사용자
echo - ^[주요 사용자 그룹^]
echo.
echo ## 핵심 가치
echo - ^[제공하는 가치 1^]
echo - ^[제공하는 가치 2^]
) > .agent-os\product\overview.md

:: roadmap.md
(
echo # 개발 로드맵
echo.
echo ## Phase 1: MVP ^(Week 1-2^)
echo - [ ] 기본 UI 구조
echo - [ ] 핵심 기능 1
echo - [ ] 핵심 기능 2
echo.
echo ## Phase 2: 기능 확장 ^(Week 3-4^)
echo - [ ] 추가 기능 1
echo - [ ] 추가 기능 2
echo - [ ] 사용자 피드백 반영
echo.
echo ## Phase 3: 최적화 ^(Week 5-6^)
echo - [ ] 성능 최적화
echo - [ ] UI/UX 개선
echo - [ ] 테스트 및 버그 수정
echo.
echo ## Phase 4: 출시 준비 ^(Week 7-8^)
echo - [ ] 배포 환경 설정
echo - [ ] 문서화
echo - [ ] 마케팅 준비
) > .agent-os\product\roadmap.md

:: decisions.md
(
echo # 기술 결정사항
echo.
echo ## 2025-01-15: 프로젝트 시작
echo - **결정**: Agent OS 도입
echo - **이유**: AI를 활용한 개발 생산성 향상
echo - **대안**: 수동 개발
echo - **선택 근거**: 개발 시간 단축, 코드 품질 일관성
echo.
echo ## 기술 스택 선택
echo - **프론트엔드**: ^[선택한 프레임워크^]
echo - **백엔드**: ^[선택한 기술^]
echo - **데이터베이스**: ^[선택한 DB^]
echo - **선택 이유**: ^[근거^]
) > .agent-os\product\decisions.md

:: user-stories.md
(
echo # 사용자 스토리
echo.
echo ## 사용자 인증
echo **As a** 사용자
echo **I want to** 로그인할 수 있기를
echo **So that** 개인화된 서비스를 이용할 수 있다
echo.
echo ### 인수 조건
echo - 이메일과 비밀번호로 로그인 가능
echo - 소셜 로그인 지원
echo - 비밀번호 찾기 기능
echo.
echo ## ^[기능명^]
echo **As a** ^[사용자 유형^]
echo **I want to** ^[원하는 것^]
echo **So that** ^[얻고자 하는 가치^]
echo.
echo ### 인수 조건
echo - ^[조건 1^]
echo - ^[조건 2^]
) > .agent-os\product\user-stories.md

echo ✅ Product 문서 생성 완료
echo.

:: Cursor 설정 (옵션)
echo [3/3] AI 도구 설정 중...
if exist ".cursor" (
    echo    Cursor 설정 이미 존재
) else (
    mkdir .cursor\rules 2>nul
    if exist "%USERPROFILE%\.agent-os\instructions" (
        xcopy "%USERPROFILE%\.agent-os\instructions\*.md" ".cursor\rules\" /Y /Q >nul 2>&1
        :: .mdc 확장자로 변경
        for %%f in (.cursor\rules\*.md) do ren "%%f" "%%~nf.mdc" 2>nul
        echo    ✅ Cursor 설정 완료
    ) else (
        echo    ⚠️ Agent OS가 설치되지 않음. install-agent-os.bat 먼저 실행하세요
    )
)
echo.

:: Git 초기화 제안
if not exist ".git" (
    echo 💡 Git 저장소가 없습니다. 초기화하시겠습니까?
    set /p git_init="Git init? (Y/N): "
    if /i "%git_init%"=="Y" (
        git init
        echo ✅ Git 저장소 초기화 완료
    )
    echo.
)

:: 완료 메시지
echo ╔══════════════════════════════════════════════════════╗
echo ║       ✨ 프로젝트 초기화가 완료되었습니다! ✨       ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo 📁 생성된 구조:
echo    .agent-os\
echo    ├── product\
echo    │   ├── overview.md      # 제품 개요
echo    │   ├── roadmap.md      # 개발 로드맵
echo    │   ├── decisions.md    # 기술 결정사항
echo    │   └── user-stories.md # 사용자 스토리
echo    └── specs\              # 기능 명세 (자동 생성됨)
echo.
echo 🚀 다음 단계:
echo    1. product 폴더의 문서들을 프로젝트에 맞게 수정하세요
echo    2. AI 도구에서 @plan-product 명령을 실행하세요
echo    3. @create-spec으로 첫 기능을 정의하세요
echo    4. @execute-task로 코드를 생성하세요
echo.
echo 💡 팁: overview.md와 roadmap.md를 먼저 작성하면 
echo        AI가 더 정확한 코드를 생성합니다!
echo.
pause
