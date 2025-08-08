"""
SpineLift Debug Logger
GUI 워크플로우 및 메쉬 파라미터 조절 문제 디버깅을 위한 전용 로깅 시스템
"""

import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from functools import wraps

# 디버그 로그 파일 경로
DEBUG_LOG_DIR = Path("logs/debug")
DEBUG_LOG_DIR.mkdir(parents=True, exist_ok=True)

# 디버그 로거 설정
debug_logger = logging.getLogger("spinelift_debug")
debug_logger.setLevel(logging.DEBUG)

# 파일 핸들러
debug_file_handler = logging.FileHandler(
    DEBUG_LOG_DIR / f"gui_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    encoding='utf-8'
)
debug_file_handler.setLevel(logging.DEBUG)

# 콘솔 핸들러
debug_console_handler = logging.StreamHandler()
debug_console_handler.setLevel(logging.INFO)

# 포맷터
debug_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s'
)
debug_file_handler.setFormatter(debug_formatter)
debug_console_handler.setFormatter(debug_formatter)

# 핸들러 추가
if not debug_logger.handlers:
    debug_logger.addHandler(debug_file_handler)
    debug_logger.addHandler(debug_console_handler)


class WorkflowDebugTracker:
    """워크플로우 상태 추적 및 디버깅을 위한 클래스"""
    
    def __init__(self):
        self.state_history: list = []
        self.signal_trace: list = []
        self.widget_states: Dict[str, Any] = {}
        self.start_time = time.time()
        
        debug_logger.info("=== WorkflowDebugTracker 초기화 ===")
    
    def log_state_change(self, component: str, old_state: Any, new_state: Any, context: str = ""):
        """상태 변경 로깅"""
        timestamp = time.time() - self.start_time
        entry = {
            'timestamp': timestamp,
            'component': component,
            'old_state': str(old_state),
            'new_state': str(new_state),
            'context': context
        }
        self.state_history.append(entry)
        
        debug_logger.info(f"상태 변경 [{component}]: {old_state} → {new_state} ({context})")
    
    def log_signal_emission(self, sender: str, signal_name: str, args: tuple = (), context: str = ""):
        """시그널 방출 로깅"""
        timestamp = time.time() - self.start_time
        entry = {
            'timestamp': timestamp,
            'sender': sender,
            'signal': signal_name,
            'args': str(args),
            'context': context
        }
        self.signal_trace.append(entry)
        
        debug_logger.debug(f"시그널 방출 [{sender}::{signal_name}]: {args} ({context})")
    
    def log_widget_state(self, widget_name: str, state: Dict[str, Any]):
        """위젯 상태 스냅샷 로깅"""
        self.widget_states[widget_name] = {
            'timestamp': time.time() - self.start_time,
            'state': state.copy()
        }
        
        debug_logger.debug(f"위젯 상태 [{widget_name}]: {json.dumps(state, ensure_ascii=False, indent=2)}")
    
    def dump_current_state(self):
        """현재 상태 전체 덤프"""
        debug_logger.info("=== 현재 상태 덤프 ===")
        debug_logger.info(f"경과 시간: {time.time() - self.start_time:.2f}초")
        debug_logger.info(f"상태 변경 이벤트 수: {len(self.state_history)}")
        debug_logger.info(f"시그널 이벤트 수: {len(self.signal_trace)}")
        debug_logger.info(f"추적 중인 위젯 수: {len(self.widget_states)}")
        
        # 최근 10개 이벤트 출력
        debug_logger.info("=== 최근 상태 변경 ===")
        for entry in self.state_history[-10:]:
            debug_logger.info(f"  [{entry['timestamp']:.2f}s] {entry['component']}: {entry['old_state']} → {entry['new_state']}")
            
        debug_logger.info("=== 최근 시그널 ===")
        for entry in self.signal_trace[-10:]:
            debug_logger.info(f"  [{entry['timestamp']:.2f}s] {entry['sender']}::{entry['signal']}")


# 전역 디버그 트래커 인스턴스
workflow_tracker = WorkflowDebugTracker()


def debug_method(component_name: str = ""):
    """메소드 호출 추적을 위한 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cls_name = args[0].__class__.__name__ if args else "Unknown"
            method_name = f"{cls_name}.{func.__name__}"
            full_name = f"{component_name}.{method_name}" if component_name else method_name
            
            debug_logger.debug(f">>> 메소드 호출: {full_name}({len(args)} args, {len(kwargs)} kwargs)")
            
            try:
                result = func(*args, **kwargs)
                debug_logger.debug(f"<<< 메소드 완료: {full_name}")
                return result
            except Exception as e:
                debug_logger.error(f"!!! 메소드 오류: {full_name} - {str(e)}")
                raise
                
        return wrapper
    return decorator


def log_gui_event(event_type: str, component: str, details: Dict[str, Any]):
    """GUI 이벤트 로깅 헬퍼 함수"""
    debug_logger.info(f"GUI 이벤트 [{event_type}] {component}: {json.dumps(details, ensure_ascii=False)}")


def log_parameter_change(param_name: str, old_value: Any, new_value: Any, source: str):
    """파라미터 변경 로깅 헬퍼 함수"""
    workflow_tracker.log_state_change(
        component=f"Parameter.{param_name}",
        old_state=old_value,
        new_state=new_value,
        context=f"source: {source}"
    )


def log_workflow_transition(from_step: str, to_step: str, success: bool, error_msg: str = ""):
    """워크플로우 전환 로깅 헬퍼 함수"""
    status = "성공" if success else f"실패: {error_msg}"
    workflow_tracker.log_state_change(
        component="WorkflowManager",
        old_state=from_step,
        new_state=to_step if success else f"{to_step} (실패)",
        context=status
    )


def capture_widget_state(widget, widget_name: str):
    """위젯 상태 캡처 헬퍼 함수"""
    try:
        state = {}
        
        # 일반적인 위젯 속성들
        if hasattr(widget, 'isEnabled'):
            state['enabled'] = widget.isEnabled()
        if hasattr(widget, 'isVisible'):
            state['visible'] = widget.isVisible()
        if hasattr(widget, 'text') and callable(getattr(widget, 'text')):
            state['text'] = widget.text()
        if hasattr(widget, 'value') and callable(getattr(widget, 'value')):
            state['value'] = widget.value()
        if hasattr(widget, 'isChecked') and callable(getattr(widget, 'isChecked')):
            state['checked'] = widget.isChecked()
            
        workflow_tracker.log_widget_state(widget_name, state)
        
    except Exception as e:
        debug_logger.warning(f"위젯 상태 캡처 실패 [{widget_name}]: {e}")