# SpineLift Rails - 즉시 실행 계획

**작성일**: 2025년 1월 9일  
**목표**: 2주 내 MVP 완성  
**현재 상태**: PSD-to-Mesh 기본 기능 작동  

## Week 1: 파라미터 조정 UI 구현

### Day 1-2: 프론트엔드 컴포넌트 개발

#### 작업 1: ParameterPanel 컴포넌트
```typescript
// frontend/src/components/ParameterPanel/index.tsx
interface MeshParameters {
  maxVertices: number;      // 100-5000
  quality: number;          // 0.1-1.0
  simplification: number;   // 0.0-0.5
  boundaryAccuracy: number; // 0.5-1.0
  interiorAccuracy: number; // 0.5-1.0
  smoothing: number;        // 0.0-1.0
  edgeThreshold: number;    // 10-200
}
```

**구현 체크리스트**:
- [ ] 컴포넌트 파일 구조 생성
- [ ] 슬라이더 UI 구현 (react-range)
- [ ] 디바운싱 로직 추가 (300ms)
- [ ] API 연동 테스트

#### 작업 2: 프리셋 시스템
```typescript
const presets = {
  low: { maxVertices: 500, quality: 0.3, ... },
  medium: { maxVertices: 1000, quality: 0.6, ... },
  high: { maxVertices: 2000, quality: 0.9, ... }
};
```

**구현 체크리스트**:
- [ ] 프리셋 데이터 정의
- [ ] 프리셋 선택 UI
- [ ] localStorage 저장/로드

### Day 3-4: 백엔드 API 개선

#### 작업 3: MeshesController 업데이트
```ruby
# app/controllers/api/v1/meshes_controller.rb
def update_parameters
  @mesh = Mesh.find(params[:id])
  
  if @mesh.update(mesh_params)
    RegenerateMeshJob.perform_later(@mesh.id, mesh_params[:parameters])
    render json: MeshSerializer.new(@mesh)
  else
    render_errors(@mesh.errors)
  end
end

private

def mesh_params
  params.permit(parameters: [
    :max_vertices, :quality, :simplification,
    :boundary_accuracy, :interior_accuracy,
    :smoothing, :edge_threshold
  ])
end
```

**구현 체크리스트**:
- [ ] 파라미터 검증 추가
- [ ] 에러 처리 개선
- [ ] WebSocket 브로드캐스트

### Day 5: 통합 테스트

#### 작업 4: End-to-End 테스트
```javascript
// frontend/src/__tests__/ParameterPanel.test.tsx
describe('Parameter Panel Integration', () => {
  it('should update mesh when parameter changes', async () => {
    // 1. 슬라이더 조정
    // 2. API 호출 확인
    // 3. 메시 업데이트 확인
  });
});
```

**테스트 체크리스트**:
- [ ] 컴포넌트 단위 테스트
- [ ] API 통합 테스트
- [ ] WebSocket 연동 테스트

## Week 2: 메시 프리뷰 개선 및 익스포트

### Day 6-7: 메시 프리뷰 개선

#### 작업 5: 뷰포트 조작
```typescript
// frontend/src/components/MeshPreview/viewport.ts
class ViewportController {
  zoom: number = 1;
  pan: { x: number, y: number } = { x: 0, y: 0 };
  
  handleWheel(e: WheelEvent) {
    this.zoom *= e.deltaY > 0 ? 0.9 : 1.1;
  }
  
  handleDrag(e: MouseEvent) {
    this.pan.x += e.movementX;
    this.pan.y += e.movementY;
  }
}
```

**구현 체크리스트**:
- [ ] 마우스 휠 줌
- [ ] 드래그 팬
- [ ] 더블클릭 리셋

#### 작업 6: 메시 통계 표시
```typescript
interface MeshStats {
  vertexCount: number;
  triangleCount: number;
  qualityScore: number;
  fileSize: number;
}
```

**구현 체크리스트**:
- [ ] 통계 오버레이 UI
- [ ] 실시간 업데이트
- [ ] 성능 경고 표시

### Day 8-9: 익스포트 기능

#### 작업 7: JSON 익스포트
```ruby
# app/services/mesh_export_service.rb
class MeshExportService
  def initialize(project)
    @project = project
  end
  
  def export_as_json
    {
      version: "1.0",
      project: @project.name,
      layers: @project.layers.map do |layer|
        {
          name: layer.name,
          mesh: layer.mesh&.as_json(only: [:vertices, :triangles]),
          texture: rails_blob_url(layer.image)
        }
      end
    }
  end
  
  def export_as_zip
    # JSON + 텍스처 이미지 ZIP 생성
  end
end
```

**구현 체크리스트**:
- [ ] JSON 생성 로직
- [ ] ZIP 패키징
- [ ] 다운로드 엔드포인트

#### 작업 8: 다운로드 UI
```typescript
// frontend/src/components/ExportButton.tsx
const ExportButton = ({ projectId }) => {
  const handleExport = async () => {
    const response = await apiClient.get(
      `/projects/${projectId}/export`,
      { responseType: 'blob' }
    );
    downloadFile(response.data, `${projectName}.zip`);
  };
  
  return <button onClick={handleExport}>Export Project</button>;
};
```

**구현 체크리스트**:
- [ ] 다운로드 버튼 UI
- [ ] 진행 상황 표시
- [ ] 에러 처리

### Day 10: 최종 테스트 및 문서화

#### 작업 9: 통합 테스트
- [ ] 전체 워크플로우 테스트
- [ ] 성능 측정
- [ ] 버그 수정

#### 작업 10: 문서 작성
- [ ] README.md 업데이트
- [ ] API 문서 생성
- [ ] 사용자 가이드

## 일일 체크리스트

### 매일 수행할 작업
- [ ] Git 커밋 (기능별)
- [ ] 진행 상황 기록
- [ ] 블로커 식별 및 해결
- [ ] 코드 리뷰 (가능한 경우)

### 주요 마일스톤
- **Day 5**: 파라미터 UI 완성 ✓
- **Day 7**: 프리뷰 개선 완성 ✓
- **Day 9**: 익스포트 기능 완성 ✓
- **Day 10**: MVP 완성 ✓

## 필요한 라이브러리 설치

### 프론트엔드
```bash
npm install react-range lodash jszip file-saver
npm install --save-dev @testing-library/react jest
```

### 백엔드
```bash
# Gemfile에 추가
gem 'rubyzip', '~> 2.3'
gem 'rspec-rails', group: [:development, :test]
gem 'factory_bot_rails', group: [:development, :test]
```

## 위험 요소 및 대응

### 위험 1: 실시간 업데이트 지연
- **문제**: 디바운싱과 메시 생성 시간
- **해결**: 캐싱 전략, 낙관적 업데이트

### 위험 2: 대용량 메시 성능
- **문제**: Canvas 렌더링 한계
- **해결**: LOD 시스템, 점진적 렌더링

### 위험 3: 브라우저 호환성
- **문제**: Canvas API 차이
- **해결**: Polyfill, 기능 감지

## 성공 기준

### 기능적 성공 기준
- [x] 7개 파라미터 실시간 조정 가능
- [x] 메시 프리뷰 60fps 유지
- [x] JSON/ZIP 익스포트 작동
- [x] 에러율 < 1%

### 기술적 성공 기준
- [x] 테스트 커버리지 > 50%
- [x] API 응답 시간 < 500ms
- [x] 메모리 사용량 < 200MB
- [x] 코드 품질 (ESLint, RuboCop)

## 다음 단계 (MVP 이후)

### Phase 2 준비 (Week 3-4)
1. WebGL 라이브러리 선택 (PIXI.js vs Three.js)
2. 본 시스템 데이터 모델 설계
3. 사용자 피드백 수집
4. 성능 프로파일링

### 장기 목표 확인
- Month 2: WebGL 메시 에디터
- Month 3-4: 본 시스템
- Month 5: Spine 익스포트
- Month 6: 애니메이션 기초

## 일일 스탠드업 템플릿

```markdown
### [날짜] 진행 상황

**어제 완료한 작업:**
- 

**오늘 할 작업:**
- 

**블로커:**
- 

**도움 필요:**
- 
```

## 결론

이 2주 계획을 따르면 SpineLift Rails는 **실제로 사용 가능한 PSD-to-Mesh 변환 도구**가 됩니다. 

**핵심 deliverables**:
1. ✅ 파라미터 조정 UI
2. ✅ 개선된 메시 프리뷰
3. ✅ 기본 익스포트 기능
4. ✅ 기본 테스트 및 문서

**Not included** (향후 구현):
- ❌ WebGL 렌더링
- ❌ 버텍스 직접 편집
- ❌ 본 시스템
- ❌ 애니메이션