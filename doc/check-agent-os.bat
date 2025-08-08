@echo off
chcp 65001 >nul
cls
echo ╔══════════════════════════════════════════════════════╗
echo ║            Agent OS 설치 상태 확인                   ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Agent OS 폴더 확인
if exist "%USERPROFILE%\.agent-os" (
    echo ✅ Agent OS 폴더: 설치됨
    echo    위치: %USERPROFILE%\.agent-os
) else (
    echo ❌ Agent OS 폴더: 설치 안됨
    echo    👉 install-agent-os.bat를 실행하세요
)
echo.

:: Standards 파일 확인
echo 📋 Standards 파일:
if exist "%USERPROFILE%\.agent-os\standards\tech-stack.md" (
    echo    ✅ tech-stack.md
) else (
    echo    ❌ tech-stack.md
)

if exist "%USERPROFILE%\.agent-os\standards\code-style.md" (
    echo    ✅ code-style.md
) else (
    echo    ❌ code-style.md
)

if exist "%USERPROFILE%\.agent-os\standards\best-practices.md" (
    echo    ✅ best-practices.md
) else (
    echo    ❌ best-practices.md
)
echo.

:: Instructions 파일 확인
echo 📋 Instructions 파일:
for %%f in (plan-product create-spec execute-tasks analyze-product) do (
    if exist "%USERPROFILE%\.agent-os\instructions\%%f.md" (
        echo    ✅ %%f.md
    ) else (
        echo    ❌ %%f.md
    )
)
echo.

:: Claude 설정 확인
if exist "%USERPROFILE%\.claude" (
    echo ✅ Claude Code 설정: 구성됨
    echo    위치: %USERPROFILE%\.claude
) else (
    echo ❌ Claude Code 설정: 구성 안됨
)
echo.

:: 프로젝트 Agent OS 확인
if exist ".agent-os" (
    echo ✅ 현재 프로젝트 Agent OS: 활성화됨
    echo    구조:
    dir /b ".agent-os" 2>nul | findstr /r "^" >nul && (
        for /f "tokens=*" %%d in ('dir /b ".agent-os"') do echo       - %%d
    )
) else (
    echo ℹ️ 현재 프로젝트에 Agent OS가 설정되지 않았습니다
    echo    👉 프로젝트 폴더에서 init-project.bat를 실행하세요
)
echo.

:: 설치 상태 요약
echo ═══════════════════════════════════════════════════════
set /a score=0

if exist "%USERPROFILE%\.agent-os" set /a score+=25
if exist "%USERPROFILE%\.agent-os\standards\tech-stack.md" set /a score+=25
if exist "%USERPROFILE%\.agent-os\instructions\plan-product.md" set /a score+=25
if exist "%USERPROFILE%\.claude" set /a score+=25

echo 설치 완료도: %score%%%

if %score% equ 100 (
    echo 상태: ✅ 완벽하게 설치됨!
) else if %score% geq 75 (
    echo 상태: ⚠️ 대부분 설치됨
) else if %score% geq 50 (
    echo 상태: ⚠️ 부분적으로 설치됨
) else (
    echo 상태: ❌ 설치 필요
)
echo ═══════════════════════════════════════════════════════
echo.
pause
