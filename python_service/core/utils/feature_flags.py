"""
SpineLift - Feature Flag System
Phase 2 개발을 위한 안전한 기능 격리 시스템
"""

import os
from typing import Dict, List
import logging

# 로그 레벨 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class FeatureFlags:
    """Feature Flag 관리 시스템"""
    
    # 기본 Feature Flag 설정
    _FLAGS: Dict[str, bool] = {
        # Phase 1 완료된 기능
        "mesh_generation": True,
        "psd_processing": True,
        "parameter_system": True,
        
        # Phase 2 스켈레톤 시스템 (개발 중)
        "skeleton_system": True,         # 전체 스켈레톤 시스템 (기본 기능 완성)
        "skeleton_templates": True,      # 템플릿 시스템 (완성)
        "skeleton_editing": True,        # 본 편집 기능 (활성화)
        "skeleton_export": True,         # 통합 내보내기 (완성)
        "integrated_canvas": True,       # 통합 프리뷰 캔버스 (기본 완성)
        "preview_mode_distinction": True, # 프리뷰 모드 구분 기능 (완성)
        
        # GlobalPreview 리팩터링 시스템
        "layer_system": True,           # 새로운 레이어 기반 아키텍처 (개발 중 - 50% 완성)
        
        # Phase 3+ 미래 기능들
        "animation_system": False,
        "ai_pose_analysis": False,
        "advanced_constraints": False,
        
        # 애니메이션 패널 분리 시스템 (Phase 3 - 개발 완료)
        "animation_panel": True,         # 독립적인 애니메이션 패널
        "animation_templates": True,     # 애니메이션 템플릿 시스템
        "animation_export": True,        # 애니메이션 통합 익스포트
        
        # Phase UI 시스템 (통합 단계) - 탭 시스템으로 변경
        "phase_system": False,                   # Phase 기반 UI 시스템 -> 탭 시스템으로 변경
        "phase_ui_container": False,             # PhaseUIContainer 사용 안함
        "phase_navigation": False,               # Phase 네비게이션 바 사용 안함
        "phase_status_indicator": False,         # Phase 상태 표시기 사용 안함
        "tab_based_ui": True,                    # 탭 기반 UI 시스템
        
        # MainWindow 리팩토링 시스템 (Phase 4 - 구현 완료)
        "refactored_file_manager": True,         # FileManager 분리 (완료)
        "refactored_settings_manager": True,     # SettingsManager 분리 (완료)  
        "refactored_theme_manager": True,        # ThemeManager 분리 (완료)
        "refactored_state_manager": True,        # StateManager 분리 (완료)
        "refactored_workflow_manager": True,     # WorkflowManager 분리 (완료)
        "refactored_event_coordinator": True,    # EventCoordinator 분리 (완료)
        "refactored_mesh_coordinator": True,     # MeshCoordinator 분리 (완료)
        "refactored_skeleton_coordinator": True, # SkeletonCoordinator 분리 (완료)
        "refactored_export_coordinator": True,   # ExportCoordinator 분리 (완료) - 테스트 활성화
        "refactored_menu_manager": True,         # MenuManager 분리 (완료)
        "refactored_layout_manager": True,       # LayoutManager 분리 (완료)
        "refactored_main_window": False,         # MainWindow 최종 정리 (미완성)
    }
    
    @classmethod
    def is_enabled(cls, flag_name: str) -> bool:
        """Feature Flag 활성화 상태 확인
        
        Args:
            flag_name: 확인할 Feature Flag 이름
            
        Returns:
            bool: Flag 활성화 상태 (환경변수 우선)
        """
        # 환경변수 우선 확인
        env_var = f"SPINELIFT_FEATURE_{flag_name.upper()}"
        env_value = os.getenv(env_var)
        
        if env_value is not None:
            return env_value.lower() in ("true", "1", "yes", "on")
        
        # 기본값 반환
        return cls._FLAGS.get(flag_name, False)
    
    @classmethod
    def enable(cls, flag_name: str) -> None:
        """Feature Flag 활성화 (개발/테스트용)"""
        cls._FLAGS[flag_name] = True
    
    @classmethod
    def disable(cls, flag_name: str) -> None:
        """Feature Flag 비활성화 (개발/테스트용)"""
        cls._FLAGS[flag_name] = False
    
    @classmethod
    def get_all_flags(cls) -> Dict[str, bool]:
        """모든 Feature Flag 상태 반환"""
        return cls._FLAGS.copy()
    
    @classmethod
    def validate_flag_consistency(cls) -> List[str]:
        """Feature Flag 일관성 검증
        
        Returns:
            List[str]: 불일치하는 플래그 이름 목록
        """
        inconsistencies = []
        current_flags = cls._FLAGS
        
        # reset_to_defaults로 설정되는 값들과 비교
        temp_flags = cls._FLAGS.copy()
        cls.reset_to_defaults()
        default_flags = cls._FLAGS.copy()
        cls._FLAGS = temp_flags  # 원래 값 복원
        
        for flag_name in current_flags:
            if current_flags[flag_name] != default_flags.get(flag_name, False):
                inconsistencies.append(flag_name)
        
        return inconsistencies
    
    @classmethod
    def reset_to_defaults(cls) -> None:
        """Feature Flag를 기본값으로 재설정 (테스트용)
        
        주의: _FLAGS와 동일한 값으로 설정하여 일관성 보장
        """
        cls._FLAGS = {
            # Phase 1 완료된 기능
            "mesh_generation": True,
            "psd_processing": True,
            "parameter_system": True,
            
            # Phase 2 스켈레톤 시스템 (개발 중)
            "skeleton_system": True,         # 전체 스켈레톤 시스템
            "skeleton_templates": True,      # 템플릿 시스템
            "skeleton_editing": False,       # 본 편집 기능 (개발 중)
            "skeleton_export": True,         # 통합 내보내기
            "integrated_canvas": True,       # 통합 프리뷰 캔버스
            "preview_mode_distinction": True, # 프리뷰 모드 구분 기능
            
            # GlobalPreview 리팩터링 시스템
            "layer_system": True,            # 새로운 레이어 기반 아키텍처
            
            # Phase 3+ 미래 기능들
            "animation_system": False,
            "ai_pose_analysis": False,
            "advanced_constraints": False,
            
            # 애니메이션 패널 분리 시스템 (Phase 3 - 개발 완료)
            "animation_panel": True,         # 독립적인 애니메이션 패널
            "animation_templates": True,     # 애니메이션 템플릿 시스템
            "animation_export": True,        # 애니메이션 통합 익스포트
            
            # MainWindow 리팩토링 시스템 (Phase 4 - 구현 완료)
            "refactored_file_manager": True,         # FileManager 분리 (완료)
            "refactored_settings_manager": True,     # SettingsManager 분리 (완료)  
            "refactored_theme_manager": True,        # ThemeManager 분리 (완료)
            "refactored_state_manager": True,        # StateManager 분리 (완료)
            "refactored_workflow_manager": True,     # WorkflowManager 분리 (완료)
            "refactored_event_coordinator": True,    # EventCoordinator 분리 (완료)
            "refactored_mesh_coordinator": True,     # MeshCoordinator 분리 (완료)
            "refactored_skeleton_coordinator": True, # SkeletonCoordinator 분리 (완료)
            "refactored_export_coordinator": True,   # ExportCoordinator 분리 (완료)
            "refactored_menu_manager": True,         # MenuManager 분리 (완료)
            "refactored_layout_manager": True,       # LayoutManager 분리 (완료)
            "refactored_main_window": False,         # MainWindow 최종 정리 (미완성)
        }


# 편의를 위한 함수들
def is_enabled(flag_name: str) -> bool:
    """Feature Flag 활성화 여부 확인 (전역 함수)"""
    return FeatureFlags.is_enabled(flag_name)


def enable_feature(flag_name: str) -> None:
    """Feature Flag 활성화 (전역 함수)"""
    FeatureFlags.enable(flag_name)


def disable_feature(flag_name: str) -> None:
    """Feature Flag 비활성화 (전역 함수)"""
    FeatureFlags.disable(flag_name)


def validate_consistency() -> List[str]:
    """Feature Flag 일관성 검증 (전역 함수)"""
    return FeatureFlags.validate_flag_consistency()


# 전역 인스턴스 생성 (테스트에서 사용)
feature_flags = FeatureFlags() 