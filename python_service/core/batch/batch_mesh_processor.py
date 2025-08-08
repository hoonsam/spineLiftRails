#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SpineLift - BatchMeshProcessor
여러 이미지에 대해 spine_mesh_tool과 유사한 메시 생성 로직을 일괄 적용

이식된 핵심 기능:
1. 이미지 로드 및 마스크 생성 (image_processor 로직)
2. 컨투어 추출 및 단순화 (mesh_generator 로직)
3. 삼각분할 및 메시 생성 (triangulation 로직)
4. Spine JSON 데이터 구조 생성 (이 파일에서는 직접 생성하지 않고, 메시 데이터만 반환)
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import cv2
import numpy as np
import logging

# 예제 사용을 위한 추가 임포트 (파일 하단 if __name__ == '__main__' 블록에서만 사용)
from PIL import Image, ImageDraw
import tempfile

try:
    from core.utils.mesh_utils import generate_standard_uvs
except ImportError:
    # Fallback for when mesh_utils is not available
    def generate_standard_uvs(vertices, width, height):
        """Simple UV generation fallback"""
        uvs = []
        for v in vertices:
            u = v[0] / width
            v_coord = 1.0 - (v[1] / height)  # Flip Y for UV coordinates
            uvs.append([u, v_coord])
        return np.array(uvs)

logger = logging.getLogger(__name__)

try:
    import triangle as tr
except ImportError:
    logger.warning("Triangle library not available. Mesh generation will be limited.")
    tr = None


class BatchMeshProcessor:
    """
    spine_mesh_tool의 검증된 로직을 이식하여 여러 이미지에 대한 메시 생성을 일괄 처리하는 클래스입니다.
    이미지 로드, 마스크 생성, 컨투어 추출 및 단순화, 삼각분할을 수행하여
    메시의 정점(vertices), 삼각형(triangles), UV 좌표 등을 포함하는 데이터를 생성합니다.
    """
    
    DEFAULT_PARAMS: Dict[str, Union[float, int]] = {
        "detail_factor": 0.01,         # 컨투어 단순화 시 디테일 수준 (0.001 ~ 0.050)
        "alpha_threshold": 10,         # 초기 마스크 생성 시 알파 채널 임계값
        "concave_factor": 0.0,         # 컨투어 단순화 시 오목한 부분 유지 수준 (0.0 ~ 100.0)
        "internal_vertex_density": 0,  # 내부 정점 밀도 (0이면 사용 안함, 높을수록 조밀)
        "blur_kernel_size": 1,         # 마스크 블러 처리 시 커널 크기 (홀수)
        "binary_threshold": 128,       # 마스크 이진화 임계값
        "min_contour_area": 10,        # 컨투어 필터링 시 최소 면적
        "density_scaling_factor": 1000.0, # 밀도-면적 변환 시 스케일링 팩터
        "min_triangle_area": 1.0       # 삼각분할 시 최소 삼각형 면적
    }
    
    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        """
        BatchMeshProcessor 인스턴스를 초기화합니다.

        제공된 파라미터로 메시 생성 설정을 구성합니다. 파라미터가 없으면
        `DEFAULT_PARAMS`에 정의된 기본값을 사용합니다.

        Args:
            params: 메시 생성에 사용될 파라미터 딕셔너리.
                    키는 `DEFAULT_PARAMS`의 키와 일치해야 합니다.
                    예: {"detail_factor": 0.02, "alpha_threshold": 5}
        """
        self.params: Dict[str, Union[float, int]] = {**self.DEFAULT_PARAMS}
        if params:
            # 제공된 파라미터 중 DEFAULT_PARAMS에 있는 키만 업데이트
            valid_params = {k: v for k, v in params.items() if k in self.DEFAULT_PARAMS}
            self.params.update(valid_params)
            # 사용자가 DEFAULT_PARAMS에 없는 키를 제공한 경우 경고
            invalid_keys = [k for k in params if k not in self.DEFAULT_PARAMS]
            if invalid_keys:
                logger.warning(f"Ignored invalid parameters: {invalid_keys}")
        
        logger.info(f"Initialized with params: {self.params}")
    
    def load_image(self, image_path_str: str) -> Tuple[Optional[np.ndarray], int, int]:
        """
        지정된 경로에서 이미지를 로드하고, 이미지 객체, 높이, 너비를 반환합니다.
        spine_mesh_tool image_processor.load_image() 기능을 이식했습니다.
        유니코드 경로 지원을 위해 PIL을 우선 사용하고, numpy.fromfile + cv2.imdecode도 시도합니다.

        Args:
            image_path_str: 로드할 이미지 파일의 경로 문자열.

        Returns:
            Tuple[Optional[np.ndarray], int, int]:
                - 성공 시: (로드된 이미지 NumPy 배열, 이미지 높이, 이미지 너비)
                - 실패 시: (None, 0, 0)
        """
        image_file = Path(image_path_str)
        if not image_file.exists() or not image_file.is_file():
            logger.error(f"Image file not found or is not a file: {image_path_str}")
            return None, 0, 0
            
        # 방법 1: PIL을 사용한 유니코드 경로 지원
        try:
            from PIL import Image
            logger.debug(f"Attempting PIL image load: {image_file.name}")
            pil_image = Image.open(str(image_file)).convert('RGBA')
            
            # PIL 이미지를 OpenCV 형식으로 변환 (RGBA -> BGRA)
            img_array = np.array(pil_image)
            img = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
            
            if img is not None:
                h, w = img.shape[:2]
                logger.info(f"Successfully loaded image via PIL: {image_file.name} ({w}x{h})")
                return img, h, w
                
        except Exception as pil_e:
            logger.warning(f"PIL method failed for {image_file.name}: {pil_e}")
        
        # 방법 2: numpy.fromfile + cv2.imdecode (유니코드 경로 대안)
        try:
            logger.debug(f"Attempting numpy.fromfile + cv2.imdecode: {image_file.name}")
            
            # 파일을 바이트로 읽어서 OpenCV 디코딩
            file_bytes = np.fromfile(str(image_file), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
            
            if img is not None:
                h, w = img.shape[:2]
                logger.info(f"Successfully loaded image via numpy+cv2: {image_file.name} ({w}x{h})")
                return img, h, w
                
        except Exception as numpy_e:
            logger.warning(f"numpy.fromfile method failed for {image_file.name}: {numpy_e}")
            
        # 방법 3: 기존 cv2.imread 폴백 (ASCII 경로용)
        try:
            logger.debug(f"Attempting cv2.imread fallback: {image_file.name}")
            img = cv2.imread(str(image_file), cv2.IMREAD_UNCHANGED)
            if img is not None:
                h, w = img.shape[:2]
                logger.info(f"Successfully loaded image via cv2.imread: {image_file.name} ({w}x{h})")
                return img, h, w
                
        except Exception as cv2_e:
            logger.warning(f"cv2.imread fallback failed for {image_file.name}: {cv2_e}")
        
        # 모든 방법 실패
        logger.error(f"All image loading methods failed for: {image_path_str}")
        return None, 0, 0
    
    def create_initial_mask(self, img: np.ndarray, h: int, w: int) -> Optional[np.ndarray]:
        """
        입력 이미지로부터 초기 마스크를 생성합니다.
        이미지에 알파 채널이 있으면 이를 사용하고, 없으면 전체가 불투명한 마스크를 생성합니다.
        spine_mesh_tool image_processor.create_initial_mask() 기능을 이식했습니다.

        Args:
            img: 원본 이미지 NumPy 배열.
            h: 이미지 높이.
            w: 이미지 너비.

        Returns:
            Optional[np.ndarray]: 생성된 마스크 NumPy 배열. 이미지 입력이 None이면 None 반환.
        """
        if img is None:
            logger.warning("Cannot create mask from None image input.")
            return None
            
        if img.ndim == 3 and img.shape[2] == 4: # BGRA 또는 RGBA 가정
            mask = img[:, :, 3] # 알파 채널
            if np.all(mask < self.params["alpha_threshold"]):
                logger.warning(f"Alpha channel for image ({w}x{h}) is mostly transparent (all values < {self.params['alpha_threshold']}). Mesh might be empty or small.")
            elif np.all(mask == 255):
                logger.info(f"Using fully opaque alpha channel mask for image ({w}x{h}).")
            else:
                logger.info(f"Using alpha channel as mask for image ({w}x{h}).")
        else:
            mask = np.ones((h, w), dtype=np.uint8) * 255
            logger.info(f"Creating full opaque mask for image ({w}x{h}) (no alpha channel or not 4-channel image).")
            
        return mask
    
    def process_mask_for_contours(self, mask: np.ndarray, blur_kernel_size_param: int, binary_threshold_param: int) -> Optional[np.ndarray]:
        """
        입력 마스크에 블러(GaussianBlur) 및 이진화(threshold) 처리를 적용하여 컨투어 추출에 적합한 형태로 만듭니다.
        spine_mesh_tool image_processor.process_mask_for_contours() 기능을 이식했습니다.

        Args:
            mask: 원본 마스크 NumPy 배열.
            blur_kernel_size_param: 가우시안 블러 커널 크기. 홀수여야 하며, 1 이하면 블러 미적용.
            binary_threshold_param: 이진화 임계값 (0-255).

        Returns:
            Optional[np.ndarray]: 처리된 이진 마스크 NumPy 배열. 입력 마스크가 None이면 None 반환.
        """
        if mask is None:
            logger.warning("Cannot process None mask input.")
            return None
            
        processed_mask = mask.copy()
        kernel_size = int(blur_kernel_size_param)
        
        if kernel_size > 0 and kernel_size % 2 == 0:
            kernel_size += 1
            logger.debug(f"Adjusted blur kernel size to be odd: {kernel_size}")
            
        if kernel_size > 1:
            logger.info(f"Applying simple blur (kernel: {kernel_size}x{kernel_size}) to mask.")
            processed_mask = cv2.blur(processed_mask, (kernel_size, kernel_size))
        else:
            logger.info("Skipping simple blur (kernel_size <= 1).")
        
        threshold_value = int(np.clip(binary_threshold_param, 0, 255))
        logger.info(f"Applying binary threshold (value: {threshold_value}) to mask.")
        _, binary_mask = cv2.threshold(processed_mask, threshold_value, 255, cv2.THRESH_BINARY)
        
        return binary_mask
    
    def find_main_contour(self, binary_mask: np.ndarray) -> Optional[np.ndarray]:
        """
        이진 마스크에서 가장 큰 외부 컨투어를 찾습니다.
        spine_mesh_tool image_processor.find_main_contour() 기능을 이식했습니다.

        Args:
            binary_mask: 이진화된 마스크 NumPy 배열.

        Returns:
            Optional[np.ndarray]: 찾은 가장 큰 컨투어 (OpenCV 컨투어 형식).
                                 컨투어를 찾지 못하거나 입력이 유효하지 않으면 None 반환.
                                 컨투어는 [[x1, y1], [x2, y2], ...] 형태의 2D 점들의 배열입니다.
        """
        if binary_mask is None:
            logger.warning("Cannot find contours in None mask input.")
            return None
        
        if binary_mask.dtype != np.uint8 or binary_mask.ndim != 2:
            logger.error(f"Invalid mask format for findContours. Expected 8-bit single channel, got {binary_mask.dtype} with {binary_mask.ndim} dimensions.")
            return None
            
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            logger.warning("No contours found in the binary mask.")
            return None
            
        min_contour_area = self.params.get("min_contour_area", 10) # type: ignore
        significant_contours = [c for c in contours if cv2.contourArea(c) >= min_contour_area]
        
        if not significant_contours:
            logger.warning(f"No significant contours found (area >= {min_contour_area}). Found {len(contours)} raw contours.")
            return None
            
        main_contour = max(significant_contours, key=cv2.contourArea)
        logger.info(f"Found main contour with {len(main_contour)} points. Area: {cv2.contourArea(main_contour):.2f}")
        return main_contour
    
    def simplify_contour(self, contour: np.ndarray, w: int, h: int, detail_factor_param: float, concave_factor_param: float) -> Tuple[np.ndarray, bool]:
        """
        Douglas-Peucker 알고리즘을 사용하여 컨투어를 단순화합니다.
        spine_mesh_tool mesh_generator.simplify_contour() 기능을 이식했습니다.

        Args:
            contour: 단순화할 원본 컨투어 NumPy 배열.
            w: 원본 이미지 너비 (기본 사각형 생성 시 사용).
            h: 원본 이미지 높이 (기본 사각형 생성 시 사용).
            detail_factor_param: 단순화 정밀도에 영향을 미치는 요소 (0.001 ~ 0.050). 작을수록 디테일 유지.
            concave_factor_param: 오목한 부분을 유지하려는 정도 (0.0 ~ 100.0). 클수록 오목한 부분 유지.

        Returns:
            Tuple[np.ndarray, bool]:
                - 단순화된 컨투어 NumPy 배열 ((N, 2) 형태).
                - 성공 여부 (True: 성공, False: 실패 또는 기본 사각형 반환).
        """
        default_rect = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.int32)

        if contour is None or len(contour) < 3:
            logger.warning(f"Using default rectangle ({w}x{h}) due to insufficient contour points (found {len(contour) if contour is not None else 0}).")
            return default_rect.copy(), False # type: ignore
            
        try:
            reshaped_contour = contour.reshape(-1, 2) if contour.ndim == 3 and contour.shape[1] == 1 else contour

            arc_length = cv2.arcLength(reshaped_contour, True)
            if arc_length == 0:
                logger.warning(f"Using default rectangle ({w}x{h}) due to zero arc length for contour.")
                return default_rect.copy(), False # type: ignore
            
            min_detail, max_detail = 0.001, 0.050
            min_eps_perc, max_eps_perc = 0.03, 0.002
            
            clamped_detail_factor = np.clip(detail_factor_param, min_detail, max_detail)
            normalized_detail = (clamped_detail_factor - min_detail) / (max_detail - min_detail) if (max_detail - min_detail) != 0 else 0.5
            epsilon_perc = max_eps_perc + (1.0 - np.sqrt(normalized_detail)) * (min_eps_perc - max_eps_perc)
            epsilon = epsilon_perc * arc_length
            
            clamped_concave_factor = np.clip(concave_factor_param, 0.0, 100.0)
            concave_multiplier = 1.0 + (clamped_concave_factor / 100.0) * 4.0
            epsilon *= concave_multiplier
            epsilon = max(0.1, epsilon)
            
            logger.info(f"Simplifying contour: detail_factor={detail_factor_param:.3f} (norm:{normalized_detail:.3f}), "
                        f"concave_factor={concave_factor_param:.1f} (mult:{concave_multiplier:.2f}), "
                        f"arc_length={arc_length:.1f}, calculated_epsilon={epsilon:.3f}")
            
            approx_contour = cv2.approxPolyDP(reshaped_contour.reshape(-1, 1, 2), epsilon, True)
            pts_simplified = approx_contour.reshape(-1, 2)
            
            if len(pts_simplified) < 3:
                logger.warning(f"Simplified contour has less than 3 points ({len(pts_simplified)}). Using default rectangle.")
                return default_rect.copy(), False # type: ignore
                
            logger.info(f"Contour simplified from {len(reshaped_contour)} to {len(pts_simplified)} points.")
            return pts_simplified.astype(np.int32), True
            
        except Exception as e:
            logger.error(f"Error during contour simplification: {e}", exc_info=True)
            return default_rect.copy(), False # type: ignore
    
    def triangulate_mesh(self, pts_simplified: np.ndarray, w: int, h: int, internal_vertex_density_param: float) -> Optional[Dict[str, Any]]:
        """
        단순화된 컨투어 포인트를 사용하여 삼각분할(triangulation)을 수행하고 메시 데이터를 생성합니다.
        spine_mesh_tool mesh_generator.triangulate_and_pad() 기능을 이식했습니다.

        Args:
            pts_simplified: 단순화된 컨투어 포인트 NumPy 배열 ((N, 2) 형태).
            w: 원본 이미지 너비 (내부 정점 밀도 계산 시 사용).
            h: 원본 이미지 높이 (내부 정점 밀도 계산 시 사용).
            internal_vertex_density_param: 메시 내부 정점 밀도. 0이면 사용 안 함. 높을수록 조밀.

        Returns:
            Optional[Dict[str, Any]]: 
                성공 시 삼각분할 결과 딕셔너리. 포함된 키:
                - "vertices": 메시 정점 NumPy 배열 ((M, 2) 형태).
                - "triangles": 메시 삼각형 인덱스 NumPy 배열 ((T, 3) 형태).
                - "boundary_indices": 원본 입력 정점(pts_simplified)에 해당하는 출력 정점 인덱스 리스트.
                실패 시 None 반환.
        """
        if tr is None:
            logger.error("Triangle library not available. Cannot perform triangulation.")
            return None
            
        if pts_simplified is None or len(pts_simplified) < 3:
            logger.warning(f"Insufficient points ({len(pts_simplified) if pts_simplified is not None else 0}) for triangulation.")
            return None
            
        try:
            triangulation_input_pts = pts_simplified.astype(np.float64)
            num_input_pts = len(triangulation_input_pts)
            segments = np.array([[i, (i + 1) % num_input_pts] for i in range(num_input_pts)], dtype=np.int32)
            input_dict = {"vertices": triangulation_input_pts, "segments": segments}
            tri_opts = "p" # Planar Straight Line Graph (PSLG)
            
            if internal_vertex_density_param > 0:
                max_area = self._map_density_to_area(internal_vertex_density_param, w, h)
                if max_area and max_area > 0:
                    tri_opts += f"a{max_area:.10f}"
                    logger.info(f"Using max area constraint for triangulation: {max_area:.6f}")
            
            logger.info(f"Triangulating with options: \"{tri_opts}\"")
            
            t = tr.triangulate(input_dict, tri_opts)
            output_vertices: Optional[np.ndarray] = t.get("vertices")
            output_triangles: Optional[np.ndarray] = t.get("triangles")
            
            if output_vertices is None or output_triangles is None or len(output_vertices) < 3 or len(output_triangles) == 0:
                logger.error("Triangulation failed: no/insufficient vertices or triangles returned by 'triangle' library.")
                return None
            
            logger.info(f"Triangulation successful: {len(output_vertices)} vertices, {len(output_triangles)} triangles.")
            return {
                "vertices": output_vertices,
                "triangles": output_triangles,
                "boundary_indices": list(range(num_input_pts))
            }
            
        except Exception as e:
            logger.error(f"Exception during triangulation: {e}", exc_info=True)
            return None
    
    def _map_density_to_area(self, density: float, w: int, h: int) -> Optional[float]:
        """
        내부 정점 밀도(density)를 삼각분할 시 사용할 최대 삼각형 면적(max_area)으로 변환합니다.
        spine_mesh_tool utils.helpers.map_density_to_area() 로직을 기반으로 합니다.
        밀도가 높을수록 최대 면적은 작아져 더 조밀한 메시가 생성됩니다.

        Args:
            density: 내부 정점 밀도 값. 0 이하면 None을 반환하여 면적 제한을 적용하지 않도록 합니다.
            w: 이미지 너비.
            h: 이미지 높이.

        Returns:
            Optional[float]: 계산된 최대 삼각형 면적. density가 0 이하면 None.
                             최소 설정된 면적(min_triangle_area)을 보장합니다.
        """
        if not (density > 0 and w > 0 and h > 0):
            logger.debug(f"Invalid input for density mapping: density={density}, w={w}, h={h}. Skipping area constraint.")
            return None
            
        image_area = float(w * h)
        scaling_factor: float = self.params.get("density_scaling_factor", 1000.0) # type: ignore
        max_area_val = image_area / (density * scaling_factor)
        
        min_allowed_area: float = self.params.get("min_triangle_area", 1.0) # type: ignore
        calculated_area = max(min_allowed_area, max_area_val)
        logger.debug(f"Mapped density {density} to max_area {calculated_area:.6f} for image size {w}x{h}.")
        return calculated_area
    
    def _calculate_mesh_edges(self, triangles: np.ndarray, num_vertices: int) -> Tuple[List[int], List[int]]:
        """외곽선과 내부 엣지를 구분하여 계산
        
        Args:
            triangles: 삼각형 인덱스 배열 ((N, 3) 형태)
            num_vertices: 총 정점 수
            
        Returns:
            Tuple[boundary_edges, internal_edges]: 외곽선 엣지와 내부 엣지 리스트 (정점 인덱스 기준)
        """
        from collections import defaultdict
        
        # 엣지 사용 횟수 카운트 (정점 인덱스 기준)
        edge_count = defaultdict(int)
        
        # 삼각형에서 모든 엣지 추출
        for triangle in triangles:
            v1, v2, v3 = triangle
            
            # 삼각형의 세 엣지 (작은 인덱스를 먼저 오도록 정규화)
            edges = [
                (min(v1, v2), max(v1, v2)),
                (min(v2, v3), max(v2, v3)),
                (min(v3, v1), max(v3, v1))
            ]
            
            for edge in edges:
                edge_count[edge] += 1
        
        # 외곽선과 내부 엣지 분리
        boundary_edges = []
        internal_edges = []
        
        for edge, count in edge_count.items():
            v1, v2 = edge
            
            if count == 1:
                # 한 번만 사용되는 엣지 = 외곽선
                boundary_edges.extend([v1, v2])
            else:
                # 두 번 이상 사용되는 엣지 = 내부 엣지
                internal_edges.extend([v1, v2])
        
        logger.debug(f"메시 엣지 계산 완료: 외곽선 {len(boundary_edges)//2}개, 내부 엣지 {len(internal_edges)//2}개")
        
        return boundary_edges, internal_edges
    
    def generate_mesh_data(self, image_path_str: str) -> Optional[Dict[str, Any]]:
        """
        단일 이미지에 대해 전체 메시 생성 파이프라인을 실행합니다.
        이미지 로드, 마스크 생성, 컨투어 추출/단순화, 삼각분할, UV 좌표 생성을 포함합니다.
        spine_mesh_tool의 logic_facade.generate_preview_data() 로직을 주로 이식했습니다.

        Args:
            image_path_str: 처리할 이미지 파일의 경로.

        Returns:
            Optional[Dict[str, Any]]: 
                성공 시 생성된 메시 데이터 딕셔너리. 포함된 키:
                - "image_path": 원본 이미지 경로 (str).
                - "image_name": 확장자를 제외한 이미지 이름 (str).
                - "width": 이미지 너비 (int).
                - "height": 이미지 높이 (int).
                - "vertices": 메시 정점 NumPy 배열 ((N, 2) 형태, float).
                - "triangles": 메시 삼각형 인덱스 NumPy 배열 ((M, 3) 형태, int).
                - "uvs": UV 좌표 리스트 ([u1, v1, u2, v2, ...], float).
                - "boundary_indices": 원본 컨투어 정점에 해당하는 메시 정점 인덱스 리스트 (List[int]).
                - "boundary_edges": 외곽선 엣지 리스트 (List[Tuple[int, int]]).
                - "internal_edges": 내부 엣지 리스트 (List[Tuple[int, int]]).
                - "params_used": 생성에 사용된 파라미터 딕셔너리 (Dict[str, Any]).
                - "x": 이미지 중심 X 좌표 (float, 본 위치 계산용).
                - "y": 이미지 중심 Y 좌표 (float, 본 위치 계산용).
                실패 시 None 반환.
        """
        current_image_path = Path(image_path_str)
        logger.info(f"Processing image: {current_image_path.name}")
        
        img, h, w = self.load_image(image_path_str)
        if img is None or h == 0 or w == 0:
            logger.error(f"Failed to load image or image has zero dimensions: {current_image_path.name}")
            return None
        
        mask = self.create_initial_mask(img, h, w)
        if mask is None:
            logger.error(f"Failed to create initial mask for {current_image_path.name}")
            return None
        
        binary_mask = self.process_mask_for_contours(
            mask,
            self.params["blur_kernel_size"], # type: ignore
            self.params["binary_threshold"] # type: ignore
        )
        if binary_mask is None:
            logger.error(f"Failed to process mask for contours for {current_image_path.name}")
            return None
        
        contour = self.find_main_contour(binary_mask)
        if contour is None:
            logger.error(f"Failed to find main contour in {current_image_path.name}")
            return None
        
        pts_simplified, success = self.simplify_contour(
            contour, w, h,
            self.params["detail_factor"], # type: ignore
            self.params["concave_factor"] # type: ignore
        )
        if not success:
            logger.warning(f"Contour simplification for {current_image_path.name} used fallback (default rectangle).")
        
        mesh_result = self.triangulate_mesh(
            pts_simplified, w, h,
            self.params["internal_vertex_density"] # type: ignore
        )
        if mesh_result is None or "vertices" not in mesh_result or "triangles" not in mesh_result:
            logger.error(f"Failed to triangulate mesh for {current_image_path.name}")
            return None
        
        vertices_for_uv: np.ndarray = mesh_result["vertices"]
        uvs = generate_standard_uvs(vertices_for_uv.flatten().tolist(), w, h)
        
        # 외곽선과 내부 엣지 계산 (렌더링 개선용)
        boundary_edges, internal_edges = self._calculate_mesh_edges(
            mesh_result["triangles"], len(mesh_result["vertices"])
        )
        
        center_x = w / 2.0
        center_y = h / 2.0
        
        result: Dict[str, Any] = {
            "image_path": image_path_str,
            "image_name": current_image_path.stem,
            "width": w,
            "height": h,
            "vertices": mesh_result["vertices"],
            "triangles": mesh_result["triangles"],
            "uvs": uvs,
            "boundary_indices": mesh_result.get("boundary_indices", []),
            "boundary_edges": boundary_edges,  # 외곽선 엣지 추가
            "internal_edges": internal_edges,  # 내부 엣지 추가
            "params_used": self.params.copy(),
            "x": center_x,
            "y": center_y
        }
        
        logger.info(f"Successfully generated mesh data for {result['image_name']}.")
        return result
    
    def process_image_batch(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        여러 이미지 파일 경로 목록을 받아 배치로 메시 생성을 처리합니다.

        Args:
            image_paths: 처리할 이미지 파일 경로들의 리스트.

        Returns:
            List[Dict[str, Any]]: 성공적으로 처리된 각 이미지의 메시 데이터 딕셔너리 리스트.
                                 실패한 이미지는 결과에 포함되지 않습니다.
        """
        results: List[Dict[str, Any]] = []
        total_count = len(image_paths)
        if total_count == 0:
            logger.info("Empty image batch provided. Nothing to process.")
            return results
            
        logger.info(f"Starting batch processing for {total_count} images.")
        
        for i, image_path_str_item in enumerate(image_paths, 1):
            current_image_file_item = Path(image_path_str_item)
            logger.info(f"Processing image {i}/{total_count}: {current_image_file_item.name}") 
            try:
                mesh_data = self.generate_mesh_data(image_path_str_item)
                if mesh_data:
                    results.append(mesh_data)
                    logger.info(f"Successfully processed image {i}/{total_count}: {current_image_file_item.name}")
                else:
                    logger.warning(f"Failed to generate mesh data for image {i}/{total_count}: {current_image_file_item.name}. Skipping.")
            except Exception as e:
                logger.error(f"Unhandled exception during processing image {i}/{total_count} ({current_image_file_item.name}): {e}", exc_info=True)
        
        success_count = len(results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        logger.info(f"Batch processing complete: {success_count}/{total_count} images processed successfully ({success_rate:.1f}%).")
        return results


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG, # 상세 로그 확인을 위해 DEBUG로 변경
        format='%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s',
        handlers=[logging.StreamHandler()]
    )

    logger.info("BatchMeshProcessor example started.")

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        logger.info(f"Created temporary directory for images: {temp_dir}")

        image_paths_to_process: List[str] = []

        def create_test_image(file_path: Path, size: Tuple[int, int], draw_commands: callable) -> None:
            """Helper to create a test image."""
            try:
                img = Image.new("RGBA", size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                draw_commands(draw)
                img.save(file_path)
                image_paths_to_process.append(str(file_path))
                logger.info(f"Created test image: {file_path.name} at {file_path}")
            except Exception as e_create:
                logger.error(f"Failed to create test image {file_path.name}: {e_create}", exc_info=True)

        create_test_image(
            temp_dir / "01_rectangle_opaque.png", (100, 150),
            lambda draw: draw.rectangle([(20, 30), (80, 120)], fill=(255, 0, 0, 255))
        )
        create_test_image(
            temp_dir / "02_circle_transparent_alpha.png", (120, 120),
            lambda draw: draw.ellipse([(10, 10), (110, 110)], fill=(0, 255, 0, 180))
        )
        create_test_image(
            temp_dir / "03_star_complex_shape.png", (200, 200),
            lambda draw: draw.polygon([
                (100, 20), (120, 70), (180, 80), (130, 120),
                (150, 180), (100, 150), (50, 180), (70, 120),
                (20, 80), (80, 70)
            ], fill=(0, 0, 255, 255))
        )
        create_test_image( # 이미지 전체가 투명한 경우 테스트
            temp_dir / "04_fully_transparent.png", (50, 50),
            lambda draw: draw.rectangle([(0,0), (50,50)], fill=(0,0,0,0))
        )
        create_test_image( # 매우 작은 이미지
            temp_dir / "05_tiny_image.png", (5, 5),
            lambda draw: draw.rectangle([(1,1), (4,4)], fill=(255,255,0,255))
        )

        non_existent_path_str = str(temp_dir / "06_fake_image_non_existent.png")
        image_paths_to_process.append(non_existent_path_str)
        logger.info(f"Added non-existent image path for failure test: {non_existent_path_str}")
        
        processor_custom_params = {
            "detail_factor": 0.02,
            "internal_vertex_density": 15,
            "blur_kernel_size": 3,
            "binary_threshold": 100,
            "alpha_threshold": 5, # 더 낮은 알파 임계값
            "min_contour_area": 5 # 더 작은 컨투어 허용
        }
        processor = BatchMeshProcessor(params=processor_custom_params)

        logger.info(f"Processing batch of {len(image_paths_to_process)} images with custom params...")
        results = processor.process_image_batch(image_paths_to_process)

        logger.info(f"--- Batch Processing Results ({len(results)} successful) ---")
        if not results:
            logger.info("No images were processed successfully in the batch.")
            
        for idx, mesh_data_item in enumerate(results):
            img_name = mesh_data_item['image_name']
            logger.info(f"Result [{idx+1}] for: {img_name}")
            logger.info(f"  Source Path: {mesh_data_item['image_path']}")
            logger.info(f"  Dimensions: {mesh_data_item['width']}x{mesh_data_item['height']}")
            logger.info(f"  Vertices count: {len(mesh_data_item['vertices'])} (shape: {mesh_data_item['vertices'].shape})")
            logger.info(f"  Triangles count: {len(mesh_data_item['triangles'])} (shape: {mesh_data_item['triangles'].shape})")
            logger.info(f"  UVs items: {len(mesh_data_item['uvs'])}")
            logger.info(f"  Boundary Indices count: {len(mesh_data_item['boundary_indices'])}")
            logger.info(f"  Image Center (x, y): ({mesh_data_item['x']:.2f}, {mesh_data_item['y']:.2f})")
            # logger.debug(f"  Params Used: {mesh_data_item['params_used']}") # 상세 파라미터는 DEBUG 레벨

            try:
                source_image_path = Path(mesh_data_item['image_path'])
                if source_image_path.exists():
                    pil_img = Image.open(source_image_path).convert("RGBA")
                    draw_on_pil_img = ImageDraw.Draw(pil_img)
                    
                    # 삼각형 그리기 (시각화)
                    if mesh_data_item['vertices'] is not None and mesh_data_item['triangles'] is not None:
                        for tri_indices_item in mesh_data_item['triangles']:
                            p1_coords = tuple(mesh_data_item['vertices'][tri_indices_item[0]])
                            p2_coords = tuple(mesh_data_item['vertices'][tri_indices_item[1]])
                            p3_coords = tuple(mesh_data_item['vertices'][tri_indices_item[2]])
                            draw_on_pil_img.polygon([p1_coords, p2_coords, p3_coords], outline="magenta", width=1)
                    
                    # 경계 정점 그리기 (시각화)
                    # if mesh_data_item.get('boundary_indices') and mesh_data_item['vertices'] is not None:
                    #    for v_idx in mesh_data_item['boundary_indices']:
                    #        if 0 <= v_idx < len(mesh_data_item['vertices']):
                    #            vx, vy = mesh_data_item['vertices'][v_idx]
                    #            draw_on_pil_img.ellipse([(vx-2, vy-2), (vx+2, vy+2)], fill="cyan")

                    viz_output_path = temp_dir / f"{img_name}_విజువలైజేషన్.png"
                    pil_img.save(viz_output_path)
                    logger.info(f"  Saved visualization for '{img_name}' to: {viz_output_path}")
                else:
                    logger.warning(f"  Original image for visualization not found: {source_image_path}")
            except Exception as e_viz_item:
                logger.error(f"  Error during visualization for {img_name}: {e_viz_item}", exc_info=True)

    logger.info("BatchMeshProcessor example finished. Temporary directory and its contents have been removed.")