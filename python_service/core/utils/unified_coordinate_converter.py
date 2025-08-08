"""
SpineLift 통합 좌표 변환 시스템

모든 좌표계 간 변환을 단일 클래스에서 처리:
- GUI 좌표계: Qt 기본 (좌상단 원점, Y축 아래쪽 양수)
- PSD 좌표계: Photoshop 기본 (좌상단 원점, Y축 아래쪽 양수)  
- Spine 좌표계: 중앙 원점, Y축 위쪽 양수

이 모듈은 기존의 분산된 좌표 변환 로직을 통합하여
일관성 있고 정확한 변환을 제공합니다.
"""

import math
from typing import Tuple, Optional
from PyQt6.QtCore import QPointF

from src.core.utils.logging_config import get_logger

logger = get_logger(__name__)


class UnifiedCoordinateConverter:
    """
    SpineLift 통합 좌표 변환기
    
    모든 좌표계 간의 변환을 단일 클래스에서 처리하여
    일관성과 정확성을 보장합니다.
    """
    
    def __init__(self, canvas_width: int = 800, canvas_height: int = 600):
        """
        좌표 변환기 초기화
        
        Args:
            canvas_width: GUI 캔버스 너비
            canvas_height: GUI 캔버스 높이
        """
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.canvas_center_x = canvas_width / 2.0
        self.canvas_center_y = canvas_height / 2.0
        
        # 좌표 유효성 검증 범위
        self.max_coordinate_range = 20000.0
        
        logger.info(f"통합 좌표 변환기 초기화: {canvas_width}x{canvas_height}")
        logger.debug(f"캔버스 중앙점: ({self.canvas_center_x}, {self.canvas_center_y})")
    
    def gui_to_spine(self, gui_point: QPointF) -> Tuple[float, float]:
        """
        GUI 좌표를 Spine 좌표로 변환
        
        GUI: 좌상단 원점, Y축 아래쪽 양수
        Spine: 중앙 원점, Y축 위쪽 양수
        
        Args:
            gui_point: GUI 캔버스 좌표
            
        Returns:
            Tuple[float, float]: (spine_x, spine_y)
        """
        # 중앙점 기준으로 이동
        spine_x = gui_point.x() - self.canvas_center_x
        # Y축 반전: GUI 위쪽(작은 값) → Spine 위쪽(양수), GUI 아래쪽(큰 값) → Spine 아래쪽(음수)
        spine_y = self.canvas_center_y - gui_point.y()
        
        logger.debug(
            f"GUI→Spine: ({gui_point.x():.2f}, {gui_point.y():.2f}) → ({spine_x:.2f}, {spine_y:.2f})"
        )
        
        return spine_x, spine_y
    
    def spine_to_gui(self, spine_x: float, spine_y: float) -> QPointF:
        """
        Spine 좌표를 GUI 좌표로 변환
        
        Args:
            spine_x: Spine X 좌표
            spine_y: Spine Y 좌표
            
        Returns:
            QPointF: GUI 캔버스 좌표
        """
        # 중앙점 기준으로 이동
        gui_x = spine_x + self.canvas_center_x
        # Y축 반전 (Spine 위쪽 → GUI 위쪽, Spine 아래쪽 → GUI 아래쪽)
        gui_y = self.canvas_center_y - spine_y
        
        gui_point = QPointF(gui_x, gui_y)
        
        logger.debug(
            f"Spine→GUI: ({spine_x:.2f}, {spine_y:.2f}) → ({gui_x:.2f}, {gui_y:.2f})"
        )
        
        return gui_point
    
    def psd_to_spine(self, psd_x: float, psd_y: float, 
                     psd_width: int, psd_height: int) -> Tuple[float, float]:
        """
        PSD 좌표를 Spine 좌표로 변환
        
        PSD: 좌상단 원점, Y축 아래쪽 양수
        Spine: 중앙 원점, Y축 위쪽 양수
        
        Args:
            psd_x: PSD X 좌표
            psd_y: PSD Y 좌표
            psd_width: PSD 캔버스 너비
            psd_height: PSD 캔버스 높이
            
        Returns:
            Tuple[float, float]: (spine_x, spine_y)
        """
        # PSD 중앙점 계산
        psd_center_x = psd_width / 2.0
        psd_center_y = psd_height / 2.0
        
        # 중앙점 기준으로 이동
        spine_x = psd_x - psd_center_x
        # Y축 반전: PSD 위쪽(작은 값) → Spine 위쪽(양수), PSD 아래쪽(큰 값) → Spine 아래쪽(음수)
        spine_y = psd_center_y - psd_y
        
        logger.debug(
            f"PSD→Spine: ({psd_x:.2f}, {psd_y:.2f}) → ({spine_x:.2f}, {spine_y:.2f}) "
            f"[PSD: {psd_width}x{psd_height}]"
        )
        
        return spine_x, spine_y
    
    def spine_to_psd(self, spine_x: float, spine_y: float,
                     psd_width: int, psd_height: int) -> Tuple[float, float]:
        """
        Spine 좌표를 PSD 좌표로 변환
        
        Args:
            spine_x: Spine X 좌표
            spine_y: Spine Y 좌표
            psd_width: PSD 캔버스 너비
            psd_height: PSD 캔버스 높이
            
        Returns:
            Tuple[float, float]: (psd_x, psd_y)
        """
        # PSD 중앙점 계산
        psd_center_x = psd_width / 2.0
        psd_center_y = psd_height / 2.0
        
        # 중앙점 기준으로 이동
        psd_x = spine_x + psd_center_x
        # Y축 반전 (Spine 위쪽 → PSD 위쪽, Spine 아래쪽 → PSD 아래쪽)
        psd_y = psd_center_y - spine_y
        
        logger.debug(
            f"Spine→PSD: ({spine_x:.2f}, {spine_y:.2f}) → ({psd_x:.2f}, {psd_y:.2f}) "
            f"[PSD: {psd_width}x{psd_height}]"
        )
        
        return psd_x, psd_y
    
    def radians_to_degrees(self, radians: float) -> float:
        """
        라디안을 도로 변환
        
        Args:
            radians: 라디안 각도
            
        Returns:
            float: 도 단위 각도
        """
        degrees = math.degrees(radians)
        logger.debug(f"라디안→도: {radians:.4f} → {degrees:.2f}")
        return degrees
    
    def degrees_to_radians(self, degrees: float) -> float:
        """
        도를 라디안으로 변환
        
        Args:
            degrees: 도 단위 각도
            
        Returns:
            float: 라디안 각도
        """
        radians = math.radians(degrees)
        logger.debug(f"도→라디안: {degrees:.2f} → {radians:.4f}")
        return radians
    
    def normalize_spine_angle(self, degrees: float) -> float:
        """
        Spine 각도를 -180~180 범위로 정규화
        
        Args:
            degrees: 정규화할 각도 (도)
            
        Returns:
            float: 정규화된 각도 (-180~180)
        """
        # -180~180 범위로 정규화
        normalized = degrees
        while normalized > 180.0:
            normalized -= 360.0
        while normalized < -180.0:
            normalized += 360.0
        
        logger.debug(f"각도 정규화: {degrees:.2f} → {normalized:.2f}")
        return normalized
    
    def update_canvas_size(self, width: int, height: int) -> None:
        """
        캔버스 크기 업데이트
        
        Args:
            width: 새로운 캔버스 너비
            height: 새로운 캔버스 높이
        """
        old_size = f"{self.canvas_width}x{self.canvas_height}"
        
        self.canvas_width = width
        self.canvas_height = height
        self.canvas_center_x = width / 2.0
        self.canvas_center_y = height / 2.0
        
        logger.info(f"캔버스 크기 업데이트: {old_size} → {width}x{height}")
        logger.debug(f"새로운 중앙점: ({self.canvas_center_x}, {self.canvas_center_y})")
    
    def validate_coordinates(self, x: float, y: float) -> bool:
        """
        좌표값의 유효성 검증
        
        Args:
            x: X 좌표
            y: Y 좌표
            
        Returns:
            bool: 유효성 여부
        """
        # NaN, Infinity 검사
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            return False
        
        # 범위 검사
        if abs(x) > self.max_coordinate_range or abs(y) > self.max_coordinate_range:
            return False
        
        return True
    
    def validate_angle(self, degrees: float) -> bool:
        """
        각도값의 유효성 검증
        
        Args:
            degrees: 각도 (도 단위)
            
        Returns:
            bool: 유효성 여부
        """
        return not (math.isnan(degrees) or math.isinf(degrees))
    
    def clamp_coordinates(self, x: float, y: float) -> Tuple[float, float]:
        """
        좌표를 유효한 범위로 제한
        
        Args:
            x: X 좌표
            y: Y 좌표
            
        Returns:
            Tuple[float, float]: 제한된 좌표
        """
        # NaN, Infinity를 0으로 대체
        if math.isnan(x) or math.isinf(x):
            x = 0.0
        if math.isnan(y) or math.isinf(y):
            y = 0.0
        
        # 범위 제한
        x = max(-self.max_coordinate_range, min(self.max_coordinate_range, x))
        y = max(-self.max_coordinate_range, min(self.max_coordinate_range, y))
        
        return x, y
    
    def calculate_bone_world_position(self, bone_position: QPointF, bone_length: float,
                                    bone_angle_radians: float) -> Tuple[float, float]:
        """
        본의 월드 끝점 위치를 Spine 좌표로 계산
        
        Args:
            bone_position: 본의 시작점 (GUI 좌표)
            bone_length: 본의 길이
            bone_angle_radians: 본의 각도 (라디안)
            
        Returns:
            Tuple[float, float]: 본 끝점의 Spine 좌표
        """
        # 본의 끝점 계산 (GUI 좌표계)
        end_x = bone_position.x() + bone_length * math.cos(bone_angle_radians)
        end_y = bone_position.y() + bone_length * math.sin(bone_angle_radians)
        
        # Spine 좌표로 변환
        spine_x, spine_y = self.gui_to_spine(QPointF(end_x, end_y))
        
        logger.debug(
            f"본 월드 위치: 길이={bone_length:.2f}, 각도={bone_angle_radians:.4f} "
            f"→ Spine({spine_x:.2f}, {spine_y:.2f})"
        )
        
        return spine_x, spine_y
    
    def get_conversion_info(self) -> dict:
        """
        현재 변환기 설정 정보 반환
        
        Returns:
            dict: 변환기 설정 정보
        """
        return {
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "canvas_center": (self.canvas_center_x, self.canvas_center_y),
            "max_coordinate_range": self.max_coordinate_range,
            "coordinate_systems": {
                "GUI": "좌상단 원점, Y축 아래쪽 양수",
                "PSD": "좌상단 원점, Y축 아래쪽 양수",
                "Spine": "중앙 원점, Y축 위쪽 양수"
            }
        } 