# 메시 생성 파라미터 조정 UI 명세서

## 개요

현재 SpineLift Rails에서는 메시 생성 파라미터가 하드코딩되어 있어 사용자가 실시간으로 조정할 수 없습니다. 이 명세서는 직관적인 파라미터 조정 UI와 실시간 메시 프리뷰 업데이트 기능을 정의합니다.

**담당 영역**: 프론트엔드 UI/UX, 백엔드 API  
**우선순위**: High  
**예상 구현 시간**: 2-3주  

## 현재 상태 분석

### 기존 파라미터 (Python Service)
```python
# mesh_service.py에서 하드코딩된 파라미터
parameters = {
    "detail_factor": 0.01,          # 메시 디테일 수준
    "alpha_threshold": 10,          # 투명도 임계값
    "concave_factor": 0.0,          # 오목한 부분 처리
    "internal_vertex_density": 0,   # 내부 버텍스 밀도
    "blur_kernel_size": 1,          # 블러 커널 크기
    "binary_threshold": 128,        # 이진화 임계값
    "min_contour_area": 10          # 최소 컨투어 면적
}
```

### 현재 제약사항
- 파라미터가 `MeshGenerationService.default_parameters`에 고정
- 사용자가 실시간으로 조정 불가
- 파라미터 변경 시 전체 메시를 재생성해야 함
- 파라미터 프리셋 저장/로드 기능 없음

## 기능 요구사항

### 1. 파라미터 조정 패널

#### 1.1 기본 파라미터
```typescript
interface MeshParameters {
  detail_factor: number;           // 0.001 - 0.05, 기본값: 0.01
  alpha_threshold: number;         // 0 - 255, 기본값: 10
  concave_factor: number;          // 0.0 - 1.0, 기본값: 0.0
  internal_vertex_density: number; // 0 - 100, 기본값: 0
  blur_kernel_size: number;        // 1 - 10, 기본값: 1
  binary_threshold: number;        // 0 - 255, 기본값: 128
  min_contour_area: number;        // 1 - 1000, 기본값: 10
}
```

#### 1.2 고급 파라미터
```typescript
interface AdvancedMeshParameters {
  edge_threshold: number;          // 1 - 50, 기본값: 5
  smoothing_iterations: number;    // 0 - 10, 기본값: 2
  optimization_level: number;      // 1 - 3, 기본값: 2
  texture_padding: number;         // 0 - 32, 기본값: 2
  uv_unwrap_method: 'angle' | 'conformal' | 'area'; // 기본값: 'angle'
}
```

### 2. UI 컴포넌트 설계

#### 2.1 ParameterPanel 컴포넌트
```typescript
interface ParameterPanelProps {
  layerId: string;
  initialParameters: MeshParameters;
  onParameterChange: (parameter: keyof MeshParameters, value: number) => void;
  onPresetLoad: (preset: MeshParameterPreset) => void;
  onPresetSave: (name: string, parameters: MeshParameters) => void;
  isProcessing: boolean;
}

export const ParameterPanel: React.FC<ParameterPanelProps> = ({
  layerId,
  initialParameters,
  onParameterChange,
  onPresetLoad,
  onPresetSave,
  isProcessing
}) => {
  // 구현 내용
};
```

#### 2.2 ParameterSlider 컴포넌트
```typescript
interface ParameterSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  description?: string;
  onChange: (value: number) => void;
  disabled?: boolean;
}

export const ParameterSlider: React.FC<ParameterSliderProps> = ({
  label,
  value,
  min,
  max,
  step,
  unit = '',
  description,
  onChange,
  disabled = false
}) => {
  // 슬라이더 UI 구현
};
```

### 3. 실시간 업데이트 시스템

#### 3.1 디바운싱 전략
```typescript
// 파라미터 변경 시 과도한 API 요청 방지
const useDebouncedMeshUpdate = (
  layerId: string,
  parameters: MeshParameters,
  delay: number = 300
) => {
  const debouncedUpdate = useMemo(
    () => debounce(async (params: MeshParameters) => {
      try {
        await meshApi.updateParameters(layerId, params);
      } catch (error) {
        console.error('Failed to update mesh parameters:', error);
      }
    }, delay),
    [layerId, delay]
  );

  useEffect(() => {
    debouncedUpdate(parameters);
  }, [parameters, debouncedUpdate]);
};
```

#### 3.2 WebSocket 실시간 업데이트
```typescript
// ActionCable을 통한 실시간 메시 업데이트 수신
const useMeshUpdates = (layerId: string) => {
  const [mesh, setMesh] = useState<Mesh | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    const subscription = createConsumer().subscriptions.create(
      { channel: 'MeshChannel', layer_id: layerId },
      {
        received: (data: { status: string; mesh?: Mesh; progress?: number }) => {
          if (data.status === 'updating') {
            setIsUpdating(true);
          } else if (data.status === 'completed' && data.mesh) {
            setMesh(data.mesh);
            setIsUpdating(false);
          }
        }
      }
    );

    return () => subscription?.unsubscribe();
  }, [layerId]);

  return { mesh, isUpdating };
};
```

### 4. 프리셋 시스템

#### 4.1 프리셋 데이터 구조
```typescript
interface MeshParameterPreset {
  id: string;
  name: string;
  description: string;
  parameters: MeshParameters;
  tags: string[];
  created_at: string;
  is_system: boolean; // 시스템 기본 프리셋 여부
}

// 기본 시스템 프리셋
const SYSTEM_PRESETS: MeshParameterPreset[] = [
  {
    id: 'high-detail',
    name: '고품질 메시',
    description: '많은 버텍스로 세밀한 메시 생성',
    parameters: {
      detail_factor: 0.005,
      alpha_threshold: 5,
      concave_factor: 0.3,
      internal_vertex_density: 50,
      // ...
    },
    tags: ['high-quality', 'detailed'],
    created_at: '2025-01-09',
    is_system: true
  },
  {
    id: 'low-poly',
    name: '최적화 메시',
    description: '적은 버텍스로 최적화된 메시',
    parameters: {
      detail_factor: 0.02,
      alpha_threshold: 20,
      concave_factor: 0.0,
      internal_vertex_density: 0,
      // ...
    },
    tags: ['optimized', 'mobile'],
    created_at: '2025-01-09',
    is_system: true
  }
];
```

#### 4.2 프리셋 관리 UI
```typescript
const PresetManager: React.FC<{
  onPresetSelect: (preset: MeshParameterPreset) => void;
  onPresetSave: (name: string, description: string) => void;
}> = ({ onPresetSelect, onPresetSave }) => {
  const [presets, setPresets] = useState<MeshParameterPreset[]>([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  return (
    <div className="preset-manager">
      <div className="preset-list">
        {presets.map(preset => (
          <div key={preset.id} className="preset-item">
            <h4>{preset.name}</h4>
            <p>{preset.description}</p>
            <div className="preset-tags">
              {preset.tags.map(tag => (
                <span key={tag} className="tag">{tag}</span>
              ))}
            </div>
            <button onClick={() => onPresetSelect(preset)}>
              적용
            </button>
          </div>
        ))}
      </div>
      
      <button onClick={() => setShowSaveDialog(true)}>
        현재 설정 저장
      </button>
      
      {showSaveDialog && (
        <PresetSaveDialog
          onSave={onPresetSave}
          onCancel={() => setShowSaveDialog(false)}
        />
      )}
    </div>
  );
};
```

## 백엔드 API 설계

### 1. 새로운 엔드포인트

#### 1.1 파라미터 업데이트 API
```ruby
# app/controllers/api/v1/mesh_controller.rb
class Api::V1::MeshController < Api::V1::BaseController
  def update_parameters
    layer = Layer.find(params[:layer_id])
    parameters = mesh_parameters_params
    
    # 백그라운드에서 메시 재생성
    RegenerateMeshJob.perform_later(layer.id, parameters)
    
    render json: { 
      status: 'processing',
      message: 'Mesh regeneration started' 
    }
  end
  
  private
  
  def mesh_parameters_params
    params.require(:parameters).permit(
      :detail_factor,
      :alpha_threshold,
      :concave_factor,
      :internal_vertex_density,
      :blur_kernel_size,
      :binary_threshold,
      :min_contour_area,
      :edge_threshold,
      :smoothing_iterations,
      :optimization_level,
      :texture_padding,
      :uv_unwrap_method
    )
  end
end
```

#### 1.2 프리셋 관리 API
```ruby
# app/controllers/api/v1/mesh_presets_controller.rb
class Api::V1::MeshPresetsController < Api::V1::BaseController
  def index
    system_presets = MeshParameterPreset.system_presets
    user_presets = current_user.mesh_parameter_presets
    
    render json: {
      system: MeshPresetSerializer.new(system_presets),
      user: MeshPresetSerializer.new(user_presets)
    }
  end
  
  def create
    preset = current_user.mesh_parameter_presets.build(preset_params)
    
    if preset.save
      render json: MeshPresetSerializer.new(preset), status: :created
    else
      render json: { errors: preset.errors }, status: :unprocessable_entity
    end
  end
  
  private
  
  def preset_params
    params.require(:preset).permit(:name, :description, parameters: {}, tags: [])
  end
end
```

### 2. 데이터베이스 스키마

#### 2.1 mesh_parameter_presets 테이블
```ruby
# db/migrate/create_mesh_parameter_presets.rb
class CreateMeshParameterPresets < ActiveRecord::Migration[7.0]
  def change
    create_table :mesh_parameter_presets do |t|
      t.references :user, null: false, foreign_key: true
      t.string :name, null: false
      t.text :description
      t.jsonb :parameters, null: false
      t.jsonb :tags, default: []
      t.boolean :is_system, default: false
      
      t.timestamps
    end
    
    add_index :mesh_parameter_presets, :parameters, using: :gin
    add_index :mesh_parameter_presets, :tags, using: :gin
    add_index :mesh_parameter_presets, [:user_id, :name], unique: true
  end
end
```

#### 2.2 Mesh 모델 확장
```ruby
# app/models/mesh.rb
class Mesh < ApplicationRecord
  belongs_to :layer
  
  validates :data, presence: true
  validates :parameters, presence: true
  
  # 파라미터 기본값
  def self.default_parameters
    {
      'detail_factor' => 0.01,
      'alpha_threshold' => 10,
      'concave_factor' => 0.0,
      'internal_vertex_density' => 0,
      'blur_kernel_size' => 1,
      'binary_threshold' => 128,
      'min_contour_area' => 10,
      'edge_threshold' => 5,
      'smoothing_iterations' => 2,
      'optimization_level' => 2,
      'texture_padding' => 2,
      'uv_unwrap_method' => 'angle'
    }
  end
  
  # 파라미터 검증
  def validate_parameters
    errors.add(:parameters, 'Invalid detail_factor') unless (0.001..0.05).include?(parameters['detail_factor'])
    errors.add(:parameters, 'Invalid alpha_threshold') unless (0..255).include?(parameters['alpha_threshold'])
    # ... 다른 파라미터 검증
  end
end
```

## UI/UX 가이드라인

### 1. 레이아웃 설계
```
┌─────────────────────────────────────────────────────────────────┐
│                        메시 에디터                               │
├─────────────────────────────┬───────────────────────────────────┤
│                             │                                   │
│        메시 프리뷰           │         파라미터 패널              │
│      (실시간 업데이트)       │                                   │
│                             │  ┌─ 기본 파라미터 ─────────────┐   │
│                             │  │ • 디테일 수준    [슬라이더] │   │
│                             │  │ • 투명도 임계값  [슬라이더] │   │
│                             │  │ • 오목 처리      [슬라이더] │   │
│                             │  └─────────────────────────────┘   │
│                             │                                   │
│                             │  ┌─ 고급 파라미터 ─────────────┐   │
│                             │  │ • 최적화 수준    [드롭다운] │   │
│                             │  │ • UV 방법       [드롭다운] │   │
│                             │  └─────────────────────────────┘   │
│                             │                                   │
│                             │  ┌─ 프리셋 ────────────────────┐   │
│                             │  │ [고품질] [최적화] [사용자정의] │   │
│                             │  │ [저장] [불러오기]           │   │
│                             │  └─────────────────────────────┘   │
└─────────────────────────────┴───────────────────────────────────┘
```

### 2. 시각적 피드백
- **진행 중**: 로딩 인디케이터, 흐린 프리뷰
- **완료**: 선명한 프리뷰, 성공 알림
- **오류**: 에러 메시지, 이전 상태 복원 옵션

### 3. 접근성 고려사항
- 키보드 네비게이션 지원
- 스크린 리더 호환성
- 색상 대비 준수
- 툴팁을 통한 파라미터 설명

## 성능 고려사항

### 1. 최적화 전략
- **디바운싱**: 300ms 지연으로 과도한 요청 방지
- **캐싱**: 이전 파라미터 조합 결과 캐시
- **점진적 로딩**: 낮은 품질로 먼저 표시, 고품질로 업데이트

### 2. 메모리 관리
```typescript
// 메시 데이터 메모리 정리
useEffect(() => {
  return () => {
    // 컴포넌트 언마운트 시 WebGL 리소스 정리
    if (meshRenderer.current) {
      meshRenderer.current.dispose();
    }
  };
}, []);
```

## 테스트 전략

### 1. 단위 테스트
```typescript
// ParameterSlider 컴포넌트 테스트
describe('ParameterSlider', () => {
  it('should call onChange when slider value changes', () => {
    const mockOnChange = jest.fn();
    const { getByRole } = render(
      <ParameterSlider
        label="Detail Factor"
        value={0.01}
        min={0.001}
        max={0.05}
        step={0.001}
        onChange={mockOnChange}
      />
    );
    
    const slider = getByRole('slider');
    fireEvent.change(slider, { target: { value: '0.02' } });
    
    expect(mockOnChange).toHaveBeenCalledWith(0.02);
  });
});
```

### 2. 통합 테스트
```ruby
# Rails API 테스트
RSpec.describe 'Mesh Parameters API', type: :request do
  let(:user) { create(:user) }
  let(:layer) { create(:layer, project: create(:project, user: user)) }
  
  describe 'PATCH /api/v1/layers/:id/mesh/parameters' do
    it 'updates mesh parameters and triggers regeneration' do
      patch "/api/v1/layers/#{layer.id}/mesh/parameters",
            params: { parameters: { detail_factor: 0.02 } },
            headers: auth_headers(user)
      
      expect(response).to have_http_status(:ok)
      expect(RegenerateMeshJob).to have_been_enqueued
    end
  end
end
```

## 구현 로드맵

### Week 1: 기본 UI 구현
- [x] ParameterSlider 컴포넌트
- [x] ParameterPanel 컴포넌트
- [x] 기본 파라미터 7개 슬라이더

### Week 2: 실시간 업데이트
- [x] 디바운싱 구현
- [x] WebSocket 연결
- [x] 백엔드 API 업데이트

### Week 3: 프리셋 시스템
- [x] 프리셋 모델 및 API
- [x] 프리셋 UI 구현
- [x] 시스템 기본 프리셋

### Week 4: 고급 기능 및 최적화
- [ ] 고급 파라미터 추가
- [ ] 성능 최적화
- [ ] 테스트 및 디버깅

## 성공 지표

1. **기능성**: 모든 파라미터 실시간 조정 가능
2. **성능**: 파라미터 변경 후 3초 이내 프리뷰 업데이트
3. **사용성**: 직관적인 UI, 툴팁 제공
4. **안정성**: 오류 처리 및 복구 기능