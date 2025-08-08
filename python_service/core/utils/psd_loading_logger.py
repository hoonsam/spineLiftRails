"""
PSD 로딩 프로세스 전용 로거
"""

import logging
from pathlib import Path
from datetime import datetime

def setup_psd_loading_logger():
    """PSD 로딩 전용 로거 설정"""
    
    # 로그 디렉토리 생성
    log_dir = Path("logs/psd_loading")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 로그 파일 이름
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"psd_loading_{timestamp}.log"
    
    # 로거 생성
    logger = logging.getLogger('psd_loading')
    logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거
    logger.handlers.clear()
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 전역 로거 인스턴스
psd_logger = setup_psd_loading_logger()

def log_psd_loading_step(step: str, details: str = ""):
    """PSD 로딩 단계 로그"""
    psd_logger.info(f"[PSD_LOADING_STEP] {step}")
    if details:
        psd_logger.debug(f"  Details: {details}")

def log_layer_tree_update(widget_name: str, layer_count: int, success: bool = True):
    """Layer Tree 업데이트 로그"""
    status = "SUCCESS" if success else "FAILED"
    psd_logger.info(f"[LAYER_TREE_UPDATE] {widget_name}: {status} - {layer_count} layers")

def log_phase_ui_status(component: str, status: str, details: str = ""):
    """Phase UI 상태 로그"""
    psd_logger.info(f"[PHASE_UI] {component}: {status}")
    if details:
        psd_logger.debug(f"  Details: {details}")