export interface User {
  id: string;
  email: string;
  name: string;
}

export interface Project {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  psd_file_url?: string;
}

export interface Layer {
  id: string;
  project_id: string;
  name: string;
  position: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  image_url?: string;
  bounds?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  mesh?: Mesh;
  error_message?: string;
}

export interface Mesh {
  id: string;
  layer_id: string;
  data: {
    vertices: number[][];
    triangles: number[][];
    uvs: number[];
  };
  parameters: MeshParameters;
  metadata?: {
    vertex_count: number;
    triangle_count: number;
  };
}

export interface MeshParameters {
  maxVertices?: number;
  quality?: number;
  simplification?: number;
  boundaryAccuracy?: number;
  interiorAccuracy?: number;
  smoothing?: number;
  edgeThreshold?: number;
  // Legacy parameters
  detail_factor?: number;
  alpha_threshold?: number;
  concave_factor?: number;
  internal_vertex_density?: number;
  blur_kernel_size?: number;
  binary_threshold?: number;
  min_contour_area?: number;
}