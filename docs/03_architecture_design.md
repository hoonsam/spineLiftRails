# SpineLift 웹 서비스 아키텍처 설계

## 시스템 개요

SpineLift 웹 서비스는 기존 Python 데스크톱 애플리케이션의 핵심 기능을 웹 환경으로 이식하는 하이브리드 아키텍처를 채택합니다. Rails를 메인 웹 프레임워크로 사용하면서 Python 메시 생성 엔진을 마이크로서비스로 활용합니다.

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                        클라이언트 (브라우저)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   React/    │  │  Pixi.js     │  │   ActionCable         │  │
│  │   Vue.js    │  │  Spine뷰어   │  │   (WebSocket)         │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────┴────────────────────────────────────┐
│                        Rails 애플리케이션                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   API       │  │   Active     │  │   Background          │  │
│  │   컨트롤러  │  │   Storage    │  │   Jobs (Sidekiq)      │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
│         │                  │                     │               │
│  ┌──────┴──────┐  ┌───────┴──────┐  ┌──────────┴────────────┐  │
│  │   비즈니스  │  │   파일       │  │   Python Service      │  │
│  │   로직      │  │   스토리지   │  │   커넥터             │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────┬───────────────────┘
                                              │ HTTP/gRPC
┌─────────────────────────────────────────────┴───────────────────┐
│                     Python 메시 처리 서비스                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   Flask/    │  │   Batch      │  │   Spine JSON          │  │
│  │   FastAPI   │  │   Mesh       │  │   Builder             │  │
│  └─────────────┘  │   Processor  │  └───────────────────────┘  │
│                   └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## 핵심 컴포넌트

### 1. 프론트엔드 레이어

#### 1.1 UI 프레임워크
- **주 프레임워크**: React 또는 Vue.js 3
- **상태 관리**: Redux/Vuex 또는 Zustand/Pinia
- **스타일링**: Tailwind CSS + 커스텀 컴포넌트
- **빌드 도구**: Vite 또는 Webpack 5

#### 1.2 메시 렌더링 엔진
- **Pixi.js**: 2D WebGL 렌더링
- **pixi-spine**: Spine 애니메이션 재생
- **커스텀 셰이더**: 메시 와이어프레임, 버텍스 하이라이트

#### 1.3 실시간 통신
- **ActionCable**: WebSocket 기반 양방향 통신
- **폴링 대체**: 실시간 지원 불가 시 HTTP 폴링

### 2. Rails 백엔드 레이어

#### 2.1 API 설계
```ruby
# RESTful API 구조
namespace :api do
  namespace :v1 do
    resources :projects do
      member do
        post :upload_psd
        get :export_spine_json
      end
      
      resources :layers do
        resource :mesh do
          post :generate
          patch :update_parameters
        end
      end
    end
  end
end
```

#### 2.2 데이터 모델
```ruby
# 핵심 모델 구조
class Project < ApplicationRecord
  has_many :layers, dependent: :destroy
  has_one_attached :psd_file
  
  enum status: { 
    draft: 0, 
    processing: 1, 
    completed: 2, 
    failed: 3 
  }
end

class Layer < ApplicationRecord
  belongs_to :project
  has_one :mesh, dependent: :destroy
  has_one_attached :image
  
  store :metadata, accessors: [:width, :height, :opacity, :blend_mode]
end

class Mesh < ApplicationRecord
  belongs_to :layer
  
  # JSON 필드로 대용량 데이터 저장
  store :data, accessors: [:vertices, :triangles, :uvs]
  store :parameters, accessors: [:detail_factor, :alpha_threshold]
end
```

#### 2.3 서비스 객체
```ruby
# app/services/python_mesh_service.rb
class PythonMeshService
  include HTTParty
  base_uri ENV['PYTHON_SERVICE_URL']
  
  def generate_mesh(image_path, parameters)
    response = self.class.post('/generate_mesh',
      body: {
        image_path: image_path,
        parameters: parameters
      }.to_json,
      headers: { 'Content-Type' => 'application/json' }
    )
    
    handle_response(response)
  end
  
  private
  
  def handle_response(response)
    case response.code
    when 200
      JSON.parse(response.body, symbolize_names: true)
    when 422
      raise MeshGenerationError, response['error']
    else
      raise ServiceUnavailableError
    end
  end
end
```

### 3. Python 서비스 레이어

#### 3.1 API 서버
```python
# main.py - FastAPI 서버
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from typing import Dict, List, Any

app = FastAPI()

class MeshParameters(BaseModel):
    detail_factor: float = 0.01
    alpha_threshold: int = 128
    edge_tolerance: float = 2.0

class MeshResponse(BaseModel):
    vertices: List[float]
    triangles: List[int]
    uvs: List[float]
    statistics: Dict[str, Any]

@app.post("/generate_mesh", response_model=MeshResponse)
async def generate_mesh(
    file: UploadFile = File(...),
    parameters: MeshParameters = MeshParameters()
):
    # 기존 BatchMeshProcessor 활용
    processor = BatchMeshProcessor(parameters.dict())
    mesh_data = processor.generate_mesh_data(file.file)
    
    return MeshResponse(**mesh_data)
```

#### 3.2 워커 프로세스
```python
# worker.py - Celery 워커
from celery import Celery
from batch_mesh_processor import BatchMeshProcessor

celery = Celery('spinelift', broker='redis://localhost:6379')

@celery.task
def process_layer_batch(project_id: str, layer_ids: List[str]):
    """여러 레이어를 배치로 처리"""
    results = []
    
    for layer_id in layer_ids:
        try:
            # 레이어 이미지 로드
            image_path = get_layer_image_path(layer_id)
            params = get_layer_parameters(layer_id)
            
            # 메시 생성
            processor = BatchMeshProcessor(params)
            mesh_data = processor.generate_mesh_data(image_path)
            
            # 결과 저장
            save_mesh_data(layer_id, mesh_data)
            results.append({'layer_id': layer_id, 'status': 'success'})
            
        except Exception as e:
            results.append({'layer_id': layer_id, 'status': 'failed', 'error': str(e)})
    
    return results
```

### 4. 데이터 저장 전략

#### 4.1 파일 스토리지
- **Active Storage**: Rails 내장 파일 관리
- **S3/R2**: 프로덕션 환경 파일 저장
- **로컬 캐시**: 자주 사용되는 파일 캐싱

#### 4.2 데이터베이스
- **PostgreSQL**: 메인 데이터베이스
- **Redis**: 캐싱 및 세션 저장
- **JSON 필드**: 메시 데이터 효율적 저장

```sql
-- 메시 데이터 최적화된 스키마
CREATE TABLE meshes (
    id BIGSERIAL PRIMARY KEY,
    layer_id BIGINT NOT NULL,
    data JSONB NOT NULL, -- 버텍스, 삼각형, UV
    parameters JSONB NOT NULL,
    statistics JSONB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    
    -- 인덱스
    FOREIGN KEY (layer_id) REFERENCES layers(id),
    INDEX idx_layer_id (layer_id)
);

-- JSONB 필드 인덱싱 (필요시)
CREATE INDEX idx_mesh_parameters ON meshes USING GIN (parameters);
```

### 5. 캐싱 전략

#### 5.1 Rails 캐싱
```ruby
class MeshController < ApplicationController
  def show
    @mesh = Rails.cache.fetch("mesh/#{params[:id]}", expires_in: 1.hour) do
      Mesh.find(params[:id])
    end
  end
end
```

#### 5.2 CDN 통합
```yaml
# config/environments/production.rb
config.action_controller.asset_host = ENV['CDN_HOST']
config.force_ssl = true
```

### 6. 보안 아키텍처

#### 6.1 인증/인가
```ruby
# JWT 기반 API 인증
class ApplicationController < ActionController::API
  before_action :authenticate_request
  
  private
  
  def authenticate_request
    token = request.headers['Authorization']&.split(' ')&.last
    decoded = JWT.decode(token, Rails.application.secrets.secret_key_base)
    @current_user = User.find(decoded[0]['user_id'])
  rescue JWT::DecodeError
    render json: { error: 'Unauthorized' }, status: :unauthorized
  end
end
```

#### 6.2 파일 업로드 보안
```ruby
class PsdUploadValidator < ActiveModel::Validator
  def validate(record)
    return unless record.psd_file.attached?
    
    # 파일 크기 제한
    if record.psd_file.blob.byte_size > 500.megabytes
      record.errors.add(:psd_file, 'is too large (max 500MB)')
    end
    
    # 파일 타입 검증
    unless record.psd_file.blob.content_type == 'image/vnd.adobe.photoshop'
      record.errors.add(:psd_file, 'must be a PSD file')
    end
  end
end
```

### 7. 확장성 설계

#### 7.1 수평 확장
```yaml
# docker-compose.yml
version: '3.8'

services:
  rails:
    build: .
    scale: 3  # Rails 인스턴스 3개
    
  python_service:
    build: ./python
    scale: 5  # Python 워커 5개
    
  nginx:
    image: nginx
    depends_on:
      - rails
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

#### 7.2 비동기 처리
```ruby
# 대용량 파일 처리를 위한 비동기 작업
class ProcessPsdJob < ApplicationJob
  queue_as :default
  
  def perform(project_id)
    project = Project.find(project_id)
    
    # Python 서비스 호출
    PythonMeshService.new.process_project(project)
    
    # 완료 알림
    ProjectMailer.processing_complete(project).deliver_later
  end
end
```

## Railway 배포 아키텍처

### 1. 서비스 구성
```toml
# railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile"

[deploy]
startCommand = "bundle exec rails server -b 0.0.0.0"
healthcheckPath = "/health"
healthcheckTimeout = 10

[environment]
RAILS_ENV = "production"
RAILS_SERVE_STATIC_FILES = "true"
```

### 2. 멀티 서비스 배포
- **Rails 서비스**: 메인 웹 애플리케이션
- **Python 서비스**: 별도 Railway 서비스로 배포
- **PostgreSQL**: Railway 제공 데이터베이스
- **Redis**: Railway 제공 Redis 인스턴스

### 3. 환경 변수 관리
```bash
# Railway 환경 변수
DATABASE_URL          # PostgreSQL 연결
REDIS_URL            # Redis 연결
PYTHON_SERVICE_URL   # Python 서비스 내부 URL
S3_BUCKET           # 파일 저장소
JWT_SECRET          # 인증 시크릿
```

## 성능 메트릭

### 목표 성능
- **응답 시간**: API 평균 < 200ms
- **메시 생성**: 레이어당 < 5초
- **동시 사용자**: 100명 이상
- **파일 업로드**: 500MB까지 안정적 처리

### 모니터링
- **APM**: New Relic 또는 DataDog
- **로그**: Logflare 또는 Papertrail
- **업타임**: UptimeRobot
- **에러 추적**: Sentry

## 결론

이 아키텍처는 SpineLift의 핵심 기능을 웹으로 성공적으로 이식하면서도 확장 가능하고 유지보수가 용이한 구조를 제공합니다. Python 엔진의 강력함과 Rails의 생산성을 결합하여 최적의 솔루션을 구현합니다.