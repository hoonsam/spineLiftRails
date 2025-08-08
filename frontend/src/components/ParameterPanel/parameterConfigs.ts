import type { ParameterConfig, MeshPreset, MeshParameters } from './types';

export const parameterConfigs: ParameterConfig[] = [
  {
    key: 'maxVertices',
    label: '최대 버텍스',
    min: 100,
    max: 5000,
    step: 100,
    defaultValue: 1000,
    description: '메시의 최대 버텍스 수를 설정합니다'
  },
  {
    key: 'quality',
    label: '품질',
    min: 0.1,
    max: 1.0,
    step: 0.05,
    defaultValue: 0.6,
    description: '메시 생성 품질을 조정합니다'
  },
  {
    key: 'simplification',
    label: '단순화',
    min: 0.0,
    max: 0.5,
    step: 0.05,
    defaultValue: 0.15,
    description: '메시 단순화 정도를 설정합니다'
  },
  {
    key: 'boundaryAccuracy',
    label: '경계 정확도',
    min: 0.5,
    max: 1.0,
    step: 0.05,
    defaultValue: 0.8,
    description: '이미지 경계선의 정확도를 조정합니다'
  },
  {
    key: 'interiorAccuracy',
    label: '내부 정확도',
    min: 0.5,
    max: 1.0,
    step: 0.05,
    defaultValue: 0.7,
    description: '메시 내부의 정확도를 조정합니다'
  },
  {
    key: 'smoothing',
    label: '스무딩',
    min: 0.0,
    max: 1.0,
    step: 0.05,
    defaultValue: 0.3,
    description: '메시 표면의 부드러움을 조정합니다'
  },
  {
    key: 'edgeThreshold',
    label: '엣지 임계값',
    min: 10,
    max: 200,
    step: 10,
    defaultValue: 50,
    description: '엣지 검출 임계값을 설정합니다'
  }
];

export const systemPresets: MeshPreset[] = [
  {
    id: 'low',
    name: '저품질 (빠른 처리)',
    description: '빠른 처리를 위한 낮은 품질 설정',
    parameters: {
      maxVertices: 500,
      quality: 0.3,
      simplification: 0.3,
      boundaryAccuracy: 0.6,
      interiorAccuracy: 0.5,
      smoothing: 0.2,
      edgeThreshold: 100
    },
    isSystem: true
  },
  {
    id: 'medium',
    name: '중간 품질 (균형)',
    description: '속도와 품질의 균형잡힌 설정',
    parameters: {
      maxVertices: 1000,
      quality: 0.6,
      simplification: 0.15,
      boundaryAccuracy: 0.8,
      interiorAccuracy: 0.7,
      smoothing: 0.3,
      edgeThreshold: 50
    },
    isSystem: true
  },
  {
    id: 'high',
    name: '고품질 (정밀)',
    description: '높은 품질의 정밀한 메시 생성',
    parameters: {
      maxVertices: 2000,
      quality: 0.9,
      simplification: 0.05,
      boundaryAccuracy: 0.95,
      interiorAccuracy: 0.9,
      smoothing: 0.4,
      edgeThreshold: 20
    },
    isSystem: true
  }
];

export const getDefaultParameters = (): MeshParameters => {
  const defaults: MeshParameters = {};
  parameterConfigs.forEach(config => {
    defaults[config.key] = config.defaultValue;
  });
  return defaults;
};