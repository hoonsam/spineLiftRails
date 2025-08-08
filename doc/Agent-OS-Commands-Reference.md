# Agent OS 명령어 참조 가이드 📋

## 기본 명령어 (4개)

### 1. @plan-product
**용도**: 새 프로젝트 계획 수립
**사용 시점**: 프로젝트 시작 시

```
@plan-product

SaaS 도구를 만들고 싶습니다.
주요 기능:
- 사용자 관리
- 대시보드
- 결제 시스템
타겟: B2B 기업
기술 스택: 제 기본 설정 사용
```

**생성되는 것**:
- `.agent-os/product/overview.md`
- `.agent-os/product/roadmap.md`
- `.agent-os/product/user-stories.md`
- `.agent-os/product/tech-architecture.md`

---

### 2. @create-spec
**용도**: 기능 상세 명세 작성
**사용 시점**: 새 기능 개발 전

```
@create-spec

사용자 인증 시스템을 만들어주세요.
요구사항:
- 이메일/비밀번호 로그인
- OAuth (Google, GitHub)
- JWT 토큰
- 비밀번호 재설정
```

**생성되는 것**:
- `.agent-os/specs/2025-01-15-user-auth/requirements.md`
- `.agent-os/specs/2025-01-15-user-auth/technical.md`
- `.agent-os/specs/2025-01-15-user-auth/tasks.md`

---

### 3. @execute-task
**용도**: 코드 생성 및 작업 실행
**사용 시점**: 명세 작성 후

```
@execute-task

사용자 인증 프로젝트의 다음 작업을 진행해주세요
```

**변형 사용법**:
```
# 특정 작업 실행
@execute-task
작업 1.2와 1.3을 완료해주세요

# 여러 작업 실행
@execute-task
작업 1과 2를 모든 하위 작업과 함께 완료해주세요

# 이어서 작업
@execute-task
어제 중단한 곳부터 계속 진행해주세요
```

---

### 4. @analyze-product
**용도**: 기존 코드베이스 분석
**사용 시점**: 기존 프로젝트에 Agent OS 도입

```
@analyze-product

기존 React 프로젝트에 Agent OS를 적용하고 싶습니다.
현재 코드를 분석하고 문서를 생성해주세요.
```

**분석하는 것**:
- 파일 구조
- 사용된 기술 스택
- 주요 컴포넌트
- API 엔드포인트
- 데이터베이스 스키마

---

## 고급 사용 패턴

### 🔄 자동 흐름
```
# 1. 다음 기능 자동 선택
@create-spec
로드맵에서 다음 미완료 기능을 진행해주세요

# 2. 자동으로 작업 계속
@execute-task
완료되지 않은 작업을 계속 진행해주세요
```

### 🐛 버그 수정
```
@create-spec
버그: 로그인 후 세션이 10분 후에 만료됩니다.
24시간 유지되도록 수정해주세요.
```

### 🔧 리팩토링
```
@create-spec
user-service.js를 TypeScript로 마이그레이션해주세요.
인터페이스 정의와 타입 안정성을 추가해주세요.
```

### 📊 기능 개선
```
@create-spec
대시보드 로딩 속도를 개선해주세요.
- 레이지 로딩 적용
- 데이터 캐싱
- 페이지네이션 추가
```

---

## 명령어 조합 예시

### 전체 프로젝트 플로우
```
1️⃣ @plan-product
   → 프로젝트 계획 수립

2️⃣ @create-spec
   → 첫 번째 기능 명세

3️⃣ @execute-task
   → 코드 생성

4️⃣ @create-spec
   → 다음 기능으로 이동

5️⃣ @execute-task
   → 반복...
```

### 빠른 프로토타입
```
@plan-product
간단한 TODO 앱 MVP를 만들어주세요

@create-spec
CRUD 기능만 구현해주세요

@execute-task
모든 작업을 한번에 완료해주세요
```

### 점진적 개발
```
@plan-product
복잡한 ERP 시스템

@create-spec
Phase 1의 첫 번째 기능만 진행

@execute-task
작업 1.1만 완료 (데이터베이스 설계)

# 검토 후...
@execute-task
작업 1.2 진행 (API 개발)
```

---

## 명령어 옵션과 플래그

### @create-spec 옵션
```
# 긴급 수정
@create-spec [URGENT]
프로덕션 버그 수정이 필요합니다

# 성능 중심
@create-spec [PERFORMANCE]
페이지 로드 시간을 50% 단축해주세요

# 보안 중심
@create-spec [SECURITY]
XSS 취약점을 수정해주세요
```

### @execute-task 옵션
```
# 테스트 포함
@execute-task
다음 작업을 진행하고 단위 테스트도 작성해주세요

# 문서화 포함
@execute-task
코드 생성 시 JSDoc 주석을 상세히 추가해주세요

# 리뷰 모드
@execute-task
코드를 생성하기 전에 접근 방법을 먼저 설명해주세요
```

---

## 실제 사용 시나리오

### 시나리오 1: 스타트업 MVP
```
Day 1:
@plan-product
온라인 교육 플랫폼 MVP
- 강의 업로드
- 수강생 관리
- 결제

Day 2:
@create-spec
강의 업로드 기능

@execute-task
백엔드 API 먼저 구현

Day 3:
@execute-task
프론트엔드 UI 구현

Day 4:
@create-spec
결제 시스템 통합
```

### 시나리오 2: 레거시 마이그레이션
```
Week 1:
@analyze-product
jQuery 프로젝트를 분석해주세요

@plan-product
React로 단계적 마이그레이션 계획

Week 2:
@create-spec
컴포넌트 단위로 마이그레이션 시작

@execute-task
헤더 컴포넌트부터 변환
```

### 시나리오 3: 기능 추가
```
@analyze-product
현재 프로젝트 상태 파악

@create-spec
다크 모드 지원 추가

@execute-task
CSS 변수 시스템 구축

@execute-task
토글 스위치 구현

@execute-task
사용자 설정 저장
```

---

## 문제 해결 팁

### ❓ AI가 컨텍스트를 잃어버렸을 때
```
@analyze-product
현재 프로젝트 상태를 다시 분석해주세요
```

### ❓ 작업이 너무 크게 분해되었을 때
```
@create-spec
이전 명세를 수정해주세요.
작업을 더 작은 단위로 분해해주세요.
```

### ❓ 잘못된 기술 스택을 사용할 때
```
@execute-task
중단! tech-stack.md를 확인하고
올바른 기술 스택으로 다시 구현해주세요.
```

### ❓ 코드 스타일이 맞지 않을 때
```
@execute-task
code-style.md 가이드라인에 맞춰
코드를 리팩토링해주세요.
```

---

## 효율적인 사용을 위한 팁

### 1. 명확한 요구사항
```
# 좋은 예 ✅
@create-spec
사용자 프로필 페이지
- 프로필 사진 업로드 (최대 5MB, JPG/PNG)
- 닉네임 변경 (중복 체크)
- 자기소개 (최대 500자)
- 이메일 알림 설정

# 나쁜 예 ❌
@create-spec
프로필 페이지 만들어주세요
```

### 2. 단계적 실행
```
# 한번에 모든 것 ❌
@execute-task
모든 작업을 완료해주세요

# 단계별로 검증 ✅
@execute-task
데이터베이스 스키마만 먼저 생성

# 검토 후...
@execute-task
API 엔드포인트 구현

# 테스트 후...
@execute-task
프론트엔드 연동
```

### 3. 컨텍스트 유지
```
# 작업 전 상태 확인
@execute-task
현재 tasks.md 파일을 보여주고
완료된 작업을 표시해주세요

# 이어서 작업
@execute-task
표시된 다음 작업부터 진행해주세요
```

---

## Standards 파일 활용

### tech-stack.md 참조
```
@execute-task
tech-stack.md에 정의된 
Prisma ORM을 사용해서 
User 모델을 생성해주세요
```

### code-style.md 적용
```
@execute-task
code-style.md의 네이밍 규칙을 따라
모든 컴포넌트를 PascalCase로 수정해주세요
```

### best-practices.md 준수
```
@create-spec
best-practices.md의 보안 섹션을 참고해서
인증 시스템을 설계해주세요
```

---

## 팀 협업 활용

### 작업 분배
```
@create-spec
프론트엔드 팀을 위한 UI 작업과
백엔드 팀을 위한 API 작업을
별도로 분리해주세요
```

### 코드 리뷰 준비
```
@execute-task
PR 설명을 위한 변경사항 요약과
테스트 방법을 문서화해주세요
```

### 문서화
```
@execute-task
생성된 코드에 대한
API 문서와 사용 가이드를 작성해주세요
```

---

## 자주 사용하는 템플릿

### CRUD 기능
```
@create-spec
[모델명] CRUD API를 만들어주세요.
- Create: POST /api/[모델명]
- Read: GET /api/[모델명]/:id
- Update: PUT /api/[모델명]/:id
- Delete: DELETE /api/[모델명]/:id
- List: GET /api/[모델명] (페이지네이션 포함)
```

### 인증 시스템
```
@create-spec
JWT 기반 인증 시스템
- 회원가입 (이메일 중복 체크)
- 로그인 (비밀번호 해싱)
- 토큰 갱신
- 로그아웃
- 비밀번호 재설정
```

### 파일 업로드
```
@create-spec
파일 업로드 시스템
- 다중 파일 업로드
- 파일 타입 검증
- 크기 제한 (10MB)
- S3 저장
- 썸네일 생성
```

---

## 체크리스트

### 프로젝트 시작 전
- [ ] Agent OS 설치 완료
- [ ] Standards 파일 커스터마이징
- [ ] AI 도구 설정 완료
- [ ] 프로젝트 폴더 생성

### 기능 개발 전
- [ ] @create-spec 실행
- [ ] 생성된 명세 검토
- [ ] 작업 분해 확인
- [ ] 우선순위 설정

### 코드 생성 후
- [ ] 생성된 코드 검토
- [ ] 테스트 실행
- [ ] 코드 스타일 확인
- [ ] 문서 업데이트

### 기능 완료 후
- [ ] roadmap.md 업데이트
- [ ] decisions.md 기록
- [ ] 새로운 패턴 문서화
- [ ] 다음 기능 준비

---

*이 가이드는 Agent OS를 효과적으로 사용하기 위한 참조 문서입니다.*
*지속적으로 업데이트하며 사용하세요.*
