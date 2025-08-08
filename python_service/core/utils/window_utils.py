"""
Window Display Utilities
SpineLift GUI 윈도우 표시 및 위치 관리 유틸리티
"""

import logging
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QScreen
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class WindowDisplayManager:
    """윈도우 표시 관리자"""
    
    @staticmethod
    def get_safe_window_position(window: QWidget, preferred_width: int = 1200, preferred_height: int = 800) -> Tuple[int, int, int, int]:
        """화면 내 안전한 윈도우 위치 계산
        
        Returns:
            Tuple[x, y, width, height]: 안전한 윈도우 위치 및 크기
        """
        app = QApplication.instance()
        if not app:
            logger.warning("QApplication 인스턴스가 없어 기본 위치 반환")
            return 100, 100, preferred_width, preferred_height
        
        # 기본 화면 가져오기
        primary_screen = app.primaryScreen()
        if not primary_screen:
            logger.warning("기본 화면을 찾을 수 없어 기본 위치 반환")
            return 100, 100, preferred_width, preferred_height
        
        screen_geometry = primary_screen.availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        # 화면 크기에 맞게 윈도우 크기 조정
        window_width = min(preferred_width, int(screen_width * 0.9))
        window_height = min(preferred_height, int(screen_height * 0.9))
        
        # 화면 중앙에 배치
        x = (screen_width - window_width) // 2 + screen_geometry.x()
        y = (screen_height - window_height) // 2 + screen_geometry.y()
        
        logger.info(f"안전한 윈도우 위치 계산됨: ({x}, {y}) 크기: {window_width}x{window_height}")
        return x, y, window_width, window_height
    
    @staticmethod
    def ensure_window_visible(window: QWidget) -> bool:
        """윈도우가 화면에 표시되도록 보장
        
        Returns:
            bool: 성공 여부
        """
        try:
            if not window:
                logger.error("윈도우 객체가 None")
                return False
            
            # 윈도우 속성 설정
            window.setWindowFlags(
                Qt.WindowType.Window | 
                Qt.WindowType.WindowCloseButtonHint |
                Qt.WindowType.WindowMinimizeButtonHint |
                Qt.WindowType.WindowMaximizeButtonHint
            )
            
            # 윈도우 속성 강화
            window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
            window.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
            
            # 안전한 위치로 이동
            x, y, width, height = WindowDisplayManager.get_safe_window_position(window)
            window.setGeometry(x, y, width, height)
            
            # 윈도우 표시
            window.show()
            window.raise_()
            window.activateWindow()
            
            # 강제 업데이트
            window.repaint()
            QApplication.processEvents()
            
            logger.info(f"윈도우 표시 완료: 위치({x}, {y}) 크기({width}x{height})")
            return True
            
        except Exception as e:
            logger.error(f"윈도우 표시 실패: {e}")
            return False
    
    @staticmethod
    def check_window_visibility(window: QWidget) -> bool:
        """윈도우 가시성 확인
        
        Returns:
            bool: 윈도우가 보이는지 여부
        """
        try:
            if not window:
                return False
            
            is_visible = window.isVisible()
            is_active = window.isActiveWindow()
            geometry = window.geometry()
            
            logger.info(f"윈도우 상태 - 보임: {is_visible}, 활성: {is_active}, 위치: ({geometry.x()}, {geometry.y()}), 크기: {geometry.width()}x{geometry.height()}")
            
            return is_visible and geometry.width() > 0 and geometry.height() > 0
            
        except Exception as e:
            logger.error(f"윈도우 가시성 확인 실패: {e}")
            return False
    
    @staticmethod
    def delayed_visibility_check(window: QWidget, delay_ms: int = 1000) -> None:
        """지연된 윈도우 가시성 확인 및 복구
        
        Args:
            window: 확인할 윈도우
            delay_ms: 지연 시간 (밀리초)
        """
        def check_and_recover():
            try:
                if not WindowDisplayManager.check_window_visibility(window):
                    logger.warning("윈도우가 보이지 않음 - 복구 시도")
                    WindowDisplayManager.ensure_window_visible(window)
                else:
                    logger.info("윈도우 정상 표시 중")
            except Exception as e:
                logger.error(f"지연된 가시성 확인 실패: {e}")
        
        # QTimer를 사용한 지연된 실행
        QTimer.singleShot(delay_ms, check_and_recover)
    
    @staticmethod
    def diagnose_display_issue(window: QWidget) -> str:
        """윈도우 표시 문제 진단
        
        Returns:
            str: 진단 결과 메시지
        """
        try:
            app = QApplication.instance()
            if not app:
                return "❌ QApplication 인스턴스 없음"
            
            if not window:
                return "❌ Window 객체 없음"
            
            # 기본 상태 확인
            is_visible = window.isVisible()
            is_active = window.isActiveWindow()
            geometry = window.geometry()
            
            # 화면 정보 확인
            primary_screen = app.primaryScreen()
            screen_info = "알 수 없음"
            if primary_screen:
                screen_geometry = primary_screen.availableGeometry()
                screen_info = f"{screen_geometry.width()}x{screen_geometry.height()}"
            
            # 진단 결과 생성
            diagnosis = []
            diagnosis.append(f"🖥️  화면 크기: {screen_info}")
            diagnosis.append(f"👁️  윈도우 보임: {'✅' if is_visible else '❌'}")
            diagnosis.append(f"🎯 윈도우 활성: {'✅' if is_active else '❌'}")
            diagnosis.append(f"📐 윈도우 위치: ({geometry.x()}, {geometry.y()})")
            diagnosis.append(f"📏 윈도우 크기: {geometry.width()}x{geometry.height()}")
            
            # 문제 분석
            issues = []
            if not is_visible:
                issues.append("윈도우가 숨겨져 있음")
            if geometry.width() <= 0 or geometry.height() <= 0:
                issues.append("윈도우 크기가 0")
            if primary_screen and not primary_screen.availableGeometry().intersects(geometry):
                issues.append("윈도우가 화면 밖에 위치")
            
            if issues:
                diagnosis.append(f"⚠️  발견된 문제: {', '.join(issues)}")
            else:
                diagnosis.append("✅ 문제 없음")
            
            return "\n".join(diagnosis)
            
        except Exception as e:
            return f"❌ 진단 실패: {e}"


def ensure_gui_visibility(window: QWidget) -> bool:
    """GUI 가시성 보장 (편의 함수)
    
    Args:
        window: 표시할 윈도우
        
    Returns:
        bool: 성공 여부
    """
    return WindowDisplayManager.ensure_window_visible(window)


def diagnose_gui_display(window: QWidget) -> str:
    """GUI 표시 문제 진단 (편의 함수)
    
    Args:
        window: 진단할 윈도우
        
    Returns:
        str: 진단 결과
    """
    return WindowDisplayManager.diagnose_display_issue(window)