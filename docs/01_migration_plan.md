# SpineLift 웹 서비스 마이그레이션 계획서

## 개요

SpineLift를 Python 데스크톱 애플리케이션에서 Rails 기반 웹 서비스로 단계적으로 마이그레이션하는 계획서입니다. Railway 배포 환경을 고려하여 MVP는 메시 편집 기능까지 구현하는 것을 목표로 합니다.

## 현재 시스템 분석

### 핵심 기능 구성요소

1. **PSD 파일 처리**
   - `src/core/processors/psd_processor.py`: PSD 파일 파싱 및 레이어 추출
   - psd-tools 라이브러리 사용
   - 레이어별 이미지 추출 및 메타데이터 생성

2. **메시 생성 엔진**
   - `src/core/batch/batch_mesh_processor.py`: spine_mesh_tool 로직 이식
   - Triangle 라이브러리 기반 Delaunay 삼각분할
   - 컨투어 추출, 단순화, UV 매핑

3. **Spine JSON 생성**
   - `src/core/spine_json/spine_json_builder.py`: Spine 3.8.95 호환 JSON 생성
   - 메시 데이터, 스켈레톤, 애니메이션 통합

4. **GUI 시스템**
   - PyQt6 기반 데스크톱 인터페이스
   - 실시간 파라미터 조정 및 프리뷰
   - 레이어 트리, 메시 프리뷰, 파라미터 패널

### 의존성 분석

```
핵심 의존성:
- numpy: 수치 계산 및 배열 처리
- opencv-python: 이미지 처리 및 컨투어 추출
- Pillow: 이미지 포맷 변환
- psd-tools: PSD 파일 파싱
- triangle: 메시 삼각분할
- scikit-image: 고급 이미지 처리
```

## 마이그레이션 전략

### Phase 1: 백엔드 API 구축 (MVP)

#### 1.1 Rails API 설계
```ruby
# API 엔드포인트
POST   /api/v1/projects              # 프로젝트 생성
POST   /api/v1/projects/:id/upload   # PSD 파일 업로드
GET    /api/v1/projects/:id/layers   # 레이어 목록 조회
POST   /api/v1/layers/:id/mesh       # 메시 생성
GET    /api/v1/layers/:id/mesh       # 메시 데이터 조회
PUT    /api/v1/layers/:id/mesh       # 메시 파라미터 수정
DELETE /api/v1/layers/:id/mesh       # 메시 삭제
POST   /api/v1/projects/:id/export   # Spine JSON 익스포트
```

#### 1.2 Python 서비스 래퍼
```ruby
# Python 프로세스를 Rails에서 관리
class PythonMeshService
  def generate_mesh(image_path, params)
    # Python 스크립트 호출
    result = `python3 #{Rails.root}/python/mesh_generator.py #{image_path} #{params.to_json}`
    JSON.parse(result)
  end
end
```

#### 1.3 데이터 모델
```ruby
# app/models/project.rb
class Project < ApplicationRecord
  has_many :layers
  has_one_attached :psd_file
end

# app/models/layer.rb
class Layer < ApplicationRecord
  belongs_to :project
  has_one :mesh
  has_one_attached :image
end

# app/models/mesh.rb
class Mesh < ApplicationRecord
  belongs_to :layer
  # vertices, triangles, uvs 등은 JSON 필드로 저장
end
```

### Phase 2: 프론트엔드 웹 UI

#### 2.1 React/Vue.js 컴포넌트 구조
```
components/
├── ProjectManager/       # 프로젝트 관리
├── PSDUploader/         # PSD 업로드
├── LayerTree/           # 레이어 트리 뷰
├── MeshEditor/          # 메시 편집기 (MVP 핵심)
│   ├── ParameterPanel/  # 파라미터 조정
│   ├── MeshPreview/     # 메시 프리뷰 (WebGL)
│   └── MeshControls/    # 메시 제어 도구
└── ExportManager/       # 익스포트 관리
```

#### 2.2 WebGL 기반 메시 렌더링
```javascript
// Three.js 또는 PixiJS 활용
class MeshRenderer {
  constructor(canvas) {
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera();
    this.renderer = new THREE.WebGLRenderer({ canvas });
  }
  
  renderMesh(meshData) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(meshData.vertices, 2));
    geometry.setIndex(meshData.triangles);
    // UV, 텍스처 적용...
  }
}
```

### Phase 3: Python 서비스 최적화

#### 3.1 마이크로서비스 분리
```python
# mesh_service.py - 독립 실행 가능한 서비스
from flask import Flask, request, jsonify
from batch_mesh_processor import BatchMeshProcessor

app = Flask(__name__)

@app.route('/generate_mesh', methods=['POST'])
def generate_mesh():
    image_data = request.files['image']
    params = request.json['params']
    
    processor = BatchMeshProcessor(params)
    mesh_data = processor.generate_mesh_data(image_data)
    
    return jsonify(mesh_data)
```

#### 3.2 비동기 작업 처리
```ruby
# Sidekiq을 활용한 백그라운드 처리
class MeshGenerationJob < ApplicationJob
  def perform(layer_id)
    layer = Layer.find(layer_id)
    result = PythonMeshService.new.generate_mesh(
      layer.image.path,
      layer.mesh_params
    )
    layer.create_mesh!(result)
  end
end
```

## MVP 구현 로드맵

### Week 1-2: 기본 Rails API
- [ ] Rails 프로젝트 구조 설정
- [ ] 데이터 모델 구현
- [ ] 파일 업로드 시스템
- [ ] Python 서비스 연동

### Week 3-4: 메시 생성 API
- [ ] Python 메시 생성 모듈 분리
- [ ] API 엔드포인트 구현
- [ ] 파라미터 검증 및 처리
- [ ] 에러 핸들링

### Week 5-6: 웹 UI 기본 구조
- [ ] React/Vue.js 프로젝트 설정
- [ ] 파일 업로드 UI
- [ ] 레이어 목록 표시
- [ ] 기본 메시 프리뷰

### Week 7-8: 메시 편집기 MVP
- [ ] WebGL 렌더링 구현
- [ ] 파라미터 조정 UI
- [ ] 실시간 업데이트
- [ ] 익스포트 기능

## 기술적 고려사항

### 1. 파일 처리
- **문제**: 대용량 PSD 파일 처리
- **해결**: 
  - Active Storage + S3/R2 활용
  - 청크 업로드 구현
  - 백그라운드 작업 큐 활용

### 2. 실시간 업데이트
- **문제**: 파라미터 변경 시 실시간 프리뷰
- **해결**:
  - WebSocket (Action Cable) 활용
  - 클라이언트 사이드 캐싱
  - 디바운싱으로 요청 최적화

### 3. Python 통합
- **문제**: Ruby-Python 프로세스 간 통신
- **해결**:
  - HTTP API 방식 (권장)
  - Unix 소켓 통신
  - Redis를 통한 메시지 큐

### 4. Railway 배포
- **고려사항**:
  - Dockerfile 멀티스테이지 빌드
  - Python 의존성 포함
  - 환경 변수 관리
  - 볼륨 마운트 (임시 파일)

## 성능 최적화 전략

### 1. 캐싱
```ruby
class MeshController < ApplicationController
  def show
    @mesh = Rails.cache.fetch("mesh_#{params[:id]}", expires_in: 1.hour) do
      Layer.find(params[:id]).mesh
    end
  end
end
```

### 2. CDN 활용
- 생성된 메시 데이터 CDN 캐싱
- 이미지 리소스 최적화
- WebGL 에셋 압축

### 3. 데이터베이스 최적화
```ruby
# 메시 데이터는 별도 테이블로 분리
class MeshData < ApplicationRecord
  belongs_to :mesh
  # JSON 필드 인덱싱
end
```

## 보안 고려사항

1. **파일 업로드 검증**
   - 파일 타입 검증
   - 파일 크기 제한
   - 바이러스 스캔

2. **API 인증**
   - JWT 토큰 기반 인증
   - Rate limiting
   - CORS 설정

3. **데이터 보호**
   - 사용자별 데이터 격리
   - 암호화된 저장소
   - 정기적인 데이터 정리

## 결론

이 마이그레이션 계획은 SpineLift의 핵심 메시 편집 기능을 웹 서비스로 전환하는 MVP 구현에 초점을 맞추고 있습니다. Python 코어 로직을 유지하면서 Rails API와 현대적인 웹 UI를 통해 접근성을 높이는 것이 목표입니다. Railway 환경에서의 배포를 고려하여 확장 가능하고 유지보수가 용이한 아키텍처를 설계했습니다.