@echo off
echo Installing Agent OS for SpineLift Project...
echo.

REM Create global Agent OS folders
echo Creating global Agent OS folders...
mkdir "%USERPROFILE%\.agent-os\standards" 2>nul
mkdir "%USERPROFILE%\.agent-os\instructions" 2>nul

REM Create standard files
echo Creating standard files...
(
echo # Tech Stack for SpineLift
echo ## Language
echo - Python 3.9+
echo.
echo ## GUI Framework  
echo - PyQt6
echo.
echo ## Image Processing
echo - OpenCV
echo - psd-tools
echo.
echo ## Mesh Generation
echo - Triangle library
echo - NumPy
echo.
echo ## Testing
echo - pytest
echo - pytest-qt
) > "%USERPROFILE%\.agent-os\standards\tech-stack.md"

(
echo # Code Style Guide
echo ## Python
echo - PEP 8 compliance
echo - Type hints for all functions
echo - Docstrings for public methods
echo.
echo ## File Organization
echo - src/core/ - Core business logic
echo - src/gui/ - UI components
echo - tests/ - Test files
echo.
echo ## Naming Conventions
echo - Classes: PascalCase
echo - Functions: snake_case
echo - Constants: UPPER_SNAKE_CASE
) > "%USERPROFILE%\.agent-os\standards\code-style.md"

(
echo # Best Practices
echo ## Error Handling
echo - Use specific exceptions
echo - Log errors appropriately
echo - Provide user-friendly messages
echo.
echo ## Memory Management
echo - Cleanup signals in PyQt6
echo - Clear large image data
echo - Use weak references for event handlers
echo.
echo ## Testing
echo - Write tests before implementation (TDD)
echo - Minimum 80%% coverage
echo - Test edge cases
) > "%USERPROFILE%\.agent-os\standards\best-practices.md"

REM Create instruction files (Agent OS commands)
echo Creating instruction files...
(
echo # Plan Product
echo You are planning a new product or project feature.
echo.
echo 1. Create product overview document
echo 2. Define roadmap and milestones
echo 3. List user stories
echo 4. Outline technical architecture
echo.
echo Save all documents in .agent-os/product/
) > "%USERPROFILE%\.agent-os\instructions\plan-product.md"

(
echo # Create Spec
echo You are creating a detailed specification for a feature.
echo.
echo 1. Write requirements document
echo 2. Create technical specification
echo 3. Break down into tasks
echo 4. Define test criteria
echo.
echo Save in .agent-os/specs/[date]-[feature-name]/
) > "%USERPROFILE%\.agent-os\instructions\create-spec.md"

(
echo # Execute Task
echo You are executing tasks from the specification.
echo.
echo 1. Read the current task list
echo 2. Implement the next pending task
echo 3. Follow the technical specification
echo 4. Write tests for the implementation
echo 5. Update task status
) > "%USERPROFILE%\.agent-os\instructions\execute-task.md"

(
echo # Analyze Product
echo You are analyzing an existing codebase.
echo.
echo 1. Scan project structure
echo 2. Identify tech stack
echo 3. Document main components
echo 4. Create product overview
echo 5. Generate initial roadmap
) > "%USERPROFILE%\.agent-os\instructions\analyze-product.md"

REM Setup for Claude Code
if exist "%USERPROFILE%\.claude" (
    echo Setting up Claude Code commands...
    mkdir "%USERPROFILE%\.claude\commands" 2>nul
    copy "%USERPROFILE%\.agent-os\instructions\*.md" "%USERPROFILE%\.claude\commands\" >nul
    echo Claude Code setup complete!
)

REM Project-specific setup already done
echo.
echo ✅ Agent OS installed successfully!
echo.
echo 📁 Global files created at: %USERPROFILE%\.agent-os\
echo 📁 Project files at: %CD%\.agent-os\
echo.
echo 🚀 Next steps:
echo 1. Restart Claude Code
echo 2. Use @plan-product to plan features
echo 3. Use @create-spec to create specifications
echo 4. Use @execute-task to implement code
echo.
pause