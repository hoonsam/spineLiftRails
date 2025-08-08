"""
SpineLift 로깅 설정

과도한 로그를 방지하고 개발 시 필요한 로그만 표시하도록 설정
"""

import logging
import os
from typing import Dict


class LoggingConfig:
    """로깅 설정 관리 클래스"""
    
    # 모듈별 로그 레벨 설정
    MODULE_LOG_LEVELS: Dict[str, int] = {
        # GUI 위젯들 (paintEvent 등 과도한 로그 방지)
        "src.gui.widgets.global_preview_widget_v2": logging.INFO,
        "src.gui.widgets.renderers": logging.INFO,
        "src.gui.widgets.handlers": logging.INFO,
        "src.gui.layers": logging.INFO,
        "src.gui.events": logging.INFO,
        "src.gui.main_window": logging.INFO,
        
        # 핵심 시스템
        "src.core.skeleton": logging.INFO,
        "src.core.processors": logging.INFO,
        "src.core.managers": logging.INFO,
        
        # 기본 레벨
        "root": logging.INFO,
    }
    
    @classmethod
    def setup_logging(cls) -> None:
        """로깅 설정 초기화"""
        # 환경변수에서 전역 로그 레벨 확인
        global_level = os.getenv('SPINELIFT_LOG_LEVEL', 'INFO').upper()
        
        try:
            global_log_level = getattr(logging, global_level)
        except AttributeError:
            global_log_level = logging.INFO
        
        # 루트 로거 설정
        logging.basicConfig(
            level=global_log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 모듈별 로그 레벨 적용
        for module_name, level in cls.MODULE_LOG_LEVELS.items():
            if module_name != "root":
                logger = logging.getLogger(module_name)
                logger.setLevel(level)
    
    @classmethod
    def set_module_log_level(cls, module_name: str, level: int) -> None:
        """특정 모듈의 로그 레벨 설정"""
        cls.MODULE_LOG_LEVELS[module_name] = level
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
    
    @classmethod
    def reduce_gui_logs(cls) -> None:
        """GUI 관련 로그를 최소화"""
        gui_modules = [
            "src.gui.widgets.global_preview_widget_v2",
            "src.gui.widgets.renderers.mesh_renderer",
            "src.gui.widgets.renderers.skeleton_renderer",
            "src.gui.widgets.handlers.simple_bone_handler",
        ]
        
        for module in gui_modules:
            cls.set_module_log_level(module, logging.WARNING)
    
    @classmethod
    def enable_debug_logs(cls) -> None:
        """디버그 로그 활성화"""
        for module_name in cls.MODULE_LOG_LEVELS:
            if module_name != "root":
                cls.set_module_log_level(module_name, logging.DEBUG)


# 편의 함수들
def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환 (모듈별 로그 레벨 적용)"""
    logger = logging.getLogger(name)
    
    # 모듈별 설정된 로그 레벨 적용
    for module_pattern, level in LoggingConfig.MODULE_LOG_LEVELS.items():
        if module_pattern != "root" and name.startswith(module_pattern):
            logger.setLevel(level)
            break
    
    return logger


def setup_logging():
    """로깅 설정 초기화 (전역 함수)"""
    LoggingConfig.setup_logging()


def reduce_gui_logs():
    """GUI 로그 최소화 (전역 함수)"""
    LoggingConfig.reduce_gui_logs()


def enable_debug_logs():
    """디버그 로그 활성화 (전역 함수)"""
    LoggingConfig.enable_debug_logs()


# 자동 초기화
setup_logging() 