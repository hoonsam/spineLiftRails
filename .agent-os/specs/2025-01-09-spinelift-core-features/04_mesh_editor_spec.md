# 메시 프리뷰 및 편집 기능 명세서

## 개요

현재 SpineLift Rails의 메시 프리뷰는 기본적인 HTML5 Canvas 렌더링만 제공하고 있어, 사용자가 메시를 직접 편집하거나 세밀한 조작을 할 수 없습니다. 이 명세서는 WebGL 기반의 고성능 메시 에디터와 실시간 편집 기능을 정의합니다.

**담당 영역**: 프론트엔드 WebGL 렌더링, 상호작용 시스템  
**우선순위**: High  
**예상 구현 시간**: 4-5주  
**의존성**: 메시 생성 시스템 기본 동작 완료 후 구현  

## 현재 상태 분석

### 기존 MeshPreview 컴포넌트의 한계
- **HTML5 Canvas 2D**: 기본적인 2D 렌더링만 가능
- **정적 시각화**: 메시를 보기만 할 수 있고 편집 불가
- **제한된 상호작용**: 줌, 팬, 회전 등 뷰포트 조작 불가
- **성능 이슈**: 복잡한 메시에서 렌더링 성능 저하
- **시각적 피드백 부족**: 와이어프레임, 버텍스 하이라이트 등 없음

### 원래 SpineLift의 메시 에디터 기능
- 버텍스 직접 드래그 앤 드롭으로 조작
- 실시간 메시 형태 변경
- 와이어프레임/솔리드 모드 전환
- 버텍스 선택 및 다중 선택
- 언두/리두 시스템
- 메시 품질 실시간 피드백

## 기능 요구사항

### 1. WebGL 기반 렌더링 시스템

#### 1.1 PIXI.js 통합 설정
```typescript
// src/lib/mesh-editor/MeshRenderer.ts
import * as PIXI from 'pixi.js';

export class MeshRenderer {
  private app: PIXI.Application;
  private meshContainer: PIXI.Container;
  private backgroundContainer: PIXI.Container;
  private overlayContainer: PIXI.Container;
  
  constructor(canvas: HTMLCanvasElement, width: number, height: number) {
    this.app = new PIXI.Application({
      view: canvas,
      width,
      height,
      backgroundColor: 0x2b2b2b,
      antialias: true,
      transparent: false,
      resolution: window.devicePixelRatio || 1,
      autoDensity: true,
    });
    
    this.setupContainers();
    this.setupInteraction();
  }
  
  private setupContainers() {
    // 레이어 구조: 배경 → 메시 → 오버레이
    this.backgroundContainer = new PIXI.Container();
    this.meshContainer = new PIXI.Container();
    this.overlayContainer = new PIXI.Container();
    
    this.app.stage.addChild(this.backgroundContainer);
    this.app.stage.addChild(this.meshContainer); 
    this.app.stage.addChild(this.overlayContainer);
  }
  
  private setupInteraction() {
    // 인터랙션 플러그인 활성화
    this.app.stage.interactive = true;
    this.app.stage.sortableChildren = true;
    
    // 뷰포트 조작 설정
    this.setupViewportControls();
  }
  
  private setupViewportControls() {
    let isDragging = false;
    let lastPosition = { x: 0, y: 0 };
    
    // 팬 (드래그로 이동)
    this.app.stage.on('pointerdown', (event) => {
      if (event.data.originalEvent.button === 1) { // 마우스 휠 버튼
        isDragging = true;
        lastPosition = event.data.global;
        this.app.stage.cursor = 'grab';
      }
    });
    
    this.app.stage.on('pointermove', (event) => {
      if (isDragging) {
        const dx = event.data.global.x - lastPosition.x;
        const dy = event.data.global.y - lastPosition.y;
        
        this.meshContainer.x += dx;
        this.meshContainer.y += dy;
        
        lastPosition = event.data.global;
      }
    });
    
    this.app.stage.on('pointerup', () => {
      isDragging = false;
      this.app.stage.cursor = 'default';
    });
    
    // 줌 (휠 스크롤)
    this.app.view.addEventListener('wheel', (event) => {
      event.preventDefault();
      
      const scaleFactor = event.deltaY < 0 ? 1.1 : 0.9;
      const newScale = this.meshContainer.scale.x * scaleFactor;
      
      // 줌 제한
      if (newScale >= 0.1 && newScale <= 5) {
        const mousePosition = this.app.renderer.plugins.interaction.mouse.global;
        
        // 마우스 포인터를 중심으로 줌
        this.meshContainer.scale.set(newScale);
        
        const dx = (mousePosition.x - this.meshContainer.x) * (scaleFactor - 1);
        const dy = (mousePosition.y - this.meshContainer.y) * (scaleFactor - 1);
        
        this.meshContainer.x -= dx;
        this.meshContainer.y -= dy;
      }
    });
  }
  
  public renderMesh(meshData: MeshData, texture: PIXI.Texture, renderMode: RenderMode) {
    this.meshContainer.removeChildren();
    
    // 메시 지오메트리 생성
    const geometry = new PIXI.Geometry()
      .addAttribute('aVertexPosition', meshData.vertices, 2)
      .addAttribute('aUvs', meshData.uvs, 2)
      .addIndex(meshData.triangles);
    
    // 렌더링 모드에 따른 셰이더 선택
    const material = this.createMaterial(texture, renderMode);
    
    const mesh = new PIXI.Mesh(geometry, material);
    mesh.interactive = true;
    
    this.meshContainer.addChild(mesh);
    
    // 와이어프레임 오버레이
    if (renderMode.showWireframe) {
      this.renderWireframe(meshData);
    }
    
    // 버텍스 포인트 오버레이
    if (renderMode.showVertices) {
      this.renderVertices(meshData);
    }
  }
  
  private createMaterial(texture: PIXI.Texture, renderMode: RenderMode): PIXI.MeshMaterial | PIXI.Shader {
    if (renderMode.useCustomShader) {
      return this.createCustomShader(texture, renderMode);
    }
    
    return new PIXI.MeshMaterial(texture, {
      alpha: renderMode.opacity,
      tint: renderMode.tint,
    });
  }
  
  private createCustomShader(texture: PIXI.Texture, renderMode: RenderMode): PIXI.Shader {
    const vertexShader = `
      precision mediump float;
      attribute vec2 aVertexPosition;
      attribute vec2 aUvs;
      
      uniform mat3 translationMatrix;
      uniform mat3 projectionMatrix;
      
      varying vec2 vUvs;
      
      void main() {
        vUvs = aUvs;
        gl_Position = vec4((projectionMatrix * translationMatrix * vec3(aVertexPosition, 1.0)).xy, 0.0, 1.0);
      }
    `;
    
    const fragmentShader = `
      precision mediump float;
      varying vec2 vUvs;
      uniform sampler2D uSampler;
      uniform float uAlpha;
      uniform vec3 uTint;
      uniform float uShowWeights;
      uniform sampler2D uWeightTexture;
      
      void main() {
        vec4 color = texture2D(uSampler, vUvs);
        
        if (uShowWeights > 0.5) {
          vec4 weight = texture2D(uWeightTexture, vUvs);
          color.rgb = mix(color.rgb, weight.rgb, 0.7);
        }
        
        color.rgb *= uTint;
        color.a *= uAlpha;
        
        gl_FragColor = color;
      }
    `;
    
    return PIXI.Shader.from(vertexShader, fragmentShader, {
      uSampler: texture,
      uAlpha: renderMode.opacity,
      uTint: [1.0, 1.0, 1.0],
      uShowWeights: renderMode.showWeights ? 1.0 : 0.0,
      uWeightTexture: renderMode.weightTexture || PIXI.Texture.WHITE,
    });
  }
  
  private renderWireframe(meshData: MeshData) {
    const wireframe = new PIXI.Graphics();
    wireframe.lineStyle(1, 0x00ff00, 0.8);
    
    // 삼각형 엣지 그리기
    for (let i = 0; i < meshData.triangles.length; i += 3) {
      const i1 = meshData.triangles[i] * 2;
      const i2 = meshData.triangles[i + 1] * 2;
      const i3 = meshData.triangles[i + 2] * 2;
      
      const v1 = { x: meshData.vertices[i1], y: meshData.vertices[i1 + 1] };
      const v2 = { x: meshData.vertices[i2], y: meshData.vertices[i2 + 1] };
      const v3 = { x: meshData.vertices[i3], y: meshData.vertices[i3 + 1] };
      
      wireframe.moveTo(v1.x, v1.y);
      wireframe.lineTo(v2.x, v2.y);
      wireframe.lineTo(v3.x, v3.y);
      wireframe.lineTo(v1.x, v1.y);
    }
    
    this.overlayContainer.addChild(wireframe);
  }
  
  private renderVertices(meshData: MeshData) {
    for (let i = 0; i < meshData.vertices.length; i += 2) {
      const vertex = new PIXI.Graphics();
      vertex.beginFill(0xff6b35);
      vertex.drawCircle(0, 0, 3);
      vertex.endFill();
      
      vertex.x = meshData.vertices[i];
      vertex.y = meshData.vertices[i + 1];
      vertex.interactive = true;
      vertex.buttonMode = true;
      
      // 버텍스 인덱스 저장
      (vertex as any).vertexIndex = i / 2;
      
      // 버텍스 드래그 이벤트
      this.setupVertexInteraction(vertex);
      
      this.overlayContainer.addChild(vertex);
    }
  }
  
  private setupVertexInteraction(vertex: PIXI.Graphics) {
    let isDragging = false;
    let startPosition = { x: 0, y: 0 };
    
    vertex.on('pointerdown', (event) => {
      isDragging = true;
      startPosition = event.data.global;
      vertex.alpha = 0.7;
      
      // 드래그 시작 이벤트 발생
      this.emit('vertex-drag-start', { 
        vertexIndex: (vertex as any).vertexIndex,
        position: { x: vertex.x, y: vertex.y }
      });
    });
    
    vertex.on('pointermove', (event) => {
      if (isDragging) {
        const dx = event.data.global.x - startPosition.x;
        const dy = event.data.global.y - startPosition.y;
        
        vertex.x += dx;
        vertex.y += dy;
        
        startPosition = event.data.global;
        
        // 드래그 중 이벤트 발생
        this.emit('vertex-drag', { 
          vertexIndex: (vertex as any).vertexIndex,
          position: { x: vertex.x, y: vertex.y }
        });
      }
    });
    
    vertex.on('pointerup', () => {
      if (isDragging) {
        isDragging = false;
        vertex.alpha = 1.0;
        
        // 드래그 종료 이벤트 발생
        this.emit('vertex-drag-end', { 
          vertexIndex: (vertex as any).vertexIndex,
          position: { x: vertex.x, y: vertex.y }
        });
      }
    });
  }
  
  public dispose() {
    this.app.destroy(true);
  }
}
```

#### 1.2 메시 데이터 타입 정의
```typescript
// src/lib/mesh-editor/types.ts
export interface MeshData {
  vertices: Float32Array | number[];
  triangles: Uint16Array | number[];
  uvs: Float32Array | number[];
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface RenderMode {
  showWireframe: boolean;
  showVertices: boolean;
  showWeights: boolean;
  useCustomShader: boolean;
  opacity: number;
  tint: number;
  weightTexture?: PIXI.Texture;
}

export interface EditOperation {
  type: 'vertex-move' | 'vertex-add' | 'vertex-delete' | 'triangle-add' | 'triangle-delete';
  data: any;
  timestamp: number;
  beforeState: MeshData;
  afterState: MeshData;
}
```

### 2. 메시 에디터 메인 컴포넌트

#### 2.1 MeshEditor 컴포넌트
```typescript
// src/components/MeshEditor.tsx
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { MeshRenderer } from '../lib/mesh-editor/MeshRenderer';
import { MeshEditHistory } from '../lib/mesh-editor/MeshEditHistory';

interface MeshEditorProps {
  mesh: Mesh;
  texture: string;
  editMode: EditMode;
  onMeshChange: (newMeshData: MeshData) => void;
  onSelectionChange: (selectedVertices: number[]) => void;
}

export const MeshEditor: React.FC<MeshEditorProps> = ({
  mesh,
  texture,
  editMode,
  onMeshChange,
  onSelectionChange
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<MeshRenderer | null>(null);
  const historyRef = useRef<MeshEditHistory>(new MeshEditHistory());
  
  const [renderMode, setRenderMode] = useState<RenderMode>({
    showWireframe: true,
    showVertices: true,
    showWeights: false,
    useCustomShader: false,
    opacity: 1.0,
    tint: 0xffffff,
  });
  
  const [selectedVertices, setSelectedVertices] = useState<Set<number>>(new Set());
  const [isEditing, setIsEditing] = useState(false);
  
  // 렌더러 초기화
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const renderer = new MeshRenderer(canvasRef.current, 800, 600);
    rendererRef.current = renderer;
    
    // 이벤트 리스너 설정
    renderer.on('vertex-drag-start', handleVertexDragStart);
    renderer.on('vertex-drag', handleVertexDrag);
    renderer.on('vertex-drag-end', handleVertexDragEnd);
    
    return () => {
      renderer.dispose();
    };
  }, []);
  
  // 메시 데이터 변경 시 렌더링 업데이트
  useEffect(() => {
    if (!rendererRef.current || !mesh?.data) return;
    
    const textureObj = PIXI.Texture.from(texture);
    rendererRef.current.renderMesh(mesh.data, textureObj, renderMode);
  }, [mesh, texture, renderMode]);
  
  const handleVertexDragStart = useCallback((event: any) => {
    const { vertexIndex } = event;
    
    if (!selectedVertices.has(vertexIndex)) {
      // 새로운 선택
      const newSelection = editMode.multiSelect 
        ? new Set([...selectedVertices, vertexIndex])
        : new Set([vertexIndex]);
      
      setSelectedVertices(newSelection);
      onSelectionChange(Array.from(newSelection));
    }
    
    setIsEditing(true);
    
    // 언두를 위한 상태 저장
    historyRef.current.saveState(mesh.data);
  }, [selectedVertices, editMode, onSelectionChange, mesh]);
  
  const handleVertexDrag = useCallback((event: any) => {
    if (!isEditing) return;
    
    const { vertexIndex, position } = event;
    
    // 메시 데이터 업데이트
    const newMeshData = { ...mesh.data };
    newMeshData.vertices[vertexIndex * 2] = position.x;
    newMeshData.vertices[vertexIndex * 2 + 1] = position.y;
    
    // 다중 선택된 버텍스들도 함께 이동
    if (selectedVertices.size > 1 && selectedVertices.has(vertexIndex)) {
      const deltaX = position.x - mesh.data.vertices[vertexIndex * 2];
      const deltaY = position.y - mesh.data.vertices[vertexIndex * 2 + 1];
      
      selectedVertices.forEach(vIndex => {
        if (vIndex !== vertexIndex) {
          newMeshData.vertices[vIndex * 2] += deltaX;
          newMeshData.vertices[vIndex * 2 + 1] += deltaY;
        }
      });
    }
    
    onMeshChange(newMeshData);
  }, [isEditing, selectedVertices, mesh, onMeshChange]);
  
  const handleVertexDragEnd = useCallback((event: any) => {
    setIsEditing(false);
    
    // 언두 히스토리에 추가
    historyRef.current.addOperation({
      type: 'vertex-move',
      data: event,
      timestamp: Date.now(),
      beforeState: historyRef.current.getLastSavedState(),
      afterState: mesh.data
    });
  }, [mesh]);
  
  const undo = useCallback(() => {
    const previousState = historyRef.current.undo();
    if (previousState) {
      onMeshChange(previousState);
    }
  }, [onMeshChange]);
  
  const redo = useCallback(() => {
    const nextState = historyRef.current.redo();
    if (nextState) {
      onMeshChange(nextState);
    }
  }, [onMeshChange]);
  
  const resetView = useCallback(() => {
    if (rendererRef.current) {
      rendererRef.current.resetView();
    }
  }, []);
  
  const exportMesh = useCallback(() => {
    // 메시 데이터를 서버에 저장
    onMeshChange(mesh.data);
  }, [mesh, onMeshChange]);
  
  return (
    <div className="mesh-editor">
      <div className="editor-toolbar">
        <div className="tool-group">
          <button 
            className={`tool-button ${editMode.tool === 'select' ? 'active' : ''}`}
            onClick={() => setEditMode({ ...editMode, tool: 'select' })}
            title="선택 도구"
          >
            <SelectIcon />
          </button>
          
          <button 
            className={`tool-button ${editMode.tool === 'move' ? 'active' : ''}`}
            onClick={() => setEditMode({ ...editMode, tool: 'move' })}
            title="이동 도구"
          >
            <MoveIcon />
          </button>
          
          <button 
            className={`tool-button ${editMode.tool === 'add' ? 'active' : ''}`}
            onClick={() => setEditMode({ ...editMode, tool: 'add' })}
            title="버텍스 추가"
          >
            <AddIcon />
          </button>
          
          <button 
            className={`tool-button ${editMode.tool === 'delete' ? 'active' : ''}`}
            onClick={() => setEditMode({ ...editMode, tool: 'delete' })}
            title="버텍스 삭제"
          >
            <DeleteIcon />
          </button>
        </div>
        
        <div className="view-group">
          <button 
            className={`view-button ${renderMode.showWireframe ? 'active' : ''}`}
            onClick={() => setRenderMode({ ...renderMode, showWireframe: !renderMode.showWireframe })}
            title="와이어프레임 표시"
          >
            <WireframeIcon />
          </button>
          
          <button 
            className={`view-button ${renderMode.showVertices ? 'active' : ''}`}
            onClick={() => setRenderMode({ ...renderMode, showVertices: !renderMode.showVertices })}
            title="버텍스 표시"
          >
            <VerticesIcon />
          </button>
          
          <button onClick={resetView} title="뷰 리셋">
            <ResetViewIcon />
          </button>
        </div>
        
        <div className="action-group">
          <button 
            onClick={undo} 
            disabled={!historyRef.current.canUndo()}
            title="실행 취소 (Ctrl+Z)"
          >
            <UndoIcon />
          </button>
          
          <button 
            onClick={redo} 
            disabled={!historyRef.current.canRedo()}
            title="다시 실행 (Ctrl+Y)"
          >
            <RedoIcon />
          </button>
          
          <button onClick={exportMesh} title="메시 저장">
            <SaveIcon />
          </button>
        </div>
      </div>
      
      <div className="editor-viewport">
        <canvas ref={canvasRef} className="mesh-canvas" />
        
        {selectedVertices.size > 0 && (
          <div className="selection-info">
            선택된 버텍스: {selectedVertices.size}개
          </div>
        )}
      </div>
      
      <div className="editor-status">
        <span>모드: {editMode.tool}</span>
        <span>줌: {Math.round((rendererRef.current?.getZoom() || 1) * 100)}%</span>
        <span>버텍스: {mesh?.data?.vertices.length / 2 || 0}개</span>
        <span>삼각형: {mesh?.data?.triangles.length / 3 || 0}개</span>
      </div>
    </div>
  );
};
```

#### 2.2 메시 편집 히스토리 관리
```typescript
// src/lib/mesh-editor/MeshEditHistory.ts
export class MeshEditHistory {
  private history: MeshData[] = [];
  private currentIndex: number = -1;
  private maxHistorySize: number = 50;
  private savedState: MeshData | null = null;
  
  saveState(meshData: MeshData) {
    this.savedState = this.cloneMeshData(meshData);
  }
  
  getLastSavedState(): MeshData | null {
    return this.savedState;
  }
  
  addOperation(operation: EditOperation) {
    // 현재 인덱스 이후의 히스토리 제거
    this.history = this.history.slice(0, this.currentIndex + 1);
    
    // 새로운 상태 추가
    this.history.push(this.cloneMeshData(operation.afterState));
    this.currentIndex++;
    
    // 히스토리 크기 제한
    if (this.history.length > this.maxHistorySize) {
      this.history.shift();
      this.currentIndex--;
    }
  }
  
  undo(): MeshData | null {
    if (this.canUndo()) {
      this.currentIndex--;
      return this.cloneMeshData(this.history[this.currentIndex]);
    }
    return null;
  }
  
  redo(): MeshData | null {
    if (this.canRedo()) {
      this.currentIndex++;
      return this.cloneMeshData(this.history[this.currentIndex]);
    }
    return null;
  }
  
  canUndo(): boolean {
    return this.currentIndex > 0;
  }
  
  canRedo(): boolean {
    return this.currentIndex < this.history.length - 1;
  }
  
  clear() {
    this.history = [];
    this.currentIndex = -1;
    this.savedState = null;
  }
  
  private cloneMeshData(meshData: MeshData): MeshData {
    return {
      vertices: new Float32Array(meshData.vertices),
      triangles: new Uint16Array(meshData.triangles),
      uvs: new Float32Array(meshData.uvs),
      bounds: { ...meshData.bounds }
    };
  }
}
```

### 3. 고급 편집 도구

#### 3.1 버텍스 추가/삭제 도구
```typescript
// src/lib/mesh-editor/MeshEditTools.ts
export class MeshEditTools {
  constructor(private renderer: MeshRenderer, private onMeshChange: (mesh: MeshData) => void) {}
  
  addVertex(position: { x: number, y: number }, meshData: MeshData): MeshData {
    // 새 버텍스 추가
    const newVertices = new Float32Array(meshData.vertices.length + 2);
    newVertices.set(meshData.vertices);
    newVertices[meshData.vertices.length] = position.x;
    newVertices[meshData.vertices.length + 1] = position.y;
    
    // UV 좌표 계산 (바운드 기준)
    const newUvs = new Float32Array(meshData.uvs.length + 2);
    newUvs.set(meshData.uvs);
    newUvs[meshData.uvs.length] = (position.x - meshData.bounds.x) / meshData.bounds.width;
    newUvs[meshData.uvs.length + 1] = 1.0 - (position.y - meshData.bounds.y) / meshData.bounds.height;
    
    // 새 버텍스를 포함하도록 삼각분할 재계산
    const newTriangles = this.retriangulate(newVertices);
    
    return {
      vertices: newVertices,
      triangles: newTriangles,
      uvs: newUvs,
      bounds: this.calculateBounds(newVertices)
    };
  }
  
  deleteVertex(vertexIndex: number, meshData: MeshData): MeshData {
    if (meshData.vertices.length <= 6) { // 최소 3개 버텍스 유지
      throw new Error('Cannot delete vertex: minimum 3 vertices required');
    }
    
    // 버텍스 제거
    const newVertices = new Float32Array(meshData.vertices.length - 2);
    const newUvs = new Float32Array(meshData.uvs.length - 2);
    
    let newIndex = 0;
    for (let i = 0; i < meshData.vertices.length / 2; i++) {
      if (i !== vertexIndex) {
        newVertices[newIndex * 2] = meshData.vertices[i * 2];
        newVertices[newIndex * 2 + 1] = meshData.vertices[i * 2 + 1];
        newUvs[newIndex * 2] = meshData.uvs[i * 2];
        newUvs[newIndex * 2 + 1] = meshData.uvs[i * 2 + 1];
        newIndex++;
      }
    }
    
    // 삼각형 인덱스 재조정
    const newTriangles = this.retriangulate(newVertices);
    
    return {
      vertices: newVertices,
      triangles: newTriangles,
      uvs: newUvs,
      bounds: this.calculateBounds(newVertices)
    };
  }
  
  private retriangulate(vertices: Float32Array): Uint16Array {
    // Earcut 알고리즘을 사용한 삼각분할
    const earcut = require('earcut');
    
    const indices = earcut(Array.from(vertices));
    return new Uint16Array(indices);
  }
  
  private calculateBounds(vertices: Float32Array): { x: number, y: number, width: number, height: number } {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    
    for (let i = 0; i < vertices.length; i += 2) {
      const x = vertices[i];
      const y = vertices[i + 1];
      
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    }
    
    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY
    };
  }
  
  snapToGrid(position: { x: number, y: number }, gridSize: number): { x: number, y: number } {
    return {
      x: Math.round(position.x / gridSize) * gridSize,
      y: Math.round(position.y / gridSize) * gridSize
    };
  }
  
  validateMeshTopology(meshData: MeshData): { isValid: boolean, errors: string[] } {
    const errors: string[] = [];
    
    // 최소 버텍스 수 확인
    if (meshData.vertices.length < 6) {
      errors.push('Minimum 3 vertices required');
    }
    
    // 삼각형 인덱스 유효성 확인
    const vertexCount = meshData.vertices.length / 2;
    for (let i = 0; i < meshData.triangles.length; i++) {
      if (meshData.triangles[i] >= vertexCount) {
        errors.push(`Invalid triangle index: ${meshData.triangles[i]}`);
      }
    }
    
    // 중복 버텍스 확인
    const vertexMap = new Map();
    for (let i = 0; i < meshData.vertices.length; i += 2) {
      const key = `${meshData.vertices[i]},${meshData.vertices[i + 1]}`;
      if (vertexMap.has(key)) {
        errors.push(`Duplicate vertex at (${meshData.vertices[i]}, ${meshData.vertices[i + 1]})`);
      }
      vertexMap.set(key, true);
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
}
```

### 4. 품질 분석 및 최적화 도구

#### 4.1 메시 품질 분석기
```typescript
// src/lib/mesh-editor/MeshQualityAnalyzer.ts
export class MeshQualityAnalyzer {
  
  analyzeMesh(meshData: MeshData): MeshQualityReport {
    const triangleCount = meshData.triangles.length / 3;
    const vertexCount = meshData.vertices.length / 2;
    
    return {
      vertexCount,
      triangleCount,
      aspectRatio: this.calculateAspectRatios(meshData),
      triangleArea: this.calculateTriangleAreas(meshData),
      edgeLength: this.calculateEdgeLengths(meshData),
      meshDensity: this.calculateMeshDensity(meshData),
      qualityScore: this.calculateOverallQuality(meshData)
    };
  }
  
  private calculateAspectRatios(meshData: MeshData): { min: number, max: number, average: number } {
    const ratios: number[] = [];
    
    for (let i = 0; i < meshData.triangles.length; i += 3) {
      const triangle = this.getTriangleVertices(meshData, i);
      const ratio = this.calculateTriangleAspectRatio(triangle);
      ratios.push(ratio);
    }
    
    return {
      min: Math.min(...ratios),
      max: Math.max(...ratios),
      average: ratios.reduce((sum, r) => sum + r, 0) / ratios.length
    };
  }
  
  private calculateTriangleAspectRatio(triangle: { v1: Point, v2: Point, v3: Point }): number {
    const edges = [
      this.distance(triangle.v1, triangle.v2),
      this.distance(triangle.v2, triangle.v3),
      this.distance(triangle.v3, triangle.v1)
    ];
    
    const maxEdge = Math.max(...edges);
    const minEdge = Math.min(...edges);
    
    return maxEdge / minEdge;
  }
  
  private calculateTriangleAreas(meshData: MeshData): { min: number, max: number, average: number, total: number } {
    const areas: number[] = [];
    
    for (let i = 0; i < meshData.triangles.length; i += 3) {
      const triangle = this.getTriangleVertices(meshData, i);
      const area = this.calculateTriangleArea(triangle);
      areas.push(area);
    }
    
    return {
      min: Math.min(...areas),
      max: Math.max(...areas),
      average: areas.reduce((sum, a) => sum + a, 0) / areas.length,
      total: areas.reduce((sum, a) => sum + a, 0)
    };
  }
  
  private calculateTriangleArea(triangle: { v1: Point, v2: Point, v3: Point }): number {
    // 외적을 사용한 삼각형 넓이 계산
    const { v1, v2, v3 } = triangle;
    return Math.abs(
      (v2.x - v1.x) * (v3.y - v1.y) - (v3.x - v1.x) * (v2.y - v1.y)
    ) / 2;
  }
  
  private calculateMeshDensity(meshData: MeshData): number {
    const bounds = meshData.bounds;
    const totalArea = bounds.width * bounds.height;
    const triangleCount = meshData.triangles.length / 3;
    
    return triangleCount / totalArea; // 단위 면적당 삼각형 수
  }
  
  private calculateOverallQuality(meshData: MeshData): number {
    // 0-100 점수로 전체적인 메시 품질 평가
    const aspectRatios = this.calculateAspectRatios(meshData);
    const areas = this.calculateTriangleAreas(meshData);
    
    // 좋은 메시의 특징:
    // - 균등한 삼각형 크기 (낮은 면적 분산)
    // - 정삼각형에 가까운 형태 (낮은 aspect ratio)
    // - 적절한 버텍스 밀도
    
    const aspectScore = Math.max(0, 100 - (aspectRatios.average - 1) * 50);
    const areaVariance = this.calculateVariance(this.getTriangleAreas(meshData));
    const areaScore = Math.max(0, 100 - areaVariance / areas.average * 100);
    
    return (aspectScore + areaScore) / 2;
  }
  
  private getTriangleVertices(meshData: MeshData, triangleStartIndex: number) {
    const i1 = meshData.triangles[triangleStartIndex] * 2;
    const i2 = meshData.triangles[triangleStartIndex + 1] * 2;
    const i3 = meshData.triangles[triangleStartIndex + 2] * 2;
    
    return {
      v1: { x: meshData.vertices[i1], y: meshData.vertices[i1 + 1] },
      v2: { x: meshData.vertices[i2], y: meshData.vertices[i2 + 1] },
      v3: { x: meshData.vertices[i3], y: meshData.vertices[i3 + 1] }
    };
  }
  
  private distance(p1: Point, p2: Point): number {
    return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
  }
}

interface MeshQualityReport {
  vertexCount: number;
  triangleCount: number;
  aspectRatio: { min: number, max: number, average: number };
  triangleArea: { min: number, max: number, average: number, total: number };
  edgeLength: { min: number, max: number, average: number };
  meshDensity: number;
  qualityScore: number;
}

interface Point {
  x: number;
  y: number;
}
```

### 5. 키보드 단축키 및 접근성

#### 5.1 키보드 이벤트 핸들러
```typescript
// src/hooks/useMeshEditorKeyboard.ts
import { useEffect, useCallback } from 'react';

export const useMeshEditorKeyboard = (
  meshEditor: MeshEditor | null,
  isActive: boolean
) => {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!isActive || !meshEditor) return;
    
    const { ctrlKey, shiftKey, altKey, key } = event;
    
    // 기본 단축키들
    if (ctrlKey && key === 'z' && !shiftKey) {
      event.preventDefault();
      meshEditor.undo();
    } else if ((ctrlKey && key === 'y') || (ctrlKey && shiftKey && key === 'z')) {
      event.preventDefault();
      meshEditor.redo();
    } else if (ctrlKey && key === 'a') {
      event.preventDefault();
      meshEditor.selectAll();
    } else if (key === 'Delete' || key === 'Backspace') {
      event.preventDefault();
      meshEditor.deleteSelected();
    }
    
    // 도구 선택 단축키
    switch (key) {
      case '1':
        meshEditor.setTool('select');
        break;
      case '2':
        meshEditor.setTool('move');
        break;
      case '3':
        meshEditor.setTool('add');
        break;
      case '4':
        meshEditor.setTool('delete');
        break;
    }
    
    // 뷰 조작 단축키
    if (key === 'r' && !ctrlKey) {
      meshEditor.resetView();
    } else if (key === 'f') {
      meshEditor.frameSelected();
    }
    
    // 표시 모드 토글
    if (key === 'w') {
      meshEditor.toggleWireframe();
    } else if (key === 'v') {
      meshEditor.toggleVertices();
    }
    
  }, [isActive, meshEditor]);
  
  useEffect(() => {
    if (isActive) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isActive, handleKeyDown]);
};
```

## 성능 최적화 전략

### 1. WebGL 렌더링 최적화
- **인스턴싱**: 동일한 지오메트리 재사용
- **LOD**: 거리에 따른 상세도 조절
- **프러스텀 컬링**: 뷰포트 밖 오브젝트 제외
- **배치 렌더링**: 드로우 콜 최소화

### 2. 메모리 관리
- **오브젝트 풀링**: 자주 생성/삭제되는 오브젝트 재사용
- **지오메트리 캐싱**: 메시 지오메트리 캐시
- **텍스처 압축**: WebGL 압축 텍스처 포맷 활용

### 3. 상호작용 최적화
- **공간 분할**: 버텍스 선택을 위한 공간 인덱싱
- **이벤트 디바운싱**: 연속적인 편집 작업 최적화
- **차분 업데이트**: 변경된 부분만 업데이트

## 구현 로드맵

### Week 1-2: WebGL 렌더링 시스템
- [x] PIXI.js 기반 MeshRenderer 구현
- [x] 기본 메시 렌더링 및 와이어프레임
- [x] 뷰포트 조작 (줌, 팬, 회전)

### Week 3: 버텍스 편집 시스템
- [x] 버텍스 선택 및 드래그 앤 드롭
- [x] 다중 선택 및 그룹 편집
- [x] 실시간 메시 업데이트

### Week 4: 고급 편집 도구
- [x] 버텍스 추가/삭제 도구
- [x] 메시 토폴로지 검증
- [x] 언두/리두 시스템

### Week 5: 품질 분석 및 UI
- [x] 메시 품질 분석기
- [x] 편집 히스토리 관리
- [x] 키보드 단축키 시스템

## 성공 지표

1. **성능**: 1000+ 버텍스에서 60fps 유지
2. **사용성**: 직관적인 버텍스 편집 워크플로우
3. **안정성**: 메시 토폴로지 무결성 보장
4. **호환성**: 다양한 브라우저에서 동작