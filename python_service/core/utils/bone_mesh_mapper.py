"""
본-메시 매핑 시스템

메시 레이어를 적절한 스켈레톤 본에 자동으로 연결하는 시스템입니다.
레이어 이름 기반 매핑과 위치 기반 매핑을 지원합니다.
"""

import math
from typing import Dict, List, Optional, Any, Tuple
from PyQt6.QtCore import QPointF

from src.core.models.enhanced_bone import EnhancedBone
from src.core.utils.logging_utils import get_logger

logger = get_logger(__name__)


class BoneMeshMapper:
    """메시를 적절한 본에 연결하는 매핑 시스템"""
    
    def __init__(self):
        self.body_part_mapping = self._initialize_body_part_mapping()
        self.position_weight = 0.3  # 위치 기반 매핑 가중치
        self.name_weight = 0.7      # 이름 기반 매핑 가중치
    
    def _initialize_body_part_mapping(self) -> Dict[str, List[str]]:
        """신체 부위별 키워드 매핑 초기화"""
        return {
            # 머리/목 부위
            "head": [
                "head", "hair", "face", "eye", "nose", "mouth", "ear", 
                "brow", "cheek", "chin", "forehead", "skull"
            ],
            "neck": [
                "neck", "collar", "throat", "nape"
            ],
            
            # 몸통 부위
            "body": [
                "body", "torso", "chest", "back", "shoulder", "breast",
                "nipple", "pectoral", "spine", "ribcage"
            ],
            "waist": [
                "waist", "belly", "stomach", "abdomen", "navel", "core"
            ],
            "hip": [
                "hip", "pelvis", "pants", "skirt", "bottom", "groin",
                "buttock", "glute"
            ],
            
            # 왼쪽 팔
            "upperarm_L": [
                "l_arm", "left_arm", "l_upperarm", "left_upperarm",
                "l_shoulder", "left_shoulder", "l_bicep", "left_bicep"
            ],
            "arm_L": [
                "l_forearm", "left_forearm", "l_elbow", "left_elbow",
                "l_wrist", "left_wrist"
            ],
            "hand_L": [
                "l_hand", "left_hand", "l_finger", "left_finger",
                "l_thumb", "left_thumb", "l_palm", "left_palm"
            ],
            
            # 오른쪽 팔
            "upperarm_R": [
                "r_arm", "right_arm", "r_upperarm", "right_upperarm",
                "r_shoulder", "right_shoulder", "r_bicep", "right_bicep"
            ],
            "arm_R": [
                "r_forearm", "right_forearm", "r_elbow", "right_elbow",
                "r_wrist", "right_wrist"
            ],
            "hand_R": [
                "r_hand", "right_hand", "r_finger", "right_finger",
                "r_thumb", "right_thumb", "r_palm", "right_palm"
            ],
            
            # 왼쪽 다리
            "upperleg_L": [
                "l_leg", "left_leg", "l_thigh", "left_thigh",
                "l_hip", "left_hip", "l_quad", "left_quad"
            ],
            "leg_L": [
                "l_shin", "left_shin", "l_knee", "left_knee",
                "l_calf", "left_calf", "l_ankle", "left_ankle"
            ],
            "foot_L": [
                "l_foot", "left_foot", "l_toe", "left_toe",
                "l_heel", "left_heel", "l_sole", "left_sole"
            ],
            
            # 오른쪽 다리
            "upperleg_R": [
                "r_leg", "right_leg", "r_thigh", "right_thigh",
                "r_hip", "right_hip", "r_quad", "right_quad"
            ],
            "leg_R": [
                "r_shin", "right_shin", "r_knee", "right_knee",
                "r_calf", "right_calf", "r_ankle", "right_ankle"
            ],
            "foot_R": [
                "r_foot", "right_foot", "r_toe", "right_toe",
                "r_heel", "right_heel", "r_sole", "right_sole"
            ],
            
            # 기타 부위
            "root": [
                "root", "center", "main", "base", "origin"
            ]
        }
    
    def find_best_bone_for_mesh(
        self,
        mesh_data: Dict[str, Any],
        enhanced_bones: Dict[str, EnhancedBone],
        canvas_width: float,
        canvas_height: float
    ) -> str:
        """메시에 가장 적합한 본 찾기
        
        Args:
            mesh_data: 메시 데이터
            enhanced_bones: 스켈레톤 본 데이터
            canvas_width: 캔버스 너비
            canvas_height: 캔버스 높이
            
        Returns:
            str: 가장 적합한 본의 이름
        """
        layer_name = mesh_data.get("layer_name", "").lower()
        
        logger.debug("Finding best bone for mesh: %s", layer_name)
        
        # 1. 레이어 이름 기반 매핑 시도
        name_based_bone = self._map_by_layer_name(layer_name, enhanced_bones)
        
        # 2. 위치 기반 매핑 시도
        position_based_bone = self._map_by_position(
            mesh_data, enhanced_bones, canvas_width, canvas_height
        )
        
        # 3. 결과 결정
        if name_based_bone and position_based_bone:
            # 둘 다 있으면 이름 기반 우선 (더 정확함)
            selected_bone = name_based_bone
            logger.info(
                "Mesh '%s' mapped to bone '%s' (name-based, position suggested: %s)",
                layer_name, selected_bone, position_based_bone
            )
        elif name_based_bone:
            selected_bone = name_based_bone
            logger.info(
                "Mesh '%s' mapped to bone '%s' (name-based only)",
                layer_name, selected_bone
            )
        elif position_based_bone:
            selected_bone = position_based_bone
            logger.info(
                "Mesh '%s' mapped to bone '%s' (position-based only)",
                layer_name, selected_bone
            )
        else:
            # 기본값: 루트 본
            selected_bone = "root"
            logger.warning(
                "Mesh '%s' mapped to root bone (no suitable bone found)",
                layer_name
            )
        
        return selected_bone
    
    def _map_by_layer_name(
        self,
        layer_name: str,
        enhanced_bones: Dict[str, EnhancedBone]
    ) -> Optional[str]:
        """레이어 이름을 기반으로 본 매핑
        
        Args:
            layer_name: 레이어 이름 (소문자)
            enhanced_bones: 스켈레톤 본 데이터
            
        Returns:
            Optional[str]: 매핑된 본 이름 또는 None
        """
        best_bone = None
        best_score = 0
        
        for bone_name, keywords in self.body_part_mapping.items():
            if bone_name not in enhanced_bones:
                continue  # 존재하지 않는 본은 건너뛰기
            
            # 키워드 매칭 점수 계산
            score = self._calculate_name_matching_score(layer_name, keywords)
            
            if score > best_score:
                best_score = score
                best_bone = bone_name
        
        if best_bone and best_score > 0.5:  # 최소 신뢰도 임계값
            logger.debug(
                "Name-based mapping: '%s' -> '%s' (score: %.2f)",
                layer_name, best_bone, best_score
            )
            return best_bone
        
        return None
    
    def _calculate_name_matching_score(
        self,
        layer_name: str,
        keywords: List[str]
    ) -> float:
        """레이어 이름과 키워드 목록 간의 매칭 점수 계산
        
        Args:
            layer_name: 레이어 이름
            keywords: 키워드 목록
            
        Returns:
            float: 매칭 점수 (0.0 ~ 1.0)
        """
        if not layer_name or not keywords:
            return 0.0
        
        max_score = 0.0
        
        for keyword in keywords:
            if keyword in layer_name:
                # 정확한 매치일수록 높은 점수
                if keyword == layer_name:
                    score = 1.0  # 완전 일치
                elif layer_name.startswith(keyword) or layer_name.endswith(keyword):
                    score = 0.9  # 시작/끝 일치
                else:
                    score = 0.7  # 부분 일치
                
                # 키워드 길이에 따른 가중치 (긴 키워드일수록 더 정확)
                length_weight = min(len(keyword) / 10.0, 1.0)
                score *= (0.5 + 0.5 * length_weight)
                
                max_score = max(max_score, score)
        
        return max_score
    
    def _map_by_position(
        self,
        mesh_data: Dict[str, Any],
        enhanced_bones: Dict[str, EnhancedBone],
        canvas_width: float,
        canvas_height: float
    ) -> Optional[str]:
        """메시 위치를 기반으로 가장 가까운 본 찾기
        
        Args:
            mesh_data: 메시 데이터
            enhanced_bones: 스켈레톤 본 데이터
            canvas_width: 캔버스 너비
            canvas_height: 캔버스 높이
            
        Returns:
            Optional[str]: 가장 가까운 본 이름 또는 None
        """
        # 메시 중심점 계산
        mesh_center = self._calculate_mesh_center(mesh_data)
        if mesh_center is None:
            return None
        
        # 가장 가까운 본 찾기
        min_distance = float('inf')
        closest_bone = None
        
        for bone_name, enhanced_bone in enhanced_bones.items():
            if enhanced_bone.is_direction_only:
                continue  # 방향점은 제외
            
            # 본과 메시 중심점 간 거리 계산
            distance = self._calculate_distance(mesh_center, enhanced_bone.position)
            
            if distance < min_distance:
                min_distance = distance
                closest_bone = bone_name
        
        # 거리 임계값 검사
        max_distance = min(canvas_width, canvas_height) * 0.3  # 캔버스 크기의 30%
        
        if closest_bone and min_distance <= max_distance:
            logger.debug(
                "Position-based mapping: mesh_center=(%.2f, %.2f) -> '%s' (distance: %.2f)",
                mesh_center.x(), mesh_center.y(), closest_bone, min_distance
            )
            return closest_bone
        
        logger.debug(
            "Position-based mapping failed: min_distance=%.2f > max_distance=%.2f",
            min_distance, max_distance
        )
        return None
    
    def _calculate_mesh_center(self, mesh_data: Dict[str, Any]) -> Optional[QPointF]:
        """메시의 중심점 계산
        
        Args:
            mesh_data: 메시 데이터
            
        Returns:
            Optional[QPointF]: 메시 중심점 또는 None
        """
        vertices = mesh_data.get("vertices", [])
        if not vertices or len(vertices) < 2:
            logger.warning("Invalid mesh vertices for center calculation")
            return None
        
        try:
            # 정점들의 평균 위치 계산
            x_sum = sum(vertices[i] for i in range(0, len(vertices), 2))
            y_sum = sum(vertices[i+1] for i in range(0, len(vertices), 2))
            
            vertex_count = len(vertices) // 2
            center_x = x_sum / vertex_count
            center_y = y_sum / vertex_count
            
            return QPointF(center_x, center_y)
            
        except (IndexError, ZeroDivisionError) as e:
            logger.error("Error calculating mesh center: %s", str(e))
            return None
    
    def _calculate_distance(self, point1: QPointF, point2: QPointF) -> float:
        """두 점 사이의 거리 계산
        
        Args:
            point1: 첫 번째 점
            point2: 두 번째 점
            
        Returns:
            float: 거리
        """
        dx = point2.x() - point1.x()
        dy = point2.y() - point1.y()
        return math.sqrt(dx * dx + dy * dy)
    
    def get_mapping_suggestions(
        self,
        mesh_data_list: List[Dict[str, Any]],
        enhanced_bones: Dict[str, EnhancedBone],
        canvas_width: float,
        canvas_height: float
    ) -> List[Dict[str, Any]]:
        """모든 메시에 대한 본 매핑 제안 생성
        
        Args:
            mesh_data_list: 메시 데이터 목록
            enhanced_bones: 스켈레톤 본 데이터
            canvas_width: 캔버스 너비
            canvas_height: 캔버스 높이
            
        Returns:
            List[Dict[str, Any]]: 매핑 제안 목록
        """
        suggestions = []
        
        for mesh_data in mesh_data_list:
            layer_name = mesh_data.get("layer_name", "unknown")
            
            # 최적 본 찾기
            best_bone = self.find_best_bone_for_mesh(
                mesh_data, enhanced_bones, canvas_width, canvas_height
            )
            
            # 대안 본들 찾기
            alternatives = self._find_alternative_bones(
                mesh_data, enhanced_bones, canvas_width, canvas_height, best_bone
            )
            
            suggestion = {
                "layer_name": layer_name,
                "best_bone": best_bone,
                "alternatives": alternatives,
                "confidence": self._calculate_mapping_confidence(
                    mesh_data, enhanced_bones, best_bone, canvas_width, canvas_height
                )
            }
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def _find_alternative_bones(
        self,
        mesh_data: Dict[str, Any],
        enhanced_bones: Dict[str, EnhancedBone],
        canvas_width: float,
        canvas_height: float,
        exclude_bone: str
    ) -> List[str]:
        """대안 본들 찾기
        
        Args:
            mesh_data: 메시 데이터
            enhanced_bones: 스켈레톤 본 데이터
            canvas_width: 캔버스 너비
            canvas_height: 캔버스 높이
            exclude_bone: 제외할 본 이름
            
        Returns:
            List[str]: 대안 본 목록 (최대 3개)
        """
        layer_name = mesh_data.get("layer_name", "").lower()
        mesh_center = self._calculate_mesh_center(mesh_data)
        
        if mesh_center is None:
            return []
        
        # 거리 기반으로 가까운 본들 찾기
        bone_distances = []
        
        for bone_name, enhanced_bone in enhanced_bones.items():
            if (bone_name == exclude_bone or 
                enhanced_bone.is_direction_only):
                continue
            
            distance = self._calculate_distance(mesh_center, enhanced_bone.position)
            bone_distances.append((bone_name, distance))
        
        # 거리순 정렬하여 상위 3개 반환
        bone_distances.sort(key=lambda x: x[1])
        alternatives = [bone_name for bone_name, _ in bone_distances[:3]]
        
        return alternatives
    
    def _calculate_mapping_confidence(
        self,
        mesh_data: Dict[str, Any],
        enhanced_bones: Dict[str, EnhancedBone],
        selected_bone: str,
        canvas_width: float,
        canvas_height: float
    ) -> float:
        """매핑 신뢰도 계산
        
        Args:
            mesh_data: 메시 데이터
            enhanced_bones: 스켈레톤 본 데이터
            selected_bone: 선택된 본 이름
            canvas_width: 캔버스 너비
            canvas_height: 캔버스 높이
            
        Returns:
            float: 신뢰도 (0.0 ~ 1.0)
        """
        layer_name = mesh_data.get("layer_name", "").lower()
        
        # 이름 기반 신뢰도
        name_confidence = 0.0
        if selected_bone in self.body_part_mapping:
            keywords = self.body_part_mapping[selected_bone]
            name_confidence = self._calculate_name_matching_score(layer_name, keywords)
        
        # 위치 기반 신뢰도
        position_confidence = 0.0
        mesh_center = self._calculate_mesh_center(mesh_data)
        
        if mesh_center and selected_bone in enhanced_bones:
            bone_position = enhanced_bones[selected_bone].position
            distance = self._calculate_distance(mesh_center, bone_position)
            max_distance = min(canvas_width, canvas_height) * 0.5
            position_confidence = max(0.0, 1.0 - (distance / max_distance))
        
        # 가중 평균 계산
        total_confidence = (
            name_confidence * self.name_weight + 
            position_confidence * self.position_weight
        )
        
        return min(1.0, total_confidence)