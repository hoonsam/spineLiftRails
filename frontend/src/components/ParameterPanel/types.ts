export interface MeshParameters {
  maxVertices?: number;
  quality?: number;
  simplification?: number;
  boundaryAccuracy?: number;
  interiorAccuracy?: number;
  smoothing?: number;
  edgeThreshold?: number;
  // Legacy parameters
  detailFactor?: number;
  alphaThreshold?: number;
  maxTriangles?: number;
}

export interface ParameterConfig {
  key: keyof MeshParameters;
  label: string;
  min: number;
  max: number;
  step: number;
  defaultValue: number;
  unit?: string;
  description: string;
}

export interface MeshPreset {
  id: string;
  name: string;
  description?: string;
  parameters: MeshParameters;
  isSystem: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface ParameterPanelProps {
  meshId: string;
  layerId: string;
  projectId: string;
  initialParameters?: MeshParameters;
  disabled?: boolean;
  onParameterChange?: (params: MeshParameters) => void;
  onRegenerateMesh?: () => void;
}