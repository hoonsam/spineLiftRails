# Spine JSON 익스포트 기능 명세서

## 개요

현재 SpineLift Rails에서는 메시 데이터만 저장되고 있으며, Spine 런타임에서 실제로 사용할 수 있는 완전한 Spine JSON 파일을 생성하는 기능이 없습니다. 이 명세서는 Spine 3.8.95 표준에 완전히 호환되는 JSON, Atlas, 텍스처 파일을 생성하고 패키지로 다운로드할 수 있는 기능을 정의합니다.

**담당 영역**: 백엔드 생성 로직, 프론트엔드 UI, Python 서비스  
**우선순위**: Medium  
**예상 구현 시간**: 3-4주  
**의존성**: 본 시스템 완료 후 구현  

## 현재 상태 분석

### 기존 구현의 한계
- 메시 데이터만 JSON으로 저장 (`mesh.data` 필드)
- Spine 런타임 호환 JSON 구조 없음
- Atlas(.atlas) 파일 생성 없음
- 텍스처 아틀라스 패킹 기능 없음
- 다운로드 가능한 패키지 생성 없음

### Spine 3.8.95 요구 사항
완전한 Spine 프로젝트는 다음 파일들로 구성됩니다:
```
character.json      # 또는 .skel (바이너리)
character.atlas     # 텍스처 아틀라스 정보
character.png       # 패킹된 텍스처 이미지
```

## 기능 요구사항

### 1. Spine JSON 구조 정의

#### 1.1 완전한 Spine JSON 스키마
```typescript
interface SpineData {
  skeleton: {
    hash: string;
    spine: string;        // "3.8.95"
    x: number;
    y: number;
    width: number;
    height: number;
    images?: string;      // 이미지 폴더 경로
    audio?: string;       // 오디오 폴더 경로
  };
  bones: BoneData[];
  slots: SlotData[];
  skins: {
    [skinName: string]: {
      [slotName: string]: {
        [attachmentName: string]: AttachmentData;
      };
    };
  };
  events?: { [eventName: string]: EventData };
  animations?: { [animationName: string]: AnimationData };
}

interface BoneData {
  name: string;
  parent?: string;
  length?: number;
  x?: number;
  y?: number;
  rotation?: number;
  scaleX?: number;
  scaleY?: number;
  shearX?: number;
  shearY?: number;
  inheritRotation?: boolean;
  inheritScale?: boolean;
  color?: string;
}

interface SlotData {
  name: string;
  bone: string;
  color?: string;
  dark?: string;
  attachment?: string;
  blend?: string;
}

interface AttachmentData {
  type?: 'region' | 'mesh' | 'linkedmesh' | 'boundingbox' | 'path' | 'point' | 'clipping';
  name?: string;
  path?: string;
  x?: number;
  y?: number;
  scaleX?: number;
  scaleY?: number;
  rotation?: number;
  width?: number;
  height?: number;
  color?: string;
  
  // 메시 전용 속성
  triangles?: number[];
  vertices?: number[];
  uvs?: number[];
  hull?: number;
  edges?: number[];
}
```

#### 1.2 Atlas 파일 구조
```typescript
interface AtlasData {
  pages: AtlasPage[];
  regions: AtlasRegion[];
}

interface AtlasPage {
  name: string;         // "character.png"
  size: [number, number]; // [2048, 2048]
  format: string;       // "RGBA8888"
  filter: [string, string]; // ["Linear", "Linear"]
  repeat: string;       // "none"
}

interface AtlasRegion {
  name: string;         // 레이어 이름
  rotate: boolean;
  xy: [number, number]; // 아틀라스 내 위치
  size: [number, number]; // 원본 크기
  orig: [number, number]; // 원본 크기
  offset: [number, number]; // 오프셋
  index: number;
}
```

### 2. 백엔드 익스포트 서비스

#### 2.1 SpineExportService 구현
```ruby
# app/services/spine_export_service.rb
class SpineExportService
  def initialize(project)
    @project = project
    @temp_dir = Dir.mktmpdir("spine_export_#{@project.id}")
  end
  
  def generate_spine_package
    # 1. Spine JSON 생성
    spine_json = generate_spine_json
    
    # 2. 텍스처 아틀라스 생성
    atlas_data = generate_texture_atlas
    
    # 3. 파일들을 임시 디렉토리에 저장
    save_spine_files(spine_json, atlas_data)
    
    # 4. ZIP 패키지 생성
    package_path = create_zip_package
    
    # 5. 정리
    cleanup_temp_files
    
    package_path
  end
  
  private
  
  def generate_spine_json
    {
      skeleton: generate_skeleton_data,
      bones: generate_bones_data,
      slots: generate_slots_data,
      skins: generate_skins_data,
      events: {},
      animations: generate_animations_data
    }
  end
  
  def generate_skeleton_data
    bounds = calculate_project_bounds
    
    {
      hash: generate_content_hash,
      spine: "3.8.95",
      x: bounds[:x],
      y: bounds[:y], 
      width: bounds[:width],
      height: bounds[:height],
      images: "./images/",
      audio: "./audio/"
    }
  end
  
  def generate_bones_data
    @project.bones.order(:order_index).map do |bone|
      bone_data = {
        name: bone.name
      }
      
      bone_data[:parent] = bone.parent_bone.name if bone.parent_bone
      bone_data[:length] = bone.length if bone.length > 0
      bone_data[:x] = bone.x if bone.x != 0
      bone_data[:y] = bone.y if bone.y != 0
      bone_data[:rotation] = bone.rotation if bone.rotation != 0
      bone_data[:scaleX] = bone.scale_x if bone.scale_x != 1
      bone_data[:scaleY] = bone.scale_y if bone.scale_y != 1
      
      bone_data
    end
  end
  
  def generate_slots_data
    @project.layers.order(:position).map do |layer|
      {
        name: layer.name,
        bone: find_primary_bone_for_layer(layer)&.name || "root",
        attachment: layer.name
      }
    end
  end
  
  def generate_skins_data
    default_skin = {}
    
    @project.layers.includes(:mesh).each do |layer|
      next unless layer.mesh
      
      slot_name = layer.name
      attachment_name = layer.name
      
      default_skin[slot_name] = {
        attachment_name => generate_attachment_data(layer)
      }
    end
    
    { "default" => default_skin }
  end
  
  def generate_attachment_data(layer)
    mesh = layer.mesh
    mesh_data = JSON.parse(mesh.data)
    
    attachment = {
      type: "mesh",
      name: layer.name,
      path: layer.name,
      vertices: flatten_vertices_with_weights(mesh_data['vertices'], layer),
      triangles: mesh_data['triangles'].flatten,
      uvs: mesh_data['uvs'].flatten,
      hull: calculate_hull_vertex_count(mesh_data['vertices'])
    }
    
    # 색상 정보 추가 (레이어 메타데이터에서)
    if layer.metadata && layer.metadata['color']
      attachment[:color] = layer.metadata['color']
    end
    
    attachment
  end
  
  def flatten_vertices_with_weights(vertices, layer)
    flattened = []
    
    vertices.each_with_index do |(x, y), index|
      # 버텍스 위치
      flattened << x << y
      
      # Weight 정보 추가
      vertex_weights = get_vertex_weights(layer, index)
      vertex_weights.each do |bone_index, weight|
        flattened << bone_index << weight
      end
    end
    
    flattened
  end
  
  def get_vertex_weights(layer, vertex_index)
    # BoneWeight 테이블에서 해당 버텍스의 Weight 정보 가져오기
    vertex = layer.mesh.vertices.find_by(index: vertex_index)
    return [] unless vertex
    
    weights = []
    vertex.bone_weights.significant.each do |bw|
      bone_index = @project.bones.order(:order_index).index(bw.bone)
      weights << [bone_index, bw.weight] if bone_index
    end
    
    weights
  end
end
```

#### 2.2 텍스처 아틀라스 생성 서비스
```ruby
# app/services/texture_atlas_service.rb  
class TextureAtlasService
  def initialize(project)
    @project = project
    @atlas_size = [2048, 2048] # 기본 아틀라스 크기
    @padding = 2 # 텍스처 간 패딩
  end
  
  def generate_atlas
    layers_with_images = @project.layers.includes(image_attachment: :blob)
                                     .where.not(image_attachments: { id: nil })
    
    # 1. 이미지 크기 정보 수집
    image_infos = collect_image_infos(layers_with_images)
    
    # 2. 패킹 알고리즘으로 배치 계산
    packed_layout = calculate_packing_layout(image_infos)
    
    # 3. 아틀라스 이미지 생성
    atlas_image_path = create_atlas_image(packed_layout)
    
    # 4. Atlas 파일 생성
    atlas_file_content = generate_atlas_file(packed_layout)
    
    {
      atlas_image_path: atlas_image_path,
      atlas_content: atlas_file_content,
      regions: packed_layout
    }
  end
  
  private
  
  def collect_image_infos(layers)
    layers.map do |layer|
      image_blob = layer.image.blob
      
      # ImageProcessing을 사용해 이미지 크기 확인
      analyzer = ActiveStorage::Analyzer::ImageAnalyzer.new(image_blob)
      metadata = analyzer.metadata
      
      {
        layer: layer,
        name: layer.name,
        width: metadata[:width],
        height: metadata[:height],
        blob: image_blob
      }
    end
  end
  
  def calculate_packing_layout(image_infos)
    # Bin packing 알고리즘 구현 (Bottom-Left-Fill)
    packer = BinPacker.new(@atlas_size[0], @atlas_size[1])
    
    # 큰 이미지부터 먼저 패킹
    sorted_images = image_infos.sort_by { |info| -(info[:width] * info[:height]) }
    
    packed_layout = []
    
    sorted_images.each do |image_info|
      position = packer.pack(
        image_info[:width] + @padding * 2,
        image_info[:height] + @padding * 2
      )
      
      if position
        packed_layout << {
          layer: image_info[:layer],
          name: image_info[:name],
          x: position[:x] + @padding,
          y: position[:y] + @padding,
          width: image_info[:width],
          height: image_info[:height],
          blob: image_info[:blob]
        }
      else
        raise "Cannot fit image #{image_info[:name]} in atlas"
      end
    end
    
    packed_layout
  end
  
  def create_atlas_image(packed_layout)
    require 'mini_magick'
    
    # 빈 아틀라스 이미지 생성
    atlas = MiniMagick::Image.create(".png", false) do |c|
      c.size "#{@atlas_size[0]}x#{@atlas_size[1]}"
      c.canvas "transparent"
    end
    
    # 각 레이어 이미지를 아틀라스에 합성
    packed_layout.each do |region|
      # 레이어 이미지를 임시 파일로 저장
      temp_image_path = save_blob_to_temp_file(region[:blob])
      
      # ImageMagick으로 아틀라스에 합성
      atlas = atlas.composite(MiniMagick::Image.open(temp_image_path)) do |c|
        c.compose "Over"
        c.geometry "+#{region[:x]}+#{region[:y]}"
      end
      
      # 임시 파일 정리
      File.delete(temp_image_path)
    end
    
    # 아틀라스 이미지 저장
    atlas_path = Rails.root.join("tmp", "atlas_#{@project.id}.png")
    atlas.write(atlas_path)
    
    atlas_path.to_s
  end
  
  def generate_atlas_file(packed_layout)
    atlas_content = []
    
    # 아틀라스 페이지 정보
    atlas_content << "atlas_#{@project.id}.png"
    atlas_content << "size: #{@atlas_size[0]}, #{@atlas_size[1]}"
    atlas_content << "format: RGBA8888"
    atlas_content << "filter: Linear, Linear"
    atlas_content << "repeat: none"
    atlas_content << ""
    
    # 각 리전 정보
    packed_layout.each do |region|
      atlas_content << region[:name]
      atlas_content << "  rotate: false"
      atlas_content << "  xy: #{region[:x]}, #{region[:y]}"
      atlas_content << "  size: #{region[:width]}, #{region[:height]}"
      atlas_content << "  orig: #{region[:width]}, #{region[:height]}"
      atlas_content << "  offset: 0, 0"
      atlas_content << "  index: -1"
      atlas_content << ""
    end
    
    atlas_content.join("\n")
  end
end
```

#### 2.3 Bin Packing 알고리즘
```ruby
# app/services/bin_packer.rb
class BinPacker
  def initialize(width, height)
    @width = width
    @height = height
    @free_rects = [{ x: 0, y: 0, width: width, height: height }]
  end
  
  def pack(item_width, item_height)
    # Bottom-Left-Fill 알고리즘
    best_rect = find_best_rect(item_width, item_height)
    return nil unless best_rect
    
    # 사각형을 free_rects에서 제거하고 분할
    @free_rects.delete(best_rect)
    split_free_rect(best_rect, item_width, item_height)
    
    { x: best_rect[:x], y: best_rect[:y] }
  end
  
  private
  
  def find_best_rect(width, height)
    best_rect = nil
    best_y = @height
    best_x = @width
    
    @free_rects.each do |rect|
      if rect[:width] >= width && rect[:height] >= height
        if rect[:y] < best_y || (rect[:y] == best_y && rect[:x] < best_x)
          best_rect = rect
          best_y = rect[:y]
          best_x = rect[:x]
        end
      end
    end
    
    best_rect
  end
  
  def split_free_rect(rect, used_width, used_height)
    # 사용된 사각형을 제외한 나머지 공간을 새로운 free_rects로 분할
    if rect[:width] > used_width
      @free_rects << {
        x: rect[:x] + used_width,
        y: rect[:y],
        width: rect[:width] - used_width,
        height: used_height
      }
    end
    
    if rect[:height] > used_height
      @free_rects << {
        x: rect[:x],
        y: rect[:y] + used_height,
        width: rect[:width],
        height: rect[:height] - used_height
      }
    end
    
    # 겹치는 사각형 제거 및 병합
    merge_free_rects
  end
  
  def merge_free_rects
    # 겹치는 free_rects 정리 (최적화)
    @free_rects.reject! do |rect1|
      @free_rects.any? do |rect2|
        rect1 != rect2 && 
        rect2[:x] <= rect1[:x] && 
        rect2[:y] <= rect1[:y] &&
        rect2[:x] + rect2[:width] >= rect1[:x] + rect1[:width] &&
        rect2[:y] + rect2[:height] >= rect1[:y] + rect1[:height]
      end
    end
  end
end
```

### 3. API 엔드포인트 설계

#### 3.1 익스포트 컨트롤러
```ruby
# app/controllers/api/v1/exports_controller.rb
class Api::V1::ExportsController < Api::V1::BaseController
  before_action :set_project
  
  def spine_json
    export_service = SpineExportService.new(@project)
    spine_data = export_service.generate_spine_json
    
    render json: spine_data
  end
  
  def spine_package
    # 백그라운드에서 패키지 생성
    job = GenerateSpinePackageJob.perform_later(@project.id, current_user.id)
    
    render json: { 
      job_id: job.job_id,
      status: 'processing',
      message: 'Spine package generation started'
    }
  end
  
  def package_status
    job_id = params[:job_id]
    job_status = Sidekiq::Status::status(job_id)
    
    case job_status
    when :complete
      package_path = Sidekiq::Status::get(job_id, 'package_path')
      render json: {
        status: 'completed',
        download_url: rails_blob_url(package_path)
      }
    when :failed
      error_message = Sidekiq::Status::get(job_id, 'error_message')
      render json: {
        status: 'failed',
        error: error_message
      }
    else
      progress = Sidekiq::Status::pct_complete(job_id)
      render json: {
        status: 'processing',
        progress: progress
      }
    end
  end
  
  def download_package
    package = SpineExportPackage.find(params[:package_id])
    
    if package.file.attached?
      redirect_to rails_blob_url(package.file)
    else
      render json: { error: 'Package not found' }, status: :not_found
    end
  end
  
  private
  
  def set_project
    @project = current_user.projects.find(params[:project_id])
  end
end
```

#### 3.2 백그라운드 작업
```ruby
# app/jobs/generate_spine_package_job.rb
class GenerateSpinePackageJob < ApplicationJob
  include Sidekiq::Status::Worker
  
  queue_as :default
  
  def perform(project_id, user_id)
    project = Project.find(project_id)
    user = User.find(user_id)
    
    at(10, 100, "Initializing export...")
    
    begin
      # Spine 익스포트 서비스 실행
      export_service = SpineExportService.new(project)
      
      at(30, 100, "Generating Spine JSON...")
      spine_json = export_service.generate_spine_json
      
      at(60, 100, "Creating texture atlas...")
      atlas_data = TextureAtlasService.new(project).generate_atlas
      
      at(80, 100, "Packaging files...")
      package_path = create_package(project, spine_json, atlas_data)
      
      # 패키지 레코드 저장
      package = create_package_record(project, user, package_path)
      
      at(100, 100, "Export completed!")
      store(package_path: package.file.url)
      
    rescue StandardError => e
      Rails.logger.error "Spine export failed: #{e.message}"
      Rails.logger.error e.backtrace.join("\n")
      
      store(error_message: e.message)
      raise
    end
  end
  
  private
  
  def create_package(project, spine_json, atlas_data)
    temp_dir = Dir.mktmpdir("spine_package_#{project.id}")
    
    begin
      # JSON 파일 저장
      json_path = File.join(temp_dir, "#{project.name}.json")
      File.write(json_path, JSON.pretty_generate(spine_json))
      
      # Atlas 파일 저장
      atlas_path = File.join(temp_dir, "#{project.name}.atlas")
      File.write(atlas_path, atlas_data[:atlas_content])
      
      # 텍스처 이미지 복사
      texture_name = "#{project.name}.png"
      FileUtils.cp(atlas_data[:atlas_image_path], File.join(temp_dir, texture_name))
      
      # ZIP 파일 생성
      zip_path = Rails.root.join("tmp", "#{project.name}_spine.zip")
      create_zip(temp_dir, zip_path)
      
      zip_path
    ensure
      FileUtils.rm_rf(temp_dir)
    end
  end
  
  def create_zip(source_dir, zip_path)
    require 'zip'
    
    Zip::File.open(zip_path, Zip::File::CREATE) do |zipfile|
      Dir.glob(File.join(source_dir, "**", "*")).each do |file|
        next if File.directory?(file)
        
        zipfile.add(File.basename(file), file)
      end
    end
  end
  
  def create_package_record(project, user, package_path)
    package = SpineExportPackage.create!(
      project: project,
      user: user,
      name: "#{project.name}_spine_export",
      spine_version: "3.8.95",
      export_settings: {
        atlas_size: [2048, 2048],
        padding: 2,
        format: "RGBA8888"
      }
    )
    
    package.file.attach(
      io: File.open(package_path),
      filename: File.basename(package_path),
      content_type: "application/zip"
    )
    
    package
  end
end
```

### 4. 프론트엔드 익스포트 UI

#### 4.1 ExportPanel 컴포넌트
```typescript
interface ExportPanelProps {
  projectId: string;
  onExportComplete: (downloadUrl: string) => void;
}

export const ExportPanel: React.FC<ExportPanelProps> = ({
  projectId,
  onExportComplete
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportStatus, setExportStatus] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  
  const startExport = async () => {
    try {
      setIsExporting(true);
      setExportProgress(0);
      setExportStatus('Starting export...');
      
      const response = await api.post(`/projects/${projectId}/exports/spine_package`);
      const { job_id } = response.data;
      setJobId(job_id);
      
      // 진행 상황 폴링
      pollExportStatus(job_id);
      
    } catch (error) {
      console.error('Export failed:', error);
      setIsExporting(false);
      setExportStatus('Export failed');
    }
  };
  
  const pollExportStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await api.get(`/projects/${projectId}/exports/package_status`, {
          params: { job_id: jobId }
        });
        
        const { status, progress, download_url, error } = response.data;
        
        setExportProgress(progress || 0);
        setExportStatus(getStatusMessage(status, progress));
        
        if (status === 'completed' && download_url) {
          setIsExporting(false);
          onExportComplete(download_url);
        } else if (status === 'failed') {
          setIsExporting(false);
          setExportStatus(`Export failed: ${error}`);
        } else if (status === 'processing') {
          setTimeout(poll, 2000); // 2초마다 상태 확인
        }
        
      } catch (error) {
        console.error('Status polling failed:', error);
        setIsExporting(false);
        setExportStatus('Status check failed');
      }
    };
    
    poll();
  };
  
  const getStatusMessage = (status: string, progress?: number): string => {
    switch (status) {
      case 'processing':
        if (progress < 30) return 'Generating Spine JSON...';
        if (progress < 60) return 'Creating texture atlas...';
        if (progress < 80) return 'Packaging files...';
        return 'Finalizing export...';
      case 'completed':
        return 'Export completed!';
      case 'failed':
        return 'Export failed';
      default:
        return 'Starting export...';
    }
  };
  
  return (
    <div className="export-panel">
      <div className="export-header">
        <h3>Spine 익스포트</h3>
        <p>Spine 런타임에서 사용할 수 있는 파일들을 생성합니다.</p>
      </div>
      
      <div className="export-settings">
        <div className="setting-group">
          <label>Spine 버전</label>
          <select defaultValue="3.8.95">
            <option value="3.8.95">3.8.95 (권장)</option>
            <option value="4.0.64">4.0.64</option>
          </select>
        </div>
        
        <div className="setting-group">
          <label>아틀라스 크기</label>
          <select defaultValue="2048">
            <option value="1024">1024x1024</option>
            <option value="2048">2048x2048</option>
            <option value="4096">4096x4096</option>
          </select>
        </div>
        
        <div className="setting-group">
          <label>텍스처 포맷</label>
          <select defaultValue="RGBA8888">
            <option value="RGBA8888">RGBA8888</option>
            <option value="RGB888">RGB888</option>
          </select>
        </div>
      </div>
      
      <div className="export-actions">
        <button 
          onClick={startExport} 
          disabled={isExporting}
          className="export-button"
        >
          {isExporting ? 'Exporting...' : 'Export Spine Package'}
        </button>
      </div>
      
      {isExporting && (
        <div className="export-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${exportProgress}%` }}
            />
          </div>
          <div className="progress-text">
            {exportStatus} ({exportProgress}%)
          </div>
        </div>
      )}
    </div>
  );
};
```

#### 4.2 ExportHistory 컴포넌트
```typescript
interface ExportHistoryProps {
  projectId: string;
}

export const ExportHistory: React.FC<ExportHistoryProps> = ({ projectId }) => {
  const [exports, setExports] = useState<SpineExportPackage[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadExportHistory();
  }, [projectId]);
  
  const loadExportHistory = async () => {
    try {
      const response = await api.get(`/projects/${projectId}/exports`);
      setExports(response.data.exports);
    } catch (error) {
      console.error('Failed to load export history:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const downloadExport = (exportPackage: SpineExportPackage) => {
    window.open(exportPackage.download_url, '_blank');
  };
  
  if (loading) {
    return <div className="loading">Loading export history...</div>;
  }
  
  return (
    <div className="export-history">
      <h4>익스포트 히스토리</h4>
      
      {exports.length === 0 ? (
        <p className="no-exports">아직 익스포트된 파일이 없습니다.</p>
      ) : (
        <div className="export-list">
          {exports.map(exportPackage => (
            <div key={exportPackage.id} className="export-item">
              <div className="export-info">
                <h5>{exportPackage.name}</h5>
                <p>Spine {exportPackage.spine_version}</p>
                <p>{new Date(exportPackage.created_at).toLocaleDateString()}</p>
              </div>
              
              <div className="export-actions">
                <button onClick={() => downloadExport(exportPackage)}>
                  다운로드
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

### 5. 데이터베이스 스키마

#### 5.1 SpineExportPackage 모델
```ruby
# db/migrate/create_spine_export_packages.rb
class CreateSpineExportPackages < ActiveRecord::Migration[7.0]
  def change
    create_table :spine_export_packages do |t|
      t.references :project, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true
      
      t.string :name, null: false
      t.string :spine_version, null: false, default: '3.8.95'
      t.jsonb :export_settings, default: {}
      t.integer :file_size, default: 0
      t.string :status, default: 'pending'
      t.text :error_message
      
      t.timestamps
    end
    
    add_index :spine_export_packages, [:project_id, :created_at]
    add_index :spine_export_packages, :status
  end
end

# app/models/spine_export_package.rb
class SpineExportPackage < ApplicationRecord
  belongs_to :project
  belongs_to :user
  has_one_attached :file
  
  enum status: {
    pending: 0,
    processing: 1, 
    completed: 2,
    failed: 3
  }
  
  validates :name, presence: true
  validates :spine_version, presence: true
  
  def download_url
    return unless file.attached?
    Rails.application.routes.url_helpers.rails_blob_url(file)
  end
  
  def file_size_mb
    (file_size / 1_048_576.0).round(2) if file_size > 0
  end
end
```

## 테스트 전략

### 1. 단위 테스트
```ruby
# spec/services/spine_export_service_spec.rb
RSpec.describe SpineExportService do
  let(:project) { create(:project) }
  let(:bone) { create(:bone, project: project, name: 'root') }
  let(:layer) { create(:layer, project: project) }
  let(:mesh) { create(:mesh, layer: layer) }
  
  subject { described_class.new(project) }
  
  describe '#generate_spine_json' do
    before do
      # 테스트 데이터 설정
      bone
      layer
      mesh
    end
    
    it 'generates valid Spine JSON structure' do
      result = subject.send(:generate_spine_json)
      
      expect(result).to have_key(:skeleton)
      expect(result).to have_key(:bones)
      expect(result).to have_key(:slots)
      expect(result).to have_key(:skins)
      
      expect(result[:skeleton][:spine]).to eq('3.8.95')
      expect(result[:bones]).to be_an(Array)
      expect(result[:bones].first[:name]).to eq('root')
    end
  end
  
  describe '#generate_bones_data' do
    let!(:root_bone) { create(:bone, project: project, name: 'root', x: 0, y: 0) }
    let!(:spine_bone) { create(:bone, project: project, name: 'spine', parent_bone: root_bone, x: 10, y: 20) }
    
    it 'generates correct bone hierarchy' do
      bones_data = subject.send(:generate_bones_data)
      
      expect(bones_data.length).to eq(2)
      expect(bones_data.first[:name]).to eq('root')
      expect(bones_data.second[:name]).to eq('spine')
      expect(bones_data.second[:parent]).to eq('root')
    end
  end
end
```

### 2. 통합 테스트
```ruby
# spec/requests/exports_spec.rb
RSpec.describe 'Exports API', type: :request do
  let(:user) { create(:user) }
  let(:project) { create(:project, user: user) }
  
  describe 'POST /api/v1/projects/:id/exports/spine_package' do
    it 'starts spine package generation' do
      post "/api/v1/projects/#{project.id}/exports/spine_package",
           headers: auth_headers(user)
      
      expect(response).to have_http_status(:ok)
      expect(JSON.parse(response.body)).to have_key('job_id')
      expect(GenerateSpinePackageJob).to have_been_enqueued
    end
  end
end
```

## 구현 로드맵

### Week 1: 기본 Spine JSON 구조
- [x] SpineExportService 기본 구현
- [x] Skeleton, Bones, Slots 데이터 생성
- [x] 기본 JSON 구조 테스트

### Week 2: 메시 어태치먼트 처리
- [x] 메시 데이터를 Spine 형식으로 변환
- [x] Weight 정보 포함
- [x] Skins 데이터 생성

### Week 3: 텍스처 아틀라스 생성
- [x] TextureAtlasService 구현
- [x] Bin packing 알고리즘
- [x] Atlas 파일 생성

### Week 4: 백그라운드 작업 및 UI
- [x] GenerateSpinePackageJob 구현
- [x] 프론트엔드 ExportPanel 구현
- [x] 진행 상황 추적

## 성공 지표

1. **호환성**: Spine 런타임에서 정상 로드 및 렌더링
2. **완성도**: JSON, Atlas, 텍스처 모든 파일 정상 생성
3. **품질**: 아틀라스 패킹 효율성 80% 이상
4. **사용성**: 직관적인 익스포트 UI 및 진행 상황 표시