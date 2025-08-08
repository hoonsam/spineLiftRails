# SpineLift 웹 서비스 구현 로드맵

## 개요

이 문서는 SpineLift를 Python 데스크톱 애플리케이션에서 Rails 기반 웹 서비스로 전환하는 상세한 구현 로드맵을 제공합니다. MVP는 메시 편집 기능에 초점을 맞추며, 이후 단계적으로 기능을 확장합니다.

## Phase 1: 기반 구축 (2주)

### Week 1: Rails API 및 Python 서비스 설정

#### Day 1-2: Rails 프로젝트 초기 설정
```bash
# 기본 gem 추가
bundle add jwt devise rack-cors sidekiq aws-sdk-s3
bundle add rspec-rails factory_bot_rails --group "development, test"

# 데이터베이스 설정
rails generate model Project name:string status:integer user:references
rails generate model Layer name:string position:integer project:references
rails generate model Mesh layer:references data:jsonb parameters:jsonb
rails db:create db:migrate
```

#### Day 3-4: Python 서비스 분리
```python
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
numpy==1.24.3
opencv-python==4.8.1
pillow==10.1.0
psd-tools==1.9.28
triangle==20230923

# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Day 5: API 엔드포인트 구현
```ruby
# app/controllers/api/v1/projects_controller.rb
class Api::V1::ProjectsController < Api::V1::BaseController
  def create
    @project = current_user.projects.build(project_params)
    
    if @project.save
      ProcessPsdJob.perform_later(@project.id)
      render json: ProjectSerializer.new(@project), status: :created
    else
      render json: { errors: @project.errors }, status: :unprocessable_entity
    end
  end
  
  private
  
  def project_params
    params.require(:project).permit(:name, :psd_file)
  end
end
```

### Week 2: 파일 처리 및 메시 생성

#### Day 6-7: Active Storage 설정
```ruby
# config/storage.yml
amazon:
  service: S3
  access_key_id: <%= ENV['AWS_ACCESS_KEY_ID'] %>
  secret_access_key: <%= ENV['AWS_SECRET_ACCESS_KEY'] %>
  region: <%= ENV['AWS_REGION'] %>
  bucket: <%= ENV['AWS_BUCKET'] %>

# 직접 업로드 설정
class Project < ApplicationRecord
  has_one_attached :psd_file
  
  def psd_file_url
    return unless psd_file.attached?
    
    Rails.application.routes.url_helpers.rails_blob_url(psd_file)
  end
end
```

#### Day 8-9: Python 서비스 연동
```ruby
# app/services/mesh_generation_service.rb
class MeshGenerationService
  include HTTParty
  base_uri ENV['PYTHON_SERVICE_URL']
  
  def self.generate_for_layer(layer)
    response = post('/api/generate_mesh',
      body: {
        image_url: layer.image_url,
        parameters: layer.mesh_parameters
      }.to_json,
      headers: { 'Content-Type' => 'application/json' }
    )
    
    if response.success?
      layer.create_mesh!(data: response.parsed_response)
    else
      raise MeshGenerationError, response['error']
    end
  end
end
```

#### Day 10: 배경 작업 설정
```ruby
# app/jobs/process_layer_job.rb
class ProcessLayerJob < ApplicationJob
  queue_as :default
  
  def perform(layer_id)
    layer = Layer.find(layer_id)
    
    # 이미지 추출
    ExtractLayerImageService.call(layer)
    
    # 메시 생성
    MeshGenerationService.generate_for_layer(layer)
    
    # 상태 업데이트
    layer.update!(status: 'completed')
    
    # WebSocket으로 알림
    LayerChannel.broadcast_to(layer, { status: 'completed' })
  end
end
```

## Phase 2: 프론트엔드 개발 (2주)

### Week 3: React/Vue 설정 및 기본 UI

#### Day 11-12: 프론트엔드 프로젝트 설정
```javascript
// package.json
{
  "name": "spinelift-frontend",
  "dependencies": {
    "react": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "pixi.js": "^7.3.0",
    "pixi-spine": "^4.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0"
  }
}

// src/api/client.js
import axios from 'axios'

const client = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

client.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

#### Day 13-14: 파일 업로드 UI
```javascript
// src/components/PsdUploader.jsx
import { useDropzone } from 'react-dropzone'
import { useMutation } from '@tanstack/react-query'
import { uploadPsd } from '../api/projects'

export function PsdUploader({ onSuccess }) {
  const mutation = useMutation({
    mutationFn: uploadPsd,
    onSuccess: (data) => {
      onSuccess(data.project)
    }
  })
  
  const { getRootProps, getInputProps } = useDropzone({
    accept: {
      'image/vnd.adobe.photoshop': ['.psd']
    },
    maxSize: 500 * 1024 * 1024, // 500MB
    onDrop: (files) => {
      const formData = new FormData()
      formData.append('psd_file', files[0])
      mutation.mutate(formData)
    }
  })
  
  return (
    <div {...getRootProps()} className="upload-zone">
      <input {...getInputProps()} />
      {mutation.isLoading ? (
        <LoadingSpinner />
      ) : (
        <p>PSD 파일을 드래그하거나 클릭하여 업로드</p>
      )}
    </div>
  )
}
```

#### Day 15: 레이어 목록 UI
```javascript
// src/components/LayerList.jsx
import { useQuery } from '@tanstack/react-query'
import { fetchProjectLayers } from '../api/layers'

export function LayerList({ projectId, onSelectLayer }) {
  const { data: layers, isLoading } = useQuery({
    queryKey: ['layers', projectId],
    queryFn: () => fetchProjectLayers(projectId)
  })
  
  if (isLoading) return <LoadingSpinner />
  
  return (
    <div className="layer-list">
      {layers.map(layer => (
        <LayerItem
          key={layer.id}
          layer={layer}
          onClick={() => onSelectLayer(layer)}
        />
      ))}
    </div>
  )
}
```

### Week 4: 메시 편집기 MVP

#### Day 16-17: Pixi.js 메시 렌더러
```javascript
// src/components/MeshRenderer.jsx
import { useEffect, useRef } from 'react'
import * as PIXI from 'pixi.js'

export function MeshRenderer({ meshData, textureUrl }) {
  const canvasRef = useRef()
  const appRef = useRef()
  
  useEffect(() => {
    // PIXI 앱 초기화
    const app = new PIXI.Application({
      width: 800,
      height: 600,
      backgroundColor: 0x2b2b2b,
      view: canvasRef.current
    })
    
    appRef.current = app
    
    return () => {
      app.destroy(true)
    }
  }, [])
  
  useEffect(() => {
    if (!meshData || !appRef.current) return
    
    const app = appRef.current
    app.stage.removeChildren()
    
    // 텍스처 로드
    const texture = PIXI.Texture.from(textureUrl)
    
    // 메시 생성
    const geometry = new PIXI.Geometry()
      .addAttribute('aVertexPosition', meshData.vertices, 2)
      .addAttribute('aUvs', meshData.uvs, 2)
      .addIndex(meshData.triangles)
    
    const mesh = new PIXI.Mesh(geometry, new PIXI.MeshMaterial(texture))
    app.stage.addChild(mesh)
    
    // 카메라 중앙 정렬
    mesh.position.set(app.screen.width / 2, app.screen.height / 2)
    
  }, [meshData, textureUrl])
  
  return <canvas ref={canvasRef} />
}
```

#### Day 18-19: 파라미터 조정 UI
```javascript
// src/components/MeshParameters.jsx
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { updateMeshParameters } from '../api/mesh'
import { debounce } from 'lodash'

export function MeshParameters({ layerId, initialParams, onUpdate }) {
  const [params, setParams] = useState(initialParams)
  
  const mutation = useMutation({
    mutationFn: (params) => updateMeshParameters(layerId, params),
    onSuccess: (data) => {
      onUpdate(data.mesh)
    }
  })
  
  const debouncedUpdate = debounce((newParams) => {
    mutation.mutate(newParams)
  }, 300)
  
  const handleChange = (name, value) => {
    const newParams = { ...params, [name]: value }
    setParams(newParams)
    debouncedUpdate(newParams)
  }
  
  return (
    <div className="parameters-panel">
      <h3>메시 파라미터</h3>
      
      <div className="parameter">
        <label>디테일 수준</label>
        <input
          type="range"
          min="0.001"
          max="0.05"
          step="0.001"
          value={params.detail_factor}
          onChange={(e) => handleChange('detail_factor', parseFloat(e.target.value))}
        />
        <span>{params.detail_factor}</span>
      </div>
      
      <div className="parameter">
        <label>알파 임계값</label>
        <input
          type="range"
          min="0"
          max="255"
          step="1"
          value={params.alpha_threshold}
          onChange={(e) => handleChange('alpha_threshold', parseInt(e.target.value))}
        />
        <span>{params.alpha_threshold}</span>
      </div>
    </div>
  )
}
```

#### Day 20: 실시간 업데이트 (ActionCable)
```javascript
// src/hooks/useMeshUpdates.js
import { useEffect } from 'react'
import { createConsumer } from '@rails/actioncable'

const consumer = createConsumer(process.env.REACT_APP_WEBSOCKET_URL)

export function useMeshUpdates(layerId, onUpdate) {
  useEffect(() => {
    if (!layerId) return
    
    const subscription = consumer.subscriptions.create(
      { channel: 'MeshChannel', layer_id: layerId },
      {
        received: (data) => {
          onUpdate(data.mesh)
        }
      }
    )
    
    return () => {
      subscription.unsubscribe()
    }
  }, [layerId, onUpdate])
}
```

## Phase 3: 통합 및 최적화 (1주)

### Week 5: 시스템 통합 및 테스트

#### Day 21-22: 엔드투엔드 테스트
```ruby
# spec/system/mesh_generation_spec.rb
require 'rails_helper'

RSpec.describe "Mesh Generation", type: :system do
  let(:user) { create(:user) }
  
  before do
    sign_in user
  end
  
  it "generates mesh from uploaded PSD" do
    visit new_project_path
    
    attach_file "project[psd_file]", 
      Rails.root.join("spec/fixtures/files/test.psd")
    
    click_button "Upload"
    
    expect(page).to have_content("Processing PSD file...")
    
    # 처리 완료 대기
    within ".layer-list" do
      expect(page).to have_css(".layer-item", count: 3)
    end
    
    # 첫 번째 레이어 선택
    first(".layer-item").click
    
    # 메시 프리뷰 확인
    within ".mesh-preview" do
      expect(page).to have_css("canvas")
    end
  end
end
```

#### Day 23: 성능 최적화
```ruby
# 캐싱 전략
class MeshController < ApplicationController
  def show
    @mesh = Rails.cache.fetch(
      ["mesh", params[:id], params[:version]], 
      expires_in: 1.hour
    ) do
      Mesh.find(params[:id])
    end
    
    render json: MeshSerializer.new(@mesh)
  end
end

# N+1 쿼리 방지
class ProjectsController < ApplicationController
  def show
    @project = Project.includes(layers: :mesh).find(params[:id])
  end
end
```

#### Day 24: 에러 처리 및 복구
```javascript
// src/components/ErrorBoundary.jsx
import { Component } from 'react'
import * as Sentry from '@sentry/react'

export class ErrorBoundary extends Component {
  state = { hasError: false }
  
  static getDerivedStateFromError(error) {
    return { hasError: true }
  }
  
  componentDidCatch(error, errorInfo) {
    Sentry.captureException(error, { contexts: { react: errorInfo } })
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>오류가 발생했습니다</h2>
          <button onClick={() => window.location.reload()}>
            새로고침
          </button>
        </div>
      )
    }
    
    return this.props.children
  }
}
```

#### Day 25: Railway 배포 준비
```dockerfile
# Dockerfile
FROM ruby:3.2-slim as rails-base

# 시스템 의존성
RUN apt-get update -qq && \
    apt-get install -y build-essential libpq-dev nodejs npm

WORKDIR /app

# Gem 설치
COPY Gemfile Gemfile.lock ./
RUN bundle install --deployment

# 애플리케이션 복사
COPY . .

# 에셋 컴파일
RUN bundle exec rails assets:precompile

# Python 서비스는 별도 Dockerfile
FROM python:3.11-slim as python-base

WORKDIR /app
COPY python/requirements.txt .
RUN pip install -r requirements.txt
COPY python/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

## Phase 4: 프로덕션 배포 (3일)

### Day 26: Railway 설정
```yaml
# railway.yml
version: 1

services:
  web:
    build:
      dockerfile: Dockerfile
    start_command: bundle exec rails server -b 0.0.0.0
    health_check_path: /health
    
  python:
    build:
      dockerfile: python/Dockerfile
    start_command: uvicorn main:app --host 0.0.0.0
    
  worker:
    build:
      dockerfile: Dockerfile
    start_command: bundle exec sidekiq
    
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
```

### Day 27: 모니터링 설정
```ruby
# config/initializers/sentry.rb
Sentry.init do |config|
  config.dsn = ENV['SENTRY_DSN']
  config.breadcrumbs_logger = [:active_support_logger]
  config.traces_sample_rate = 0.1
end

# config/initializers/newrelic.rb
# New Relic 설정
```

### Day 28: 배포 및 검증
```bash
# 배포 스크립트
#!/bin/bash

# 테스트 실행
bundle exec rspec
npm test

# 마이그레이션
railway run bundle exec rails db:migrate

# 배포
railway up

# 헬스체크
curl https://spinelift.up.railway.app/health
```

## 향후 로드맵

### Phase 5: 스켈레톤 편집 (2주)
- 본 생성 및 편집 UI
- 계층구조 관리
- 자동 리깅

### Phase 6: 애니메이션 (3주)
- 타임라인 UI
- 키프레임 편집
- 애니메이션 프리뷰

### Phase 7: 고급 기능 (4주)
- 협업 기능
- 버전 관리
- 플러그인 시스템

## 성공 지표

### MVP (Phase 1-4)
- ✅ PSD 업로드 및 레이어 추출
- ✅ 실시간 메시 생성 및 편집
- ✅ Spine JSON 익스포트
- ✅ 웹 기반 메시 프리뷰

### 성능 목표
- 📊 5초 이내 메시 생성
- 📊 실시간 파라미터 업데이트 (<100ms)
- 📊 500MB PSD 파일 처리
- 📊 동시 사용자 100명 지원

### 사용성 목표
- 👥 직관적인 UI/UX
- 📱 반응형 디자인
- 🌐 크로스 브라우저 지원
- ♿ 접근성 준수

## 리스크 관리

### 기술적 리스크
1. **대용량 파일 처리**: 청크 업로드, 스트리밍 처리
2. **실시간 성능**: WebSocket 최적화, 클라이언트 캐싱
3. **브라우저 호환성**: 폴리필, 프로그레시브 향상

### 운영 리스크
1. **스케일링**: 자동 스케일링 설정
2. **보안**: 정기 보안 감사
3. **백업**: 자동 백업 및 복구 절차

## 결론

이 로드맵을 따라 구현하면 4주 내에 SpineLift의 핵심 메시 편집 기능을 웹 서비스로 성공적으로 이식할 수 있습니다. MVP 완성 후 사용자 피드백을 바탕으로 추가 기능을 단계적으로 구현합니다.