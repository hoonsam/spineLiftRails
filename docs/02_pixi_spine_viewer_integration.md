# SpineLift - 기존 Spine Viewer 활용 가이드

## 개요

spine_manager_rails 프로젝트에 이미 구현된 PIXI.js Spine 뷰어를 SpineLift 프로젝트에 활용하는 방법을 설명합니다.

## 기존 구현 분석

### 핵심 컴포넌트

1. **SpineLoader** (`spine_loader.js`)
   - PIXI.js 앱 초기화
   - Spine 파일 로딩 (.skel, .atlas, .png)
   - 애니메이션 재생/제어

2. **SpineViewerManager** (`spine_viewer_manager.js`)
   - 여러 Spine 뷰어 인스턴스 관리
   - UI 이벤트 처리

3. **SpineProxyController**
   - Spine 파일 서빙 (로컬/Google Drive)
   - 캐싱 및 스트리밍

## SpineLift 통합 전략

### 1. 코드 재사용

#### JavaScript 모듈 복사
```bash
# SpineLoader 관련 파일 복사
cp -r /home/hoons/spine_manager_rails/app/javascript/spine/* \
      /home/hoons/spineLiftRails/app/javascript/spine/

# ViewComponent 복사 (필요시)
cp -r /home/hoons/spine_manager_rails/app/components/spine/* \
      /home/hoons/spineLiftRails/app/components/spine/
```

#### Spine 런타임 복사
```bash
# Spine 3.8 번들 파일
cp /home/hoons/spine_manager_rails/public/spine-3.8-bundle.js \
   /home/hoons/spineLiftRails/public/
```

### 2. SpineLift 맞춤 수정

#### 메시 프리뷰 통합
```javascript
// app/javascript/spine/mesh_preview_loader.js
import { SpineLoader } from './spine_loader';

export class MeshPreviewLoader extends SpineLoader {
  constructor() {
    super();
    this.meshData = null;
    this.showWireframe = false;
  }
  
  // SpineLift의 메시 데이터를 Spine 형식으로 변환
  loadMeshPreview(containerId, meshData, textureUrl) {
    this.initPixiApp(containerId);
    
    // 메시 데이터를 PIXI Mesh로 변환
    const geometry = new PIXI.Geometry()
      .addAttribute('aVertexPosition', meshData.vertices, 2)
      .addAttribute('aUvs', meshData.uvs, 2)
      .addIndex(meshData.triangles);
    
    const texture = PIXI.Texture.from(textureUrl);
    const mesh = new PIXI.Mesh(geometry, new PIXI.MeshMaterial(texture));
    
    this.app.stage.addChild(mesh);
    
    // 와이어프레임 옵션
    if (this.showWireframe) {
      this.drawWireframe(meshData);
    }
  }
  
  // 실시간 메시 업데이트
  updateMesh(meshData) {
    // 기존 메시 제거
    this.app.stage.removeChildren();
    
    // 새 메시 로드
    this.loadMeshPreview(this.containerId, meshData, this.textureUrl);
  }
}
```

#### Rails 컨트롤러 수정
```ruby
# app/controllers/api/v1/mesh_preview_controller.rb
class Api::V1::MeshPreviewController < ApplicationController
  def show
    layer = Layer.find(params[:layer_id])
    mesh = layer.mesh
    
    # SpineLoader가 이해할 수 있는 형식으로 변환
    spine_compatible_data = {
      id: mesh.id,
      vertices: mesh.data['vertices'],
      triangles: mesh.data['triangles'],
      uvs: mesh.data['uvs'],
      texture_path: url_for(layer.image),
      scale: 1.0,
      animations: [] # 메시 프리뷰는 애니메이션 없음
    }
    
    render json: spine_compatible_data
  end
end
```

### 3. 프록시 컨트롤러 활용

```ruby
# app/controllers/spine_files_controller.rb
# SpineProxyController를 참고하여 구현
class SpineFilesController < ApplicationController
  # SpineLift에서 생성한 Spine JSON 파일 서빙
  def show
    filename = params[:filename]
    project = Project.find(params[:project_id])
    
    # 생성된 Spine 파일 경로
    file_path = project.spine_export_path(filename)
    
    if File.exist?(file_path)
      send_file file_path,
                type: content_type_for(filename),
                disposition: 'inline'
    else
      render plain: "File not found", status: 404
    end
  end
  
  private
  
  def content_type_for(filename)
    case File.extname(filename)
    when '.json', '.skel'
      'application/json'
    when '.atlas'
      'text/plain'
    when '.png'
      'image/png'
    else
      'application/octet-stream'
    end
  end
end
```

### 4. ViewComponent 통합

```erb
<!-- app/views/projects/show.html.erb -->
<div class="spine-preview-section">
  <h2>Spine 프리뷰</h2>
  
  <!-- 기존 SpineViewerComponent 활용 -->
  <%= render Spine::SpineViewerComponent.new(
    spine_animation: @project.spine_animation,
    width: 800,
    height: 600,
    auto_play: true
  ) %>
  
  <!-- 컨트롤 UI -->
  <%= render Spine::SpineControlsComponent.new(
    spine_animation: @project.spine_animation,
    show_skin_selector: true,
    show_speed_control: true
  ) %>
</div>
```

### 5. ActionCable 통합

```javascript
// app/javascript/channels/mesh_update_channel.js
import consumer from "./consumer"
import { MeshPreviewLoader } from "../spine/mesh_preview_loader"

consumer.subscriptions.create({ 
  channel: "MeshUpdateChannel",
  layer_id: document.querySelector('[data-layer-id]').dataset.layerId
}, {
  connected() {
    console.log("Connected to MeshUpdateChannel");
  },

  received(data) {
    // 실시간 메시 업데이트
    if (window.meshPreviewLoader) {
      window.meshPreviewLoader.updateMesh(data.mesh);
    }
  }
});
```

## 주요 차이점 및 고려사항

### 1. 파일 구조
- **spine_manager_rails**: 완성된 Spine 파일 재생
- **SpineLift**: 메시 생성 중간 단계 프리뷰

### 2. 데이터 흐름
```
SpineLift 메시 생성 → Python 서비스 → Rails API → PIXI.js 렌더링
                                                    ↑
                                          SpineLoader (재사용)
```

### 3. 추가 기능
- 메시 와이어프레임 표시
- 버텍스 하이라이트
- 실시간 파라미터 조정

## 구현 체크리스트

- [ ] SpineLoader 모듈 복사 및 수정
- [ ] Spine 런타임 파일 설치
- [ ] MeshPreviewLoader 클래스 구현
- [ ] Rails 컨트롤러 설정
- [ ] ViewComponent 통합
- [ ] ActionCable 실시간 업데이트
- [ ] 테스트 및 디버깅

## 성능 최적화

### 1. 리소스 재사용
```javascript
// 메시 업데이트 시 geometry만 교체
updateGeometry(newMeshData) {
  if (this.mesh) {
    this.mesh.geometry.destroy();
    this.mesh.geometry = this.createGeometry(newMeshData);
  }
}
```

### 2. 텍스처 캐싱
```javascript
// 텍스처는 한 번만 로드
if (!PIXI.utils.TextureCache[textureUrl]) {
  PIXI.Texture.from(textureUrl);
}
```

## SpineLift 특화 기능 구현

### 메시 편집기 전용 기능
```javascript
// app/javascript/controllers/mesh_editor_controller.js
import { Controller } from "@hotwired/stimulus"
import { MeshPreviewLoader } from "../spine/mesh_preview_loader"

export default class extends Controller {
  static targets = ["preview", "parameters"]
  
  connect() {
    this.loader = new MeshPreviewLoader();
    this.setupParameterControls();
  }
  
  // 파라미터 변경 시 실시간 업데이트
  updateParameter(event) {
    const param = event.target.name;
    const value = parseFloat(event.target.value);
    
    // Rails API 호출
    fetch(`/api/v1/layers/${this.layerId}/mesh/update_parameters`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': this.csrfToken
      },
      body: JSON.stringify({ [param]: value })
    });
  }
  
  // 와이어프레임 토글
  toggleWireframe(event) {
    this.loader.showWireframe = event.target.checked;
    this.loader.refreshDisplay();
  }
  
  // 버텍스 포인트 표시
  showVertices(event) {
    this.loader.showVertices = event.target.checked;
    this.loader.refreshDisplay();
  }
}
```

### 메시 데이터 변환 헬퍼
```javascript
// app/javascript/spine/mesh_data_converter.js
export class MeshDataConverter {
  // SpineLift 메시 데이터를 PIXI 형식으로 변환
  static toPIXIFormat(spineLiftMesh) {
    return {
      vertices: new Float32Array(spineLiftMesh.vertices),
      uvs: new Float32Array(spineLiftMesh.uvs),
      indices: new Uint16Array(spineLiftMesh.triangles)
    };
  }
  
  // Spine JSON 포맷으로 변환
  static toSpineFormat(spineLiftMesh, attachmentName) {
    return {
      type: "mesh",
      uvs: spineLiftMesh.uvs,
      triangles: spineLiftMesh.triangles,
      vertices: spineLiftMesh.vertices,
      hull: spineLiftMesh.hull || 0,
      edges: spineLiftMesh.edges || [],
      width: spineLiftMesh.width,
      height: spineLiftMesh.height
    };
  }
}
```

## 결론

spine_manager_rails의 검증된 Spine 뷰어 구현을 활용하면 SpineLift의 메시 프리뷰 기능을 빠르게 구현할 수 있습니다. 기존 코드를 재사용하면서 SpineLift의 특수한 요구사항(메시 편집, 실시간 업데이트)에 맞게 확장하는 것이 핵심입니다.