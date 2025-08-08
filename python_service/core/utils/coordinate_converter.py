"""
SpineLift 캔버스 좌표와 Spine 좌표 간 변환 유틸리티

SpineLift 좌표계:
- 원점: 캔버스 중앙
- X축: 오른쪽이 양수
- Y축: 아래쪽이 양수

Spine 좌표계:
- 원점: 스켈레톤 루트 (보통 캔버스 중앙)
- X축: 오른쪽이 양수  
- Y축: 위쪽이 양수
"""

import math
from typing import Tuple
from PyQt6.QtCore import QPointF

from src.core.utils.logging_utils import get_logger

logger = get_logger(__name__)


class CoordinateConverter:
    """SpineLift 캔버스 좌표와 Spine 좌표 간 변환"""
    
    @staticmethod
    def canvas_to_spine(
        canvas_position: QPointF,
        canvas_width: float,
        canvas_height: float
    ) -> Tuple[float, float]:
        """캔버스 좌표를 Spine 좌표로 변환
        
        Args:
            canvas_position: SpineLift 캔버스 좌표
            canvas_width: 캔버스 너비
            canvas_height: 캔버스 높이
            
        Returns:
            Tuple[float, float]: (spine_x, spine_y) Spine 좌표
        """
        # SpineLift: 중앙 원점, Y축 아래쪽 양수
        # Spine: 중앙 원점, Y축 위쪽 양수
        spine_x = canvas_position.x()
        spine_y = -canvas_position.y()  # Y축 반전
        
        logger.debug(
            "Canvas to Spine: (%.2f, %.2f) -> (%.2f, %.2f)",
            canvas_position.x(), canvas_position.y(), spine_x, spine_y
        )
        
        return spine_x, spine_y
    
    @staticmethod
    def spine_to_canvas(
        spine_x: float,
        spine_y: float,
        canvas_width: float,
        canvas_height: float
    ) -> QPointF:
        """Spine 좌표를 캔버스 좌표로 변환
        
        Args:
            spine_x: Spine X 좌표
            spine_y: Spine Y 좌표
            canvas_width: 캔버스 너비
            canvas_height: 캔버스 높이
            
        Returns:
            QPointF: SpineLift 캔버스 좌표
        """
        # Spine: 중앙 원점, Y축 위쪽 양수
        # SpineLift: 중앙 원점, Y축 아래쪽 양수
        canvas_x = spine_x
        canvas_y = -spine_y  # Y축 반전
        
        canvas_position = QPointF(canvas_x, canvas_y)
        
        logger.debug(
            "Spine to Canvas: (%.2f, %.2f) -> (%.2f, %.2f)",
            spine_x, spine_y, canvas_x, canvas_y
        )
        
        return canvas_position
    
    @staticmethod
    def radians_to_degrees(radians: float) -> float:
        """라디안을 도로 변환
        
        Args:
            radians: 라디안 각도
            
        Returns:
            float: 도 단위 각도
        """
        degrees = math.degrees(radians)
        logger.debug("Radians to Degrees: %.4f -> %.2f", radians, degrees)
        return degrees
    
    @staticmethod
    def degrees_to_radians(degrees: float) -> float:
        """도를 라디안으로 변환
        
        Args:
            degrees: 도 단위 각도
            
        Returns:
            float: 라디안 각도
        """
        radians = math.radians(degrees)
        logger.debug("Degrees to Radians: %.2f -> %.4f", degrees, radians)
        return radians
    
    @staticmethod
    def normalize_spine_rotation(degrees: float) -> float:
        """Spine 회전각을 -180 ~ 180 범위로 정규화
        
        Args:
            degrees: 정규화할 각도 (도)
            
        Returns:
            float: 정규화된 각도 (-180 ~ 180)
        """
        # -180 ~ 180 범위로 정규화
        while degrees > 180:
            degrees -= 360
        while degrees <= -180:
            degrees += 360
        
        return degrees
    
    @staticmethod
    def calculate_bone_world_position(
        bone_position: QPointF,
        parent_position: QPointF,
        bone_length: float,
        bone_rotation: float,
        canvas_width: float,
        canvas_height: float
    ) -> Tuple[float, float]:
        """본의 월드 위치를 계산하여 Spine 좌표로 반환
        
        Args:
            bone_position: 본의 로컬 위치 (캔버스 좌표)
            parent_position: 부모 본의 위치 (캔버스 좌표)
            bone_length: 본의 길이
            bone_rotation: 본의 회전각 (라디안)
            canvas_width: 캔버스 너비
            canvas_height: 캔버스 높이
            
        Returns:
            Tuple[float, float]: Spine 좌표계의 본 끝점 위치
        """
        # 본의 끝점 계산 (캔버스 좌표)
        end_x = bone_position.x() + bone_length * math.cos(bone_rotation)
        end_y = bone_position.y() + bone_length * math.sin(bone_rotation)
        
        # Spine 좌표로 변환
        spine_x, spine_y = CoordinateConverter.canvas_to_spine(
            QPointF(end_x, end_y), canvas_width, canvas_height
        )
        
        logger.debug(
            "Bone world position: length=%.2f, rotation=%.4f -> Spine(%.2f, %.2f)",
            bone_length, bone_rotation, spine_x, spine_y
        )
        
        return spine_x, spine_y
    
    @staticmethod
    def calculate_relative_bone_position(
        child_position: QPointF,
        parent_position: QPointF,
        parent_rotation: float,
        canvas_width: float,
        canvas_height: float
    ) -> Tuple[float, float]:
        """자식 본의 부모 본 기준 상대 위치 계산
        
        Args:
            child_position: 자식 본 위치 (캔버스 좌표)
            parent_position: 부모 본 위치 (캔버스 좌표)
            parent_rotation: 부모 본 회전각 (라디안)
            canvas_width: 캔버스 너비
            canvas_height: 캔버스 높이
            
        Returns:
            Tuple[float, float]: 부모 본 기준 상대 위치 (Spine 좌표)
        """
        # 절대 위치 차이 계산
        dx = child_position.x() - parent_position.x()
        dy = child_position.y() - parent_position.y()
        
        # 부모 본의 회전을 고려한 상대 위치 계산
        cos_rot = math.cos(-parent_rotation)  # 역회전
        sin_rot = math.sin(-parent_rotation)
        
        relative_x = dx * cos_rot - dy * sin_rot
        relative_y = dx * sin_rot + dy * cos_rot
        
        # Spine 좌표계로 변환 (Y축 반전)
        spine_relative_x = relative_x
        spine_relative_y = -relative_y
        
        logger.debug(
            "Relative bone position: dx=%.2f, dy=%.2f, parent_rot=%.4f -> (%.2f, %.2f)",
            dx, dy, parent_rotation, spine_relative_x, spine_relative_y
        )
        
        return spine_relative_x, spine_relative_y


class SpineCoordinateValidator:
    """Spine 좌표 유효성 검증"""
    
    @staticmethod
    def validate_bone_position(x: float, y: float, max_distance: float = 10000.0) -> bool:
        """본 위치가 유효한 범위 내에 있는지 검증
        
        Args:
            x: X 좌표
            y: Y 좌표
            max_distance: 원점에서 최대 허용 거리
            
        Returns:
            bool: 유효하면 True
        """
        distance = math.sqrt(x * x + y * y)
        is_valid = distance <= max_distance
        
        if not is_valid:
            logger.warning(
                "Invalid bone position: (%.2f, %.2f), distance=%.2f > max=%.2f",
                x, y, distance, max_distance
            )
        
        return is_valid
    
    @staticmethod
    def validate_bone_rotation(degrees: float) -> bool:
        """본 회전각이 유효한 범위 내에 있는지 검증
        
        Args:
            degrees: 회전각 (도)
            
        Returns:
            bool: 유효하면 True
        """
        # Spine은 -180 ~ 180 범위를 권장
        is_valid = -180 <= degrees <= 180
        
        if not is_valid:
            logger.warning(
                "Invalid bone rotation: %.2f degrees (should be -180 ~ 180)",
                degrees
            )
        
        return is_valid
    
    @staticmethod
    def validate_bone_length(length: float) -> bool:
        """본 길이가 유효한지 검증
        
        Args:
            length: 본 길이
            
        Returns:
            bool: 유효하면 True
        """
        is_valid = length >= 0 and length <= 5000.0  # 최대 5000픽셀
        
        if not is_valid:
            logger.warning(
                "Invalid bone length: %.2f (should be 0 ~ 5000)",
                length
            )
        
        return is_valid