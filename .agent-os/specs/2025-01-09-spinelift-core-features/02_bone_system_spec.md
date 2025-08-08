# 본(Bone) 설정 및 바인딩 시스템 명세서

## 개요

현재 SpineLift Rails에서는 메시 생성까지만 구현되어 있고, Spine 애니메이션의 핵심인 본(Bone) 시스템이 전혀 구현되지 않았습니다. 이 명세서는 본 생성, 계층 구조 편집, 메시-본 바인딩, Weight 페인팅 등의 완전한 본 시스템을 정의합니다.

**담당 영역**: 풀스택 (백엔드 모델, API, 프론트엔드 에디터)  
**우선순위**: Medium-High  
**예상 구현 시간**: 4-5주  
**의존성**: 메시 생성 시스템 완료 후 구현  

## 현재 상태 분석

### 기존 구현 부족사항
- 본(Bone) 데이터 모델 없음
- 본-메시 바인딩 시스템 없음
- Weight 페인팅 도구 없음  
- 본 계층 구조 관리 없음
- IK(Inverse Kinematics) 시스템 없음

### Spine 본 시스템 요구사항
Spine 3.8.95 표준에 따른 본 시스템 구조:
```json
{
  "bones": [
    {
      "name": "root",
      "length": 0,
      "x": 0, "y": 0,
      "rotation": 0,
      "scaleX": 1, "scaleY": 1
    },
    {
      "name": "spine",
      "parent": "root", 
      "length": 100,
      "x": 0, "y": 50,
      "rotation": 90
    }
  ]
}
```

## 기능 요구사항

### 1. 본 데이터 구조

#### 1.1 Bone 모델
```ruby
# app/models/bone.rb
class Bone < ApplicationRecord
  belongs_to :project
  belongs_to :parent_bone, class_name: 'Bone', optional: true
  has_many :child_bones, class_name: 'Bone', foreign_key: 'parent_bone_id', dependent: :destroy
  has_many :bone_weights, dependent: :destroy
  has_many :vertices, through: :bone_weights, source: :vertex
  
  validates :name, presence: true, uniqueness: { scope: :project_id }
  validates :length, presence: true, numericality: { greater_than_or_equal_to: 0 }
  validates :x, :y, :rotation, :scale_x, :scale_y, presence: true, numericality: true
  
  # 계층 구조 관리
  def descendants
    child_bones.includes(:child_bones).flat_map { |child| [child] + child.descendants }
  end
  
  def ancestors
    parent_bone ? [parent_bone] + parent_bone.ancestors : []
  end
  
  def depth
    parent_bone ? parent_bone.depth + 1 : 0
  end
  
  # 변환 매트릭스 계산
  def world_transform
    local_transform = calculate_local_transform
    parent_bone ? parent_bone.world_transform * local_transform : local_transform
  end
  
  private
  
  def calculate_local_transform
    # 2D 변환 매트릭스 계산 (위치, 회전, 스케일)
    Matrix[
      [scale_x * Math.cos(rotation), -scale_y * Math.sin(rotation), x],
      [scale_x * Math.sin(rotation), scale_y * Math.cos(rotation), y],
      [0, 0, 1]
    ]
  end
end
```

#### 1.2 Vertex 및 BoneWeight 모델
```ruby
# app/models/vertex.rb
class Vertex < ApplicationRecord
  belongs_to :mesh
  has_many :bone_weights, dependent: :destroy
  has_many :bones, through: :bone_weights
  
  validates :x, :y, presence: true, numericality: true
  validates :u, :v, presence: true, numericality: { in: 0.0..1.0 } # UV 좌표
  validates :index, presence: true, numericality: { greater_than_or_equal_to: 0 }
  
  # Weight 정규화
  def normalize_weights!
    total_weight = bone_weights.sum(:weight)
    return if total_weight.zero?
    
    bone_weights.each do |bw|
      bw.update!(weight: bw.weight / total_weight)
    end
  end
end

# app/models/bone_weight.rb
class BoneWeight < ApplicationRecord
  belongs_to :bone
  belongs_to :vertex
  
  validates :weight, presence: true, numericality: { in: 0.0..1.0 }
  validates :bone_id, uniqueness: { scope: :vertex_id }
  
  scope :significant, -> { where('weight > 0.001') } # 의미있는 가중치만
end
```

#### 1.3 데이터베이스 스키마
```ruby
# db/migrate/create_bones.rb
class CreateBones < ActiveRecord::Migration[7.0]
  def change
    create_table :bones do |t|
      t.references :project, null: false, foreign_key: true
      t.references :parent_bone, null: true, foreign_key: { to_table: :bones }
      
      t.string :name, null: false
      t.float :length, null: false, default: 0
      t.float :x, null: false, default: 0
      t.float :y, null: false, default: 0
      t.float :rotation, null: false, default: 0
      t.float :scale_x, null: false, default: 1
      t.float :scale_y, null: false, default: 1
      
      t.jsonb :metadata, default: {}
      t.integer :order_index, default: 0
      
      t.timestamps
    end
    
    add_index :bones, [:project_id, :name], unique: true
    add_index :bones, :parent_bone_id
    add_index :bones, :order_index
  end
end

# db/migrate/create_vertices.rb
class CreateVertices < ActiveRecord::Migration[7.0]
  def change
    create_table :vertices do |t|
      t.references :mesh, null: false, foreign_key: true
      
      t.float :x, null: false
      t.float :y, null: false
      t.float :u, null: false # UV 좌표
      t.float :v, null: false # UV 좌표
      t.integer :index, null: false # 메시 내 버텍스 인덱스
      
      t.timestamps
    end
    
    add_index :vertices, [:mesh_id, :index], unique: true
  end
end

# db/migrate/create_bone_weights.rb
class CreateBoneWeights < ActiveRecord::Migration[7.0]
  def change
    create_table :bone_weights do |t|
      t.references :bone, null: false, foreign_key: true
      t.references :vertex, null: false, foreign_key: true
      
      t.float :weight, null: false, default: 0
      
      t.timestamps
    end
    
    add_index :bone_weights, [:bone_id, :vertex_id], unique: true
    add_index :bone_weights, :weight
  end
end
```

### 2. 본 에디터 UI 컴포넌트

#### 2.1 BoneHierarchy 컴포넌트
```typescript
interface BoneNode {
  id: string;
  name: string;
  parentId?: string;
  children: BoneNode[];
  x: number;
  y: number;
  rotation: number;
  length: number;
  scaleX: number;
  scaleY: number;
  isSelected: boolean;
  isVisible: boolean;
}

interface BoneHierarchyProps {
  bones: BoneNode[];
  selectedBoneIds: string[];
  onBoneSelect: (boneId: string, multiSelect?: boolean) => void;
  onBoneCreate: (parentId?: string) => void;
  onBoneDelete: (boneId: string) => void;
  onBoneRename: (boneId: string, newName: string) => void;
  onBoneReorder: (boneId: string, newParentId?: string, newIndex?: number) => void;
}

export const BoneHierarchy: React.FC<BoneHierarchyProps> = ({
  bones,
  selectedBoneIds,
  onBoneSelect,
  onBoneCreate,
  onBoneDelete,
  onBoneRename,
  onBoneReorder
}) => {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  
  const renderBoneNode = (bone: BoneNode, depth: number = 0) => (
    <div key={bone.id} className={`bone-node depth-${depth}`}>
      <div className={`bone-item ${selectedBoneIds.includes(bone.id) ? 'selected' : ''}`}>
        <button 
          className="expand-toggle"
          onClick={() => toggleExpanded(bone.id)}
          disabled={bone.children.length === 0}
        >
          {bone.children.length > 0 && (
            expandedNodes.has(bone.id) ? '▼' : '▶'
          )}
        </button>
        
        <span 
          className="bone-name"
          onClick={() => onBoneSelect(bone.id)}
          onDoubleClick={() => startRenaming(bone.id)}
        >
          {bone.name}
        </span>
        
        <div className="bone-controls">
          <button onClick={() => onBoneCreate(bone.id)}>+</button>
          <button onClick={() => onBoneDelete(bone.id)}>×</button>
        </div>
      </div>
      
      {expandedNodes.has(bone.id) && bone.children.map(child => 
        renderBoneNode(child, depth + 1)
      )}
    </div>
  );
  
  return (
    <div className="bone-hierarchy">
      <div className="hierarchy-header">
        <h3>본 계층 구조</h3>
        <button onClick={() => onBoneCreate()}>루트 본 추가</button>
      </div>
      
      <div className="hierarchy-tree">
        {bones.filter(bone => !bone.parentId).map(rootBone => 
          renderBoneNode(rootBone)
        )}
      </div>
    </div>
  );
};
```

#### 2.2 BoneEditor 캔버스 컴포넌트
```typescript
interface BoneEditorProps {
  mesh: Mesh;
  bones: BoneNode[];
  selectedBoneIds: string[];
  editMode: 'select' | 'create' | 'weight_paint';
  onBoneTransform: (boneId: string, transform: BoneTransform) => void;
  onBoneCreate: (position: { x: number; y: number }, parentId?: string) => void;
  onWeightPaint: (vertexId: string, boneId: string, weight: number) => void;
}

export const BoneEditor: React.FC<BoneEditorProps> = ({
  mesh,
  bones,
  selectedBoneIds,
  editMode,
  onBoneTransform,
  onBoneCreate,
  onWeightPaint
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  // PIXI.js 또는 Fabric.js를 사용한 캔버스 구현
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const app = new PIXI.Application({
      view: canvasRef.current,
      width: 800,
      height: 600,
      backgroundColor: 0x2b2b2b,
    });
    
    // 메시 렌더링
    renderMesh(app, mesh);
    
    // 본 렌더링
    renderBones(app, bones, selectedBoneIds);
    
    // 이벤트 핸들러 설정
    setupInteractionHandlers(app);
    
    return () => {
      app.destroy(true);
    };
  }, [mesh, bones, selectedBoneIds, editMode]);
  
  const renderBones = (app: PIXI.Application, bones: BoneNode[], selectedIds: string[]) => {
    bones.forEach(bone => {
      // 본을 선분으로 표시
      const graphics = new PIXI.Graphics();
      const isSelected = selectedIds.includes(bone.id);
      
      graphics.lineStyle(isSelected ? 3 : 2, isSelected ? 0xff6b35 : 0x4ecdc4);
      graphics.moveTo(bone.x, bone.y);
      
      const endX = bone.x + bone.length * Math.cos(bone.rotation);
      const endY = bone.y + bone.length * Math.sin(bone.rotation);
      graphics.lineTo(endX, endY);
      
      // 본의 끝에 조인트 표시
      graphics.beginFill(isSelected ? 0xff6b35 : 0x4ecdc4);
      graphics.drawCircle(bone.x, bone.y, isSelected ? 6 : 4);
      graphics.drawCircle(endX, endY, isSelected ? 4 : 3);
      graphics.endFill();
      
      // 본 이름 표시
      const nameText = new PIXI.Text(bone.name, {
        fontSize: 12,
        fill: 0xffffff,
        fontFamily: 'Arial'
      });
      nameText.x = bone.x + 10;
      nameText.y = bone.y - 10;
      
      app.stage.addChild(graphics);
      app.stage.addChild(nameText);
    });
  };
  
  return (
    <div className="bone-editor">
      <div className="editor-toolbar">
        <button 
          className={editMode === 'select' ? 'active' : ''}
          onClick={() => setEditMode('select')}
        >
          선택
        </button>
        <button 
          className={editMode === 'create' ? 'active' : ''}
          onClick={() => setEditMode('create')}
        >
          본 생성
        </button>
        <button 
          className={editMode === 'weight_paint' ? 'active' : ''}
          onClick={() => setEditMode('weight_paint')}
        >
          Weight 페인팅
        </button>
      </div>
      
      <canvas ref={canvasRef} className="bone-canvas" />
      
      <div className="editor-status">
        선택된 본: {selectedBoneIds.length}개 | 모드: {editMode}
      </div>
    </div>
  );
};
```

#### 2.3 WeightPainter 컴포넌트
```typescript
interface WeightPainterProps {
  mesh: Mesh;
  selectedBoneId: string;
  brushSize: number;
  brushStrength: number;
  paintMode: 'add' | 'subtract' | 'smooth';
  onWeightChange: (vertexIndices: number[], weights: number[]) => void;
}

export const WeightPainter: React.FC<WeightPainterProps> = ({
  mesh,
  selectedBoneId,
  brushSize,
  brushStrength,
  paintMode,
  onWeightChange
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPainting, setIsPainting] = useState(false);
  
  const handleMouseDown = useCallback((event: MouseEvent) => {
    if (!selectedBoneId) return;
    
    setIsPainting(true);
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    paintWeights(x, y);
  }, [selectedBoneId, brushSize, brushStrength, paintMode]);
  
  const paintWeights = useCallback((x: number, y: number) => {
    if (!mesh || !selectedBoneId) return;
    
    // 브러시 범위 내의 버텍스 찾기
    const affectedVertices = mesh.vertices.filter(vertex => {
      const distance = Math.sqrt(
        Math.pow(vertex.x - x, 2) + Math.pow(vertex.y - y, 2)
      );
      return distance <= brushSize;
    });
    
    // Weight 계산 및 적용
    const vertexIndices: number[] = [];
    const weights: number[] = [];
    
    affectedVertices.forEach(vertex => {
      const distance = Math.sqrt(
        Math.pow(vertex.x - x, 2) + Math.pow(vertex.y - y, 2)
      );
      const falloff = Math.max(0, 1 - (distance / brushSize));
      
      let newWeight = 0;
      const currentWeight = vertex.getBoneWeight(selectedBoneId) || 0;
      
      switch (paintMode) {
        case 'add':
          newWeight = Math.min(1, currentWeight + (brushStrength * falloff));
          break;
        case 'subtract':
          newWeight = Math.max(0, currentWeight - (brushStrength * falloff));
          break;
        case 'smooth':
          // 주변 버텍스의 평균 Weight로 부드럽게
          newWeight = calculateSmoothedWeight(vertex, selectedBoneId);
          break;
      }
      
      vertexIndices.push(vertex.index);
      weights.push(newWeight);
    });
    
    onWeightChange(vertexIndices, weights);
  }, [mesh, selectedBoneId, brushSize, brushStrength, paintMode, onWeightChange]);
  
  return (
    <div className="weight-painter">
      <div className="painter-controls">
        <div className="control-group">
          <label>브러시 크기</label>
          <input 
            type="range" 
            min="5" 
            max="100" 
            value={brushSize} 
            onChange={(e) => setBrushSize(Number(e.target.value))}
          />
          <span>{brushSize}px</span>
        </div>
        
        <div className="control-group">
          <label>브러시 강도</label>
          <input 
            type="range" 
            min="0.1" 
            max="1" 
            step="0.1" 
            value={brushStrength} 
            onChange={(e) => setBrushStrength(Number(e.target.value))}
          />
          <span>{brushStrength}</span>
        </div>
        
        <div className="control-group">
          <label>페인트 모드</label>
          <select value={paintMode} onChange={(e) => setPaintMode(e.target.value as any)}>
            <option value="add">추가</option>
            <option value="subtract">제거</option>
            <option value="smooth">부드럽게</option>
          </select>
        </div>
      </div>
      
      <canvas 
        ref={canvasRef} 
        className="weight-canvas"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={() => setIsPainting(false)}
      />
      
      <div className="weight-visualization">
        <h4>Weight 시각화</h4>
        <div className="weight-legend">
          <span style={{ background: 'linear-gradient(to right, blue, red)' }}>
            0.0 ← Weight → 1.0
          </span>
        </div>
      </div>
    </div>
  );
};
```

### 3. 백엔드 API 설계

#### 3.1 본 관리 API
```ruby
# app/controllers/api/v1/bones_controller.rb
class Api::V1::BonesController < Api::V1::BaseController
  before_action :set_project
  before_action :set_bone, only: [:show, :update, :destroy]
  
  def index
    bones = @project.bones.includes(:parent_bone, :child_bones)
    render json: BoneSerializer.new(bones, include: [:parent_bone, :child_bones])
  end
  
  def create
    bone = @project.bones.build(bone_params)
    
    if bone.save
      render json: BoneSerializer.new(bone), status: :created
    else
      render json: { errors: bone.errors }, status: :unprocessable_entity
    end
  end
  
  def update
    if @bone.update(bone_params)
      render json: BoneSerializer.new(@bone)
    else
      render json: { errors: @bone.errors }, status: :unprocessable_entity
    end
  end
  
  def destroy
    @bone.destroy
    head :no_content
  end
  
  # 본 계층 구조 재정렬
  def reorder
    bones_data = params[:bones]
    
    ActiveRecord::Base.transaction do
      bones_data.each do |bone_data|
        bone = @project.bones.find(bone_data[:id])
        bone.update!(
          parent_bone_id: bone_data[:parent_id],
          order_index: bone_data[:order_index]
        )
      end
    end
    
    render json: { status: 'success' }
  end
  
  # 자동 본 생성 (메시 기반)
  def auto_generate
    service = AutoBoneGenerationService.new(@project)
    bones = service.generate_from_mesh
    
    render json: BoneSerializer.new(bones)
  end
  
  private
  
  def set_project
    @project = current_user.projects.find(params[:project_id])
  end
  
  def set_bone
    @bone = @project.bones.find(params[:id])
  end
  
  def bone_params
    params.require(:bone).permit(
      :name, :parent_bone_id, :length, :x, :y, :rotation, 
      :scale_x, :scale_y, :order_index, metadata: {}
    )
  end
end
```

#### 3.2 Weight 페인팅 API
```ruby
# app/controllers/api/v1/bone_weights_controller.rb
class Api::V1::BoneWeightsController < Api::V1::BaseController
  def batch_update
    vertex_ids = params[:vertex_ids]
    bone_id = params[:bone_id]
    weights = params[:weights]
    
    ActiveRecord::Base.transaction do
      vertex_ids.each_with_index do |vertex_id, index|
        weight_value = weights[index]
        
        if weight_value > 0.001
          # 의미있는 Weight만 저장
          BoneWeight.find_or_initialize_by(
            vertex_id: vertex_id,
            bone_id: bone_id
          ).update!(weight: weight_value)
        else
          # 작은 Weight는 삭제
          BoneWeight.where(
            vertex_id: vertex_id,
            bone_id: bone_id
          ).destroy_all
        end
      end
      
      # Weight 정규화
      vertex_ids.each do |vertex_id|
        vertex = Vertex.find(vertex_id)
        vertex.normalize_weights!
      end
    end
    
    render json: { status: 'success' }
  end
  
  # 자동 Weight 생성
  def auto_generate
    layer = Layer.find(params[:layer_id])
    service = AutoWeightService.new(layer)
    weights = service.generate_automatic_weights
    
    render json: { weights: weights }
  end
end
```

### 4. 자동화 서비스

#### 4.1 자동 본 생성 서비스
```ruby
# app/services/auto_bone_generation_service.rb
class AutoBoneGenerationService
  def initialize(project)
    @project = project
  end
  
  def generate_from_mesh
    layers = @project.layers.includes(:mesh)
    bones = []
    
    layers.each do |layer|
      next unless layer.mesh
      
      # 메시 중심점을 기준으로 본 생성
      center = calculate_mesh_center(layer.mesh)
      
      # 루트 본 생성
      root_bone = create_bone(
        name: "#{layer.name}_root",
        x: center[:x],
        y: center[:y],
        length: 0
      )
      bones << root_bone
      
      # 메시 크기에 따른 스파인 본 생성
      spine_bone = create_bone(
        name: "#{layer.name}_spine",
        parent: root_bone,
        x: center[:x],
        y: center[:y] + 50,
        length: calculate_optimal_length(layer.mesh),
        rotation: Math::PI / 2 # 90도
      )
      bones << spine_bone
    end
    
    bones
  end
  
  private
  
  def calculate_mesh_center(mesh)
    vertices = JSON.parse(mesh.data)['vertices']
    x_sum = vertices.sum { |v| v[0] }
    y_sum = vertices.sum { |v| v[1] }
    
    {
      x: x_sum / vertices.length,
      y: y_sum / vertices.length
    }
  end
  
  def calculate_optimal_length(mesh)
    # 메시 크기의 30% 정도로 본 길이 설정
    bounds = calculate_mesh_bounds(mesh)
    Math.sqrt(bounds[:width]**2 + bounds[:height]**2) * 0.3
  end
  
  def create_bone(attributes)
    @project.bones.create!(attributes)
  end
end
```

#### 4.2 자동 Weight 생성 서비스
```ruby
# app/services/auto_weight_service.rb
class AutoWeightService
  def initialize(layer)
    @layer = layer
    @mesh = layer.mesh
  end
  
  def generate_automatic_weights
    vertices = create_vertices_from_mesh
    bones = @layer.project.bones
    
    weights = {}
    
    vertices.each do |vertex|
      bone_weights = calculate_vertex_weights(vertex, bones)
      weights[vertex.id] = bone_weights
    end
    
    apply_weights_to_database(weights)
    weights
  end
  
  private
  
  def calculate_vertex_weights(vertex, bones)
    weights = {}
    total_influence = 0
    
    bones.each do |bone|
      # 거리 기반 Weight 계산
      distance = calculate_distance_to_bone(vertex, bone)
      influence = calculate_influence(distance)
      
      if influence > 0.001
        weights[bone.id] = influence
        total_influence += influence
      end
    end
    
    # Weight 정규화
    if total_influence > 0
      weights.each { |bone_id, weight| weights[bone_id] = weight / total_influence }
    end
    
    weights
  end
  
  def calculate_distance_to_bone(vertex, bone)
    # 점-선분 거리 계산
    bone_start = { x: bone.x, y: bone.y }
    bone_end = {
      x: bone.x + bone.length * Math.cos(bone.rotation),
      y: bone.y + bone.length * Math.sin(bone.rotation)
    }
    
    distance_to_line_segment(
      { x: vertex.x, y: vertex.y },
      bone_start,
      bone_end
    )
  end
  
  def calculate_influence(distance)
    # 거리가 가까울수록 높은 영향력
    max_distance = 200 # 최대 영향 거리
    return 0 if distance > max_distance
    
    1.0 - (distance / max_distance)
  end
end
```

## 사용자 워크플로우

### 1. 기본 본 생성 워크플로우
```
1. 메시 생성 완료 후 "본 추가" 버튼 클릭
2. 자동 본 생성 또는 수동 본 생성 선택
3. 캔버스에서 본 위치 클릭하여 생성
4. 본 계층 구조에서 부모-자식 관계 설정
5. 본 속성(길이, 회전, 스케일) 조정
```

### 2. Weight 페인팅 워크플로우
```
1. 본 선택 후 "Weight 페인팅" 모드 활성화
2. 브러시 크기 및 강도 조정
3. 메시 위에 Weight 페인팅
4. Weight 시각화로 결과 확인
5. 필요시 다른 본으로 전환하여 추가 페인팅
6. 자동 정규화로 Weight 합계를 1.0으로 조정
```

## 성능 최적화

### 1. 데이터베이스 최적화
- 본 계층 구조 쿼리 최적화 (Nested Set 또는 Path Enumeration)
- Weight 데이터 압축 저장
- 인덱스 최적화

### 2. 프론트엔드 최적화
- WebGL 기반 렌더링으로 성능 향상
- Weight 시각화를 위한 셰이더 활용
- LOD(Level of Detail) 시스템으로 복잡한 메시 처리

## 테스트 전략

### 1. 단위 테스트
```ruby
# spec/models/bone_spec.rb
RSpec.describe Bone, type: :model do
  describe 'hierarchy management' do
    let(:root) { create(:bone, name: 'root') }
    let(:spine) { create(:bone, name: 'spine', parent_bone: root) }
    let(:head) { create(:bone, name: 'head', parent_bone: spine) }
    
    it 'calculates depth correctly' do
      expect(root.depth).to eq(0)
      expect(spine.depth).to eq(1)
      expect(head.depth).to eq(2)
    end
    
    it 'finds descendants correctly' do
      expect(root.descendants).to contain_exactly(spine, head)
      expect(spine.descendants).to contain_exactly(head)
    end
  end
end
```

### 2. 통합 테스트
```ruby
# spec/services/auto_bone_generation_service_spec.rb
RSpec.describe AutoBoneGenerationService do
  let(:project) { create(:project) }
  let(:layer) { create(:layer, project: project) }
  let(:mesh) { create(:mesh, layer: layer) }
  
  before do
    mesh.update!(data: {
      vertices: [[0, 0], [100, 0], [50, 100]],
      triangles: [[0, 1, 2]],
      uvs: [[0, 0], [1, 0], [0.5, 1]]
    })
  end
  
  it 'generates appropriate bone structure' do
    service = described_class.new(project)
    bones = service.generate_from_mesh
    
    expect(bones.length).to be >= 2
    expect(bones.first.name).to include('root')
  end
end
```

## 구현 로드맵

### Week 1-2: 데이터 모델 구현
- [x] Bone, Vertex, BoneWeight 모델 생성
- [x] 데이터베이스 마이그레이션
- [x] 기본 관계 설정 및 검증

### Week 3: 본 계층 구조 UI
- [x] BoneHierarchy 컴포넌트 구현
- [x] 드래그 앤 드롭으로 계층 구조 편집
- [x] 본 생성/삭제/이름 변경 기능

### Week 4: 본 에디터 캔버스
- [x] PIXI.js 기반 본 시각화
- [x] 본 선택 및 변형 도구
- [x] 메시 위에 본 오버레이

### Week 5: Weight 페인팅 시스템
- [x] Weight 페인팅 브러시 구현
- [x] Weight 시각화
- [x] 자동 Weight 생성

### Week 6: 자동화 및 최적화
- [ ] 자동 본 생성 알고리즘
- [ ] 성능 최적화
- [ ] 테스트 및 디버깅

## 성공 지표

1. **기능성**: 완전한 본 계층 구조 생성 및 편집
2. **정확성**: Weight의 정확한 정규화 및 바인딩
3. **성능**: 1000+ 버텍스에서도 실시간 Weight 페인팅
4. **사용성**: 직관적인 본 생성 및 Weight 페인팅 워크플로우