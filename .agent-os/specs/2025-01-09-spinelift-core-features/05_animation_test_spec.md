# 애니메이션 테스트 기능 명세서

## 개요

현재 SpineLift Rails에서는 정적인 메시와 본 시스템만 지원하고 있으며, Spine 애니메이션의 핵심 기능인 실시간 애니메이션 프리뷰 및 테스트 기능이 전혀 구현되지 않았습니다. 이 명세서는 타임라인 에디터, 키프레임 시스템, 애니메이션 재생 및 테스트 도구를 정의합니다.

**담당 영역**: 프론트엔드 애니메이션 시스템, 백엔드 애니메이션 데이터  
**우선순위**: Medium-Low  
**예상 구현 시간**: 5-6주  
**의존성**: 본 시스템 완료 후 구현  

## 현재 상태 분석

### 기존 구현 부족사항
- 애니메이션 데이터 모델 없음
- 키프레임 에디터 없음
- 타임라인 UI 없음
- Spine 런타임 통합 없음 (pixi-spine)
- 애니메이션 재생/테스트 기능 없음
- 이징(Easing) 및 보간 없음

### Spine 애니메이션 요구사항
Spine 3.8.95 애니메이션 구조:
```json
{
  "animations": {
    "idle": {
      "bones": {
        "spine": {
          "rotate": [
            { "time": 0, "value": 0 },
            { "time": 1, "value": 15, "curve": "stepped" },
            { "time": 2, "value": 0 }
          ]
        }
      },
      "slots": {
        "body": {
          "color": [
            { "time": 0, "color": "ffffffff" },
            { "time": 0.5, "color": "ff0000ff" }
          ]
        }
      }
    }
  }
}
```

## 기능 요구사항

### 1. 애니메이션 데이터 구조

#### 1.1 Animation 모델
```ruby
# app/models/animation.rb
class Animation < ApplicationRecord
  belongs_to :project
  has_many :animation_tracks, dependent: :destroy
  has_many :keyframes, through: :animation_tracks
  
  validates :name, presence: true, uniqueness: { scope: :project_id }
  validates :duration, presence: true, numericality: { greater_than: 0 }
  validates :fps, presence: true, numericality: { greater_than: 0 }
  
  enum loop_mode: { no_loop: 0, loop: 1, ping_pong: 2 }
  
  def total_frames
    (duration * fps).round
  end
  
  def frame_to_time(frame)
    frame / fps.to_f
  end
  
  def time_to_frame(time)
    (time * fps).round
  end
  
  # Spine JSON 형식으로 변환
  def to_spine_json
    animation_data = {}
    
    # 본 애니메이션 트랙들
    bone_tracks = animation_tracks.joins(:bone).group_by(&:bone)
    if bone_tracks.any?
      animation_data['bones'] = {}
      bone_tracks.each do |bone, tracks|
        animation_data['bones'][bone.name] = {}
        
        tracks.each do |track|
          case track.property_type
          when 'rotation'
            animation_data['bones'][bone.name]['rotate'] = track.keyframes_to_spine_format
          when 'translation'
            animation_data['bones'][bone.name]['translate'] = track.keyframes_to_spine_format
          when 'scale'
            animation_data['bones'][bone.name]['scale'] = track.keyframes_to_spine_format
          end
        end
      end
    end
    
    # 슬롯 애니메이션 트랙들
    slot_tracks = animation_tracks.joins(:layer).group_by(&:layer)
    if slot_tracks.any?
      animation_data['slots'] = {}
      slot_tracks.each do |layer, tracks|
        animation_data['slots'][layer.name] = {}
        
        tracks.each do |track|
          case track.property_type
          when 'color'
            animation_data['slots'][layer.name]['color'] = track.keyframes_to_spine_format
          when 'attachment'
            animation_data['slots'][layer.name]['attachment'] = track.keyframes_to_spine_format
          end
        end
      end
    end
    
    animation_data
  end
end
```

#### 1.2 AnimationTrack 및 Keyframe 모델
```ruby
# app/models/animation_track.rb
class AnimationTrack < ApplicationRecord
  belongs_to :animation
  belongs_to :bone, optional: true
  belongs_to :layer, optional: true # slot 애니메이션용
  has_many :keyframes, dependent: :destroy
  
  validates :property_type, presence: true
  validates :property_type, inclusion: { 
    in: %w[rotation translation scale color attachment] 
  }
  
  validate :must_have_bone_or_layer
  
  def keyframes_to_spine_format
    keyframes.order(:time).map do |kf|
      spine_keyframe = { 'time' => kf.time }
      
      case property_type
      when 'rotation'
        spine_keyframe['value'] = kf.rotation_value || 0
      when 'translation'
        spine_keyframe['x'] = kf.x_value || 0
        spine_keyframe['y'] = kf.y_value || 0
      when 'scale'
        spine_keyframe['x'] = kf.x_value || 1
        spine_keyframe['y'] = kf.y_value || 1
      when 'color'
        spine_keyframe['color'] = kf.color_value || 'ffffffff'
      when 'attachment'
        spine_keyframe['name'] = kf.string_value
      end
      
      # 이징 커브 추가
      if kf.curve_type && kf.curve_type != 'linear'
        spine_keyframe['curve'] = kf.curve_type
        if kf.curve_type == 'bezier'
          spine_keyframe['c1'] = kf.curve_c1 || 0
          spine_keyframe['c2'] = kf.curve_c2 || 0
          spine_keyframe['c3'] = kf.curve_c3 || 1
          spine_keyframe['c4'] = kf.curve_c4 || 1
        end
      end
      
      spine_keyframe
    end
  end
  
  private
  
  def must_have_bone_or_layer
    if bone.nil? && layer.nil?
      errors.add(:base, 'Must belong to either a bone or a layer')
    elsif bone.present? && layer.present?
      errors.add(:base, 'Cannot belong to both bone and layer')
    end
  end
end

# app/models/keyframe.rb
class Keyframe < ApplicationRecord
  belongs_to :animation_track
  
  validates :time, presence: true, numericality: { greater_than_or_equal_to: 0 }
  validates :time, uniqueness: { scope: :animation_track_id }
  
  # 커브 타입: linear, stepped, bezier
  enum curve_type: { linear: 0, stepped: 1, bezier: 2 }
  
  # 다양한 값 타입 지원
  validates :rotation_value, numericality: true, allow_nil: true
  validates :x_value, :y_value, numericality: true, allow_nil: true
  validates :color_value, format: { with: /\A[0-9a-fA-F]{8}\z/ }, allow_nil: true
  
  # 베지어 커브 파라미터 (0-1 범위)
  validates :curve_c1, :curve_c2, :curve_c3, :curve_c4, 
            numericality: { in: 0..1 }, allow_nil: true
  
  scope :in_time_range, ->(start_time, end_time) { 
    where(time: start_time..end_time) 
  }
  
  def interpolate_to(next_keyframe, current_time)
    return self.value if next_keyframe.nil? || current_time <= self.time
    return next_keyframe.value if current_time >= next_keyframe.time
    
    # 시간 정규화 (0-1)
    t = (current_time - self.time) / (next_keyframe.time - self.time)
    
    case curve_type
    when 'linear'
      interpolate_linear(next_keyframe, t)
    when 'stepped'
      self.value # 계단식 - 다음 키프레임까지 현재 값 유지
    when 'bezier'
      interpolate_bezier(next_keyframe, t)
    end
  end
  
  private
  
  def interpolate_linear(next_keyframe, t)
    current = self.numeric_value
    target = next_keyframe.numeric_value
    
    current + (target - current) * t
  end
  
  def interpolate_bezier(next_keyframe, t)
    # 베지어 곡선 보간 구현
    current = self.numeric_value
    target = next_keyframe.numeric_value
    
    # 3차 베지어 곡선: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
    p0, p1, p2, p3 = 0, curve_c1 || 0, curve_c3 || 1, 1
    
    bezier_t = cubic_bezier_solve(p1, p2, t)
    current + (target - current) * bezier_t
  end
  
  def numeric_value
    rotation_value || x_value || y_value || 0
  end
end
```

#### 1.3 데이터베이스 스키마
```ruby
# db/migrate/create_animations.rb
class CreateAnimations < ActiveRecord::Migration[7.0]
  def change
    create_table :animations do |t|
      t.references :project, null: false, foreign_key: true
      
      t.string :name, null: false
      t.text :description
      t.float :duration, null: false, default: 1.0 # 초
      t.integer :fps, null: false, default: 30
      t.integer :loop_mode, null: false, default: 0
      
      t.jsonb :metadata, default: {}
      t.integer :order_index, default: 0
      
      t.timestamps
    end
    
    add_index :animations, [:project_id, :name], unique: true
    add_index :animations, :order_index
  end
end

# db/migrate/create_animation_tracks.rb
class CreateAnimationTracks < ActiveRecord::Migration[7.0]
  def change
    create_table :animation_tracks do |t|
      t.references :animation, null: false, foreign_key: true
      t.references :bone, null: true, foreign_key: true
      t.references :layer, null: true, foreign_key: true
      
      t.string :property_type, null: false # rotation, translation, scale, color, attachment
      t.string :property_component # x, y, z (for translation/scale)
      
      t.jsonb :metadata, default: {}
      
      t.timestamps
    end
    
    add_index :animation_tracks, [:animation_id, :property_type]
    add_index :animation_tracks, :bone_id
    add_index :animation_tracks, :layer_id
  end
end

# db/migrate/create_keyframes.rb
class CreateKeyframes < ActiveRecord::Migration[7.0]
  def change
    create_table :keyframes do |t|
      t.references :animation_track, null: false, foreign_key: true
      
      t.float :time, null: false # 초 단위
      
      # 다양한 값 타입들
      t.float :rotation_value # 회전값 (도)
      t.float :x_value # X 위치/스케일
      t.float :y_value # Y 위치/스케일  
      t.string :color_value # RRGGBBAA 헥스 색상
      t.string :string_value # 어태치먼트 이름 등
      
      # 이징 커브
      t.integer :curve_type, default: 0 # linear, stepped, bezier
      t.float :curve_c1 # 베지어 제어점 1 X
      t.float :curve_c2 # 베지어 제어점 1 Y
      t.float :curve_c3 # 베지어 제어점 2 X
      t.float :curve_c4 # 베지어 제어점 2 Y
      
      t.timestamps
    end
    
    add_index :keyframes, [:animation_track_id, :time], unique: true
    add_index :keyframes, :time
  end
end
```

### 2. 타임라인 에디터 UI

#### 2.1 Timeline 컴포넌트
```typescript
// src/components/AnimationEditor/Timeline.tsx
import React, { useState, useRef, useCallback, useEffect } from 'react';

interface TimelineProps {
  animation: Animation;
  tracks: AnimationTrack[];
  currentTime: number;
  isPlaying: boolean;
  onTimeChange: (time: number) => void;
  onKeyframeAdd: (trackId: string, time: number) => void;
  onKeyframeMove: (keyframeId: string, newTime: number) => void;
  onKeyframeDelete: (keyframeId: string) => void;
  onKeyframeSelect: (keyframeIds: string[]) => void;
}

export const Timeline: React.FC<TimelineProps> = ({
  animation,
  tracks,
  currentTime,
  isPlaying,
  onTimeChange,
  onKeyframeAdd,
  onKeyframeMove,
  onKeyframeDelete,
  onKeyframeSelect
}) => {
  const timelineRef = useRef<HTMLDivElement>(null);
  const [pixelsPerSecond, setPixelsPerSecond] = useState(100);
  const [selectedKeyframes, setSelectedKeyframes] = useState<Set<string>>(new Set());
  const [dragState, setDragState] = useState<DragState | null>(null);
  
  const timelineWidth = animation.duration * pixelsPerSecond;
  const totalFrames = animation.total_frames;
  
  // 시간을 픽셀 위치로 변환
  const timeToPixel = useCallback((time: number) => {
    return time * pixelsPerSecond;
  }, [pixelsPerSecond]);
  
  // 픽셀 위치를 시간으로 변환  
  const pixelToTime = useCallback((pixel: number) => {
    return Math.max(0, Math.min(animation.duration, pixel / pixelsPerSecond));
  }, [pixelsPerSecond, animation.duration]);
  
  // 시간을 프레임으로 스냅
  const snapToFrame = useCallback((time: number) => {
    const frame = Math.round(time * animation.fps);
    return frame / animation.fps;
  }, [animation.fps]);
  
  const handleTimelineClick = useCallback((event: React.MouseEvent) => {
    if (!timelineRef.current) return;
    
    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const newTime = snapToFrame(pixelToTime(clickX));
    
    onTimeChange(newTime);
  }, [pixelToTime, snapToFrame, onTimeChange]);
  
  const handleKeyframeDoubleClick = useCallback((trackId: string, time: number) => {
    onKeyframeAdd(trackId, time);
  }, [onKeyframeAdd]);
  
  const handleKeyframeDragStart = useCallback((keyframeId: string, initialTime: number, event: React.MouseEvent) => {
    const startX = event.clientX;
    
    setDragState({
      keyframeId,
      startX,
      initialTime,
      currentTime: initialTime
    });
    
    event.preventDefault();
  }, []);
  
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!dragState) return;
    
    const deltaX = event.clientX - dragState.startX;
    const deltaTime = deltaX / pixelsPerSecond;
    const newTime = snapToFrame(dragState.initialTime + deltaTime);
    
    setDragState({
      ...dragState,
      currentTime: newTime
    });
  }, [dragState, pixelsPerSecond, snapToFrame]);
  
  const handleMouseUp = useCallback(() => {
    if (!dragState) return;
    
    onKeyframeMove(dragState.keyframeId, dragState.currentTime);
    setDragState(null);
  }, [dragState, onKeyframeMove]);
  
  useEffect(() => {
    if (dragState) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [dragState, handleMouseMove, handleMouseUp]);
  
  return (
    <div className="timeline">
      {/* 시간 눈금자 */}
      <div className="timeline-ruler" style={{ width: timelineWidth }}>
        {Array.from({ length: totalFrames + 1 }, (_, frame) => {
          const time = animation.frame_to_time(frame);
          const position = timeToPixel(time);
          const isSecond = frame % animation.fps === 0;
          
          return (
            <div 
              key={frame}
              className={`ruler-tick ${isSecond ? 'major' : 'minor'}`}
              style={{ left: position }}
            >
              {isSecond && (
                <span className="ruler-label">{Math.round(time)}s</span>
              )}
            </div>
          );
        })}
      </div>
      
      {/* 현재 시간 인디케이터 */}
      <div 
        className="timeline-cursor"
        style={{ left: timeToPixel(currentTime) }}
      />
      
      {/* 트랙들 */}
      <div className="timeline-tracks">
        {tracks.map(track => (
          <TimelineTrack
            key={track.id}
            track={track}
            timelineWidth={timelineWidth}
            pixelsPerSecond={pixelsPerSecond}
            selectedKeyframes={selectedKeyframes}
            onKeyframeDoubleClick={handleKeyframeDoubleClick}
            onKeyframeDragStart={handleKeyframeDragStart}
            onKeyframeSelect={setSelectedKeyframes}
          />
        ))}
      </div>
      
      {/* 타임라인 클릭 영역 */}
      <div 
        ref={timelineRef}
        className="timeline-clickarea"
        style={{ width: timelineWidth }}
        onClick={handleTimelineClick}
      />
    </div>
  );
};

interface DragState {
  keyframeId: string;
  startX: number;
  initialTime: number;
  currentTime: number;
}
```

#### 2.2 TimelineTrack 컴포넌트
```typescript
// src/components/AnimationEditor/TimelineTrack.tsx
import React from 'react';

interface TimelineTrackProps {
  track: AnimationTrack;
  timelineWidth: number;
  pixelsPerSecond: number;
  selectedKeyframes: Set<string>;
  onKeyframeDoubleClick: (trackId: string, time: number) => void;
  onKeyframeDragStart: (keyframeId: string, time: number, event: React.MouseEvent) => void;
  onKeyframeSelect: (selectedKeyframes: Set<string>) => void;
}

export const TimelineTrack: React.FC<TimelineTrackProps> = ({
  track,
  timelineWidth,
  pixelsPerSecond,
  selectedKeyframes,
  onKeyframeDoubleClick,
  onKeyframeDragStart,
  onKeyframeSelect
}) => {
  const timeToPixel = (time: number) => time * pixelsPerSecond;
  
  const getTrackColor = (propertyType: string): string => {
    switch (propertyType) {
      case 'rotation': return '#ff6b35';
      case 'translation': return '#4ecdc4';
      case 'scale': return '#45b7d1';
      case 'color': return '#96ceb4';
      case 'attachment': return '#feca57';
      default: return '#95a5a6';
    }
  };
  
  const handleKeyframeClick = (keyframeId: string, event: React.MouseEvent) => {
    if (event.ctrlKey || event.metaKey) {
      // 다중 선택
      const newSelection = new Set(selectedKeyframes);
      if (newSelection.has(keyframeId)) {
        newSelection.delete(keyframeId);
      } else {
        newSelection.add(keyframeId);
      }
      onKeyframeSelect(newSelection);
    } else {
      // 단일 선택
      onKeyframeSelect(new Set([keyframeId]));
    }
  };
  
  const handleTrackDoubleClick = (event: React.MouseEvent) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const time = clickX / pixelsPerSecond;
    
    onKeyframeDoubleClick(track.id, time);
  };
  
  return (
    <div className="timeline-track">
      <div className="track-header">
        <div 
          className="track-color-indicator"
          style={{ backgroundColor: getTrackColor(track.property_type) }}
        />
        <span className="track-label">
          {track.bone?.name || track.layer?.name} - {track.property_type}
        </span>
      </div>
      
      <div 
        className="track-content"
        style={{ width: timelineWidth }}
        onDoubleClick={handleTrackDoubleClick}
      >
        {/* 키프레임들 */}
        {track.keyframes.map(keyframe => (
          <div
            key={keyframe.id}
            className={`keyframe ${selectedKeyframes.has(keyframe.id) ? 'selected' : ''}`}
            style={{ 
              left: timeToPixel(keyframe.time),
              backgroundColor: getTrackColor(track.property_type)
            }}
            onClick={(e) => handleKeyframeClick(keyframe.id, e)}
            onMouseDown={(e) => onKeyframeDragStart(keyframe.id, keyframe.time, e)}
            title={`${keyframe.time}s - ${keyframe.value}`}
          >
            {/* 키프레임 커브 타입 표시 */}
            {keyframe.curve_type === 'bezier' && (
              <div className="keyframe-curve-indicator bezier" />
            )}
            {keyframe.curve_type === 'stepped' && (
              <div className="keyframe-curve-indicator stepped" />
            )}
          </div>
        ))}
        
        {/* 키프레임 간 연결선 */}
        {track.keyframes.length > 1 && (
          <svg className="keyframe-connections" width={timelineWidth} height="20">
            {track.keyframes.slice(0, -1).map((keyframe, index) => {
              const nextKeyframe = track.keyframes[index + 1];
              const startX = timeToPixel(keyframe.time);
              const endX = timeToPixel(nextKeyframe.time);
              
              return (
                <line
                  key={`${keyframe.id}-${nextKeyframe.id}`}
                  x1={startX}
                  y1={10}
                  x2={endX}
                  y2={10}
                  stroke={getTrackColor(track.property_type)}
                  strokeWidth={2}
                  strokeOpacity={0.5}
                />
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
};
```

### 3. 애니메이션 플레이어 및 제어

#### 3.1 AnimationPlayer 컴포넌트
```typescript
// src/components/AnimationEditor/AnimationPlayer.tsx
import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as PIXI from 'pixi.js';
import { Spine } from 'pixi-spine';

interface AnimationPlayerProps {
  project: Project;
  animation: Animation;
  currentTime: number;
  isPlaying: boolean;
  onTimeUpdate: (time: number) => void;
  onPlayStateChange: (isPlaying: boolean) => void;
}

export const AnimationPlayer: React.FC<AnimationPlayerProps> = ({
  project,
  animation,
  currentTime,
  isPlaying,
  onTimeUpdate,
  onPlayStateChange
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const appRef = useRef<PIXI.Application | null>(null);
  const spineRef = useRef<Spine | null>(null);
  const animationLoopRef = useRef<number | null>(null);
  
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [showBones, setShowBones] = useState(true);
  const [showAttachments, setShowAttachments] = useState(true);
  
  // PIXI 앱 초기화
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const app = new PIXI.Application({
      view: canvasRef.current,
      width: 800,
      height: 600,
      backgroundColor: 0x2b2b2b,
      antialias: true,
    });
    
    appRef.current = app;
    
    // Spine 로더 설정
    loadSpineAnimation();
    
    return () => {
      if (animationLoopRef.current) {
        cancelAnimationFrame(animationLoopRef.current);
      }
      app.destroy(true);
    };
  }, []);
  
  const loadSpineAnimation = async () => {
    if (!appRef.current) return;
    
    try {
      // 프로젝트에서 Spine 데이터 생성
      const spineData = await generateSpineData(project);
      
      // Spine 인스턴스 생성
      const spine = new Spine(spineData);
      spine.x = 400;
      spine.y = 300;
      spine.scale.set(0.5);
      
      appRef.current.stage.addChild(spine);
      spineRef.current = spine;
      
      // 애니메이션 설정
      if (spine.state.data.skeletonData.animations.length > 0) {
        spine.state.setAnimation(0, animation.name, false);
        spine.state.timeScale = 0; // 수동 제어를 위해 일시정지
      }
      
    } catch (error) {
      console.error('Failed to load Spine animation:', error);
    }
  };
  
  const generateSpineData = async (project: Project): Promise<any> => {
    // 서버에서 Spine JSON 데이터 가져오기
    const response = await api.get(`/projects/${project.id}/exports/spine_json`);
    return response.data;
  };
  
  // 애니메이션 재생 루프
  const updateAnimation = useCallback(() => {
    if (!spineRef.current || !isPlaying) return;
    
    const deltaTime = 1 / 60; // 60fps 가정
    const newTime = currentTime + (deltaTime * playbackSpeed);
    
    if (newTime >= animation.duration) {
      if (animation.loop_mode === 'loop') {
        onTimeUpdate(0);
      } else if (animation.loop_mode === 'ping_pong') {
        // TODO: ping-pong 로직 구현
        onTimeUpdate(animation.duration);
        onPlayStateChange(false);
      } else {
        onTimeUpdate(animation.duration);
        onPlayStateChange(false);
        return;
      }
    } else {
      onTimeUpdate(newTime);
    }
    
    animationLoopRef.current = requestAnimationFrame(updateAnimation);
  }, [currentTime, isPlaying, playbackSpeed, animation, onTimeUpdate, onPlayStateChange]);
  
  // 재생 상태 변경 시 루프 시작/중지
  useEffect(() => {
    if (isPlaying) {
      animationLoopRef.current = requestAnimationFrame(updateAnimation);
    } else if (animationLoopRef.current) {
      cancelAnimationFrame(animationLoopRef.current);
      animationLoopRef.current = null;
    }
    
    return () => {
      if (animationLoopRef.current) {
        cancelAnimationFrame(animationLoopRef.current);
      }
    };
  }, [isPlaying, updateAnimation]);
  
  // 현재 시간 변경 시 Spine 애니메이션 업데이트
  useEffect(() => {
    if (spineRef.current && spineRef.current.state.tracks.length > 0) {
      spineRef.current.state.tracks[0].trackTime = currentTime;
      spineRef.current.update(0); // 강제 업데이트
    }
  }, [currentTime]);
  
  const togglePlay = () => {
    onPlayStateChange(!isPlaying);
  };
  
  const stop = () => {
    onPlayStateChange(false);
    onTimeUpdate(0);
  };
  
  const stepBackward = () => {
    const frameTime = 1 / animation.fps;
    const newTime = Math.max(0, currentTime - frameTime);
    onTimeUpdate(newTime);
  };
  
  const stepForward = () => {
    const frameTime = 1 / animation.fps;
    const newTime = Math.min(animation.duration, currentTime + frameTime);
    onTimeUpdate(newTime);
  };
  
  return (
    <div className="animation-player">
      <div className="player-viewport">
        <canvas ref={canvasRef} />
        
        <div className="player-overlay">
          <div className="time-display">
            {currentTime.toFixed(2)}s / {animation.duration.toFixed(2)}s
          </div>
          
          <div className="frame-display">
            Frame {animation.time_to_frame(currentTime)} / {animation.total_frames}
          </div>
        </div>
      </div>
      
      <div className="player-controls">
        <div className="playback-controls">
          <button onClick={stop} title="정지">
            <StopIcon />
          </button>
          
          <button onClick={stepBackward} title="이전 프레임">
            <StepBackwardIcon />
          </button>
          
          <button onClick={togglePlay} title={isPlaying ? '일시정지' : '재생'}>
            {isPlaying ? <PauseIcon /> : <PlayIcon />}
          </button>
          
          <button onClick={stepForward} title="다음 프레임">
            <StepForwardIcon />
          </button>
        </div>
        
        <div className="speed-control">
          <label>속도:</label>
          <select 
            value={playbackSpeed} 
            onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
          >
            <option value={0.25}>0.25x</option>
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={1.5}>1.5x</option>
            <option value={2}>2x</option>
          </select>
        </div>
        
        <div className="display-options">
          <label>
            <input 
              type="checkbox" 
              checked={showBones} 
              onChange={(e) => setShowBones(e.target.checked)}
            />
            본 표시
          </label>
          
          <label>
            <input 
              type="checkbox" 
              checked={showAttachments} 
              onChange={(e) => setShowAttachments(e.target.checked)}
            />
            어태치먼트 표시
          </label>
        </div>
      </div>
    </div>
  );
};
```

### 4. 키프레임 에디터

#### 4.1 KeyframeEditor 컴포넌트
```typescript
// src/components/AnimationEditor/KeyframeEditor.tsx
import React, { useState, useCallback } from 'react';

interface KeyframeEditorProps {
  selectedKeyframes: Keyframe[];
  onKeyframeUpdate: (keyframeId: string, updates: Partial<Keyframe>) => void;
  onKeyframeDelete: (keyframeIds: string[]) => void;
}

export const KeyframeEditor: React.FC<KeyframeEditorProps> = ({
  selectedKeyframes,
  onKeyframeUpdate,
  onKeyframeDelete
}) => {
  const [activeTab, setActiveTab] = useState<'properties' | 'curves'>('properties');
  
  if (selectedKeyframes.length === 0) {
    return (
      <div className="keyframe-editor empty">
        <p>키프레임을 선택하여 편집하세요.</p>
      </div>
    );
  }
  
  const firstKeyframe = selectedKeyframes[0];
  const isMultiSelect = selectedKeyframes.length > 1;
  
  const handlePropertyChange = useCallback((property: keyof Keyframe, value: any) => {
    selectedKeyframes.forEach(keyframe => {
      onKeyframeUpdate(keyframe.id, { [property]: value });
    });
  }, [selectedKeyframes, onKeyframeUpdate]);
  
  const handleCurveChange = useCallback((curveType: string, curveParams?: any) => {
    const updates: Partial<Keyframe> = { curve_type: curveType };
    
    if (curveType === 'bezier' && curveParams) {
      updates.curve_c1 = curveParams.c1;
      updates.curve_c2 = curveParams.c2;
      updates.curve_c3 = curveParams.c3;
      updates.curve_c4 = curveParams.c4;
    }
    
    selectedKeyframes.forEach(keyframe => {
      onKeyframeUpdate(keyframe.id, updates);
    });
  }, [selectedKeyframes, onKeyframeUpdate]);
  
  const handleDelete = () => {
    const keyframeIds = selectedKeyframes.map(kf => kf.id);
    onKeyframeDelete(keyframeIds);
  };
  
  return (
    <div className="keyframe-editor">
      <div className="editor-header">
        <h3>키프레임 편집 {isMultiSelect && `(${selectedKeyframes.length}개)`}</h3>
        <button onClick={handleDelete} className="delete-button">
          삭제
        </button>
      </div>
      
      <div className="editor-tabs">
        <button 
          className={activeTab === 'properties' ? 'active' : ''}
          onClick={() => setActiveTab('properties')}
        >
          속성
        </button>
        <button 
          className={activeTab === 'curves' ? 'active' : ''}
          onClick={() => setActiveTab('curves')}
        >
          커브
        </button>
      </div>
      
      <div className="editor-content">
        {activeTab === 'properties' && (
          <KeyframeProperties
            keyframe={firstKeyframe}
            isMultiSelect={isMultiSelect}
            onPropertyChange={handlePropertyChange}
          />
        )}
        
        {activeTab === 'curves' && (
          <KeyframeCurves
            keyframe={firstKeyframe}
            isMultiSelect={isMultiSelect}
            onCurveChange={handleCurveChange}
          />
        )}
      </div>
    </div>
  );
};

const KeyframeProperties: React.FC<{
  keyframe: Keyframe;
  isMultiSelect: boolean;
  onPropertyChange: (property: keyof Keyframe, value: any) => void;
}> = ({ keyframe, isMultiSelect, onPropertyChange }) => {
  const track = keyframe.animation_track;
  
  const renderValueEditor = () => {
    switch (track.property_type) {
      case 'rotation':
        return (
          <div className="property-group">
            <label>회전값 (도)</label>
            <input 
              type="number" 
              value={keyframe.rotation_value || 0}
              onChange={(e) => onPropertyChange('rotation_value', parseFloat(e.target.value))}
              step={0.1}
            />
            <div className="rotation-wheel">
              {/* 회전 휠 UI 구현 */}
            </div>
          </div>
        );
        
      case 'translation':
        return (
          <div className="property-group">
            <label>위치</label>
            <div className="vector-input">
              <input 
                type="number" 
                placeholder="X"
                value={keyframe.x_value || 0}
                onChange={(e) => onPropertyChange('x_value', parseFloat(e.target.value))}
                step={0.1}
              />
              <input 
                type="number" 
                placeholder="Y"
                value={keyframe.y_value || 0}
                onChange={(e) => onPropertyChange('y_value', parseFloat(e.target.value))}
                step={0.1}
              />
            </div>
          </div>
        );
        
      case 'scale':
        return (
          <div className="property-group">
            <label>스케일</label>
            <div className="vector-input">
              <input 
                type="number" 
                placeholder="X"
                value={keyframe.x_value || 1}
                onChange={(e) => onPropertyChange('x_value', parseFloat(e.target.value))}
                step={0.01}
                min={0.01}
              />
              <input 
                type="number" 
                placeholder="Y"
                value={keyframe.y_value || 1}
                onChange={(e) => onPropertyChange('y_value', parseFloat(e.target.value))}
                step={0.01}
                min={0.01}
              />
            </div>
          </div>
        );
        
      case 'color':
        return (
          <div className="property-group">
            <label>색상</label>
            <ColorPicker 
              value={keyframe.color_value || 'ffffffff'}
              onChange={(color) => onPropertyChange('color_value', color)}
            />
          </div>
        );
        
      case 'attachment':
        return (
          <div className="property-group">
            <label>어태치먼트</label>
            <select 
              value={keyframe.string_value || ''}
              onChange={(e) => onPropertyChange('string_value', e.target.value)}
            >
              <option value="">없음</option>
              {/* 사용 가능한 어태치먼트 목록 */}
            </select>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <div className="keyframe-properties">
      <div className="property-group">
        <label>시간 (초)</label>
        <input 
          type="number" 
          value={keyframe.time}
          onChange={(e) => onPropertyChange('time', parseFloat(e.target.value))}
          step={1 / track.animation.fps}
          min={0}
          max={track.animation.duration}
        />
      </div>
      
      {renderValueEditor()}
      
      {isMultiSelect && (
        <div className="multi-select-notice">
          {selectedKeyframes.length}개의 키프레임이 동시에 편집됩니다.
        </div>
      )}
    </div>
  );
};

const KeyframeCurves: React.FC<{
  keyframe: Keyframe;
  isMultiSelect: boolean;
  onCurveChange: (curveType: string, curveParams?: any) => void;
}> = ({ keyframe, isMultiSelect, onCurveChange }) => {
  return (
    <div className="keyframe-curves">
      <div className="curve-type-selector">
        <label>커브 타입</label>
        <select 
          value={keyframe.curve_type}
          onChange={(e) => onCurveChange(e.target.value)}
        >
          <option value="linear">선형</option>
          <option value="stepped">계단</option>
          <option value="bezier">베지어</option>
        </select>
      </div>
      
      {keyframe.curve_type === 'bezier' && (
        <BezierCurveEditor
          c1={keyframe.curve_c1 || 0}
          c2={keyframe.curve_c2 || 0}
          c3={keyframe.curve_c3 || 1}
          c4={keyframe.curve_c4 || 1}
          onChange={(params) => onCurveChange('bezier', params)}
        />
      )}
      
      <div className="curve-preview">
        <CurvePreviewGraph keyframe={keyframe} />
      </div>
    </div>
  );
};
```

## 백엔드 API 설계

### 1. 애니메이션 관리 API
```ruby
# app/controllers/api/v1/animations_controller.rb
class Api::V1::AnimationsController < Api::V1::BaseController
  before_action :set_project
  before_action :set_animation, only: [:show, :update, :destroy, :duplicate]
  
  def index
    animations = @project.animations.includes(:animation_tracks)
    render json: AnimationSerializer.new(animations, include: [:animation_tracks])
  end
  
  def create
    animation = @project.animations.build(animation_params)
    
    if animation.save
      # 기본 트랙들 자동 생성
      create_default_tracks(animation)
      render json: AnimationSerializer.new(animation), status: :created
    else
      render json: { errors: animation.errors }, status: :unprocessable_entity
    end
  end
  
  def update
    if @animation.update(animation_params)
      render json: AnimationSerializer.new(@animation)
    else
      render json: { errors: @animation.errors }, status: :unprocessable_entity
    end
  end
  
  def duplicate
    new_animation = @animation.dup
    new_animation.name = "#{@animation.name}_copy"
    
    if new_animation.save
      # 트랙과 키프레임 복사
      duplicate_tracks_and_keyframes(@animation, new_animation)
      render json: AnimationSerializer.new(new_animation), status: :created
    else
      render json: { errors: new_animation.errors }, status: :unprocessable_entity
    end
  end
  
  def preview
    # 실시간 애니메이션 프리뷰 데이터 생성
    preview_data = AnimationPreviewService.new(@animation).generate_preview
    render json: preview_data
  end
  
  private
  
  def set_project
    @project = current_user.projects.find(params[:project_id])
  end
  
  def set_animation
    @animation = @project.animations.find(params[:id])
  end
  
  def animation_params
    params.require(:animation).permit(:name, :description, :duration, :fps, :loop_mode)
  end
  
  def create_default_tracks(animation)
    # 각 본에 대해 기본 트랙 생성
    @project.bones.each do |bone|
      %w[rotation translation scale].each do |property_type|
        animation.animation_tracks.create!(
          bone: bone,
          property_type: property_type
        )
      end
    end
    
    # 각 레이어에 대해 기본 트랙 생성  
    @project.layers.each do |layer|
      %w[color attachment].each do |property_type|
        animation.animation_tracks.create!(
          layer: layer,
          property_type: property_type
        )
      end
    end
  end
end
```

### 2. 키프레임 관리 API
```ruby
# app/controllers/api/v1/keyframes_controller.rb
class Api::V1::KeyframesController < Api::V1::BaseController
  def bulk_create
    keyframes_data = params[:keyframes]
    created_keyframes = []
    
    ActiveRecord::Base.transaction do
      keyframes_data.each do |keyframe_data|
        track = AnimationTrack.find(keyframe_data[:animation_track_id])
        keyframe = track.keyframes.create!(keyframe_params(keyframe_data))
        created_keyframes << keyframe
      end
    end
    
    render json: KeyframeSerializer.new(created_keyframes), status: :created
  end
  
  def bulk_update
    updates = params[:keyframe_updates]
    
    ActiveRecord::Base.transaction do
      updates.each do |update|
        keyframe = Keyframe.find(update[:id])
        keyframe.update!(keyframe_params(update))
      end
    end
    
    render json: { status: 'success' }
  end
  
  def bulk_delete
    keyframe_ids = params[:keyframe_ids]
    
    Keyframe.where(id: keyframe_ids).destroy_all
    
    render json: { status: 'success' }
  end
  
  # 키프레임 간 보간값 계산
  def interpolate
    track_id = params[:track_id]
    time = params[:time].to_f
    
    track = AnimationTrack.find(track_id)
    interpolated_value = InterpolationService.new(track).interpolate_at_time(time)
    
    render json: { 
      time: time,
      value: interpolated_value,
      track_id: track_id
    }
  end
  
  private
  
  def keyframe_params(data)
    data.permit(
      :time, :rotation_value, :x_value, :y_value, :color_value, :string_value,
      :curve_type, :curve_c1, :curve_c2, :curve_c3, :curve_c4
    )
  end
end
```

## 구현 로드맵

### Week 1-2: 데이터 모델 및 기본 API
- [x] Animation, AnimationTrack, Keyframe 모델 구현
- [x] 데이터베이스 마이그레이션
- [x] 기본 CRUD API 엔드포인트

### Week 3: 타임라인 UI 기본 구조
- [x] Timeline 컴포넌트 구현
- [x] TimelineTrack 컴포넌트
- [x] 기본 키프레임 시각화

### Week 4: 키프레임 편집 시스템
- [x] 키프레임 추가/삭제/이동
- [x] KeyframeEditor 컴포넌트
- [x] 속성별 값 편집 UI

### Week 5: 애니메이션 재생 시스템
- [x] AnimationPlayer 컴포넌트
- [x] pixi-spine 통합
- [x] 재생 컨트롤 UI

### Week 6: 고급 기능 및 최적화
- [x] 베지어 커브 에디터
- [x] 보간 서비스
- [x] 애니메이션 익스포트 통합

## 성공 지표

1. **기능성**: 완전한 키프레임 애니메이션 시스템
2. **성능**: 60fps 실시간 애니메이션 재생
3. **사용성**: 직관적인 타임라인 및 키프레임 편집
4. **호환성**: Spine 런타임 완벽 호환